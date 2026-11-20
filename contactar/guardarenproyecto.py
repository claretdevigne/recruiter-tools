import os
import sys
import time
import pyautogui
import pyperclip

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_ABRIR_RECRUITER = os.path.join(BASE_DIR, "10.png")    # Botón "Abrir en Recruiter" (pestaña 2)
IMG_GUARDAR_PROYECTO = os.path.join(BASE_DIR, "11.png")   # Botón "Guardar en proyecto" (pestaña 3)
IMG_PROYECTO_EXISTENTE = os.path.join(BASE_DIR, "12.png") # Radio button "Seleccionar proyecto existente"
IMG_BOTON_GUARDAR = os.path.join(BASE_DIR, "14.png")      # Botón azul "Guardar" final del modal

NOMBRE_PROYECTO = "Vulnerability engineer"


def log(mensaje: str):
    print(mensaje, flush=True)


def buscar_imagen(ruta_imagen: str, confianza: float = 0.7):
    try:
        return pyautogui.locateCenterOnScreen(ruta_imagen, confidence=confianza, grayscale=True)
    except Exception:
        return None


# -------------------------------------------------------------------------
# 1.- Busca "Abrir en Recruiter" (10.png) y hace clic
# -------------------------------------------------------------------------
def paso_1_abrir_en_recruiter(tiempo_max: int = 30) -> bool:
    log(f"[Paso 1] INICIO - Buscando '10.png' (Abrir en Recruiter) (máx {tiempo_max}s)...")
    inicio = time.time()

    while time.time() - inicio < tiempo_max:
        ubicacion_10 = buscar_imagen(IMG_ABRIR_RECRUITER, confianza=0.7)
        if ubicacion_10 is not None:
            log(f"[Paso 1] ÉXITO - 10.png encontrado en ({ubicacion_10.x}, {ubicacion_10.y}). Haciendo clic...")
            pyautogui.moveTo(ubicacion_10.x, ubicacion_10.y, duration=0.2)
            pyautogui.click()
            time.sleep(2.0)
            return True
        time.sleep(0.5)

    log("[Paso 1] FALLO - Tiempo agotado sin encontrar 10.png")
    return False


# -------------------------------------------------------------------------
# 2.- Espera carga de Recruiter y hace clic en "Guardar en proyecto" (11.png)
# -------------------------------------------------------------------------
def paso_2_clic_guardar_en_proyecto(tiempo_max: int = 120):
    log(f"[Paso 2] INICIO - Esperando carga de Recruiter y buscando '11.png' (máx {tiempo_max}s)...")
    inicio = time.time()
    ultimo_log = -5

    while time.time() - inicio < tiempo_max:
        ubicacion_11 = buscar_imagen(IMG_GUARDAR_PROYECTO, confianza=0.7)
        if ubicacion_11 is not None:
            log(f"[Paso 2] ÉXITO - 11.png encontrado en ({ubicacion_11.x}, {ubicacion_11.y}). Haciendo clic...")
            pyautogui.moveTo(ubicacion_11.x, ubicacion_11.y, duration=0.2)
            pyautogui.click()
            time.sleep(2.0)
            return ubicacion_11

        transcurrido = int(time.time() - inicio)
        if transcurrido - ultimo_log >= 5:
            log(f"[Paso 2] Esperando que cargue Recruiter (11.png)... ({transcurrido}s / {tiempo_max}s)")
            ultimo_log = transcurrido

        time.sleep(0.5)

    log("[Paso 2] FALLO - Tiempo agotado sin encontrar 11.png")
    return None


# -------------------------------------------------------------------------
# 3.- Scrollea hasta ver "Seleccionar proyecto existente" (12.png) y hace clic
# -------------------------------------------------------------------------
def paso_3_seleccionar_proyecto_existente(ubicacion_11, tiempo_max: int = 20) -> bool:
    log("[Paso 3] INICIO - Buscando 'Seleccionar proyecto existente' (12.png)...")
    inicio = time.time()

    x_modal = ubicacion_11.x
    y_modal = ubicacion_11.y + 150

    while time.time() - inicio < tiempo_max:
        ubicacion_12 = buscar_imagen(IMG_PROYECTO_EXISTENTE, confianza=0.75)
        if ubicacion_12 is not None:
            log(f"[Paso 3] ÉXITO - 12.png encontrado en ({ubicacion_12.x}, {ubicacion_12.y}). Haciendo clic...")
            pyautogui.moveTo(ubicacion_12.x, ubicacion_12.y, duration=0.2)
            pyautogui.click()
            time.sleep(0.8)
            return True

        log("[Paso 3] 12.png no visible aún, haciendo scroll hacia abajo...")
        pyautogui.moveTo(x_modal, y_modal, duration=0.1)
        pyautogui.scroll(-5)
        time.sleep(0.8)

    log("[Paso 3] FALLO - No se encontró 'Seleccionar proyecto existente' (12.png)")
    return False


# -------------------------------------------------------------------------
# 4.- Solo teclado: pega el nombre donde ya quedó el cursor y selecciona
# -------------------------------------------------------------------------
def paso_4_elegir_proyecto() -> bool:
    log(f"[Paso 4] INICIO - Pegando '{NOMBRE_PROYECTO}' directamente en el campo enfocado...")
    pyperclip.copy(NOMBRE_PROYECTO)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.5)

    log("[Paso 4] Seleccionando opción de la lista (Down + Enter)...")
    pyautogui.press('down')
    time.sleep(0.2)
    pyautogui.press('enter')
    time.sleep(0.5)

    log("[Paso 4] ÉXITO - Proyecto seleccionado.")
    return True


# -------------------------------------------------------------------------
# 5.- Hace clic en Guardar (14.png), espera confirmación y cierra pestaña
# -------------------------------------------------------------------------
def paso_5_guardar_y_cerrar(tiempo_max: int = 15) -> bool:
    log("[Paso 5] INICIO - Buscando botón 'Guardar' (14.png)...")
    inicio = time.time()

    while time.time() - inicio < tiempo_max:
        ubicacion_14 = buscar_imagen(IMG_BOTON_GUARDAR, confianza=0.75)
        if ubicacion_14 is not None:
            log(f"[Paso 5] ÉXITO - 14.png encontrado en ({ubicacion_14.x}, {ubicacion_14.y}). Haciendo clic...")
            pyautogui.moveTo(ubicacion_14.x, ubicacion_14.y, duration=0.2)
            pyautogui.click()

            # Esperar a que Recruiter complete el guardado antes de cerrar la pestaña
            log("[Paso 5] Esperando 2.5s a que se guarde en Recruiter...")
            time.sleep(2.5)

            log("[Paso 5] Cerrando pestaña de Recruiter con Ctrl+W...")
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(0.5)
            log("[Paso 5] ÉXITO - Candidato guardado y pestaña cerrada.")
            return True

        time.sleep(0.5)

    log("[Paso 5] FALLO - Tiempo agotado sin encontrar botón Guardar (14.png)")
    return False


# -------------------------------------------------------------------------
# Ejecución principal
# -------------------------------------------------------------------------
def main() -> bool:
    log("==========================================")
    log(f"INICIANDO guardarenproyecto.py | Carpeta base: {BASE_DIR}")

    for ruta in (IMG_ABRIR_RECRUITER, IMG_GUARDAR_PROYECTO, IMG_PROYECTO_EXISTENTE, IMG_BOTON_GUARDAR):
        if not os.path.exists(ruta):
            log(f"ERROR CRÍTICO: Falta el archivo '{ruta}'")
            return False

    if not paso_1_abrir_en_recruiter(tiempo_max=30):
        return False

    ubicacion_11 = paso_2_clic_guardar_en_proyecto(tiempo_max=120)
    if ubicacion_11 is None:
        return False

    if not paso_3_seleccionar_proyecto_existente(ubicacion_11, tiempo_max=20):
        return False

    if not paso_4_elegir_proyecto():
        return False

    if not paso_5_guardar_y_cerrar(tiempo_max=15):
        return False

    log("==========================================")
    return True


if __name__ == "__main__":
    exito = main()
    log(f"FIN guardarenproyecto.py | Resultado: {'EXITO (0)' if exito else 'FALLO (1)'}")
    sys.exit(0 if exito else 1)