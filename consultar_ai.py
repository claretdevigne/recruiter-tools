import os
import sys
import re
import json
from pathlib import Path
import pyperclip
from dotenv import load_dotenv
from openai import OpenAI

# -------------------------------------------------------------------------
# Busca la api_key en el .env y lo guarda en una variable
# -------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# -------------------------------------------------------------------------
# 2.- Lectura dinámica de la JD desde config_agente.json
# -------------------------------------------------------------------------
def obtener_jd_activa():
    config_path = os.path.join(BASE_DIR, "config_agente.json")
    if not os.path.exists(config_path):
        print("Error: No se encontró 'config_agente.json'. Selecciona una vacante en la interfaz.")
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"Error al leer 'config_agente.json': {e}")
        sys.exit(1)

    jd = cfg.get("jd_actual", "").strip()
    role = cfg.get("pestana_activa", "Sin especificar")
    if not jd:
        print(f"Error: No hay ninguna JD guardada para '{role}' en config_agente.json.")
        sys.exit(1)

    return jd, role

# -------------------------------------------------------------------------
# 2.- Prompt para la consulta
# -------------------------------------------------------------------------

PLANTILLA_PROMPT = """
Actúa como un Technical Recruiter Senior. Tu tarea es evaluar un CV contra la descripción de la vacante (JD) proporcionada abajo y devolver un análisis estructurado con un porcentaje de match objetivo.

=== DESCRIPCIÓN DE LA VACANTE (JD) ===

{jd_texto}

=== INSTRUCCIONES DE EVALUACIÓN ===

1. Lee la JD y el CV completo antes de puntuar.
2. Identifica los requisitos obligatorios, ubicación requerida, años de experiencia y el orden de prioridad o pesos indicados en la JD. Si la JD no especifica porcentajes exactos, distribuye el 100% proporcionalmente según el orden de prioridad de las tecnologías y responsabilidades descritas.
3. Para cada requisito, asigna un score de 0 a 100 basado únicamente en evidencia explícita del CV.
4. No asumas habilidades no evidenciadas — si no aparece en el CV, se puntúa como 0.
5. Diferencia entre mención superficial y experiencia hands-on demostrable (proyectos, roles, responsabilidades descritas).
6. FILTROS ELIMINATORIOS (knock-out):
   - Si la JD exige un país/ubicación obligatoria y el candidato reside fuera → Match = 0%
   - Si no cumple con los años mínimos de experiencia exigidos → Match = 0%
   - Si carece de la tecnología principal #1 de la vacante → Match ≤ 30%
7. Calcula el Match final ponderado (más hasta +5% de bonus si cumple con los Nice-to-Have, sin superar 100%) e indica si se disparó algún filtro eliminatorio.

=== FORMATO DE SALIDA REQUERIDO ===

**1. VEREDICTO RÁPIDO**
- Match total: XX%

**2. DESGLOSE POR REQUISITO**
- Resume brevemente los puntos fuertes, brechas y cumplimiento de filtros obligatorios.

=== CV A EVALUAR ===
"""

# -------------------------------------------------------------------------
# 4.- Consultar a OpenAI
# -------------------------------------------------------------------------

MODELO = "gpt-4o-mini-2024-07-18"

def evaluar_cv_con_openai():
    texto_cv = pyperclip.paste().strip()
    if not texto_cv:
        print("Error: El portapapeles está vacío. No hay CV para evaluar.")
        sys.exit(1)

    jd_texto, role = obtener_jd_activa()
    prompt_sistema = PLANTILLA_PROMPT.format(jd_texto=jd_texto)

    client = OpenAI(api_key=OPENAI_API_KEY)

    print(f"Consultando a {MODELO}...")
    try:
        respuesta = client.chat.completions.create(
            model=MODELO,
            temperature=0.1,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Analiza este CV:\n\n{texto_cv}"}
            ]
        )
    except Exception as e:
        print(f"Error al conectar con la API de OpenAI: {e}")
        sys.exit(1)

    contenido = respuesta.choices[0].message.content
    print("\n--- Respuesta de OpenAI ---")
    print(contenido)
    print("---------------------------\n")

    # Extraer el porcentaje de "Match total: XX.XX%" y convertir punto a coma
    coincidencia = re.search(r"Match\s*total[:\s]*([\d.,]+\s*%)", contenido, re.IGNORECASE)
    if coincidencia:
        porcentaje = coincidencias = coincidencia.group(1).replace(" ", "").replace(".", ",")
        pyperclip.copy(porcentaje)
        print(f"¡Porcentaje listo en portapapeles!: {porcentaje}")
        return porcentaje
    else:
        print("Error: La respuesta no incluyó el formato 'Match total: XX.XX%'.")
        sys.exit(1)

if __name__ == "__main__":
    evaluar_cv_con_openai()
