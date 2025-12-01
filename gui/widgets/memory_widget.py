"""
Widget para monitoreo de Memoria RAM
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QProgressBar, QFrame,
                             QSizePolicy, QTableWidget, QTableWidgetItem,
                             QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime


class MemoryWidget(QWidget):
    """Widget para mostrar información de memoria RAM."""
    
    def __init__(self, memory_monitor, parent=None):
        super().__init__(parent)
        self.memory_monitor = memory_monitor
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("🧠 Monitor de Memoria RAM")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Panel superior: RAM y Swap
        top_layout = QHBoxLayout()
        
        # Grupo de RAM
        ram_group = QGroupBox("Memoria RAM")
        ram_layout = QVBoxLayout(ram_group)
        
        self.ram_usage_label = QLabel("0%")
        self.ram_usage_label.setFont(QFont('Arial', 32, QFont.Bold))
        self.ram_usage_label.setAlignment(Qt.AlignCenter)
        self.ram_usage_label.setStyleSheet("color: #9c27b0;")
        
        self.ram_progress = QProgressBar()
        self.ram_progress.setRange(0, 100)
        self.ram_progress.setTextVisible(True)
        self.ram_progress.setFixedHeight(30)
        self.ram_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #9c27b0;
                border-radius: 3px;
            }
        """)
        
        self.ram_details = QLabel("Usado: 0 GB / Total: 0 GB")
        self.ram_details.setAlignment(Qt.AlignCenter)
        
        ram_layout.addWidget(self.ram_usage_label)
        ram_layout.addWidget(self.ram_progress)
        ram_layout.addWidget(self.ram_details)
        
        # Grupo de Swap
        swap_group = QGroupBox("Memoria Swap")
        swap_layout = QVBoxLayout(swap_group)
        
        self.swap_usage_label = QLabel("0%")
        self.swap_usage_label.setFont(QFont('Arial', 32, QFont.Bold))
        self.swap_usage_label.setAlignment(Qt.AlignCenter)
        self.swap_usage_label.setStyleSheet("color: #ff5722;")
        
        self.swap_progress = QProgressBar()
        self.swap_progress.setRange(0, 100)
        self.swap_progress.setTextVisible(True)
        self.swap_progress.setFixedHeight(30)
        self.swap_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #ff5722;
                border-radius: 3px;
            }
        """)
        
        self.swap_details = QLabel("Usado: 0 GB / Total: 0 GB")
        self.swap_details.setAlignment(Qt.AlignCenter)
        
        swap_layout.addWidget(self.swap_usage_label)
        swap_layout.addWidget(self.swap_progress)
        swap_layout.addWidget(self.swap_details)
        
        top_layout.addWidget(ram_group)
        top_layout.addWidget(swap_group)
        layout.addLayout(top_layout)
        
        # Panel de detalles de memoria
        details_group = QGroupBox("Detalles de Memoria")
        details_layout = QGridLayout(details_group)
        
        self.total_label = QLabel("Total: -")
        self.available_label = QLabel("Disponible: -")
        self.used_label = QLabel("En Uso: -")
        self.free_label = QLabel("Libre: -")
        
        for i, label in enumerate([self.total_label, self.available_label, 
                                   self.used_label, self.free_label]):
            label.setStyleSheet("padding: 8px; background-color: #f3e5f5; border-radius: 5px;")
            details_layout.addWidget(label, 0, i)
        
        layout.addWidget(details_group)
        
        # Panel de fragmentación (EXTRA)
        frag_group = QGroupBox("⭐ Análisis de Fragmentación (Punto Extra)")
        frag_layout = QVBoxLayout(frag_group)
        
        self.frag_ratio_label = QLabel("Índice de Fragmentación: Calculando...")
        self.frag_ratio_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.frag_ratio_label.setAlignment(Qt.AlignCenter)
        
        self.frag_progress = QProgressBar()
        self.frag_progress.setRange(0, 100)
        self.frag_progress.setTextVisible(True)
        self.frag_progress.setFixedHeight(25)
        
        self.frag_details = QLabel("Analizando memoria...")
        self.frag_details.setWordWrap(True)
        self.frag_details.setStyleSheet("padding: 10px; background-color: #fff3e0; border-radius: 5px;")
        
        frag_layout.addWidget(self.frag_ratio_label)
        frag_layout.addWidget(self.frag_progress)
        frag_layout.addWidget(self.frag_details)
        
        layout.addWidget(frag_group)
        
        # Gráfico de historial
        chart_group = QGroupBox("Historial de Uso (Última Hora)")
        chart_layout = QVBoxLayout(chart_group)
        
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.figure.patch.set_facecolor('#f0f0f0')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.figure.add_subplot(111)
        
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_group)
        
    def update_data(self):
        """Actualiza los datos del widget."""
        stats = self.memory_monitor.get_current_stats()
        
        # Actualizar RAM
        mem = stats['memory']
        self.ram_usage_label.setText(f"{mem['percent']:.1f}%")
        self.ram_progress.setValue(int(mem['percent']))
        self.ram_details.setText(f"Usado: {mem['used_gb']:.2f} GB / Total: {mem['total_gb']:.2f} GB")
        
        # Color según uso
        if mem['percent'] > 80:
            color = "#f44336"
        elif mem['percent'] > 60:
            color = "#ff9800"
        else:
            color = "#9c27b0"
        
        self.ram_usage_label.setStyleSheet(f"color: {color};")
        self.ram_progress.setStyleSheet(f"""
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
        
        # Actualizar Swap
        swap = stats['swap']
        self.swap_usage_label.setText(f"{swap['percent']:.1f}%")
        self.swap_progress.setValue(int(swap['percent']))
        self.swap_details.setText(f"Usado: {swap['used_gb']:.2f} GB / Total: {swap['total_gb']:.2f} GB")
        
        # Actualizar detalles
        self.total_label.setText(f"Total: {mem['total_gb']:.2f} GB")
        self.available_label.setText(f"Disponible: {mem['available_gb']:.2f} GB")
        self.used_label.setText(f"En Uso: {mem['used_gb']:.2f} GB")
        self.free_label.setText(f"Libre: {mem['free_gb']:.2f} GB")
        
        # Actualizar fragmentación
        frag = stats['fragmentation']
        frag_ratio = frag['fragmentation_ratio'] * 100
        
        self.frag_ratio_label.setText(f"Índice de Fragmentación: {frag_ratio:.1f}%")
        self.frag_progress.setValue(int(frag_ratio))
        
        # Color según fragmentación
        if frag_ratio > 50:
            frag_color = "#f44336"
            frag_status = "Alta fragmentación"
        elif frag_ratio > 25:
            frag_color = "#ff9800"
            frag_status = "Fragmentación moderada"
        else:
            frag_color = "#4caf50"
            frag_status = "Baja fragmentación"
        
        self.frag_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {frag_color};
                border-radius: 3px;
            }}
        """)
        
        # Detalles de fragmentación
        if frag.get('available'):
            details_text = f"Estado: {frag_status}\n"
            if 'zones' in frag:
                details_text += "Información de zonas de memoria disponible (buddyinfo)"
            elif 'vm_stat' in frag:
                details_text += "Información de vm_stat disponible"
        else:
            details_text = f"Estado: {frag_status}\n"
            details_text += f"Diferencia entre memoria libre ({mem['free_gb']:.2f} GB) y disponible ({mem['available_gb']:.2f} GB) "
            details_text += "indica el nivel de fragmentación."
        
        self.frag_details.setText(details_text)
        
        # Actualizar gráfico
        self.update_chart()
    
    def update_chart(self):
        """Actualiza el gráfico de historial."""
        history = self.memory_monitor.get_history()
        
        self.ax.clear()
        
        if history['timestamps'] and history['memory_percent']:
            timestamps = history['timestamps']
            mem_percent = history['memory_percent']
            swap_percent = history['swap_percent']
            
            now = datetime.now()
            times_relative = [-(now - t).total_seconds() / 60 for t in timestamps]
            
            # Gráfico de RAM
            self.ax.fill_between(times_relative, mem_percent, alpha=0.3, color='#9c27b0', label='RAM')
            self.ax.plot(times_relative, mem_percent, color='#9c27b0', linewidth=2)
            
            # Gráfico de Swap
            if any(s > 0 for s in swap_percent):
                self.ax.fill_between(times_relative, swap_percent, alpha=0.3, color='#ff5722', label='Swap')
                self.ax.plot(times_relative, swap_percent, color='#ff5722', linewidth=2, linestyle='--')
            
            self.ax.set_xlim(-60, 0)
            self.ax.set_ylim(0, 100)
            self.ax.set_xlabel('Tiempo (minutos)')
            self.ax.set_ylabel('Uso (%)')
            self.ax.grid(True, alpha=0.3)
            self.ax.legend(loc='upper left')
            self.ax.set_title('Uso de Memoria en el tiempo')
        else:
            self.ax.text(0.5, 0.5, 'Recopilando datos...', 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.ax.set_xlim(-60, 0)
            self.ax.set_ylim(0, 100)
        
        self.figure.tight_layout()
        self.canvas.draw()
