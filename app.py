import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import webbrowser
import sys
import os
import json
import signal

from googlesheetsapi.functions import (
    listar_hojas_y_pestanas,
    guardar_vacante_en_sheet,
    leer_toda_la_pestana
)


class AgenteReclutamientoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Agente de Reclutamiento")
        self.root.geometry("760x700")
        self.root.resizable(True, True)
        self.proceso = None

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, "config_agente.json")
        self.config = self.cargar_config()

        self.root.protocol("WM_DELETE_WINDOW", self.al_cerrar)

        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 6])
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=24)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

        # ==========================================
        # BARRA SUPERIOR: ORIGEN DE DATOS AUTOMÁTICO
        # ==========================================
        frame_top = ttk.LabelFrame(root, text=" 📊 Origen de Datos (Google Sheets Automático) ", padding="10 8")
        frame_top.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(frame_top, text="Hoja:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.combo_hojas = ttk.Combobox(frame_top, state="readonly", width=28, font=("Segoe UI", 9))
        self.combo_hojas.grid(row=0, column=1, padx=(0, 10))
        self.combo_hojas.bind("<<ComboboxSelected>>", self.al_cambiar_hoja)

        ttk.Label(frame_top, text="Pestaña (Role):", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.combo_pestanas = ttk.Combobox(frame_top, state="readonly", width=22, font=("Segoe UI", 9))
        self.combo_pestanas.grid(row=0, column=3, padx=(0, 10))
        self.combo_pestanas.bind("<<ComboboxSelected>>", self.al_cambiar_pestana)

        self.btn_sync = tk.Button(
            frame_top, text="🔄 Sincronizar", font=("Segoe UI", 9, "bold"), bg="#dbeafe", fg="#1e40af",
            relief="flat", padx=10, pady=2, cursor="hand2", command=self.sincronizar_sheets_async
        )
        self.btn_sync.grid(row=0, column=4, sticky="e")

        self.lbl_sheet_id = ttk.Label(frame_top, text="ID: Esperando sincronización...", font=("Consolas", 8), foreground="#6b7280")
        self.lbl_sheet_id.grid(row=1, column=0, columnspan=5, sticky="w", pady=(5, 0))

        # ==========================================
        # CONTENEDOR PRINCIPAL DE PESTAÑAS
        # ==========================================
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        self.notebook.bind("<<NotebookTabChanged>>", self.al_cambiar_tab_ui)

        self.tab_analisis = ttk.Frame(self.notebook, padding=15)
        self.tab_contacto = ttk.Frame(self.notebook, padding=15)
        self.tab_jd = ttk.Frame(self.notebook, padding=15)
        self.tab_sheet = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_analisis, text="1. Evaluación de CVs")
        self.notebook.add(self.tab_contacto, text="2. Outreach y Recruiter")
        self.notebook.add(self.tab_jd, text="3. Vacante, JD y Mensaje")
        self.notebook.add(self.tab_sheet, text="4. Vista de Hoja")

        self.construir_tab_analisis()
        self.construir_tab_contacto()
        self.construir_tab_jd()
        self.construir_tab_sheet()

        # ==========================================
        # CONSOLA DE PROGRESO COMPARTIDA
        # ==========================================
        frame_log = ttk.Frame(root, padding="10 0 10 10")
        frame_log.pack(fill="both", expand=False)

        ttk.Label(frame_log, text="Registro de actividad del agente:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.log_area = scrolledtext.ScrolledText(
            frame_log, height=8, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4", state="disabled"
        )
        self.log_area.pack(fill="both", expand=True)

        # Cargar caché local y lanzar búsqueda automática en Google Sheets
        self.refrescar_combos_desde_config()
        self.sincronizar_sheets_async()

    # ==========================================
    # GESTIÓN DE CONFIGURACIÓN Y SINCRONIZACIÓN
    # ==========================================
    def cargar_config(self):
        default_config = {
            "hoja_activa": "",
            "pestana_activa": "",
            "hojas": {},
            "proyecto_recruiter": "",
            "jd_actual": "",
            "mensaje_actual": "",
            "ana_inicio": "1",
            "ana_fin": "",
            "con_inicio": "1",
            "con_fin": "",
            "con_min_pct": "80"
        }
        if not os.path.exists(self.config_path):
            return default_config
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_config.update(data)
                return default_config
        except Exception:
            return default_config

    def persistir_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def sincronizar_sheets_async(self):
        self.btn_sync.config(state="disabled", text="⏳ Buscando...")
        self.lbl_sheet_id.config(text="Consultando Google Sheets y AGENTE_DB...")
        hilo = threading.Thread(target=self._tarea_sincronizar, daemon=True)
        hilo.start()

    def _tarea_sincronizar(self):
        try:
            hojas_encontradas = listar_hojas_y_pestanas()
            self.root.after(0, self._finalizar_sincronizacion, hojas_encontradas, None)
        except Exception as e:
            self.root.after(0, self._finalizar_sincronizacion, None, str(e))

    def _finalizar_sincronizacion(self, hojas_encontradas, error):
        self.btn_sync.config(state="normal", text="🔄 Sincronizar")
        if error:
            self.lbl_sheet_id.config(text="Error al conectar con Google Sheets")
            self.escribir_log(f"❌ Error sincronizando Sheets: {error}\n")
            return

        if not hojas_encontradas:
            self.lbl_sheet_id.config(text="0 hojas encontradas (verifica permisos del credentials.json)")
            self.escribir_log("⚠️ No se encontraron hojas. Verifica permisos en Google Drive.\n")
            return

        self.config["hojas"] = hojas_encontradas
        self.persistir_config()
        self.refrescar_combos_desde_config()
        self.escribir_log(f"✅ Sincronización completa: {len(hojas_encontradas)} hoja(s) cargada(s).\n")

    def refrescar_combos_desde_config(self):
        hojas = self.config.get("hojas", {})
        nombres = list(hojas.keys())
        self.combo_hojas["values"] = nombres

        if not nombres:
            self.combo_hojas.set("")
            self.combo_pestanas["values"] = []
            self.combo_pestanas.set("")
            return

        activa = self.config.get("hoja_activa", "")
        if activa in nombres:
            self.combo_hojas.set(activa)
        else:
            self.combo_hojas.current(0)

        self.al_cambiar_hoja()

    def al_cambiar_hoja(self, event=None):
        nombre = self.combo_hojas.get()
        datos = self.config.get("hojas", {}).get(nombre, {})
        sheet_id = datos.get("spreadsheet_id", "")
        pestanas = datos.get("pestanas", [])

        self.lbl_sheet_id.config(text=f"ID: {sheet_id}")
        self.combo_pestanas["values"] = pestanas

        pestana_guardada = self.config.get("pestana_activa", "")
        if pestana_guardada in pestanas:
            self.combo_pestanas.set(pestana_guardada)
        elif pestanas:
            self.combo_pestanas.current(0)
        else:
            self.combo_pestanas.set("")

        self.al_cambiar_pestana()

    def al_cambiar_pestana(self, event=None):
        hoja = self.combo_hojas.get()
        role = self.combo_pestanas.get()
        self.config["hoja_activa"] = hoja
        self.config["pestana_activa"] = role

        vacantes = self.config.get("hojas", {}).get(hoja, {}).get("vacantes", {})
        info_vacante = vacantes.get(role, {})

        jd = info_vacante.get("jd", "")
        mensaje = info_vacante.get("mensaje", "")
        proyecto = info_vacante.get("proyecto", "")

        self.config["jd_actual"] = jd
        self.config["mensaje_actual"] = mensaje
        self.config["proyecto_recruiter"] = proyecto
        self.persistir_config()

        self.lbl_role_activo.config(text=f"Role (Pestaña): {role or '-'}")
        self.entry_proyecto.delete(0, tk.END)
        self.entry_proyecto.insert(0, proyecto)

        self.txt_jd.delete("1.0", tk.END)
        self.txt_jd.insert("1.0", jd)

        self.txt_mensaje.delete("1.0", tk.END)
        self.txt_mensaje.insert("1.0", mensaje)
        self.actualizar_contador_mensaje()

        if info_vacante:
            self.escribir_log(f"📋 Configuración cargada desde AGENTE_DB para '{role}' (Proyecto: {proyecto}).\n")
        elif role:
            self.escribir_log(f"ℹ️ '{role}' aún no tiene registro en AGENTE_DB. Puedes completarlo en la Pestaña 3.\n")

        # Si el usuario tiene abierta la pestaña 4 (Vista de Hoja), refrescar automáticamente
        if self.notebook.index(self.notebook.select()) == 3:
            self.cargar_vista_hoja_async()

    def al_cambiar_tab_ui(self, event=None):
        # Al entrar a la Pestaña 4 (índice 3), cargar los datos de la hoja seleccionada
        if self.notebook.index(self.notebook.select()) == 3:
            self.cargar_vista_hoja_async()

    # ==========================================
    # PESTAÑA 1: EVALUACIÓN DE CVs (run.py)
    # ==========================================
    def construir_tab_analisis(self):
        desc = ttk.Label(
            self.tab_analisis,
            text="Lee links (Col C), descarga CV en PDF, evalúa match vs JD activa y guarda % en Col B.",
            font=("Segoe UI", 9), foreground="#4b5563"
        )
        desc.pack(anchor="w", pady=(0, 12))

        frame_inputs = ttk.Frame(self.tab_analisis)
        frame_inputs.pack(fill="x", pady=(0, 15))

        ttk.Label(frame_inputs, text="Fila inicial:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.ana_inicio = ttk.Entry(frame_inputs, width=10, font=("Segoe UI", 11))
        self.ana_inicio.grid(row=0, column=1, padx=(0, 25))
        self.ana_inicio.insert(0, self.config.get("ana_inicio", "1"))

        ttk.Label(frame_inputs, text="Fila final:", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=(0, 5), sticky="w")
        self.ana_fin = ttk.Entry(frame_inputs, width=10, font=("Segoe UI", 11))
        self.ana_fin.grid(row=0, column=3)
        self.ana_fin.insert(0, self.config.get("ana_fin", ""))

        frame_btns = ttk.Frame(self.tab_analisis)
        frame_btns.pack(fill="x")

        self.btn_iniciar_ana = tk.Button(
            frame_btns, text="▶ Evaluar CVs con JD Activa", bg="#2563eb", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8,
            cursor="hand2", command=self.lanzar_analisis
        )
        self.btn_iniciar_ana.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_detener_ana = tk.Button(
            frame_btns, text="⏹ Detener", bg="#dc2626", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8,
            cursor="hand2", state="disabled", command=self.detener_proceso
        )
        self.btn_detener_ana.pack(side="right", expand=True, fill="x", padx=(5, 0))

    # ==========================================
    # PESTAÑA 2: OUTREACH Y RECRUITER (contactar/main.py)
    # ==========================================
    def construir_tab_contacto(self):
        desc = ttk.Label(
            self.tab_contacto,
            text="Filtra Col B ≥ Match mín (y Col A vacía) → Contacta con nota, guarda en proyecto y marca Col A.",
            font=("Segoe UI", 9), foreground="#4b5563"
        )
        desc.pack(anchor="w", pady=(0, 12))

        frame_inputs = ttk.Frame(self.tab_contacto)
        frame_inputs.pack(fill="x", pady=(0, 15))

        ttk.Label(frame_inputs, text="Fila inicial:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.con_inicio = ttk.Entry(frame_inputs, width=7, font=("Segoe UI", 11))
        self.con_inicio.grid(row=0, column=1, padx=(0, 12))
        self.con_inicio.insert(0, self.config.get("con_inicio", "1"))

        ttk.Label(frame_inputs, text="Fila final:", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=(0, 5), sticky="w")
        self.con_fin = ttk.Entry(frame_inputs, width=7, font=("Segoe UI", 11))
        self.con_fin.grid(row=0, column=3, padx=(0, 12))
        self.con_fin.insert(0, self.config.get("con_fin", ""))

        ttk.Label(frame_inputs, text="Match mín (%):", font=("Segoe UI", 10, "bold")).grid(row=0, column=4, padx=(0, 5), sticky="w")
        self.con_min_pct = ttk.Entry(frame_inputs, width=6, font=("Segoe UI", 11))
        self.con_min_pct.grid(row=0, column=5)
        self.con_min_pct.insert(0, self.config.get("con_min_pct", "80"))

        frame_btns = ttk.Frame(self.tab_contacto)
        frame_btns.pack(fill="x")

        self.btn_iniciar_con = tk.Button(
            frame_btns, text="🚀 Iniciar Contacto y Guardado", bg="#059669", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8,
            cursor="hand2", command=self.lanzar_contacto
        )
        self.btn_iniciar_con.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_detener_con = tk.Button(
            frame_btns, text="⏹ Detener", bg="#dc2626", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8,
            cursor="hand2", state="disabled", command=self.detener_proceso
        )
        self.btn_detener_con.pack(side="right", expand=True, fill="x", padx=(5, 0))

    # ==========================================
    # PESTAÑA 3: VACANTE, JD Y MENSAJE (AGENTE_DB)
    # ==========================================
    def construir_tab_jd(self):
        frame_top_jd = ttk.Frame(self.tab_jd)
        frame_top_jd.pack(fill="x", pady=(0, 6))

        self.lbl_role_activo = ttk.Label(frame_top_jd, text="Role (Pestaña): -", font=("Segoe UI", 9, "bold"), foreground="#1d4ed8")
        self.lbl_role_activo.pack(side="left", padx=(0, 15))

        ttk.Label(frame_top_jd, text="Proyecto Recruiter:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))
        self.entry_proyecto = ttk.Entry(frame_top_jd, font=("Segoe UI", 9))
        self.entry_proyecto.pack(side="left", fill="x", expand=True)

        ttk.Label(self.tab_jd, text="Job Description (Col B):", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.txt_jd = scrolledtext.ScrolledText(self.tab_jd, height=5, font=("Segoe UI", 9), wrap="word")
        self.txt_jd.pack(fill="both", expand=True, pady=(2, 6))

        frame_lbl_msg = ttk.Frame(self.tab_jd)
        frame_lbl_msg.pack(fill="x")
        ttk.Label(frame_lbl_msg, text="Mensaje de LinkedIn (Col C):", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.lbl_chars_msg = ttk.Label(frame_lbl_msg, text="0 / 300 caracteres", font=("Segoe UI", 8), foreground="#6b7280")
        self.lbl_chars_msg.pack(side="right")

        self.txt_mensaje = scrolledtext.ScrolledText(self.tab_jd, height=3, font=("Segoe UI", 9), wrap="word")
        self.txt_mensaje.pack(fill="x", pady=(2, 8))
        self.txt_mensaje.bind("<KeyRelease>", self.actualizar_contador_mensaje)

        self.btn_guardar_jd = tk.Button(
            self.tab_jd, text="☁️ Guardar en AGENTE_DB y Local", bg="#4f46e5", fg="white",
            font=("Segoe UI", 9, "bold"), relief="flat", pady=6,
            cursor="hand2", command=self.guardar_vacante_async
        )
        self.btn_guardar_jd.pack(fill="x")

    # ==========================================
    # PESTAÑA 4: VISTA DE HOJA (COMO GOOGLE SHEETS)
    # ==========================================
    def construir_tab_sheet(self):
        barra = ttk.Frame(self.tab_sheet)
        barra.pack(fill="x", pady=(0, 6))

        self.lbl_info_tabla = ttk.Label(
            barra, text="Doble clic en una fila abre el perfil en LinkedIn.",
            font=("Segoe UI", 8), foreground="#4b5563"
        )
        self.lbl_info_tabla.pack(side="left")

        self.btn_refrescar_tabla = tk.Button(
            barra, text="🔄 Refrescar vista", font=("Segoe UI", 8, "bold"),
            bg="#e0e7ff", fg="#1e3a8a", relief="flat", padx=8, pady=2,
            cursor="hand2", command=self.cargar_vista_hoja_async
        )
        self.btn_refrescar_tabla.pack(side="right")

        # Contenedor con scrollbars vertical y horizontal
        cont_tabla = ttk.Frame(self.tab_sheet)
        cont_tabla.pack(fill="both", expand=True)

        scroll_y = ttk.Scrollbar(cont_tabla, orient="vertical")
        scroll_x = ttk.Scrollbar(cont_tabla, orient="horizontal")

        self.tree_sheet = ttk.Treeview(
            cont_tabla, show="headings",
            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set
        )
        scroll_y.config(command=self.tree_sheet.yview)
        scroll_x.config(command=self.tree_sheet.xview)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree_sheet.pack(side="left", fill="both", expand=True)

        # Colores tipo hoja de cálculo según estado
        self.tree_sheet.tag_configure("contactado", background="#dbeafe")  # Azul claro (Col A con dato)
        self.tree_sheet.tag_configure("alto_match", background="#dcfce7")  # Verde claro (Col B >= Match mín)
        self.tree_sheet.tag_configure("par", background="#f9fafb")

        self.tree_sheet.bind("<Double-1>", self.abrir_link_de_fila)

    def cargar_vista_hoja_async(self):
        sheet_id, pestana = self.obtener_datos_hoja_activa(silencioso=True)
        if not sheet_id or not pestana:
            return

        self.btn_refrescar_tabla.config(state="disabled", text="⏳ Cargando...")
        self.lbl_info_tabla.config(text=f"Cargando '{pestana}'...")
        hilo = threading.Thread(
            target=self._tarea_cargar_vista_hoja,
            args=(sheet_id, pestana),
            daemon=True
        )
        hilo.start()

    def _tarea_cargar_vista_hoja(self, sheet_id, pestana):
        try:
            filas = leer_toda_la_pestana(sheet_id, pestana)
            self.root.after(0, self._renderizar_tabla_sheet, filas, pestana, None)
        except Exception as e:
            self.root.after(0, self._renderizar_tabla_sheet, None, pestana, str(e))

    def _renderizar_tabla_sheet(self, filas, pestana, error):
        self.btn_refrescar_tabla.config(state="normal", text="🔄 Refrescar vista")
        if error:
            self.lbl_info_tabla.config(text=f"Error al cargar '{pestana}'")
            self.escribir_log(f"❌ Error cargando vista de hoja: {error}\n")
            return

        # Limpiar tabla actual
        self.tree_sheet.delete(*self.tree_sheet.get_children())

        if not filas:
            self.lbl_info_tabla.config(text=f"La pestaña '{pestana}' está vacía.")
            return

        max_cols = max(len(f) for f in filas)
        letras_cols = [self._indice_a_letra_col(i) for i in range(max_cols)]
        columnas = ["Fila"] + letras_cols
        self.tree_sheet["columns"] = columnas

        # Configurar columna fija de número de fila
        self.tree_sheet.heading("Fila", text="#")
        self.tree_sheet.column("Fila", width=45, minwidth=40, anchor="center", stretch=False)

        # Usar fila 1 como referencia de encabezado si tiene texto
        fila_1 = filas[0]
        anchos_sugeridos = {"A": 95, "B": 75, "C": 210, "D": 180}

        for idx, letra in enumerate(letras_cols):
            titulo_col = fila_1[idx].strip() if idx < len(fila_1) and fila_1[idx].strip() else ""
            encabezado = f"{letra} ({titulo_col})" if titulo_col else letra
            self.tree_sheet.heading(letra, text=encabezado, anchor="w")
            ancho = anchos_sugeridos.get(letra, 130)
            self.tree_sheet.column(letra, width=ancho, minwidth=65, anchor="w", stretch=False)

        try:
            min_pct = int(self.con_min_pct.get().strip() or 80)
        except ValueError:
            min_pct = 80

        # Renderizar todas las filas desde la 1 para que los índices coincidan 1:1 con Google Sheets
        for num_fila, fila in enumerate(filas, start=1):
            fila_rellena = fila + [""] * (max_cols - len(fila))
            valores = [num_fila] + fila_rellena

            col_a = fila_rellena[0].strip() if max_cols > 0 else ""
            col_b = fila_rellena[1].strip().replace("%", "") if max_cols > 1 else ""

            tag = "par" if num_fila % 2 == 0 else ""
            if col_a and num_fila > 1:
                tag = "contactado"
            elif col_b.isdigit() and int(col_b) >= min_pct:
                tag = "alto_match"

            self.tree_sheet.insert("", "end", values=valores, tags=(tag,) if tag else ())

        self.lbl_info_tabla.config(
            text=f"Mostrando {len(filas)} filas de '{pestana}' • Azul: Contactado | Verde: ≥{min_pct}% | Doble clic: abrir link"
        )

    def _indice_a_letra_col(self, idx):
        resultado = ""
        while idx >= 0:
            resultado = chr(idx % 26 + 65) + resultado
            idx = idx // 26 - 1
        return resultado

    def abrir_link_de_fila(self, event):
        item = self.tree_sheet.focus()
        if not item:
            return
        valores = self.tree_sheet.item(item, "values")
        for val in valores:
            texto = str(val).strip()
            if texto.startswith("http://") or texto.startswith("https://"):
                webbrowser.open(texto)
                return

    # ==========================================
    # GESTIÓN DE VACANTE Y MENSAJE (PESTAÑA 3)
    # ==========================================
    def actualizar_contador_mensaje(self, event=None):
        largo = len(self.txt_mensaje.get("1.0", tk.END).strip())
        color = "#dc2626" if largo > 300 else "#059669"
        self.lbl_chars_msg.config(text=f"{largo} / 300 caracteres (nota invitación)", foreground=color)

    def guardar_vacante_local(self):
        hoja = self.combo_hojas.get()
        role = self.combo_pestanas.get()
        jd_texto = self.txt_jd.get("1.0", tk.END).strip()
        mensaje_texto = self.txt_mensaje.get("1.0", tk.END).strip()
        proyecto = self.entry_proyecto.get().strip()

        if len(jd_texto) > 50000:
            messagebox.showerror("Límite excedido", "La JD supera los 50,000 caracteres permitidos por celda en Google Sheets.")
            return False

        self.config["jd_actual"] = jd_texto
        self.config["mensaje_actual"] = mensaje_texto
        self.config["proyecto_recruiter"] = proyecto

        if hoja in self.config.get("hojas", {}) and role:
            self.config["hojas"][hoja].setdefault("vacantes", {})[role] = {
                "jd": jd_texto,
                "mensaje": mensaje_texto,
                "proyecto": proyecto
            }

        self.persistir_config()
        return True

    def guardar_vacante_async(self):
        hoja = self.combo_hojas.get()
        role = self.combo_pestanas.get()
        if not hoja or not role:
            messagebox.showerror("Sin selección", "Selecciona primero una Hoja y una Pestaña (Role) arriba.")
            return

        if not self.guardar_vacante_local():
            return

        sheet_id = self.config["hojas"][hoja]["spreadsheet_id"]
        jd = self.config["jd_actual"]
        mensaje = self.config["mensaje_actual"]
        proyecto = self.config["proyecto_recruiter"]

        self.btn_guardar_jd.config(state="disabled", text="⏳ Guardando en AGENTE_DB...")
        hilo = threading.Thread(
            target=self._tarea_guardar_vacante,
            args=(sheet_id, role, jd, mensaje, proyecto),
            daemon=True
        )
        hilo.start()

    def _tarea_guardar_vacante(self, sheet_id, role, jd, mensaje, proyecto):
        try:
            fila = guardar_vacante_en_sheet(sheet_id, role, jd, mensaje, proyecto)
            self.root.after(0, self._finalizar_guardar_vacante, fila, role, None)
        except Exception as e:
            self.root.after(0, self._finalizar_guardar_vacante, None, role, str(e))

    def _finalizar_guardar_vacante(self, fila, role, error):
        self.btn_guardar_jd.config(state="normal", text="☁️ Guardar en AGENTE_DB y Local")
        if error:
            self.escribir_log(f"❌ Error guardando en AGENTE_DB: {error}\n")
        else:
            self.escribir_log(f"✅ Fila {fila} de AGENTE_DB actualizada para '{role}'.\n")

    # ==========================================
    # LÓGICA DE EJECUCIÓN EN SEGUNDO PLANO
    # ==========================================
    def escribir_log(self, texto):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, texto)
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    def bloquear_controles(self, activo=True):
        estado_iniciar = "disabled" if activo else "normal"
        estado_detener = "normal" if activo else "disabled"

        self.btn_iniciar_ana.config(state=estado_iniciar)
        self.btn_iniciar_con.config(state=estado_iniciar)
        self.btn_sync.config(state=estado_iniciar)
        self.btn_guardar_jd.config(state=estado_iniciar)
        self.btn_detener_ana.config(state=estado_detener)
        self.btn_detener_con.config(state=estado_detener)

    def obtener_datos_hoja_activa(self, silencioso=False):
        nombre = self.combo_hojas.get()
        pestana = self.combo_pestanas.get()
        if not nombre or not pestana:
            if not silencioso:
                messagebox.showerror("Sin selección", "Selecciona una hoja de cálculo y una pestaña válida.")
            return None, None
        sheet_id = self.config.get("hojas", {}).get(nombre, {}).get("spreadsheet_id", "")
        return sheet_id, pestana

    def lanzar_analisis(self):
        inicio = self.ana_inicio.get().strip()
        fin = self.ana_fin.get().strip()

        if not self.validar_rango(inicio, fin):
            return

        self.config["ana_inicio"] = inicio
        self.config["ana_fin"] = fin
        self.persistir_config()

        sheet_id, pestana = self.obtener_datos_hoja_activa()
        if not sheet_id or not self.guardar_vacante_local():
            return

        if not self.config.get("jd_actual"):
            messagebox.showwarning("JD vacía", "No hay una JD cargada para esta pestaña. Agrégala en la Pestaña 3.")
            return

        self.iniciar_subproceso("run.py", [inicio, fin, sheet_id, pestana])

    def lanzar_contacto(self):
        inicio = self.con_inicio.get().strip()
        fin = self.con_fin.get().strip()
        porcentaje = self.con_min_pct.get().strip()

        if not self.validar_rango(inicio, fin):
            return
        if not porcentaje.isdigit() or not (0 <= int(porcentaje) <= 100):
            messagebox.showerror("Dato inválido", "El porcentaje mínimo debe ser un número entero entre 0 y 100.")
            return

        self.config["con_inicio"] = inicio
        self.config["con_fin"] = fin
        self.config["con_min_pct"] = porcentaje
        self.persistir_config()

        sheet_id, pestana = self.obtener_datos_hoja_activa()
        if not sheet_id or not self.guardar_vacante_local():
            return

        proyecto = self.config.get("proyecto_recruiter", "")
        self.iniciar_subproceso(
            os.path.join("contactar", "main.py"),
            [inicio, fin, porcentaje, sheet_id, pestana, proyecto]
        )

    def validar_rango(self, inicio, fin):
        if not inicio.isdigit() or not fin.isdigit():
            messagebox.showerror("Dato inválido", "Por favor ingresa números enteros en fila inicial y final.")
            return False
        if int(fin) < int(inicio):
            messagebox.showerror("Rango inválido", "La fila final no puede ser menor que la fila inicial.")
            return False
        return True

    def iniciar_subproceso(self, script_rel_path, args):
        self.log_area.config(state="normal")
        self.log_area.delete("1.0", tk.END)
        self.log_area.config(state="disabled")

        self.bloquear_controles(True)
        hilo = threading.Thread(target=self.ejecutar_script, args=(script_rel_path, args), daemon=True)
        hilo.start()

    def ejecutar_script(self, script_rel_path, args):
        ruta_script = os.path.join(self.base_dir, script_rel_path)

        if not os.path.exists(ruta_script):
            self.root.after(0, self.escribir_log, f"❌ Error: No se encontró '{script_rel_path}' en el proyecto.\n")
            self.root.after(0, self.bloquear_controles, False)
            return

        cmd = [sys.executable, "-u", ruta_script] + args
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        try:
            self.proceso = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=self.base_dir,
                env=env,
                start_new_session=True
            )

            for linea in self.proceso.stdout:
                self.root.after(0, self.escribir_log, linea)

            self.proceso.wait()
        except Exception as e:
            self.root.after(0, self.escribir_log, f"\n❌ Error al ejecutar: {e}\n")
        finally:
            self.root.after(0, self.bloquear_controles, False)
            # Si terminó de correr y la vista de hoja está abierta, actualizarla automáticamente
            self.root.after(0, self._refrescar_si_vista_activa)

    def _refrescar_si_vista_activa(self):
        if self.notebook.index(self.notebook.select()) == 3:
            self.cargar_vista_hoja_async()

    def detener_proceso(self):
        if self.proceso and self.proceso.poll() is None:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.proceso.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            else:
                try:
                    os.killpg(os.getpgid(self.proceso.pid), signal.SIGTERM)
                except Exception:
                    self.proceso.terminate()
            self.escribir_log("\n⛔ Proceso detenido por el usuario.\n")
        self.bloquear_controles(False)

    def al_cerrar(self):
        self.config["ana_inicio"] = self.ana_inicio.get().strip()
        self.config["ana_fin"] = self.ana_fin.get().strip()
        self.config["con_inicio"] = self.con_inicio.get().strip()
        self.config["con_fin"] = self.con_fin.get().strip()
        self.config["con_min_pct"] = self.con_min_pct.get().strip()
        self.persistir_config()
        self.detener_proceso()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AgenteReclutamientoApp(root)
    root.mainloop()