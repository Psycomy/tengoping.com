---
title: 'Comandos esenciales de LVM: guía rápida'
description: 'Cheatsheet con los comandos más usados de LVM (Logical Volume Manager) para la gestión de volúmenes lógicos en Linux.'
author: 'antonio'
pubDate: 2026-02-20
category: 'Automatización'
tags: ['LVM', 'Storage', 'Linux', 'Cheatsheet']
image: '../../assets/images/lvm-storage.jpg'
draft: false
---

## Los comandos básicos de LVM organizados por nivel

**1. Volúmenes Físicos (PV - Physical Volumes)**

- `pvs` - ver resumen de volúmenes físicos
- `pvdisplay` - ver detalles completos
- `pvcreate /dev/sdb` - crear un volumen físico

**2. Grupos de Volúmenes (VG - Volume Groups)**

- `vgs` - ver resumen de grupos
- `vgdisplay` - ver detalles completos
- `vgcreate nombre_vg /dev/sdb` - crear grupo
- `vgextend nombre_vg /dev/sdc` - añadir disco al grupo

**3. Volúmenes Lógicos (LV - Logical Volumes)**

- `lvs` - ver resumen de volúmenes lógicos
- `lvdisplay` - ver detalles completos
- `lvcreate -L 10G -n nombre_lv nombre_vg` - crear volumen de 10GB
- `lvextend -L +5G /dev/nombre_vg/nombre_lv` - ampliar 5GB más
- `lvresize -L 20G /dev/nombre_vg/nombre_lv` - establecer tamaño fijo

## Truco para recordarlos

El patrón es siempre el mismo:

- **Consulta rápida**: `pvs`, `vgs`, `lvs` (la "s" de summary)
- **Consulta detallada**: `pvdisplay`, `vgdisplay`, `lvdisplay`
- **Crear**: `pvcreate`, `vgcreate`, `lvcreate`
- **Extender**: `vgextend`, `lvextend`

## Secuencia típica que usarás

```bash
# 1. Ver qué discos tienes disponibles
lsblk

# 2. Crear volumen físico en el nuevo disco
pvcreate /dev/sdb

# 3. Añadirlo a un grupo existente
vgextend vg_datos /dev/sdb
# o crear uno nuevo
vgcreate vg_datos /dev/sdb

# 4. Ampliar el volumen lógico
lvextend -L +50G /dev/vg_datos/lv_archivos
# o para usar todo el espacio disponible:
lvextend -l +100%FREE /dev/vg_datos/lv_archivos

# 5. Ampliar el sistema de archivos
resize2fs /dev/vg_datos/lv_archivos  # para ext4
# o
xfs_growfs /dev/vg_datos/lv_archivos  # para xfs

```

## Proceso para extender un volumen LVM

**1. Primero, verificar el estado actual**

```bash
# Ver los volúmenes lógicos y su tamaño
lvs

# Ver cuánto espacio libre tiene el grupo de volúmenes
vgs

```

**2. Extender el volumen lógico**

Tienes dos opciones:

```bash
# Opción A: Añadir una cantidad específica
lvextend -L +10G /dev/nombre_vg/nombre_lv

# Opción B: Usar todo el espacio libre disponible
lvextend -l +100%FREE /dev/nombre_vg/nombre_lv

```

**3. Extender el sistema de archivos** (¡IMPORTANTE! Sin este paso no verás el espacio)

```bash
# Para ext4
resize2fs /dev/nombre_vg/nombre_lv

# Para xfs
xfs_growfs /dev/nombre_vg/nombre_lv

```

**4. Verificar que se aplicó**

```bash
df -h

```

## Ejemplo práctico completo

```bash
# 1. Ver estado
lvs
vgs

# 2. Extender 20GB más al volumen
lvextend -L +20G /dev/vg_datos/lv_home

# 3. Extender el sistema de archivos
resize2fs /dev/vg_datos/lv_home

# 4. Confirmar
df -h /home

```

## ¿Y si no hay espacio libre en el VG?

Si `vgs` muestra que no hay espacio libre (VFree = 0), primero necesitas añadir un disco nuevo:

```bash
# 1. Preparar el nuevo disco
pvcreate /dev/sdc

# 2. Añadirlo al grupo de volúmenes
vgextend nombre_vg /dev/sdc

# 3. Ahora sí, extender el volumen lógico
lvextend -L +50G /dev/nombre_vg/nombre_lv

# 4. Extender el sistema de archivos
resize2fs /dev/nombre_vg/nombre_lv

```

## Casos típicos en administración LVM

**1. Crear un nuevo volumen lógico desde cero**

```bash
# Ver espacio disponible
vgs

# Crear volumen de 50GB
lvcreate -L 50G -n lv_backup vg_datos

# Formatear
mkfs.ext4 /dev/vg_datos/lv_backup

# Montar
mkdir /backup
mount /dev/vg_datos/lv_backup /backup

# Hacerlo permanente (añadir a /etc/fstab)
echo "/dev/vg_datos/lv_backup /backup ext4 defaults 0 2" >> /etc/fstab

```

**2. Reducir un volumen (¡CUIDADO! Puede perder datos)**

```bash
# Primero desmontar
umount /dev/vg_datos/lv_old

# Verificar el sistema de archivos
e2fsck -f /dev/vg_datos/lv_old

# Reducir el sistema de archivos PRIMERO (siempre un poco menos)
resize2fs /dev/vg_datos/lv_old 40G

# Luego reducir el volumen lógico
lvreduce -L 40G /dev/vg_datos/lv_old

# Volver a montar
mount /dev/vg_datos/lv_old /mnt/old

```

**3. Mover datos entre discos físicos (migración)**

```bash
# Añadir disco nuevo al VG
pvcreate /dev/sdd
vgextend vg_datos /dev/sdd

# Mover datos del disco viejo al nuevo
pvmove /dev/sdb /dev/sdd

# Quitar el disco viejo del VG
vgreduce vg_datos /dev/sdb
pvremove /dev/sdb

```

**4. Crear snapshot (copia instantánea para backups)**

```bash
# Crear snapshot del volumen (necesita espacio libre en el VG)
lvcreate -L 10G -s -n snap_home /dev/vg_datos/lv_home

# Montar el snapshot para hacer backup
mkdir /mnt/snapshot
mount /dev/vg_datos/snap_home /mnt/snapshot

# Hacer backup tranquilamente
tar czf /backup/home.tar.gz /mnt/snapshot

# Eliminar snapshot cuando termines
umount /mnt/snapshot
lvremove /dev/vg_datos/snap_home

```

**5. Ver información detallada cuando algo falla**

```bash
# Ver TODO sobre un volumen específico
lvdisplay -m /dev/vg_datos/lv_home

# Ver en qué discos físicos está un volumen
lvs -o +devices /dev/vg_datos/lv_home

# Ver todos los PV y su uso
pvs -o +pv_used

```

**6. Renombrar volúmenes**

```bash
# Renombrar volumen lógico
lvrename vg_datos lv_old lv_antiguo

# Renombrar grupo de volúmenes
vgrename vg_old vg_nuevo

```

**7. Eliminar volúmenes (orden inverso a la creación)**

```bash
# 1. Desmontar
umount /mnt/datos

# 2. Eliminar volumen lógico
lvremove /dev/vg_datos/lv_temporal

# 3. Si quieres eliminar el VG completo
vgremove vg_datos

# 4. Eliminar volúmenes físicos
pvremove /dev/sdb

```

**8. Activar/desactivar volúmenes**

```bash
# Desactivar un volumen (para mantenimiento)
lvchange -an /dev/vg_datos/lv_home

# Reactivar
lvchange -ay /dev/vg_datos/lv_home

# Activar todos los VG (útil tras arranque o rescate)
vgchange -ay

```

Los casos más frecuentes que verás en el día a día son el **1** (crear nuevos volúmenes), el **extender** que ya vimos, y el **4** (snapshots para backups seguros). El **3** (migración) lo usarás cuando cambies discos.
