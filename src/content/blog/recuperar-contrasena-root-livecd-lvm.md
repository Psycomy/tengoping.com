---
title: 'Recuperar contraseña root con livecd y LVM'
description: '¿Olvidaste la contraseña de root en tu sistema Linux con LVM? Este artículo te guía paso a paso para recuperarla usando un live CD: monta los volúmenes lógicos, haz chroot y cambia la contraseña de forma rápida y segura.'
author: 'antonio'
pubDate: 2026-03-03
category: 'Linux'
tags: ['rescate', 'linux', 'LVM']
image: '../../assets/images/recuperar-contrasena-root-livecd-lvm.jpg'
draft: false
---

Para recuperar la contraseña root en un sistema con LVM, necesitas algunos pasos adicionales. Te explico el proceso completo:

## Pasos desde el LiveCD

**1. Identificar los volúmenes LVM**

Primero, activa los volúmenes lógicos:

```bash
sudo vgscan
sudo vgchange -ay
```

Esto escaneará y activará todos los grupos de volúmenes.

**2. Listar los volúmenes disponibles**

```bash
sudo lvdisplay
```

Busca el volumen que contiene el sistema raíz, normalmente algo como `/dev/nombre_vg/root` o `/dev/nombre_vg/lv_root`.

**3. Montar el volumen**

```bash
sudo mkdir /mnt/recuperacion
sudo mount /dev/nombre_vg/root /mnt/recuperacion
```

Si la partición `/boot` está fuera del LVM (es común), también debes montarla:

```bash
sudo mount /dev/sdaX /mnt/recuperacion/boot
```

(Reemplaza `sdaX` con la partición boot correcta, puedes verla con `lsblk`)

**4. Hacer chroot al sistema**

```bash
sudo mount --bind /dev /mnt/recuperacion/dev
sudo mount --bind /proc /mnt/recuperacion/proc
sudo mount --bind /sys /mnt/recuperacion/sys
sudo chroot /mnt/recuperacion
```

**5. Cambiar la contraseña**

Ahora ya estás "dentro" del sistema:

```bash
passwd root
```

Introduce la nueva contraseña dos veces.

**6. Salir y reiniciar**

```bash
exit
sudo umount /mnt/recuperacion/dev
sudo umount /mnt/recuperacion/proc
sudo umount /mnt/recuperacion/sys
sudo umount /mnt/recuperacion/boot  # si la montaste
sudo umount /mnt/recuperacion
sudo reboot
```
