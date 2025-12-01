#!/usr/bin/env python3
"""
Monitor de Recursos del Sistema
Universidad San Francisco de Quito
Sistemas Operativos - Proyecto Final

Este programa permite monitorear en tiempo real:
- Utilización del CPU
- Memoria RAM y Swap (incluyendo fragmentación)
- Almacenamiento y I/O (incluyendo fragmentación)
- Procesos del sistema (con capacidad de terminarlos)
- Ancho de banda de red (upload y download)

Autor: Estudiante USFQ
Fecha: Diciembre 2025
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Función principal de la aplicación."""
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    
    # Configurar estilo
    app.setStyle('Fusion')
    
    # Configurar nombre de la aplicación
    app.setApplicationName("Monitor de Recursos")
    app.setOrganizationName("USFQ")
    app.setOrganizationDomain("usfq.edu.ec")
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar loop de eventos
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
