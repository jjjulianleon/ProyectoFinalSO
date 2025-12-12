"""
Widget para monitoreo de Red
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QFrame,
                             QSizePolicy, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime


class NetworkDetailsDialog(QDialog):
    """Ventana emergente para ver detalles de interfaces y conexiones."""
    
    def __init__(self, network_monitor, parent=None):
        super().__init__(parent)
        self.network_monitor = network_monitor
        self.setWindowTitle("Detalles de Red - Interfaces y Conexiones")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Detalles de Red")
        title.setFont(QFont('Arial', 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # --- TABLA DE INTERFACES ---
        group_interfaces = QGroupBox("Interfaces de Red")
        layout_interfaces = QVBoxLayout(group_interfaces)
        
        self.interfaces_table = QTableWidget()
        self.interfaces_table.setColumnCount(5)
        self.interfaces_table.setHorizontalHeaderLabels([
            "Interfaz", "Estado", "Dirección IP", "Velocidad (Mbps)", "MTU"
        ])
        self.interfaces_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout_interfaces.addWidget(self.interfaces_table)
        layout.addWidget(group_interfaces)
        
        # --- TABLA DE CONEXIONES ---
        group_connections = QGroupBox("Conexiones Activas")
        layout_connections = QVBoxLayout(group_connections)
        
        self.connections_label = QLabel("Total conexiones: 0")
        layout_connections.addWidget(self.connections_label)
        
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(5)
        self.connections_table.setHorizontalHeaderLabels([
            "Local", "Remoto", "Estado", "PID", "Proceso"
        ])
        self.connections_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout_connections.addWidget(self.connections_table)
        layout.addWidget(group_connections)
        
        # Botón cerrar
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
        
    def update_data(self):
        """Actualiza las tablas de la ventana de detalles."""
        stats = self.network_monitor.get_current_stats()
        
        # 1. Interfaces
        interfaces = stats['interfaces']
        self.interfaces_table.setRowCount(len(interfaces))
        
        for row, iface in enumerate(interfaces):
            self.interfaces_table.setItem(row, 0, QTableWidgetItem(iface['name']))
            
            status_text = "🟢 Activa" if iface['is_up'] else "🔴 Inactiva"
            status_item = QTableWidgetItem(status_text)
            # Colorear fondo celda
            bg_color = QColor('#c8e6c9') if iface['is_up'] else QColor('#ffcdd2')
            status_item.setBackground(bg_color)
            self.interfaces_table.setItem(row, 1, status_item)
            
            ipv4 = "N/A"
            for addr in iface['addresses']:
                if addr['family'] == 'IPv4' and addr['address']:
                    ipv4 = addr['address']
                    break
            
            self.interfaces_table.setItem(row, 2, QTableWidgetItem(ipv4))
            self.interfaces_table.setItem(row, 3, QTableWidgetItem(str(iface['speed'])))
            self.interfaces_table.setItem(row, 4, QTableWidgetItem(str(iface['mtu'])))
            
        # 2. Conexiones
        try:
            # Obtener conexiones frescas
            connections = self.network_monitor.get_connections()
            self.connections_label.setText(f"Total conexiones activas: {len(connections)}")
            
            # Limitar visualización a 100 para no congelar la UI
            display_conns = connections[:100]
            self.connections_table.setRowCount(len(display_conns))
            
            for row, conn in enumerate(display_conns):
                local = f"{conn['local_address']}:{conn['local_port']}"
                remote = f"{conn['remote_address']}:{conn['remote_port']}" if conn['remote_address'] else "-"
                
                self.connections_table.setItem(row, 0, QTableWidgetItem(local))
                self.connections_table.setItem(row, 1, QTableWidgetItem(remote))
                
                status_item = QTableWidgetItem(conn['status'])
                if conn['status'] == 'ESTABLISHED':
                    status_item.setBackground(QColor('#e8f5e9')) # Verde claro
                elif conn['status'] == 'LISTEN':
                    status_item.setBackground(QColor('#e3f2fd')) # Azul claro
                    
                self.connections_table.setItem(row, 2, status_item)
                self.connections_table.setItem(row, 3, QTableWidgetItem(str(conn['pid'] or "-")))
                self.connections_table.setItem(row, 4, QTableWidgetItem(conn.get('process_name', '-')))
                
        except Exception:
            pass


class NetworkWidget(QWidget):
    """Widget principal para mostrar información de red."""
    
    def __init__(self, network_monitor, parent=None):
        super().__init__(parent)
        self.network_monitor = network_monitor
        self.details_dialog = None # Referencia a la ventana de detalles
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("🌐 Monitor de Red")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # --- PANEL DE VELOCIDAD (Mejorado para no cortar números) ---
        speed_group = QGroupBox("Ancho de Banda Actual")
        speed_layout = QHBoxLayout(speed_group)
        speed_layout.setSpacing(20)
        
        # Estilo base para las cajas de velocidad
        box_style = """
            QFrame {
                border-radius: 10px;
                background-color: %s;
            }
            QLabel {
                background-color: transparent;
            }
        """
        
        # --- DOWNLOAD ---
        dl_frame = QFrame()
        dl_frame.setStyleSheet(box_style % "#e8f5e9") # Verde muy suave
        dl_layout = QVBoxLayout(dl_frame)
        dl_layout.setContentsMargins(10, 15, 10, 15) # Más padding vertical
        
        dl_icon = QLabel("▼")
        dl_icon.setAlignment(Qt.AlignCenter)
        dl_icon.setFont(QFont('Arial', 24, QFont.Bold))
        dl_icon.setStyleSheet("color: #2e7d32;")
        
        self.download_speed_label = QLabel("0.0 KB/s")
        self.download_speed_label.setAlignment(Qt.AlignCenter)
        # Reducimos un poco la fuente para evitar recortes
        self.download_speed_label.setFont(QFont('Arial', 20, QFont.Bold))
        self.download_speed_label.setStyleSheet("color: #1b5e20;")
        
        dl_title = QLabel("Descarga")
        dl_title.setAlignment(Qt.AlignCenter)
        dl_title.setFont(QFont('Arial', 10))
        
        dl_layout.addWidget(dl_icon)
        dl_layout.addWidget(self.download_speed_label)
        dl_layout.addWidget(dl_title)
        
        # --- UPLOAD ---
        ul_frame = QFrame()
        ul_frame.setStyleSheet(box_style % "#e3f2fd") # Azul muy suave
        ul_layout = QVBoxLayout(ul_frame)
        ul_layout.setContentsMargins(10, 15, 10, 15)
        
        ul_icon = QLabel("▲")
        ul_icon.setAlignment(Qt.AlignCenter)
        ul_icon.setFont(QFont('Arial', 24, QFont.Bold))
        ul_icon.setStyleSheet("color: #1565c0;")
        
        self.upload_speed_label = QLabel("0.0 KB/s")
        self.upload_speed_label.setAlignment(Qt.AlignCenter)
        self.upload_speed_label.setFont(QFont('Arial', 20, QFont.Bold))
        self.upload_speed_label.setStyleSheet("color: #0d47a1;")
        
        ul_title = QLabel("Subida")
        ul_title.setAlignment(Qt.AlignCenter)
        ul_title.setFont(QFont('Arial', 10))
        
        ul_layout.addWidget(ul_icon)
        ul_layout.addWidget(self.upload_speed_label)
        ul_layout.addWidget(ul_title)
        
        # Añadir al layout horizontal
        speed_layout.addWidget(dl_frame)
        speed_layout.addWidget(ul_frame)
        
        layout.addWidget(speed_group)
        
        # --- ESTADÍSTICAS TOTALES ---
        stats_group = QGroupBox("Estadísticas de la Sesión")
        stats_layout = QGridLayout(stats_group)
        
        self.total_dl_label = QLabel("Total Descargado: 0 GB")
        self.total_ul_label = QLabel("Total Subido: 0 GB")
        self.pkts_in_label = QLabel("Paquetes Recibidos: 0")
        self.pkts_out_label = QLabel("Paquetes Enviados: 0")
        
        # Estilo etiquetas estadísticas
        st_style = "background-color: #f5f5f5; padding: 8px; border-radius: 4px;"
        for lbl in [self.total_dl_label, self.total_ul_label, self.pkts_in_label, self.pkts_out_label]:
            lbl.setStyleSheet(st_style)
            
        stats_layout.addWidget(self.total_dl_label, 0, 0)
        stats_layout.addWidget(self.total_ul_label, 0, 1)
        stats_layout.addWidget(self.pkts_in_label, 1, 0)
        stats_layout.addWidget(self.pkts_out_label, 1, 1)
        
        layout.addWidget(stats_group)
        
        # --- GRÁFICO ---
        chart_group = QGroupBox("Historial de Actividad (Último Minuto)")
        chart_layout = QVBoxLayout(chart_group)
        
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.figure.patch.set_facecolor('#f0f0f0')
        self.figure.subplots_adjust(bottom=0.15, top=0.9, left=0.1, right=0.95)
        
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.figure.add_subplot(111)
        
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_group)
        
        # --- BOTÓN PARA VER DETALLES ---
        self.btn_details = QPushButton("🔍 Ver Detalles de Conexiones e Interfaces")
        self.btn_details.setCursor(Qt.PointingHandCursor)
        self.btn_details.setFixedHeight(40)
        self.btn_details.setStyleSheet("""
            QPushButton {
                background-color: #607d8b;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #546e7a;
            }
        """)
        self.btn_details.clicked.connect(self.show_details)
        layout.addWidget(self.btn_details)
        
    def show_details(self):
        """Abre la ventana de detalles."""
        if self.details_dialog is None:
            self.details_dialog = NetworkDetailsDialog(self.network_monitor, self)
        
        self.details_dialog.show()
        self.details_dialog.raise_()
        self.details_dialog.activateWindow()
        
    def update_data(self):
        """Actualiza los datos del widget principal y del diálogo si está abierto."""
        stats = self.network_monitor.get_current_stats()
        
        # 1. Velocidades
        speeds = stats['speeds']
        self.download_speed_label.setText(speeds['download']['formatted'])
        self.upload_speed_label.setText(speeds['upload']['formatted'])
        
        # 2. Estadísticas Totales
        io = stats['io_counters']
        self.total_dl_label.setText(f"📥 Total Descargado: {io['bytes_recv_gb']:.2f} GB")
        self.total_ul_label.setText(f"📤 Total Subido: {io['bytes_sent_gb']:.2f} GB")
        self.pkts_in_label.setText(f"📦 Paquetes Rx: {io['packets_recv']:,}")
        self.pkts_out_label.setText(f"📦 Paquetes Tx: {io['packets_sent']:,}")
        
        # 3. Gráfico
        self.update_chart()
        
        # 4. Actualizar ventana de detalles si está visible
        if self.details_dialog and self.details_dialog.isVisible():
            self.details_dialog.update_data()
    
    def update_chart(self):
        """Actualiza el gráfico de historial."""
        history = self.network_monitor.get_history()
        
        self.ax.clear()
        
        if history['timestamps'] and history['download_kbps']:
            timestamps = history['timestamps']
            download = history['download_kbps']
            upload = history['upload_kbps']
            
            now = datetime.now()
            times = [-(now - t).total_seconds() for t in timestamps]
            
            f_times, f_dl, f_ul = [], [], []
            for t, d, u in zip(times, download, upload):
                if t >= -60:
                    f_times.append(t)
                    f_dl.append(d)
                    f_ul.append(u)
            
            if f_times:
                # Download (Verde)
                self.ax.fill_between(f_times, f_dl, alpha=0.3, color='#4caf50', label='Descarga')
                self.ax.plot(f_times, f_dl, color='#4caf50', linewidth=1.5)
                
                # Upload (Azul)
                self.ax.fill_between(f_times, f_ul, alpha=0.3, color='#2196f3', label='Subida')
                self.ax.plot(f_times, f_ul, color='#2196f3', linewidth=1.5)
                
                # Ajuste de escala Y dinámico
                max_val = max(max(f_dl + [1]), max(f_ul + [1]))
                self.ax.set_ylim(0, max_val * 1.2)
                
                self.ax.legend(loc='upper left', fontsize=8)
                self.ax.grid(True, linestyle='--', alpha=0.4)
                self.ax.set_xlabel('Segundos atrás', fontsize=8)
                self.ax.set_ylabel('KB/s', fontsize=8)
                self.ax.set_xlim(-60, 0)
                
        else:
            self.ax.text(0.5, 0.5, 'Recopilando datos...', 
                        ha='center', va='center', transform=self.ax.transAxes)
        
        self.canvas.draw()
