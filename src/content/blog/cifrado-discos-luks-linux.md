---
title: "Cifrado de discos con LUKS en Linux"
description: "Aprende a cifrar particiones y discos completos con LUKS para proteger tus datos en caso de pérdida o robo del equipo."
author: "alois"
pubDate: 2025-06-30
category: "Seguridad"
tags: ["LUKS", "Cifrado", "Seguridad", "Linux"]
image: "../../assets/images/luks-cifrado.jpg"
draft: false
---

## Por que cifrar tus discos

Si un servidor o portatil cae en manos equivocadas, cualquiera puede montar el disco desde otro sistema y acceder a todos los archivos, sin necesidad de conocer contrasenas de usuario. El cifrado de disco resuelve este problema: sin la clave de descifrado, los datos son ilegibles.

LUKS (Linux Unified Key Setup) es el estandar de cifrado de disco en Linux. Utiliza dm-crypt en el kernel y proporciona una capa de gestion de claves robusta, permitiendo multiples passphrase para un mismo volumen.

## Requisitos previos

Necesitas el paquete `cryptsetup`, que suele estar instalado por defecto. Si no lo esta:

```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install cryptsetup -y

# Debian / Ubuntu
sudo apt install cryptsetup -y
```

Los ejemplos usan `/dev/sdb1` como particion de destino. Sustituye esta ruta por tu dispositivo real. Todos los datos de la particion se perderan al formatearla con LUKS.

## Crear un volumen LUKS

Primero, formatea la particion con LUKS. El comando pedira confirmacion y una passphrase:

```bash
sudo cryptsetup luksFormat /dev/sdb1
```

Puedes especificar el algoritmo de cifrado si necesitas algo distinto al predeterminado (aes-xts-plain64):

```bash
sudo cryptsetup luksFormat --cipher aes-xts-plain64 --key-size 512 --hash sha512 /dev/sdb1
```

Verifica que la cabecera LUKS se ha creado correctamente:

```bash
sudo cryptsetup luksDump /dev/sdb1
```

## Abrir y cerrar volumenes cifrados

Para acceder al contenido, primero debes abrir (desbloquear) el volumen. Esto crea un dispositivo mapeado en `/dev/mapper/`:

```bash
# Abrir el volumen con el nombre "datos"
sudo cryptsetup luksOpen /dev/sdb1 datos
```

Ahora tienes un dispositivo `/dev/mapper/datos` que puedes formatear y montar como cualquier particion normal:

```bash
# Crear sistema de archivos (solo la primera vez)
sudo mkfs.ext4 /dev/mapper/datos

# Montar
sudo mkdir -p /mnt/datos
sudo mount /dev/mapper/datos /mnt/datos
```

Para cerrar el volumen cuando termines:

```bash
sudo umount /mnt/datos
sudo cryptsetup luksClose datos
```

## Montaje automatico con crypttab y fstab

Si necesitas que el volumen se monte automaticamente en cada arranque, configura `/etc/crypttab` y `/etc/fstab`.

Primero, obtiene el UUID de la particion LUKS:

```bash
sudo blkid /dev/sdb1
```

Edita `/etc/crypttab` y anade una linea con el UUID:

```text
datos UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx none luks
```

El valor `none` indica que el sistema pedira la passphrase durante el arranque. Si prefieres usar un archivo de clave (ver siguiente seccion), sustituye `none` por la ruta al archivo.

Anade la entrada en `/etc/fstab`:

```text
/dev/mapper/datos /mnt/datos ext4 defaults 0 2
```

Prueba que la configuracion funciona sin reiniciar:

```bash
sudo cryptdisks_start datos
sudo mount -a
```

## Gestion de claves

LUKS permite hasta 8 slots de clave. Puedes anadir passphrase adicionales o archivos de clave sin eliminar los existentes.

### Anadir una nueva passphrase

```bash
sudo cryptsetup luksAddKey /dev/sdb1
```

El comando pedira primero una passphrase existente para autorizar la operacion y luego la nueva passphrase.

### Usar un archivo de clave

Un archivo de clave permite desbloquear el volumen sin introducir passphrase manualmente, util para montaje automatico en servidores:

```bash
# Generar un archivo de clave aleatorio
sudo dd if=/dev/urandom of=/root/luks-key bs=4096 count=1
sudo chmod 400 /root/luks-key

# Anadir el archivo como clave del volumen
sudo cryptsetup luksAddKey /dev/sdb1 /root/luks-key
```

Actualiza `/etc/crypttab` para usar el archivo:

```text
datos UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx /root/luks-key luks
```

### Eliminar una clave

```bash
# Eliminar una passphrase (pedira la que quieres borrar)
sudo cryptsetup luksRemoveKey /dev/sdb1

# Eliminar un slot concreto por numero
sudo cryptsetup luksKillSlot /dev/sdb1 1
```

Nunca elimines todas las claves o perderas acceso permanente al volumen.

## Cifrar unidades USB

El proceso para cifrar un USB es identico. Identifica el dispositivo con `lsblk`, formatea con LUKS, abre, crea el sistema de archivos y monta:

```bash
# Identificar el USB (por ejemplo /dev/sdc1)
lsblk

# Cifrar
sudo cryptsetup luksFormat /dev/sdc1
sudo cryptsetup luksOpen /dev/sdc1 usb_cifrado
sudo mkfs.ext4 /dev/mapper/usb_cifrado

# Montar
sudo mkdir -p /mnt/usb
sudo mount /dev/mapper/usb_cifrado /mnt/usb
```

La mayoria de entornos de escritorio Linux (GNOME, KDE) detectan automaticamente los volumenes LUKS en USB y muestran un dialogo para introducir la passphrase al conectar el dispositivo.

## Consideraciones finales

- Haz **backup de la cabecera LUKS** con `cryptsetup luksHeaderBackup`. Si la cabecera se corrompe, los datos son irrecuperables.
- El cifrado tiene un impacto minimo en el rendimiento gracias a las instrucciones AES-NI presentes en procesadores modernos.
- Combina el cifrado de disco con permisos adecuados del sistema de archivos. LUKS protege los datos en reposo, no mientras el volumen esta desbloqueado.
- Para servidores remotos sin acceso a consola durante el arranque, considera usar `clevis` y `tang` para desbloqueo automatico por red (Network Bound Disk Encryption).
