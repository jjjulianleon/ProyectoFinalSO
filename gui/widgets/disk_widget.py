"""
Widget para monitoreo de Almacenamiento/Disco
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QProgressBar, QFrame,
                             QSizePolicy, QTableWidget, QTableWidgetItem,
                             QHeaderView, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime


class DiskWidget(QWidget):
    """Widget para mostrar información de almacenamiento."""
    
    def __init__(self, disk_monitor, parent=None):
        super().__init__(parent)
        self.disk_monitor = disk_monitor
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("💾 Monitor de Almacenamiento")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Panel de particiones
        partitions_group = QGroupBox("Particiones del Sistema")
        partitions_layout = QVBoxLayout(partitions_group)
        
        # Área scrollable para particiones
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        
        self.partitions_container = QWidget()
        self.partitions_layout = QVBoxLayout(self.partitions_container)
        scroll.setWidget(self.partitions_container)
        
        partitions_layout.addWidget(scroll)
        layout.addWidget(partitions_group)
        
        # Panel de I/O
        io_group = QGroupBox("Estadísticas de I/O")
        io_layout = QGridLayout(io_group)
        
        self.read_speed_label = QLabel("Velocidad Lectura: 0 MB/s")
        self.write_speed_label = QLabel("Velocidad Escritura: 0 MB/s")
        self.total_read_label = QLabel("Total Leído: 0 GB")
        self.total_write_label = QLabel("Total Escrito: 0 GB")
        
        self.read_speed_label.setStyleSheet("padding: 10px; background-color: #e8f5e9; border-radius: 5px;")
        self.write_speed_label.setStyleSheet("padding: 10px; background-color: #fff3e0; border-radius: 5px;")
        self.total_read_label.setStyleSheet("padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        self.total_write_label.setStyleSheet("padding: 10px; background-color: #fce4ec; border-radius: 5px;")
        
        io_layout.addWidget(self.read_speed_label, 0, 0)
        io_layout.addWidget(self.write_speed_label, 0, 1)
        io_layout.addWidget(self.total_read_label, 1, 0)
        io_layout.addWidget(self.total_write_label, 1, 1)
        
        layout.addWidget(io_group)
        
        # Panel de fragmentación (EXTRA)
        frag_group = QGroupBox("Análisis de Fragmentación de Disco (Punto Extra)")
        frag_layout = QVBoxLayout(frag_group)
        
        self.disk_frag_label = QLabel("Analizando fragmentación...")
        self.disk_frag_label.setWordWrap(True)
        self.disk_frag_label.setStyleSheet("padding: 10px; background-color: #e8eaf6; border-radius: 5px;")
        
        self.disk_frag_details = QLabel("")
        self.disk_frag_details.setWordWrap(True)
        
        frag_layout.addWidget(self.disk_frag_label)
        frag_layout.addWidget(self.disk_frag_details)
        
        layout.addWidget(frag_group)
        
        # Gráfico de historial de I/O
        chart_group = QGroupBox("Historial de I/O (Tiempo Real - 60 segundos)")
        chart_layout = QVBoxLayout(chart_group)
        
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.figure.patch.set_facecolor('#f0f0f0')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.figure.add_subplot(111)
        
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_group)
        
        # Almacenar widgets de particiones
        self.partition_widgets = []
        
    def update_data(self):
        """Actualiza los datos del widget."""
        stats = self.disk_monitor.get_current_stats()
        
        # Actualizar particiones
        partitions = stats['partitions']
        
        # Limpiar widgets anteriores
        for widget in self.partition_widgets:
            widget.setParent(None)
        self.partition_widgets = []
        
        for part in partitions:
            if 'error' in part:
                continue
                
            part_widget = QWidget()
            part_layout = QVBoxLayout(part_widget)
            part_layout.setContentsMargins(5, 5, 5, 5)
            
            # Información de la partición
            header = QLabel(f"📁 {part['mountpoint']} ({part['device']})")
            header.setFont(QFont('Arial', 10, QFont.Bold))
            
            info = QLabel(f"Sistema: {part['fstype']} | "
                         f"Usado: {part['used_gb']:.1f} GB / {part['total_gb']:.1f} GB")
            
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(int(part['percent']))
            progress.setTextVisible(True)
            progress.setFormat(f"{part['percent']:.1f}% usado ({part['free_gb']:.1f} GB libres)")
            progress.setFixedHeight(25)
            
            # Color según uso
            if part['percent'] > 90:
                color = "#f44336"
            elif part['percent'] > 70:
                color = "#ff9800"
            else:
                color = "#4caf50"
            
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid #ddd;
                    border-radius: 5px;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
            
            part_layout.addWidget(header)
            part_layout.addWidget(info)
            part_layout.addWidget(progress)
            
            part_widget.setStyleSheet("background-color: #fafafa; border-radius: 5px; margin: 2px;")
            
            self.partitions_layout.addWidget(part_widget)
            self.partition_widgets.append(part_widget)
        
        # Actualizar I/O
        io = stats['io_counters']
        if io:
            self.read_speed_label.setText(f"Velocidad Lectura: {io['read_speed_mb']:.2f} MB/s")
            self.write_speed_label.setText(f"Velocidad Escritura: {io['write_speed_mb']:.2f} MB/s")
            self.total_read_label.setText(f"Total Leído: {io['read_bytes_gb']:.2f} GB")
            self.total_write_label.setText(f"Total Escrito: {io['write_bytes_gb']:.2f} GB")
        
        # Actualizar fragmentación
        frag = stats['fragmentation']
        
        if frag['message']:
            self.disk_frag_label.setText(f"{frag['message']}")
        
        if frag.get('fragmentation_percent', 0) > 0:
            self.disk_frag_details.setText(f"Fragmentación detectada: {frag['fragmentation_percent']:.1f}%")
        elif frag.get('available'):
            self.disk_frag_details.setText("Sistema de archivos moderno con baja fragmentación")
        else:
            self.disk_frag_details.setText("Información de fragmentación no disponible para este sistema de archivos")
        
        # Actualizar gráfico
        self.update_chart()
    
    def update_chart(self):
        """Actualiza el gráfico de historial."""
        history = self.disk_monitor.get_history()
        
        self.ax.clear()
        
        if history['timestamps'] and history['io_stats']:
            timestamps = history['timestamps']
            io_stats = history['io_stats']
            
            # Extraer velocidades
            read_speeds = []
            write_speeds = []
            
            for io in io_stats:
                if io:
                    read_speeds.append(io.get('read_speed_mb', 0))
                    write_speeds.append(io.get('write_speed_mb', 0))
                else:
                    read_speeds.append(0)
                    write_speeds.append(0)
            
            now = datetime.now()
            times_relative = [-(now - t).total_seconds() for t in timestamps]
            
            # Filtrar solo los últimos 60 segundos
            filtered_times = []
            filtered_read = []
            filtered_write = []
            for t, r, w in zip(times_relative, read_speeds, write_speeds):
                if t >= -60:
                    filtered_times.append(t)
                    filtered_read.append(r)
                    filtered_write.append(w)
            
            if filtered_times:
                # Gráfico de lectura
                self.ax.fill_between(filtered_times, filtered_read, alpha=0.3, color='#4caf50', label='Lectura')
                self.ax.plot(filtered_times, filtered_read, color='#4caf50', linewidth=2)
                
                # Gráfico de escritura
                self.ax.fill_between(filtered_times, filtered_write, alpha=0.3, color='#ff9800', label='Escritura')
                self.ax.plot(filtered_times, filtered_write, color='#ff9800', linewidth=2)
                
                max_val = max(max(filtered_read + [1]), max(filtered_write + [1]))
            else:
                max_val = 1
            
            self.ax.set_xlim(-60, 0)
            self.ax.set_ylim(0, max_val * 1.1)
            self.ax.set_xlabel('Tiempo (segundos)')
            self.ax.set_ylabel('Velocidad (MB/s)')
            self.ax.grid(True, alpha=0.3)
            self.ax.legend(loc='upper left')
            self.ax.set_title('Velocidad de I/O en tiempo real')
        else:
            self.ax.text(0.5, 0.5, 'Recopilando datos...', 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.ax.set_xlim(-60, 0)
            self.ax.set_ylim(0, 100)
        
        self.figure.tight_layout()
        self.canvas.draw()
