---
title: 'Configurar Fail2Ban para proteger servicios'
description: 'Guía práctica para instalar y configurar Fail2Ban: protege SSH, Nginx y otros servicios contra ataques de fuerza bruta.'
author: 'antonio'
pubDate: 2026-01-28
category: 'Seguridad'
tags: ['Fail2Ban', 'Seguridad', 'SSH', 'Linux']
image: '../../assets/images/fail2ban.jpg'
draft: false
---

## Qué es Fail2Ban y por qué lo necesitas

Fail2Ban es un daemon que monitoriza los logs del sistema en busca de patrones de autenticación fallida. Cuando detecta un número determinado de intentos fallidos desde una misma IP, la banea automáticamente durante un tiempo configurable. Es la primera línea de defensa contra ataques de fuerza bruta en cualquier servidor expuesto a Internet.

Sin Fail2Ban, un [servidor SSH](/blog/configurar-servidor-ssh-seguro-linux/) público puede recibir miles de intentos de login por hora. Fail2Ban reduce ese ruido a prácticamente cero con una configuración mínima.

## Instalación

En distribuciones basadas en RHEL y en Debian/Ubuntu:

```bash
# RHEL/Rocky/Oracle Linux
sudo dnf install epel-release -y
sudo dnf install fail2ban -y

# Ubuntu/Debian
sudo apt update
sudo apt install fail2ban -y
```

Activa el servicio para que arranque con el sistema:

```bash
sudo systemctl enable --now fail2ban
```

## jail.conf vs jail.local

Fail2Ban lee su configuración desde `/etc/fail2ban/jail.conf`, pero este archivo se sobreescribe con las actualizaciones del paquete. La práctica correcta es crear un archivo `/etc/fail2ban/jail.local` que contenga solo tus personalizaciones. Los valores definidos en `jail.local` tienen prioridad sobre `jail.conf`.

```bash
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
```

Aunque puedes copiar el archivo completo, lo recomendable es mantener en `jail.local` únicamente las secciones que modificas para facilitar el mantenimiento.

## Configurar la jail de SSH

Edita `/etc/fail2ban/jail.local` y ajusta la sección `[sshd]`:

```ini
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 3
banaction = nftables-multiport

[sshd]
enabled  = true
port     = ssh
logpath  = %(sshd_log)s
backend  = systemd
maxretry = 3
```

Con esta configuración, tres intentos fallidos en 10 minutos (findtime) provocan un baneo de una hora (bantime). El `backend = systemd` permite que Fail2Ban lea directamente del journal en lugar de un archivo de log.

```
Fail2Ban vigila el journal de sshd (backend = systemd)
   │
   ▼
1. Se registra un intento de login SSH fallido
   │
   ▼
2. ¿Van 3 intentos (maxretry) en los últimos 600s (findtime)?
   │
   ├── No  → sigue vigilando
   └── Sí  → banaction = nftables-multiport bloquea la IP
   │
   ▼
3. Pasados 3600s (bantime), el baneo se levanta automáticamente
```

Reinicia el servicio para aplicar los cambios:

```bash
sudo systemctl restart fail2ban
```

## Filtros personalizados para Nginx

Fail2Ban incluye filtros predefinidos para muchos servicios, pero puedes crear los tuyos. Por ejemplo, un filtro para bloquear IPs que devuelvan demasiados errores 401 en Nginx.

Crea el archivo `/etc/fail2ban/filter.d/nginx-auth.conf`:

```ini
[Definition]
failregex = ^<HOST> -.*"(GET|POST).*" 401
ignoreregex =
```

Ahora añade la jail correspondiente en `/etc/fail2ban/jail.local`:

```ini
[nginx-auth]
enabled  = true
port     = http,https
filter   = nginx-auth
logpath  = /var/log/nginx/access.log
maxretry = 5
bantime  = 1800
```

Con esto, cinco respuestas 401 desde la misma IP en el período de `findtime` activarán un baneo de 30 minutos.

## Acciones de baneo: iptables vs nftables

Fail2Ban soporta varias acciones de baneo. Las más comunes son `iptables-multiport` y `nftables-multiport`. Si tu distribución utiliza nftables por defecto (RHEL 9, Debian 12, Ubuntu 22.04+), configura la acción global en `[DEFAULT]`:

```ini
[DEFAULT]
banaction = nftables-multiport
banaction_allports = nftables-allports
```

Si todavía dependes de iptables:

```ini
[DEFAULT]
banaction = iptables-multiport
banaction_allports = iptables-allports
```

Puedes verificar qué sistema de filtrado usa tu servidor con:

```bash
# Comprobar si nftables está activo
sudo nft list ruleset

# Comprobar si iptables está activo
sudo iptables -L -n
```

## Comprobar el estado con fail2ban-client

El comando `fail2ban-client` es la herramienta principal para interactuar con el servicio en ejecucion.

```bash
# Estado general: lista de jails activas
sudo fail2ban-client status

# Estado detallado de una jail concreta
sudo fail2ban-client status sshd
```

La salida del estado de una jail muestra los intentos fallidos detectados, las IPs actualmente baneadas y el total histórico de baneos:

```text
Status for the jail: sshd
|- Filter
|  |- Currently failed: 2
|  |- Total failed:     847
|  `- Journal matches:  _SYSTEMD_UNIT=sshd.service + _COMM=sshd
`- Actions
   |- Currently banned: 3
   |- Total banned:     156
   `- Banned IP list:   203.0.113.10 198.51.100.22 192.0.2.45
```

## Desbanear IPs

Si bloqueas una IP por error (por ejemplo, la tuya propia tras varios intentos con una clave incorrecta), puedes desbanearla manualmente:

```bash
# Desbanear una IP de una jail concreta
sudo fail2ban-client set sshd unbanip 203.0.113.10
```

> [!IMPORTANT]
> Para evitar banearte a ti mismo, añade tu IP a la lista blanca en la sección `[DEFAULT]` de `jail.local` antes de que ocurra:
>
> ```
> ignoreip = 127.0.0.1/8 ::1 10.0.0.0/8 192.168.1.0/24
> ```

## Recomendaciones finales

Algunos ajustes adicionales que conviene tener en cuenta:

- Activa el **baneo incremental** con `bantime.increment = true` para que las IPs reincidentes reciban baneos cada vez más largos.
- Configura notificaciones por correo con la acción `sendmail-whois` para recibir alertas de cada baneo.
- Revisa periódicamente los logs de Fail2Ban en `/var/log/fail2ban.log` para detectar patrones y ajustar las reglas.
- Combina Fail2Ban con otras medidas: claves SSH, [firewall con listas de permitidos](/blog/firewalld-nftables-seguridad-red-linux/), port knocking o [VPN](/blog/wireguard-vpn-autoalojada/).

Fail2Ban no sustituye una configuración de seguridad sólida, pero es un complemento imprescindible para cualquier servidor Linux expuesto a la red.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
