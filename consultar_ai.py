import os
import sys
import re
from pathlib import Path
import pyperclip
from dotenv import load_dotenv
from openai import OpenAI

# -------------------------------------------------------------------------
# Busca la api_key en el .env y lo guarda en una variable
# -------------------------------------------------------------------------

load_dotenv(dotenv_path=".env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# -------------------------------------------------------------------------
# 2.- Prompt para la consulta
# -------------------------------------------------------------------------

INSTRUCCIONES_CVMATCH = """
Actúa como un Technical Recruiter Senior especializado en perfiles Full Stack .NET + Security Remediation. Tu tarea es evaluar un CV contra el siguiente perfil de vacante y devolver un análisis estructurado con un porcentaje de match objetivo.

=== PERFIL DE LA VACANTE ===

Rol: Full Stack Developer + Security Remediation
Ubicación: Colombia (OBLIGATORIO — candidatos fuera de Colombia se descartan automáticamente)
Experiencia mínima: 3+ años de desarrollo profesional

RESPONSABILIDADES CLAVE:
- Identificar, diagnosticar y remediar vulnerabilidades de seguridad en aplicaciones .NET y React, dependencias e infraestructura cloud.
- Resolver vulnerabilidades críticas en SLA de 24 horas.
- Desarrollar, modificar y mantener código para resolver issues de seguridad y defectos productivos.
- Troubleshooting de aplicaciones desplegadas en Azure Kubernetes Service (AKS).
- Implementar y desplegar fixes a producción garantizando estabilidad y seguridad.
- Colaborar con equipos de ingeniería y ciberseguridad.
- Soportar releases de producción (ocasionalmente noches o fines de semana).
- Asistir con testing automatizado de regresión cuando no haya remediación.

ORDEN DE PRIORIDAD (pesos sugeridos):
1. C#/.NET — 25%
2. React — 20%
3. AKS / Kubernetes — 20%
4. Vulnerability Remediation — 15%
5. Production Support — 10%
6. Experiencia 3+ años — 10% (gate obligatorio)

NICE TO HAVE (bonus, máximo +5% adicional):
- React Native
- Servicios adicionales de Microsoft Azure
- QA testing / frameworks de regresión
- Herramientas de vulnerability scanning y reporting
- Experiencia en entornos Agile

FILTROS ELIMINATORIOS (knock-out):
- ❌ No reside en Colombia → Match = 0%
- ❌ Menos de 3 años de experiencia profesional → Match = 0%
- ❌ Sin evidencia de C#/.NET en el CV → Match ≤ 30%

=== INSTRUCCIONES DE EVALUACIÓN ===

1. Lee el CV completo antes de puntuar.
2. Para cada categoría, asigna un score de 0 a 100 basado en evidencia explícita del CV.
3. No asumas habilidades no evidenciadas — si no aparece, se puntúa como 0.
4. Diferencia entre uso superficial y experiencia hands-on demostrable (proyectos, roles, responsabilidades descritas).
5. Calcula el Match final aplicando la fórmula:
   Match% = (C#/.NET × 0.25) + (React × 0.20) + (AKS × 0.20) + (Vulnerability Remediation × 0.15) + (Production Support × 0.10) + (Años exp. × 0.10) + bonus
6. Si se dispara un filtro eliminatorio, el Match final es 0% o ≤30% según corresponda y debes indicarlo claramente.

=== FORMATO DE SALIDA REQUERIDO ===

**1. VEREDICTO RÁPIDO**
- Match total: XX%

=== CV A EVALUAR ===
"""

# -------------------------------------------------------------------------
# 3.- Hace la consulta a openai
# -------------------------------------------------------------------------

MODELO = "gpt-4o-mini-2024-07-18"

def evaluar_cv_con_openai():
    texto_cv = pyperclip.paste().strip()
    if not texto_cv:
        print("Error: El portapapeles está vacío. No hay CV para evaluar.")
        sys.exit(1)

    client = OpenAI(api_key=OPENAI_API_KEY)

    print(f"Consultando a {MODELO}...")
    try:
        respuesta = client.chat.completions.create(
            model=MODELO,
            temperature=0.1,  # Baja temperatura para evaluaciones consistentes y precisas
            messages=[
                {"role": "system", "content": INSTRUCCIONES_CVMATCH},
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
