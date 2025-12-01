# 🖥️ Monitor de Recursos del Sistema

## Universidad San Francisco de Quito
### Sistemas Operativos - Proyecto Final
### Semestre 202510

---

## 📋 Descripción

Herramienta de monitoreo y visualización de recursos del sistema desarrollada en Python con interfaz gráfica PyQt5. Permite monitorear en tiempo real:

- **📊 CPU**: Utilización total y por núcleo, frecuencia, load average
- **🧠 Memoria RAM**: Uso de RAM y Swap, análisis de fragmentación
- **💾 Almacenamiento**: Uso de particiones, velocidad de I/O, fragmentación
- **⚙️ Procesos**: Lista de procesos con capacidad de terminarlos
- **🌐 Red**: Ancho de banda de upload y download

---

## 🚀 Instalación

### Requisitos previos
- Python 3.8 o superior
- Sistema operativo: Linux, macOS o Windows

### Pasos de instalación

1. **Clonar o descargar el proyecto**

2. **Crear entorno virtual (recomendado)**
```bash
python3 -m venv venv
source venv/bin/activate  # En Linux/macOS
# o
venv\Scripts\activate  # En Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

---

## 🎮 Uso

### Ejecutar la aplicación
```bash
python main.py
```

### Navegación
- Use las pestañas para navegar entre los diferentes monitores
- Presione **F5** para actualizar todos los recursos
- En la pestaña de Procesos, puede buscar y terminar procesos

---

## 📁 Estructura del Proyecto

```
ProyectoFinalSO/
│
├── main.py                     # Punto de entrada de la aplicación
├── requirements.txt            # Dependencias del proyecto
├── README.md                   # Este archivo
│
├── monitors/                   # Módulos de monitoreo
│   ├── __init__.py
│   ├── cpu_monitor.py         # Monitor de CPU
│   ├── memory_monitor.py      # Monitor de memoria RAM
│   ├── disk_monitor.py        # Monitor de almacenamiento
│   ├── process_monitor.py     # Monitor de procesos
│   └── network_monitor.py     # Monitor de red
│
└── gui/                        # Interfaz gráfica
    ├── __init__.py
    ├── main_window.py         # Ventana principal
    └── widgets/               # Widgets personalizados
        ├── __init__.py
        ├── cpu_widget.py
        ├── memory_widget.py
        ├── disk_widget.py
        ├── process_widget.py
        └── network_widget.py
```

---

## ✨ Características

### 1. Monitor de CPU
- Uso total del CPU en tiempo real
- Uso individual por cada núcleo
- Frecuencia del procesador
- Load average (1, 5, 15 minutos)
- Distribución de tiempo (usuario, sistema, inactivo)
- Gráfico histórico de la última hora

### 2. Monitor de Memoria RAM
- Uso de memoria RAM y Swap
- Memoria total, disponible, usada y libre
- **⭐ Análisis de fragmentación de memoria**
- Gráfico histórico de la última hora

### 3. Monitor de Almacenamiento
- Lista de particiones con uso
- Velocidad de lectura/escritura
- **⭐ Análisis de fragmentación de disco**
- Gráfico histórico de I/O

### 4. Monitor de Procesos
- Lista completa de procesos
- Información: PID, nombre, estado, CPU%, memoria, disco
- Búsqueda y filtrado
- **⭐ Capacidad de terminar procesos (SIGTERM y SIGKILL)**
- Vista detallada de cada proceso

### 5. Monitor de Red
- Velocidad de descarga (download) y subida (upload)
- Estadísticas totales de transferencia
- Lista de interfaces de red
- Conexiones activas
- Gráfico histórico de ancho de banda

---

## 🧵 Uso de Hilos

La aplicación utiliza hilos (threading) para:
1. **Recolección de datos**: Cada monitor tiene un hilo dedicado que recopila datos en segundo plano
2. **Actualización de UI**: Los timers de Qt actualizan la interfaz sin bloquear la interacción del usuario
3. **Historial**: Se mantiene un historial de la última hora de forma asíncrona

Esto permite que:
- La interfaz permanezca responsiva
- Los datos se actualicen constantemente
- El usuario pueda interactuar mientras se recopilan datos

---

## 🎯 Puntos Extra Implementados

1. **Fragmentación de Memoria RAM**: Análisis en tiempo real del nivel de fragmentación de la memoria
2. **Fragmentación de Disco**: Información sobre fragmentación del almacenamiento
3. **Terminar Procesos**: Posibilidad de matar procesos desde la aplicación con confirmación

---

## 🛠️ Tecnologías Utilizadas

| Tecnología | Uso |
|------------|-----|
| Python 3 | Lenguaje de programación |
| PyQt5 | Framework de interfaz gráfica |
| psutil | Obtención de información del sistema |
| matplotlib | Gráficos de historial |
| threading | Manejo de hilos para actualización |

---

## 📊 Capturas de Pantalla

*(Agregar capturas de pantalla de la aplicación en ejecución)*

---

## 👥 Integrantes del Grupo

| Nombre | Contribución |
|--------|--------------|
| [Nombre 1] | [Descripción de aportes] |
| [Nombre 2] | [Descripción de aportes] |
| [Nombre 3] | [Descripción de aportes] |

---

## 📝 Notas Adicionales

- La aplicación está optimizada para sistemas Linux y macOS
- En Windows, algunas características pueden tener comportamiento diferente
- Para terminar procesos del sistema puede requerirse ejecutar como administrador

---

## 📧 Contacto

Profesor: driofrioa@usfq.edu.ec  
Telegram: @danielriofrio

---

**Universidad San Francisco de Quito - 2025**
