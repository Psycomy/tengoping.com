---
title: 'Incus/LXC: contenedores de sistema en Linux'
description: 'Incus gestiona contenedores de sistema con LXC: instalación, incus launch, storage pools y redes, y cuándo elegirlo frente a Docker o una VM.'
author: 'antonio'
pubDate: 2026-08-03
category: 'Virtualización'
tags: ['LXC', 'Incus', 'Virtualización', 'Linux', 'Contenedores']
image: '../../assets/images/virt-incus.jpg'
draft: false
---

Incus es el gestor de contenedores e hipervisor ligero del proyecto Linux Containers, construido sobre LXC. A diferencia de Docker o Podman, que empaquetan un solo proceso o servicio, Incus levanta **contenedores de sistema**: instancias con su propio `systemd`, múltiples servicios y un ciclo de vida que se parece más al de una máquina virtual que al de un contenedor de aplicación, pero compartiendo el kernel del host y con el arranque casi instantáneo de un contenedor.

## Qué es Incus y de dónde viene

Incus nació en agosto de 2023 como un fork comunitario de LXD, el proyecto que Canonical llevaba manteniendo desde 2014. Canonical empezó a exigir a los colaboradores externos firmar un acuerdo (CLA) que le daba control total sobre el código, y el mismo equipo que había creado LXD decidió forkearlo bajo el proyecto Linux Containers para mantenerlo 100% comunitario ([The Register](https://www.theregister.com/software/2023/08/04/incus-a-new-fork-of-canonicals-lxd-containervisor/)). La versión LTS actual es Incus 7.0, publicada en mayo de 2026 con soporte hasta 2031.

En la práctica, Incus es a LXC lo que `virsh`/`libvirt` es a QEMU/KVM: una capa de gestión (API REST, CLI, red, storage, migración) sobre una tecnología de bajo nivel que ya existía. Si ya usas [KVM y libvirt](/blog/kvm-libvirt-virtualizacion-nativa-linux/), Incus te resultará familiar — de hecho gestiona ambas cosas, contenedores LXC y VMs QEMU, con la misma CLI.

> [!NOTE]
> Si vienes de [Proxmox VE](/blog/proxmox-ve-hipervisor-casero/): sus contenedores LXC usan la misma tecnología de base (`liblxc`, namespaces y cgroups del kernel). Lo que cambia es la capa de gestión — Proxmox los administra con su propia herramienta (`pct`) integrada en su web UI y en el clúster, mientras que Incus los gestiona con su API y CLI propias. Por dentro, un contenedor creado en Proxmox y uno creado con Incus son el mismo tipo de aislamiento.

## Contenedores de sistema vs de aplicación vs VMs

Es fácil confundir "contenedor" con "Docker", pero son dos modelos de aislamiento distintos:

```
Aislamiento y qué corre dentro de cada capa
   │
   ├── VM completa (KVM/libvirt)          → kernel propio, arranca un SO entero desde cero
   ├── Contenedor de sistema (Incus/LXC)  → kernel compartido con el host, pero con systemd/init propio y varios servicios
   └── Contenedor de aplicación (Podman)  → kernel compartido con el host, un único proceso empaquetado con sus dependencias
```

- **VM (KVM):** kernel independiente, aislamiento total. Más pesada, arranque en segundos.
- **Contenedor de sistema (Incus/LXC):** kernel compartido con el host, pero con `systemd` real dentro gestionando varios servicios — como una VM ligera. Arranque casi instantáneo.
- **Contenedor de aplicación (Docker/Podman):** kernel compartido, imagen con un único proceso y sus dependencias. Pensado para inmutabilidad, no para administrar un sistema completo por dentro.

En la práctica, la pregunta no es "¿cuál es mejor?" sino "¿qué necesito aislar?":

- **Incus/LXC** si quieres algo que se administre como un servidor Linux normal — varios servicios, tu propio usuario SSH, `systemctl` funcionando de verdad — o migrar una VM o un servidor físico existente sin reescribir nada.
- **[Docker](/blog/docker-guia-practica-contenedores-linux/)/Podman** si el objetivo es empaquetar una aplicación concreta de forma inmutable con un `Dockerfile` versionado. Ya escribí sobre ese modelo en la [introducción a Podman](/blog/introduccion-contenedores-podman-linux/).
- **VM completa (KVM)** si necesitas un kernel distinto al del host o aislar inquilinos que no confían entre sí.

En un homelab es habitual combinar los tres: KVM/Proxmox para servicios grandes y con estado, Incus para "mini-servidores" ligeros, y Docker/Podman para aplicaciones que ya vienen empaquetadas así.

## Instalación

La distribución de tu Linux probablemente ya trae un paquete de Incus, pero suele ir varias versiones por detrás. El propio proyecto mantiene el repositorio [Zabbly](https://github.com/zabbly/incus) con paquetes actualizados para Debian y Ubuntu, que es la vía recomendada si quieres la última LTS (7.0) o la interfaz web incluida:

```bash
# Añade la clave y el repositorio Zabbly (Incus 7.0 LTS)
sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://pkgs.zabbly.com/key.asc -o /etc/apt/keyrings/zabbly.asc

sudo sh -c 'cat <<EOF > /etc/apt/sources.list.d/zabbly-incus-lts-7.0.sources
Enabled: yes
Types: deb
URIs: https://pkgs.zabbly.com/incus/lts-7.0
Suites: $(. /etc/os-release && echo ${VERSION_CODENAME})
Components: main
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/zabbly.asc
EOF'

sudo apt update
sudo apt install -y incus qemu-system
```

En Ubuntu 24.04 y posteriores también existe un paquete `incus` nativo en los repos oficiales (`sudo apt install incus`), pero sigue la rama 6.0 LTS con soporte de Ubuntu en lugar de la última versión del proyecto.

> [!IMPORTANT]
> Tras instalar, ejecuta `incus admin init` antes de crear ningún contenedor. Este paso configura el storage pool por defecto y la red bridge (`incusbr0`) — sin él, `incus launch` falla porque no hay dónde guardar las instancias ni cómo darles red.

```bash
sudo incus admin init
```

El asistente interactivo pregunta por el backend de almacenamiento (ZFS, btrfs, LVM o simple directorio), si quieres crear una red bridge local, y si quieres exponer la API en la red (útil si vas a gestionar el host en remoto). Para un homelab de un solo nodo, aceptar los valores por defecto (`--minimal`) es suficiente:

```bash
sudo incus admin init --minimal
```

## Primeros pasos: lanzar y gestionar contenedores

Incus descarga imágenes de un servidor remoto (por defecto `images:`, el catálogo de linuxcontainers.org) la primera vez que las usas, y las cachea localmente:

```bash
# Lanza un contenedor de sistema Debian 12
incus launch images:debian/12 web01

# Lanza una VM (mismo comando, con --vm) en vez de un contenedor
incus launch images:debian/12 vm01 --vm -c limits.cpu=2 -c limits.memory=2GiB

# Lista instancias (contenedores y VMs)
incus list

# Entra en una shell dentro del contenedor
incus exec web01 -- bash

# Para, arranca y borra
incus stop web01
incus start web01
incus delete web01
```

La diferencia entre `incus launch imagen nombre` y `incus launch imagen nombre --vm` es solo esa flag: mismo flujo de trabajo, mismo catálogo de imágenes, pero una crea un contenedor LXC y la otra una VM QEMU completa. Es la ventaja práctica de tener contenedores y VMs bajo la misma herramienta.

Dentro del contenedor tienes un Debian normal — puedes instalar y arrancar servicios exactamente como en cualquier servidor Linux, sin nada especial:

```bash
# Instala y arranca nginx dentro del contenedor
incus exec web01 -- apt update
incus exec web01 -- apt install -y nginx

# Comprueba la IP del contenedor y que el servicio responde
incus list web01
incus exec web01 -- curl -s localhost
```

## Storage pools

Incus organiza el almacenamiento en _storage pools_ — el equivalente a los grupos de volúmenes que ya viste si has trabajado con [LVM](/blog/comandos-esenciales-lvm-guia-rapida/). Cada instancia guarda su sistema de archivos raíz como un volumen dentro de un pool:

```bash
# Crea un pool adicional con backend ZFS sobre un dispositivo dedicado
incus storage create datos zfs source=/dev/sdb

# Lista los pools existentes
incus storage list

# Lanza un contenedor usando ese pool en vez del que viene por defecto
incus launch images:debian/12 web02 --storage datos
```

ZFS y btrfs son los backends recomendados porque soportan snapshots y clonado eficiente (copy-on-write); con `dir` (un directorio normal) funciona pero pierdes esas operaciones rápidas.

## Redes

`incus admin init` crea por defecto un bridge local (`incusbr0`) con NAT hacia el exterior, igual que hace `virbr0` en libvirt. Para exponer un servicio del contenedor en la red local sin NAT, puedes conectarlo directamente a un bridge existente del host:

```bash
# Crea un dispositivo de red conectado al bridge br0 del host
incus network attach br0 web01 eth0

# O defínelo directamente al lanzar el contenedor
incus launch images:debian/12 web01 --network br0
```

> [!TIP]
> Si vas a exponer varios contenedores en distintas VLANs, el mismo enfoque que usarías con KVM/libvirt aplica aquí: crea bridges o sub-interfaces por VLAN en el host y asigna cada contenedor al que corresponda. Si no lo tienes claro, la guía de [VLANs para segmentar red](/blog/vlans-explicadas-segmentar-red/) cubre el paso previo a nivel de switch.

## Snapshots y migración entre hosts

Antes de tocar algo arriesgado en un contenedor (una actualización mayor, un cambio de configuración delicado), crea un snapshot:

```bash
# Crea un snapshot
incus snapshot create web01 antes-de-actualizar

# Lista los snapshots del contenedor
incus snapshot list web01

# Si algo sale mal, restaura
incus snapshot restore web01 antes-de-actualizar
```

Para mover una instancia a otro host o a otro nodo de un clúster Incus, el comando es `incus move`:

```bash
incus move web01 --target otro-nodo
```

> [!NOTE]
> Que el traslado sea realmente "en caliente" (sin cortar el servicio) depende del tipo de instancia. En las VMs, Incus soporta migración en vivo de forma fiable. En contenedores LXC, la migración en caliente depende de CRIU y hoy solo funciona con contenedores muy básicos (sin `systemd` ni dispositivos de red) — para un contenedor de sistema normal, `incus move` implica parar, mover y volver a arrancar, no una migración sin corte de servicio.

## Siguiente paso

Si vienes de gestionar VMs con KVM y libvirt, el salto a Incus es principalmente de vocabulario: mismo modelo mental de imágenes, instancias y storage pools, pero con el arranque instantáneo de un contenedor. Empieza lanzando un par de contenedores de sistema para servicios que hoy tengas sueltos en el host (un servidor DNS, un proxy, una herramienta de monitorización) y comprueba cuánto menos overhead necesitan frente a la misma carga en una VM.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
