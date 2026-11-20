import sys
import time
import pyautogui
import pytesseract
import pyperclip
import re

# Región central donde aparece el chat de Gemini (x, y, ancho, alto)
REGION_CHAT = (22, 400, 800, 600)

TIMEOUT_MAX = 120       # Tiempo máximo de espera en segundos (2 minutos)
INTERVALO_ESCANEO = 2  # Cada cuántos segundos revisa la pantalla
ESPERA_INICIAL = 4     # Pausa inicial para que el chat anterior suba y no lea el porcentaje viejo

def obtener_porcentaje_pantalla():
    print(f"Esperando respuesta de Gemini (máx. {TIMEOUT_MAX}s)...")
    time.sleep(ESPERA_INICIAL)

    tiempo_inicio = time.time()

    while (time.time() - tiempo_inicio) < TIMEOUT_MAX:
        captura = pyautogui.screenshot(region=REGION_CHAT)
        texto = pytesseract.image_to_string(captura, lang='spa')

        # Usamos findall para tomar siempre la última aparición en pantalla si hay más de una
        coincidencias = re.findall(r"Match\s*total[:\s]*([\d.,]+\s*%)", texto, re.IGNORECASE)
        if coincidencias:
            porcentaje = coincidencias[-1].replace(" ", "").replace(".", ",")
            pyperclip.copy(porcentaje)
            transcurrido = round(time.time() - tiempo_inicio + ESPERA_INICIAL, 1)
            print(f"¡Encontrado en {transcurrido}s! Copiado al portapapeles: {porcentaje}")
            return porcentaje

        time.sleep(INTERVALO_ESCANEO)

    print(f"Error: Tiempo agotado ({TIMEOUT_MAX}s). No se encontró 'Match total' en pantalla.")
    sys.exit(1)

if __name__ == "__main__":
    obtener_porcentaje_pantalla()