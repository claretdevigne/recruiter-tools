import sys
import pyautogui
import pyperclip
import time
import os
from pypdf import PdfReader

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

# --- CONFIGURACIÓN ---
COLUMNA_LINK = "B"
RUTA_PDF = os.path.expanduser("~/Descargas/perfilcv.pdf")
IMG_TRES_PUNTOS = os.path.expanduser("~/Documentos/recruiter/boton.png")
IMG_GUARDAR_PDF = os.path.expanduser("~/Documentos/recruiter/guardarpdf.png")

X_CHAT_GEMINI = 382
Y_CHAT_GEMINI = 737

TIMEOUT_LINKEDIN = 240  # Máximo 4 minutos de espera
INTERVALO_BUSQUEDA = 2  # Revisar pantalla cada 2 segundos

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
    print(f"Abriendo el enlace de la celda {celda}...")

def esperar_y_buscar_imagen(ruta_imagen, timeout, intervalo=2):
    """Busca una imagen en pantalla repetidamente hasta encontrarla o agotar el tiempo."""
    tiempo_inicio = time.time()
    while (time.time() - tiempo_inicio) < timeout:
        try:
            ubicacion = pyautogui.locateCenterOnScreen(ruta_imagen, confidence=0.85)
            if ubicacion:
                return ubicacion
        except pyautogui.ImageNotFoundException:
            # En versiones recientes de PyAutoGUI/PyScreeze lanza excepción en vez de devolver None
            pass
        time.sleep(intervalo)
    return None

def descargar_pdf_linkedin():
    # Pausa inicial breve mientras se abre la pestaña nueva
    time.sleep(3)
    print(f"Esperando a que cargue LinkedIn y aparezca el botón '...' (máx. {TIMEOUT_LINKEDIN}s)...")
    
    # 1. Esperar dinámicamente hasta encontrar el botón "..."
    ubicacion_puntos = esperar_y_buscar_imagen(IMG_TRES_PUNTOS, TIMEOUT_LINKEDIN, INTERVALO_BUSQUEDA)
    if not ubicacion_puntos:
        print(f"Error: Tiempo agotado ({TIMEOUT_LINKEDIN}s). No se encontró el botón '...' en pantalla.")
        return False

    print("¡Botón '...' detectado! Abriendo menú...")
    pyautogui.click(ubicacion_puntos)
    time.sleep(0.8)

    # 2. Buscar visualmente la opción "Guardar en PDF" (con 10s de margen por si el menú tarda un poco en desplegarse)
    ubicacion_pdf = esperar_y_buscar_imagen(IMG_GUARDAR_PDF, timeout=10, intervalo=0.5)
    if not ubicacion_pdf:
        print("No se encontró el botón 'Guardar en PDF' en el menú.")
        return False

    pyautogui.click(ubicacion_pdf)
    time.sleep(3)

    if os.path.exists(RUTA_PDF):
        os.remove(RUTA_PDF)

    pyautogui.write("perfilcv")
    pyautogui.press('enter')
    time.sleep(2)

    # Cierra la pestaña de LinkedIn
    pyautogui.hotkey('ctrl', 'w')

    if os.path.exists(RUTA_PDF):
        reader = PdfReader(RUTA_PDF)
        texto_cv = "\n".join(page.extract_text() for page in reader.pages)
        pyperclip.copy(texto_cv)
        os.remove(RUTA_PDF)
        print(f"CV copiado ({len(texto_cv)} caracteres) y perfilcv.pdf eliminado.")
        return True
    else:
        print("Error: No se encontró perfilcv.pdf en Descargas.")
        return False

def enviar_a_gemini():
    pyautogui.hotkey('ctrl', '2')
    time.sleep(0.3)
    pyautogui.click(x=X_CHAT_GEMINI, y=Y_CHAT_GEMINI)
    time.sleep(0.3)

    pyautogui.write("@cvmatch ", interval=0.03)
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    pyautogui.press('enter')
    print("¡Petición enviada a Gemini!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python app.py <numero_de_fila>  (Ejemplo: python app.py 13)")
        sys.exit(1)

    fila = sys.argv[1]
    celda_objetivo = f"{COLUMNA_LINK}{fila}"

    abrir_link_de_celda(celda_objetivo)
    if descargar_pdf_linkedin():
        enviar_a_gemini()
    else:
        # Salir con código 1 para avisar a run.py que esta fila falló y pase a la siguiente
        sys.exit(1)