import os
import psutil
import customtkinter
import tkinter as tk 
from tkinter import ttk 
from tkinter import messagebox 

customtkinter.set_appearance_mode("System") 
customtkinter.set_default_color_theme("blue") 

proceso_actual = os.getpid()

class GuardKev402(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("GuardKev402")
        try:
            self.iconbitmap("icono.ico") 
            pass
        except tk.TclError:
            print("Advertencia: No se pudo cargar 'icono.ico'. Asegúrate de que el archivo exista y sea válido.")
            
        self.geometry("900x700")

        self.setup_ui()
        self.actualizar_tabla() # Llamada inicial

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Permitir que la tabla se expanda

        # --- Frame Filtro ---
        filtro_frame = customtkinter.CTkFrame(self)
        filtro_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        filtro_frame.grid_columnconfigure(1, weight=1)

        filtro_label = customtkinter.CTkLabel(filtro_frame, text="Filtrar conexiones por nombre de proceso:")
        filtro_label.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")

        self.input_filtro = customtkinter.CTkEntry(filtro_frame, placeholder_text="Ingrese parte del nombre del proceso...")
        self.input_filtro.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ew")
        self.input_filtro.bind("<KeyRelease>", lambda event: self.actualizar_tabla())

        # --- Frame Tabla (usando ttk.Treeview) ---
        tabla_frame = customtkinter.CTkFrame(self)
        tabla_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        tabla_frame.grid_rowconfigure(0, weight=1)
        tabla_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        bg_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkLabel"]["text_color"])
        selected_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

        style.theme_use("default") 
        style.configure("Treeview",
                        background=bg_color,
                        foreground=text_color,
                        fieldbackground=bg_color,
                        rowheight=25)
        style.map('Treeview', background=[('selected', selected_color)], foreground=[('selected', text_color)])
        style.configure("Treeview.Heading",
                        background=self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkButton"]["fg_color"]),
                        foreground=text_color,
                        font=('CTkFont', 13, 'bold')) # Ajusta la fuente si es necesario
        style.map("Treeview.Heading",
                  background=[('active', self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkButton"]["hover_color"]))])


        self.tree = ttk.Treeview(tabla_frame, columns=("PID", "Proceso", "Local", "Remoto", "Estado"), show='headings')
        self.tree.heading("PID", text="PID")
        self.tree.heading("Proceso", text="Proceso")
        self.tree.heading("Local", text="Local")
        self.tree.heading("Remoto", text="Remoto")
        self.tree.heading("Estado", text="Estado")

        # Ajustar ancho inicial de columnas 
        self.tree.column("PID", width=60, anchor='center')
        self.tree.column("Proceso", width=150)
        self.tree.column("Local", width=200)
        self.tree.column("Remoto", width=200)
        self.tree.column("Estado", width=100)

        # Scrollbars
        vsb = customtkinter.CTkScrollbar(tabla_frame, orientation="vertical", command=self.tree.yview)
        hsb = customtkinter.CTkScrollbar(tabla_frame, orientation="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.tree.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        # --- Frame Detalles ---
        detalles_frame = customtkinter.CTkFrame(self)
        detalles_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        detalles_frame.grid_columnconfigure(0, weight=1)
        detalles_frame.grid_rowconfigure(1, weight=1) # Permitir que el textbox crezca un poco si es necesario

        detalles_label = customtkinter.CTkLabel(detalles_frame, text="Detalles de la Conexión Seleccionada", font=customtkinter.CTkFont(weight="bold"))
        detalles_label.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")

        self.text_detalles = customtkinter.CTkTextbox(detalles_frame, height=120) # Altura inicial
        self.text_detalles.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.text_detalles.configure(state="disabled") # Hacerlo read-only

        # --- Frame Control ---
        control_frame = customtkinter.CTkFrame(self)
        control_frame.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")

        control_label = customtkinter.CTkLabel(control_frame, text="Control de Procesos", font=customtkinter.CTkFont(weight="bold"))
        control_label.pack(pady=(5, 0), padx=10, anchor="w")

        inner_control_frame = customtkinter.CTkFrame(control_frame, fg_color="transparent")
        inner_control_frame.pack(fill="x", padx=10, pady=5)
        inner_control_frame.grid_columnconfigure(1, weight=1)


        terminar_label = customtkinter.CTkLabel(inner_control_frame, text="Proceso a terminar:")
        terminar_label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")

        self.input_terminar = customtkinter.CTkEntry(inner_control_frame, placeholder_text="Nombre exacto del proceso")
        self.input_terminar.grid(row=0, column=1, padx=0, pady=5, sticky="ew")

        btn_terminar = customtkinter.CTkButton(inner_control_frame, text="Terminar Proceso", command=self.terminar_proceso)
        btn_terminar.grid(row=1, column=0, columnspan=2, padx=0, pady=(5, 10))


    def actualizar_tabla(self):
        """Actualiza la tabla (Treeview) con las conexiones de red."""
        try:
            # Obtener todas las conexiones
            conexiones = psutil.net_connections(kind='inet')
            filtro_texto = self.input_filtro.get().strip().lower()

            # Limpiar tabla actual
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Filtrar y añadir conexiones
            for conn in conexiones:
                proc_name = "-"
                pid_val = conn.pid if conn.pid else "-"
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        proc_name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        # Si el proceso ya no existe o no tenemos permisos
                        proc_name = "Desconocido/Terminado"

                # Aplicar filtro si existe
                if filtro_texto and filtro_texto not in proc_name.lower():
                    continue

                # Dirección local
                local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr and conn.laddr.ip else "-"
                # Dirección remota
                remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr and conn.raddr.ip else "-"
                status = conn.status if conn.status else "-"

                # Añadir fila al Treeview
                self.tree.insert("", tk.END, values=(str(pid_val), proc_name, local, remote, status))

        except Exception as e:
            print(f"Error al actualizar tabla: {e}") # Loggeo básico del error
        finally:
            self.after(500, self.actualizar_tabla)


    def mostrar_detalle(self, event=None):
        """Muestra detalles adicionales de la conexión seleccionada en el Treeview."""
        selected_items = self.tree.selection()
        if not selected_items:
            return # No hay nada seleccionado

        item_id = selected_items[0] # Tomar el primer (y usualmente único) item seleccionado
        values = self.tree.item(item_id, 'values')

        if not values or len(values) < 5:
            self.text_detalles.configure(state="normal")
            self.text_detalles.delete("1.0", tk.END)
            self.text_detalles.insert(tk.END, "Error al obtener datos de la fila.")
            self.text_detalles.configure(state="disabled")
            return

        pid_str, proc_name, local, remote, status = values

        detalle = (
            f"PID: {pid_str}\n"
            f"Proceso: {proc_name}\n"
            f"Local: {local}\n"
            f"Remoto: {remote}\n"
            f"Estado: {status}\n"
        )

        try:
            pid = int(pid_str)
            if pid != '-' and pid != proceso_actual: # Verificar que PID sea válido y no el propio script
                proc = psutil.Process(pid)
                detalle += "\n--- Información Adicional ---\n"
                detalle += f"Nombre completo: {proc.name()}\n"
                # Usar try-except individuales para atributos que pueden fallar
                try:
                    detalle += f"Ejecutable: {proc.exe()}\n"
                except (psutil.AccessDenied, FileNotFoundError):
                     detalle += "Ejecutable: Acceso denegado o no encontrado\n"
                try:
                    detalle += f"Argumentos: {' '.join(proc.cmdline())}\n"
                except psutil.AccessDenied:
                     detalle += "Argumentos: Acceso denegado\n"
                try:
                    detalle += f"Creado (timestamp): {proc.create_time()}\n"
                except psutil.AccessDenied:
                     detalle += "Creado: Acceso denegado\n"
                try:
                    detalle += f"Uso de CPU (instantáneo): {proc.cpu_percent(interval=0)}%\n"
                except (psutil.AccessDenied, Exception): # Captura otras posibles excepciones
                     detalle += "Uso de CPU: No disponible\n"
        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
             detalle += f"\n--- No se pudo obtener información adicional ({type(e).__name__}) ---\n"
        except Exception as e: 
            detalle += f"\n--- Error inesperado al obtener info adicional: {e} ---\n"

        # Actualizar el CTkTextbox
        self.text_detalles.configure(state="normal") # Habilitar escritura
        self.text_detalles.delete("1.0", tk.END)     # Borrar contenido anterior
        self.text_detalles.insert("1.0", detalle)    # Insertar nuevo contenido
        self.text_detalles.configure(state="disabled") # Deshabilitar escritura (read-only)

    def terminar_proceso(self):
        """Intenta terminar procesos basados en el nombre ingresado."""
        nombre = self.input_terminar.get().strip()
        if not nombre:
            messagebox.showwarning("Entrada Vacía", "Por favor, ingresa el nombre del proceso a terminar.")
            return

        encontrados = []
        procesos_terminados = 0
        errores = []

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == nombre.lower() and proc.info['pid'] != proceso_actual:
                     encontrados.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue # Ignorar procesos que ya no existen o a los que no podemos acceder

        if not encontrados:
            messagebox.showinfo("No Encontrado", f"No se encontró ningún proceso activo llamado '{nombre}' (al que se tenga acceso).")
        else:
            confirmacion = messagebox.askyesno("Confirmar Terminación",
                                              f"Se encontraron {len(encontrados)} proceso(s) llamado(s) '{nombre}'.\n"
                                              f"¿Estás seguro de que deseas intentar terminarlos?")
            if confirmacion:
                for proc in encontrados:
                    try:
                        proc.terminate()
                        try:
                            proc.wait(timeout=0.5) 
                            procesos_terminados += 1
                        except psutil.TimeoutExpired:
                            # Si no terminó amigablemente, forzarlo (kill)
                            print(f"Proceso {proc.info['pid']} no terminó, forzando...")
                            proc.kill()
                            proc.wait(timeout=0.5) # Esperar un poco después de kill
                            procesos_terminados += 1
                    except (psutil.NoSuchProcess, psutil.ZombieProcess):
                        procesos_terminados += 1 # Contarlo como terminado
                    except (psutil.AccessDenied, Exception) as e:
                        errores.append(f"PID {proc.info['pid']}: {e}")

                msg_final = f"Se intentó terminar {len(encontrados)} proceso(s) '{nombre}'.\n"
                msg_final += f"Terminados exitosamente: {procesos_terminados}\n"
                if errores:
                    msg_final += "\nErrores:\n" + "\n".join(errores)
                messagebox.showinfo("Resultado", msg_final)
            else:
                 messagebox.showinfo("Cancelado", "Operación de terminación cancelada.")


        self.input_terminar.delete(0, tk.END) # Limpiar el campo de entrada

# --- Punto de Entrada ---
if __name__ == "__main__":
    app = GuardKev402() 
    app.mainloop()      
