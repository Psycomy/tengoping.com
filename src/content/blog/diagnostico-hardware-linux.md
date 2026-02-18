---
title: 'Diagnóstico de hardware en Linux desde terminal'
description: 'Herramientas de línea de comandos para diagnosticar CPU, RAM, discos y red en sistemas Linux.'
author: 'antonio'
pubDate: 2026-01-25
category: 'Hardware'
tags: ['Diagnóstico', 'Hardware', 'Linux', 'Sysadmin']
image: '../../assets/images/linux-hardware-diag.jpg'
draft: false
---

## Introduccion

Cuando un servidor se comporta de forma extraña, lo primero es descartar problemas de hardware. Linux ofrece un arsenal de herramientas de terminal para diagnosticar cada componente del sistema sin necesidad de interfaces gráficas ni reinicios. En esta guía repasamos las utilidades esenciales para inspeccionar CPU, RAM, discos, red y temperaturas.

## CPU: identificar y estresar el procesador

### Información del procesador

```bash
# Resumen rápido del procesador
lscpu

# Detalle completo incluyendo flags y vulnerabilidades
cat /proc/cpuinfo | head -30

# Solo el modelo y número de cores
lscpu | grep -E "Model name|Socket|Core|Thread"
```

El comando `lscpu` muestra de un vistazo la arquitectura, el número de cores físicos y lógicos, las frecuencias y si el procesador soporta virtualización (VT-x/AMD-V).

### Test de estrés con stress-ng

Para verificar que la CPU es estable bajo carga sostenida (útil tras un overclock o cuando sospechas de problemas térmicos):

```bash
# Instalar stress-ng
sudo apt install stress-ng    # Debian/Ubuntu
sudo dnf install stress-ng    # Fedora/RHEL

# Estresar todos los cores durante 5 minutos
stress-ng --cpu 0 --timeout 300s --metrics-brief

# Test específico de operaciones en punto flotante
stress-ng --cpu 0 --cpu-method matrixprod --timeout 120s
```

Mientras corre el test, monitoriza la temperatura y las frecuencias en otra terminal para detectar throttling.

## RAM: capacidad, tipo y errores

### Uso actual de memoria

```bash
# Resumen de uso de RAM
free -h

# Desglose detallado
cat /proc/meminfo | head -15
```

La línea importante en `free` es la de **available**, que indica cuánta memoria puede usar realmente una nueva aplicación (incluye buffers y cache que el kernel puede liberar).

### Información física de los módulos

```bash
# Tipo, velocidad y slots de memoria (requiere root)
sudo dmidecode -t memory | grep -E "Size|Type|Speed|Locator"
```

Esto muestra cuántos slots tienes ocupados, la capacidad de cada módulo, el tipo (DDR4, DDR5) y la velocidad configurada. Muy útil para saber si puedes ampliar la RAM sin abrir la carcasa.

### Test de errores con memtest86+

Para un test exhaustivo de RAM, la herramienta de referencia sigue siendo memtest86+. No se ejecuta desde el sistema operativo sino desde el arranque:

```bash
# Instalar memtest86+ para que aparezca en GRUB
sudo apt install memtest86+
sudo update-grub

# Al reiniciar, selecciona memtest86+ desde el menú de GRUB
```

Un test completo de RAM tarda varias horas dependiendo de la cantidad de memoria. Si encuentra errores, hay que reemplazar el módulo afectado.

## Discos: estado, rendimiento y SMART

### Listar discos y particiones

```bash
# Vista de árbol de discos y particiones
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL

# Información detallada de un disco
sudo hdparm -I /dev/sda | head -20
```

### Monitorización SMART

SMART (Self-Monitoring, Analysis and Reporting Technology) permite detectar fallos de disco antes de que ocurran:

```bash
# Instalar smartmontools
sudo apt install smartmontools

# Estado general del disco
sudo smartctl -H /dev/sda

# Informe completo con todos los atributos
sudo smartctl -a /dev/sda

# Iniciar un test de diagnóstico corto
sudo smartctl -t short /dev/sda

# Ver resultados del test (esperar unos minutos)
sudo smartctl -l selftest /dev/sda
```

Los atributos SMART más críticos a vigilar son:

- **Reallocated_Sector_Ct**: sectores reasignados por defectuosos. Si crece, el disco está muriendo.
- **Current_Pending_Sector**: sectores pendientes de reasignación. Otro indicador de fallo inminente.
- **UDMA_CRC_Error_Count**: errores de transferencia. Puede indicar un cable SATA defectuoso.

### Benchmarks de disco con fio

```bash
# Instalar fio
sudo apt install fio

# Test de lectura secuencial
fio --name=seq-read --rw=read --bs=1M --size=1G --numjobs=1 \
    --runtime=30 --filename=/tmp/fio-test

# Test de escritura aleatoria (simula carga de base de datos)
fio --name=rand-write --rw=randwrite --bs=4k --size=512M --numjobs=4 \
    --runtime=30 --filename=/tmp/fio-test

# Limpiar el archivo de test
rm /tmp/fio-test
```

## Red: enlace, velocidad y latencia

### Estado de la interfaz

```bash
# Ver todas las interfaces y sus IPs
ip addr show

# Detalles del enlace físico (velocidad, duplex, driver)
sudo ethtool eth0
```

Si `ethtool` muestra una velocidad inferior a la esperada (100 Mbps en lugar de 1 Gbps), revisa el cable de red, el puerto del switch o prueba a forzar la negociación:

```bash
# Forzar velocidad y duplex (solo si la autonegociación falla)
sudo ethtool -s eth0 speed 1000 duplex full autoneg on
```

### Medir el ancho de banda con iperf3

```bash
# Instalar iperf3
sudo apt install iperf3

# En el servidor (máquina destino)
iperf3 -s

# En el cliente (máquina origen)
iperf3 -c IP_DEL_SERVIDOR -t 10

# Test con múltiples flujos paralelos
iperf3 -c IP_DEL_SERVIDOR -P 4 -t 10
```

Un enlace Gigabit debería dar entre 900 y 940 Mbps en condiciones normales. Si obtienes significativamente menos, el problema puede estar en el cable, el switch o la configuración de la interfaz.

## Temperaturas: lm-sensors

```bash
# Instalar lm-sensors
sudo apt install lm-sensors

# Detectar los sensores disponibles (responder YES a todo)
sudo sensors-detect

# Leer las temperaturas actuales
sensors
```

La salida muestra temperaturas de CPU, chipset y, en algunos casos, discos y GPU. Para monitorización continua:

```bash
# Actualizar cada 2 segundos
watch -n 2 sensors
```

Temperaturas de CPU por encima de 85-90 grados bajo carga indican un problema de refrigeración. Comprueba la pasta térmica, el disipador y el flujo de aire de la carcasa.

## Dispositivos PCI y USB

```bash
# Listar dispositivos PCI (tarjetas de red, GPU, controladores)
lspci

# Con detalle del driver en uso
lspci -k

# Listar dispositivos USB
lsusb

# Con detalle jerárquico
lsusb -t
```

Estos comandos son esenciales cuando instalas hardware nuevo y necesitas verificar que el kernel lo detecta y tiene un driver cargado.

## Vista general del sistema: inxi y hwinfo

Para obtener un resumen completo del hardware en un solo comando:

```bash
# Instalar inxi
sudo apt install inxi

# Resumen completo del sistema
inxi -Fz

# Solo CPU, RAM y discos
inxi -CDm
```

La opción `-z` oculta información sensible como direcciones MAC e IPs, útil si vas a pegar la salida en un foro o ticket de soporte.

Para un inventario más detallado:

```bash
# Instalar hwinfo
sudo apt install hwinfo

# Resumen de hardware
hwinfo --short

# Detalle de un componente específico
hwinfo --disk
hwinfo --network
```

## Script de diagnostico rapido

Un script sencillo que recopila la información esencial de un vistazo:

```bash
#!/bin/bash
echo "=== CPU ==="
lscpu | grep -E "Model name|Socket|Core|Thread|MHz"
echo ""
echo "=== RAM ==="
free -h
echo ""
echo "=== DISCOS ==="
lsblk -d -o NAME,SIZE,MODEL,ROTA
echo ""
echo "=== RED ==="
ip -br addr show
echo ""
echo "=== TEMPERATURAS ==="
sensors 2>/dev/null || echo "lm-sensors no instalado"
echo ""
echo "=== SMART (disco principal) ==="
sudo smartctl -H /dev/sda 2>/dev/null || echo "smartctl no disponible"
```

Guárdalo como `hw-diag.sh`, dale permisos de ejecución y ejecútalo como root para obtener un diagnóstico rápido:

```bash
chmod +x hw-diag.sh
sudo ./hw-diag.sh
```

## Conclusion

Diagnosticar hardware desde la terminal no solo es posible sino que es la forma más directa y eficiente de hacerlo en servidores Linux. Con `smartctl` puedes anticipar fallos de disco, con `stress-ng` verificar la estabilidad de la CPU, con `sensors` controlar las temperaturas y con `iperf3` medir el rendimiento real de la red. Incorpora estas herramientas a tu rutina de mantenimiento y tendrás tus servidores bajo control.
