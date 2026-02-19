---
title: 'Montar tu propia nube con Nextcloud'
description: 'Guía completa para instalar Nextcloud en un servidor Linux y tener tu propio almacenamiento en la nube sin depender de terceros.'
author: 'alois'
pubDate: 2025-04-05
category: 'Self-Hosting'
tags: ['Nextcloud', 'Self-Hosting', 'Nube', 'Linux']
image: '../../assets/images/nextcloud-server.jpg'
draft: false
---

## Por que autoalojar tu almacenamiento en la nube

Servicios como Google Drive o Dropbox son comodos, pero tus datos quedan en servidores ajenos. Con Nextcloud puedes tener sincronizacion de archivos, calendario, contactos y mucho mas bajo tu propio control. Tu decides donde se almacenan los datos, quien accede y durante cuanto tiempo se conservan.

## Requisitos previos

Necesitas un servidor Linux con acceso root y una pila LAMP o LEMP funcional:

- **Sistema operativo**: Debian 12, Ubuntu 22.04+ o similar
- **Servidor web**: Apache o Nginx
- **Base de datos**: MariaDB 10.6+ o MySQL 8.0+
- **PHP**: 8.2 o superior con modulos necesarios

### Instalar dependencias

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install apache2 mariadb-server libapache2-mod-php \
  php php-gd php-json php-mysql php-curl php-mbstring \
  php-intl php-imagick php-xml php-zip php-bcmath php-gmp \
  unzip wget -y
```

## Preparar la base de datos

Accede a MariaDB y crea la base de datos y el usuario dedicado para Nextcloud:

```bash
sudo mysql -u root
```

```sql
CREATE DATABASE nextcloud CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE USER 'nextcloud'@'localhost' IDENTIFIED BY 'tu_password_segura';
GRANT ALL PRIVILEGES ON nextcloud.* TO 'nextcloud'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Usa una contrasena robusta. Nunca dejes la contrasena por defecto en produccion.

## Descargar e instalar Nextcloud

Descarga la ultima version estable desde el sitio oficial y extrae el archivo en el directorio web:

```bash
cd /tmp
wget https://download.nextcloud.com/server/releases/latest.zip
sudo unzip latest.zip -d /var/www/
sudo chown -R www-data:www-data /var/www/nextcloud
```

## Configurar Apache

Crea un virtualhost dedicado para Nextcloud:

```bash
sudo nano /etc/apache2/sites-available/nextcloud.conf
```

```apache
<VirtualHost *:80>
    ServerName nube.tudominio.com
    DocumentRoot /var/www/nextcloud

    <Directory /var/www/nextcloud>
        Require all granted
        AllowOverride All
        Options FollowSymLinks MultiViews
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/nextcloud-error.log
    CustomLog ${APACHE_LOG_DIR}/nextcloud-access.log combined
</VirtualHost>
```

Activa el sitio y los modulos necesarios:

```bash
sudo a2ensite nextcloud.conf
sudo a2enmod rewrite headers env dir mime
sudo systemctl restart apache2
```

### Alternativa con Nginx

Si prefieres Nginx, la configuracion del bloque server seria similar. Apunta el root a `/var/www/nextcloud` y asegurate de pasar las peticiones PHP a `php-fpm` mediante un bloque `location ~ \.php$` con `fastcgi_pass`.

## Ajustar PHP

Edita el archivo de configuracion de PHP para mejorar el rendimiento:

```bash
sudo nano /etc/php/8.2/apache2/php.ini
```

Modifica estos valores:

```ini
memory_limit = 512M
upload_max_filesize = 16G
post_max_size = 16G
max_execution_time = 3600
opcache.enable = 1
opcache.memory_consumption = 128
opcache.interned_strings_buffer = 16
opcache.max_accelerated_files = 10000
opcache.revalidate_freq = 1
```

```bash
sudo systemctl restart apache2
```

## Primer acceso y configuracion del administrador

Abre el navegador y accede a `http://nube.tudominio.com`. El asistente de instalacion te pedira:

1. **Usuario administrador**: elige un nombre y contrasena seguros.
2. **Directorio de datos**: por defecto `/var/www/nextcloud/data`. Puedes cambiarlo a otra particion con mas espacio.
3. **Base de datos**: selecciona MySQL/MariaDB e introduce los datos creados antes (usuario `nextcloud`, contrasena y nombre de base de datos `nextcloud`).

Haz clic en instalar y espera a que termine el proceso.

## Habilitar aplicaciones

Nextcloud incluye un ecosistema de aplicaciones. Desde el panel de administracion, accede a **Aplicaciones** y activa las que necesites:

- **Calendar**: calendario compatible con CalDAV
- **Contacts**: libreta de direcciones con CardDAV
- **Notes**: notas en formato Markdown
- **Talk**: videollamadas y chat
- **Office**: edicion colaborativa de documentos (requiere Collabora o OnlyOffice)

## Configurar tareas cron

Para que las tareas de fondo se ejecuten de forma fiable, configura un cron del sistema en lugar del AJAX por defecto:

```bash
sudo crontab -u www-data -e
```

Anade esta linea:

```cron
*/5 * * * * php -f /var/www/nextcloud/cron.php
```

Despues, en **Configuracion > Administracion > Ajustes basicos**, selecciona **Cron** como metodo de tareas en segundo plano.

## Recomendaciones finales

- **HTTPS**: configura un certificado SSL con Let's Encrypt usando `certbot`. Nunca expongas Nextcloud sin cifrado.
- **Firewall**: abre unicamente los puertos 80 y 443. Bloquea todo lo demas.
- **Actualizaciones**: revisa las actualizaciones periodicamente desde el panel de administracion o con `sudo -u www-data php /var/www/nextcloud/updater/updater.phar`.
- **Backups**: programa copias de seguridad del directorio de datos y de la base de datos con `mysqldump`.

Con Nextcloud funcionando, tienes tu propia nube privada donde tus archivos, calendarios y contactos permanecen bajo tu control total.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
