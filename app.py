
import os
import re
import requests
from flask import Flask, render_template, request
from docx import Document
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()
app = Flask(__name__)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def analizar_docx(file):
    file_stream = BytesIO(file.read())  # ✅ ← Esta línea es la clave
    doc = Document(file_stream)
    resultado = []
    for para in doc.paragraphs:
        alineacion = para.alignment
        for run in para.runs:
            texto = run.text.strip()
            if not texto:
                continue
            result = {
                "texto": texto,
                "negrita": run.bold,
                "tamaño_fuente": run.font.size.pt if run.font.size else None,
                "alineacion": str(alineacion),
                "estilo": para.style.name
            }
            resultado.append(result)
    return resultado


def content_to_texto_plano(lista):
    return "\n".join([
        f"{item['texto']} | Negrita: {item['negrita']} | Tamaño: {item['tamaño_fuente']} | Alineación: {item['alineacion']} | Estilo: {item['estilo']}"
        for item in lista
    ])

def generar_prompt(nombre_archivo, contenido):
    with open("prompt_base.txt", "r", encoding="utf-8") as f:
        plantilla = f.read()
    prompt = plantilla.replace("{{nombre_archivo}}", nombre_archivo)
    prompt = prompt.replace("{{contenido}}", content_to_texto_plano(content))
    return prompt

def enviar_a_deepseek(prompt):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1000
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = ""
    if request.method == "POST":
        archivo = request.files["archivo"]
        if archivo.filename.endswith(".docx"):
            datos = analizar_docx(archivo)
            prompt = generar_prompt(archivo.filename, datos)
            resultado = enviar_a_deepseek(prompt)
            return render_template("resultado.html", resultado=resultado, nombre=archivo.filename)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
