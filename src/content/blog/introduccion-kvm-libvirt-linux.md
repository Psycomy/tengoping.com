---
title: 'Introducción a KVM y libvirt en Linux'
description: 'Guía para empezar con virtualización KVM en Linux: instalación de libvirt, creación de VMs desde terminal y configuración de red.'
author: 'antonio'
pubDate: 2026-01-26
category: 'Virtualización'
tags: ['KVM', 'libvirt', 'Virtualización', 'Linux']
image: '../../assets/images/kvm-libvirt.jpg'
draft: true
---

## Que es KVM

KVM (Kernel-based Virtual Machine) es el hipervisor nativo de Linux. Desde la version 2.6.20 del kernel, KVM convierte Linux en un hipervisor de tipo 1 capaz de ejecutar maquinas virtuales con rendimiento casi nativo gracias a las extensiones de virtualizacion del procesador (Intel VT-x o AMD-V).

A diferencia de soluciones como VirtualBox, KVM trabaja directamente con el kernel y delega la emulacion de hardware a QEMU. La capa de gestion la proporciona libvirt, un conjunto de herramientas y APIs que simplifica la administracion de VMs desde la linea de comandos.

## Verificar soporte de virtualizacion

Antes de instalar nada, comprueba que tu CPU soporta virtualizacion por hardware:

```bash
grep -Ec '(vmx|svm)' /proc/cpuinfo
```

Si el resultado es mayor que 0, tu procesador soporta KVM. Tambien puedes verificar que el modulo esta cargado:

```bash
lsmod | grep kvm
```

## Instalacion

### En distribuciones RHEL/Fedora

```bash
sudo dnf install qemu-kvm libvirt virt-install virt-viewer -y
sudo systemctl enable --now libvirtd
```

### En distribuciones Debian/Ubuntu

```bash
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients virtinst virt-viewer -y
sudo systemctl enable --now libvirtd
```

Anade tu usuario al grupo libvirt para poder gestionar VMs sin sudo:

```bash
sudo usermod -aG libvirt $USER
newgrp libvirt
```

Verifica que el servicio esta activo:

```bash
systemctl status libvirtd
```

## Crear una VM con virt-install

La herramienta `virt-install` permite crear maquinas virtuales directamente desde la terminal. Este ejemplo crea una VM con Debian 12:

```bash
virt-install \
  --name debian12-server \
  --ram 2048 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/debian12.qcow2,size=20 \
  --os-variant debian12 \
  --network network=default \
  --graphics none \
  --console pty,target_type=serial \
  --location https://deb.debian.org/debian/dists/bookworm/main/installer-amd64/ \
  --extra-args 'console=ttyS0,115200n8'
```

Los parametros clave son:

- `--ram` y `--vcpus`: recursos asignados a la VM.
- `--disk`: ruta y tamano del disco virtual en formato qcow2.
- `--os-variant`: optimizaciones automaticas segun el SO. Consulta las opciones con `osinfo-query os`.
- `--network`: red virtual a la que se conecta la VM.
- `--graphics none`: instalacion por consola serie, ideal para servidores.

## Gestion de VMs con virsh

`virsh` es el cliente de linea de comandos de libvirt. Estos son los comandos mas habituales:

### Listar maquinas virtuales

```bash
virsh list --all
```

### Arrancar y detener VMs

```bash
virsh start debian12-server
virsh shutdown debian12-server
virsh destroy debian12-server   # apagado forzado
```

### Conectar a la consola

```bash
virsh console debian12-server
```

Para salir de la consola pulsa `Ctrl+]`.

### Crear y gestionar snapshots

Los snapshots permiten guardar el estado de la VM en un punto concreto:

```bash
virsh snapshot-create-as debian12-server --name "pre-actualizacion" \
  --description "Antes de actualizar paquetes"
```

Listar snapshots disponibles:

```bash
virsh snapshot-list debian12-server
```

Revertir a un snapshot anterior:

```bash
virsh snapshot-revert debian12-server --snapshotname "pre-actualizacion"
```

Eliminar un snapshot que ya no necesitas:

```bash
virsh snapshot-delete debian12-server --snapshotname "pre-actualizacion"
```

## Configuracion de red NAT

Por defecto, libvirt crea una red NAT llamada `default` que permite a las VMs acceder a Internet a traves del host. Puedes verificar su estado con:

```bash
virsh net-list --all
```

Si la red no esta activa, iniciala manualmente:

```bash
virsh net-start default
virsh net-autostart default
```

La red `default` utiliza el rango 192.168.122.0/24 y asigna direcciones mediante un DHCP interno gestionado por dnsmasq. Para consultar las IPs asignadas:

```bash
virsh net-dhcp-leases default
```

Si necesitas acceder a la VM desde otras maquinas de tu LAN, puedes configurar un bridge o usar port forwarding con iptables, pero eso queda para una guia mas avanzada.

## Comandos de referencia rapida

```bash
virsh list --all                  # ver todas las VMs
virsh start <vm>                  # arrancar VM
virsh shutdown <vm>               # apagar VM (graceful)
virsh destroy <vm>                # apagar VM (forzado)
virsh undefine <vm> --remove-all-storage  # eliminar VM y disco
virsh dominfo <vm>                # informacion de la VM
virsh edit <vm>                   # editar XML de la VM
virsh snapshot-create-as <vm> --name <snap>  # crear snapshot
virsh snapshot-revert <vm> --snapshotname <snap>  # revertir
```

## Conclusion

KVM con libvirt es la base de la virtualizacion en Linux. Con `virt-install` y `virsh` puedes crear y gestionar maquinas virtuales completas sin salir de la terminal. Una vez domines estos fundamentos, puedes explorar redes bridge, almacenamiento compartido y migracion en vivo entre hosts.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
