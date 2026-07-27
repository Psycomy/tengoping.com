---
title: 'Proxmox VE: monta tu propio hipervisor casero'
description: 'Instala y configura Proxmox VE como hipervisor tipo 1 para tu homelab: creación de VMs, snapshots, backups y primeros pasos con la red.'
author: 'antonio'
pubDate: 2026-07-25
updatedDate: 2026-07-27
category: 'Virtualización'
tags: ['Proxmox', 'Virtualización', 'Homelab', 'Hipervisor']
image: '../../assets/images/virt-proxmox.jpg'
draft: false
---

Proxmox VE es un hipervisor tipo 1 basado en Debian que te permite ejecutar máquinas virtuales KVM y contenedores LXC directamente sobre el hardware, sin pasar por un sistema operativo anfitrión. Es la opción más habitual para montar un servidor de virtualización casero: es gratuito, de código abierto, y ofrece una interfaz web completa para gestionar todo el clúster sin tocar la línea de comandos si no quieres.

A diferencia de Vagrant —que ya vimos en este blog y que orquesta VMs sobre un hipervisor existente como VirtualBox o libvirt—, Proxmox VE _es_ el hipervisor. No necesitas otro sistema operativo por debajo: lo instalas directamente en el hardware y desde ahí administras todas tus VMs y contenedores.

## Requisitos previos

Antes de instalar, ten en cuenta:

- **CPU de 64 bits** con soporte de virtualización por hardware (Intel VT-x o AMD-V), activado en la BIOS/UEFI
- **RAM**: 2 GB es el mínimo para el propio Proxmox, pero en la práctica necesitas sumar la memoria que vayas a asignar a cada VM o contenedor. Para un homelab con varias VMs ligeras, 16-32 GB es un punto de partida razonable
- **Almacenamiento**: al menos 32 GB para el sistema, preferiblemente en SSD — el rendimiento de disco es el cuello de botella más habitual en homelabs
- **Una interfaz de red** conectada a tu router o switch
- Un **USB booteable** de al menos 2 GB para el instalador

La versión actual es **Proxmox VE 9.2**, basada en Debian 13 "Trixie" con kernel Linux 6.14.

## Instalación

1. Descarga la ISO desde la [web oficial de Proxmox](https://www.proxmox.com/en/downloads) y grábala en un USB con `dd` o herramientas como Rufus/Balena Etcher.
2. Arranca la máquina desde el USB y sigue el asistente gráfico del instalador.
3. Elige el disco de destino y el sistema de ficheros. El instalador ofrece cuatro opciones:
   - **ext4** (por defecto, usa LVM)
   - **XFS** (usa LVM)
   - **ZFS** (RAID por software, recomendado si tienes varios discos y quieres redundancia sin controladora RAID dedicada)
   - **BTRFS** (en fase de vista previa tecnológica, no recomendado para producción)
4. Configura zona horaria, teclado y contraseña de root.
5. Configura la red: IP estática (recomendado para un hipervisor, que debe tener una dirección predecible), máscara, puerta de enlace y DNS.
6. Termina la instalación y reinicia. El servidor arrancará directamente en Proxmox VE.

Tras el primer arranque, accede a la interfaz web en `https://IP-DEL-SERVIDOR:8006` con el usuario `root` y la contraseña que definiste.

> [!TIP]
> Si vas a usar Proxmox en producción (no solo para pruebas), ten en cuenta que el repositorio `pve-enterprise` requiere suscripción de pago. Para uso doméstico, cambia al repositorio `pve-no-subscription`, gratuito, desde `Actualizaciones del sistema > Repositorios` en la interfaz web, o editando `/etc/apt/sources.list.d/`.

## Red: el puente vmbr0

El instalador crea automáticamente un puente Linux llamado `vmbr0`, conectado a tu primera tarjeta de red física. Este puente es el que usan tus VMs y contenedores para salir a la red: funciona como un switch virtual donde la interfaz física es un puerto más, y cada VM se conecta a otro puerto del mismo puente.

La configuración vive en `/etc/network/interfaces` y tiene un aspecto similar a este:

```
auto vmbr0
iface vmbr0 inet static
    address 192.168.1.10/24
    gateway 192.168.1.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
```

Si más adelante quieres segmentar tráfico por VLANs entre tus VMs, Proxmox soporta VLANs (IEEE 802.1q) directamente sobre este puente sin necesidad de crear interfaces adicionales — pero eso da para un artículo aparte.

## Crear tu primera máquina virtual

Desde la interfaz web:

1. Haz clic en **Crear VM** en la esquina superior derecha.
2. **General**: asigna un nombre y un VM ID (se autoincrementa).
3. **SO**: sube o selecciona la ISO de instalación (primero debes subirla a un storage tipo `local` desde `Almacenamiento > ISO Images`).
4. **Sistema**: normalmente puedes dejar los valores por defecto (BIOS SeaBIOS o UEFI, según lo que necesite tu SO invitado).
5. **Discos**: define el tamaño y el storage donde vivirá el disco virtual.
6. **CPU**: número de núcleos. Para uso general, el tipo `host` ofrece el mejor rendimiento al exponer el set de instrucciones real de tu CPU a la VM.
7. **Memoria**: RAM asignada.
8. **Red**: conecta la VM al puente `vmbr0` (o al que hayas creado).

Al terminar, arranca la VM e instala el sistema operativo como lo harías en una máquina física.

También puedes hacerlo por línea de comandos con `qm create`, útil si quieres scriptar la creación de VMs:

```bash
qm create 100 --name mi-vm --memory 4096 --cores 2 --net0 virtio,bridge=vmbr0
qm set 100 --ide2 local:iso/debian-13.0.0-amd64-netinst.iso,media=cdrom
qm set 100 --scsihw virtio-scsi-pci --scsi0 local-lvm:32
qm set 100 --boot "order=ide2;scsi0"
```

## Snapshots: guarda el estado de una VM

Un snapshot de Proxmox captura la memoria, la configuración y el estado de los discos virtuales de una VM en un momento dado, y te permite volver a ese punto exacto si algo sale mal — por ejemplo, antes de aplicar una actualización arriesgada.

Para crear uno desde la web: selecciona la VM, ve a la pestaña **Snapshots** y pulsa **Take Snapshot**. Puedes añadir una descripción y, opcionalmente, incluir el estado de RAM.

Por línea de comandos:

```bash
qm snapshot 100 antes-de-actualizar --description "Estado previo a actualizar el kernel"
```

Para volver a ese estado:

```bash
qm rollback 100 antes-de-actualizar
```

> [!IMPORTANT]
> Un snapshot **no es un backup**. Vive en el mismo storage que el disco de la VM, así que si pierdes ese disco, pierdes también los snapshots. Para proteger tus datos de verdad necesitas backups independientes.

## Backups con vzdump

Proxmox VE incluye `vzdump`, la herramienta de backup integrada que genera copias completas de VMs y contenedores (configuración + datos). A diferencia de los snapshots, los backups de `vzdump` no dependen del storage original y pueden guardarse en un destino distinto (otro disco, NFS, un servidor de backups Proxmox Backup Server, etc.).

Para configurar un backup programado, ve a **Centro de Datos > Backup** y define un job con el storage de destino, la programación y las VMs a incluir. También puedes lanzarlo manualmente:

```bash
vzdump 100 --storage backup-nfs --mode snapshot --compress zstd
```

El modo `snapshot` permite hacer el backup con la VM en marcha, minimizando el tiempo de inactividad.

## Siguiente paso

Con esto ya tienes un hipervisor funcional para tu homelab: puedes crear VMs y contenedores LXC, protegerlos con snapshots antes de cambios arriesgados, y programar backups reales con `vzdump`. El siguiente paso natural es explorar clustering (unir varios nodos Proxmox) o profundizar en el almacenamiento compartido con Ceph si tu homelab crece a varios servidores.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
