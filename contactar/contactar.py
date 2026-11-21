import os
import sys
import json
import time
import pyautogui
import pyperclip

# Permitir importar desde la raíz del proyecto para consultar AGENTE_DB si hiciera falta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from googlesheetsapi.functions import listar_hojas_y_pestanas

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

IMG_CONECTAR = os.path.join(BASE_DIR, "1.png")      # Botón directo Conectar
IMG_ANADIR_NOTA = os.path.join(BASE_DIR, "2.png")   # Botón Añadir nota en el modal
IMG_SEGUIR = os.path.join(BASE_DIR, "3.png")        # Botón Seguir
IMG_TRES_PUNTOS = os.path.join(BASE_DIR, "4.png")   # Botón Más / 3 puntos
IMG_CONECTAR_MENU = os.path.join(BASE_DIR, "5.png") # Opción Conectar dentro del desplegable
IMG_ENVIAR = os.path.join(BASE_DIR, "6.png")        # Botón azul "Enviar" del modal


def log(mensaje: str):
    print(mensaje, flush=True)


def obtener_mensaje_agente_db() -> str:
    """
    Obtiene estrictamente el mensaje correspondiente al Role activo en AGENTE_DB.
    Primero revisa el caché local (config_agente.json) y, si está vacío, consulta Google Sheets directamente.
    """
    config_path = os.path.join(ROOT_DIR, "config_agente.json")
    cfg = {}

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            log(f"[Aviso] Error leyendo config_agente.json: {e}")

    hoja_activa = cfg.get("hoja_activa", "")
    role_activo = cfg.get("pestana_activa", "")

    # 1. Intentar leer desde la tabla sincronizada de AGENTE_DB en config_agente.json
    vacantes_cache = cfg.get("hojas", {}).get(hoja_activa, {}).get("vacantes", {})
    mensaje = vacantes_cache.get(role_activo, {}).get("mensaje", "").strip()
    if mensaje:
        return mensaje

    # 2. Respaldo directo: leer mensaje_actual si está presente
    mensaje_actual = cfg.get("mensaje_actual", "").strip()
    if mensaje_actual:
        return mensaje_actual

    # 3. Último recurso: consultar AGENTE_DB en vivo desde Google Sheets
    if hoja_activa and role_activo:
        log(f"[Config] Consultando AGENTE_DB en vivo para '{role_activo}'...")
        try:
            datos_sheets = listar_hojas_y_pestanas()
            mensaje_vivo = (
                datos_sheets.get(hoja_activa, {})
                .get("vacantes", {})
                .get(role_activo, {})
                .get("mensaje", "")
                .strip()
            )
            if mensaje_vivo:
                return mensaje_vivo
        except Exception as e:
            log(f"[Error] No se pudo consultar AGENTE_DB en vivo: {e}")

    return ""


def buscar_imagen(ruta_imagen: str, confianza: float = 0.7):
    try:
        return pyautogui.locateCenterOnScreen(ruta_imagen, confidence=confianza, grayscale=True)
    except Exception:
        return None


# -------------------------------------------------------------------------
# 1.- Alterna cada 5s buscando 1.png (Conectar) y 3.png (Seguir) hasta 120s
# -------------------------------------------------------------------------
def paso_1_detectar_tipo_perfil(tiempo_max: int = 120, intervalo_cambio: int = 5):
    log(f"[Paso 1] INICIO - Alternando cada {intervalo_cambio}s entre '1.png' y '3.png' (máx {tiempo_max}s)...")
    inicio_total = time.time()

    while time.time() - inicio_total < tiempo_max:
        log("[Paso 1] Buscando 1.png (Conectar) por 5s...")
        inicio_turno = time.time()
        while time.time() - inicio_turno < intervalo_cambio and (time.time() - inicio_total < tiempo_max):
            ubicacion_1 = buscar_imagen(IMG_CONECTAR, confianza=0.7)
            if ubicacion_1 is not None:
                log(f"[Paso 1] ÉXITO - 1.png encontrado en ({ubicacion_1.x}, {ubicacion_1.y})")
                return ("conectar_directo", ubicacion_1)
            time.sleep(0.5)

        if time.time() - inicio_total >= tiempo_max:
            break

        log("[Paso 1] No apareció 1.png. Buscando 3.png (Seguir) por 5s...")
        inicio_turno = time.time()
        while time.time() - inicio_turno < intervalo_cambio and (time.time() - inicio_total < tiempo_max):
            ubicacion_3 = buscar_imagen(IMG_SEGUIR, confianza=0.7)
            if ubicacion_3 is not None:
                log(f"[Paso 1] ÉXITO - 3.png encontrado en ({ubicacion_3.x}, {ubicacion_3.y})")
                return ("seguir_menu", ubicacion_3)
            time.sleep(0.5)

    log("[Paso 1] FALLO - Tiempo agotado (120s) sin encontrar 1.png ni 3.png")
    return (None, None)


# -------------------------------------------------------------------------
# 2A.- Camino 1.png: Clic en 1.png -> espera 3s -> busca 2.png (devuelve ubicacion_2)
# -------------------------------------------------------------------------
def flujo_conectar_directo(ubicacion_1, tiempo_max: int = 45):
    log(f"[Flujo 1.png] Haciendo clic en 1.png ({ubicacion_1.x}, {ubicacion_1.y}) y esperando 3s...")
    pyautogui.moveTo(ubicacion_1.x, ubicacion_1.y, duration=0.2)
    pyautogui.click()
    time.sleep(3)

    inicio = time.time()
    intento = 1

    while time.time() - inicio < tiempo_max:
        log(f"[Flujo 1.png] Intento #{intento} buscando 2.png...")
        ubicacion_2 = buscar_imagen(IMG_ANADIR_NOTA, confianza=0.7)

        if ubicacion_2 is not None:
            log(f"[Flujo 1.png] ÉXITO - 2.png encontrado en ({ubicacion_2.x}, {ubicacion_2.y}). Haciendo clic...")
            pyautogui.moveTo(ubicacion_2.x, ubicacion_2.y, duration=0.2)
            pyautogui.click()
            return ubicacion_2

        log("[Flujo 1.png] No se encontró 2.png. Volviendo a hacer clic en 1.png y esperando 3s...")
        nueva_1 = buscar_imagen(IMG_CONECTAR, confianza=0.7)
        objetivo_1 = nueva_1 if nueva_1 is not None else ubicacion_1
        pyautogui.moveTo(objetivo_1.x, objetivo_1.y, duration=0.2)
        pyautogui.click()
        time.sleep(3)
        intento += 1

    log("[Flujo 1.png] FALLO - Tiempo agotado sin encontrar 2.png")
    return None


# -------------------------------------------------------------------------
# 2B.- Camino 3.png: Espera 3s -> busca 4.png -> clic 4.png -> 5.png -> 2.png
# -------------------------------------------------------------------------
def flujo_seguir_menu(tiempo_max: int = 60):
    log("[Flujo 3.png] Esperando 3s antes de buscar 4.png (3 puntos)...")
    time.sleep(3)

    inicio = time.time()
    ubicacion_4 = None

    while time.time() - inicio < tiempo_max:
        ubicacion_4 = buscar_imagen(IMG_TRES_PUNTOS, confianza=0.7)
        if ubicacion_4 is not None:
            log(f"[Flujo 3.png] 4.png encontrado en ({ubicacion_4.x}, {ubicacion_4.y}).")
            break
        log("[Flujo 3.png] No se encontró 4.png. Esperando 2s para buscar de nuevo...")
        time.sleep(2)

    if ubicacion_4 is None:
        log("[Flujo 3.png] FALLO - Tiempo agotado sin encontrar 4.png")
        return None

    log("[Flujo 3.png] Haciendo clic en 4.png y esperando 3s...")
    pyautogui.moveTo(ubicacion_4.x, ubicacion_4.y, duration=0.2)
    pyautogui.click()
    time.sleep(3)

    ubicacion_5 = None
    while time.time() - inicio < tiempo_max:
        ubicacion_5 = buscar_imagen(IMG_CONECTAR_MENU, confianza=0.7)
        if ubicacion_5 is not None:
            log(f"[Flujo 3.png] 5.png encontrado en ({ubicacion_5.x}, {ubicacion_5.y}). Haciendo clic...")
            pyautogui.moveTo(ubicacion_5.x, ubicacion_5.y, duration=0.2)
            pyautogui.click()
            time.sleep(3)
            break

        log("[Flujo 3.png] No se encontró 5.png. Volviendo a hacer clic en 4.png y esperando 3s...")
        nueva_4 = buscar_imagen(IMG_TRES_PUNTOS, confianza=0.7)
        objetivo_4 = nueva_4 if nueva_4 is not None else ubicacion_4
        pyautogui.moveTo(objetivo_4.x, objetivo_4.y, duration=0.2)
        pyautogui.click()
        time.sleep(3)

    if ubicacion_5 is None:
        log("[Flujo 3.png] FALLO - Tiempo agotado sin encontrar 5.png")
        return None

    log("[Flujo 3.png] Buscando 2.png (Añadir nota) tras hacer clic en 5.png...")
    while time.time() - inicio < tiempo_max:
        ubicacion_2 = buscar_imagen(IMG_ANADIR_NOTA, confianza=0.7)
        if ubicacion_2 is not None:
            log(f"[Flujo 3.png] ÉXITO - 2.png encontrado en ({ubicacion_2.x}, {ubicacion_2.y}). Haciendo clic...")
            pyautogui.moveTo(ubicacion_2.x, ubicacion_2.y, duration=0.2)
            pyautogui.click()
            return ubicacion_2

        log("[Flujo 3.png] Aún no aparece 2.png. Esperando 2s...")
        time.sleep(2)

    log("[Flujo 3.png] FALLO - Tiempo agotado sin encontrar 2.png")
    return None


# -------------------------------------------------------------------------
# 3.- Pega el mensaje, verifica que esté dentro del cuadro y hace clic en Enviar (6.png)
# -------------------------------------------------------------------------
def paso_final_pegar_y_enviar(ubicacion_2, mensaje_texto: str, max_intentos_pegado: int = 3) -> bool:
    log("[Paso Final] Esperando 1.5s a que abra el cuadro de texto...")
    time.sleep(1.5)

    x_textarea = ubicacion_2.x
    y_textarea = ubicacion_2.y - 100
    mensaje_esperado = mensaje_texto[:300].strip()

    texto_verificado = False

    for intento in range(1, max_intentos_pegado + 1):
        log(f"[Paso Final] Intento #{intento} de pegado y verificación en ({x_textarea}, {y_textarea})...")
        pyautogui.moveTo(x_textarea, y_textarea, duration=0.2)
        pyautogui.click()
        time.sleep(0.2)

        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyperclip.copy(mensaje_esperado)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)

        pyperclip.copy("")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)

        pyautogui.press('right')

        contenido_actual = pyperclip.paste().strip()

        if contenido_actual == mensaje_esperado:
            log(f"[Paso Final] VERIFICADO - El texto coincide ({len(contenido_actual)} caracteres).")
            texto_verificado = True
            break
        else:
            log(f"[Paso Final] AVISO - El contenido leído no coincide ({len(contenido_actual)} chars). Reintentando...")
            time.sleep(0.5)

    if not texto_verificado:
        log("[Paso Final] FALLO - No se pudo verificar que el texto se pegara. No se enviará.")
        return False

    log("[Paso Final] Buscando botón Enviar (6.png)...")
    inicio = time.time()
    while time.time() - inicio < 10:
        ubicacion_enviar = buscar_imagen(IMG_ENVIAR, confianza=0.7)
        if ubicacion_enviar is not None:
            log(f"[Paso Final] 6.png encontrado en ({ubicacion_enviar.x}, {ubicacion_enviar.y}). Enviando invitación...")
            pyautogui.moveTo(ubicacion_enviar.x, ubicacion_enviar.y, duration=0.2)
            pyautogui.click()
            time.sleep(1.0)
            log("[Paso Final] ÉXITO - Invitación enviada correctamente.")
            return True
        time.sleep(0.5)

    log("[Paso Final] FALLO - No se encontró el botón Enviar (6.png).")
    return False


# -------------------------------------------------------------------------
# Ejecución principal
# -------------------------------------------------------------------------
def main() -> bool:
    log("==========================================")
    log(f"INICIANDO contactar/main.py | Carpeta base: {BASE_DIR}")

    for ruta in (IMG_CONECTAR, IMG_ANADIR_NOTA, IMG_SEGUIR, IMG_TRES_PUNTOS, IMG_CONECTAR_MENU, IMG_ENVIAR):
        if not os.path.exists(ruta):
            log(f"ERROR CRÍTICO: Falta el archivo '{ruta}'")
            return False

    mensaje_activo = obtener_mensaje_agente_db()
    if not mensaje_activo:
        log("ERROR CRÍTICO: No hay ningún mensaje configurado en AGENTE_DB para la pestaña activa. Abortando envío.")
        return False

    log(f"[Config AGENTE_DB] Mensaje cargado ({len(mensaje_activo[:300])} chars): {mensaje_activo[:60]}...")

    tipo_perfil, ubicacion_detectada = paso_1_detectar_tipo_perfil(tiempo_max=120, intervalo_cambio=5)
    if tipo_perfil is None:
        return False

    if tipo_perfil == "conectar_directo":
        ubicacion_2 = flujo_conectar_directo(ubicacion_detectada, tiempo_max=45)
    else:
        ubicacion_2 = flujo_seguir_menu(tiempo_max=60)

    if ubicacion_2 is None:
        return False

    if not paso_final_pegar_y_enviar(ubicacion_2, mensaje_activo):
        return False

    log("==========================================")
    return True


if __name__ == "__main__":
    exito = main()
    log(f"FIN contactar/main.py | Resultado: {'EXITO (0)' if exito else 'FALLO (1)'}")
    sys.exit(0 if exito else 1)