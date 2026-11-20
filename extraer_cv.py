import sys
import pyautogui
import pyperclip
import time
import os
from pypdf import PdfReader

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

COLUMNA_LINK = "C"
RUTA_PDF = os.path.expanduser("~/Descargas/perfilcv.pdf")
IMG_TRES_PUNTOS = os.path.expanduser("~/Documentos/recruiter/boton.png")
IMG_GUARDAR_PDF = os.path.expanduser("~/Documentos/recruiter/guardarpdf.png")

TIMEOUT_LINKEDIN = 120  # Máximo 120 segundos (2 minutos)
INTERVALO_BUSQUEDA = 5  # Revisar/reintentar cada 5 segundos

def abrir_link_de_celda(celda):
    pyautogui.click(x=500, y=200)
    pyautogui.hotkey('ctrl', '1')
    time.sleep(0.3)

    pyautogui.hotkey('ctrl', 'j')
    time.sleep(0.2)
    pyautogui.write(celda)
    pyautogui.press('enter')
    time.sleep(0.3)
    pyautogui.hotkey('alt', 'enter')
    print(f"Abriendo el enlace de la celda {celda}...", flush=True)

def buscar_imagen_una_vez(ruta_imagen):
    try:
        return pyautogui.locateCenterOnScreen(ruta_imagen, confidence=0.85)
    except pyautogui.ImageNotFoundException:
        return None

def esperar_y_buscar_imagen(ruta_imagen, timeout, intervalo=5, mostrar_progreso=False):
    tiempo_inicio = time.time()
    while (time.time() - tiempo_inicio) < timeout:
        ubicacion = buscar_imagen_una_vez(ruta_imagen)
        if ubicacion:
            return ubicacion
        
        tiempo_transcurrido = int(time.time() - tiempo_inicio)
        tiempo_restante = timeout - (time.time() - tiempo_inicio)
        
        if tiempo_restante > 0:
            if mostrar_progreso:
                print(f"Esperando carga de perfil... ({tiempo_transcurrido}s / {timeout}s)", flush=True)
            time.sleep(min(intervalo, tiempo_restante))
            
    return None

def abrir_menu_y_buscar_pdf(ubicacion_puntos, timeout=120, intervalo=5):
    """Hace clic en el botón y busca 'Guardar en PDF'. Si no aparece, espera 5s y vuelve a hacer clic."""
    tiempo_inicio = time.time()
    while (time.time() - tiempo_inicio) < timeout:
        pyautogui.click(ubicacion_puntos)
        time.sleep(1.0)  # Pequeña pausa para que se despliegue el menú
        
        ubicacion_pdf = buscar_imagen_una_vez(IMG_GUARDAR_PDF)
        if ubicacion_pdf:
            return ubicacion_pdf
            
        tiempo_transcurrido = int(time.time() - tiempo_inicio)
        tiempo_restante = timeout - (time.time() - tiempo_inicio)
        
        if tiempo_restante > 0:
            print(f"Menú aún no responde, reintentando clic en botón... ({tiempo_transcurrido}s / {timeout}s)", flush=True)
            time.sleep(min(intervalo, tiempo_restante))
            
    return None

def limpiar_y_volver():
    """Cierra la pestaña actual y regresa a la pestaña 1."""
    pyautogui.hotkey('ctrl', 'w')
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', '1')
    time.sleep(0.2)

def descargar_y_copiar_cv():
    time.sleep(3)
    print(f"Buscando botón (máx. {TIMEOUT_LINKEDIN}s, revisando cada {INTERVALO_BUSQUEDA}s)...", flush=True)
    
    ubicacion_puntos = esperar_y_buscar_imagen(
        IMG_TRES_PUNTOS, 
        TIMEOUT_LINKEDIN, 
        INTERVALO_BUSQUEDA, 
        mostrar_progreso=True
    )
    if not ubicacion_puntos:
        print(f"Tiempo agotado ({TIMEOUT_LINKEDIN}s). No apareció 'boton.png'. Saltando a la siguiente...", flush=True)
        limpiar_y_volver()
        return False

    print("Botón encontrado. Intentando desplegar menú para 'Guardar en PDF'...", flush=True)
    ubicacion_pdf = abrir_menu_y_buscar_pdf(
        ubicacion_puntos, 
        timeout=TIMEOUT_LINKEDIN, 
        intervalo=INTERVALO_BUSQUEDA
    )
    if not ubicacion_pdf:
        print(f"Tiempo agotado ({TIMEOUT_LINKEDIN}s). No apareció 'Guardar en PDF'. Saltando a la siguiente...", flush=True)
        limpiar_y_volver()
        return False

    pyautogui.click(ubicacion_pdf)
    time.sleep(3)

    if os.path.exists(RUTA_PDF):
        os.remove(RUTA_PDF)

    pyautogui.write("perfilcv")
    pyautogui.press('enter')
    time.sleep(2)

    limpiar_y_volver()

    if os.path.exists(RUTA_PDF):
        reader = PdfReader(RUTA_PDF)
        texto_cv = "\n".join(page.extract_text() for page in reader.pages)
        pyperclip.copy(texto_cv)
        os.remove(RUTA_PDF)
        print(f"CV copiado ({len(texto_cv)} caracteres) y perfilcv.pdf eliminado.", flush=True)
        return True
    else:
        print("Error: No se encontró perfilcv.pdf en Descargas.", flush=True)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python extraer_cv.py <numero_de_fila>")
        sys.exit(1)

    celda_objetivo = f"{COLUMNA_LINK}{sys.argv[1]}"
    abrir_link_de_celda(celda_objetivo)
    
    if not descargar_y_copiar_cv():
        sys.exit(1)