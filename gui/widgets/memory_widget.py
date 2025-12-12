"""
Widget para monitoreo de Memoria RAM
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QProgressBar, QSizePolicy, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
import numpy as np


class MemoryWidget(QWidget):
    """Widget para mostrar información de memoria RAM con gráficos mejorados."""
    
    def __init__(self, memory_monitor, parent=None):
        super().__init__(parent)
        self.memory_monitor = memory_monitor
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # --- Título ---
        title = QLabel("🧠 Monitor de Memoria RAM")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # --- Panel Superior: Distribución Actual ---
        top_panel = QHBoxLayout()
        
        # Grupo 1: Distribución de RAM (Gráfico de Donas)
        ram_group = QGroupBox("Distribución de RAM")
        ram_layout = QHBoxLayout(ram_group)
        
        # Figura para el donut chart
        self.donut_figure = Figure(figsize=(4, 3), dpi=100)
        self.donut_figure.patch.set_facecolor('#f0f0f0')
        self.donut_canvas = FigureCanvas(self.donut_figure)
        self.donut_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax_donut = self.donut_figure.add_subplot(111)
        
        ram_layout.addWidget(self.donut_canvas)
        
        # Panel lateral con detalles numéricos
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setAlignment(Qt.AlignCenter)
        
        self.ram_usage_label = QLabel("0%")
        self.ram_usage_label.setFont(QFont('Arial', 28, QFont.Bold))
        self.ram_usage_label.setAlignment(Qt.AlignCenter)
        self.ram_usage_label.setStyleSheet("color: #9c27b0;")
        
        self.ram_total_label = QLabel("Total: 0 GB")
        self.ram_used_label = QLabel("Usado: 0 GB")
        self.ram_free_label = QLabel("Libre: 0 GB")
        
        # Estilo para etiquetas
        for lbl in [self.ram_total_label, self.ram_used_label, self.ram_free_label]:
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 12px; padding: 2px;")
            
        details_layout.addWidget(self.ram_usage_label)
        details_layout.addWidget(self.ram_total_label)
        details_layout.addWidget(self.ram_used_label)
        details_layout.addWidget(self.ram_free_label)
        
        ram_layout.addWidget(details_panel)
        ram_layout.setStretch(0, 2)
        ram_layout.setStretch(1, 1)
        
        top_panel.addWidget(ram_group)
        
        # Grupo 2: Swap y Fragmentación
        right_group = QGroupBox("Estado del Sistema")
        right_layout = QVBoxLayout(right_group)
        right_layout.setSpacing(15)
        
        # Swap
        swap_container = QWidget()
        swap_layout = QVBoxLayout(swap_container)
        swap_layout.setContentsMargins(0,0,0,0)
        
        swap_title = QLabel("Memoria Swap")
        swap_title.setFont(QFont('Arial', 10, QFont.Bold))
        
        self.swap_progress = QProgressBar()
        self.swap_progress.setRange(0, 100)
        self.swap_progress.setTextVisible(True)
        self.swap_progress.setFormat("%p% Usado")
        self.swap_progress.setFixedHeight(20)
        self.swap_progress.setStyleSheet("""
            QProgressBar { border: 1px solid #bbb; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background-color: #ff5722; }
        """)
        
        self.swap_details = QLabel("0 GB / 0 GB")
        self.swap_details.setAlignment(Qt.AlignRight)
        self.swap_details.setStyleSheet("color: #666; font-size: 10px;")
        
        swap_layout.addWidget(swap_title)
        swap_layout.addWidget(self.swap_progress)
        swap_layout.addWidget(self.swap_details)
        right_layout.addWidget(swap_container)
        
        # Fragmentación
        frag_container = QWidget()
        frag_layout = QVBoxLayout(frag_container)
        frag_layout.setContentsMargins(0,0,0,0)
        
        frag_title = QLabel("Fragmentación de Memoria")
        frag_title.setFont(QFont('Arial', 10, QFont.Bold))
        
        self.frag_progress = QProgressBar()
        self.frag_progress.setRange(0, 100)
        self.frag_progress.setTextVisible(True)
        self.frag_progress.setFormat("%p% Índice")
        self.frag_progress.setFixedHeight(20)
        
        self.frag_status = QLabel("Analizando...")
        self.frag_status.setWordWrap(True)
        self.frag_status.setStyleSheet("font-size: 10px; color: #555;")
        
        frag_layout.addWidget(frag_title)
        frag_layout.addWidget(self.frag_progress)
        frag_layout.addWidget(self.frag_status)
        right_layout.addWidget(frag_container)
        
        right_layout.addStretch()
        top_panel.addWidget(right_group)
        
        layout.addLayout(top_panel)
        
        # --- Gráfico de Historial ---
        chart_group = QGroupBox("Historial de Uso (Último Minuto)")
        chart_layout = QVBoxLayout(chart_group)
        
        self.history_figure = Figure(figsize=(8, 2.5), dpi=100)
        self.history_figure.patch.set_facecolor('#f0f0f0')
        self.history_figure.subplots_adjust(bottom=0.2, top=0.9, left=0.08, right=0.98)
        
        self.history_canvas = FigureCanvas(self.history_figure)
        self.history_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax_history = self.history_figure.add_subplot(111)
        
        chart_layout.addWidget(self.history_canvas)
        layout.addWidget(chart_group)

    def update_data(self):
        """Actualiza los datos del widget."""
        stats = self.memory_monitor.get_current_stats()
        mem = stats['memory']
        swap = stats['swap']
        frag = stats['fragmentation']
        
        # --- Actualizar Etiquetas ---
        self.ram_usage_label.setText(f"{mem['percent']:.1f}%")
        self.ram_total_label.setText(f"Total: {mem['total_gb']:.1f} GB")
        self.ram_used_label.setText(f"Usado: {mem['used_gb']:.1f} GB")
        self.ram_free_label.setText(f"Libre: {mem['free_gb']:.1f} GB")
        
        # Color del porcentaje
        if mem['percent'] > 85:
            self.ram_usage_label.setStyleSheet("color: #f44336;") # Rojo
        elif mem['percent'] > 60:
            self.ram_usage_label.setStyleSheet("color: #ff9800;") # Naranja
        else:
            self.ram_usage_label.setStyleSheet("color: #9c27b0;") # Púrpura
            
        # --- Actualizar Swap ---
        self.swap_progress.setValue(int(swap['percent']))
        self.swap_details.setText(f"{swap['used_gb']:.2f} GB / {swap['total_gb']:.2f} GB")
        
        # --- Actualizar Fragmentación ---
        frag_ratio = frag['fragmentation_ratio'] * 100
        self.frag_progress.setValue(int(frag_ratio))
        
        # Color fragmentación
        if frag_ratio > 50:
            frag_col = "#f44336"
            status_txt = "Alta"
        elif frag_ratio > 20:
            frag_col = "#ff9800"
            status_txt = "Moderada"
        else:
            frag_col = "#4caf50"
            status_txt = "Baja"
            
        self.frag_progress.setStyleSheet(f"""
            QProgressBar {{ border: 1px solid #bbb; border-radius: 4px; text-align: center; }}
            QProgressBar::chunk {{ background-color: {frag_col}; }}
        """)
        self.frag_status.setText(f"Nivel: {status_txt}")
        
        # --- Actualizar Gráficos ---
        self.update_donut_chart(mem)
        self.update_history_chart()
        
    def update_donut_chart(self, mem):
        """Dibuja el gráfico de donas para la RAM."""
        self.ax_donut.clear()
        
        # Datos: Usado, Libre (y Disponible que es técnicamente Free + Cache)
        # Para simplificar visualmente usamos Used vs Available (que es lo "realmente" libre)
        sizes = [mem['used'], mem['available']]
        labels = ['', '']
        colors = ['#9c27b0', '#e1bee7'] # Púrpura oscuro, Púrpura claro
        
        # Crear donut
        wedges, _ = self.ax_donut.pie(sizes, labels=labels, colors=colors, startangle=90, 
                                      wedgeprops=dict(width=0.4, edgecolor='w'))
        
        # Texto central
        self.ax_donut.text(0, 0, "RAM", ha='center', va='center', fontsize=12, fontweight='bold', color='#555')
        
        self.donut_canvas.draw()
        
    def update_history_chart(self):
        """Actualiza el gráfico de historial (RAM y Swap)."""
        history = self.memory_monitor.get_history()
        self.ax_history.clear()
        
        if history['timestamps'] and history['memory_percent']:
            timestamps = history['timestamps']
            mem_p = history['memory_percent']
            swap_p = history['swap_percent']
            
            # Segundos relativos
            now = datetime.now()
            times = [-(now - t).total_seconds() for t in timestamps]
            
            # Filtrar últimos 60s
            f_times, f_mem, f_swap = [], [], []
            for t, m, s in zip(times, mem_p, swap_p):
                if t >= -60:
                    f_times.append(t)
                    f_mem.append(m)
                    f_swap.append(s)
            
            if f_times:
                # RAM
                self.ax_history.plot(f_times, f_mem, color='#9c27b0', linewidth=2, label='RAM')
                self.ax_history.fill_between(f_times, f_mem, color='#9c27b0', alpha=0.2)
                
                # Swap (solo si hay uso)
                if any(s > 0 for s in f_swap):
                    self.ax_history.plot(f_times, f_swap, color='#ff5722', linewidth=2, linestyle='--', label='Swap')
            
            self.ax_history.set_ylim(0, 100)
            self.ax_history.set_xlim(-60, 0)
            self.ax_history.grid(True, linestyle='--', alpha=0.4)
            self.ax_history.set_xlabel("Segundos atrás", fontsize=8)
            self.ax_history.set_ylabel("Uso (%)", fontsize=9)
            self.ax_history.legend(loc='upper left', fontsize=8)
            
        else:
            self.ax_history.text(0.5, 0.5, 'Recopilando datos...', 
                                ha='center', va='center', transform=self.ax_history.transAxes)
        
        self.history_canvas.draw()
