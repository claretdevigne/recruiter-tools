import sys
import os
import gspread

SHEET_ID = "1IgctcXouhK3QRIO-4LDhf4uTOWV8XuM-M7omzqowF6Y"
NOMBRE_PESTANA = "Full_Stack_Security"
UMBRAL_MATCH = 85.0

# Índices de columna en base 0 (A=0, B=1, C=2...)
IDX_CHECK = 0       # Columna A
IDX_PORCENTAJE = 1  # Columna B
# IDX_LINK = 2      # Columna C


def revisar_filas(fila_inicio: int) -> int | None:
    ruta_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
    gc = gspread.service_account(filename=ruta_json)

    doc = gc.open_by_key(SHEET_ID)
    hoja = doc.worksheet(NOMBRE_PESTANA)

    # Descarga toda la tabla en una sola petición (evita cientos de llamadas individuales)
    todas_las_filas = hoja.get_all_values()

    max_filas = 500
    limite_superior = min(len(todas_las_filas), fila_inicio - 1 + max_filas)

    # Iterar desde fila_inicio (ajustando índice 1-based de Sheets a 0-based de Python)
    for idx in range(fila_inicio - 1, limite_superior):
        fila_actual = todas_las_filas[idx]
        numero_fila_sheet = idx + 1

        # Obtener valor de porcentaje (Columna B) de forma segura
        texto_pct = fila_actual[IDX_PORCENTAJE].strip() if len(fila_actual) > IDX_PORCENTAJE else ""

        # Si la celda de porcentaje está vacía, termina la búsqueda (misma lógica original)
        if not texto_pct:
            return None

        valor_limpio = texto_pct.replace("%", "").replace(",", ".").strip()

        try:
            numero = float(valor_limpio)

            # Descomenta si se guarda como decimal (ej. 0.85 en lugar de 85%):
            # if 0 < numero <= 1: numero *= 100

            if numero >= UMBRAL_MATCH:
                # Revisar si la columna A (Check) está vacía
                valor_check = fila_actual[IDX_CHECK].strip().upper() if len(fila_actual) > IDX_CHECK else ""

                if valor_check == "":
                    return numero_fila_sheet

        except ValueError:
            # Ignora encabezados o celdas con texto no numérico (ej. "N/A")
            continue

    return None


if __name__ == "__main__":
    fila_inicial = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    fila_encontrada = revisar_filas(fila_inicial)

    if fila_encontrada is not None:
        print(fila_encontrada)
        sys.exit(0)  # Código de salida 0 = éxito
    else:
        print(-1)
        sys.exit(1)  # Código de salida 1 = no encontrado