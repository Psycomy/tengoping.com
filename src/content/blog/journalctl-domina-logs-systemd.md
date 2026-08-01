---
title: 'journalctl: domina los logs de systemd'
description: 'Domina journalctl para filtrar logs de systemd por servicio, prioridad y fecha, seguirlos en tiempo real y controlar el espacio que ocupan.'
author: 'antonio'
pubDate: 2026-08-01
category: 'Linux'
tags: ['systemd', 'Linux', 'Sysadmin', 'Logs']
image: '../../assets/images/linux-journalctl.jpg'
draft: false
---

Si tu distro usa systemd, ya tienes journald recogiendo cada línea de log del sistema y de tus servicios en un único sitio. El problema no es la falta de información, sino encontrar la línea que importa entre miles de entradas. `journalctl` es el cliente que viene con systemd para leer, filtrar y gestionar ese journal — y la mayoría de sysadmins solo usan un puñado de sus flags, dejando en la mesa filtros que ahorran minutos de `grep` cada vez que algo falla.

Ya vimos cómo [systemd gestiona servicios](/blog/guia-systemd-servicios-linux/) con `systemctl`; `journalctl` es su complemento natural para depurar por qué un servicio no arrancó, cuándo empezó a fallar, o qué pasó exactamente en el último reinicio.

## Journal persistente vs volátil

Antes de filtrar nada, conviene saber dónde vive el journal, porque de eso depende si tus logs sobreviven a un reinicio.

`journald` soporta dos modos de almacenamiento (`Storage=` en `journald.conf`):

- **`persistent`** — los logs se guardan en disco, en `/var/log/journal/`. Sobreviven a reinicios.
- **`volatile`** — los logs solo viven en memoria, en `/run/log/journal/`. Se pierden al reiniciar.

El valor por defecto compilado en systemd es `persistent`, y así viene configurado en la mayoría de distros modernas (Ubuntu, Debian, Fedora, RHEL). Aun así, conviene comprobarlo en vez de asumirlo, porque algunas imágenes mínimas o contenedores lo dejan en `volatile` para no escribir en disco:

```bash
# Ver dónde está guardando el journal ahora mismo
journalctl --disk-usage
```

Si el comando no encuentra archivos en `/var/log/journal/`, está en modo volátil. Para forzar almacenamiento persistente:

```bash
sudo mkdir -p /var/log/journal
sudo systemd-tmpfiles --create --prefix /var/log/journal
sudo systemctl restart systemd-journald
```

## Filtrar por servicio con -u

El filtro que más vas a usar es `-u` (`--unit`), que limita la salida a una unidad de systemd concreta:

```bash
# Logs de un servicio
journalctl -u nginx

# Varios servicios a la vez
journalctl -u nginx -u php-fpm

# Logs de SSH, como vimos al configurar un servidor SSH seguro
journalctl -u sshd
```

Si ya sigues la [guía de SSH seguro](/blog/configurar-servidor-ssh-seguro-linux/), este es exactamente el comando que te permite ver qué IPs están intentando autenticarse y con qué resultado.

## Seguir logs en tiempo real con -f

Para depurar un problema mientras ocurre, combina `-u` con `-f` (`--follow`), el equivalente a `tail -f` pero para el journal:

```bash
# Sigue los logs de un servicio en vivo, Ctrl+C para salir
journalctl -u nginx -f
```

## Filtrar por fecha con --since y --until

`journalctl` entiende fechas en formato `AAAA-MM-DD HH:MM:SS` y también expresiones relativas como `today`, `yesterday`, `"1 hour ago"` o `"-30 min"`:

```bash
# Logs de la última hora
journalctl --since "-1 hour"

# Logs de un rango concreto
journalctl --since "2026-08-01 09:00:00" --until "2026-08-01 10:00:00"

# Todo lo de hoy
journalctl --since today
```

## Filtrar por prioridad con -p

Cada mensaje del journal lleva una prioridad heredada de syslog, de más a menos grave: `emerg`, `alert`, `crit`, `err`, `warning`, `notice`, `info`, `debug` (numéricamente 0-7). `-p` filtra por ese nivel o por un rango:

```bash
# Solo errores y niveles más graves
journalctl -p err

# Rango: de warning a emerg
journalctl -p warning..emerg
```

Esto es lo primero que deberías teclear cuando un servidor "va lento" sin motivo aparente y quieres descartar ruido antes de sospechar de algo concreto.

## Logs del arranque y del kernel

Dos filtros específicos que ahorran mucho tiempo al depurar hardware o arranques fallidos:

```bash
# Solo mensajes del kernel (equivalente a dmesg, pero persistente)
journalctl -k

# Logs del arranque actual
journalctl -b

# Logs del arranque anterior (útil tras un crash o kernel panic)
journalctl -b -1

# Lista todos los arranques disponibles en el journal
journalctl --list-boots
```

> [!TIP]
> `journalctl -b -1 -p err` es el primer comando que deberías ejecutar después de que un servidor se haya reiniciado solo — te enseña los últimos errores del arranque anterior, justo antes del crash.

## Formatos de salida y contexto extra

Por defecto `journalctl` muestra un formato legible (`short`), pero `-o` cambia el formato de salida para otros usos:

```bash
# Formato JSON, útil para parsear con jq o enviar a otra herramienta
journalctl -u nginx -o json

# Solo el mensaje, sin metadatos (para pegar en un script)
journalctl -u nginx -o cat

# Timestamp ISO 8601 completo, útil para correlacionar con otros logs
journalctl -u nginx -o short-iso
```

`-x` (`--catalog`) añade explicaciones extendidas del catálogo de mensajes de systemd cuando existen, y `-r` (`--reverse`) muestra las entradas más recientes primero:

```bash
journalctl -u nginx -x -r -n 20
```

`-n` limita el número de líneas (por defecto son 10 si no se especifica). Combinado con `-e` (`--pager-end`, que salta directamente al final del journal e implica `--lines=1000`), es la forma más rápida de ver "lo último que ha pasado" sin scroll.

## Controlar el espacio: --disk-usage y vacuum

El journal persistente crece indefinidamente si no se le pone límite, así que systemd aplica un tope por defecto: `SystemMaxUse` (el espacio máximo que puede ocupar el journal en disco) se calcula automáticamente como el 10% del tamaño del sistema de archivos, con un tope de 4 GiB — lo que sea menor de los dos.

```bash
# Cuánto espacio ocupa el journal ahora mismo
journalctl --disk-usage
```

Cuando necesitas liberar espacio de forma manual o ajustar la retención puntualmente, usa las opciones `--vacuum-*`:

```bash
# Elimina archivos de journal archivados más antiguos de 7 días
journalctl --vacuum-time=7d

# Reduce el journal archivado a un tamaño máximo de 500MB
journalctl --vacuum-size=500M

# Deja como máximo 10 archivos de journal archivados
journalctl --vacuum-files=10
```

> [!IMPORTANT]
> `--vacuum-time`, `--vacuum-size` y `--vacuum-files` **borran archivos de journal de forma permanente e irreversible**. Solo actúan sobre archivos archivados (no sobre el archivo activo actual), pero una vez borrados no hay forma de recuperarlos. Si necesitas conservar logs históricos por auditoría o cumplimiento normativo, expórtalos antes con `journalctl -o export > backup.journal`.

Para hacer el límite permanente en vez de puntual, edita `/etc/systemd/journald.conf`:

```ini
[Journal]
SystemMaxUse=500M
SystemKeepFree=1G
```

Y reinicia el servicio para aplicar el cambio:

```bash
sudo systemctl restart systemd-journald
```

## Aplicación práctica: depurar un baneo de Fail2Ban

Un caso real donde todo esto encaja: si sigues la guía para [configurar Fail2Ban](/blog/configurar-fail2ban-proteger-servicios/), ya sabes que revisar los logs periódicamente es parte del mantenimiento — pero no siempre queda claro cómo hacerlo. Con `journalctl` es directo:

```bash
# Ver toda la actividad de Fail2Ban
journalctl -u fail2ban

# Solo los baneos, en tiempo real
journalctl -u fail2ban -f | grep -i ban

# Baneos de las últimas 24 horas, sin metadatos de más
journalctl -u fail2ban --since "-24 hours" -o cat | grep -i ban
```

Este mismo patrón — `-u <servicio>` combinado con `--since` y `-p` — es el que vas a reutilizar para depurar prácticamente cualquier servicio del sistema, no solo Fail2Ban.

## Siguiente paso

`journalctl` reemplaza a `grep` sobre archivos de texto dispersos en `/var/log/` por un único punto de consulta estructurado, con filtros que cubren el 90% de los casos de depuración diarios. La curva de aprendizaje es corta: con `-u`, `-p`, `--since` y `-f` ya cubres la mayoría de situaciones; el resto de flags están ahí para cuando los necesites.

Si administras varios servidores, el siguiente paso natural es centralizar estos logs en un sistema como Prometheus/Grafana o Zabbix en vez de conectarte por SSH a cada máquina para lanzar `journalctl` — pero para depuración local en un único servidor, no vas a necesitar nada más que esto.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
