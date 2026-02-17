---
title: "Comandos esenciales de LVM: guía rápida"
description: "Cheatsheet con los comandos más usados de LVM (Logical Volume Manager) para la gestión de volúmenes lógicos en Linux."
author: "antonio"
pubDate: 2025-02-01
category: "Automatización"
tags: ["LVM", "Storage", "Linux", "Cheatsheet"]
image: "../../assets/images/lvm-storage.jpg"
draft: false
---

## Qué es LVM

LVM (Logical Volume Manager) permite gestionar el almacenamiento de forma flexible, añadiendo capas de abstracción sobre los discos físicos. Sus tres componentes principales son:

- **PV** (Physical Volume): disco o partición física
- **VG** (Volume Group): agrupación de PVs
- **LV** (Logical Volume): volúmenes que se formatean y montan

## Volúmenes físicos (PV)

```bash
# Crear un PV
pvcreate /dev/sdb

# Listar PVs
pvs
pvdisplay

# Ver información detallada
pvdisplay /dev/sdb

# Eliminar un PV
pvremove /dev/sdb
```

## Grupos de volúmenes (VG)

```bash
# Crear un VG
vgcreate vg_data /dev/sdb /dev/sdc

# Extender un VG con un nuevo disco
vgextend vg_data /dev/sdd

# Listar VGs
vgs
vgdisplay

# Reducir un VG
vgreduce vg_data /dev/sdd

# Eliminar un VG
vgremove vg_data
```

## Volúmenes lógicos (LV)

### Crear volúmenes

```bash
# Crear LV de tamaño fijo
lvcreate -L 50G -n lv_apps vg_data

# Crear LV usando porcentaje del espacio libre
lvcreate -l 100%FREE -n lv_logs vg_data

# Crear LV con nombre específico
lvcreate -L 10G -n lv_backups vg_data
```

### Listar y consultar

```bash
# Listar LVs
lvs
lvdisplay

# Ver ruta del dispositivo
ls -la /dev/vg_data/
```

### Redimensionar volúmenes

```bash
# Extender un LV (+20GB)
lvextend -L +20G /dev/vg_data/lv_apps

# Extender al máximo del espacio disponible
lvextend -l +100%FREE /dev/vg_data/lv_apps

# Redimensionar el sistema de archivos (ext4)
resize2fs /dev/vg_data/lv_apps

# Extender LV y filesystem en un solo paso
lvextend -L +20G --resizefs /dev/vg_data/lv_apps

# Para XFS
xfs_growfs /mount/point
```

### Reducir volúmenes

```bash
# Reducir (solo ext4, NO xfs)
umount /dev/vg_data/lv_apps
e2fsck -f /dev/vg_data/lv_apps
resize2fs /dev/vg_data/lv_apps 30G
lvreduce -L 30G /dev/vg_data/lv_apps
mount /dev/vg_data/lv_apps /mnt/apps
```

### Eliminar volúmenes

```bash
umount /dev/vg_data/lv_apps
lvremove /dev/vg_data/lv_apps
```

## Snapshots

```bash
# Crear snapshot
lvcreate -s -L 5G -n snap_apps /dev/vg_data/lv_apps

# Restaurar desde snapshot
lvconvert --merge /dev/vg_data/snap_apps

# Eliminar snapshot
lvremove /dev/vg_data/snap_apps
```

## Formatear y montar

```bash
# Formatear con ext4
mkfs.ext4 /dev/vg_data/lv_apps

# Formatear con XFS
mkfs.xfs /dev/vg_data/lv_apps

# Montar
mkdir -p /mnt/apps
mount /dev/vg_data/lv_apps /mnt/apps

# Añadir a fstab para persistencia
echo '/dev/vg_data/lv_apps /mnt/apps ext4 defaults 0 2' >> /etc/fstab
```

## Resumen visual del flujo

```
Disco (/dev/sdb) → PV → VG (vg_data) → LV (lv_apps) → Filesystem → Mount
```

## Comandos de diagnóstico

```bash
# Ver todo el stack LVM
lsblk
df -hT
vgs -o +vg_free
lvs -o +lv_size,seg_pe_ranges
```

> Recuerda: siempre haz un backup antes de modificar volúmenes en producción.
