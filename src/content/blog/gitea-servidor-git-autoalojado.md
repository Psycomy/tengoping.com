---
title: 'Gitea: monta tu propio servidor Git'
description: 'Instala y configura Gitea como alternativa ligera a GitHub o GitLab para alojar repositorios Git en tu propio servidor.'
author: 'antonio'
pubDate: 2025-10-08
category: 'Self-Hosting'
tags: ['Gitea', 'Git', 'Self-Hosting', 'DevOps']
image: '../../assets/images/gitea-server.jpg'
draft: false
---

## Por que autoalojar Git

Tener tus repositorios en GitHub o GitLab es practico, pero dependes de sus politicas, disponibilidad y precios. Con un servidor Git propio mantienes el control total sobre tu codigo, defines tus propias reglas de acceso y no tienes limites de repositorios privados ni de almacenamiento mas alla de tu disco.

## Gitea vs GitLab vs Forgejo

- **GitLab**: completo pero pesado. Necesita minimo 4 GB de RAM y consume muchos recursos. Ideal para equipos grandes con necesidades de CI/CD integrado.
- **Gitea**: ligero, rapido y con poca huella de memoria. Escrito en Go, funciona con un solo binario. Interfaz web similar a GitHub.
- **Forgejo**: fork comunitario de Gitea con gobernanza abierta. Compatible a nivel de API y configuracion. Buena alternativa si prefieres un proyecto sin control corporativo.

Para servidores modestos o uso personal, Gitea es la mejor opcion por su bajo consumo de recursos.

## Requisitos

- Servidor Linux con acceso root (Debian, Ubuntu, Rocky, etc.)
- Git instalado en el servidor
- PostgreSQL o MariaDB (opcional pero recomendado para produccion)
- Un usuario de sistema dedicado

## Preparar el sistema

Crea un usuario sin shell interactiva para ejecutar Gitea:

```bash
sudo adduser --system --shell /bin/bash --group --home /home/gitea gitea
```

Instala Git si no lo tienes:

```bash
sudo apt install git -y
```

## Instalar Gitea

Descarga el binario de la ultima version estable desde la pagina oficial:

```bash
GITEA_VERSION="1.22.3"
sudo wget -O /usr/local/bin/gitea \
  "https://dl.gitea.com/gitea/${GITEA_VERSION}/gitea-${GITEA_VERSION}-linux-amd64"
sudo chmod +x /usr/local/bin/gitea
```

Crea los directorios necesarios:

```bash
sudo mkdir -p /etc/gitea /var/lib/gitea/{custom,data,log}
sudo chown -R gitea:gitea /var/lib/gitea
sudo chown root:gitea /etc/gitea
sudo chmod 770 /etc/gitea
```

## Configurar la base de datos

Usaremos PostgreSQL. Instalalo y crea la base de datos:

```bash
sudo apt install postgresql -y
sudo -u postgres psql
```

```sql
CREATE ROLE gitea WITH LOGIN PASSWORD 'tu_password_segura';
CREATE DATABASE giteadb WITH OWNER gitea TEMPLATE template0 ENCODING UTF8 LC_COLLATE 'es_ES.UTF-8' LC_CTYPE 'es_ES.UTF-8';
\q
```

## Crear el servicio systemd

Crea el archivo de unidad para gestionar Gitea como servicio:

```bash
sudo nano /etc/systemd/system/gitea.service
```

```ini
[Unit]
Description=Gitea (Git with a cup of tea)
After=syslog.target
After=network.target
After=postgresql.service

[Service]
RestartSec=2s
Type=simple
User=gitea
Group=gitea
WorkingDirectory=/var/lib/gitea
ExecStart=/usr/local/bin/gitea web --config /etc/gitea/app.ini
Restart=always
Environment=USER=gitea HOME=/home/gitea GITEA_WORK_DIR=/var/lib/gitea

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gitea
```

Gitea arrancara en el puerto 3000 por defecto. Accede a `http://tu-servidor:3000` para completar la configuracion inicial desde el navegador.

## Configurar app.ini

El archivo principal de configuracion se genera tras el primer acceso web en `/etc/gitea/app.ini`. Algunos ajustes importantes:

```ini
[server]
DOMAIN           = git.tudominio.com
ROOT_URL         = https://git.tudominio.com/
HTTP_PORT        = 3000
SSH_DOMAIN       = git.tudominio.com
START_SSH_SERVER = false

[database]
DB_TYPE  = postgres
HOST     = 127.0.0.1:5432
NAME     = giteadb
USER     = gitea
PASSWD   = tu_password_segura

[service]
DISABLE_REGISTRATION = true

[log]
MODE = file
LEVEL = Warn
```

Despues de modificar `app.ini`, reinicia el servicio:

```bash
sudo systemctl restart gitea
```

## Proxy inverso con Nginx

Para servir Gitea con HTTPS a traves de Nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name git.tudominio.com;

    ssl_certificate     /etc/letsencrypt/live/git.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/git.tudominio.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## Crear usuario y primer repositorio

Con `DISABLE_REGISTRATION = true`, crea el primer usuario administrador desde la linea de comandos:

```bash
sudo -u gitea /usr/local/bin/gitea admin user create \
  --config /etc/gitea/app.ini \
  --username admin \
  --password 'ContrasenaSegura123!' \
  --email admin@tudominio.com \
  --admin
```

Accede al panel web, crea un repositorio y clonalo:

```bash
git clone git@git.tudominio.com:admin/mi-proyecto.git
```

## Configurar acceso SSH

Anade tu clave publica en **Configuracion > Claves SSH** del perfil de usuario. Si usas el servidor SSH del sistema (no el integrado de Gitea), asegurate de que el usuario `gitea` tenga un `~/.ssh/authorized_keys` gestionado por Gitea.

## Migrar repositorios desde GitHub

Gitea incluye una herramienta de migracion integrada. Desde el panel web, haz clic en **+** > **Nueva migracion** y selecciona GitHub como origen. Introduce la URL del repositorio y, opcionalmente, un token de acceso personal para repositorios privados. Gitea importara el codigo, issues, labels y milestones.

Tambien puedes migrar por terminal:

```bash
git clone --mirror https://github.com/usuario/repo.git
cd repo.git
git remote set-url origin git@git.tudominio.com:admin/repo.git
git push --mirror
```

## Mantenimiento

- **Actualizaciones**: descarga el nuevo binario y reemplaza el existente en `/usr/local/bin/gitea`. Reinicia el servicio.
- **Backups**: usa `gitea dump` para generar un archivo con los repositorios, base de datos y configuracion.
- **Monitoreo**: revisa los logs en `/var/lib/gitea/log/` y supervisa el uso de disco.

Con Gitea funcionando, tienes un servidor Git completo con interfaz web, gestion de usuarios, issues y pull requests, todo bajo tu propio techo.
