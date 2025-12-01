"""
Módulo de monitoreo de Memoria RAM
Proporciona información sobre la utilización de memoria del sistema
incluyendo análisis de fragmentación
"""

import psutil
import time
from collections import deque
from datetime import datetime
from threading import Thread, Lock
import subprocess
import platform


class MemoryMonitor:
    """
    Clase para monitorear la utilización de memoria RAM.
    Mantiene un historial de la última hora de datos.
    Incluye análisis de fragmentación de memoria.
    """
    
    def __init__(self, history_duration=3600, update_interval=1):
        """
        Inicializa el monitor de memoria.
        
        Args:
            history_duration: Duración del historial en segundos (default: 3600 = 1 hora)
            update_interval: Intervalo de actualización en segundos (default: 1)
        """
        self.history_duration = history_duration
        self.update_interval = update_interval
        
        # Calcular el tamaño máximo del historial
        max_samples = history_duration // update_interval
        
        # Historial de memoria
        self.memory_history = deque(maxlen=max_samples)
        self.swap_history = deque(maxlen=max_samples)
        self.timestamps = deque(maxlen=max_samples)
        
        # Lock para acceso thread-safe
        self._lock = Lock()
        
        # Thread de actualización
        self._running = False
        self._thread = None
    
    def get_memory_info(self):
        """Obtiene información completa de la memoria RAM."""
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'free': mem.free,
            'percent': mem.percent,
            'total_gb': mem.total / (1024 ** 3),
            'available_gb': mem.available / (1024 ** 3),
            'used_gb': mem.used / (1024 ** 3),
            'free_gb': mem.free / (1024 ** 3)
        }
    
    def get_swap_info(self):
        """Obtiene información de la memoria swap."""
        swap = psutil.swap_memory()
        return {
            'total': swap.total,
            'used': swap.used,
            'free': swap.free,
            'percent': swap.percent,
            'total_gb': swap.total / (1024 ** 3),
            'used_gb': swap.used / (1024 ** 3),
            'free_gb': swap.free / (1024 ** 3),
            'sin': swap.sin,  # Bytes leídos desde disco
            'sout': swap.sout  # Bytes escritos a disco
        }
    
    def get_memory_fragmentation(self):
        """
        Obtiene información sobre la fragmentación de memoria.
        Esta es una aproximación basada en la información disponible.
        
        En Linux, intenta leer /proc/buddyinfo para información de fragmentación.
        En otros sistemas, proporciona una estimación basada en memoria libre vs disponible.
        """
        fragmentation_info = {
            'fragmentation_ratio': 0.0,
            'details': {},
            'available': False
        }
        
        system = platform.system()
        
        if system == 'Linux':
            try:
                # Leer buddyinfo para información de fragmentación real
                with open('/proc/buddyinfo', 'r') as f:
                    buddyinfo = f.read()
                
                fragmentation_info['buddyinfo'] = buddyinfo
                fragmentation_info['available'] = True
                
                # Parsear buddyinfo
                zones = []
                for line in buddyinfo.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 4:
                        zone_name = parts[3]
                        # Los valores son el número de bloques libres de cada orden (4KB, 8KB, 16KB, etc.)
                        blocks = [int(x) for x in parts[4:]]
                        zones.append({
                            'name': zone_name,
                            'blocks': blocks
                        })
                
                fragmentation_info['zones'] = zones
                
                # Calcular índice de fragmentación
                # Más bloques pequeños = más fragmentación
                total_small = 0
                total_large = 0
                for zone in zones:
                    if zone['blocks']:
                        # Bloques pequeños (primeros 3 órdenes: 4KB, 8KB, 16KB)
                        total_small += sum(zone['blocks'][:3]) if len(zone['blocks']) >= 3 else sum(zone['blocks'])
                        # Bloques grandes (resto)
                        total_large += sum(zone['blocks'][3:]) if len(zone['blocks']) > 3 else 0
                
                if total_small + total_large > 0:
                    fragmentation_info['fragmentation_ratio'] = total_small / (total_small + total_large)
                
            except (FileNotFoundError, PermissionError):
                pass
        
        elif system == 'Darwin':  # macOS
            try:
                # Usar vm_stat para obtener información de memoria
                result = subprocess.run(['vm_stat'], capture_output=True, text=True)
                if result.returncode == 0:
                    fragmentation_info['vm_stat'] = result.stdout
                    fragmentation_info['available'] = True
                    
                    # Parsear vm_stat
                    stats = {}
                    for line in result.stdout.split('\n'):
                        if ':' in line:
                            key, value = line.split(':')
                            value = value.strip().rstrip('.')
                            try:
                                stats[key.strip()] = int(value)
                            except ValueError:
                                pass
                    
                    fragmentation_info['details'] = stats
                    
                    # Estimar fragmentación basada en páginas especulativas y purgables
                    page_size = 4096  # Tamaño de página típico en macOS
                    
                    if 'Pages free' in stats and 'Pages speculative' in stats:
                        free_pages = stats.get('Pages free', 0)
                        speculative = stats.get('Pages speculative', 0)
                        if free_pages + speculative > 0:
                            # Más páginas especulativas relativas indica potencial fragmentación
                            fragmentation_info['fragmentation_ratio'] = speculative / (free_pages + speculative + 1)
                    
            except Exception:
                pass
        
        # Si no pudimos obtener info específica, usar estimación general
        if not fragmentation_info['available']:
            mem = psutil.virtual_memory()
            # Diferencia entre available y free puede indicar fragmentación
            if mem.available > 0:
                fragmentation_info['fragmentation_ratio'] = 1 - (mem.free / mem.available)
                fragmentation_info['details'] = {
                    'free': mem.free,
                    'available': mem.available,
                    'cached': getattr(mem, 'cached', 0),
                    'buffers': getattr(mem, 'buffers', 0)
                }
        
        return fragmentation_info
    
    def get_current_stats(self):
        """Obtiene todas las estadísticas actuales de memoria."""
        return {
            'memory': self.get_memory_info(),
            'swap': self.get_swap_info(),
            'fragmentation': self.get_memory_fragmentation(),
            'timestamp': datetime.now()
        }
    
    def get_history(self):
        """Obtiene el historial de uso de memoria."""
        with self._lock:
            return {
                'timestamps': list(self.timestamps),
                'memory_percent': [m['percent'] for m in self.memory_history],
                'memory_used_gb': [m['used_gb'] for m in self.memory_history],
                'swap_percent': [s['percent'] for s in self.swap_history]
            }
    
    def _update_history(self):
        """Actualiza el historial de memoria."""
        mem_info = self.get_memory_info()
        swap_info = self.get_swap_info()
        timestamp = datetime.now()
        
        with self._lock:
            self.memory_history.append(mem_info)
            self.swap_history.append(swap_info)
            self.timestamps.append(timestamp)
    
    def _monitor_loop(self):
        """Loop principal de monitoreo en segundo plano."""
        while self._running:
            self._update_history()
            time.sleep(self.update_interval)
    
    def start_monitoring(self):
        """Inicia el monitoreo en segundo plano."""
        if not self._running:
            self._running = True
            self._thread = Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
    
    def stop_monitoring(self):
        """Detiene el monitoreo en segundo plano."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
    
    def __del__(self):
        """Destructor: asegura que el thread se detenga."""
        self.stop_monitoring()
