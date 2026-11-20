import sys
import time
import pyautogui
import pyperclip

columna_checks = "A"
columna_porcentajes = "B"
columna_links = "C"

# Failsafe: mueve el mouse rápido a la esquina superior izquierda para abortar
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# Coordenada dentro de la ventana de Chrome para enfocarla
X_CHROME = 500
Y_CHROME = 300


def revisar_filas(fila_inicio: int) -> int | None:
    time.sleep(3)

    # 1. Enfocar Chrome e ir a la pestaña 1 (Ctrl + 1)
    pyautogui.click(X_CHROME, Y_CHROME)
    pyautogui.hotkey('ctrl', '1')
    time.sleep(0.5)

    max_filas = 500

    for fila in range(fila_inicio, fila_inicio + max_filas):
        celda_porcentaje = f"{columna_porcentajes}{fila}"

        # 2. Ir directo a la celda de porcentaje (B{fila}) con Ctrl + J
        pyautogui.hotkey('ctrl', 'j')
        time.sleep(0.15)
        pyautogui.write(celda_porcentaje)
        pyautogui.press('enter')
        time.sleep(0.15)

        # 3. Copiar valor de la celda B{fila}
        pyperclip.copy("")
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.15)

        texto = pyperclip.paste().strip()

        # Si la celda de porcentaje está vacía, termina la búsqueda
        if not texto:
            return None

        valor_limpio = texto.replace('%', '').replace(',', '.').strip()

        try:
            numero = float(valor_limpio)

            # Descomenta si copia como decimal (ej. 0.85 en lugar de 85%):
            # if 0 < numero <= 1: numero *= 100

            if numero >= 85:
                # 4. Revisar si A{fila} tiene una "X" o está vacía
                celda_check = f"{columna_checks}{fila}"
                pyautogui.hotkey('ctrl', 'j')
                time.sleep(0.15)
                pyautogui.write(celda_check)
                pyautogui.press('enter')
                time.sleep(0.15)

                pyperclip.copy("")
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.15)

                valor_check = pyperclip.paste().strip().upper()

                # Si está vacía (no hay "X"), devuelve esta fila
                if valor_check == "":
                    return fila
                # Si tiene "X" (o cualquier marca), el ciclo continúa solo

        except ValueError:
            pass

    return None


if __name__ == "__main__":
    # Leer fila inicial desde argv (si no se pasa argumento, empieza en 1)
    fila_inicial = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    fila_encontrada = revisar_filas(fila_inicial)

    if fila_encontrada is not None:
        print(fila_encontrada)
        sys.exit(0)  # Código de salida 0 = éxito
    else:
        print(-1)
        sys.exit(1)  # Código de salida 1 = no encontrado