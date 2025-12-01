"""
Módulo de monitoreo de CPU
Proporciona información sobre la utilización del CPU/CPUs del sistema
"""

import psutil
import time
from collections import deque
from datetime import datetime
from threading import Thread, Lock


class CPUMonitor:
    """
    Clase para monitorear la utilización del CPU.
    Mantiene un historial de la última hora de datos.
    """
    
    def __init__(self, history_duration=3600, update_interval=1):
        """
        Inicializa el monitor de CPU.
        
        Args:
            history_duration: Duración del historial en segundos (default: 3600 = 1 hora)
            update_interval: Intervalo de actualización en segundos (default: 1)
        """
        self.history_duration = history_duration
        self.update_interval = update_interval
        
        # Calcular el tamaño máximo del historial
        max_samples = history_duration // update_interval
        
        # Historial de uso total de CPU
        self.cpu_history = deque(maxlen=max_samples)
        self.timestamps = deque(maxlen=max_samples)
        
        # Historial por núcleo
        self.per_cpu_history = deque(maxlen=max_samples)
        
        # Lock para acceso thread-safe
        self._lock = Lock()
        
        # Thread de actualización
        self._running = False
        self._thread = None
    
    def get_cpu_count(self):
        """Obtiene el número de CPUs (núcleos) del sistema."""
        return {
            'physical': psutil.cpu_count(logical=False),
            'logical': psutil.cpu_count(logical=True)
        }
    
    def get_cpu_freq(self):
        """Obtiene la frecuencia actual del CPU."""
        freq = psutil.cpu_freq()
        if freq:
            return {
                'current': freq.current,
                'min': freq.min,
                'max': freq.max
            }
        return None
    
    def get_current_usage(self):
        """Obtiene el uso actual del CPU (porcentaje total)."""
        return psutil.cpu_percent(interval=0.1)
    
    def get_per_cpu_usage(self):
        """Obtiene el uso de cada núcleo del CPU."""
        return psutil.cpu_percent(interval=0.1, percpu=True)
    
    def get_cpu_times(self):
        """Obtiene los tiempos de CPU (user, system, idle, etc.)."""
        times = psutil.cpu_times()
        return {
            'user': times.user,
            'system': times.system,
            'idle': times.idle
        }
    
    def get_cpu_times_percent(self):
        """Obtiene los porcentajes de tiempo de CPU."""
        times = psutil.cpu_times_percent(interval=0.1)
        return {
            'user': times.user,
            'system': times.system,
            'idle': times.idle
        }
    
    def get_load_average(self):
        """Obtiene el load average del sistema (1, 5, 15 minutos)."""
        try:
            load = psutil.getloadavg()
            return {
                '1min': load[0],
                '5min': load[1],
                '15min': load[2]
            }
        except (AttributeError, OSError):
            # Windows no soporta getloadavg
            return None
    
    def get_current_stats(self):
        """Obtiene todas las estadísticas actuales del CPU."""
        return {
            'usage_percent': self.get_current_usage(),
            'per_cpu_percent': self.get_per_cpu_usage(),
            'cpu_count': self.get_cpu_count(),
            'frequency': self.get_cpu_freq(),
            'times_percent': self.get_cpu_times_percent(),
            'load_average': self.get_load_average(),
            'timestamp': datetime.now()
        }
    
    def get_history(self):
        """Obtiene el historial de uso de CPU."""
        with self._lock:
            return {
                'timestamps': list(self.timestamps),
                'cpu_usage': list(self.cpu_history),
                'per_cpu_usage': list(self.per_cpu_history)
            }
    
    def _update_history(self):
        """Actualiza el historial de uso de CPU."""
        usage = psutil.cpu_percent(interval=None)
        per_cpu = psutil.cpu_percent(interval=None, percpu=True)
        timestamp = datetime.now()
        
        with self._lock:
            self.cpu_history.append(usage)
            self.per_cpu_history.append(per_cpu)
            self.timestamps.append(timestamp)
    
    def _monitor_loop(self):
        """Loop principal de monitoreo en segundo plano."""
        # Primera lectura para inicializar
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)
        
        while self._running:
            time.sleep(self.update_interval)
            if self._running:
                self._update_history()
    
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
