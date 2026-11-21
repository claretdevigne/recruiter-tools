import gspread
import os

SHEET_ID = "1IgctcXouhK3QRIO-4LDhf4uTOWV8XuM-M7omzqowF6Y"
NOMBRE_PESTANA = "Full_Stack_Security"
COLUMNA_LINK = "C"
COLUMNA_PORCENTAJE = "P"

def configurar(SHEET_ID, NOMBRE_PESTANA):
    ruta_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
    gc = gspread.service_account(filename=ruta_json)
    doc = gc.open_by_key(SHEET_ID)
    hoja = doc.worksheet(NOMBRE_PESTANA)
    return hoja

def leer_celda(celda):
    hoja = configurar(SHEET_ID, NOMBRE_PESTANA)
    valor = hoja.acell(celda).value
    return valor

def actualizar_celda(celda, valor):
    hoja = configurar(SHEET_ID, NOMBRE_PESTANA)    
    hoja.update_acell(celda, valor)
    print(f"Se escribió {valor} en {celda}")