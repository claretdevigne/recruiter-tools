import sys
import time
import pyautogui

# Failsafe: mueve el mouse rápido a la esquina superior izquierda para abortar
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

columna_links = "C"


def abrir_hipervinculo(fila: int) -> bool:
    if fila <= 0:
        print("Número de fila inválido.", file=sys.stderr)
        return False

    celda = f"{columna_links}{fila}"

    # 1. Saltar directo a C{fila} con Ctrl + J
    pyautogui.hotkey('ctrl', 'j')
    time.sleep(0.15)
    pyautogui.write(celda)
    pyautogui.press('enter')
    time.sleep(0.25)

    # 2. Abrir el hipervínculo de la celda seleccionada (Alt + Enter en Google Sheets)
    pyautogui.hotkey('alt', 'enter')
    time.sleep(1.0)  # Espera 1 segundo a que Chrome abra y enfoque la nueva pestaña

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python abrir_link.py <numero_fila>", file=sys.stderr)
        sys.exit(1)

    try:
        fila_objetivo = int(sys.argv[1])
    except ValueError:
        print("La fila debe ser un número entero.", file=sys.stderr)
        sys.exit(1)

    if abrir_hipervinculo(fila_objetivo):
        sys.exit(0)
    else:
        sys.exit(1)