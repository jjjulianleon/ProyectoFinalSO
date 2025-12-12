"""
Ventana principal de la aplicación de monitoreo
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QStatusBar, QMenuBar, QAction,
                             QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

import sys
import os

# Agregar el directorio padre al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitors import CPUMonitor, MemoryMonitor, DiskMonitor, ProcessMonitor, NetworkMonitor
from gui.widgets import CPUWidget, MemoryWidget, DiskWidget, ProcessWidget, NetworkWidget


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación."""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar monitores
        self.cpu_monitor = CPUMonitor()
        self.memory_monitor = MemoryMonitor()
        self.disk_monitor = DiskMonitor()
        self.process_monitor = ProcessMonitor()
        self.network_monitor = NetworkMonitor()
        
        # Configurar ventana
        self.setWindowTitle("🖥️ Monitor de Recursos del Sistema - USFQ")
        self.setMinimumSize(1200, 800)
        
        # Configurar interfaz
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # Configurar timers para actualización
        self.setup_timers()
        
        # Iniciar monitoreo
        self.start_monitoring()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Título
        title_layout = QHBoxLayout()
        
        title = QLabel("🖥️ Monitor de Recursos del Sistema")
        title.setFont(QFont('Arial', 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1976d2; padding: 10px;")
        
        subtitle = QLabel("Universidad San Francisco de Quito - Sistemas Operativos")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        
        title_widget = QWidget()
        title_widget_layout = QVBoxLayout(title_widget)
        title_widget_layout.addWidget(title)
        title_widget_layout.addWidget(subtitle)
        
        title_layout.addWidget(title_widget)
        layout.addLayout(title_layout)
        
        # Tabs para diferentes recursos
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 2px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                background-color: #f5f5f5;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #1976d2;
            }
            QTabBar::tab:hover {
                background-color: #e3f2fd;
            }
        """)
        
        # Crear widgets para cada recurso
        self.cpu_widget = CPUWidget(self.cpu_monitor)
        self.memory_widget = MemoryWidget(self.memory_monitor)
        self.disk_widget = DiskWidget(self.disk_monitor)
        self.process_widget = ProcessWidget(self.process_monitor)
        self.network_widget = NetworkWidget(self.network_monitor)
        
        # Agregar tabs
        self.tabs.addTab(self.cpu_widget, "📊 CPU")
        self.tabs.addTab(self.memory_widget, "🧠 Memoria")
        self.tabs.addTab(self.disk_widget, "💾 Disco")
        self.tabs.addTab(self.process_widget, "⚙️ Procesos")
        self.tabs.addTab(self.network_widget, "🌐 Red")
        
        layout.addWidget(self.tabs)
        
    def setup_menu(self):
        """Configura el menú de la aplicación."""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu("Archivo")
        
        refresh_action = QAction("🔄 Actualizar Todo", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("❌ Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Ver
        view_menu = menubar.addMenu("Ver")
        
        cpu_action = QAction("📊 CPU", self)
        cpu_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        view_menu.addAction(cpu_action)
        
        memory_action = QAction("🧠 Memoria", self)
        memory_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        view_menu.addAction(memory_action)
        
        disk_action = QAction("💾 Disco", self)
        disk_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        view_menu.addAction(disk_action)
        
        process_action = QAction("⚙️ Procesos", self)
        process_action.triggered.connect(lambda: self.tabs.setCurrentIndex(3))
        view_menu.addAction(process_action)
        
        network_action = QAction("🌐 Red", self)
        network_action.triggered.connect(lambda: self.tabs.setCurrentIndex(4))
        view_menu.addAction(network_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu("Ayuda")
        
        about_action = QAction("ℹ️ Acerca de", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_status_bar(self):
        """Configura la barra de estado."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Sistema: Iniciando...")
        self.status_bar.addWidget(self.status_label)
        
        self.update_count_label = QLabel("Actualizaciones: 0")
        self.status_bar.addPermanentWidget(self.update_count_label)
        
        self.update_count = 0
        
    def setup_timers(self):
        """Configura los timers para actualización automática."""
        # Timer para CPU, Memoria y Red (cada 1 segundo)
        self.fast_timer = QTimer()
        self.fast_timer.timeout.connect(self.update_fast_resources)
        self.fast_timer.start(1000)  # 1 segundo
        
        # Timer para Disco (cada 5 segundos)
        self.slow_timer = QTimer()
        self.slow_timer.timeout.connect(self.update_slow_resources)
        self.slow_timer.start(5000)  # 5 segundos
        
        # Timer para procesos (cada 3 segundos)
        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self.update_processes)
        self.process_timer.start(3000)  # 3 segundos
        
    def start_monitoring(self):
        """Inicia el monitoreo de todos los recursos."""
        self.cpu_monitor.start_monitoring()
        self.memory_monitor.start_monitoring()
        self.disk_monitor.start_monitoring()
        self.network_monitor.start_monitoring()
        self.process_monitor.start_monitoring()
        
        # Primera actualización
        self.refresh_all()
        
        self.status_label.setText("Sistema: Monitoreando recursos...")
        
    def stop_monitoring(self):
        """Detiene el monitoreo de todos los recursos."""
        self.cpu_monitor.stop_monitoring()
        self.memory_monitor.stop_monitoring()
        self.disk_monitor.stop_monitoring()
        self.network_monitor.stop_monitoring()
        self.process_monitor.stop_monitoring()
        
    def update_fast_resources(self):
        """Actualiza recursos de alta frecuencia (CPU, Memoria, Red)."""
        current_tab = self.tabs.currentIndex()
        
        # Siempre actualizar el tab actual
        if current_tab == 0:
            self.cpu_widget.update_data()
        elif current_tab == 1:
            self.memory_widget.update_data()
        elif current_tab == 4:
            self.network_widget.update_data()
        
        self.update_count += 1
        self.update_count_label.setText(f"Actualizaciones: {self.update_count}")
        
    def update_slow_resources(self):
        """Actualiza recursos de baja frecuencia (Disco)."""
        if self.tabs.currentIndex() == 2:
            self.disk_widget.update_data()
            
    def update_processes(self):
        """Actualiza la lista de procesos."""
        if self.tabs.currentIndex() == 3:
            self.process_widget.update_data()
            
    def refresh_all(self):
        """Actualiza todos los recursos."""
        self.cpu_widget.update_data()
        self.memory_widget.update_data()
        self.disk_widget.update_data()
        self.process_widget.update_data()
        self.network_widget.update_data()
        
        self.status_label.setText("Sistema: Actualización completa")
        
    def show_about(self):
        """Muestra el diálogo Acerca de."""
        QMessageBox.about(
            self,
            "Acerca de - Monitor de Recursos",
            """
            <h2>🖥️ Monitor de Recursos del Sistema</h2>
            <p><b>Versión:</b> 1.0</p>
            <p><b>Universidad:</b> San Francisco de Quito</p>
            <p><b>Materia:</b> Sistemas Operativos</p>
            <p><b>Semestre:</b> 202510</p>
            <hr>
            <p>Esta herramienta permite monitorear en tiempo real:</p>
            <ul>
                <li>📊 Utilización del CPU</li>
                <li>🧠 Memoria RAM y Swap</li>
                <li>💾 Almacenamiento y I/O</li>
                <li>⚙️ Procesos del sistema</li>
                <li>🌐 Ancho de banda de red</li>
            </ul>
            <hr>
            <p><i>Desarrollado con Python y PyQt5</i></p>
            """
        )
        
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        # Detener timers
        self.fast_timer.stop()
        self.slow_timer.stop()
        self.process_timer.stop()
        
        # Detener monitoreo
        self.stop_monitoring()
        
        event.accept()


def main():
    """Función principal de la aplicación."""
    app = QApplication(sys.argv)
    
    # Estilo global
    app.setStyle('Fusion')
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
