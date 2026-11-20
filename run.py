import sys
import subprocess
import time
import random

PAUSA_MIN = 5
PAUSA_MAX = 12

def procesar_fila(fila):
    fila_str = str(fila)
    print(f"\n==========================================")
    print(f"   PROCESANDO FILA {fila_str} (C{fila_str} -> B{fila_str})")
    print(f"==========================================")

    # Paso 1: Extraer CV de LinkedIn al portapapeles
    print(f"--- [1/3] extrayendo CV {fila_str} ---")
    if subprocess.run([sys.executable, "extraer_cv.py", fila_str]).returncode != 0:
        print(f"Fallo en extracción para fila {fila_str}. Saltando...")
        return

    # Paso 2: Enviar el CV del portapapeles a Gemini
    print("--- [2/3] consultando ia ---")
    if subprocess.run([sys.executable, "consultar_ai.py"]).returncode != 0:
        print(f"Fallo al enviar a Gemini en fila {fila_str}. Saltando...")
        return

    # Paso 3: Pegar el porcentaje en Google Sheets (B{fila})
    print(f"--- [3/3] agregando porcentaje {fila_str} ---")
    subprocess.run([sys.executable, "pegar_match.py", fila_str])

def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  Rango: python run.py <fila_inicio> <fila_fin>  (Ej: python run.py 13 25)")
        print("  Única: python run.py <fila>                   (Ej: python run.py 13)")
        sys.exit(1)

    try:
        fila_inicio = int(sys.argv[1])
        fila_fin = int(sys.argv[2]) if len(sys.argv) >= 3 else fila_inicio
    except ValueError:
        print("Error: Los argumentos deben ser números enteros.")
        sys.exit(1)

    if fila_fin < fila_inicio:
        print("Error: La fila final no puede ser menor que la fila inicial.")
        sys.exit(1)

    total_filas = (fila_fin - fila_inicio) + 1

    if total_filas > 50:
        print(f"Aviso: Vas a procesar {total_filas} perfiles. Se recomienda no pasar de 40-50 por tanda diaria para cuidar tu cuenta de LinkedIn.")

    for fila in range(fila_inicio, fila_fin + 1):
        procesar_fila(fila)
        if fila < fila_fin:
            pausa = random.uniform(PAUSA_MIN, PAUSA_MAX)
            print(f"\nPausa de {pausa:.1f}s antes del siguiente candidato...")
            time.sleep(pausa)

    print("\n¡Lote completo terminado!")

if __name__ == "__main__":
    main()