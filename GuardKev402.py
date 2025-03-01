import sys
import os
import psutil
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QLabel,
    QMessageBox, QTextEdit, QGroupBox, QFormLayout
)

proceso_actual = os.getpid()

class GuardKev402(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GuardKev402")
        self.setWindowIcon(QIcon("icono.png"))
        self.resize(900, 700)
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_tabla)
        self.timer.start(10)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Filtro por nombre de proceso
        filtro_layout = QHBoxLayout()
        filtro_label = QLabel("Filtrar conexiones por nombre de proceso:")
        filtro_layout.addWidget(filtro_label)
        self.input_filtro = QLineEdit()
        self.input_filtro.setPlaceholderText("Ingrese parte del nombre del proceso...")
        filtro_layout.addWidget(self.input_filtro)
        main_layout.addLayout(filtro_layout)

        # Tabla para mostrar las conexiones
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["PID", "Proceso", "Local", "Remoto", "Estado"])

        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.cellClicked.connect(self.mostrar_detalle)
        main_layout.addWidget(self.tabla)

        # Área de detalles de conexión
        detalles_group = QGroupBox("Detalles de la Conexión Seleccionada")
        detalles_layout = QVBoxLayout()
        self.text_detalles = QTextEdit()
        self.text_detalles.setReadOnly(True)
        detalles_layout.addWidget(self.text_detalles)
        detalles_group.setLayout(detalles_layout)
        main_layout.addWidget(detalles_group)

        # Área de control para terminar procesos
        control_group = QGroupBox("Control de Procesos")
        control_layout = QFormLayout()
        self.input_terminar = QLineEdit()
        self.input_terminar.setPlaceholderText("Nombre del proceso a terminar")
        control_layout.addRow("Proceso a terminar:", self.input_terminar)
        btn_terminar = QPushButton("Terminar Proceso")
        btn_terminar.clicked.connect(self.terminar_proceso)
        control_layout.addRow(btn_terminar)
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

    def actualizar_tabla(self):
        # Obtener todas las conexiones
        conexiones = psutil.net_connections(kind='inet')
        filtro_texto = self.input_filtro.text().strip().lower()

        # Filtrar conexiones según el filtro
        conexiones_filtradas = []
        for conn in conexiones:
            # Obtener el nombre del proceso
            proc_name = "-"
            if conn.pid:
                try:
                    proc_name = psutil.Process(conn.pid).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    proc_name = "Desconocido"
            # Si hay filtro, verificamos si el nombre del proceso lo contiene
            if filtro_texto:
                if filtro_texto not in proc_name.lower():
                    continue
            conexiones_filtradas.append((conn, proc_name))

        self.tabla.setRowCount(len(conexiones_filtradas))
        for i, (conn, proc_name) in enumerate(conexiones_filtradas):
            pid = conn.pid if conn.pid else "-"
            # Dirección local
            local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "-"
            # Dirección remota
            remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
            status = conn.status if conn.status else "-"

            self.tabla.setItem(i, 0, QTableWidgetItem(str(pid)))
            self.tabla.setItem(i, 1, QTableWidgetItem(proc_name))
            self.tabla.setItem(i, 2, QTableWidgetItem(local))
            self.tabla.setItem(i, 3, QTableWidgetItem(remote))
            self.tabla.setItem(i, 4, QTableWidgetItem(status))

        # Ajustar tamaño de las filas y columnas
        self.tabla.resizeColumnsToContents()
        self.tabla.resizeRowsToContents()

    def mostrar_detalle(self, fila):
        """Muestra detalles adicionales de la conexión seleccionada."""
        pid_item = self.tabla.item(fila, 0)
        proc_item = self.tabla.item(fila, 1)
        local_item = self.tabla.item(fila, 2)
        remote_item = self.tabla.item(fila, 3)
        status_item = self.tabla.item(fila, 4)

        detalle = (
            f"PID: {pid_item.text()}\n"
            f"Proceso: {proc_item.text()}\n"
            f"Local: {local_item.text()}\n"
            f"Remoto: {remote_item.text()}\n"
            f"Estado: {status_item.text()}\n"
        )

        try:
            pid = int(pid_item.text())
            if pid != proceso_actual:
                proc = psutil.Process(pid)
                detalle += "\n--- Información Adicional ---\n"
                detalle += f"Nombre completo: {proc.name()}\n"
                detalle += f"Ejecutable: {proc.exe()}\n"
                detalle += f"Argumentos: {' '.join(proc.cmdline())}\n"
                detalle += f"Creado: {proc.create_time()}\n"
                detalle += f"Uso de CPU: {proc.cpu_percent(interval=0.1)}%\n"
        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        self.text_detalles.setPlainText(detalle)

    def terminar_proceso(self):
        nombre = self.input_terminar.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "Por favor, ingresa el nombre del proceso a terminar.")
            return
        encontrados = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == nombre.lower():
                    if proc.info['pid'] == proceso_actual:
                        continue 
                    encontrados.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not encontrados:
            QMessageBox.information(self, "Información", f"No se encontró ningún proceso llamado '{nombre}'.")
        else:
            for proc in encontrados:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"No se pudo terminar el proceso {proc.info['pid']}: {e}")
            QMessageBox.information(self, "Información", f"Proceso(s) '{nombre}' terminado(s) (si se pudo).")
        self.input_terminar.clear()

def main():
    app = QApplication(sys.argv)
    window = GuardKev402()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()