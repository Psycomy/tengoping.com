---
title: 'RAID por software con mdadm: guía práctica'
description: 'Crea arrays RAID 0, 1, 5 y 10 con mdadm en Linux, monitoriza su estado con alertas por email y recupera un array tras el fallo de un disco.'
author: 'antonio'
pubDate: 2026-07-27
updatedDate: 2026-07-27
category: 'Hardware'
tags: ['RAID', 'mdadm', 'Storage', 'Linux']
image: '../../assets/images/hard-raid-mdadm.jpg'
draft: false
---

mdadm es la herramienta estándar en Linux para crear y gestionar arrays RAID por software, sin depender de una controladora RAID hardware dedicada. Ya vimos un uso puntual en el post de [OpenMediaVault](/blog/nas-casero-openmediavault/) para levantar un RAID 1 rápido en un NAS; aquí profundizamos en los distintos niveles disponibles, cómo vigilar la salud de un array activamente y, sobre todo, qué hacer cuando un disco falla de verdad — que es el motivo real por el que montas RAID.

## Niveles RAID: cuál elegir

mdadm soporta varios niveles, cada uno con un compromiso distinto entre capacidad, rendimiento y tolerancia a fallos:

- **RAID 0 (stripe)**: reparte los datos entre discos sin redundancia. Mínimo 2 discos. Máximo rendimiento y capacidad total (100% del espacio combinado), pero **si falla un disco, pierdes todos los datos del array**. mdadm no soporta hot-spare ni resincronización en RAID 0, precisamente porque no hay nada que reconstruir. Solo tiene sentido para datos desechables o combinado con backups aparte.
- **RAID 1 (mirror)**: duplica los datos en todos los discos del array. Mínimo 2 discos. Tolera el fallo de todos los discos menos uno. Capacidad útil = la del disco más pequeño, independientemente de cuántos discos añadas.
- **RAID 5**: distribuye datos y paridad entre discos. Mínimo 3 discos. Con n discos, la capacidad útil es la de (n-1) discos — un disco se "pierde" en paridad, pero esa paridad está repartida entre todos, no en uno solo. Tolera el fallo de un disco.
- **RAID 10 (1+0)**: combina mirroring y striping — en la práctica, un RAID 0 hecho de varios pares RAID 1. El RAID 1+0 anidado clásico requiere un número par de discos, mínimo 4 en la configuración típica (aunque técnicamente funciona con 2, en cuyo caso equivale a RAID 1). El RAID10 nativo de mdadm (`--level=10`), en cambio, admite número impar de discos (por ejemplo 3 o 5) gracias a sus layouts near/far/offset. Mejor rendimiento que RAID 5 en escrituras y reconstrucción más rápida tras un fallo, a costa de perder la mitad de la capacidad total.

Para un homelab con presupuesto limitado, RAID 1 es la opción más simple y predecible. Si tienes 4+ discos y priorizas rendimiento sobre capacidad máxima, RAID 10 reconstruye más rápido que RAID 5 tras sustituir un disco, lo que reduce la ventana de exposición a un segundo fallo.

## Crear un array

Identifica primero los discos disponibles (sin particionar, o con una partición dedicada tipo `fd` / Linux RAID):

```bash
lsblk
```

Crear un RAID 5 con tres discos:

```bash
sudo mdadm --create /dev/md0 --level=5 --raid-devices=3 /dev/sdb /dev/sdc /dev/sdd
```

Comprueba el progreso de la sincronización inicial (en RAID 5 y 10 tarda; en RAID 0 no aplica al no haber redundancia que construir):

```bash
cat /proc/mdstat
```

Guarda la configuración para que el array se reensamble automáticamente en el próximo arranque:

```bash
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf
sudo update-initramfs -u
```

Formatea y monta el array como harías con cualquier disco:

```bash
sudo mkfs.ext4 /dev/md0
sudo mount /dev/md0 /mnt/datos
```

## Leer el estado del array

`/proc/mdstat` es la fuente de verdad más rápida sobre el estado de tus arrays:

```
Personalities : [raid1] [raid5]
md0 : active raid5 sdd[3] sdc[2] sdb[1] sda[0]
      5860147200 blocks super 1.2 level 5, 512k chunk, algorithm 2 [4/4] [UUUU]
```

La parte entre corchetes al final (`[UUUU]`) es lo que hay que vigilar: cada `U` representa un disco activo y sano. Un guion bajo en su lugar (`[UUU_]` o `[_UUU]`) indica un disco caído o ausente, y su posición te dice cuál. El primer par de corchetes (`[4/4]`) muestra discos activos frente a discos esperados en el array.

Para un detalle completo de un array concreto, incluyendo qué disco específico ha fallado:

```bash
sudo mdadm --detail /dev/md0
```

## Monitorización activa con alertas por email

Revisar `/proc/mdstat` a mano no escala. mdadm incluye un demonio de monitorización que vigila los arrays en segundo plano y envía un email cuando detecta un evento (disco caído, array degradado, resincronización terminada).

Añade tu dirección en `/etc/mdadm/mdadm.conf` (Debian/Ubuntu) o `/etc/mdadm.conf` (RHEL/Fedora):

```
MAILADDR tu-email@dominio.com
```

En distribuciones con systemd, el monitor se gestiona como servicio (`mdmonitor` en RHEL/Fedora; en Debian/Ubuntu el paquete `mdadm` ya arranca `mdadm --monitor` vía su propio servicio):

```bash
sudo systemctl enable --now mdmonitor
```

Este comando de habilitar y arrancar el servicio manualmente aplica a **RHEL/Fedora**. En **Debian/Ubuntu** no hace falta (ni existe como tal): el servicio `mdmonitor` se activa normalmente mediante udev al detectar arrays mdadm, no con `systemctl enable --now`.

Para comprobar que el envío de correo funciona sin esperar a un fallo real:

```bash
sudo mdadm --monitor --test --oneshot /dev/md0
```

Ten en cuenta que necesitas un MTA local (Postfix, msmtp) configurado para que el email realmente salga — mdadm solo genera el mensaje, no gestiona el envío.

## Recuperar un array tras el fallo de un disco

Este es el procedimiento que justifica todo lo anterior. Cuando `/proc/mdstat` o una alerta te avisan de un disco caído:

1. **Confirma qué disco ha fallado** con `mdadm --detail /dev/md0` — buscarás el estado `faulty` junto al dispositivo.

2. **Márcalo como fallido explícitamente** (si mdadm no lo ha hecho ya automáticamente) y sácalo del array:

```bash
sudo mdadm --manage /dev/md0 --fail /dev/sdc
sudo mdadm --manage /dev/md0 --remove /dev/sdc
```

3. **Sustituye el disco físicamente.** En bahías hot-swap puedes extraer el disco fallido e insertar el nuevo sin apagar el servidor; el kernel debería detectarlo automáticamente.

4. **Verifica que el disco nuevo está sano** antes de añadirlo — de nada sirve reconstruir sobre un disco defectuoso:

```bash
sudo smartctl -H /dev/sdc
```

5. **Añádelo al array** para iniciar la reconstrucción:

```bash
sudo mdadm --manage /dev/md0 --add /dev/sdc
```

El disco de reemplazo debe tener al menos el mismo tamaño que el original, o mdadm rechazará añadirlo. mdadm reconstruye automáticamente los datos en el disco nuevo; sigue el progreso con `cat /proc/mdstat`, que mostrará un porcentaje de recuperación hasta volver a un estado `[UUUU]` limpio.

> [!WARNING]
> Mientras el array está degradado (con un disco menos de los esperados), no tienes redundancia real: un segundo fallo durante ese periodo puede significar pérdida total de datos, especialmente en RAID 5. Cuanto antes sustituyas el disco caído, menor es la ventana de riesgo — por eso las alertas por email de la sección anterior importan más que la creación del array en sí.

## Siguiente paso

Con esto tienes lo necesario para elegir el nivel RAID adecuado a tu caso, crear el array, vigilar su salud de forma proactiva en lugar de reactiva, y actuar con un procedimiento claro cuando un disco falle de verdad. RAID no sustituye a las copias de seguridad — protege contra el fallo de un disco, no contra un borrado accidental o un ransomware — así que combínalo con la estrategia de [backups incrementales con rsync](/blog/backup-incremental-rsync-servidores-linux/) que ya vimos en este blog.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
