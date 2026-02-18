---
title: 'Proxy inverso con Nginx: guía práctica'
description: 'Aprende a configurar Nginx como proxy inverso para redirigir tráfico a tus aplicaciones internas con HTTPS, cabeceras y balanceo de carga.'
author: 'antonio'
pubDate: 2025-01-28
category: 'Redes'
tags: ['Nginx', 'Proxy', 'Redes', 'Sysadmin']
image: '../../assets/images/redes-proxy.jpg'
draft: false
---

## Qué es un proxy inverso

Un proxy inverso recibe las peticiones de los clientes y las reenvía al servidor interno correspondiente. El cliente nunca se conecta directamente al backend. Esto permite centralizar HTTPS, añadir cabeceras de seguridad, cachear contenido y distribuir carga.

## Instalación

```bash
# RHEL / Oracle Linux / Rocky
sudo dnf install nginx

# Debian / Ubuntu
sudo apt install nginx
```

```bash
sudo systemctl enable --now nginx
```

## Configuración básica

Un proxy que redirige todo el tráfico de un dominio a una aplicación interna en el puerto 3000:

```nginx
server {
    listen 80;
    server_name app.ejemplo.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Las cabeceras `X-Real-IP` y `X-Forwarded-For` permiten que la aplicación conozca la IP real del cliente en lugar de ver siempre `127.0.0.1`.

## Añadir HTTPS con Let's Encrypt

```bash
sudo dnf install certbot python3-certbot-nginx
sudo certbot --nginx -d app.ejemplo.com
```

Certbot modifica automáticamente la configuración de Nginx para escuchar en el puerto 443 y redirigir el tráfico HTTP a HTTPS.

Para renovar automáticamente:

```bash
sudo systemctl enable --now certbot-renew.timer
```

## Múltiples aplicaciones en un servidor

```nginx
# App principal
server {
    listen 443 ssl;
    server_name app.ejemplo.com;
    ssl_certificate /etc/letsencrypt/live/app.ejemplo.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.ejemplo.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API
server {
    listen 443 ssl;
    server_name api.ejemplo.com;
    ssl_certificate /etc/letsencrypt/live/api.ejemplo.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.ejemplo.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Balanceo de carga

Si tienes varios backends para la misma aplicación:

```nginx
upstream backend_app {
    server 192.168.1.10:3000;
    server 192.168.1.11:3000;
    server 192.168.1.12:3000 backup;
}

server {
    listen 443 ssl;
    server_name app.ejemplo.com;

    location / {
        proxy_pass http://backend_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

El tercer servidor con `backup` solo recibe tráfico si los dos primeros están caídos.

## Cabeceras de seguridad

Añade estas cabeceras a nivel global o por servidor:

```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

## WebSockets

Si tu aplicación usa WebSockets, necesitas pasar las cabeceras de upgrade:

```nginx
location /ws {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

## Verificar la configuración

Siempre antes de reiniciar:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Conclusión

Nginx como proxy inverso es el estándar para exponer aplicaciones internas de forma segura. Con HTTPS centralizado, cabeceras de seguridad y balanceo de carga, un solo Nginx puede gestionar decenas de servicios internos sin que cada uno tenga que preocuparse por certificados o seguridad a nivel de transporte.
