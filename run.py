# --------------------------------------------------
# IMPORTACIÓN DE MÓDULOS ESTÁNDAR
# --------------------------------------------------

import sys
import subprocess
import time
import random

# --------------------------------------------------
# CONFIGURACIÓN GLOBAL DE PAUSAS ANTI-BLOQUEO
# --------------------------------------------------

PAUSA_MIN = 5
PAUSA_MAX = 12

# --------------------------------------------------
# FUNCIÓN PRINCIPAL DE PROCESAMIENTO POR CANDIDATO
# --------------------------------------------------

def procesar_fila(fila):
    fila_str = str(fila)

    # Encabezado visual de seguimiento en consola
    print(f"\n==========================================")
    print(f"   PROCESANDO FILA {fila_str} (C{fila_str} -> B{fila_str})")
    print(f"==========================================")

    # --------------------------------------------------
    # PASO 1: EXTRACCIÓN DE CV DESDE LINKEDIN
    # --------------------------------------------------
    # Ejecuta el script externo pasando el número de fila para copiar el CV al portapapeles
    print(f"--- [1/3] extrayendo CV {fila_str} ---")
    if subprocess.run([sys.executable, "extraer_cv.py", fila_str]).returncode != 0:
        print(f"Fallo en extracción para fila {fila_str}. Saltando...")
        return

    # --------------------------------------------------
    # PASO 2: EVALUACIÓN DEL PERFIL CON INTELIGENCIA ARTIFICIAL
    # --------------------------------------------------
    # Toma el contenido del portapapeles y consulta a Gemini para obtener el match
    print("--- [2/3] consultando ia ---")
    if subprocess.run([sys.executable, "consultar_ai.py"]).returncode != 0:
        print(f"Fallo al enviar a Gemini en fila {fila_str}. Saltando...")
        return

    # --------------------------------------------------
    # PASO 3: REGISTRO DE RESULTADO EN GOOGLE SHEETS
    # --------------------------------------------------
    # Escribe el porcentaje de compatibilidad resultante en la celda B{fila}
    print(f"--- [3/3] agregando porcentaje {fila_str} ---")
    subprocess.run([sys.executable, "pegar_match.py", fila_str])


# --------------------------------------------------
# ORQUESTADOR Y VALIDACIÓN DE ARGUMENTOS CLI
# --------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  Rango: python run.py <fila_inicio> <fila_fin>  (Ej: python run.py 13 25)")
        print("  Única: python run.py <fila>                   (Ej: python run.py 13)")
        sys.exit(1)

    # Conversión y validación de tipo de dato (enteros)
    try:
        fila_inicio = int(sys.argv[1])
        fila_fin = int(sys.argv[2]) if len(sys.argv) >= 3 else fila_inicio
    except ValueError:
        print("Error: Los argumentos deben ser números enteros.")
        sys.exit(1)

    # Validación lógica del rango de filas
    if fila_fin < fila_inicio:
        print("Error: La fila final no puede ser menor que la fila inicial.")
        sys.exit(1)

    # --------------------------------------------------
    # CONTROL DE VOLUMEN Y ADVERTENCIA DE SEGURIDAD
    # --------------------------------------------------
    total_filas = (fila_fin - fila_inicio) + 1

    if total_filas > 50:
        print(f"Aviso: Vas a procesar {total_filas} perfiles. Se recomienda no pasar de 40-50 por tanda diaria para cuidar tu cuenta de LinkedIn.")

    # --------------------------------------------------
    # BUCLE DE EJECUCIÓN POR LOTES
    # --------------------------------------------------
    for fila in range(fila_inicio, fila_fin + 1):
        procesar_fila(fila)
        if fila < fila_fin:
            pausa = random.uniform(PAUSA_MIN, PAUSA_MAX)
            print(f"\nPausa de {pausa:.1f}s antes del siguiente candidato...")
            time.sleep(pausa)

    print("\n¡Lote completo terminado!")

# --------------------------------------------------
# PUNTO DE ENTRADA DEL SCRIPT
# --------------------------------------------------
if __name__ == "__main__":
    main()