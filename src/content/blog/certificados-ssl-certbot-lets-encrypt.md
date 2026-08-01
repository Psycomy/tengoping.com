---
title: "Certificados SSL gratis con Certbot y Let's Encrypt"
description: 'Cómo funciona la validación ACME, cuándo usar HTTP-01 o DNS-01, cómo emitir certificados wildcard y cómo funciona la renovación automática de Certbot.'
author: 'antonio'
pubDate: 2026-07-27
category: 'Seguridad'
tags: ['SSL', 'Certbot', "Let's Encrypt", 'HTTPS']
image: '../../assets/images/certbot-ssl.jpg'
draft: false
---

Let's Encrypt es una autoridad de certificación gratuita que emite certificados SSL/TLS validados automáticamente mediante el protocolo ACME, y Certbot es su cliente oficial para gestionarlos desde línea de comandos. Ya vimos en el post de [proxy inverso con Nginx](/blog/proxy-inverso-nginx-guia-practica/) cómo activar HTTPS con un único comando (`certbot --nginx`), pero ese comando esconde decisiones importantes: qué tipo de validación usa, si puedes emitir certificados wildcard, y cómo funciona realmente la renovación automática. Este artículo entra en esas decisiones.

## Cómo funciona la validación ACME

Antes de emitir un certificado, Let's Encrypt necesita comprobar que controlas el dominio para el que lo pides. Este proceso se llama validación ACME y tiene dos variantes principales:

### HTTP-01

Certbot recibe un token de Let's Encrypt y lo publica en un fichero accesible en `http://tu-dominio/.well-known/acme-challenge/<TOKEN>`. Let's Encrypt intenta descargar ese fichero desde varias ubicaciones distintas; si lo encuentra, da por validado el dominio.

- Solo funciona por el **puerto 80** (HTTP, no HTTPS)
- Es el método más simple de configurar
- **No puede emitir certificados wildcard** — esta es su limitación principal

### DNS-01

Certbot crea un registro TXT en `_acme-challenge.tu-dominio` con un valor derivado del token. Let's Encrypt consulta el DNS público y, si encuentra el registro, valida el dominio.

- Requiere acceso a la gestión del DNS (vía API de tu proveedor, o manualmente)
- Funciona aunque el servidor no sea accesible desde internet (útil para servidores internos)
- **Es el único método que permite emitir certificados wildcard** — HTTP-01 no puede, porque no hay forma de demostrar control sobre todos los subdominios posibles con un único fichero HTTP

La elección no es solo de preferencia: si necesitas un wildcard, DNS-01 es obligatorio.

## Certificados wildcard

Un certificado wildcard (`*.tudominio.com`) cubre todos los subdominios de primer nivel con un único certificado, en lugar de emitir uno por cada subdominio. Es útil si gestionas muchos subdominios (`app.`, `api.`, `mail.`, etc.) y quieres simplificar la gestión de certificados.

Para emitirlo necesitas un plugin DNS de Certbot específico de tu proveedor (Certbot soporta oficialmente más de 50), por ejemplo para Cloudflare:

```bash
sudo apt install certbot python3-certbot-dns-cloudflare
```

Crea un fichero de credenciales con permisos restringidos:

```bash
sudo mkdir -p /etc/certbot
sudo tee /etc/certbot/cloudflare.ini > /dev/null <<EOF
dns_cloudflare_api_token = tu_token_de_api
EOF
sudo chmod 600 /etc/certbot/cloudflare.ini
```

Y emite el certificado:

```bash
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/certbot/cloudflare.ini \
  -d "tudominio.com" -d "*.tudominio.com"
```

Si tu proveedor de DNS no tiene plugin oficial, puedes usar el modo `--manual`, que te pedirá crear el registro TXT a mano — funciona, pero no es apto para renovación automática sin intervención.

## Modos de emisión: standalone, webroot y plugin de Nginx

Certbot puede obtener el certificado de tres formas distintas, según cómo quieras que gestione el servidor web:

- **Plugin de Nginx/Apache** (`--nginx` / `--apache`): Certbot edita automáticamente la configuración del servidor web para servir el challenge y activar HTTPS. Es el método más cómodo si ya tienes Nginx corriendo, como se vio en el post de proxy inverso.
- **Webroot** (`--webroot -w /ruta/al/sitio`): Certbot coloca el fichero de challenge directamente en el directorio que sirve tu servidor web, sin modificar su configuración. Útil si prefieres gestionar tú mismo los bloques `server` de Nginx.
- **Standalone** (`--standalone`): Certbot levanta su propio servidor web temporal para responder al challenge. Requiere que el puerto 80 (o 443) esté libre en ese momento, así que no puedes usarlo si ya tienes Nginx u otro servicio escuchando ahí — tendrías que pararlo primero, lo que provoca downtime.

Para la mayoría de servidores con Nginx ya en marcha, el plugin de Nginx o webroot son las opciones sin downtime; standalone tiene sentido sobre todo en servidores sin un servidor web previo.

## Renovación automática: qué pasa realmente

La instalación de Certbot desde los paquetes oficiales configura un timer de systemd (o una entrada de cron, según la distribución) que ejecuta `certbot renew` **dos veces al día**. Esto no significa que renueve el certificado dos veces al día: `certbot renew` solo actúa sobre certificados que estén realmente cerca de caducar.

Desde Certbot 4.0, un certificado se considera listo para renovar cuando queda **menos de un tercio de su periodo de validez**. Para certificados muy cortos (10 días o menos), el umbral es la mitad de su vida útil.

Puedes comprobar que la renovación automática funcionará sin arriesgar tus certificados de producción usando el entorno de pruebas (staging) de Let's Encrypt:

```bash
sudo certbot renew --dry-run
```

Este comando simula el proceso completo de renovación contra el servidor de staging de Let's Encrypt, que emite certificados de prueba no válidos (no cuentan para los límites de tasa de producción).

## Cuánto duran los certificados (y por qué está cambiando)

El perfil clásico de Let's Encrypt sigue emitiendo certificados válidos **90 días**, pero el panorama está cambiando activamente:

- Desde enero de 2026, Let's Encrypt ofrece certificados de **6 días** (144 horas) como opción, pensados para infraestructuras con renovación totalmente automatizada. Es opt-in, seleccionando el perfil `shortlived` en el cliente ACME.
- El perfil `tlsserver` pasó a emitir certificados de **45 días** en mayo de 2026.
- Está previsto que el perfil clásico (el que usa Certbot por defecto si no indicas perfil) pase a certificados de **64 días** en febrero de 2027.

Para la inmensa mayoría de instalaciones con renovación automática ya funcionando (el timer de systemd que revisa dos veces al día), estos cambios no requieren ninguna acción — simplemente los certificados se renovarán con más frecuencia. Solo importa si tienes procesos manuales o sistemas que asumen una validez fija de 90 días.

## Límites de emisión (rate limits)

Let's Encrypt aplica límites para evitar abuso, y es fácil toparse con ellos si pruebas configuraciones en producción:

- **50 certificados por dominio registrado cada 7 días** (se recarga aproximadamente uno cada 202 minutos)
- **5 certificados con el mismo conjunto exacto de nombres cada 7 días** — este es el límite que más rápido se agota si repites pruebas con el mismo dominio
- **5 fallos de validación por nombre de dominio cada hora**

Por eso conviene probar siempre primero con `--dry-run` o añadiendo `--test-cert` (que usa el entorno de staging), y reservar las peticiones reales para cuando la configuración ya funciona.

## Siguiente paso

Con esto tienes criterio para elegir el tipo de validación correcto (HTTP-01 para dominios simples accesibles públicamente, DNS-01 si necesitas wildcards o el servidor no es accesible desde fuera), el modo de emisión que mejor encaja con tu servidor web, y entiendes qué hace realmente la renovación automática por debajo. El siguiente paso natural es automatizar la emisión de certificados en infraestructura como código (por ejemplo, integrando Certbot en tus playbooks de [Ansible](/blog/automatizar-servidores-ansible-primeros-pasos/)) si gestionas varios servidores.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
