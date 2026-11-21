import sys
import time
import webbrowser
from googlesheetsapi.functions import leer_celda

columna_links = "C"

def abrir_hipervinculo(fila: int) -> bool:
    link = leer_celda(f"{columna_links}{fila}")
    print(f"Abriendo link: {link}")
    webbrowser.open_new_tab(link)
    time.sleep(1.0)
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