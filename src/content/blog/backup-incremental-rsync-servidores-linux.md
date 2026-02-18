---
title: 'Backups incrementales con rsync en servidores Linux'
description: 'Cómo implementar una estrategia de backups incrementales usando rsync y hardlinks para ahorrar espacio y tiempo en tus servidores.'
author: 'antonio'
pubDate: 2025-02-08
category: 'Automatización'
tags: ['Backup', 'rsync', 'Sysadmin', 'Scripts']
image: '../../assets/images/auto-backup.jpg'
draft: false
---

## El problema de los backups completos

Hacer una copia completa cada día consume espacio rápidamente. Si un servidor tiene 50 GB de datos y solo cambian 200 MB al día, copiar todo cada vez es un desperdicio. Los backups incrementales con rsync resuelven esto usando hardlinks para los archivos que no han cambiado.

## Cómo funciona rsync con hardlinks

La opción `--link-dest` de rsync compara el backup actual con el anterior. Si un archivo no ha cambiado, crea un hardlink en vez de copiarlo. El resultado es que cada backup parece una copia completa, pero solo ocupa el espacio de los archivos modificados.

## Script de backup incremental

```bash
#!/bin/bash

# Configuración
ORIGEN="/datos"
DESTINO="/backups/servidor01"
FECHA=$(date +%Y-%m-%d_%H%M)
ULTIMO=$(ls -1d "$DESTINO"/2* 2>/dev/null | tail -1)
RETENCION=30  # días

# Crear directorio de destino
mkdir -p "$DESTINO"

# Ejecutar backup
if [ -n "$ULTIMO" ]; then
    rsync -avz --delete \
        --link-dest="$ULTIMO" \
        "$ORIGEN/" \
        "$DESTINO/$FECHA/"
else
    rsync -avz --delete \
        "$ORIGEN/" \
        "$DESTINO/$FECHA/"
fi

# Verificar resultado
if [ $? -eq 0 ]; then
    echo "[OK] Backup completado: $DESTINO/$FECHA"
else
    echo "[ERROR] Fallo en el backup" >&2
    exit 1
fi

# Limpiar backups antiguos
find "$DESTINO" -maxdepth 1 -type d -mtime +$RETENCION -exec rm -rf {} \;
echo "[OK] Limpieza completada: eliminados backups de más de $RETENCION días"
```

## Backup remoto por SSH

Para copiar datos desde otro servidor:

```bash
rsync -avz --delete \
    --link-dest=/backups/web01/ultimo \
    -e "ssh -p 2222 -i /root/.ssh/backup_key" \
    usuario@192.168.1.50:/var/www/ \
    /backups/web01/$(date +%Y-%m-%d)/

# Actualizar enlace simbólico al último backup
ln -snf /backups/web01/$(date +%Y-%m-%d) /backups/web01/ultimo
```

## Excluir archivos innecesarios

Crea un archivo `/etc/rsync-exclude.txt`:

```text
/proc
/sys
/dev
/tmp
/var/cache
/var/tmp
*.log
*.swap
.cache
```

Úsalo con:

```bash
rsync -avz --delete --exclude-from=/etc/rsync-exclude.txt /origen/ /destino/
```

## Automatizar con systemd timer

Crea el servicio `/etc/systemd/system/backup.service`:

```ini
[Unit]
Description=Backup incremental con rsync

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
```

Y el timer `/etc/systemd/system/backup.timer`:

```ini
[Unit]
Description=Ejecutar backup diario a las 3:00

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Activar:

```bash
sudo systemctl enable --now backup.timer
```

## Verificar la integridad

No basta con hacer backups, hay que comprobar que funcionan:

```bash
# Comparar origen y backup
diff -rq /datos/ /backups/servidor01/2025-02-08_0300/

# Ver espacio real ocupado (con hardlinks)
du -sh /backups/servidor01/*
du -sh --apparent-size /backups/servidor01/*
```

## Estrategia de retención

| Periodo        | Retención |
| -------------- | --------- |
| Últimos 7 días | Diario    |
| Último mes     | Semanal   |
| Último año     | Mensual   |

Para implementarlo, en vez de borrar por antigüedad, marca los backups semanales y mensuales que quieras conservar con un enlace simbólico o muévelos a otro directorio.

## Conclusión

rsync con `--link-dest` es una solución elegante que no necesita software adicional. Cada backup es navegable como una copia completa pero ocupa una fracción del espacio. Combinado con systemd timers y una buena política de retención, tienes una estrategia de backup sólida y fiable.
