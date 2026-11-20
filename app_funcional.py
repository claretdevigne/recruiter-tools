import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import sys
import os

class ReclutadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Asistente de Reclutamiento")
        self.root.geometry("560x480")
        self.root.resizable(False, False)
        self.proceso = None

        # Configurar estilo de pestañas
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 6])

        # Contenedor principal de pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        # Crear las dos pestañas
        self.tab_analisis = ttk.Frame(self.notebook, padding=15)
        self.tab_contacto = ttk.Frame(self.notebook, padding=15)

        self.notebook.add(self.tab_analisis, text="1. Análisis de Perfiles")
        self.notebook.add(self.tab_contacto, text="2. Contacto y Recruiter")

        # Construir contenido de cada pestaña
        self.construir_tab_analisis()
        self.construir_tab_contacto()

        # --- Consola de Progreso Compartida (Parte Inferior) ---
        frame_log = ttk.Frame(root, padding="10 0 10 10")
        frame_log.pack(fill="both", expand=True)

        ttk.Label(frame_log, text="Registro de actividad:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.log_area = scrolledtext.ScrolledText(
            frame_log, height=13, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4", state="disabled"
        )
        self.log_area.pack(fill="both", expand=True)

    # ==========================================
    # PESTAÑA 1: ANÁLISIS DE PERFILES (run.py)
    # ==========================================
    def construir_tab_analisis(self):
        frame_inputs = ttk.Frame(self.tab_analisis)
        frame_inputs.pack(fill="x", pady=(0, 15))

        ttk.Label(frame_inputs, text="Fila inicial:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.ana_inicio = ttk.Entry(frame_inputs, width=10, font=("Segoe UI", 11))
        self.ana_inicio.grid(row=0, column=1, padx=(0, 25))
        self.ana_inicio.insert(0, "13")

        ttk.Label(frame_inputs, text="Fila final:", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=(0, 5), sticky="w")
        self.ana_fin = ttk.Entry(frame_inputs, width=10, font=("Segoe UI", 11))
        self.ana_fin.grid(row=0, column=3)
        self.ana_fin.insert(0, "25")

        frame_btns = ttk.Frame(self.tab_analisis)
        frame_btns.pack(fill="x")

        self.btn_iniciar_ana = tk.Button(
            frame_btns, text="▶ Iniciar Análisis", bg="#2563eb", fg="white",
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
    # PESTAÑA 2: CONTACTO Y RECRUITER
    # ==========================================
    def construir_tab_contacto(self):
        frame_inputs = ttk.Frame(self.tab_contacto)
        frame_inputs.pack(fill="x", pady=(0, 15))

        ttk.Label(frame_inputs, text="Fila inicial:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.con_inicio = ttk.Entry(frame_inputs, width=8, font=("Segoe UI", 11))
        self.con_inicio.grid(row=0, column=1, padx=(0, 15))
        self.con_inicio.insert(0, "13")

        ttk.Label(frame_inputs, text="Fila final:", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=(0, 5), sticky="w")
        self.con_fin = ttk.Entry(frame_inputs, width=8, font=("Segoe UI", 11))
        self.con_fin.grid(row=0, column=3, padx=(0, 15))
        self.con_fin.insert(0, "25")

        ttk.Label(frame_inputs, text="Match mín (%):", font=("Segoe UI", 10, "bold")).grid(row=0, column=4, padx=(0, 5), sticky="w")
        self.con_min_pct = ttk.Entry(frame_inputs, width=6, font=("Segoe UI", 11))
        self.con_min_pct.grid(row=0, column=5)
        self.con_min_pct.insert(0, "80")

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
        self.btn_detener_ana.config(state=estado_detener)
        self.btn_detener_con.config(state=estado_detener)

    def lanzar_analisis(self):
        inicio = self.ana_inicio.get().strip()
        fin = self.ana_fin.get().strip()

        if not self.validar_rango(inicio, fin):
            return

        self.iniciar_subproceso("run.py", [inicio, fin])

    def lanzar_contacto(self):
        inicio = self.con_inicio.get().strip()
        fin = self.con_fin.get().strip()
        porcentaje = self.con_min_pct.get().strip()

        if not self.validar_rango(inicio, fin):
            return
        if not porcentaje.isdigit():
            messagebox.showerror("Dato inválido", "El porcentaje mínimo debe ser un número entero.")
            return

        # CAMBIA "contactar_recruiter.py" por el nombre real de tu segundo script
        # y ajusta la lista de argumentos según lo que espere recibir.
        self.iniciar_subproceso("contactar/main.py", [inicio, fin, porcentaje])

    def validar_rango(self, inicio, fin):
        if not inicio.isdigit() or not fin.isdigit():
            messagebox.showerror("Dato inválido", "Por favor ingresa números enteros en fila inicial y final.")
            return False
        if int(fin) < int(inicio):
            messagebox.showerror("Rango inválido", "La fila final no puede ser menor que la fila inicial.")
            return False
        return True

    def iniciar_subproceso(self, script_name, args):
        self.log_area.config(state="normal")
        self.log_area.delete("1.0", tk.END)
        self.log_area.config(state="disabled")

        self.bloquear_controles(True)
        hilo = threading.Thread(target=self.ejecutar_script, args=(script_name, args), daemon=True)
        hilo.start()

    def ejecutar_script(self, script_name, args):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_script = os.path.join(base_dir, script_name)

        if not os.path.exists(ruta_script):
            self.root.after(0, self.escribir_log, f"❌ Error: No se encontró el archivo '{script_name}' en la carpeta del proyecto.\n")
            self.root.after(0, self.bloquear_controles, False)
            return

        cmd = [sys.executable, "-u", ruta_script] + args

        try:
            self.proceso = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=base_dir
            )

            for linea in self.proceso.stdout:
                self.root.after(0, self.escribir_log, linea)

            self.proceso.wait()
        except Exception as e:
            self.root.after(0, self.escribir_log, f"\n❌ Error al ejecutar: {e}\n")
        finally:
            self.root.after(0, self.bloquear_controles, False)

    def detener_proceso(self):
        if self.proceso and self.proceso.poll() is None:
            self.proceso.terminate()
            self.escribir_log("\n⛔ Proceso detenido por el usuario.\n")
        self.bloquear_controles(False)

if __name__ == "__main__":
    root = tk.Tk()
    app = ReclutadorApp(root)
    root.mainloop()