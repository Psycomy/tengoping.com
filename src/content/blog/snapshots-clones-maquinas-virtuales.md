---
title: 'Snapshots y clones en máquinas virtuales'
description: 'Cómo usar snapshots y clones en KVM y Proxmox para proteger tus VMs y acelerar despliegues.'
author: 'antonio'
pubDate: 2026-02-10
category: 'Virtualización'
tags: ['Snapshots', 'KVM', 'Proxmox', 'Virtualización']
image: '../../assets/images/vm-snapshots.jpg'
draft: true
---

## Snapshots vs clones

Antes de entrar en comandos, conviene entender la diferencia fundamental entre estas dos operaciones:

Un **snapshot** captura el estado de una VM en un momento concreto. No crea una copia independiente del disco: guarda las diferencias (deltas) respecto al estado original. Esto lo hace rapido y ligero, pero el snapshot depende del disco base. Su uso principal es crear puntos de restauracion antes de cambios arriesgados.

Un **clon** es una copia completa o parcial de la VM que funciona de forma independiente. Una vez creado, el clon no tiene dependencia con la VM original. Se usa para generar nuevas VMs a partir de una plantilla ya configurada.

## Snapshots en KVM con virsh

### Crear un snapshot

```bash
virsh snapshot-create-as mi-vm \
  --name "pre-upgrade" \
  --description "Antes de actualizar a Debian 13"
```

Este comando crea un snapshot interno del disco qcow2. Si la VM esta en ejecucion, tambien captura el estado de la memoria RAM.

### Listar snapshots

```bash
virsh snapshot-list mi-vm
```

Salida tipica:

```
 Name          Creation Time              State
-------------------------------------------------
 pre-upgrade   2026-10-20 14:30:00 +0200  running
 post-config   2026-10-21 09:15:00 +0200  shutoff
```

### Obtener informacion de un snapshot

```bash
virsh snapshot-info mi-vm --snapshotname "pre-upgrade"
```

### Revertir a un snapshot

```bash
virsh snapshot-revert mi-vm --snapshotname "pre-upgrade"
```

La VM vuelve al estado exacto en que se creo el snapshot. Si el snapshot se creo con la VM en ejecucion, la VM se reanuda automaticamente.

### Eliminar un snapshot

```bash
virsh snapshot-delete mi-vm --snapshotname "pre-upgrade"
```

Al eliminar un snapshot, los datos del delta se fusionan con la capa anterior. No se pierde informacion del estado actual.

## Como funcionan los snapshots en qcow2

El formato qcow2 (QEMU Copy-On-Write) soporta snapshots de forma nativa. Cuando creas un snapshot, qcow2 congela el estado actual del disco y empieza a escribir los cambios nuevos en una capa diferencial.

Puedes inspeccionar los snapshots internos de un disco:

```bash
qemu-img info /var/lib/libvirt/images/mi-vm.qcow2
```

La salida mostrara una seccion de snapshots con cada punto guardado, su tamano y la fecha de creacion.

Para ver la cadena de dependencias de un disco con snapshots externos:

```bash
qemu-img info --backing-chain /var/lib/libvirt/images/mi-vm.qcow2
```

Hay que tener en cuenta que acumular muchos snapshots degrada el rendimiento de I/O, porque cada lectura debe recorrer la cadena de capas hasta encontrar el bloque solicitado.

## Snapshots en Proxmox

### Desde la interfaz web

Proxmox facilita la gestion de snapshots desde el panel:

1. Selecciona la VM o contenedor en el arbol lateral.
2. Ve a la pestana "Snapshots".
3. Pulsa "Take Snapshot", asigna un nombre y opcionalmente incluye la RAM.
4. Para revertir, selecciona el snapshot y pulsa "Rollback".

### Desde la linea de comandos

Para maquinas virtuales (qm):

```bash
qm snapshot 100 pre-upgrade --description "Antes de actualizar"
qm listsnapshot 100
qm rollback 100 pre-upgrade
qm delsnapshot 100 pre-upgrade
```

Para contenedores LXC (pct):

```bash
pct snapshot 200 pre-config
pct listsnapshot 200
pct rollback 200 pre-config
pct delsnapshot 200 pre-config
```

## Clones: linked vs full

### Full clone (clon completo)

Un full clone copia todo el disco de la VM original. Es completamente independiente pero ocupa el mismo espacio:

En KVM con virt-clone:

```bash
virt-clone --original mi-vm --name mi-vm-clon \
  --file /var/lib/libvirt/images/mi-vm-clon.qcow2
```

En Proxmox:

```bash
qm clone 100 101 --name vm-clon --full
```

### Linked clone (clon enlazado)

Un linked clone comparte el disco base con la VM original y solo almacena las diferencias. Es mucho mas rapido de crear y ocupa menos espacio, pero depende del disco original:

En Proxmox, primero convierte la VM en plantilla y luego clona:

```bash
qm template 100
qm clone 100 102 --name vm-linked
```

Por defecto, clonar desde una plantilla en Proxmox crea un linked clone. Para un full clone desde plantilla:

```bash
qm clone 100 103 --name vm-full --full
```

### Comparativa

| Caracteristica     | Full clone         | Linked clone       |
| ------------------ | ------------------ | ------------------ |
| Espacio en disco   | Igual al original  | Solo diferencias   |
| Velocidad creacion | Lenta (copia todo) | Rapida             |
| Independencia      | Total              | Depende de la base |
| Uso tipico         | Produccion         | Testing, labs      |

## Buenas practicas

**Limita el numero de snapshots activos.** Cada snapshot anade una capa de lectura. Mas de 3-4 snapshots encadenados pueden afectar notablemente al rendimiento de disco.

**Nombra los snapshots de forma descriptiva.** Usa nombres que indiquen que cambio preceden, como `pre-upgrade-kernel-6.8` o `post-config-nginx`. Tu yo futuro lo agradecera.

**No uses snapshots como backups.** Los snapshots residen en el mismo disco que la VM. Si el disco falla, pierdes la VM y todos sus snapshots. Combina snapshots con backups externos (vzdump en Proxmox, o copias del qcow2 a otro almacenamiento).

**Consolida snapshots tras verificar cambios.** Si la actualizacion fue bien y no necesitas revertir, elimina el snapshot. Esto fusiona las capas y mejora el rendimiento.

**Usa linked clones para labs y testing.** Son ideales para levantar entornos temporales rapidamente. Para VMs de produccion, opta siempre por full clones.

**Apaga la VM antes de clonar si es posible.** Clonar una VM en ejecucion puede generar inconsistencias en el sistema de archivos del guest. Si necesitas clonar en caliente, asegurate de que el guest tenga el agente QEMU instalado.

## Conclusion

Los snapshots y clones son herramientas fundamentales en la gestion de maquinas virtuales. Los snapshots te protegen ante cambios arriesgados; los clones te permiten replicar entornos rapidamente. Conocer como funcionan internamente y sus limitaciones te ayudara a usarlos de forma eficiente y segura.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
