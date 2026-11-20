import re
import sys
from openai import OpenAI
import pyperclip

# --- CONFIGURACIÓN OLLAMA LOCAL ---
OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODELO = "qwen2.5:7b"

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
- Recomendación: [ALTAMENTE RECOMENDADO / RECOMENDADO / CONSIDERAR / DESCARTAR]
- Estado de filtros eliminatorios: [PASA / FALLA — motivo]

**2. DESGLOSE POR CATEGORÍA (tabla)**
| Categoría | Peso | Score (0-100) | Aporte | Evidencia del CV |
|---|---|---|---|---|
| C#/.NET | 25% | | | (cita textual o referencia a sección) |
| React | 20% | | | |
| AKS / Kubernetes | 20% | | | |
| Vulnerability Remediation | 15% | | | |
| Production Support | 10% | | | |
| Años de experiencia | 10% | | | |

**3. NICE TO HAVE (bonus)**
- Lista de los que cumple con evidencia. Bonus total: +X%

**4. FORTALEZAS PRINCIPALES**
- Máximo 4 bullets, concretos y con evidencia.

**5. GAPS O RIESGOS**
- Máximo 4 bullets. Indica qué falta y su impacto en el rol.

**6. PREGUNTAS DE VALIDACIÓN SUGERIDAS PARA ENTREVISTA**
- 3 a 5 preguntas técnicas específicas para confirmar o descartar los gaps detectados (especialmente en AKS, remediación de vulnerabilidades y soporte a producción).

**7. NOTAS DE UBICACIÓN Y DISPONIBILIDAD**
- Ciudad/país detectado en el CV.
- Señales de disponibilidad para deployments nocturnos o fines de semana (si las hay).

=== CV A EVALUAR ===
"""


def evaluar_cv_con_ollama():
    texto_cv = pyperclip.paste().strip()
    if not texto_cv:
        print("Error: El portapapeles está vacío. No hay CV para evaluar.")
        sys.exit(1)

    # Ollama no requiere API key real, pero el SDK de OpenAI exige una cadena no vacía
    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

    print(f"Consultando localmente a Ollama ({MODELO})...")
    try:
        respuesta = client.chat.completions.create(
            model=MODELO,
            temperature=0.0,
            stream=True,
            extra_body={"options": {"num_ctx": 8192}},
            messages=[
                {"role": "system", "content": INSTRUCCIONES_CVMATCH},
                {"role": "user", "content": f"Analiza este CV:\n\n{texto_cv}"},
            ],
        )
    except Exception as e:
        print(
            f"Error al conectar con Ollama (verifica que el servicio esté activo"
            f" y '{MODELO}' descargado): {e}"
        )
        sys.exit(1)

    contenido = respuesta.choices[0].message.content
    print("\n--- Respuesta de Ollama ---")
    print(contenido)
    print("---------------------------\n")

    # Tolera negritas opcionales alrededor de "Match total" (ej. **Match total:** 34%)
    coincidencia = re.search(
        r"Match\s*total\*?[:\s]*\*?([\d.,]+\s*%)", contenido, re.IGNORECASE
    )
    if coincidencia:
        porcentaje = coincidencia.group(1).replace(" ", "").replace(".", ",")
        pyperclip.copy(porcentaje)
        print(f"¡Porcentaje listo en portapapeles!: {porcentaje}")
        return porcentaje
    else:
        print(
            "Error: La respuesta no incluyó el formato 'Match total: XX.XX%'."
        )
        sys.exit(1)


if __name__ == "__main__":
    evaluar_cv_con_ollama()