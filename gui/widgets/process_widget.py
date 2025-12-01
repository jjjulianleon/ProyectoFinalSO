"""
Widget para monitoreo de Procesos
Con capacidad de matar procesos
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QProgressBar, QFrame,
                             QSizePolicy, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QLineEdit, QMessageBox,
                             QComboBox, QDialog, QTextEdit, QDialogButtonBox,
                             QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from datetime import datetime


class ProcessDetailDialog(QDialog):
    """Diálogo para mostrar detalles de un proceso."""
    
    def __init__(self, process_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detalles del Proceso - {process_info.get('name', 'N/A')} (PID: {process_info.get('pid', 'N/A')})")
        self.setMinimumSize(600, 500)
        self.setup_ui(process_info)
    
    def setup_ui(self, info):
        layout = QVBoxLayout(self)
        
        # Información básica
        basic_group = QGroupBox("Información Básica")
        basic_layout = QGridLayout(basic_group)
        
        fields = [
            ("PID", str(info.get('pid', 'N/A'))),
            ("Nombre", info.get('name', 'N/A')),
            ("Estado", info.get('status', 'N/A')),
            ("Usuario", info.get('username', 'N/A')),
            ("CPU %", f"{info.get('cpu_percent', 0):.1f}%"),
            ("Memoria %", f"{info.get('memory_percent', 0):.1f}%"),
            ("Memoria (MB)", f"{info.get('memory_mb', 0):.1f} MB"),
            ("Threads", str(info.get('num_threads', 'N/A'))),
        ]
        
        for i, (label, value) in enumerate(fields):
            row, col = divmod(i, 2)
            basic_layout.addWidget(QLabel(f"<b>{label}:</b>"), row, col * 2)
            basic_layout.addWidget(QLabel(value), row, col * 2 + 1)
        
        layout.addWidget(basic_group)
        
        # I/O
        if 'io_read_mb' in info:
            io_group = QGroupBox("I/O de Disco")
            io_layout = QHBoxLayout(io_group)
            io_layout.addWidget(QLabel(f"Leído: {info.get('io_read_mb', 0):.2f} MB"))
            io_layout.addWidget(QLabel(f"Escrito: {info.get('io_write_mb', 0):.2f} MB"))
            layout.addWidget(io_group)
        
        # Comando
        if info.get('cmdline'):
            cmd_group = QGroupBox("Línea de Comando")
            cmd_layout = QVBoxLayout(cmd_group)
            cmd_text = QTextEdit()
            cmd_text.setPlainText(' '.join(info.get('cmdline', [])))
            cmd_text.setReadOnly(True)
            cmd_text.setMaximumHeight(60)
            cmd_layout.addWidget(cmd_text)
            layout.addWidget(cmd_group)
        
        # Archivos abiertos
        if info.get('open_files'):
            files_group = QGroupBox(f"Archivos Abiertos ({len(info['open_files'])})")
            files_layout = QVBoxLayout(files_group)
            files_text = QTextEdit()
            files_text.setPlainText('\n'.join(info['open_files'][:20]))
            files_text.setReadOnly(True)
            files_text.setMaximumHeight(100)
            files_layout.addWidget(files_text)
            layout.addWidget(files_group)
        
        # Conexiones de red
        if info.get('connections'):
            conn_group = QGroupBox(f"Conexiones de Red ({len(info['connections'])})")
            conn_layout = QVBoxLayout(conn_group)
            conn_text = QTextEdit()
            conn_lines = [f"{c['local_addr']} -> {c['remote_addr']} ({c['status']})" 
                         for c in info['connections'][:10]]
            conn_text.setPlainText('\n'.join(conn_lines))
            conn_text.setReadOnly(True)
            conn_text.setMaximumHeight(100)
            conn_layout.addWidget(conn_text)
            layout.addWidget(conn_group)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class ProcessWidget(QWidget):
    """Widget para mostrar y gestionar procesos."""
    
    def __init__(self, process_monitor, parent=None):
        super().__init__(parent)
        self.process_monitor = process_monitor
        self.current_sort = 'memory_percent'
        self.sort_descending = True
        self.search_filter = ""
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("⚙️ Monitor de Procesos")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Panel de resumen
        summary_group = QGroupBox("Resumen del Sistema")
        summary_layout = QHBoxLayout(summary_group)
        
        self.total_processes_label = QLabel("Total: 0")
        self.running_label = QLabel("Ejecutando: 0")
        self.sleeping_label = QLabel("Durmiendo: 0")
        self.total_cpu_label = QLabel("CPU Total: 0%")
        self.total_mem_label = QLabel("Memoria Total: 0%")
        
        for label in [self.total_processes_label, self.running_label, 
                      self.sleeping_label, self.total_cpu_label, self.total_mem_label]:
            label.setStyleSheet("padding: 8px; background-color: #e3f2fd; border-radius: 5px;")
            summary_layout.addWidget(label)
        
        layout.addWidget(summary_group)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        # Búsqueda
        search_label = QLabel("🔍 Buscar:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nombre del proceso o PID...")
        self.search_input.textChanged.connect(self.on_search_changed)
        
        # Ordenar por
        sort_label = QLabel("Ordenar por:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Memoria %", "CPU %", "PID", "Nombre", "Disco"])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        
        # Botón de actualizar
        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.clicked.connect(self.update_data)
        
        controls_layout.addWidget(search_label)
        controls_layout.addWidget(self.search_input)
        controls_layout.addWidget(sort_label)
        controls_layout.addWidget(self.sort_combo)
        controls_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # Tabla de procesos
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(8)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Nombre", "Estado", "CPU %", "Memoria %", 
            "Memoria (MB)", "Disco (MB)", "Usuario"
        ])
        
        # Configurar tabla
        header = self.process_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre se expande
        
        self.process_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.process_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setSortingEnabled(True)
        self.process_table.doubleClicked.connect(self.on_process_double_click)
        
        layout.addWidget(self.process_table)
        
        # Botones de acción
        action_layout = QHBoxLayout()
        
        self.details_btn = QPushButton("📋 Ver Detalles")
        self.details_btn.clicked.connect(self.show_process_details)
        
        self.kill_btn = QPushButton("🛑 Terminar Proceso")
        self.kill_btn.clicked.connect(self.kill_selected_process)
        self.kill_btn.setStyleSheet("background-color: #ffcdd2;")
        
        self.force_kill_btn = QPushButton("💀 Forzar Terminación")
        self.force_kill_btn.clicked.connect(self.force_kill_selected_process)
        self.force_kill_btn.setStyleSheet("background-color: #ef9a9a;")
        
        action_layout.addStretch()
        action_layout.addWidget(self.details_btn)
        action_layout.addWidget(self.kill_btn)
        action_layout.addWidget(self.force_kill_btn)
        
        layout.addLayout(action_layout)
        
    def on_search_changed(self, text):
        """Maneja cambios en el campo de búsqueda."""
        self.search_filter = text.lower()
        self.filter_table()
    
    def on_sort_changed(self, index):
        """Maneja cambios en el criterio de ordenación."""
        sort_fields = ['memory_percent', 'cpu_percent', 'pid', 'name', 'disk_total_mb']
        self.current_sort = sort_fields[index]
        self.update_data()
    
    def filter_table(self):
        """Filtra las filas de la tabla según el texto de búsqueda."""
        for row in range(self.process_table.rowCount()):
            show = True
            if self.search_filter:
                # Buscar en PID y Nombre
                pid_item = self.process_table.item(row, 0)
                name_item = self.process_table.item(row, 1)
                
                pid_match = self.search_filter in pid_item.text().lower() if pid_item else False
                name_match = self.search_filter in name_item.text().lower() if name_item else False
                
                show = pid_match or name_match
            
            self.process_table.setRowHidden(row, not show)
    
    def update_data(self):
        """Actualiza los datos del widget."""
        # Obtener procesos
        processes = self.process_monitor.get_process_list(
            sort_by=self.current_sort,
            descending=self.sort_descending
        )
        
        # Actualizar resumen
        summary = self.process_monitor.get_system_summary()
        self.total_processes_label.setText(f"Total: {summary['total_processes']}")
        
        status = summary['status_breakdown']
        self.running_label.setText(f"Ejecutando: {status.get('running', 0)}")
        self.sleeping_label.setText(f"Durmiendo: {status.get('sleeping', 0)}")
        self.total_cpu_label.setText(f"CPU: {summary['total_cpu_percent']:.1f}%")
        self.total_mem_label.setText(f"Memoria: {summary['total_memory_percent']:.1f}%")
        
        # Actualizar tabla
        self.process_table.setSortingEnabled(False)
        self.process_table.setRowCount(len(processes))
        
        for row, proc in enumerate(processes):
            # PID
            pid_item = QTableWidgetItem(str(proc['pid']))
            pid_item.setData(Qt.UserRole, proc['pid'])
            self.process_table.setItem(row, 0, pid_item)
            
            # Nombre
            self.process_table.setItem(row, 1, QTableWidgetItem(proc['name']))
            
            # Estado
            status_item = QTableWidgetItem(proc['status'])
            if proc['status'] == 'running':
                status_item.setBackground(QColor('#c8e6c9'))
            elif proc['status'] == 'sleeping':
                status_item.setBackground(QColor('#e3f2fd'))
            elif proc['status'] == 'zombie':
                status_item.setBackground(QColor('#ffcdd2'))
            self.process_table.setItem(row, 2, status_item)
            
            # CPU %
            cpu_item = QTableWidgetItem(f"{proc['cpu_percent']:.1f}")
            cpu_item.setData(Qt.UserRole, proc['cpu_percent'])
            if proc['cpu_percent'] > 50:
                cpu_item.setBackground(QColor('#ffcdd2'))
            elif proc['cpu_percent'] > 20:
                cpu_item.setBackground(QColor('#fff9c4'))
            self.process_table.setItem(row, 3, cpu_item)
            
            # Memoria %
            mem_item = QTableWidgetItem(f"{proc['memory_percent']:.1f}")
            mem_item.setData(Qt.UserRole, proc['memory_percent'])
            if proc['memory_percent'] > 10:
                mem_item.setBackground(QColor('#ffcdd2'))
            elif proc['memory_percent'] > 5:
                mem_item.setBackground(QColor('#fff9c4'))
            self.process_table.setItem(row, 4, mem_item)
            
            # Memoria MB
            mem_mb_item = QTableWidgetItem(f"{proc['memory_mb']:.1f}")
            mem_mb_item.setData(Qt.UserRole, proc['memory_mb'])
            self.process_table.setItem(row, 5, mem_mb_item)
            
            # Disco MB
            disk_item = QTableWidgetItem(f"{proc['disk_total_mb']:.1f}")
            disk_item.setData(Qt.UserRole, proc['disk_total_mb'])
            self.process_table.setItem(row, 6, disk_item)
            
            # Usuario
            self.process_table.setItem(row, 7, QTableWidgetItem(proc['username']))
        
        self.process_table.setSortingEnabled(True)
        self.filter_table()
    
    def get_selected_pid(self):
        """Obtiene el PID del proceso seleccionado."""
        selected = self.process_table.selectedItems()
        if selected:
            row = selected[0].row()
            pid_item = self.process_table.item(row, 0)
            if pid_item:
                return int(pid_item.text())
        return None
    
    def on_process_double_click(self):
        """Maneja doble clic en un proceso."""
        self.show_process_details()
    
    def show_process_details(self):
        """Muestra detalles del proceso seleccionado."""
        pid = self.get_selected_pid()
        if pid:
            info = self.process_monitor.get_process_by_pid(pid)
            if info and 'error' not in info:
                dialog = ProcessDetailDialog(info, self)
                dialog.exec_()
            else:
                QMessageBox.warning(self, "Error", 
                                   f"No se pudo obtener información del proceso {pid}")
        else:
            QMessageBox.information(self, "Info", 
                                   "Seleccione un proceso de la lista")
    
    def kill_selected_process(self):
        """Termina el proceso seleccionado (SIGTERM)."""
        pid = self.get_selected_pid()
        if pid:
            # Obtener nombre del proceso
            row = self.process_table.currentRow()
            name = self.process_table.item(row, 1).text() if self.process_table.item(row, 1) else "Desconocido"
            
            reply = QMessageBox.question(
                self, "Confirmar",
                f"¿Está seguro de que desea terminar el proceso?\n\n"
                f"Nombre: {name}\nPID: {pid}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                result = self.process_monitor.kill_process(pid, force=False)
                if result['success']:
                    QMessageBox.information(self, "Éxito", result['message'])
                    self.update_data()
                else:
                    QMessageBox.warning(self, "Error", result['message'])
        else:
            QMessageBox.information(self, "Info", 
                                   "Seleccione un proceso de la lista")
    
    def force_kill_selected_process(self):
        """Fuerza la terminación del proceso seleccionado (SIGKILL)."""
        pid = self.get_selected_pid()
        if pid:
            row = self.process_table.currentRow()
            name = self.process_table.item(row, 1).text() if self.process_table.item(row, 1) else "Desconocido"
            
            reply = QMessageBox.warning(
                self, "⚠️ Confirmar Terminación Forzada",
                f"¿Está SEGURO de que desea FORZAR la terminación del proceso?\n\n"
                f"Nombre: {name}\nPID: {pid}\n\n"
                f"⚠️ Esto puede causar pérdida de datos no guardados.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                result = self.process_monitor.kill_process(pid, force=True)
                if result['success']:
                    QMessageBox.information(self, "Éxito", result['message'])
                    self.update_data()
                else:
                    QMessageBox.warning(self, "Error", result['message'])
        else:
            QMessageBox.information(self, "Info", 
                                   "Seleccione un proceso de la lista")
