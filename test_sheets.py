import gspread
import os

SHEET_ID = "1IgctcXouhK3QRIO-4LDhf4uTOWV8XuM-M7omzqowF6Y"
NOMBRE_PESTANA = "Full_Stack_Security"
COLUMNA_LINK = "C"
COLUMNA_PORCENTAJE = "P"

def obtener_link(fila):
    ruta_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
    gc = gspread.service_account(filename=ruta_json)
    
    doc = gc.open_by_key(SHEET_ID)
    hoja = doc.worksheet(NOMBRE_PESTANA)
    
    valor = hoja.acell(f"{COLUMNA_LINK}{fila}").value
    print(valor)
    return valor

def escribir_porcentaje(fila, porcentaje):
    ruta_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
    gc = gspread.service_account(filename=ruta_json)
    
    documento = gc.open_by_key(SHEET_ID)
    hoja = documento.worksheet(NOMBRE_PESTANA)
    
    # Escribe el porcentaje en la columna B de esa fila
    valor_a_escribir = "Ola k ase?"
    hoja.update_acell(f"{COLUMNA_PORCENTAJE}{fila}", valor_a_escribir)
    print(f"Escrito '{valor_a_escribir}' en la celda P{fila}")

escribir_porcentaje(1,1)