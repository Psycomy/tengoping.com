---
title: "Montar un NAS casero con OpenMediaVault"
description: "Guía para construir un NAS económico con OpenMediaVault: instalación, configuración de discos, carpetas compartidas y acceso remoto."
author: "antonio"
pubDate: 2025-07-28
category: "Hardware"
tags: ["NAS", "OpenMediaVault", "Hardware", "Almacenamiento"]
image: "../../assets/images/nas-omv.jpg"
draft: false
---

## Que es un NAS y por que montar uno propio

Un NAS (Network Attached Storage) es un dispositivo de almacenamiento conectado a tu red local que permite compartir archivos entre todos tus equipos. Las soluciones comerciales como Synology o QNAP funcionan bien, pero sus precios son elevados y dependes de su ecosistema propietario. Montar tu propio NAS con OpenMediaVault te da control total sobre el hardware y el software, a una fracción del coste.

## Hardware recomendado

No necesitas un equipo potente para un NAS. Estas son las opciones más comunes ordenadas de menor a mayor presupuesto:

| Opción | Pros | Contras | Presupuesto aprox. |
|---|---|---|---|
| Raspberry Pi 4/5 | Bajo consumo, barato | Limitado a USB para discos | 80-120 EUR |
| Portátil antiguo | Tiene batería como SAI integrado | Solo 1 bahía SATA interna | 0-50 EUR |
| Mini PC (Lenovo Tiny, HP EliteDesk) | Compacto, bajo consumo, bahía SATA | Normalmente 1 bahía | 80-150 EUR |
| PC dedicado con varias bahías | Múltiples discos, expansible | Mayor consumo, más ruido | 150-300 EUR |

Para un NAS doméstico serio, lo ideal es un equipo con al menos dos bahías para discos SATA de 3.5 pulgadas. Un viejo PC de sobremesa con una placa que tenga 4 puertos SATA es una opción excelente.

## Instalar OpenMediaVault

Descarga la ISO de OpenMediaVault desde su web oficial. Es un sistema basado en Debian, así que la instalación es familiar:

```bash
# Grabar la ISO en un USB desde Linux
sudo dd if=openmediavault-7.x-amd64.iso of=/dev/sdX bs=4M status=progress
sync
```

Arranca desde el USB e instala en el disco del sistema. No uses los discos de datos para la instalación del SO. El instalador es un asistente de Debian estándar: selecciona idioma, zona horaria, contraseña de root y el disco de destino.

Tras reiniciar, identifica la IP asignada:

```bash
ip addr show
```

Accede al panel web desde cualquier navegador en `http://IP_DEL_NAS`. Las credenciales por defecto son:

- **Usuario**: admin
- **Contraseña**: openmediavault

Cambia la contraseña inmediatamente desde **Sistema > Configuración general > Contraseña de administrador web**.

## Configurar los discos

### Preparar los discos de datos

Ve a **Almacenamiento > Discos** y comprueba que los discos aparecen correctamente. Limpia cada disco de datos si es necesario desde **Almacenamiento > Sistemas de archivos**:

```bash
# Desde terminal, si prefieres hacerlo manual
sudo wipefs -a /dev/sdb
sudo wipefs -a /dev/sdc
```

### Crear un array RAID con mdadm

Si tienes dos o más discos, configura RAID para proteger tus datos. Desde la interfaz web, ve a **Almacenamiento > Gestión de RAID**:

- **RAID 1 (mirror)**: duplica los datos en dos discos. Pierdes el 50% de capacidad pero aguanta la caída de un disco.
- **RAID 5**: requiere mínimo 3 discos. Pierde la capacidad de uno pero soporta un fallo.

Desde terminal, el proceso sería:

```bash
# Crear RAID 1 con dos discos
sudo mdadm --create /dev/md0 --level=1 --raid-devices=2 /dev/sdb /dev/sdc

# Verificar el estado del array
cat /proc/mdstat

# Guardar la configuración
sudo mdadm --detail --scan >> /etc/mdadm/mdadm.conf
```

### Crear el sistema de archivos

Formatea el array (o disco individual) con ext4 o btrfs:

```bash
sudo mkfs.ext4 /dev/md0
```

En la interfaz web, ve a **Almacenamiento > Sistemas de archivos**, crea uno nuevo sobre el dispositivo RAID y móntalo.

## Carpetas compartidas y permisos

### Crear usuarios

En **Gestión de acceso > Usuarios**, crea un usuario para cada persona que necesite acceso. Asigna cada usuario a un grupo si quieres gestionar permisos por grupo.

### Crear carpetas compartidas

Ve a **Almacenamiento > Carpetas compartidas** y crea las carpetas que necesites. Por ejemplo:

- `documentos` — archivos generales de la familia
- `backups` — copias de seguridad de los equipos
- `multimedia` — peliculas, musica, fotos

Asigna permisos específicos por usuario o grupo a cada carpeta.

### Habilitar SMB/CIFS

Para acceder desde Windows, macOS y Linux, activa SMB en **Servicios > SMB/CIFS**:

1. Activa el servicio
2. Ve a la pestaña **Recursos compartidos** y añade cada carpeta compartida
3. Configura si permites acceso de invitados o solo usuarios autenticados

Desde cualquier equipo Linux puedes montar el recurso:

```bash
# Montar un recurso compartido SMB
sudo mount -t cifs //IP_DEL_NAS/documentos /mnt/nas -o username=tu_usuario,uid=1000
```

### Habilitar NFS

Si todos tus equipos son Linux, NFS es más eficiente. Actívalo en **Servicios > NFS**:

```bash
# Montar un recurso NFS
sudo mount -t nfs IP_DEL_NAS:/srv/dev-disk-by-uuid-xxxx/documentos /mnt/nas
```

Para que se monte automáticamente al arrancar, añade la línea correspondiente a `/etc/fstab`.

## Copias de seguridad con rsync

OpenMediaVault incluye un plugin de rsync para programar copias de seguridad. Instálalo desde **Sistema > Plugins** buscando `openmediavault-rsnapshot` o usa rsync directamente:

```bash
# Copia de seguridad local entre discos
rsync -avh --delete /srv/datos/ /srv/backup/

# Copia remota desde otro servidor
rsync -avhz -e ssh usuario@servidor_remoto:/datos/ /srv/backup/remoto/
```

Programa las copias con un cron job o desde la interfaz web de OMV.

## Monitorización con SMART

Los discos duros fallan. SMART permite detectar problemas antes de que sea demasiado tarde. En **Almacenamiento > S.M.A.R.T.**, activa la monitorización y programa tests periódicos:

```bash
# Test rápido manual
sudo smartctl -t short /dev/sdb

# Ver el estado completo del disco
sudo smartctl -a /dev/sdb
```

Configura alertas por correo en **Sistema > Notificaciones** para recibir avisos cuando un disco muestre signos de fallo.

## Acceso remoto

Para acceder a tu NAS fuera de casa, las opciones más seguras son:

- **VPN**: monta un servidor WireGuard o OpenVPN en tu red y accede al NAS como si estuvieras en casa
- **Tailscale/ZeroTier**: VPN mesh sin necesidad de abrir puertos en el router
- **SSH tunnel**: reenvía el puerto del panel web a tu equipo local

```bash
# Tunel SSH para acceder al panel web de OMV remotamente
ssh -L 8080:localhost:80 usuario@IP_PUBLICA_DE_TU_RED
```

Nunca expongas el panel web de OMV directamente a internet sin protección adicional.

## Conclusion

OpenMediaVault convierte hardware económico o reciclado en un NAS competente. Con RAID, copias de seguridad automáticas y monitorización SMART, tus datos estarán protegidos sin depender de servicios en la nube ni pagar suscripciones. Empieza con lo que tengas, aunque sea un disco y un mini PC viejo, y amplía según tus necesidades.
