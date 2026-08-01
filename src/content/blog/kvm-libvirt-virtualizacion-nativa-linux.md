---
title: 'KVM y libvirt: virtualización nativa en Linux'
description: 'Instala KVM y libvirt en Linux sin Proxmox: crea máquinas virtuales con virt-install, gestiónalas con virsh y configura la red por defecto.'
author: 'antonio'
pubDate: 2026-08-01
category: 'Virtualización'
tags: ['KVM', 'Virtualización', 'Linux', 'Homelab']
image: '../../assets/images/virt-kvm.jpg'
draft: false
---

Si ya usas [Proxmox VE](/blog/proxmox-ve-hipervisor-casero/) sabes que por debajo corre sobre KVM. Este artículo es justo eso: la capa que hay debajo de Proxmox, montada a mano sobre un Linux normal, sin interfaz web ni clúster. Útil cuando quieres el mínimo software posible entre tú y las VMs, o cuando ya tienes un servidor Linux funcionando y no quieres reinstalarlo con un hipervisor dedicado.

## Qué son KVM, QEMU y libvirt

Son tres piezas distintas que casi siempre se mencionan juntas:

- **KVM** (Kernel-based Virtual Machine) es un módulo del kernel de Linux que convierte el propio kernel en un hipervisor, usando las extensiones de virtualización por hardware de la CPU (Intel VT-x o AMD-V).
- **QEMU** es el emulador que hace de máquina virtual en sí: gestiona el disco, la tarjeta de red virtual, la BIOS/UEFI de la VM, etc. Cuando trabaja junto a KVM, delega la ejecución de instrucciones de CPU al hardware real en vez de emularlas por software, que es lo que hace que una VM KVM/QEMU rinda casi igual que el hardware físico.
- **libvirt** es la capa de gestión: un demonio (`libvirtd` o, en versiones recientes, demonios modulares como `virtqemud`) y una API común que abstrae KVM, Xen o VMware bajo la misma interfaz. `virsh` (línea de comandos), `virt-install` (crear VMs) y `virt-manager` (GUI) hablan con libvirt, no con QEMU directamente.

Proxmox VE es precisamente KVM + QEMU + libvirt con una interfaz web y gestión de clúster añadidas encima. Si no necesitas clúster ni interfaz gráfica, libvirt a pelo es un sistema más ligero y con menos piezas que pueden fallar.

## Requisitos previos

Necesitas una CPU con virtualización por hardware activada en la BIOS/UEFI. Compruébalo así:

```bash
egrep -c '(vmx|svm)' /proc/cpuinfo
```

Un número mayor que 0 confirma que el kernel ve el soporte de virtualización (`vmx` en Intel, `svm` en AMD). Si devuelve `0`, revisa la BIOS antes de seguir.

## Instalación

Los nombres de paquete varían entre distribuciones, y no siempre coinciden con lo que dicen guías antiguas:

### Debian 12/13

```bash
sudo apt update
sudo apt install --no-install-recommends qemu-system libvirt-clients libvirt-daemon-system
```

> [!IMPORTANT]
> En Debian 12/13, `qemu-kvm` ya no es un paquete real: es un nombre virtual que apunta a `qemu-system-x86` (o `qemu-system` como metapaquete). Si sigues una guía que dice `apt install qemu-kvm`, apt lo resolverá igualmente, pero el paquete instalado será otro. En Ubuntu, en cambio, `qemu-kvm` sigue siendo el nombre de paquete que usa la documentación oficial — no asumas que el mismo comando significa lo mismo en las dos distros.

### Ubuntu

```bash
sudo apt update
sudo apt install qemu-kvm libvirt-daemon-system
```

### RHEL / Rocky Linux / AlmaLinux

```bash
sudo dnf install -y qemu-kvm libvirt virt-install virt-viewer
sudo systemctl enable --now libvirtd
```

O, si prefieres no elegir paquete a paquete, el grupo completo:

```bash
sudo dnf install -y @virtualization
```

## Gestiona VMs sin sudo

Por defecto solo root (y usuarios en el grupo `sudo`) puede usar `virsh`. Para gestionar VMs con tu usuario normal, añádelo al grupo `libvirt`:

```bash
sudo adduser $USER libvirt
```

Cierra sesión y vuelve a entrar para que el cambio de grupo tenga efecto. A partir de ahí, `virsh list --all` debería funcionar sin `sudo`.

## La red por defecto

Nada más instalar, libvirt ya trae una red NAT lista para usar, llamada `default`:

```bash
virsh net-list --all
virsh net-start default      # si no aparece como activa
virsh net-autostart default  # para que arranque sola en el próximo boot
```

Esta red usa el puente `virbr0`, con el host en `192.168.122.1` y DHCP (vía `dnsmasq`) repartiendo direcciones entre `192.168.122.2` y `192.168.122.254`. Las VMs tienen salida a internet, pero no son alcanzables desde el resto de tu red local — para eso hace falta una red con bridge (lo ves en la siguiente sección).

## Crear tu primera VM con virt-install

Con una ISO de instalación local:

```bash
virt-install \
  --name vm-web01 \
  --memory 2048 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/vm-web01.qcow2,size=20 \
  --cdrom /ruta/a/debian-13.iso \
  --network network=default \
  --graphics none \
  --console pty,target_type=serial
```

> [!TIP]
> `--ram` está obsoleto desde hace varias versiones de `virt-install` — usa `--memory` (en MiB). Si copias comandos de guías antiguas, revisa este detalle antes de ejecutarlos.

Para consultar los valores válidos de sistema operativo (usados por `--osinfo` para optimizar la configuración de la VM, como el tipo de disco virtual recomendado):

```bash
virt-install --osinfo list
```

Si ya tienes una imagen de disco lista (por ejemplo, una cloud image de Debian/Ubuntu descargada en `.qcow2`), sáltate la instalación completa con `--import`:

```bash
virt-install \
  --name vm-web02 \
  --memory 2048 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/vm-web02.qcow2 \
  --import \
  --osinfo detect=on,require=off \
  --network network=default \
  --graphics none
```

## Gestionar VMs con virsh

Los comandos del día a día:

```bash
virsh list --all              # todas las VMs, arrancadas o no
virsh start vm-web01
virsh shutdown vm-web01       # apagado ordenado (ACPI)
virsh destroy vm-web01        # apagado forzoso, equivalente a cortar la corriente
virsh console vm-web01        # consola serie (sal con Ctrl+])
virsh dumpxml vm-web01        # ver la configuración XML completa de la VM
```

> [!CAUTION]
> `virsh undefine vm-web01 --remove-all-storage` borra la definición de la VM **y** su disco virtual sin pedir confirmación. No hay papelera ni deshacer — antes de ejecutarlo, comprueba dos veces el nombre de la VM.

## NAT por defecto vs red con bridge

La red `default` (NAT) es perfecta para desarrollo y pruebas, pero si necesitas que la VM tenga su propia IP en tu red local — por ejemplo, para exponer un servicio web directamente — necesitas una interfaz bridge en el host que conecte directamente a tu red física, y arrancar la VM con `--network bridge=br0` en vez de `--network network=default`. La configuración exacta del bridge depende de tu gestor de red (`netplan`, `NetworkManager` o `/etc/network/interfaces`) y queda fuera del alcance de esta guía, pero es el primer paso a buscar si necesitas acceso directo desde el resto de tu red.

## Dónde se guardan los discos: storage pools

Todos los ejemplos anteriores usan `/var/lib/libvirt/images/`, que es el storage pool que libvirt crea automáticamente al instalarse (se llama, sin sorpresas, `default`). Para consultarlo:

```bash
virsh pool-list --all
virsh pool-info default
virsh vol-list default        # discos que contiene
```

Si ese punto de montaje se te queda corto — por ejemplo, porque tus discos de VMs quieres guardarlos en un volumen LVM separado — puedes definir un pool adicional apuntando a otra ruta o dispositivo con `virsh pool-define-as`, en vez de mover el pool `default`.

## Snapshots rápidos

Antes de un cambio arriesgado en una VM, un snapshot es más rápido que un backup completo:

```bash
virsh snapshot-create-as vm-web01 antes-de-actualizar
virsh snapshot-list vm-web01
virsh snapshot-revert vm-web01 antes-de-actualizar
```

Los snapshots internos (los que crea `snapshot-create-as` por defecto) requieren que el disco esté en formato `qcow2` — con discos `raw` necesitarás snapshots externos, que funcionan distinto.

## KVM/libvirt o Proxmox: cuál elegir

Si ya tienes un servidor Linux con otros servicios corriendo y solo necesitas un par de VMs puntuales, KVM/libvirt a pelo evita añadir una capa de gestión completa. Si vas a levantar un servidor dedicado a virtualización, quieres clúster, snapshots programados desde una interfaz o simplemente prefieres no memorizar comandos de `virsh`, [Proxmox VE](/blog/proxmox-ve-hipervisor-casero/) te da todo eso ya montado — usa exactamente lo mismo por debajo, así que lo que aprendas aquí (redes, discos, snapshots) se traslada directamente. Y si lo que buscas no es un hipervisor de propósito general sino entornos de desarrollo reproducibles y desechables, esa es la comparación que ya vimos en la guía de [Vagrant](/blog/vagrant-entornos-desarrollo-reproducibles/), que de hecho puede usar libvirt como proveedor por debajo.

## Siguiente paso

Con esto tienes lo esencial para levantar VMs sueltas en cualquier Linux sin depender de un hipervisor dedicado. Si vas a montar un servidor pensado desde cero para virtualización, revisa antes la guía de [cómo elegir hardware para tu homelab](/blog/elegir-hardware-homelab/) — la RAM disponible es, con diferencia, el factor que más limita cuántas VMs puedes correr a la vez.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
