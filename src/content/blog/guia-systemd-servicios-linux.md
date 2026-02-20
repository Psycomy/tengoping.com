---
title: 'Guía práctica de systemd: gestión de servicios en Linux'
description: 'Domina systemd para administrar servicios, timers y targets en distribuciones Linux modernas.'
author: 'alois'
pubDate: 2026-01-11
category: 'Linux'
tags: ['systemd', 'Linux', 'Servicios', 'Sysadmin']
image: '../../assets/images/linux-systemd.jpg'
draft: false
---

## ¿Qué es systemd?

systemd es el sistema de inicio y gestor de servicios estándar en la mayoría de distribuciones Linux modernas. Controla el arranque del sistema y la gestión de daemons.

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

```bash
sudo systemctl enable nginx
sudo systemctl disable nginx
sudo systemctl enable --now nginx
```

## Crear un servicio personalizado

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

## Timers como alternativa a cron

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

## Conclusión

systemd ofrece un control granular sobre los servicios del sistema. Dominar sus comandos es esencial para cualquier administrador de sistemas.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
