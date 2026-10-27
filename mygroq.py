from groq import Groq

# Inisialisasi client dengan API key
client = Groq(api_key="xx")

# Prompt untuk generate kalimat
prompt = """
Parafrase kalimat berikut menggunakan bahasa yang formal dan natural: {K}
"""

# Request ke model
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",  # model cepat dan ringanllama3-8b-8192
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=200
)

# Ambil hasil
hasil = response.choices[0].message.content
print(hasil)
