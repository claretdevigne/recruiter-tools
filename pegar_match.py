import sys
import pyautogui
import pyperclip
import time

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

COLUMNA_MATCH = "B"

def pegar_en_sheets(fila):
    celda_destino = f"{COLUMNA_MATCH}{fila}"
    valor = pyperclip.paste().strip()

    if not valor or not valor.endswith("%"):
        print(f"Advertencia: El portapapeles no tiene un porcentaje válido ('{valor}'). No se pegará nada.")
        sys.exit(1)

    # 1. Enfocar Brave y cambiar a la Pestaña 1 (Google Sheets)
    pyautogui.press('esc')
    pyautogui.click(x=500, y=200)
    pyautogui.hotkey('ctrl', '1')
    time.sleep(0.3)

    # 2. Ir a la celda A{fila} mediante el Cuadro de Nombres (Ctrl + J)
    pyautogui.hotkey('ctrl', 'j')
    time.sleep(0.2)
    pyautogui.write(celda_destino)
    pyautogui.press('enter')
    time.sleep(0.3)

    # 3. Pegar el porcentaje y confirmar con Enter
    pyautogui.hotkey('ctrl', 'v')
    pyautogui.press('enter')
    pyautogui.press('enter')
    print(f"¡Porcentaje {valor} pegado en {celda_destino}!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python pegar_match.py <numero_de_fila>  (Ejemplo: python pegar_match.py 13)")
        sys.exit(1)

    pegar_en_sheets(sys.argv[1])