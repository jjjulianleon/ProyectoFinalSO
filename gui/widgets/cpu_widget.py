"""
Widget para monitoreo de CPU (Estilo Ubuntu System Monitor)
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
import numpy as np

class CPUWidget(QWidget):
    """
    Widget de CPU con estilo Ubuntu System Monitor (Dark Mode).
    Muestra un gráfico de historia multilínea y una leyenda de núcleos abajo.
    """
    
    def __init__(self, cpu_monitor, parent=None):
        super().__init__(parent)
        self.cpu_monitor = cpu_monitor
        
        # Paleta de colores vibrantes estilo Ubuntu/GNOME para los núcleos
        # Se repetirán si hay más núcleos que colores
        self.core_colors = [
            '#FF2D2D', # Rojo brillante
            '#FF8F00', # Naranja
            '#FFD600', # Amarillo
            '#00E676', # Verde
            '#00B0FF', # Azul claro
            '#2979FF', # Azul
            '#651FFF', # Índigo
            '#AA00FF', # Púrpura
            '#FF00EA', # Magenta
            '#FF1744', # Rojo rosado
            '#00E5FF', # Cyan
            '#76FF03', # Lima
        ]
        
        self.core_labels = [] # Para guardar referencias a los labels y actualizarlos
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz oscura."""
        # Forzar estilo oscuro para este widget
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', 'Arial';
            }
            QGroupBox {
                border: none;
                margin-top: 10px;
                font-weight: bold;
                color: #cccccc;
            }
            QLabel {
                color: #eeeeee;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # --- Cabecera ---
        header_layout = QHBoxLayout()
        title = QLabel("CPU")
        title.setFont(QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # --- Gráfico Histórico (Estilo GNOME) ---
        # Fondo oscuro, sin bordes blancos
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.figure.patch.set_facecolor('#1e1e1e') # Fondo de la figura
        
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setStyleSheet("background-color: #1e1e1e;")
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1e1e1e') # Fondo del plot
        
        # Configurar ejes para que parezca monitor de sistema
        self.ax.grid(True, color='#444444', linestyle='-', linewidth=0.5)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, 60)
        
        # Eliminar bordes innecesarios (spines)
        for spine in self.ax.spines.values():
            spine.set_color('#444444')
            
        # Colores de los textos de los ejes
        self.ax.tick_params(axis='x', colors='#888888', labelsize=8)
        self.ax.tick_params(axis='y', colors='#888888', labelsize=8)
        
        # Formato eje X (segundos)
        self.ax.set_xticklabels(['60 segs', '50', '40', '30', '20', '10', '0'])
        
        # Layout del gráfico
        self.figure.tight_layout()
        
        graph_container = QFrame()
        graph_container.setStyleSheet("border: 1px solid #333333; border-radius: 4px;")
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(0,0,0,0)
        graph_layout.addWidget(self.canvas)
        
        layout.addWidget(graph_container)
        
        # --- Cuadrícula de Núcleos (Leyenda) ---
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(5, 10, 5, 0)
        
        layout.addWidget(self.grid_container)
        layout.addStretch() # Empujar todo hacia arriba

    def update_data(self):
        """Actualiza los datos numéricos y el gráfico."""
        stats = self.cpu_monitor.get_current_stats()
        per_cpu = stats['per_cpu_percent']
        
        # 1. Crear widgets de núcleos si no existen (primera ejecución)
        if not self.core_labels:
            cols = 4 # 4 columnas como en la imagen
            for i in range(len(per_cpu)):
                row = i // cols
                col = i % cols
                color = self.core_colors[i % len(self.core_colors)]
                
                # Widget contenedor para un núcleo
                core_widget = QWidget()
                h_layout = QHBoxLayout(core_widget)
                h_layout.setContentsMargins(0, 0, 0, 0)
                h_layout.setSpacing(8)
                
                # Cuadro de color (Leyenda)
                color_box = QLabel()
                color_box.setFixedSize(12, 12)
                color_box.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
                
                # Texto "CPU X"
                name_label = QLabel(f"CPU {i+1}")
                name_label.setFont(QFont('Arial', 9))
                name_label.setStyleSheet("color: #bbbbbb;")
                
                # Texto Porcentaje (se actualizará)
                percent_label = QLabel("0.0%")
                percent_label.setFont(QFont('Arial', 9, QFont.Bold))
                percent_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                h_layout.addWidget(color_box)
                h_layout.addWidget(name_label)
                h_layout.addWidget(percent_label)
                h_layout.addStretch()
                
                self.grid_layout.addWidget(core_widget, row, col)
                self.core_labels.append(percent_label)

        # 2. Actualizar textos de porcentajes
        for i, usage in enumerate(per_cpu):
            if i < len(self.core_labels):
                self.core_labels[i].setText(f"{usage:.1f}%")
        
        # 3. Actualizar Gráfico
        self.update_chart()

    def update_chart(self):
        """Dibuja las líneas superpuestas para cada núcleo."""
        history = self.cpu_monitor.get_history()
        
        # Obtener historial por núcleo
        # history['per_cpu_usage'] es una lista de listas: [ [cpu0, cpu1...], [cpu0, cpu1...] ]
        # Necesitamos transponerlo para plotear línea por línea.
        per_cpu_history = history.get('per_cpu_usage', [])
        
        if not per_cpu_history:
            return

        # Convertir a numpy array para facilitar manejo [tiempo, nucleos]
        data_np = np.array(per_cpu_history)
        
        # Si no hay suficientes datos, no dibujar
        if data_np.shape[0] < 2:
            return
            
        # Transponer para tener [nucleos, tiempo]
        # data_t[0] será el historial del núcleo 0, data_t[1] del núcleo 1, etc.
        data_t = data_np.T 
        
        self.ax.clear()
        
        # Re-aplicar estilos del grid tras limpiar
        self.ax.grid(True, color='#444444', linestyle='-', linewidth=0.5)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, 60)
        self.ax.set_xticklabels([]) # Quitar etiquetas internas para limpieza visual
        
        # Generar eje X (tiempo relativo)
        points = data_np.shape[0]
        x_axis = np.arange(points)
        
        # Si hay más de 60 puntos, recortar para mostrar solo los últimos 60 (ventana deslizante)
        if points > 60:
            x_axis = np.arange(60)
            data_t = data_t[:, -60:]
        
        # Dibujar una línea por cada núcleo
        for i in range(data_t.shape[0]):
            color = self.core_colors[i % len(self.core_colors)]
            # Linea fina
            self.ax.plot(x_axis, data_t[i], color=color, linewidth=1.5, alpha=0.9)
            
            # Opcional: Relleno muy sutil bajo la línea (como en algunos monitores)
            # self.ax.fill_between(x_axis, data_t[i], color=color, alpha=0.05)

        self.canvas.draw()
