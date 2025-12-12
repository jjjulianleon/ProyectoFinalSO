"""
Widget para monitoreo de Almacenamiento/Disco
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QProgressBar, 
                             QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
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
        
        # --- Panel Superior: Particiones ---
        partitions_group = QGroupBox("Particiones del Sistema")
        partitions_layout = QVBoxLayout(partitions_group)
        
        # Área scrollable para particiones (por si hay muchas snaps)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(180)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.partitions_container = QWidget()
        self.partitions_layout = QVBoxLayout(self.partitions_container)
        scroll.setWidget(self.partitions_container)
        
        partitions_layout.addWidget(scroll)
        layout.addWidget(partitions_group)
        
        # --- Panel Medio: I/O y Fragmentación ---
        mid_layout = QHBoxLayout()
        
        # I/O Stats
        io_group = QGroupBox("Estadísticas de I/O")
        io_layout = QGridLayout(io_group)
        
        self.read_speed_label = QLabel("Lectura: 0 MB/s")
        self.write_speed_label = QLabel("Escritura: 0 MB/s")
        self.total_read_label = QLabel("Total Leído: 0 GB")
        self.total_write_label = QLabel("Total Escrito: 0 GB")
        
        # Estilos suaves
        lbl_style = "padding: 5px; border-radius: 4px; font-weight: bold;"
        self.read_speed_label.setStyleSheet(lbl_style + "background-color: #e8f5e9; color: #2e7d32;")
        self.write_speed_label.setStyleSheet(lbl_style + "background-color: #fff3e0; color: #ef6c00;")
        self.total_read_label.setStyleSheet(lbl_style + "background-color: #e3f2fd; color: #1565c0;")
        self.total_write_label.setStyleSheet(lbl_style + "background-color: #fce4ec; color: #c2185b;")
        
        io_layout.addWidget(self.read_speed_label, 0, 0)
        io_layout.addWidget(self.write_speed_label, 0, 1)
        io_layout.addWidget(self.total_read_label, 1, 0)
        io_layout.addWidget(self.total_write_label, 1, 1)
        
        mid_layout.addWidget(io_group)
        
        # Fragmentación (Corregido)
        frag_group = QGroupBox("Análisis de Fragmentación")
        frag_layout = QVBoxLayout(frag_group)
        
        self.disk_frag_label = QLabel("Esperando análisis...")
        self.disk_frag_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.disk_frag_label.setStyleSheet("color: #555;")
        
        self.disk_frag_details = QLabel("...")
        self.disk_frag_details.setWordWrap(True)
        self.disk_frag_details.setStyleSheet("font-size: 10px; color: #666;")
        
        frag_layout.addWidget(self.disk_frag_label)
        frag_layout.addWidget(self.disk_frag_details)
        frag_layout.addStretch()
        
        mid_layout.addWidget(frag_group)
        layout.addLayout(mid_layout)
        
        # --- Gráfico Inferior: Historial I/O ---
        chart_group = QGroupBox("Historial de I/O (Último Minuto)")
        chart_layout = QVBoxLayout(chart_group)
        
        self.figure = Figure(figsize=(8, 2.5), dpi=100)
        self.figure.patch.set_facecolor('#f0f0f0')
        self.figure.subplots_adjust(bottom=0.2, top=0.9, left=0.08, right=0.98)
        
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.figure.add_subplot(111)
        
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_group)
        
        # Lista para mantener referencias a los widgets de particiones
        self.partition_widgets = []
        
    def update_data(self):
        """Actualiza los datos del widget."""
        stats = self.disk_monitor.get_current_stats()
        
        # 1. Actualizar Particiones
        partitions = stats['partitions']
        
        # Reconstruir lista solo si cambia el número de particiones (optimización simple)
        # Ojo: Para simplicidad en este ejemplo, limpiamos y recreamos si es necesario,
        # pero idealmente solo actualizaríamos los valores.
        
        # Limpiar widgets anteriores
        for w in self.partition_widgets:
            w.setParent(None)
        self.partition_widgets = []
        
        for part in partitions:
            # Filtrar snaps y loops para no llenar la pantalla de basura en Ubuntu
            if 'loop' in part['device'] or 'snap' in part['mountpoint']:
                continue
                
            p_widget = QWidget()
            p_layout = QVBoxLayout(p_widget)
            p_layout.setContentsMargins(5, 5, 5, 5)
            p_layout.setSpacing(2)
            
            # Header: /home (sda1)
            header_txt = f"📂 {part['mountpoint']} <span style='color:#777; font-size:10px;'>({part['device']})</span>"
            header = QLabel(header_txt)
            header.setTextFormat(Qt.RichText)
            
            # Barra
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(int(part['percent']))
            progress.setTextVisible(True)
            progress.setFixedHeight(15)
            
            # Color barra
            if part['percent'] > 90: col = "#f44336"
            elif part['percent'] > 75: col = "#ff9800"
            else: col = "#4caf50"
            
            progress.setStyleSheet(f"""
                QProgressBar {{ border: 1px solid #ccc; border-radius: 3px; text-align: center; font-size: 10px; }}
                QProgressBar::chunk {{ background-color: {col}; }}
            """)
            
            details = QLabel(f"{part['used_gb']:.1f} GB usados de {part['total_gb']:.1f} GB ({part['fstype']})")
            details.setStyleSheet("color: #666; font-size: 10px;")
            
            p_layout.addWidget(header)
            p_layout.addWidget(progress)
            p_layout.addWidget(details)
            
            self.partitions_layout.addWidget(p_widget)
            self.partition_widgets.append(p_widget)
            
        # 2. Actualizar I/O
        io = stats['io_counters']
        if io:
            self.read_speed_label.setText(f"Lectura: {io['read_speed_mb']:.1f} MB/s")
            self.write_speed_label.setText(f"Escritura: {io['write_speed_mb']:.1f} MB/s")
            self.total_read_label.setText(f"Total Leído: {io['read_bytes_gb']:.2f} GB")
            self.total_write_label.setText(f"Total Escrito: {io['write_bytes_gb']:.2f} GB")
        
        # 3. Actualizar Fragmentación (LÓGICA CORREGIDA)
        frag = stats['fragmentation']
        
        if frag.get('available'):
            # ÉXITO: Tenemos datos reales
            self.disk_frag_label.setText("✅ Análisis Completado")
            self.disk_frag_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
            
            # Mostrar la salida técnica real si existe
            details_text = "Estado: Saludable\n"
            
            if 'details' in frag:
                if 'filefrag' in frag['details']:
                    # Limpiamos un poco la salida cruda
                    raw = frag['details']['filefrag'].strip()
                    # Tomar solo las líneas relevantes para no saturar
                    lines = raw.split('\n')
                    summary_lines = [l for l in lines if "extent" in l or "fragment" in l]
                    if summary_lines:
                        details_text += f"\nReporte del Kernel:\n" + "\n".join(summary_lines)
                    else:
                        details_text += f"\n{raw}"
                
                elif 'fs_info' in frag['details']:
                    details_text += f"\nInfo: {frag['details']['fs_info']}"
            
            self.disk_frag_details.setText(details_text)
            
        elif frag.get('message'):
            # FALLBACK: No hay permisos o no es compatible
            self.disk_frag_label.setText("ℹ️ Información General")
            self.disk_frag_label.setStyleSheet("color: #1976d2; font-weight: bold;")
            self.disk_frag_details.setText(frag['message'])
        else:
            # ESTADO INICIAL
            self.disk_frag_label.setText("⏳ Analizando...")
        
        # 4. Actualizar Gráfico
        self.update_chart()
    
    def update_chart(self):
        """Actualiza el gráfico de historial."""
        history = self.disk_monitor.get_history()
        self.ax.clear()
        
        if history['timestamps'] and history['io_stats']:
            timestamps = history['timestamps']
            # Extraer velocidades de la lista de diccionarios
            reads = [io.get('read_speed_mb', 0) if io else 0 for io in history['io_stats']]
            writes = [io.get('write_speed_mb', 0) if io else 0 for io in history['io_stats']]
            
            now = datetime.now()
            times = [-(now - t).total_seconds() for t in timestamps]
            
            # Filtrar 60s
            f_t, f_r, f_w = [], [], []
            for t, r, w in zip(times, reads, writes):
                if t >= -60:
                    f_t.append(t)
                    f_r.append(r)
                    f_w.append(w)
            
            if f_t:
                self.ax.plot(f_t, f_r, label='Lectura', color='#4caf50', linewidth=1.5)
                self.ax.plot(f_t, f_w, label='Escritura', color='#ff9800', linewidth=1.5)
                self.ax.fill_between(f_t, f_r, color='#4caf50', alpha=0.1)
                self.ax.fill_between(f_t, f_w, color='#ff9800', alpha=0.1)
            
            self.ax.legend(loc='upper left', fontsize=8)
            self.ax.grid(True, linestyle='--', alpha=0.4)
            self.ax.set_xlim(-60, 0)
            # Y lim dinámico pero mínimo 1 MB/s
            max_val = max(max(f_r + [0]), max(f_w + [0]))
            self.ax.set_ylim(0, max(5, max_val * 1.2))
            self.ax.set_ylabel("MB/s", fontsize=8)
            self.ax.set_xlabel("Segundos atrás", fontsize=8)
            
        else:
            self.ax.text(0.5, 0.5, 'Recopilando...', ha='center', transform=self.ax.transAxes)
            
        self.canvas.draw()
