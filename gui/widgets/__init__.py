"""
Widgets personalizados para la interfaz gráfica
"""

from .cpu_widget import CPUWidget
from .memory_widget import MemoryWidget
from .disk_widget import DiskWidget
from .process_widget import ProcessWidget
from .network_widget import NetworkWidget

__all__ = [
    'CPUWidget',
    'MemoryWidget',
    'DiskWidget',
    'ProcessWidget',
    'NetworkWidget'
]
