---
title: '10 scripts Bash útiles para el día a día del sysadmin'
description: 'Colección de scripts Bash prácticos para monitorización, backups, limpieza de logs y tareas comunes de administración de sistemas.'
author: 'alois'
pubDate: 2026-01-14
category: 'Automatización'
tags: ['Bash', 'Scripts', 'Sysadmin', 'Automatización']
image: '../../assets/images/auto-bash.jpg'
draft: false
---

## Introducción

Los scripts Bash son la navaja suiza del sysadmin. Aquí tienes una colección de scripts prácticos para tareas cotidianas.

## 1. Monitor de disco

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

## 2. Backup con rotación

```bash
#!/bin/bash
BACKUP_DIR="/backups"
DAYS=7
tar czf "$BACKUP_DIR/backup-$(date +%F).tar.gz" /etc /opt/app
find "$BACKUP_DIR" -name "backup-*.tar.gz" -mtime +$DAYS -delete
```

## 3. Limpieza de logs

```bash
#!/bin/bash
find /var/log -name "*.log" -mtime +30 -exec truncate -s 0 {} \;
journalctl --vacuum-time=7d
```

## 4. Verificación de servicios

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

## 5. Info rápida del sistema

```bash
#!/bin/bash
echo "=== $(hostname) ==="
echo "Uptime: $(uptime -p)"
echo "CPU: $(nproc) cores - Load: $(cat /proc/loadavg | cut -d' ' -f1-3)"
echo "RAM: $(free -h | awk '/Mem:/{print $3"/"$2}')"
echo "Disco: $(df -h / | awk 'NR==2{print $3"/"$2" ("$5")"}')"
```

## Conclusión

Automatizar tareas repetitivas con Bash ahorra tiempo y reduce errores. Guarda estos scripts en un repositorio y adáptalos a tu entorno.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
