"""
Módulo de monitoreo de Procesos
Proporciona información sobre los procesos en ejecución
incluyendo la capacidad de terminar procesos
"""
from collections import deque
import psutil
import os
import signal
from datetime import datetime
from threading import Thread, Lock
import time


class ProcessMonitor:
    """
    Clase para monitorear los procesos del sistema.
    Permite listar procesos y terminarlos.
    """
    
    def __init__(self):
        """Inicializa el monitor de procesos."""
        self._lock = Lock()
        self._cached_processes = []
        self._last_update = None
        
        # --- NUEVO: Historial para el gráfico ---
        # Guardamos hasta 3600 segundos (1 hora)
        self.count_history = deque(maxlen=3600)
        self.timestamps = deque(maxlen=3600)
        
        # Control del hilo
        self._running = False
        self._thread = None
        # ----------------------------------------
        
    # --- NUEVOS MÉTODOS para el monitoreo en segundo plano ---
    def _monitor_loop(self):
        """Loop que cuenta procesos cada segundo."""
        while self._running:
            try:
                # Usamos len(pids()) que es rápido y ligero
                count = len(psutil.pids())
                timestamp = datetime.now()
                
                with self._lock:
                    self.count_history.append(count)
                    self.timestamps.append(timestamp)
            except Exception:
                pass
            
            time.sleep(1)

    def start_monitoring(self):
        """Inicia el hilo de monitoreo."""
        if not self._running:
            self._running = True
            self._thread = Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()

    def stop_monitoring(self):
        """Detiene el hilo."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def get_history(self):
        """Devuelve el historial para el gráfico."""
        with self._lock:
            return {
                'timestamps': list(self.timestamps),
                'counts': list(self.count_history)
            }
    # --------------------------------------------------------
    
    
    def get_process_list(self, sort_by='memory_percent', descending=True):
        """
        Obtiene la lista de todos los procesos en ejecución.
        
        Args:
            sort_by: Campo por el cual ordenar ('cpu_percent', 'memory_percent', 'pid', 'name')
            descending: Si ordenar de forma descendente
            
        Returns:
            Lista de diccionarios con información de cada proceso
        """
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 
                                          'memory_percent', 'memory_info', 
                                          'username', 'create_time', 'num_threads']):
            try:
                pinfo = proc.info
                
                # Obtener información adicional
                try:
                    io_counters = proc.io_counters()
                    disk_read = io_counters.read_bytes
                    disk_write = io_counters.write_bytes
                except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                    disk_read = 0
                    disk_write = 0
                
                # Obtener comando completo
                try:
                    cmdline = ' '.join(proc.cmdline())
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cmdline = ''
                
                # Calcular tiempo de ejecución
                try:
                    create_time = datetime.fromtimestamp(pinfo['create_time'])
                    runtime = datetime.now() - create_time
                except (TypeError, ValueError):
                    create_time = None
                    runtime = None
                
                process_info = {
                    'pid': pinfo['pid'],
                    'name': pinfo['name'] or 'Unknown',
                    'status': pinfo['status'],
                    'cpu_percent': pinfo['cpu_percent'] or 0.0,
                    'memory_percent': pinfo['memory_percent'] or 0.0,
                    'memory_mb': (pinfo['memory_info'].rss / (1024 ** 2)) if pinfo['memory_info'] else 0,
                    'memory_rss': pinfo['memory_info'].rss if pinfo['memory_info'] else 0,
                    'memory_vms': pinfo['memory_info'].vms if pinfo['memory_info'] else 0,
                    'username': pinfo['username'] or 'Unknown',
                    'create_time': create_time,
                    'runtime': str(runtime).split('.')[0] if runtime else 'N/A',
                    'num_threads': pinfo['num_threads'] or 0,
                    'disk_read_mb': disk_read / (1024 ** 2),
                    'disk_write_mb': disk_write / (1024 ** 2),
                    'disk_total_mb': (disk_read + disk_write) / (1024 ** 2),
                    'cmdline': cmdline[:100] + '...' if len(cmdline) > 100 else cmdline
                }
                
                processes.append(process_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Ordenar procesos
        if sort_by in ['cpu_percent', 'memory_percent', 'pid', 'memory_mb', 'disk_total_mb']:
            processes.sort(key=lambda x: x.get(sort_by, 0), reverse=descending)
        elif sort_by == 'name':
            processes.sort(key=lambda x: x.get('name', '').lower(), reverse=descending)
        
        with self._lock:
            self._cached_processes = processes
            self._last_update = datetime.now()
        
        return processes
    
    def get_process_count(self):
        """Obtiene el número total de procesos."""
        return len(list(psutil.process_iter()))
    
    def get_process_by_pid(self, pid):
        """
        Obtiene información detallada de un proceso específico.
        
        Args:
            pid: ID del proceso
            
        Returns:
            Diccionario con información del proceso o None si no existe
        """
        try:
            proc = psutil.Process(pid)
            
            # Información básica
            info = {
                'pid': proc.pid,
                'name': proc.name(),
                'status': proc.status(),
                'username': proc.username(),
                'create_time': datetime.fromtimestamp(proc.create_time()),
            }
            
            # CPU
            try:
                info['cpu_percent'] = proc.cpu_percent(interval=0.1)
                info['cpu_times'] = proc.cpu_times()._asdict()
            except psutil.AccessDenied:
                info['cpu_percent'] = 0.0
                info['cpu_times'] = {}
            
            # Memoria
            try:
                mem = proc.memory_info()
                info['memory_rss'] = mem.rss
                info['memory_vms'] = mem.vms
                info['memory_percent'] = proc.memory_percent()
                info['memory_mb'] = mem.rss / (1024 ** 2)
            except psutil.AccessDenied:
                info['memory_rss'] = 0
                info['memory_vms'] = 0
                info['memory_percent'] = 0.0
                info['memory_mb'] = 0
            
            # I/O
            try:
                io = proc.io_counters()
                info['io_read_bytes'] = io.read_bytes
                info['io_write_bytes'] = io.write_bytes
                info['io_read_mb'] = io.read_bytes / (1024 ** 2)
                info['io_write_mb'] = io.write_bytes / (1024 ** 2)
            except (psutil.AccessDenied, AttributeError):
                info['io_read_bytes'] = 0
                info['io_write_bytes'] = 0
            
            # Threads
            try:
                info['num_threads'] = proc.num_threads()
                info['threads'] = [{'id': t.id, 'user_time': t.user_time, 'system_time': t.system_time} 
                                  for t in proc.threads()]
            except psutil.AccessDenied:
                info['num_threads'] = 0
                info['threads'] = []
            
            # Archivos abiertos
            try:
                info['open_files'] = [f.path for f in proc.open_files()]
            except psutil.AccessDenied:
                info['open_files'] = []
            
            # Conexiones de red
            try:
                info['connections'] = [
                    {
                        'local_addr': f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else '',
                        'remote_addr': f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else '',
                        'status': c.status
                    }
                    for c in proc.net_connections()
                ]
            except psutil.AccessDenied:
                info['connections'] = []
            
            # Comando
            try:
                info['cmdline'] = proc.cmdline()
                info['exe'] = proc.exe()
                info['cwd'] = proc.cwd()
            except psutil.AccessDenied:
                info['cmdline'] = []
                info['exe'] = ''
                info['cwd'] = ''
            
            # Entorno
            try:
                info['environ'] = dict(list(proc.environ().items())[:20])  # Limitar a 20 variables
            except psutil.AccessDenied:
                info['environ'] = {}
            
            return info
            
        except psutil.NoSuchProcess:
            return None
        except psutil.AccessDenied:
            return {'pid': pid, 'error': 'Acceso denegado'}
    
    def kill_process(self, pid, force=False):
        """
        Termina un proceso.
        
        Args:
            pid: ID del proceso a terminar
            force: Si es True, usa SIGKILL en lugar de SIGTERM
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
            
            if force:
                proc.kill()  # SIGKILL
                action = 'killed (SIGKILL)'
            else:
                proc.terminate()  # SIGTERM
                action = 'terminated (SIGTERM)'
            
            # Esperar a que el proceso termine
            try:
                proc.wait(timeout=3)
                return {
                    'success': True,
                    'message': f'Proceso {process_name} (PID: {pid}) {action} exitosamente',
                    'pid': pid,
                    'name': process_name
                }
            except psutil.TimeoutExpired:
                return {
                    'success': True,
                    'message': f'Señal enviada a {process_name} (PID: {pid}), esperando terminación...',
                    'pid': pid,
                    'name': process_name,
                    'warning': 'El proceso no terminó en 3 segundos'
                }
                
        except psutil.NoSuchProcess:
            return {
                'success': False,
                'message': f'Proceso con PID {pid} no encontrado',
                'pid': pid
            }
        except psutil.AccessDenied:
            return {
                'success': False,
                'message': f'Permiso denegado para terminar proceso {pid}. Intente con sudo.',
                'pid': pid
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al terminar proceso {pid}: {str(e)}',
                'pid': pid
            }
    
    def search_processes(self, query):
        """
        Busca procesos por nombre.
        
        Args:
            query: Texto a buscar en el nombre del proceso
            
        Returns:
            Lista de procesos que coinciden
        """
        query = query.lower()
        all_processes = self.get_process_list()
        
        return [p for p in all_processes 
                if query in p['name'].lower() or 
                   query in str(p['pid']) or
                   query in p.get('cmdline', '').lower()]
    
    def get_top_processes(self, by='memory', limit=10):
        """
        Obtiene los procesos que más recursos consumen.
        
        Args:
            by: 'memory', 'cpu' o 'disk'
            limit: Número máximo de procesos a devolver
            
        Returns:
            Lista de procesos ordenados
        """
        sort_field = {
            'memory': 'memory_percent',
            'cpu': 'cpu_percent',
            'disk': 'disk_total_mb'
        }.get(by, 'memory_percent')
        
        processes = self.get_process_list(sort_by=sort_field, descending=True)
        return processes[:limit]
    
    def get_process_tree(self, pid=None):
        """
        Obtiene el árbol de procesos.
        
        Args:
            pid: PID del proceso padre (None para todos los procesos raíz)
            
        Returns:
            Árbol de procesos como diccionario anidado
        """
        def build_tree(parent_pid):
            children = []
            for proc in psutil.process_iter(['pid', 'name', 'ppid']):
                try:
                    if proc.info['ppid'] == parent_pid:
                        children.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'children': build_tree(proc.info['pid'])
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return children
        
        if pid is not None:
            try:
                proc = psutil.Process(pid)
                return {
                    'pid': pid,
                    'name': proc.name(),
                    'children': build_tree(pid)
                }
            except psutil.NoSuchProcess:
                return None
        else:
            # Procesos raíz (PPID = 0 o 1)
            roots = []
            for proc in psutil.process_iter(['pid', 'name', 'ppid']):
                try:
                    if proc.info['ppid'] in [0, 1]:
                        roots.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'children': build_tree(proc.info['pid'])
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return roots
    
    def get_system_summary(self):
        """Obtiene un resumen del estado de los procesos."""
        processes = self.get_process_list()
        
        status_count = {}
        total_memory = 0
        total_cpu = 0
        
        for proc in processes:
            status = proc.get('status', 'unknown')
            status_count[status] = status_count.get(status, 0) + 1
            total_memory += proc.get('memory_percent', 0)
            total_cpu += proc.get('cpu_percent', 0)
        
        return {
            'total_processes': len(processes),
            'status_breakdown': status_count,
            'total_memory_percent': total_memory,
            'total_cpu_percent': total_cpu,
            'timestamp': datetime.now()
        }
