---
title: "Tareas programadas: cron vs systemd timers"
description: "Comparativa entre cron y systemd timers para programar tareas automáticas en Linux, con ejemplos prácticos de ambos."
author: "antonio"
pubDate: 2025-02-12
category: "Automatización"
tags: ["Cron", "systemd", "Automatización", "Linux"]
image: "../../assets/images/auto-cron.jpg"
draft: false
---

## Introducción

Programar tareas es esencial en la administración de sistemas. Linux ofrece dos enfoques principales: el clásico cron y los modernos systemd timers.

## Cron: el clásico

### Sintaxis

```
# min hora dia mes diasem comando
  0   3    *   *   *     /opt/scripts/backup.sh
```

### Gestión

```bash
crontab -e          # editar tareas del usuario
crontab -l          # listar tareas
sudo crontab -u www-data -l  # tareas de otro usuario
```

### Atajos comunes

```bash
@reboot   /opt/scripts/init.sh
@daily    /opt/scripts/cleanup.sh
@hourly   /opt/scripts/check.sh
```

## systemd timers: la alternativa moderna

### Crear un timer

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Backup diario

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Gestión

```bash
sudo systemctl enable --now backup.timer
systemctl list-timers
systemctl status backup.timer
```

## Comparativa

| Característica | cron | systemd timers |
|---------------|------|----------------|
| Logs | syslog | journalctl |
| Dependencias | No | Sí |
| Ejecución perdida | No | Persistent=true |
| Complejidad | Baja | Media |

## Conclusión

Cron sigue siendo válido para tareas simples. Los systemd timers ofrecen mejor integración con el sistema y control de dependencias para escenarios más complejos.
