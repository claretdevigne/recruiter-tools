import sys
import os
from googlesheetsapi.functions import actualizar_celda

# Configuración de la columna de control (debe coincidir con encontrar_viable.py)
COLUMNA_CHECK = "A"
VALOR_MARCA = "X"


def main():
    if len(sys.argv) < 2:
        print("Error: Se requiere el número de fila como argumento.", file=sys.stderr)
        sys.exit(1)

    try:
        fila = int(sys.argv[1])
    except ValueError:
        print(f"Error: El argumento '{sys.argv[1]}' no es un número de fila válido.", file=sys.stderr)
        sys.exit(1)

    celda_objetivo = f"{COLUMNA_CHECK}{fila}"

    try:
        actualizar_celda(celda_objetivo, VALOR_MARCA)
        print(f"Base de datos actualizada: '{VALOR_MARCA}' escrita en {celda_objetivo}.", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"Error al actualizar la celda {celda_objetivo}: {e}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()