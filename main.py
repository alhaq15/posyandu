from groq import Groq
import pandas as pd
import random
import time

def gabung_materi(materi_list):
    if len(materi_list) < 1:
        return ''
    elif len(materi_list) == 1:
        return materi_list[0]
    elif len(materi_list) == 2:
        return f"{materi_list[0]} dan {materi_list[1]}"
    else:
        return ", ".join(materi_list[:-1]) + f", dan {materi_list[-1]}"

def generate_deskripsi(nama, materi_baik, deskripsi, materi_perlu, gaya=None):
    # Template dengan "namun"
    # Template jika ADA materi_perlu
    templates_namun = [
        "Ananda {N} telah menunjukkan pemahaman yang {D} pada materi {A}, namun perlu meningkatkan penguasaan pada materi {X}.",
        "Kemampuan Ananda {N} dalam memahami {A} {D}, namun masih perlu peningkatan pada materi {X}.",
        "Ananda {N} {D} dalam menguasai materi {A}, namun perlu lebih banyak latihan pada materi {X}.",
        "Pemahaman Ananda {N} terhadap materi {A} tergolong {D}, namun penguasaan materi {X} masih perlu ditingkatkan.",
        "Ananda {N} menunjukkan capaian yang {D} pada materi {A}, namun masih perlu pendalaman pada materi {X}."
    ]

    templates_dan = [
        "Ananda {N} telah memahami materi {A} dengan {D}, dan perlu meningkatkan penguasaan pada materi {X}.",
        "Kemampuan dalam materi {A} {D}, dan masih perlu peningkatan pada materi {X}.",
        "Ananda {N} {D} dalam menguasai materi {A}, dan perlu lebih banyak berlatih pada materi {X}.",
        "Pemahaman Ananda {N} terhadap materi {A} {D}, dan penguasaan materi {X} masih perlu ditingkatkan.",
        "Ananda {N} menunjukkan hasil yang {D} pada materi {A}, dan perlu pendalaman pada materi {X}."
    ]

    # Template jika TIDAK ADA materi_perlu
    templates_tanpa_perlu = [
        "Ananda {N} telah menunjukkan pemahaman yang {D} pada materi {A}.",
        "Kemampuan Ananda {N} dalam memahami materi {A} tergolong {D}.",
        "Ananda {N} {D} dalam menguasai materi {A}.",
        "Pemahaman Ananda {N} terhadap materi {A} sudah {D}.",
        "Ananda {N} menunjukkan capaian yang {D} pada materi {A}."
    ]

    # Gabungkan list materi jadi kalimat
    A_text = gabung_materi(materi_baik)
    X_text = gabung_materi(materi_perlu)

    #LOGIKA UTAMA
    if not materi_perlu or len(materi_perlu) == 0 or X_text.strip() == "":
        template = random.choice(templates_tanpa_perlu)
        return template.format(N=nama, D=deskripsi, A=A_text)
    
    # Pilih gaya
    if gaya == "namun":
        template = random.choice(templates_namun)
    elif gaya == "dan":
        template = random.choice(templates_dan)

    return template.format(N=nama, D=deskripsi, A=A_text, X=X_text)

def generate_deskripsi_ekskul(nama, predikat, nama_ekskul):
    templates = {
        "baik sekali": [
            "Ananda {N} menunjukkan kinerja yang sangat baik dalam kegiatan ekstrakurikuler {ekskul}.",
            "Ananda {N} aktif dan berprestasi sangat baik dalam kegiatan {ekskul}.",
            "Ananda {N} berpartisipasi dengan sangat baik dan menunjukkan antusiasme tinggi dalam {ekskul}.",
            "Ananda {N} sangat aktif serta menunjukkan hasil yang sangat memuaskan dalam kegiatan {ekskul}."
        ],
        "baik": [
            "Ananda {N} menunjukkan kinerja yang baik dalam kegiatan ekstrakurikuler {ekskul}.",
            "Ananda {N} berpartisipasi dengan baik dalam kegiatan {ekskul}.",
            "Ananda {N} cukup aktif dan menunjukkan hasil yang baik dalam kegiatan {ekskul}.",
            "Ananda {N} terlibat dengan baik dalam kegiatan {ekskul}."
        ],
        "cukup": [
            "Ananda {N} menunjukkan partisipasi yang cukup dalam kegiatan ekstrakurikuler {ekskul}.",
            "Ananda {N} cukup terlibat dalam kegiatan {ekskul}, namun masih perlu peningkatan.",
            "Ananda {N} menunjukkan keterlibatan yang cukup, dan perlu lebih aktif dalam kegiatan {ekskul}.",
            "Ananda {N} berpartisipasi pada tingkat yang cukup dalam kegiatan {ekskul} dan masih dapat ditingkatkan."
        ],
        "perlu peningkatan": [
            "Ananda {N} perlu meningkatkan partisipasi dalam kegiatan ekstrakurikuler {ekskul}.",
            "Ananda {N} menunjukkan keterlibatan yang masih perlu ditingkatkan dalam kegiatan {ekskul}.",
            "Ananda {N} kurang aktif dalam kegiatan {ekskul} dan perlu peningkatan.",
            "Partisipasi Ananda {N} dalam kegiatan {ekskul} masih perlu ditingkatkan."
        ]
    }

    predikat = predikat.lower()

    if predikat not in templates:
        return "Predikat tidak dikenali."

    template = random.choice(templates[predikat])
    return template.format(N=nama, ekskul=nama_ekskul)

def generate_deskripsi_kehadiran(nama, sakit, izin, alpa): 

    # Kategori berdasarkan alpa
    if alpa == 0:
        kategori = "sangat baik"
    elif alpa == 1:
        kategori = "baik"
    elif alpa == 2:
        kategori = "cukup"
    else:
        kategori = "perlu peningkatan"

    total = ''#sakit + izin + alpa
    templates = {
        "sangat baik": [
            "Kehadiran Ananda {N} sangat baik tanpa adanya ketidakhadiran tanpa keterangan.",
            "Ananda {N} menunjukkan kedisiplinan yang sangat baik dalam kehadiran.",
            "Tingkat kehadiran Ananda {N} sangat baik dan konsisten."
        ],
        "baik": [
            "Kehadiran Ananda {N} tergolong baik, namun perlu lebih disiplin dalam menjaga kehadiran.",
            "Ananda {N} memiliki kehadiran yang baik dengan sedikit ketidakhadiran tanpa keterangan.",
            "Tingkat kehadiran Ananda {N} baik, namun masih dapat ditingkatkan."
        ],
        "cukup": [
            "Kehadiran Ananda {N} cukup, namun perlu meningkatkan kedisiplinan terutama dalam mengurangi ketidakhadiran tanpa keterangan.",
            "Ananda {N} memiliki tingkat kehadiran yang cukup dan perlu perbaikan.",
            "Tingkat kehadiran Ananda {N} cukup, namun perlu perhatian lebih."
        ],
        "perlu peningkatan": [
            "Kehadiran Ananda {N} perlu peningkatan, terutama dalam mengurangi ketidakhadiran tanpa keterangan.",
            "Ananda {N} kurang disiplin dalam kehadiran dan perlu perhatian khusus.",
            "Tingkat kehadiran Ananda {N} masih rendah dan perlu ditingkatkan."
        ]
    }

    kalimat = random.choice(templates[kategori])
    kalimat = kalimat.format(N=nama) 
    # Tambahkan detail data absensi
    detail = f" (Sakit: {sakit}, Izin: {izin}, Alpa: {alpa})"

    return kalimat + detail

def baca_data():
    client = Groq(api_key="xxx")
    file = open("output2.txt", "w", encoding="utf-8")

    # Baca file Excel
    file_path = "data_rapor.xlsx"  # ganti dengan path file kamu
    df = pd.read_excel(file_path, sheet_name="rapor", dtype={"CP": str, "Nama": str, "Matapelajaran": str, "Perbaikan": str, "Ekskul": str})
    df = df.fillna("")
    df_cp = pd.read_excel(file_path, sheet_name="CP_SD")
    df_cp = df_cp.fillna("")

    # Akses per baris
    i = 0
    for index, row in df.iterrows():
        i = i + 1
        nama = str(row['Nama'])
        mp = str(row['Matapelajaran'])
        cp = int(row['CP'])
        nilai = row['Nilai']
        perbaikan = str(row['Perbaikan'])
        if len(perbaikan) > 1:
            revisi = perbaikan.split(',')
        else:
            revisi = []

        ekskul = str(row['Ekskul'])
        grade_ekskul = str(row['Grade_ekskul'])
        alpa = row['Alpa'] if (not pd.isna(row['Alpa']) or row['Alpa'] == '') else 0
        alpa = 0 if alpa == '' else int(alpa)
        izin = row['Izin'] if (not pd.isna(row['Izin']) or not row['Alpa']) else 0
        izin = 0 if izin == '' else int(izin)
        sakit = row['Sakit'] if (not pd.isna(row['Sakit']) or not row['Alpa']) else 0
        sakit = 0 if sakit == '' else int(sakit)
        if i % 2 ==0:
            gaya = "namun"
        else:
            gaya = "dan"

        #deskripsi nilai
        kalimat_deskripsi = generate_deskripsi(nama, get_cp_desc(df_cp, cp), konversi_nilai(nilai), revisi, gaya)
        print(kalimat_deskripsi)
        file.write(kalimat_deskripsi)
        llm_result = parafrase(client, kalimat_deskripsi)
        print(llm_result)
        file.write(llm_result)
        file.write("\n\n")
        print()
        time.sleep(2)

        #deskripsi ekskul
        kalimat_ekskul = generate_deskripsi_ekskul(nama, grade_ekskul, ekskul)
        print(kalimat_ekskul)
        file.write(kalimat_ekskul)
        llm_result = parafrase(client, kalimat_ekskul)  
        print(llm_result)  
        file.write(llm_result)
        file.write("\n\n")
        print()
        time.sleep(2)

        #deskripsi kehadiran
        kalimat_kehadiran = generate_deskripsi_kehadiran(nama, sakit, izin, alpa)
        print(kalimat_kehadiran)
        file.write(kalimat_kehadiran)
        llm_result = parafrase(client, kalimat_kehadiran)  
        print(llm_result)
        file.write(llm_result)
        file.write("\n\n")
        print()
        time.sleep(2)
    file.close()

def parafrase(myclient, awal):
    # Prompt untuk generate kalimat
    prompt = """
    Buatkan satu variasi kalimat deskripsi nilai rapor dari kalimat berikut.
    
    Kalimat:
    "{sentence}"

    Ketentuan:
    - Bahasa Indonesia formal dan natural
    - Variasikan struktur kalimat
    - Gunakan sinonim yang sesuai konteks pendidikan
    - Tetap mempertahankan makna evaluatif
    - Hindari pengulangan kata yang sama
    - Tidak perlu memberikan kalimat tambahan apapun
    """
    prompt = prompt.format(sentence=awal)
    # Request ke model
    response = myclient.chat.completions.create(
        model="openai/gpt-oss-120b", 
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=5000
    )

    # Ambil hasil
    return response.choices[0].message.content

# Fungsi konversi nilai ke deskripsi
def konversi_nilai(nilai):
    if 90 <= nilai <= 100:
        return "sangat baik"
    elif 80 <= nilai <= 89:
        return "baik"
    elif 70 <= nilai <= 79:
        return "cukup baik"
    else:
        return "perlu peningkatan"

# Fungsi ambil deskripsi CP
def get_cp_desc(df, cp_index):
    for index, row in df.iterrows():
        idx = row["Matematika"]
        if idx == cp_index:
            return [row["cp"]]
    
    print(cp_index)
    return []

# Contoh penggunaan
# Inisialisasi client dengan API key

baca_data()
