import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import sys
import os

class ReclutadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Análisis de Perfiles")
        self.root.geometry("520x420")
        self.root.resizable(False, False)
        self.proceso = None

        # --- Marco de Controles ---
        frame_top = ttk.Frame(root, padding="20 20 20 10")
        frame_top.pack(fill="x")

        # Campo Fila Inicial
        ttk.Label(frame_top, text="Fila inicial:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.entry_inicio = ttk.Entry(frame_top, width=10, font=("Segoe UI", 11))
        self.entry_inicio.grid(row=0, column=1, padx=(0, 20))
        self.entry_inicio.insert(0, "13")

        # Campo Fila Final
        ttk.Label(frame_top, text="Fila final:", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=(0, 5), sticky="w")
        self.entry_fin = ttk.Entry(frame_top, width=10, font=("Segoe UI", 11))
        self.entry_fin.grid(row=0, column=3, padx=(0, 20))
        self.entry_fin.insert(0, "25")

        # --- Botones de Acción ---
        frame_btns = ttk.Frame(root, padding="20 5 20 15")
        frame_btns.pack(fill="x")

        self.btn_iniciar = tk.Button(
            frame_btns, text="▶ Iniciar Análisis", bg="#2563eb", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8,
            cursor="hand2", command=self.iniciar_proceso
        )
        self.btn_iniciar.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_detener = tk.Button(
            frame_btns, text="⏹ Detener", bg="#dc2626", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8,
            cursor="hand2", state="disabled", command=self.detener_proceso
        )
        self.btn_detener.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # --- Área de Progreso (Salida de run.py) ---
        frame_log = ttk.Frame(root, padding="20 0 20 20")
        frame_log.pack(fill="both", expand=True)

        ttk.Label(frame_log, text="Progreso:", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        self.log_area = scrolledtext.ScrolledText(
            frame_log, height=14, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4", state="disabled"
        )
        self.log_area.pack(fill="both", expand=True)

    def escribir_log(self, texto):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, texto)
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    def iniciar_proceso(self):
        inicio = self.entry_inicio.get().strip()
        fin = self.entry_fin.get().strip()

        if not inicio.isdigit() or not fin.isdigit():
            messagebox.showerror("Dato inválido", "Por favor ingresa números enteros en fila inicial y final.")
            return

        if int(fin) < int(inicio):
            messagebox.showerror("Rango inválido", "La fila final no puede ser menor que la fila inicial.")
            return

        # Limpiar consola y bloquear controles
        self.log_area.config(state="normal")
        self.log_area.delete("1.0", tk.END)
        self.log_area.config(state="disabled")

        self.btn_iniciar.config(state="disabled", bg="#93c5fd")
        self.btn_detener.config(state="normal")

        # Ejecutar run.py en un hilo separado para no congelar la ventana
        hilo = threading.Thread(target=self.ejecutar_run_py, args=(inicio, fin), daemon=True)
        hilo.start()

    def ejecutar_run_py(self, inicio, fin):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_run = os.path.join(base_dir, "run.py")

        # '-u' fuerza salida sin buffer para ver cada print() en tiempo real
        cmd = [sys.executable, "-u", ruta_run, inicio, fin]

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
            self.root.after(0, self.escribir_log, f"\nError al ejecutar: {e}\n")
        finally:
            self.root.after(0, self.finalizar_ui)

    def detener_proceso(self):
        if self.proceso and self.proceso.poll() is None:
            self.proceso.terminate()
            self.escribir_log("\n⛔ Proceso detenido por el usuario.\n")
        self.finalizar_ui()

    def finalizar_ui(self):
        self.btn_iniciar.config(state="normal", bg="#2563eb")
        self.btn_detener.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = ReclutadorApp(root)
    root.mainloop()