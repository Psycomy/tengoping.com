---
title: '10 scripts Bash útiles para sysadmins'
description: 'Colección de scripts Bash prácticos para monitorización, backups, limpieza de logs y tareas comunes de administración de sistemas.'
author: 'alois'
pubDate: 2026-01-14
updatedDate: 2026-08-06
category: 'Automatización'
tags: ['Bash', 'Scripts', 'Sysadmin', 'Automatización']
image: '../../assets/images/auto-bash.jpg'
draft: false
---

## Introducción

Los scripts Bash son la navaja suiza del sysadmin: no sustituyen a una herramienta de gestión de configuración como Ansible cuando administras decenas de servidores, pero para una tarea puntual en una máquina concreta —o como pegamento entre comandos que ya conoces— siguen siendo la vía más rápida. Aquí tienes diez scripts prácticos, con el porqué de cada uno y los matices que no se ven a simple vista en el código.

Todos estos scripts asumen que ya tienes permisos de `sudo` configurados donde haga falta y que los ejecutas en un shell Bash (no `sh` ni `dash`, que no soportan arrays ni algunas expansiones usadas aquí).

## 1. Monitor de disco

Comprobar el uso de disco por cron es la forma más barata de evitar el clásico "el servidor se quedó sin espacio y nadie se enteró hasta que falló el backup". El umbral del 80% no es arbitrario: por debajo de ese margen casi cualquier filesystem tiene hueco de sobra para picos puntuales (logs verbosos, un `apt upgrade` con paquetes en caché); por encima, la mayoría de aplicaciones empiezan a fallar de forma menos predecible mucho antes de llegar al 100%.

```bash
#!/bin/bash
THRESHOLD=80
df -h --output=pcent,target | tail -n+2 | while read usage mount; do
  pct=${usage%\%}
  if [ "$pct" -ge "$THRESHOLD" ]; then
    echo "ALERTA: $mount está al $usage"
  fi
done
```

> [!NOTE]
> Este script solo mira espacio en bloques. Un filesystem puede quedarse sin _inodos_ (y devolver "No space left on device") con `df -h` mostrando hueco libre de sobra, típico cuando algo genera muchísimos archivos pequeños (colas de correo, cachés de paquetes). Añade `df -i` con el mismo umbral si administras servicios que crean muchos ficheros.

## 2. Backup con rotación

Este script es intencionadamente simple: una copia completa comprimida cada vez, sin deduplicación ni incrementales, borrando lo que supere `$DAYS` días. Encaja bien para directorios pequeños de configuración (`/etc`, el `/opt/app` de un ejemplo) donde una copia completa diaria pesa poco; no escala igual de bien para datos que crecen (bases de datos grandes, volúmenes de usuario), porque cada copia repite todo el contenido. Para eso —copias incrementales, exclusiones, backups remotos por SSH— consulta la guía de [backups incrementales con rsync](/blog/backup-incremental-rsync-servidores-linux/).

```bash
#!/bin/bash
BACKUP_DIR="/backups"
DAYS=7
tar czf "$BACKUP_DIR/backup-$(date +%F).tar.gz" /etc /opt/app
find "$BACKUP_DIR" -name "backup-*.tar.gz" -mtime +$DAYS -delete
```

> [!IMPORTANT]
> Un backup que nunca se ha restaurado es una suposición, no una garantía. Prueba a descomprimir uno de estos `.tar.gz` en una ruta temporal de vez en cuando — es la única forma de detectar un backup corrupto o incompleto antes de necesitarlo de verdad.

## 3. Limpieza de logs

> [!CAUTION]
> `truncate -s 0` vacía el contenido de los logs de forma irreversible. Ajusta el `-mtime +30` a tu política de retención real antes de programar este script — no hay forma de recuperar el historial una vez borrado.

```bash
#!/bin/bash
find /var/log -name "*.log" -mtime +30 -exec truncate -s 0 {} \;
journalctl --vacuum-time=7d
```

`truncate -s 0` deja el fichero en su sitio (con el mismo inodo, importante si un proceso lo tiene abierto para escritura) pero sin contenido, a diferencia de borrarlo con `rm`, que dejaría al proceso escribiendo en un fichero ya desvinculado del directorio hasta que se reinicie. `journalctl --vacuum-time=7d` es una limpieza puntual del journal de systemd; si prefieres que el límite se aplique solo, sin depender de que este script se ejecute, `SystemMaxUse=500M` en `/etc/systemd/journald.conf` impone un tope de tamaño permanente sin necesidad de cron.

## 4. Verificación de servicios

Si tus unidades systemd ya llevan `Restart=on-failure` en la sección `[Service]`, systemd reinicia el servicio caído sin necesidad de este script — vale la pena revisar si ya lo tienes antes de duplicar la lógica. El valor añadido de este script está en los casos que systemd no cubre igual de bien: un resumen de varios servicios en una sola pasada (útil como comprobación manual o de entrada en un dashboard), o un servicio que no tiene `Restart=` configurado y no quieres tocar la unit file.

```bash
#!/bin/bash
SERVICES=("nginx" "postgresql" "redis")
for svc in "${SERVICES[@]}"; do
  if ! systemctl is-active --quiet "$svc"; then
    echo "$svc caído, reiniciando..."
    sudo systemctl restart "$svc"
  fi
done
```

> [!WARNING]
> Si un servicio entra en _crash loop_ (se cae en segundos tras cada reinicio, por ejemplo por una config rota), este script lo reinicia sin límite en cada pasada del cron, generando ruido en los logs sin resolver nada. Añade un contador de reintentos o, mejor aún, deja que sea `Restart=on-failure` combinado con `StartLimitIntervalSec`/`StartLimitBurst` en la propia unit file el que decida cuándo dejar de intentarlo.

## 5. Info rápida del sistema

Útil como primer comando al entrar por SSH a un servidor que no tocas a diario, o para pegar el estado del sistema en un ticket de soporte sin tener que lanzar cuatro comandos por separado y copiar cada salida.

```bash
#!/bin/bash
echo "=== $(hostname) ==="
echo "Uptime: $(uptime -p)"
echo "CPU: $(nproc) cores - Load: $(cat /proc/loadavg | cut -d' ' -f1-3)"
echo "RAM: $(free -h | awk '/Mem:/{print $3"/"$2}')"
echo "Disco: $(df -h / | awk 'NR==2{print $3"/"$2" ("$5")"}')"
```

## 6. Alerta de memoria alta

`free` calcula la columna "used" (`$3`) restando ya la caché y los buffers reclamables desde procps 3.3.10 (2014) — la versión que traen Debian, Ubuntu, RHEL 8 y 9 —, así que este porcentaje no se infla artificialmente por la caché de disco como ocurría con versiones antiguas. Aun así, una sola lectura por encima del umbral puede ser un pico momentáneo (un proceso que compacta datos, un build puntual) y no presión real.

```bash
#!/bin/bash
THRESHOLD=85
usage=$(free | awk '/Mem:/{printf("%.0f", $3/$2*100)}')
if [ "$usage" -ge "$THRESHOLD" ]; then
  echo "ALERTA: uso de memoria al ${usage}%"
fi
```

> [!TIP]
> Si el servidor tiene swap activa, combina esta comprobación con `swapon --show`: memoria alta sin apenas swap en uso suele ser normal (el sistema usa lo que tiene disponible); memoria alta con swap creciendo de forma sostenida sí es una señal real de presión.

## 7. Sincronización de directorios con rsync

`-a` (archive) preserva permisos, timestamps, propietario y enlaces simbólicos; `-z` comprime en tránsito, lo que ayuda en enlaces lentos y perjudica poco en una LAN; `-v` muestra qué se transfiere.

```bash
#!/bin/bash
SOURCE="/srv/app/"
DEST="backup@192.168.1.50:/data/app/"
rsync -avz --delete "$SOURCE" "$DEST"
```

> [!CAUTION]
> `--delete` borra en `$DEST` cualquier archivo que ya no exista en `$SOURCE`, para mantener el destino como una réplica exacta. Es exactamente lo que quieres en una sincronización de aplicación, pero si `$SOURCE` apunta accidentalmente a un directorio vacío o incorrecto, `--delete` puede vaciar el destino en el mismo comando. Prueba primero con `--dry-run` cuando cambies las rutas.

La barra final en `"$SOURCE"` importa: `rsync -a /srv/app/ dest/` copia el _contenido_ de `app/` dentro de `dest/`, mientras que `rsync -a /srv/app dest/` (sin barra) copia el directorio `app` completo dentro de `dest/`, un nivel más anidado de lo que probablemente esperas.

## 8. Comprobación de puertos críticos

Complementa al script 4: `systemctl is-active` dice si el proceso sigue en pie, pero un proceso puede seguir vivo sin estar realmente escuchando (por ejemplo, tras un error al enlazar el puerto en un reinicio parcial, o si se quedó colgado esperando una conexión a base de datos). Comprobar el puerto directamente detecta ese caso intermedio que el estado del servicio no refleja.

```bash
#!/bin/bash
PORTS=(22 80 443 5432)
for port in "${PORTS[@]}"; do
  if ! ss -lnt | awk '{print $4}' | grep -q ":$port$"; then
    echo "ALERTA: puerto $port no está escuchando"
  fi
done
```

## 9. Renovación automática de certificados (Let's Encrypt)

Este wrapper es un extra sobre el timer que ya instala Certbot por defecto; la guía de [certificados SSL con Certbot y Let's Encrypt](/blog/certificados-ssl-certbot-lets-encrypt/) explica qué hace realmente la renovación automática por debajo.

```bash
#!/bin/bash
certbot renew --quiet
if [ $? -eq 0 ]; then
  systemctl reload nginx
fi
```

## 10. Inventario básico de servidores

Este script asume que ya tienes acceso SSH por clave a cada host de la lista (sin contraseña interactiva, porque el bucle no la pediría de forma utilizable). Usa un usuario dedicado con permisos mínimos para esta tarea de solo lectura en lugar de reutilizar una clave con acceso root — el inventario no necesita más privilegios que ejecutar `hostname`, `uname` y `uptime`.

```bash
#!/bin/bash
OUT="/tmp/inventario-$(date +%F).csv"
echo "host,ip,kernel,uptime" > "$OUT"
for host in "$@"; do
  ssh "$host" "echo -n \"$host,\"; hostname -I | awk '{print \$1}' | tr -d '\n'; echo -n ','; uname -r | tr -d '\n'; echo -n ','; uptime -p | tr -d ','"
done >> "$OUT"
echo "Inventario generado en: $OUT"
```

## Conclusión

Automatizar tareas repetitivas con Bash ahorra tiempo y reduce errores, pero solo si el script en sí es de fiar: prueba cada uno manualmente antes de programarlo, y revisa los que escriben o borran datos (limpieza de logs, backups, rsync con `--delete`) con más cuidado que los que solo leen e informan. Guarda estos scripts en un repositorio con control de versiones —no solo en el servidor— para poder auditar cambios y reutilizarlos en otras máquinas. Para que se ejecuten solos en vez de a mano, prográmalos con [cron o systemd timers](/blog/tareas-programadas-cron-systemd-timers/).

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
