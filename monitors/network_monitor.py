"""
Módulo de monitoreo de Red
Proporciona información sobre el uso de ancho de banda de la red
"""

import psutil
import time
from collections import deque
from datetime import datetime
from threading import Thread, Lock


class NetworkMonitor:
    """
    Clase para monitorear el uso de red del sistema.
    Mantiene un historial de la última hora de datos.
    Muestra upload y download por separado.
    """
    
    def __init__(self, history_duration=3600, update_interval=1):
        """
        Inicializa el monitor de red.
        
        Args:
            history_duration: Duración del historial en segundos (default: 3600 = 1 hora)
            update_interval: Intervalo de actualización en segundos (default: 1)
        """
        self.history_duration = history_duration
        self.update_interval = update_interval
        
        # Calcular el tamaño máximo del historial
        max_samples = history_duration // update_interval
        
        # Historial de red
        self.upload_history = deque(maxlen=max_samples)
        self.download_history = deque(maxlen=max_samples)
        self.timestamps = deque(maxlen=max_samples)
        
        # Para calcular velocidades
        self._last_counters = None
        self._last_time = None
        
        # Velocidades actuales calculadas
        self._current_upload_speed = 0
        self._current_download_speed = 0
        
        # Lock para acceso thread-safe
        self._lock = Lock()
        
        # Thread de actualización
        self._running = False
        self._thread = None
    
    def get_interfaces(self):
        """Obtiene la lista de interfaces de red."""
        interfaces = []
        
        # Obtener direcciones
        addrs = psutil.net_if_addrs()
        
        # Obtener estadísticas
        stats = psutil.net_if_stats()
        
        for interface_name, addr_list in addrs.items():
            interface_info = {
                'name': interface_name,
                'addresses': [],
                'is_up': False,
                'speed': 0,
                'mtu': 0
            }
            
            # Agregar direcciones
            for addr in addr_list:
                addr_info = {
                    'family': str(addr.family),
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast
                }
                interface_info['addresses'].append(addr_info)
            
            # Agregar estadísticas
            if interface_name in stats:
                stat = stats[interface_name]
                interface_info['is_up'] = stat.isup
                interface_info['speed'] = stat.speed  # Mbps
                interface_info['mtu'] = stat.mtu
            
            interfaces.append(interface_info)
        
        return interfaces
    
    def get_io_counters(self, per_interface=False):
        """
        Obtiene los contadores de I/O de red.
        
        Args:
            per_interface: Si es True, devuelve contadores por interfaz
            
        Returns:
            Diccionario con contadores de red
        """
        if per_interface:
            counters = psutil.net_io_counters(pernic=True)
            result = {}
            
            for nic, io in counters.items():
                result[nic] = {
                    'bytes_sent': io.bytes_sent,
                    'bytes_recv': io.bytes_recv,
                    'packets_sent': io.packets_sent,
                    'packets_recv': io.packets_recv,
                    'errin': io.errin,
                    'errout': io.errout,
                    'dropin': io.dropin,
                    'dropout': io.dropout,
                    'bytes_sent_mb': io.bytes_sent / (1024 ** 2),
                    'bytes_recv_mb': io.bytes_recv / (1024 ** 2)
                }
            
            return result
        else:
            io = psutil.net_io_counters()
            
            # Usar las velocidades calculadas por el hilo de monitoreo
            with self._lock:
                upload_speed = self._current_upload_speed
                download_speed = self._current_download_speed
            
            return {
                'bytes_sent': io.bytes_sent,
                'bytes_recv': io.bytes_recv,
                'packets_sent': io.packets_sent,
                'packets_recv': io.packets_recv,
                'errin': io.errin,
                'errout': io.errout,
                'dropin': io.dropin,
                'dropout': io.dropout,
                'bytes_sent_gb': io.bytes_sent / (1024 ** 3),
                'bytes_recv_gb': io.bytes_recv / (1024 ** 3),
                'upload_speed_kbps': upload_speed / 1024,
                'download_speed_kbps': download_speed / 1024,
                'upload_speed_mbps': upload_speed / (1024 ** 2),
                'download_speed_mbps': download_speed / (1024 ** 2)
            }
    
    def get_connections(self, kind='inet'):
        """
        Obtiene las conexiones de red activas.
        
        Args:
            kind: Tipo de conexiones ('inet', 'inet4', 'inet6', 'tcp', 'udp', 'all')
            
        Returns:
            Lista de conexiones activas
        """
        connections = []
        
        try:
            for conn in psutil.net_connections(kind=kind):
                conn_info = {
                    'fd': conn.fd,
                    'family': str(conn.family),
                    'type': str(conn.type),
                    'status': conn.status,
                    'pid': conn.pid
                }
                
                # Dirección local
                if conn.laddr:
                    conn_info['local_address'] = conn.laddr.ip
                    conn_info['local_port'] = conn.laddr.port
                else:
                    conn_info['local_address'] = ''
                    conn_info['local_port'] = 0
                
                # Dirección remota
                if conn.raddr:
                    conn_info['remote_address'] = conn.raddr.ip
                    conn_info['remote_port'] = conn.raddr.port
                else:
                    conn_info['remote_address'] = ''
                    conn_info['remote_port'] = 0
                
                # Obtener nombre del proceso
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        conn_info['process_name'] = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        conn_info['process_name'] = 'Unknown'
                else:
                    conn_info['process_name'] = ''
                
                connections.append(conn_info)
                
        except psutil.AccessDenied:
            pass
        
        return connections
    
    def get_current_speeds(self):
        """
        Obtiene las velocidades actuales de upload y download.
        
        Returns:
            Diccionario con velocidades en diferentes unidades
        """
        io = self.get_io_counters()
        
        return {
            'upload': {
                'kbps': io['upload_speed_kbps'],
                'mbps': io['upload_speed_mbps'],
                'formatted': self._format_speed(io['upload_speed_kbps'] * 1024)
            },
            'download': {
                'kbps': io['download_speed_kbps'],
                'mbps': io['download_speed_mbps'],
                'formatted': self._format_speed(io['download_speed_kbps'] * 1024)
            }
        }
    
    def _format_speed(self, bytes_per_sec):
        """Formatea la velocidad en formato legible."""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.1f} B/s"
        elif bytes_per_sec < 1024 ** 2:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        elif bytes_per_sec < 1024 ** 3:
            return f"{bytes_per_sec / (1024 ** 2):.1f} MB/s"
        else:
            return f"{bytes_per_sec / (1024 ** 3):.1f} GB/s"
    
    def get_current_stats(self):
        """Obtiene todas las estadísticas actuales de red."""
        return {
            'interfaces': self.get_interfaces(),
            'io_counters': self.get_io_counters(),
            'speeds': self.get_current_speeds(),
            'connections_count': len(self.get_connections()),
            'timestamp': datetime.now()
        }
    
    def get_history(self):
        """Obtiene el historial de uso de red."""
        with self._lock:
            return {
                'timestamps': list(self.timestamps),
                'upload_kbps': list(self.upload_history),
                'download_kbps': list(self.download_history)
            }
    
    def _update_history(self):
        """Actualiza el historial de red y calcula velocidades."""
        current_time = time.time()
        io = psutil.net_io_counters()
        
        # Calcular velocidades
        upload_speed = 0
        download_speed = 0
        
        if self._last_counters and self._last_time:
            time_diff = current_time - self._last_time
            if time_diff > 0:
                upload_speed = (io.bytes_sent - self._last_counters.bytes_sent) / time_diff
                download_speed = (io.bytes_recv - self._last_counters.bytes_recv) / time_diff
        
        self._last_counters = io
        self._last_time = current_time
        
        timestamp = datetime.now()
        
        with self._lock:
            # Guardar velocidades actuales para el widget
            self._current_upload_speed = upload_speed
            self._current_download_speed = download_speed
            
            # Agregar al historial
            self.upload_history.append(upload_speed / 1024)  # KB/s
            self.download_history.append(download_speed / 1024)  # KB/s
            self.timestamps.append(timestamp)
    
    def _monitor_loop(self):
        """Loop principal de monitoreo en segundo plano."""
        # Primera lectura para inicializar
        self._last_counters = psutil.net_io_counters()
        self._last_time = time.time()
        
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
