"""
Módulo de monitoreo de Almacenamiento/Disco
Proporciona información sobre la utilización del almacenamiento
incluyendo análisis de fragmentación
"""

import psutil
import time
import subprocess
import platform
from collections import deque
from datetime import datetime
from threading import Thread, Lock


class DiskMonitor:
    """
    Clase para monitorear la utilización de almacenamiento.
    Mantiene un historial de la última hora de datos.
    Incluye análisis de fragmentación del disco.
    """
    
    def __init__(self, history_duration=3600, update_interval=5):
        """
        Inicializa el monitor de disco.
        
        Args:
            history_duration: Duración del historial en segundos (default: 3600 = 1 hora)
            update_interval: Intervalo de actualización en segundos (default: 5)
        """
        self.history_duration = history_duration
        self.update_interval = update_interval
        
        # Calcular el tamaño máximo del historial
        max_samples = history_duration // update_interval
        
        # Historial de disco
        self.disk_history = deque(maxlen=max_samples)
        self.io_history = deque(maxlen=max_samples)
        self.timestamps = deque(maxlen=max_samples)
        
        # Lock para acceso thread-safe
        self._lock = Lock()
        
        # Thread de actualización
        self._running = False
        self._thread = None
        
        # Almacenar última lectura de IO para calcular velocidades
        self._last_io = None
        self._last_io_time = None
    
    def get_partitions(self):
        """Obtiene la lista de particiones del disco."""
        partitions = []
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'opts': partition.opts,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent,
                    'total_gb': usage.total / (1024 ** 3),
                    'used_gb': usage.used / (1024 ** 3),
                    'free_gb': usage.free / (1024 ** 3)
                })
            except (PermissionError, OSError):
                # Algunas particiones pueden no ser accesibles
                partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'opts': partition.opts,
                    'error': 'No accesible'
                })
        return partitions
    
    def get_disk_usage(self, path='/'):
        """Obtiene el uso del disco para una ruta específica."""
        try:
            usage = psutil.disk_usage(path)
            return {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent,
                'total_gb': usage.total / (1024 ** 3),
                'used_gb': usage.used / (1024 ** 3),
                'free_gb': usage.free / (1024 ** 3)
            }
        except (PermissionError, OSError) as e:
            return {'error': str(e)}
    
    def get_io_counters(self):
        """Obtiene los contadores de I/O del disco."""
        try:
            io = psutil.disk_io_counters()
            if io:
                current_time = time.time()
                
                # Calcular velocidades si tenemos lectura anterior
                read_speed = 0
                write_speed = 0
                
                if self._last_io and self._last_io_time:
                    time_diff = current_time - self._last_io_time
                    if time_diff > 0:
                        read_speed = (io.read_bytes - self._last_io.read_bytes) / time_diff
                        write_speed = (io.write_bytes - self._last_io.write_bytes) / time_diff
                
                self._last_io = io
                self._last_io_time = current_time
                
                return {
                    'read_count': io.read_count,
                    'write_count': io.write_count,
                    'read_bytes': io.read_bytes,
                    'write_bytes': io.write_bytes,
                    'read_time': io.read_time,
                    'write_time': io.write_time,
                    'read_bytes_gb': io.read_bytes / (1024 ** 3),
                    'write_bytes_gb': io.write_bytes / (1024 ** 3),
                    'read_speed_mb': read_speed / (1024 ** 2),
                    'write_speed_mb': write_speed / (1024 ** 2)
                }
        except Exception:
            pass
        return None
    
    def get_per_disk_io(self):
        """Obtiene contadores de I/O por disco."""
        try:
            io_per_disk = psutil.disk_io_counters(perdisk=True)
            result = {}
            for disk, io in io_per_disk.items():
                result[disk] = {
                    'read_count': io.read_count,
                    'write_count': io.write_count,
                    'read_bytes': io.read_bytes,
                    'write_bytes': io.write_bytes,
                    'read_bytes_mb': io.read_bytes / (1024 ** 2),
                    'write_bytes_mb': io.write_bytes / (1024 ** 2)
                }
            return result
        except Exception:
            return {}
    
    def get_disk_fragmentation(self):
        """
        Obtiene información sobre la fragmentación del disco.
        
        Nota: La fragmentación en sistemas de archivos modernos (ext4, APFS, etc.)
        es generalmente baja y manejada automáticamente por el sistema.
        """
        fragmentation_info = {
            'available': False,
            'fragmentation_percent': 0.0,
            'details': {},
            'message': ''
        }
        
        system = platform.system()
        
        if system == 'Linux':
            try:
                # En Linux, podemos usar e4defrag para ext4 o filefrag
                # Intentar obtener info de fragmentación usando filefrag en archivos de prueba
                result = subprocess.run(
                    ['sudo', 'filefrag', '-v', '/'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    fragmentation_info['available'] = True
                    fragmentation_info['details']['filefrag'] = result.stdout
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                pass
            
            # Intentar leer información de sistemas de archivos
            try:
                partitions = self.get_partitions()
                for part in partitions:
                    if 'ext4' in part.get('fstype', ''):
                        try:
                            # Usar dumpe2fs para obtener info del sistema de archivos
                            result = subprocess.run(
                                ['dumpe2fs', '-h', part['device']],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if result.returncode == 0:
                                fragmentation_info['details'][part['device']] = result.stdout
                                fragmentation_info['available'] = True
                        except Exception:
                            pass
            except Exception:
                pass
                
            if not fragmentation_info['available']:
                fragmentation_info['message'] = 'Los sistemas de archivos ext4/xfs modernos tienen baja fragmentación y se desfragmentan automáticamente.'
                
        elif system == 'Darwin':  # macOS
            # APFS (sistema de archivos de macOS) no se fragmenta de manera tradicional
            fragmentation_info['message'] = 'APFS (Apple File System) utiliza copy-on-write y no requiere desfragmentación tradicional.'
            fragmentation_info['details']['filesystem'] = 'APFS'
            
            # Obtener información del sistema de archivos
            try:
                result = subprocess.run(
                    ['diskutil', 'info', '/'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    fragmentation_info['details']['diskutil'] = result.stdout
                    fragmentation_info['available'] = True
                    
                    # Parsear para obtener tipo de sistema de archivos
                    for line in result.stdout.split('\n'):
                        if 'File System' in line or 'Type' in line:
                            fragmentation_info['details']['fs_info'] = line.strip()
            except Exception:
                pass
                
        elif system == 'Windows':
            fragmentation_info['message'] = 'Use la herramienta de desfragmentación de Windows para análisis detallado.'
            try:
                # En Windows, podríamos usar defrag -a
                result = subprocess.run(
                    ['defrag', 'C:', '/A'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    fragmentation_info['available'] = True
                    fragmentation_info['details']['defrag'] = result.stdout
                    
                    # Intentar extraer porcentaje de fragmentación
                    for line in result.stdout.split('\n'):
                        if 'fragmented' in line.lower():
                            try:
                                # Buscar número en la línea
                                import re
                                numbers = re.findall(r'\d+', line)
                                if numbers:
                                    fragmentation_info['fragmentation_percent'] = float(numbers[0])
                            except Exception:
                                pass
            except Exception:
                pass
        
        return fragmentation_info
    
    def get_current_stats(self):
        """Obtiene todas las estadísticas actuales del disco."""
        return {
            'partitions': self.get_partitions(),
            'io_counters': self.get_io_counters(),
            'fragmentation': self.get_disk_fragmentation(),
            'timestamp': datetime.now()
        }
    
    def get_history(self):
        """Obtiene el historial de uso del disco."""
        with self._lock:
            return {
                'timestamps': list(self.timestamps),
                'disk_usage': list(self.disk_history),
                'io_stats': list(self.io_history)
            }
    
    def _update_history(self):
        """Actualiza el historial del disco."""
        partitions = self.get_partitions()
        io_counters = self.get_io_counters()
        timestamp = datetime.now()
        
        with self._lock:
            self.disk_history.append(partitions)
            self.io_history.append(io_counters)
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
