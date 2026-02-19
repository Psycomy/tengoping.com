---
title: 'Proxmox VE: primeros pasos con virtualización profesional'
description: 'Cómo instalar y configurar Proxmox VE para gestionar máquinas virtuales y contenedores LXC desde una interfaz web.'
author: 'alois'
pubDate: 2025-05-22
category: 'Virtualización'
tags: ['Proxmox', 'Virtualización', 'LXC', 'Homelab']
image: '../../assets/images/proxmox-ve.jpg'
draft: false
---

## Que es Proxmox VE

Proxmox Virtual Environment es una plataforma de virtualizacion de codigo abierto basada en Debian. Combina dos tecnologias: KVM para maquinas virtuales completas y LXC para contenedores ligeros. Todo se gestiona desde una interfaz web accesible por navegador, aunque tambien dispone de herramientas CLI para automatizacion.

Es una opcion muy popular para homelabs y entornos de produccion porque ofrece funcionalidades de nivel enterprise (clustering, migracion en vivo, backups integrados) sin coste de licencia.

## Instalacion desde ISO

Descarga la ISO desde la web oficial de Proxmox y grabala en un USB con `dd`:

```bash
dd if=proxmox-ve_8.3-1.iso of=/dev/sdX bs=4M status=progress
```

Arranca desde el USB y sigue el asistente grafico. Los pasos principales son:

1. Aceptar la licencia AGPL.
2. Seleccionar el disco de destino (se formateara por completo).
3. Configurar pais, zona horaria y teclado.
4. Establecer la contrasena de root y un email de contacto.
5. Configurar la interfaz de red: hostname (por ejemplo `pve.local`), IP estatica, gateway y DNS.

Tras la instalacion, el sistema reinicia y muestra la URL de acceso a la interfaz web.

## Acceso a la interfaz web

Abre un navegador y navega a:

```
https://<IP-DEL-SERVIDOR>:8006
```

Inicia sesion con el usuario `root` y la contrasena que configuraste. El certificado SSL es autofirmado, asi que el navegador mostrara una advertencia que puedes aceptar.

Al entrar veras el panel principal con el datacenter a la izquierda, el nodo del servidor y un resumen de recursos (CPU, RAM, almacenamiento).

## Crear una maquina virtual

Desde la interfaz web:

1. Pulsa "Create VM" en la esquina superior derecha.
2. Asigna un nombre y un ID numerico.
3. Sube o selecciona una ISO en el almacenamiento local.
4. Configura el tipo de SO (Linux, Windows, etc.).
5. Ajusta disco, CPU y memoria segun necesidades.
6. Selecciona la red (por defecto `vmbr0`, el bridge de Linux).
7. Revisa el resumen y confirma.

Tambien puedes crear VMs desde la terminal con `qm`:

```bash
qm create 100 --name debian12 --memory 2048 --cores 2 \
  --net0 virtio,bridge=vmbr0 \
  --scsi0 local-lvm:20 \
  --cdrom local:iso/debian-12-amd64.iso \
  --boot order=scsi0;ide2
```

Arrancar la VM:

```bash
qm start 100
```

## Crear un contenedor LXC

Los contenedores LXC consumen menos recursos que una VM completa y arrancan en segundos. Para crearlos necesitas una plantilla de contenedor.

Descarga una plantilla desde la interfaz (Storage > CT Templates > Templates) o desde la terminal:

```bash
pveam update
pveam available | grep debian
pveam download local debian-12-standard_12.2-1_amd64.tar.zst
```

Crear el contenedor:

```bash
pct create 200 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  --hostname ct-debian \
  --memory 1024 \
  --cores 1 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --rootfs local-lvm:8 \
  --password
```

Arrancar y acceder:

```bash
pct start 200
pct enter 200
```

## Configuracion de almacenamiento

Proxmox soporta varios backends de almacenamiento. Los mas comunes son:

### Almacenamiento local (LVM)

La instalacion por defecto crea dos volumenes:

- `local`: para ISOs, plantillas y backups (tipo directory).
- `local-lvm`: para discos de VMs y contenedores (tipo LVM-thin).

Puedes verificar el estado desde la terminal:

```bash
pvesm status
```

### ZFS

Si necesitas snapshots eficientes, compresion y verificacion de integridad, puedes configurar un pool ZFS:

```bash
zpool create -f tank /dev/sdb /dev/sdc
pvesm add zfspool tank-storage --pool tank --content images,rootdir
```

ZFS es especialmente util para entornos donde los snapshots y la replicacion son criticos.

## Backups con vzdump

Proxmox incluye `vzdump` para crear copias de seguridad de VMs y contenedores:

```bash
vzdump 100 --mode snapshot --compress zstd --storage local
```

Los modos de backup disponibles son:

- `snapshot`: sin downtime, captura el estado en caliente.
- `suspend`: pausa brevemente la VM para garantizar consistencia.
- `stop`: detiene la VM antes del backup (maximo consistencia).

Para programar backups automaticos, ve a Datacenter > Backup en la interfaz web y crea un job con la frecuencia deseada. Tambien puedes anadirlo al cron del sistema:

```bash
# Backup diario a las 2:00 AM
0 2 * * * vzdump 100 200 --mode snapshot --compress zstd --storage local --mailto admin@ejemplo.com
```

Listar backups disponibles:

```bash
pvesm list local --content backup
```

## Comandos utiles

```bash
qm list                    # listar VMs
qm start/stop/shutdown <id> # gestionar VM
pct list                   # listar contenedores
pct start/stop <id>        # gestionar contenedor
pvesm status               # estado del almacenamiento
vzdump <id> --mode snapshot # backup con snapshot
pveam update               # actualizar plantillas
```

## Conclusion

Proxmox VE ofrece una plataforma completa de virtualizacion sin coste de licencia. Con KVM para VMs y LXC para contenedores, es una solucion versatil tanto para homelabs como para entornos de produccion. La combinacion de interfaz web y herramientas CLI permite gestionar toda la infraestructura de forma eficiente.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
