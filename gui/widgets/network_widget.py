"""
Widget para monitoreo de Red
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QProgressBar, QFrame,
                             QSizePolicy, QTableWidget, QTableWidgetItem,
                             QHeaderView, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime


class NetworkWidget(QWidget):
    """Widget para mostrar información de red."""
    
    def __init__(self, network_monitor, parent=None):
        super().__init__(parent)
        self.network_monitor = network_monitor
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("🌐 Monitor de Red")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Panel de velocidades actuales
        speed_group = QGroupBox("Velocidad Actual de Red")
        speed_layout = QHBoxLayout(speed_group)
        
        # Download
        download_widget = QWidget()
        download_layout = QVBoxLayout(download_widget)
        download_layout.setAlignment(Qt.AlignCenter)
        
        download_icon = QLabel("⬇️")
        download_icon.setFont(QFont('Arial', 32))
        download_icon.setAlignment(Qt.AlignCenter)
        
        self.download_speed_label = QLabel("0 KB/s")
        self.download_speed_label.setFont(QFont('Arial', 24, QFont.Bold))
        self.download_speed_label.setAlignment(Qt.AlignCenter)
        self.download_speed_label.setStyleSheet("color: #4caf50;")
        
        download_title = QLabel("Download")
        download_title.setAlignment(Qt.AlignCenter)
        
        download_layout.addWidget(download_icon)
        download_layout.addWidget(self.download_speed_label)
        download_layout.addWidget(download_title)
        
        download_widget.setStyleSheet("background-color: #e8f5e9; border-radius: 10px; padding: 10px;")
        
        # Upload
        upload_widget = QWidget()
        upload_layout = QVBoxLayout(upload_widget)
        upload_layout.setAlignment(Qt.AlignCenter)
        
        upload_icon = QLabel("⬆️")
        upload_icon.setFont(QFont('Arial', 32))
        upload_icon.setAlignment(Qt.AlignCenter)
        
        self.upload_speed_label = QLabel("0 KB/s")
        self.upload_speed_label.setFont(QFont('Arial', 24, QFont.Bold))
        self.upload_speed_label.setAlignment(Qt.AlignCenter)
        self.upload_speed_label.setStyleSheet("color: #2196f3;")
        
        upload_title = QLabel("Upload")
        upload_title.setAlignment(Qt.AlignCenter)
        
        upload_layout.addWidget(upload_icon)
        upload_layout.addWidget(self.upload_speed_label)
        upload_layout.addWidget(upload_title)
        
        upload_widget.setStyleSheet("background-color: #e3f2fd; border-radius: 10px; padding: 10px;")
        
        speed_layout.addWidget(download_widget)
        speed_layout.addWidget(upload_widget)
        
        layout.addWidget(speed_group)
        
        # Panel de estadísticas totales
        stats_group = QGroupBox("Estadísticas Totales")
        stats_layout = QGridLayout(stats_group)
        
        self.total_download_label = QLabel("Total Descargado: 0 GB")
        self.total_upload_label = QLabel("Total Subido: 0 GB")
        self.packets_recv_label = QLabel("Paquetes Recibidos: 0")
        self.packets_sent_label = QLabel("Paquetes Enviados: 0")
        self.errors_label = QLabel("Errores: 0")
        self.drops_label = QLabel("Drops: 0")
        
        labels = [self.total_download_label, self.total_upload_label,
                  self.packets_recv_label, self.packets_sent_label,
                  self.errors_label, self.drops_label]
        
        for i, label in enumerate(labels):
            label.setStyleSheet("padding: 8px; background-color: #f5f5f5; border-radius: 5px;")
            row, col = divmod(i, 2)
            stats_layout.addWidget(label, row, col)
        
        layout.addWidget(stats_group)
        
        # Tabs para gráfico e interfaces
        tabs = QTabWidget()
        
        # Tab de gráfico
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.figure.patch.set_facecolor('#f0f0f0')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.figure.add_subplot(111)
        
        chart_layout.addWidget(self.canvas)
        tabs.addTab(chart_widget, "📊 Historial")
        
        # Tab de interfaces
        interfaces_widget = QWidget()
        interfaces_layout = QVBoxLayout(interfaces_widget)
        
        self.interfaces_table = QTableWidget()
        self.interfaces_table.setColumnCount(5)
        self.interfaces_table.setHorizontalHeaderLabels([
            "Interfaz", "Estado", "Dirección IP", "Velocidad (Mbps)", "MTU"
        ])
        
        header = self.interfaces_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        interfaces_layout.addWidget(self.interfaces_table)
        tabs.addTab(interfaces_widget, "🔌 Interfaces")
        
        # Tab de conexiones
        connections_widget = QWidget()
        connections_layout = QVBoxLayout(connections_widget)
        
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(5)
        self.connections_table.setHorizontalHeaderLabels([
            "Local", "Remoto", "Estado", "PID", "Proceso"
        ])
        
        header = self.connections_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.connections_count_label = QLabel("Conexiones activas: 0")
        
        connections_layout.addWidget(self.connections_count_label)
        connections_layout.addWidget(self.connections_table)
        tabs.addTab(connections_widget, "🔗 Conexiones")
        
        layout.addWidget(tabs)
        
    def update_data(self):
        """Actualiza los datos del widget."""
        stats = self.network_monitor.get_current_stats()
        
        # Actualizar velocidades
        speeds = stats['speeds']
        self.download_speed_label.setText(speeds['download']['formatted'])
        self.upload_speed_label.setText(speeds['upload']['formatted'])
        
        # Actualizar estadísticas
        io = stats['io_counters']
        self.total_download_label.setText(f"⬇️ Total Descargado: {io['bytes_recv_gb']:.2f} GB")
        self.total_upload_label.setText(f"⬆️ Total Subido: {io['bytes_sent_gb']:.2f} GB")
        self.packets_recv_label.setText(f"📥 Paquetes Recibidos: {io['packets_recv']:,}")
        self.packets_sent_label.setText(f"📤 Paquetes Enviados: {io['packets_sent']:,}")
        self.errors_label.setText(f"❌ Errores: In={io['errin']:,} / Out={io['errout']:,}")
        self.drops_label.setText(f"🚫 Drops: In={io['dropin']:,} / Out={io['dropout']:,}")
        
        # Actualizar interfaces
        interfaces = stats['interfaces']
        self.interfaces_table.setRowCount(len(interfaces))
        
        for row, iface in enumerate(interfaces):
            self.interfaces_table.setItem(row, 0, QTableWidgetItem(iface['name']))
            
            status_item = QTableWidgetItem("🟢 Activa" if iface['is_up'] else "🔴 Inactiva")
            status_item.setBackground(QColor('#c8e6c9' if iface['is_up'] else '#ffcdd2'))
            self.interfaces_table.setItem(row, 1, status_item)
            
            # Buscar dirección IPv4
            ipv4 = ""
            for addr in iface['addresses']:
                if 'AF_INET' in addr['family'] and addr['address']:
                    ipv4 = addr['address']
                    break
            self.interfaces_table.setItem(row, 2, QTableWidgetItem(ipv4 or "N/A"))
            
            self.interfaces_table.setItem(row, 3, QTableWidgetItem(str(iface['speed'])))
            self.interfaces_table.setItem(row, 4, QTableWidgetItem(str(iface['mtu'])))
        
        # Actualizar conexiones
        try:
            connections = self.network_monitor.get_connections()
            self.connections_count_label.setText(f"Conexiones activas: {len(connections)}")
            
            # Mostrar solo las primeras 50 conexiones para rendimiento
            display_connections = connections[:50]
            self.connections_table.setRowCount(len(display_connections))
            
            for row, conn in enumerate(display_connections):
                local = f"{conn['local_address']}:{conn['local_port']}"
                remote = f"{conn['remote_address']}:{conn['remote_port']}" if conn['remote_address'] else "-"
                
                self.connections_table.setItem(row, 0, QTableWidgetItem(local))
                self.connections_table.setItem(row, 1, QTableWidgetItem(remote))
                
                status_item = QTableWidgetItem(conn['status'])
                if conn['status'] == 'ESTABLISHED':
                    status_item.setBackground(QColor('#c8e6c9'))
                elif conn['status'] == 'LISTEN':
                    status_item.setBackground(QColor('#e3f2fd'))
                self.connections_table.setItem(row, 2, status_item)
                
                self.connections_table.setItem(row, 3, QTableWidgetItem(str(conn['pid'] or "-")))
                self.connections_table.setItem(row, 4, QTableWidgetItem(conn.get('process_name', '-')))
        except Exception:
            pass
        
        # Actualizar gráfico
        self.update_chart()
    
    def update_chart(self):
        """Actualiza el gráfico de historial."""
        history = self.network_monitor.get_history()
        
        self.ax.clear()
        
        if history['timestamps'] and history['download_kbps']:
            timestamps = history['timestamps']
            download = history['download_kbps']
            upload = history['upload_kbps']
            
            now = datetime.now()
            times_relative = [-(now - t).total_seconds() / 60 for t in timestamps]
            
            # Gráfico de download
            self.ax.fill_between(times_relative, download, alpha=0.3, color='#4caf50', label='Download')
            self.ax.plot(times_relative, download, color='#4caf50', linewidth=2)
            
            # Gráfico de upload
            self.ax.fill_between(times_relative, upload, alpha=0.3, color='#2196f3', label='Upload')
            self.ax.plot(times_relative, upload, color='#2196f3', linewidth=2)
            
            max_val = max(max(download + [1]), max(upload + [1]))
            
            self.ax.set_xlim(-60, 0)
            self.ax.set_ylim(0, max_val * 1.1)
            self.ax.set_xlabel('Tiempo (minutos)')
            self.ax.set_ylabel('Velocidad (KB/s)')
            self.ax.grid(True, alpha=0.3)
            self.ax.legend(loc='upper left')
            self.ax.set_title('Ancho de Banda - Upload y Download')
        else:
            self.ax.text(0.5, 0.5, 'Recopilando datos...', 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.ax.set_xlim(-60, 0)
            self.ax.set_ylim(0, 100)
        
        self.figure.tight_layout()
        self.canvas.draw()
