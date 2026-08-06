---
title: 'Backups incrementales con rsync en Linux'
description: 'Cómo implementar una estrategia de backups incrementales usando rsync y hardlinks para ahorrar espacio y tiempo en tus servidores.'
author: 'antonio'
pubDate: 2026-01-16
updatedDate: 2026-08-06
category: 'Automatización'
tags: ['Backup', 'rsync', 'Sysadmin', 'Scripts']
image: '../../assets/images/auto-backup.jpg'
draft: false
---

## El problema de los backups completos

Hacer una copia completa cada día consume espacio rápidamente. Si un servidor tiene 50 GB de datos y solo cambian 200 MB al día, copiar todo cada vez es un desperdicio. Los backups incrementales con rsync resuelven esto usando hardlinks para los archivos que no han cambiado.

## Cómo funciona rsync con hardlinks

La opción `--link-dest` de rsync compara el backup actual con el anterior. Si un archivo no ha cambiado, crea un hardlink en vez de copiarlo. El resultado es que cada backup parece una copia completa, pero solo ocupa el espacio de los archivos modificados.

> [!WARNING]
> Un hardlink no es una copia: es una segunda entrada de directorio apuntando al mismo contenido en disco. Si entras a una carpeta de un backup antiguo y editas un archivo directamente (o cambias sus permisos), estás modificando el mismo dato que comparten todos los demás backups enlazados a él — la corrupción se propaga a "copias" que deberían ser independientes. Trata cualquier snapshot dentro de `$DESTINO` como solo lectura; si necesitas modificar algo, cópialo fuera primero.

> [!IMPORTANT]
> `--link-dest` solo funciona si origen y `$DESTINO` están en un filesystem que soporte hardlinks (ext4, XFS, Btrfs, NTFS). Un disco USB formateado en exFAT o FAT32 —habitual para compatibilidad con Windows— no los soporta: cada backup se copiaría completo sin ahorro de espacio, sin ningún error que lo avise. Comprueba el filesystem del destino con `df -T "$DESTINO"` antes de confiar en el ahorro de espacio.

```
Primer backup: /backups/servidor01/2026-02-06_0300/
   │
   ▼
1. rsync -avz --delete /datos/ /backups/servidor01/2026-02-06_0300/
   → copia completa: no hay backup anterior con el que comparar
   │
   ▼
2. Backups siguientes, con --link-dest apuntando al anterior:
   rsync --link-dest=.../2026-02-06_0300 /datos/ .../2026-02-07_0300/
   ├── archivo sin cambios     → hardlink al backup anterior (0 bytes extra)
   └── archivo nuevo/modificado → se copia de verdad
   │
   ▼
3. find /backups/servidor01 -mtime +$RETENCION -exec rm -rf {} \;
   → los snapshots con más de $RETENCION días se eliminan
```

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
find "$DESTINO" -mindepth 1 -maxdepth 1 -type d -mtime +$RETENCION -exec rm -rf {} \;
echo "[OK] Limpieza completada: eliminados backups de más de $RETENCION días"
```

> [!CAUTION]
> La línea `find ... -exec rm -rf {} \;` borra directorios completos sin pedir confirmación. Antes de programar el script, comprueba a mano que `$DESTINO` y `$RETENCION` apuntan donde crees — un valor mal puesto puede borrar backups que aún necesitas.

## Backup remoto por SSH

Para copiar datos desde otro servidor, por ejemplo hacia un NAS como el que vimos en la guía de [OpenMediaVault](/blog/nas-casero-openmediavault/):

> [!IMPORTANT]
> `--delete` borra en el destino cualquier archivo que ya no exista en el origen. Si inviertes por error el orden origen/destino, el comando borrará datos en producción en vez de en la copia de seguridad. Revisa siempre qué ruta va primero antes de ejecutar.

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

Aquí el mínimo necesario para este script; para entender a fondo cron frente a systemd timers (y cuándo usar cada uno) consulta la guía de [tareas programadas](/blog/tareas-programadas-cron-systemd-timers/). Crea el servicio `/etc/systemd/system/backup.service`:

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
diff -rq /datos/ /backups/servidor01/2026-02-08_0300/

# Ver espacio real ocupado (con hardlinks)
du -sh /backups/servidor01/*
du -sh --apparent-size /backups/servidor01/*
```

Al pasar todos los snapshots como argumentos de la misma llamada (`/backups/servidor01/*` se expande antes de ejecutar `du`), GNU `du` cuenta cada archivo enlazado por hardlink una sola vez en toda la invocación, no una vez por carpeta. En la práctica esto significa que el primer snapshot que `du` procesa "se lleva" el tamaño de los archivos compartidos, y los siguientes aparecen con un tamaño mucho menor — no porque ocupen menos, sino porque esos inodos ya se contaron antes. No interpretes esos números como "lo que costaría cada snapshot por separado". `--apparent-size` no cambia esa deduplicación: solo cambia si el tamaño se redondea al bloque del filesystem (el valor por defecto, típicamente múltiplos de 4 KB) o se muestra el tamaño exacto en bytes del contenido — una diferencia menor salvo que tengas muchísimos archivos muy pequeños. Para el espacio real total ocupado por todos los snapshots juntos, la fuente fiable es el uso del filesystem completo con `df -h "$DESTINO"`, no la suma de los `du` por snapshot.

> [!NOTE]
> Por defecto, rsync decide si un archivo cambió comparando solo tamaño y fecha de modificación (`mtime`), no su contenido — es lo que se conoce como "quick check". Esto es rápido, pero significa que un archivo cuyo contenido cambió pero cuyo `mtime` se restauró artificialmente (por ejemplo, tras una restauración parcial desde otra fuente) puede quedar sin copiar, compartiendo hardlink con una versión desactualizada. Para una verificación más estricta —a costa de leer todo el contenido en cada pasada, con el coste de E/S que eso implica—, añade `--checksum` puntualmente en una ejecución de auditoría, no en el cron diario.

## Estrategia de retención

El script de la sección anterior borra por antigüedad simple (`-mtime +$RETENCION`): pasados 30 días, todo desaparece por igual. Una política de retención tipo abuelo-padre-hijo (GFS, _grandfather-father-son_) conserva más historial reciente con granularidad fina y menos historial antiguo con granularidad gruesa, sin que el número total de snapshots crezca sin límite:

| Periodo        | Retención |
| -------------- | --------- |
| Últimos 7 días | Diario    |
| Último mes     | Semanal   |
| Último año     | Mensual   |

En vez de borrar por antigüedad simple, hay que decidir para cada snapshot si sigue siendo "el diario de esta semana", "el semanal de este mes" o "el mensual de este año" antes de eliminarlo:

```bash
#!/bin/bash
# Retención GFS: ejecutar después de cada backup diario
DESTINO="/backups/servidor01"
HOY=$(date +%s)

for snap in "$DESTINO"/2*_*; do
    NOMBRE=$(basename "$snap")
    FECHA_SNAP="${NOMBRE%%_*}"                      # parte "2026-02-06" del nombre
    EDAD=$(( (HOY - $(date -d "$FECHA_SNAP" +%s)) / 86400 ))
    DIA_SEMANA=$(date -d "$FECHA_SNAP" +%u)          # 1=lunes ... 7=domingo
    DIA_MES=$(date -d "$FECHA_SNAP" +%d)

    if [ "$EDAD" -le 7 ]; then
        continue                                     # última semana: se conserva entero
    elif [ "$EDAD" -le 30 ]; then
        [ "$DIA_SEMANA" -eq 7 ] || rm -rf "$snap"     # 8-30 días: solo el del domingo
    elif [ "$EDAD" -le 365 ]; then
        [ "$DIA_MES" -eq "01" ] || rm -rf "$snap"     # 31-365 días: solo el día 1 de cada mes
    else
        rm -rf "$snap"                                # más de un año: fuera
    fi
done
```

Es una implementación de ejemplo, no la única válida: ajusta los cortes (7/30/365) y qué día se considera "el semanal" a tu propia política de retención. Lo importante es el principio — decidir la granularidad según la antigüedad, no borrar todo por igual al cumplir un plazo fijo.

## Conclusión

rsync con `--link-dest` es una solución elegante que no necesita software adicional. Cada backup es navegable como una copia completa pero ocupa una fracción del espacio, siempre que el destino soporte hardlinks y trates cada snapshot como solo lectura. Combinado con systemd timers, una política de retención por niveles (diario/semanal/mensual) y una verificación periódica que no se fíe solo del quick-check por defecto, tienes una estrategia de backup sólida y fiable — y complementa, no sustituye, a la redundancia de un [array RAID](/blog/raid-software-mdadm-guia-practica/).

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
