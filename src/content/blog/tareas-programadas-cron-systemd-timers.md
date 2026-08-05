---
title: 'Tareas programadas: cron vs systemd timers'
description: 'Cron vs systemd timers en Linux: sintaxis OnCalendar, el entorno mínimo de cron y cómo migrar un cron job a timer paso a paso.'
author: 'antonio'
pubDate: 2026-01-23
updatedDate: 2026-08-05
category: 'Automatización'
tags: ['Cron', 'systemd', 'Automatización', 'Linux']
image: '../../assets/images/auto-cron.jpg'
draft: false
---

## Introducción

Programar tareas es esencial en la administración de sistemas. Linux ofrece dos enfoques principales: el clásico cron, con más de 40 años de historia y presente en prácticamente cualquier sistema Unix, y los systemd timers, que se apoyan en las mismas unidades que ya vimos en la [guía de systemd](/blog/guia-systemd-servicios-linux/) y aportan control de dependencias y registro centralizado. Ninguno es estrictamente superior: la elección depende de si necesitas simplicidad y portabilidad, o integración con el resto del sistema.

## Cron: el veterano

### Sintaxis y comodines

Cada línea de un crontab tiene cinco campos de tiempo seguidos del comando a ejecutar:

```
# min hora dia mes diasem comando
  0   3    *   *   *     /opt/scripts/backup.sh
```

Los comodines permiten expresar patrones más ricos que un simple valor fijo:

```bash
*/15 * * * *   /opt/scripts/check.sh     # cada 15 minutos (paso)
0    9-18 * * 1-5  /opt/scripts/poll.sh  # cada hora en punto, de 9 a 18h, lunes a viernes (rango)
0    0  1,15 * *    /opt/scripts/rotar.sh # los días 1 y 15 de cada mes (lista)
```

- `*` — cualquier valor
- `,` — lista de valores (`1,15`)
- `-` — rango (`9-18`, `1-5`)
- `/` — paso dentro de un rango o comodín (`*/15`)

### Tipos de crontab

No todo pasa por `crontab -e`. Cron lee tareas de varias fuentes distintas:

- **Crontab de usuario** (`crontab -e`): sin campo de usuario, se ejecuta como quien lo edita.
- **`/etc/crontab`** y **`/etc/cron.d/*`**: mismo formato de cinco campos de tiempo, pero con un campo adicional que indica **qué usuario** ejecuta el comando — un error habitual es copiar una línea de un crontab de usuario a `/etc/cron.d/` sin añadir ese campo.
- **`/etc/cron.{hourly,daily,weekly,monthly}/`**: no son crontabs, son directorios de scripts ejecutables (sin extensión con punto en el nombre) que `run-parts` recorre y ejecuta uno por uno según la frecuencia del directorio.

```bash
# /etc/cron.d/mi-tarea — nota el campo de usuario extra
0 3 * * * root /opt/scripts/backup.sh
```

### Control de acceso: cron.allow y cron.deny

Quién puede usar `crontab` se controla con dos archivos opcionales en `/etc/`:

- Si existe **`cron.allow`**, solo los usuarios listados ahí pueden usar `crontab`; todos los demás quedan bloqueados.
- Si **no** existe `cron.allow` pero sí **`cron.deny`**, pueden usarlo todos excepto los listados en `cron.deny`.

### El entorno mínimo de cron

> [!IMPORTANT]
> Cron ejecuta cada tarea con un entorno mínimo: sin `.bashrc`, sin `.profile`, y con un `PATH` reducido (normalmente `/usr/bin:/bin`) que no incluye lo que hayas añadido en tu shell interactiva. Es la causa más común de "el script funciona a mano pero falla en cron" — el comando que usas simplemente no está en ese `PATH` recortado.

La forma más fiable de evitarlo es usar rutas absolutas para los binarios, o definir `PATH` explícitamente al principio del crontab:

```bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
SHELL=/bin/bash
MAILTO=admin@ejemplo.com

0 3 * * * /opt/scripts/backup.sh
```

`MAILTO` controla a quién se envía la salida de cada ejecución por correo local; con `MAILTO=""` se silencia por completo. Para depurar una tarea que falla solo bajo cron, un truco rápido es volcar el entorno real que ve cron a un archivo y reproducirlo a mano:

```bash
* * * * * env > /tmp/cron-env.txt   # tarea temporal, bórrala después de capturar
```

### Atajos comunes

```bash
@reboot   /opt/scripts/init.sh
@daily    /opt/scripts/cleanup.sh
@hourly   /opt/scripts/check.sh
```

## systemd timers: la alternativa moderna

### Timers de calendario vs timers monótonos

systemd distingue dos formas de disparar un timer:

- **Timers de calendario** (`OnCalendar=`): equivalentes a cron, disparan en una fecha/hora concreta o repetida (`daily`, `Mon..Fri 09:00`, etc.).
- **Timers monótonos** (`OnBootSec=`, `OnUnitActiveSec=`): no dependen del reloj de pared, sino de un intervalo relativo — desde el arranque del sistema o desde la última vez que la unidad se activó. Son útiles para tareas que deben repetirse "cada X tiempo desde que terminó la anterior" en vez de en un horario fijo, algo que cron no puede expresar de forma nativa.

### Sintaxis de OnCalendar

`OnCalendar=` acepta tanto atajos como expresiones detalladas equivalentes a los campos `AAAA-MM-DD HH:MM:SS`, con los mismos comodines de lista (`,`), rango (`..`) y paso (`/`) que ya viste en cron:

```
daily                    → *-*-* 00:00:00
weekly                   → Mon *-*-* 00:00:00
monthly                  → *-*-01 00:00:00
Mon..Fri 09,18:00:00     → laborables a las 9:00 y a las 18:00
*-01,04,07,10-01 00:00   → el día 1 de enero, abril, julio y octubre (trimestral)
```

> [!TIP]
> `systemd-analyze calendar "Mon..Fri 09,18:00:00"` valida la expresión y muestra la próxima vez que se disparará, sin necesidad de crear el timer para probarlo.

### Crear un timer

El ejemplo de backup diario es el mismo patrón que usamos para automatizar los [backups incrementales con rsync](/blog/backup-incremental-rsync-servidores-linux/):

```ini
# /etc/systemd/system/backup.service
[Unit]
Description=Backup diario

[Service]
Type=oneshot
ExecStart=/opt/scripts/backup.sh
```

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Backup diario

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
RandomizedDelaySec=300
AccuracySec=1min

[Install]
WantedBy=timers.target
```

- **`Persistent=true`** — si el sistema estaba apagado cuando tocaba disparar el timer, lo ejecuta en cuanto arranca de nuevo. Cron no tiene equivalente: una tarea que caía dentro de una ventana de apagado simplemente no se ejecuta nunca.
- **`RandomizedDelaySec=300`** — añade un retraso aleatorio de hasta 5 minutos antes de disparar. Sirve para repartir en el tiempo timers idénticos en varias máquinas y evitar que todas golpeen un mismo recurso (por ejemplo, un servidor de backups) exactamente a la misma hora.
- **`AccuracySec=1min`** — es el valor por defecto; systemd puede desplazar el disparo dentro de esa ventana para agrupar despertares de CPU y ahorrar energía. En tareas donde el minuto exacto no importa, ampliarlo (`AccuracySec=1h`) reduce aún más el consumo en portátiles o equipos con gestión agresiva de energía.

### Gestión y logs

```bash
sudo systemctl enable --now backup.timer
systemctl list-timers
systemctl status backup.timer
```

A diferencia de cron, que envía la salida por correo local (o la descarta según `MAILTO`), cada ejecución de un timer queda registrada en el journal junto con el resto del sistema, consultable con la unidad `.service` asociada — tal como se explica en la guía de [journalctl](/blog/journalctl-domina-logs-systemd/):

```bash
journalctl -u backup.service --since today
```

## Migrar un cron job a systemd timer

El proceso siempre sigue la misma secuencia, tanto si migras una tarea existente como si creas una nueva:

```
1. Extraer el comando y el horario del crontab
   │
   ▼
2. Crear <nombre>.service (Type=oneshot, ExecStart=comando)
   │
   ▼
3. Crear <nombre>.timer (OnCalendar= equivalente al horario cron)
   │
   ▼
4. systemctl daemon-reload
   │
   ▼
5. systemctl enable --now <nombre>.timer
   │
   ├── horario correcto → eliminar la línea del crontab original
   └── horario no dispara como se esperaba → systemd-analyze calendar
       para verificar la expresión antes de tocar el crontab
```

> [!WARNING]
> No borres la línea del crontab original hasta confirmar con `systemctl list-timers` que el nuevo timer se ha disparado correctamente al menos una vez — tener ambos activos a la vez solo duplica la ejecución, pero quedarte sin ninguno de los dos deja la tarea sin ejecutar.

## Comparativa ampliada

| Característica                                  | cron                               | systemd timers                                     |
| ----------------------------------------------- | ---------------------------------- | -------------------------------------------------- |
| Logs                                            | Correo local / syslog              | `journalctl`, integrado con el resto del sistema   |
| Dependencias                                    | No                                 | Sí (`After=`, `Requires=` en el `.service`)        |
| Ejecución perdida (sistema apagado)             | Se pierde                          | `Persistent=true` la recupera al arrancar          |
| Reparto de carga (jitter)                       | No                                 | `RandomizedDelaySec=`                              |
| Timers monótonos ("cada X desde la última vez") | No                                 | `OnUnitActiveSec=`                                 |
| Entorno de ejecución                            | Mínimo, requiere `PATH=` explícito | El del `.service`, configurable con `Environment=` |
| Complejidad de configuración                    | Baja, una línea                    | Media, dos archivos por tarea                      |
| Portabilidad                                    | Cualquier Unix                     | Solo sistemas con systemd                          |

## ¿Cuál elegir?

Para tareas simples y puntuales —lanzar alguno de estos [scripts Bash útiles para el sysadmin](/blog/scripts-bash-utiles-sysadmin/) sin más complicación— cron sigue siendo la opción más rápida de escribir y la más portable entre sistemas. Cuando la tarea depende de que otro servicio esté disponible, necesitas reintentos, quieres que se recupere tras un apagado, o simplemente ya gestionas el resto de tus servicios con systemd, los timers encajan mejor: quedan integrados en el mismo ecosistema de `systemctl status` y `journalctl` que usas para todo lo demás.

## Conclusión

Cron sigue siendo válido para tareas simples que no necesitan más que un horario y un comando. Los systemd timers ofrecen mejor integración con el sistema, recuperación de ejecuciones perdidas y control de dependencias para escenarios más complejos — a cambio de dos archivos en vez de una línea. Conocer ambos, y saber cuándo migrar de uno a otro, es parte del oficio.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
