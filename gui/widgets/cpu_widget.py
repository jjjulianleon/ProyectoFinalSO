"""
Widget para monitoreo de CPU
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QProgressBar, QFrame,
                             QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime, timedelta
import numpy as np


class CPUWidget(QWidget):
    """Widget para mostrar información de CPU."""
    
    def __init__(self, cpu_monitor, parent=None):
        super().__init__(parent)
        self.cpu_monitor = cpu_monitor
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("📊 Monitor de CPU")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Panel superior: información actual
        info_group = QGroupBox("Estado Actual")
        info_layout = QGridLayout(info_group)
        
        # Uso total de CPU
        self.total_usage_label = QLabel("Uso Total:")
        self.total_usage_value = QLabel("0%")
        self.total_usage_value.setFont(QFont('Arial', 24, QFont.Bold))
        self.total_usage_value.setStyleSheet("color: #2196F3;")
        
        self.total_progress = QProgressBar()
        self.total_progress.setRange(0, 100)
        self.total_progress.setTextVisible(True)
        self.total_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)
        
        info_layout.addWidget(self.total_usage_label, 0, 0)
        info_layout.addWidget(self.total_usage_value, 0, 1)
        info_layout.addWidget(self.total_progress, 1, 0, 1, 2)
        
        # Información de CPU
        self.cpu_count_label = QLabel("Núcleos: -")
        self.cpu_freq_label = QLabel("Frecuencia: -")
        self.load_avg_label = QLabel("Load Average: -")
        
        info_layout.addWidget(self.cpu_count_label, 2, 0)
        info_layout.addWidget(self.cpu_freq_label, 2, 1)
        info_layout.addWidget(self.load_avg_label, 3, 0, 1, 2)
        
        layout.addWidget(info_group)
        
        # Panel de núcleos individuales
        self.cores_group = QGroupBox("Uso por Núcleo")
        self.cores_layout = QGridLayout(self.cores_group)
        self.core_progress_bars = []
        layout.addWidget(self.cores_group)
        
        # Gráfico de historial
        chart_group = QGroupBox("Historial de Uso (Tiempo Real - 60 segundos)")
        chart_layout = QVBoxLayout(chart_group)
        
        # Crear figura de matplotlib
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.figure.patch.set_facecolor('#f0f0f0')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.figure.add_subplot(111)
        
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_group)
        
        # Tiempos de CPU
        times_group = QGroupBox("Distribución de Tiempo de CPU")
        times_layout = QHBoxLayout(times_group)
        
        self.user_time_label = QLabel("Usuario: 0%")
        self.system_time_label = QLabel("Sistema: 0%")
        self.idle_time_label = QLabel("Inactivo: 0%")
        
        for label in [self.user_time_label, self.system_time_label, self.idle_time_label]:
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
            times_layout.addWidget(label)
        
        layout.addWidget(times_group)
        
    def update_data(self):
        """Actualiza los datos del widget."""
        stats = self.cpu_monitor.get_current_stats()
        
        # Actualizar uso total
        usage = stats['usage_percent']
        self.total_usage_value.setText(f"{usage:.1f}%")
        self.total_progress.setValue(int(usage))
        
        # Cambiar color según uso
        if usage > 80:
            color = "#f44336"  # Rojo
        elif usage > 60:
            color = "#ff9800"  # Naranja
        else:
            color = "#4caf50"  # Verde
        
        self.total_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        
        # Actualizar información de CPU
        cpu_count = stats['cpu_count']
        self.cpu_count_label.setText(f"Núcleos: {cpu_count['logical']} lógicos ({cpu_count['physical']} físicos)")
        
        if stats['frequency']:
            self.cpu_freq_label.setText(f"Frecuencia: {stats['frequency']['current']:.0f} MHz")
        
        if stats['load_average']:
            load = stats['load_average']
            self.load_avg_label.setText(f"Load Average: {load['1min']:.2f} / {load['5min']:.2f} / {load['15min']:.2f}")
        
        # Actualizar tiempos
        times = stats['times_percent']
        self.user_time_label.setText(f"Usuario: {times['user']:.1f}%")
        self.system_time_label.setText(f"Sistema: {times['system']:.1f}%")
        self.idle_time_label.setText(f"Inactivo: {times['idle']:.1f}%")
        
        # Actualizar barras de núcleos
        per_cpu = stats['per_cpu_percent']
        
        # Crear barras si no existen
        if len(self.core_progress_bars) != len(per_cpu):
            # Limpiar layout
            for i in reversed(range(self.cores_layout.count())): 
                self.cores_layout.itemAt(i).widget().setParent(None)
            self.core_progress_bars = []
            
            cols = 4  # Número de columnas
            for i, _ in enumerate(per_cpu):
                row = i // cols
                col = i % cols
                
                core_widget = QWidget()
                core_layout = QVBoxLayout(core_widget)
                core_layout.setContentsMargins(5, 5, 5, 5)
                
                label = QLabel(f"CPU {i}")
                label.setAlignment(Qt.AlignCenter)
                
                progress = QProgressBar()
                progress.setRange(0, 100)
                progress.setTextVisible(True)
                progress.setFixedHeight(20)
                
                core_layout.addWidget(label)
                core_layout.addWidget(progress)
                
                self.cores_layout.addWidget(core_widget, row, col)
                self.core_progress_bars.append(progress)
        
        # Actualizar valores
        for i, (bar, value) in enumerate(zip(self.core_progress_bars, per_cpu)):
            bar.setValue(int(value))
            
            if value > 80:
                color = "#f44336"
            elif value > 60:
                color = "#ff9800"
            else:
                color = "#4caf50"
            
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
        
        # Actualizar gráfico
        self.update_chart()
    
    def update_chart(self):
        """Actualiza el gráfico de historial."""
        history = self.cpu_monitor.get_history()
        
        self.ax.clear()
        
        if history['timestamps'] and history['cpu_usage']:
            timestamps = history['timestamps']
            usage = history['cpu_usage']
            
            # Convertir timestamps a segundos relativos (últimos 60 segundos)
            if timestamps:
                now = datetime.now()
                times_relative = [-(now - t).total_seconds() for t in timestamps]
                
                # Filtrar solo los últimos 60 segundos
                filtered_times = []
                filtered_usage = []
                for t, u in zip(times_relative, usage):
                    if t >= -60:
                        filtered_times.append(t)
                        filtered_usage.append(u)
                
                if filtered_times:
                    self.ax.fill_between(filtered_times, filtered_usage, alpha=0.3, color='#2196F3')
                    self.ax.plot(filtered_times, filtered_usage, color='#2196F3', linewidth=2)
                
                self.ax.set_xlim(-60, 0)
                self.ax.set_ylim(0, 100)
                self.ax.set_xlabel('Tiempo (segundos)')
                self.ax.set_ylabel('Uso CPU (%)')
                self.ax.grid(True, alpha=0.3)
                self.ax.set_title('Uso de CPU en tiempo real')
        else:
            self.ax.text(0.5, 0.5, 'Recopilando datos...', 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.ax.set_xlim(-60, 0)
            self.ax.set_ylim(0, 100)
        
        self.figure.tight_layout()
        self.canvas.draw()
