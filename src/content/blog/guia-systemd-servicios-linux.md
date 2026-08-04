---
title: 'Guía práctica de systemd en Linux'
description: 'Guía práctica de systemd: unidades service, timer y socket, targets de arranque, enable vs start, mask/unmask y overrides con systemctl edit.'
author: 'alois'
pubDate: 2026-01-11
category: 'Linux'
tags: ['systemd', 'Linux', 'Servicios', 'Sysadmin']
image: '../../assets/images/linux-systemd.jpg'
draft: false
---

## ¿Qué es systemd?

systemd es el sistema de inicio y gestor de servicios estándar en la mayoría de distribuciones Linux modernas. Controla el arranque del sistema y la gestión de daemons.

## Tipos de unidad

systemd no gestiona solo servicios: una unidad es cualquier recurso que sabe arrancar, parar y supervisar, y el tipo se indica por la extensión del archivo. Los más habituales:

- **`.service`** — un proceso o daemon (el tipo que ya usas con nginx, Gitea, etc.)
- **`.timer`** — dispara otra unidad en un horario, como alternativa a cron
- **`.socket`** — activa un servicio bajo demanda cuando llega tráfico a un puerto o socket Unix, en vez de mantenerlo siempre corriendo
- **`.mount`** — monta un sistema de archivos, generado automáticamente a partir de `/etc/fstab` o definido a mano

Un ejemplo mínimo de unidad `.socket` con activación bajo demanda:

```ini
# /etc/systemd/system/mi-app.socket
[Unit]
Description=Socket de mi-app

[Socket]
ListenStream=127.0.0.1:8080

[Install]
WantedBy=sockets.target
```

Con `Accept=no` (el valor por defecto), systemd arranca `mi-app.service` en cuanto llega la primera conexión al puerto 8080, y ese servicio es responsable de atenderlas todas — no hace falta que esté corriendo de antemano.

Un `.mount` sigue una convención de nombres estricta: la ruta de montaje se traduce reemplazando cada `/` por un `-`. Para montar algo en `/mnt/datos`, la unidad se llama `mnt-datos.mount`:

```ini
# /etc/systemd/system/mnt-datos.mount
[Unit]
Description=Montaje de /mnt/datos

[Mount]
What=/dev/sdb1
Where=/mnt/datos
Type=ext4

[Install]
WantedBy=multi-user.target
```

## Comandos esenciales

### Estado de servicios

```bash
systemctl status nginx
systemctl is-active nginx
systemctl is-enabled nginx
```

### Iniciar, parar y reiniciar

```bash
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx
```

### Habilitar y deshabilitar

`start`/`stop` y `enable`/`disable` actúan sobre dos ejes distintos, y confundirlos es uno de los errores más comunes con systemd:

- **`start`/`stop`** controlan si el servicio está corriendo **ahora mismo**
- **`enable`/`disable`** controlan si el servicio **arrancará en el próximo reinicio** (creando o quitando un symlink hacia la unidad)

Por eso un servicio puede estar activo pero no habilitado (corre ahora, pero no sobrevivirá a un reinicio), o habilitado pero parado (arrancará en el próximo boot, pero ahora mismo no está corriendo):

```bash
sudo systemctl enable nginx
sudo systemctl disable nginx
sudo systemctl enable --now nginx
```

> [!TIP]
> `enable --now` combina ambos: habilita el servicio para el arranque y lo inicia de inmediato, evitando el paso de `start` por separado.

### Enmascarar servicios: mask y unmask

`disable` quita el arranque automático, pero el servicio sigue pudiendo arrancarse a mano o como dependencia de otra unidad. `mask` va más allá: enlaza el unit file a `/dev/null`, por lo que **nada** puede arrancarlo — ni tú manualmente, ni otro servicio que dependa de él — hasta que lo desenmascares:

```bash
sudo systemctl mask servicio-a-bloquear
sudo systemctl unmask servicio-a-bloquear
```

> [!CAUTION]
> Si enmascaras un servicio del que otra unidad depende (`Requires=`), esa otra unidad fallará al arrancar en vez de arrancar sin él. Antes de enmascarar, comprueba con `systemctl list-dependencies --reverse servicio-a-bloquear` qué más lo necesita.

## Crear un servicio personalizado

Este es el mismo patrón de unidad que usamos para levantar [Gitea como servicio](/blog/gitea-servidor-git-autoalojado/):

```ini
# /etc/systemd/system/mi-app.service
[Unit]
Description=Mi aplicación web
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/mi-app
ExecStart=/opt/mi-app/bin/start.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mi-app
```

## Modificar un servicio sin tocar el unit original

Editar directamente un unit file que viene de un paquete (por ejemplo `/lib/systemd/system/nginx.service`) es frágil: la próxima actualización del paquete puede sobrescribirlo y perder tus cambios. `systemctl edit` resuelve esto creando un **drop-in file** en `/etc/systemd/system/<unidad>.d/override.conf` que añade o sustituye solo las directivas que indiques, sin tocar el original:

```bash
sudo systemctl edit nginx
```

Esto abre un editor con una plantilla vacía; basta con escribir las directivas que quieres cambiar, por ejemplo para aumentar el número de reintentos:

```ini
[Service]
Restart=on-failure
RestartSec=10
```

Al guardar, systemd recarga la configuración automáticamente. Si en algún momento quieres editar el unit file completo en vez de un override parcial, `systemctl edit --full nginx` abre una copia editable del archivo original.

## Timers como alternativa a cron

Aquí el ejemplo mínimo; para una comparativa completa entre cron y systemd timers, con sus ventajas y desventajas, consulta la guía de [tareas programadas](/blog/tareas-programadas-cron-systemd-timers/):

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Backup diario

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

## Targets: el arranque por fases

Un target agrupa unidades que deben estar activas para alcanzar un determinado estado del sistema — es el equivalente moderno a los runlevels de SysV, pero más flexible: un target puede depender de otros y puedes crear los tuyos propios. Los más comunes:

- **`multi-user.target`** — sistema completo en modo texto, sin entorno gráfico (equivalente al runlevel 3)
- **`graphical.target`** — multi-usuario con entorno gráfico (equivalente al runlevel 5)

Para consultar y cambiar cuál se usa por defecto en el arranque:

```bash
systemctl get-default
sudo systemctl set-default multi-user.target
```

`set-default` solo cambia qué target se usará en el **próximo** arranque — no afecta al sistema en ejecución ahora mismo. Para cambiar el estado activo sin reiniciar, usa `systemctl isolate <target>`, que detiene lo que no pertenezca al target destino:

```bash
sudo systemctl isolate multi-user.target
```

> [!NOTE]
> Las distribuciones actuales mantienen symlinks de compatibilidad (`runlevel3.target` → `multi-user.target`, etc.), así que los números de runlevel de toda la vida siguen funcionando como alias si los necesitas por costumbre o en scripts antiguos.

## Conclusión

systemd ofrece un control granular sobre los servicios del sistema: unidades más allá de `.service`, targets que agrupan el estado de arranque, y overrides que sobreviven a las actualizaciones de paquete. Para revisar los logs de todo lo que gestionas aquí, la guía de [journalctl](/blog/journalctl-domina-logs-systemd/) es el siguiente paso natural.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
