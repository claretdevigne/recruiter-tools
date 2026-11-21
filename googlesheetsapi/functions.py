import gspread
import os
import json

DEFAULT_SHEET_ID = "1IgctcXouhK3QRIO-4LDhf4uTOWV8XuM-M7omzqowF6Y"
DEFAULT_PESTANA = "Full_Stack_Security"
PESTANA_DB = "AGENTE_DB"
COLUMNA_LINK = "C"
COLUMNA_PORCENTAJE = "P"


def _obtener_gc():
    ruta_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
    return gspread.service_account(filename=ruta_json)


def obtener_contexto_activo():
    """Lee la configuración activa guardada por la GUI en config_agente.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config_agente.json")

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            hoja_activa = cfg.get("hoja_activa", "")
            pestana_activa = cfg.get("pestana_activa", "")
            sheet_id = cfg.get("hojas", {}).get(hoja_activa, {}).get("spreadsheet_id", "")
            if sheet_id and pestana_activa:
                return sheet_id, pestana_activa
        except Exception:
            pass

    return DEFAULT_SHEET_ID, DEFAULT_PESTANA


def listar_hojas_y_pestanas():
    """
    Consulta todas las hojas compartidas, sus pestañas de candidatos (excluyendo AGENTE_DB)
    y la configuración de vacantes almacenada en AGENTE_DB si existe.
    """
    gc = _obtener_gc()
    archivos = gc.openall()
    resultado = {}

    for doc in archivos:
        try:
            todas_ws = doc.worksheets()
            nombres_ws = [ws.title for ws in todas_ws]
            pestanas_candidatos = [t for t in nombres_ws if t != PESTANA_DB]

            vacantes_db = {}
            if PESTANA_DB in nombres_ws:
                ws_db = doc.worksheet(PESTANA_DB)
                filas = ws_db.get_all_values()
                # Saltar fila 1 (encabezados: Role | JD | Mensaje | Nombre proyecto)
                for idx, fila in enumerate(filas[1:], start=2):
                    role = fila[0].strip() if len(fila) > 0 else ""
                    if role:
                        vacantes_db[role] = {
                            "fila": idx,
                            "jd": fila[1] if len(fila) > 1 else "",
                            "mensaje": fila[2] if len(fila) > 2 else "",
                            "proyecto": fila[3] if len(fila) > 3 else ""
                        }

            resultado[doc.title] = {
                "spreadsheet_id": doc.id,
                "pestanas": pestanas_candidatos,
                "vacantes": vacantes_db
            }
        except Exception:
            continue

    return resultado


def guardar_vacante_en_sheet(sheet_id, role, jd, mensaje, proyecto):
    """Actualiza la fila del Role en AGENTE_DB o agrega una nueva si no existe."""
    gc = _obtener_gc()
    doc = gc.open_by_key(sheet_id)

    try:
        ws_db = doc.worksheet(PESTANA_DB)
    except gspread.WorksheetNotFound:
        ws_db = doc.add_worksheet(title=PESTANA_DB, rows=100, cols=4)
        ws_db.update("A1:D1", [["Role", "JD", "Mensaje", "Nombre proyecto (recruiter)"]])

    filas = ws_db.get_all_values()
    fila_objetivo = None
    for idx, fila in enumerate(filas[1:], start=2):
        if len(fila) > 0 and fila[0].strip() == role.strip():
            fila_objetivo = idx
            break

    valores = [[role, jd, mensaje, proyecto]]
    if fila_objetivo:
        ws_db.update(f"A{fila_objetivo}:D{fila_objetivo}", valores)
    else:
        fila_objetivo = len(filas) + 1
        ws_db.update(f"A{fila_objetivo}:D{fila_objetivo}", valores)

    return fila_objetivo


def configurar(sheet_id=None, nombre_pestana=None):
    if not sheet_id or not nombre_pestana:
        sheet_id, nombre_pestana = obtener_contexto_activo()
    gc = _obtener_gc()
    doc = gc.open_by_key(sheet_id)
    return doc.worksheet(nombre_pestana)


def leer_celda(celda, sheet_id=None, nombre_pestana=None):
    hoja = configurar(sheet_id, nombre_pestana)
    return hoja.acell(celda).value


def actualizar_celda(celda, valor, sheet_id=None, nombre_pestana=None):
    hoja = configurar(sheet_id, nombre_pestana)
    hoja.update_acell(celda, valor)
    print(f"Se escribió {valor} en {celda}")

def leer_toda_la_pestana(sheet_id=None, nombre_pestana=None):
    """Devuelve todas las filas de la pestaña seleccionada como una lista de listas."""
    hoja = configurar(sheet_id, nombre_pestana)
    return hoja.get_all_values()