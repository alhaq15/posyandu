"""Rule-based faithfulness checker for generated report sentences / recommendations.

Checks, for ONE student's output against the structured data it was generated from:
  - omission      : a required subject / achievement is missing
  - distortion    : the predicate conveyed for a component contradicts its true predicate
  - hallucination : an entity (subject / activity) or number that is not in the input
  - review        : ambiguous case that should be checked manually

Input structure (one student):
    inp = {
      "subjects":   [{"subject": "Bahasa Indonesia", "predicate": "perlu peningkatan",
                      "improve": ["menyimak", "menulis teks pendek"]}, ...],
      "activities": [{"name": "Pramuka", "predicate": "baik"}, ...],      # may be empty
      "attendance": {"predicate": "masih baik", "p": 3},                  # optional
    }
    universe = {"subjects": {...}, "activities": {...}}   # all valid names in the database
"""
import re
from difflib import SequenceMatcher

# ---------- predicate classes ----------
GOOD = {"sangat baik", "baik sekali", "baik", "masih baik"}
FAIR = {"cukup", "cukup baik"}
BAD = {"perlu peningkatan"}


def pclass(predicate):
    p = predicate.lower().strip()
    if p in BAD:
        return "BAD"
    if p in FAIR:
        return "FAIR"
    if p in GOOD:
        return "GOOD"
    raise ValueError(f"unknown predicate: {predicate}")


# ---------- cue lexicons (adjust to your own wording) ----------
IMPROVE_CUES = ["peningkatan", "ditingkatkan", "meningkatkan", "berlatih", "latih",
                "perlu belajar", "lebih giat", "lebih rajin", "perbaikan", "diperbaiki",
                "kurang", "belum"]
STRONG_NEG = ["perlu peningkatan", "perlu ditingkatkan", "perlu perbaikan", "perlu diperbaiki",
              "kurang", "belum", "perlu berlatih", "perlu lebih banyak berlatih",
              "perlu lebih giat", "perlu lebih rajin"]
STRONG_POS = ["sangat baik", "baik sekali", "memuaskan", "luar biasa",
              "sesuai dengan yang diharapkan", "mempertahankan"]
ATTENDANCE_ANCHORS = ["kehadiran", "hadir", "absen", "ketidakhadiran"]


# ---------- text utilities ----------
def norm(t):
    t = t.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def contains(text, phrase, thr=0.85):
    """Exact match, or fuzzy match on a sliding word window."""
    text, phrase = norm(text), norm(phrase)
    if phrase in text:
        return True
    w, n = text.split(), len(phrase.split())
    for i in range(max(1, len(w) - n + 1)):
        if SequenceMatcher(None, " ".join(w[i:i + n]), phrase).ratio() >= thr:
            return True
    return False


def has_cue(text, cues):
    t = norm(text)
    return any(norm(c) in t for c in cues)


def split_segments(text):
    """Split into sentences, then split on contrast words so each clause is judged alone."""
    segs = []
    for part in re.split(r"[.\n;]+", text):
        segs += re.split(r",?\s+(?:namun|tetapi|sedangkan)\s+", part)
    return [s.strip() for s in segs if s.strip()]


# ---------- main check ----------
def build_components(inp):
    comps = []
    for s in inp["subjects"]:
        comps.append({"name": s["subject"], "cls": pclass(s["predicate"]),
                      "anchors": [s["subject"]] + s.get("improve", []),
                      "main_anchors": [s["subject"]], "improve": s.get("improve", [])})
    for a in inp.get("activities", []):
        comps.append({"name": a["name"], "cls": pclass(a["predicate"]),
                      "anchors": [a["name"]], "main_anchors": [a["name"]], "improve": []})
    att = inp.get("attendance")
    if att:
        comps.append({"name": "kehadiran", "cls": pclass(att["predicate"]),
                      "anchors": ATTENDANCE_ANCHORS, "main_anchors": ATTENDANCE_ANCHORS,
                      "improve": []})
    return comps


def check(output, inp, universe, require_good=False):
    errors = []
    comps = build_components(inp)

    # 1. Omission: BAD / FAIR components (and their achievements) must be mentioned
    for c in comps:
        needed = c["cls"] in ("BAD", "FAIR") or (require_good and c["cls"] == "GOOD")
        if needed and not any(contains(output, a) for a in c["main_anchors"]):
            errors.append(("omission", f"component missing: {c['name']}"))
        if c["cls"] == "BAD":
            for x in c["improve"]:
                if not contains(output, x):
                    errors.append(("omission", f"achievement missing: {x}"))

    # 2. Distortion: judge the predicate conveyed in every clause that mentions a component
    for seg in split_segments(output):
        matched = [c for c in comps if any(contains(seg, a) for a in c["anchors"])]
        if not matched:
            continue
        classes = {c["cls"] for c in matched}
        if "BAD" in classes and "GOOD" in classes:
            errors.append(("review", f"clause mixes good and bad components: '{seg}'"))
            continue
        for c in matched:
            if c["cls"] == "BAD":
                if not has_cue(seg, IMPROVE_CUES):
                    errors.append(("distortion",
                                   f"{c['name']} should need improvement but clause shows none: '{seg}'"))
                elif has_cue(seg, STRONG_POS):
                    errors.append(("review",
                                   f"{c['name']}: improvement and positive cues together: '{seg}'"))
            elif c["cls"] == "FAIR":
                if has_cue(seg, ["sangat baik", "baik sekali", "memuaskan", "luar biasa"]) or \
                        has_cue(seg, ["perlu peningkatan"]):
                    errors.append(("distortion",
                                   f"{c['name']} is only 'cukup' but clause says otherwise: '{seg}'"))
            else:  # GOOD
                if has_cue(seg, STRONG_NEG):
                    errors.append(("distortion",
                                   f"{c['name']} is good but clause shows a problem: '{seg}'"))

    # 3. Hallucination: known entities not in this student's input, and unknown numbers
    present = {c["name"] for c in comps}
    for e in universe["subjects"] | universe["activities"]:
        if e not in present and contains(output, e):
            errors.append(("hallucination", f"entity not in input: {e}"))
    in_nums = set(re.findall(r"\d+", " ".join(map(str, inp.values()))))
    body = re.sub(r"(?m)^\s*\d+[.)]\s*", "", output)  # ignore list numbering such as "1."
    for n in set(re.findall(r"\d+", body)) - in_nums:
        errors.append(("hallucination", f"number not in input: {n}"))
    return errors


def summarize(results):
    """results: list of error lists (one per output). Returns consistency rate and error counts."""
    counts = {"omission": 0, "distortion": 0, "hallucination": 0, "review": 0}
    clean = 0
    for errs in results:
        if not [e for e in errs if e[0] != "review"]:
            clean += 1
        for t, _ in errs:
            counts[t] += 1
    return {"outputs": len(results), "consistent": clean,
            "consistency_rate": clean / len(results) if results else None, **counts}


if __name__ == "__main__":
    inp = {
        "subjects": [
            {"subject": "Bahasa Indonesia", "predicate": "perlu peningkatan",
             "improve": ["menyimak", "menulis teks pendek"]},
            {"subject": "Pendidikan Pancasila", "predicate": "cukup"},
            {"subject": "Matematika", "predicate": "baik"}],
        "activities": [{"name": "Pramuka", "predicate": "baik"}],
        "attendance": {"predicate": "masih baik", "p": 3},
    }
    universe = {"subjects": {"Bahasa Indonesia", "Pendidikan Pancasila", "Matematika", "IPAS"},
                "activities": {"Pramuka", "Futsal"}}

    cases = {
        "correct": ("1. Bahasa Indonesia: Ananda perlu lebih banyak berlatih menyimak dan menulis teks pendek.\n"
                    "2. Pendidikan Pancasila: Ananda diharapkan terus memperdalam pemahamannya.\n"
                    "Ananda diharapkan mempertahankan Matematika, Pramuka, dan menjaga kedisiplinan kehadiran."),
        "predicate distorted (BAD -> good)": (
                    "1. Bahasa Indonesia: Ananda sudah sangat baik dalam menyimak dan menulis teks pendek.\n"
                    "2. Pendidikan Pancasila: Ananda diharapkan terus memperdalam pemahamannya."),
        "predicate distorted (GOOD -> bad)": (
                    "1. Bahasa Indonesia: Ananda perlu berlatih menyimak dan menulis teks pendek.\n"
                    "2. Pendidikan Pancasila: Ananda diharapkan terus memperdalam pemahamannya.\n"
                    "3. Matematika: Ananda masih kurang memahami Matematika."),
        "hallucination": (
                    "1. Bahasa Indonesia: Ananda perlu berlatih menyimak dan menulis teks pendek.\n"
                    "2. Pendidikan Pancasila: Ananda perlu memperdalam pemahaman.\n"
                    "3. IPAS: Ananda perlu belajar 2 jam setiap hari."),
        "attendance distorted": (
                    "1. Bahasa Indonesia: Ananda perlu berlatih menyimak dan menulis teks pendek.\n"
                    "2. Pendidikan Pancasila: Ananda perlu memperdalam pemahaman.\n"
                    "Kehadiran Ananda kurang dan perlu ditingkatkan."),
    }
    all_results = []
    for name, out in cases.items():
        errs = check(out, inp, universe)
        all_results.append(errs)
        print(f"[{name}]")
        for e in errs:
            print("   ", e)
        if not errs:
            print("    (no errors)")
    print(summarize(all_results))