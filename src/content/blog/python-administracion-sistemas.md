---
title: "Python para administración de sistemas: scripts y automatización"
description: "Aprende a usar Python para automatizar tareas de administración de sistemas: gestión de procesos, conexiones SSH, monitorización de recursos y scripts prácticos para el día a día."
author: "antonio"
pubDate: 2026-02-16
category: "Software"
tags: ["python", "scripting", "automatizacion", "sysadmin"]
image: "../../assets/images/soft-python.jpg"
draft: false
---

Si llevas tiempo administrando sistemas, seguro que tienes una colección de scripts en Bash que resuelven problemas del día a día. Funcionan, los conoces bien y hacen su trabajo. Entonces, ¿por qué molestarse con Python?

La respuesta corta: porque hay cosas que en Bash se convierten en un infierno de `awk`, `sed` y pipes encadenados, mientras que en Python se resuelven en cinco líneas legibles. Parsear JSON, conectarte por SSH a veinte servidores en paralelo, generar informes con formato o interactuar con APIs REST son tareas donde Python brilla sin necesidad de instalar media docena de utilidades externas.

Python no viene a reemplazar a Bash. Viene a complementarlo. Para un `grep` rápido o un pipeline sencillo, Bash sigue siendo la herramienta adecuada. Pero cuando tu script empieza a necesitar funciones, manejo de errores robusto o estructuras de datos complejas, es hora de dar el salto.

## Requisitos previos

Para seguir los ejemplos de este artículo necesitas:

- **Python 3.8+** instalado (la mayoría de distribuciones actuales lo incluyen)
- Familiaridad básica con la terminal y Bash
- Un entorno virtual para no ensuciar el sistema:

```bash
python3 -m venv ~/sysadmin-env
source ~/sysadmin-env/bin/activate
```

- Las librerías que usaremos:

```bash
pip install paramiko psutil
```

Los módulos `os`, `shutil` y `subprocess` vienen incluidos en la librería estándar, así que no necesitan instalación.

## Ejecutar comandos del sistema con subprocess

El módulo `subprocess` es el puente entre Python y la shell. Te permite lanzar cualquier comando y capturar su salida de forma controlada.

### Ejecución básica

```python
import subprocess

# subprocess.run devuelve un objeto CompletedProcess
resultado = subprocess.run(
    ["df", "-h"],          # comando como lista (más seguro que string)
    capture_output=True,   # captura stdout y stderr
    text=True              # devuelve strings en lugar de bytes
)

print(resultado.stdout)

# Comprobar si el comando falló
if resultado.returncode != 0:
    print(f"Error: {resultado.stderr}")
```

Un detalle importante: pasa siempre el comando como lista (`["df", "-h"]`) en vez de como string (`"df -h"` con `shell=True`). La segunda forma es vulnerable a inyección de comandos si algún parámetro viene de una entrada del usuario.

### Script práctico: verificar servicios

Este script comprueba el estado de una lista de servicios y genera un resumen:

```python
import subprocess
import sys

SERVICIOS = ["nginx", "postgresql", "redis-server", "ssh"]

def verificar_servicio(nombre):
    """Comprueba si un servicio systemd está activo."""
    resultado = subprocess.run(
        ["systemctl", "is-active", nombre],
        capture_output=True,
        text=True
    )
    # systemctl is-active devuelve 0 si está activo
    return resultado.stdout.strip() == "active"

def main():
    print(f"{'Servicio':<20} {'Estado':<10}")
    print("-" * 30)

    fallos = []
    for servicio in SERVICIOS:
        activo = verificar_servicio(servicio)
        estado = "OK" if activo else "CAÍDO"
        print(f"{servicio:<20} {estado:<10}")
        if not activo:
            fallos.append(servicio)

    if fallos:
        print(f"\n¡Atención! Servicios caídos: {', '.join(fallos)}")
        sys.exit(1)  # código de salida no-cero para integrar con cron/monitoring

if __name__ == "__main__":
    main()
```

Puedes meter este script en un cron o en un timer de systemd y que te envíe una alerta cuando algo falle.

## Gestión de archivos con os y shutil

Para operaciones con el sistema de archivos, Python ofrece `os`, `os.path` y `shutil`. La ventaja sobre Bash es el manejo de errores: en vez de comprobar `$?` después de cada comando, usas bloques `try/except` que hacen el código mucho más claro.

### Script práctico: rotación de logs

```python
import os
import shutil
import time
from datetime import datetime

LOG_DIR = "/var/log/miapp"
ARCHIVO_DIR = "/var/log/miapp/archivo"
DIAS_RETENCION = 30

def rotar_logs():
    """Mueve logs antiguos a carpeta de archivo y elimina los más viejos."""
    os.makedirs(ARCHIVO_DIR, exist_ok=True)  # crea el directorio si no existe

    ahora = time.time()
    limite_segundos = DIAS_RETENCION * 86400  # 86400 segundos en un día

    for archivo in os.listdir(LOG_DIR):
        ruta = os.path.join(LOG_DIR, archivo)

        # Saltar directorios y el propio directorio de archivo
        if not os.path.isfile(ruta):
            continue

        edad = ahora - os.path.getmtime(ruta)  # segundos desde última modificación

        if edad > limite_segundos:
            # Log muy antiguo: eliminar
            os.remove(ruta)
            print(f"Eliminado: {archivo} ({edad / 86400:.0f} días)")
        elif archivo.endswith(".log") and edad > 86400:
            # Log de más de un día: mover a archivo
            destino = os.path.join(ARCHIVO_DIR, archivo)
            shutil.move(ruta, destino)
            print(f"Archivado: {archivo}")

if __name__ == "__main__":
    rotar_logs()
```

### Operaciones comunes que deberías conocer

```python
import os
import shutil

# Copiar un archivo preservando metadatos
shutil.copy2("/etc/nginx/nginx.conf", "/backup/nginx.conf.bak")

# Copiar un directorio completo de forma recursiva
shutil.copytree("/etc/nginx", "/backup/nginx-full")

# Obtener el tamaño de un directorio
def tamano_directorio(ruta):
    """Calcula el tamaño total en bytes de un directorio."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(ruta):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # os.path.islink evita seguir enlaces simbólicos rotos
            if not os.path.islink(fp):
                total += os.path.getsize(fp)
    return total

# Resultado en MB
tamano = tamano_directorio("/var/log")
print(f"/var/log ocupa {tamano / (1024**2):.1f} MB")
```

## Monitorización de recursos con psutil

`psutil` es una librería multiplataforma que te da acceso a información del sistema sin tener que parsear la salida de comandos como `top`, `free` o `df`. Datos estructurados, sin regex, sin sorpresas entre distribuciones.

### Dashboard de sistema en tiempo real

```python
import psutil
import time

def mostrar_estado():
    """Muestra un resumen del estado del sistema."""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)  # intervalo de 1s para medición precisa
    cpu_count = psutil.cpu_count()

    # Memoria
    mem = psutil.virtual_memory()

    # Disco
    disco = psutil.disk_usage("/")

    # Red (bytes enviados/recibidos desde el arranque)
    red = psutil.net_io_counters()

    # Procesos
    num_procesos = len(psutil.pids())

    print(f"""
=== Estado del sistema ===
CPU:      {cpu_percent}% ({cpu_count} cores)
Memoria:  {mem.percent}% usado ({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)
Disco /:  {disco.percent}% usado ({disco.free // (1024**3)}GB libre)
Red:      ↑ {red.bytes_sent // (1024**2)}MB  ↓ {red.bytes_recv // (1024**2)}MB
Procesos: {num_procesos} activos
""")

if __name__ == "__main__":
    mostrar_estado()
```

### Detectar procesos que consumen demasiados recursos

```python
import psutil

UMBRAL_CPU = 80.0    # porcentaje
UMBRAL_MEM = 500     # MB

def procesos_pesados():
    """Encuentra procesos que superan los umbrales de CPU o memoria."""
    pesados = []

    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            info = proc.info
            mem_mb = info["memory_info"].rss / (1024 ** 2)  # RSS en MB

            if info["cpu_percent"] > UMBRAL_CPU or mem_mb > UMBRAL_MEM:
                pesados.append({
                    "pid": info["pid"],
                    "nombre": info["name"],
                    "cpu": info["cpu_percent"],
                    "mem_mb": round(mem_mb, 1)
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # El proceso puede haber terminado entre la iteración y la consulta
            continue

    return pesados

if __name__ == "__main__":
    # Primera llamada a cpu_percent siempre devuelve 0, así que hacemos una de calentamiento
    for proc in psutil.process_iter(["cpu_percent"]):
        pass

    import time
    time.sleep(1)  # esperar para que la segunda medición sea real

    resultados = procesos_pesados()

    if resultados:
        print(f"{'PID':<8} {'Nombre':<20} {'CPU%':<8} {'MEM (MB)':<10}")
        print("-" * 46)
        for p in resultados:
            print(f"{p['pid']:<8} {p['nombre']:<20} {p['cpu']:<8} {p['mem_mb']:<10}")
    else:
        print("Todos los procesos dentro de los umbrales.")
```

## Conexiones SSH con Paramiko

Cuando necesitas ejecutar comandos en servidores remotos, `paramiko` te permite hacerlo desde Python sin depender de `expect` ni de wrappers sobre el binario `ssh`.

### Ejecución remota básica

```python
import paramiko

def ejecutar_remoto(host, usuario, comando, puerto=22):
    """Ejecuta un comando en un servidor remoto por SSH."""
    cliente = paramiko.SSHClient()
    # Aceptar automáticamente la clave del host (en producción, usa un known_hosts)
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Usa la clave SSH del agente o de ~/.ssh/id_rsa por defecto
        cliente.connect(host, port=puerto, username=usuario)

        stdin, stdout, stderr = cliente.exec_command(comando)

        salida = stdout.read().decode().strip()
        errores = stderr.read().decode().strip()

        codigo = stdout.channel.recv_exit_status()

        return {
            "host": host,
            "salida": salida,
            "errores": errores,
            "codigo": codigo
        }
    finally:
        cliente.close()  # siempre cerrar la conexión

# Ejemplo de uso
resultado = ejecutar_remoto("192.168.1.10", "admin", "uptime")
print(f"{resultado['host']}: {resultado['salida']}")
```

### Script práctico: ejecutar en múltiples servidores

```python
import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed

SERVIDORES = [
    {"host": "web01.ejemplo.com", "usuario": "deploy"},
    {"host": "web02.ejemplo.com", "usuario": "deploy"},
    {"host": "db01.ejemplo.com", "usuario": "admin"},
]

def ejecutar_en_servidor(servidor, comando):
    """Ejecuta un comando en un servidor y devuelve el resultado."""
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        cliente.connect(servidor["host"], username=servidor["usuario"])
        stdin, stdout, stderr = cliente.exec_command(comando)
        salida = stdout.read().decode().strip()
        codigo = stdout.channel.recv_exit_status()

        return {
            "host": servidor["host"],
            "salida": salida,
            "ok": codigo == 0
        }
    except Exception as e:
        return {
            "host": servidor["host"],
            "salida": str(e),
            "ok": False
        }
    finally:
        cliente.close()

def ejecutar_en_flota(comando, max_hilos=5):
    """Ejecuta un comando en todos los servidores en paralelo."""
    # ThreadPoolExecutor lanza las conexiones en paralelo
    with ThreadPoolExecutor(max_workers=max_hilos) as pool:
        futuros = {
            pool.submit(ejecutar_en_servidor, srv, comando): srv
            for srv in SERVIDORES
        }

        for futuro in as_completed(futuros):
            resultado = futuro.result()
            estado = "✓" if resultado["ok"] else "✗"
            print(f"[{estado}] {resultado['host']}")
            print(f"    {resultado['salida']}\n")

if __name__ == "__main__":
    print("=== Uptime de la flota ===\n")
    ejecutar_en_flota("uptime")
```

La clave aquí es `ThreadPoolExecutor`: si tienes 20 servidores no quieres conectarte a uno, esperar, conectarte al siguiente... Con hilos puedes lanzar todas las conexiones a la vez y reducir el tiempo total de ejecución de forma drástica.

## Juntándolo todo: script de auditoría

Para cerrar, un ejemplo que combina varias de las técnicas que hemos visto en un script de auditoría básico del sistema local:

```python
#!/usr/bin/env python3
"""Auditoría rápida del sistema local."""

import subprocess
import psutil
import os
from datetime import datetime

def auditar():
    informe = []
    informe.append(f"Auditoría del sistema - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    informe.append("=" * 50)

    # Información del sistema
    uname = os.uname()
    informe.append(f"Host:     {uname.nodename}")
    informe.append(f"Kernel:   {uname.release}")

    # Carga del sistema
    carga = os.getloadavg()
    informe.append(f"Carga:    {carga[0]:.2f} / {carga[1]:.2f} / {carga[2]:.2f}")

    # Memoria
    mem = psutil.virtual_memory()
    informe.append(f"Memoria:  {mem.percent}% usado")

    # Discos con más del 80% de uso
    informe.append("\nDiscos con uso > 80%:")
    for part in psutil.disk_partitions():
        try:
            uso = psutil.disk_usage(part.mountpoint)
            if uso.percent > 80:
                informe.append(f"  {part.mountpoint}: {uso.percent}%")
        except PermissionError:
            continue  # particiones sin acceso (snap, etc.)

    # Puertos en escucha
    informe.append("\nPuertos TCP en escucha:")
    for conn in psutil.net_connections(kind="tcp"):
        if conn.status == "LISTEN":
            # laddr es una tupla (ip, puerto)
            informe.append(f"  :{conn.laddr.port}")

    # Actualizaciones pendientes (Debian/Ubuntu)
    resultado = subprocess.run(
        ["apt", "list", "--upgradable"],
        capture_output=True, text=True
    )
    # La primera línea es un encabezado, las demás son paquetes
    paquetes = [l for l in resultado.stdout.splitlines() if "/" in l]
    informe.append(f"\nActualizaciones pendientes: {len(paquetes)}")

    return "\n".join(informe)

if __name__ == "__main__":
    resultado = auditar()
    print(resultado)

    # Guardar el informe
    ruta = f"/tmp/auditoria-{datetime.now().strftime('%Y%m%d')}.txt"
    with open(ruta, "w") as f:
        f.write(resultado)
    print(f"\nInforme guardado en {ruta}")
```

## Siguiente paso

Con lo que has visto en este artículo ya puedes empezar a migrar tus scripts de Bash más complejos a Python. Mi recomendación: no intentes reescribirlo todo de golpe. Elige el script que más te cueste mantener y empieza por ahí.

Si quieres ir más allá, estos son buenos siguientes pasos:

- **Fabric**: una librería de alto nivel para ejecución remota que simplifica mucho el trabajo con SSH para despliegues.
- **Click o argparse**: para construir CLIs profesionales con argumentos, flags y documentación automática.
- **logging**: sustituye los `print()` por el módulo de logging estándar para tener niveles de severidad, rotación de ficheros y formato consistente.
- **systemd timers o cron**: programa tus scripts Python para que se ejecuten periódicamente y tendrás un sistema de monitorización hecho a medida.

La gracia de Python para sysadmin no es hacer cosas que no puedas hacer con Bash. Es hacerlas de forma que dentro de seis meses puedas abrir el script, entenderlo en treinta segundos y modificarlo sin miedo a romper algo.
