import os
import subprocess
import sys
import time
import pyautogui

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPT_ENCONTRAR = os.path.join(BASE_DIR, "encontrar_viable.py")
SCRIPT_ABRIR = os.path.join(BASE_DIR, "abrir_link.py")
SCRIPT_CONTACTAR = os.path.join(BASE_DIR, "contactar.py")
SCRIPT_GUARDAR_PROYECTO = os.path.join(BASE_DIR, "guardarenproyecto.py")
SCRIPT_ACTUALIZAR_BD = os.path.join(BASE_DIR, "actualizarbasededatos.py")


def log(mensaje: str):
    print(mensaje, flush=True)


def ejecutar_paso(script: str, args: list = None, capturar_salida: bool = False):
    comando = [sys.executable, script] + (args or [])
    nombre = os.path.basename(script)
    log(f"--> Ejecutando {nombre} {' '.join(args or [])}...")

    if capturar_salida:
        return subprocess.run(comando, capture_output=True, text=True)
    return subprocess.run(comando)


def parsear_argumentos():
    # Sin parámetros: inicia en 1, sin límite superior
    if len(sys.argv) == 1:
        return 1, None
    # Un parámetro: inicia en argv[1], sin límite superior
    elif len(sys.argv) == 2:
        return int(sys.argv[1]), None
    # Dos parámetros: inicia en argv[1] y termina en argv[2]
    else:
        return int(sys.argv[1]), int(sys.argv[2])


def main():
    try:
        fila_actual, fila_fin = parsear_argumentos()
    except ValueError:
        log("ERROR: Los parámetros deben ser números enteros. Ejemplo: python3 main.py 5 20")
        sys.exit(1)

    log("==========================================")
    log(f"INICIANDO ORQUESTADOR | Inicio: {fila_actual} | Fin: {fila_fin if fila_fin is not None else 'Sin límite'}")

    procesados = 0

    while True:
        if fila_fin is not None and fila_actual > fila_fin:
            log(f"Se alcanzó la fila límite ({fila_fin}). Proceso finalizado.")
            break

        log(f"\n--- Buscando candidato viable desde fila {fila_actual} ---")
        args_buscar = [str(fila_actual)]
        if fila_fin is not None:
            args_buscar.append(str(fila_fin))

        # 1. Encontrar fila viable
        res_encontrar = ejecutar_paso(SCRIPT_ENCONTRAR, args_buscar, capturar_salida=True)
        if res_encontrar.returncode != 0:
            log("No se encontraron más filas viables en el rango indicado. Proceso terminado.")
            break

        fila_encontrada = int(res_encontrar.stdout.strip().splitlines()[-1])

        if fila_fin is not None and fila_encontrada > fila_fin:
            log(f"La siguiente fila viable ({fila_encontrada}) supera el límite ({fila_fin}). Proceso terminado.")
            break

        log(f"Fila viable encontrada: {fila_encontrada}")

        # 2. Abrir enlace del perfil en pestaña 2
        if ejecutar_paso(SCRIPT_ABRIR, [str(fila_encontrada)]).returncode != 0:
            log(f"FALLO al abrir el enlace de la fila {fila_encontrada}. Deteniendo ejecución.")
            break

        # 3. Contactar en LinkedIn (pestaña 2)
        if ejecutar_paso(SCRIPT_CONTACTAR).returncode != 0:
            log(f"FALLO en contactar.py para la fila {fila_encontrada}. Deteniendo ejecución.")
            break

        # 4. Guardar en proyecto de Recruiter (abre pestaña 3, guarda y cierra pestaña 3)
        if ejecutar_paso(SCRIPT_GUARDAR_PROYECTO).returncode != 0:
            log(f"FALLO en guardarenproyecto.py para la fila {fila_encontrada}. Deteniendo ejecución.")
            break

        # Cerrar pestaña 2 (perfil de LinkedIn) para volver a la pestaña 1 (Google Sheets)
        log("Cerrando pestaña del perfil de LinkedIn (Ctrl+W)...")
        pyautogui.hotkey('ctrl', 'w')
        time.sleep(0.8)

        # 5. Actualizar base de datos / hoja de cálculo
        if ejecutar_paso(SCRIPT_ACTUALIZAR_BD, [str(fila_encontrada)]).returncode != 0:
            log(f"FALLO en actualizarbasededatos.py para la fila {fila_encontrada}. Deteniendo ejecución.")
            break

        procesados += 1
        fila_actual = fila_encontrada + 1
        log(f"Candidato en fila {fila_encontrada} completado con éxito. (Total procesados: {procesados})")
        time.sleep(1.0)

    log("==========================================")
    log(f"RESUMEN FINAL | Total candidatos procesados: {procesados}")


if __name__ == "__main__":
    main()