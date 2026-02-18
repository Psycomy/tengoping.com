---
title: 'Monitorizar servicios web con Uptime Kuma'
description: 'Despliega Uptime Kuma con Docker para monitorizar la disponibilidad de tus servicios web: checks HTTP, TCP, ping, notificaciones y dashboard en tiempo real.'
author: 'antonio'
pubDate: 2026-02-16
category: 'Monitorización'
tags: ['uptime-kuma', 'monitoring', 'self-hosting', 'disponibilidad']
image: '../../assets/images/mon-uptimekuma.jpg'
draft: false
---

## Por qué necesitas monitorizar tus servicios

Si administras servidores, sabes que la pregunta no es si algo va a caer, sino cuándo. Un servicio web puede dejar de responder por mil razones: un certificado SSL que expira, un disco que se llena, un proceso que consume toda la RAM o simplemente un proveedor de hosting que tiene un mal día.

El problema real no es la caída en sí, sino enterarte tarde. Cada minuto que tu servicio está fuera de línea sin que lo sepas es un minuto que erosiona la confianza de tus usuarios, incumple tus SLAs y potencialmente te cuesta dinero. La diferencia entre un sysadmin reactivo y uno proactivo está precisamente ahí: en tener un sistema que te avise antes de que lo haga un usuario enfadado.

Existen soluciones comerciales de sobra (UptimeRobot, Pingdom, Datadog), pero si prefieres mantener el control total de tus datos, no depender de terceros y no pagar suscripciones mensuales, la alternativa self-hosted más popular y con razón es **Uptime Kuma**.

## Qué es Uptime Kuma

Uptime Kuma es una herramienta de monitorización de disponibilidad open source, escrita en Node.js, con una interfaz web moderna y ligera. Piensa en ella como tu propio UptimeRobot, pero corriendo en tu infraestructura.

Sus características principales incluyen:

- **Múltiples tipos de monitorización**: HTTP(S), TCP, ping (ICMP), DNS, Docker, Steam Game Server, MQTT y más.
- **Notificaciones a más de 90 servicios**: Telegram, Slack, Discord, email SMTP, webhooks, Gotify, Ntfy, Pushover, entre otros.
- **Páginas de estado públicas**: genera status pages que puedes compartir con tus usuarios o clientes.
- **Ventanas de mantenimiento**: programa periodos donde las alertas se silencian automáticamente.
- **Certificados SSL**: monitoriza la expiración de certificados y te avisa con antelación.
- **Dashboard en tiempo real**: gráficos de latencia, historial de disponibilidad y tiempos de respuesta.

Todo esto con una instalación que ocupa menos de 200 MB de RAM en reposo y se despliega en un minuto con Docker.

## Requisitos previos

Antes de empezar, asegúrate de tener lo siguiente:

- **Docker y Docker Compose** instalados en tu servidor. Si aún no los tienes, la documentación oficial de Docker cubre la instalación para cualquier distribución.
- **Un servidor con acceso a la red** desde el que quieras monitorizar. Puede ser un VPS barato, una Raspberry Pi o cualquier máquina con conectividad estable.
- **Conocimientos básicos de redes**: saber qué es un puerto, una petición HTTP y cómo funciona DNS te ayudará a configurar los monitores.
- **Un dominio** (opcional pero recomendado) si quieres acceder a la interfaz a través de un nombre en lugar de una IP, o si planeas exponer las páginas de estado públicamente.

## Instalación con Docker Compose

La forma más limpia de desplegar Uptime Kuma es con Docker Compose. Crea un directorio para el proyecto y dentro el archivo de configuración:

```bash
mkdir -p /opt/uptime-kuma && cd /opt/uptime-kuma
```

Crea el archivo `docker-compose.yml` con el siguiente contenido:

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:1
    container_name: uptime-kuma
    restart: unless-stopped
    ports:
      - '3001:3001'
    volumes:
      - ./data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - TZ=Europe/Madrid
```

Algunos detalles sobre esta configuración:

- **`image: louislam/uptime-kuma:1`**: usa la etiqueta `1` en lugar de `latest` para recibir actualizaciones menores automáticamente pero evitar saltos de versión mayor inesperados.
- **`/var/run/docker.sock`**: montar el socket de Docker en modo lectura (`:ro`) permite monitorizar contenedores Docker directamente. Si no lo necesitas, puedes omitir esa línea.
- **`./data`**: aquí se almacena la base de datos SQLite con toda tu configuración, historial y monitores. Es lo único que necesitas respaldar.
- **`TZ`**: ajusta la zona horaria para que los logs y gráficos muestren la hora correcta.

Levanta el servicio:

```bash
docker compose up -d
```

Accede a `http://tu-servidor:3001` y verás la pantalla de configuración inicial donde crearás tu usuario administrador. Elige una contraseña fuerte: esta interfaz no debería estar expuesta a internet sin autenticación adicional.

### Detrás de un proxy inverso

En producción, lo habitual es colocar Uptime Kuma detrás de un proxy inverso como Nginx, Caddy o Traefik para gestionar HTTPS. Si usas Nginx, una configuración básica sería:

```bash
server {
    listen 443 ssl http2;
    server_name monitor.tudominio.com;

    ssl_certificate     /etc/letsencrypt/live/monitor.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/monitor.tudominio.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Las cabeceras `Upgrade` y `Connection` son esenciales porque Uptime Kuma usa WebSockets para las actualizaciones en tiempo real del dashboard.

## Configurar monitores

Una vez dentro de la interfaz, haz clic en **Add New Monitor** para crear tu primer monitor. Vamos a ver los tipos más útiles.

### Monitor HTTP(S)

El más común. Comprueba que una URL devuelve un código de estado esperado.

- **URL**: la dirección completa, por ejemplo `https://tudominio.com`.
- **Heartbeat Interval**: cada cuántos segundos se realiza la comprobación. 60 segundos es un buen punto de partida.
- **Retries**: cuántas veces reintentar antes de marcar como caído. Pon al menos 2 para evitar falsos positivos por picos de red.
- **Accepted Status Codes**: por defecto acepta `200-299`. Si tu endpoint redirige, puedes añadir `301` o `302`.
- **Max Redirects**: si quieres seguir redirecciones automáticamente.
- **Certificate Expiry Notification**: actívalo y configura cuántos días antes de la expiración quieres recibir el aviso. 14 días es razonable.

### Monitor TCP

Útil para comprobar que un puerto está abierto y aceptando conexiones, sin importar el protocolo de aplicación.

- **Hostname**: la IP o dominio del servidor.
- **Port**: el puerto a comprobar (por ejemplo, 3306 para MySQL, 5432 para PostgreSQL, 6379 para Redis).

Es perfecto para bases de datos, colas de mensajes o cualquier servicio que no exponga un endpoint HTTP.

### Monitor Ping (ICMP)

Comprueba la conectividad básica a nivel de red. No verifica que el servicio esté funcionando, solo que el host responde.

- **Hostname**: IP o dominio del host.

Es el monitor más ligero y sirve como primera línea de detección: si el ping falla, todo lo demás también estará caído.

### Monitor DNS

Verifica que un registro DNS resuelve correctamente al valor esperado. Útil para detectar cambios no autorizados o propagaciones incompletas.

### Monitor Docker

Si montaste el socket de Docker, puedes monitorizar directamente el estado de tus contenedores. Selecciona el tipo **Docker Container**, elige el contenedor de la lista y Uptime Kuma comprobará que está en estado `running`.

## Configurar notificaciones

De nada sirve monitorizar si no te enteras cuando algo falla. Ve a **Settings > Notifications** para configurar los canales de alerta.

### Telegram

Probablemente la opción más popular entre sysadmins. Necesitas:

1. Crear un bot con **@BotFather** en Telegram y copiar el token.
2. Obtener tu **Chat ID** (puedes enviarte un mensaje al bot y consultar la API `getUpdates`, o usar bots como @userinfobot).
3. En Uptime Kuma, añade una notificación de tipo **Telegram**, pega el token y el Chat ID, y haz clic en **Test** para verificar.

### Email (SMTP)

Configura los datos de tu servidor SMTP:

- **SMTP Host**: por ejemplo `smtp.gmail.com` o tu propio servidor de correo.
- **SMTP Port**: 587 para STARTTLS o 465 para SSL.
- **Sender / Recipient**: dirección de origen y destino.
- **Username / Password**: credenciales de autenticación.

Si usas Gmail, necesitarás una contraseña de aplicación, no tu contraseña habitual.

### Slack

Crea un **Incoming Webhook** en tu workspace de Slack, copia la URL del webhook y pégala en la configuración de notificación de Uptime Kuma. Así de sencillo.

### Webhook genérico

Si ninguna de las integraciones predefinidas se ajusta a tu caso, el tipo **Webhook** te permite enviar un POST con un payload JSON personalizable a cualquier URL. Esto te permite integrarlo con sistemas de ticketing, plataformas de automatización como n8n o cualquier API que acepte peticiones HTTP.

Lo recomendable es configurar al menos dos canales de notificación distintos (por ejemplo, Telegram y email). Si uno falla, el otro te cubre.

## Páginas de estado

Una de las funciones más útiles de Uptime Kuma es la capacidad de crear **status pages** públicas. Estas páginas muestran el estado actual y el historial de disponibilidad de los servicios que elijas, sin revelar detalles internos de tu infraestructura.

Para crear una, ve a **Status Pages** en el menú lateral:

1. Dale un nombre y un slug (por ejemplo, `status` para que sea accesible en `/status`).
2. Añade los monitores que quieras mostrar, organizados en grupos.
3. Personaliza el título, la descripción y opcionalmente un CSS personalizado.
4. Publica la página y comparte la URL con tus usuarios.

Esto es especialmente valioso si ofreces servicios a terceros. En lugar de responder manualmente a cada consulta del tipo "¿está caído el servicio?", simplemente apuntas a la status page.

## Ventanas de mantenimiento

Cuando vas a realizar mantenimiento programado (actualizaciones, migraciones, reinicio de servicios), no quieres que Uptime Kuma te bombardee con alertas. Para eso existen las **Maintenance Windows**.

Ve a **Maintenance** en el menú y crea una nueva ventana:

- **Título**: describe brevemente el mantenimiento.
- **Afecta a**: selecciona los monitores que se verán afectados.
- **Programación**: define si es puntual o recurrente (por ejemplo, todos los domingos a las 04:00).
- **Duración**: cuánto tiempo durará.

Durante la ventana de mantenimiento, los monitores afectados se pausan automáticamente y la status page muestra un aviso de mantenimiento en lugar de una caída.

## Buenas prácticas

Después de monitorizar servicios durante un tiempo, estas son las lecciones que más se repiten:

- **No monitorices solo desde un punto**. Si tu servidor de monitorización está en la misma red que tus servicios, no detectarás problemas de conectividad externa. Considera tener una segunda instancia de Uptime Kuma en otro proveedor o región.
- **Ajusta los intervalos con criterio**. No todo necesita comprobarse cada 30 segundos. Para servicios críticos, 60 segundos está bien. Para servicios internos o secundarios, 300 segundos es suficiente. Intervalos demasiado agresivos generan ruido y consumen recursos innecesarios.
- **Usa grupos y etiquetas**. Cuando tengas más de 20 monitores, la organización importa. Agrúpalos por entorno (producción, staging), por tipo (web, base de datos, API) o por cliente.
- **Haz backup del volumen de datos**. Toda la configuración de Uptime Kuma vive en el directorio `./data` que montaste como volumen. Un simple `tar` periódico o una copia con `rsync` te salvará de un desastre.
- **Configura retries antes de alertar**. Un solo fallo no significa que el servicio esté caído. Configura al menos 2-3 reintentos para evitar que un paquete perdido te despierte a las 3 de la mañana.
- **Monitoriza los certificados SSL**. Las caídas por certificado expirado son vergonzosamente comunes y completamente evitables. Activa la alerta de expiración con al menos 14 días de margen.
- **Revisa el dashboard regularmente**. No te limites a esperar alertas. Revisa los gráficos de latencia periódicamente: un aumento gradual en los tiempos de respuesta suele preceder a una caída.

## Actualizar Uptime Kuma

Mantener la herramienta actualizada es sencillo con Docker:

```bash
cd /opt/uptime-kuma
docker compose pull
docker compose up -d
```

La base de datos se migra automáticamente entre versiones. Aun así, nunca está de más hacer un backup del directorio `data` antes de actualizar.

## Siguiente paso

Con Uptime Kuma tienes cubierta la monitorización de disponibilidad, pero la disponibilidad es solo una parte de la ecuación. El siguiente paso lógico es añadir monitorización de métricas de sistema (CPU, RAM, disco, red) con herramientas como **Prometheus + Grafana** o **Netdata**. Combinando ambos enfoques tendrás visibilidad completa: sabrás no solo si tus servicios están arriba, sino cómo de sanos están por dentro.

Otra línea interesante es integrar Uptime Kuma con tu sistema de gestión de incidentes. Si usas algo como **Grafana OnCall** o **PagerDuty**, puedes encadenar las alertas de Uptime Kuma vía webhook para que se generen incidentes automáticamente con escalado y rotación de guardia.

Sea cual sea tu siguiente movimiento, lo importante es que ya no estás a ciegas. Y eso, en administración de sistemas, marca toda la diferencia.
