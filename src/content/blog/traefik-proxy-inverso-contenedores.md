---
title: 'Traefik: proxy inverso para contenedores'
description: "Traefik detecta tus contenedores Docker automáticamente y les da HTTPS con Let's Encrypt vía labels, sin tocar un fichero de configuración."
author: 'antonio'
pubDate: 2026-08-03
updatedDate: 2026-08-07
category: 'Redes'
tags: ['Traefik', 'Proxy', 'Redes', 'Docker']
image: '../../assets/images/redes-traefik.jpg'
draft: false
---

Traefik es un proxy inverso pensado desde el origen para entornos con contenedores: en vez de mantener un fichero de configuración por cada servicio como harías con Nginx, Traefik escucha el socket de Docker y descubre automáticamente qué contenedores existen, a qué dominio deben responder y si necesitan certificado TLS — toda esa configuración vive como _labels_ en el propio contenedor.

## Traefik vs configurar Nginx a mano

Si ya sigues la guía de [proxy inverso con Nginx](/blog/proxy-inverso-nginx-guia-practica/), conoces el modelo tradicional: un `server {}` por dominio, recarga manual de configuración cada vez que añades o quitas un servicio, y gestión de certificados aparte con Certbot. Traefik invierte ese flujo:

- **Nginx:** la configuración vive centralizada en ficheros que tú mantienes; añadir un servicio nuevo implica editar y recargar Nginx.
- **Traefik:** la configuración vive distribuida, junto a cada servicio, como labels de su propio contenedor; añadir un servicio nuevo es lanzar el contenedor con las labels correctas — Traefik lo detecta solo, sin reiniciar nada.

Ninguno sustituye al otro en todos los casos: Nginx sigue siendo la opción más simple para un puñado de sitios estáticos que casi nunca cambian; Traefik gana claramente cuando tienes muchos contenedores que se crean y destruyen con frecuencia (staging dinámico, homelabs con varios stacks de Docker Compose). Si lo que buscas es ese mismo descubrimiento automático pero con una configuración más simple que la de Traefik, échale un ojo a [Caddy](/blog/caddy-proxy-inverso-https-automatico/), que también gestiona certificados HTTPS solo.

## Arquitectura: entryPoints, routers y services

Traefik organiza el tráfico en tres piezas:

```
Cliente HTTPS
   │
   ▼
Traefik — entryPoints (puertos que escucha: web:80, websecure:443)
   │
   ├── router "whoami"   Host(`whoami.tudominio.com`) → service whoami
   └── router "app"      Host(`app.tudominio.com`)    → service app
```

- **entryPoint:** el puerto por el que Traefik escucha tráfico entrante (`web` para HTTP, `websecure` para HTTPS).
- **router:** una regla que decide, según el dominio o la ruta de la petición, a qué servicio enviarla.
- **service:** el destino final — normalmente un contenedor Docker, resuelto automáticamente por su nombre e IP interna.

Cada router y cada service se declaran como labels en el contenedor correspondiente; Traefik los recompone en tiempo real leyendo el socket de Docker.

## docker-compose.yml con HTTPS automático

Este ejemplo levanta Traefik con el reto HTTP de Let's Encrypt (`httpChallenge`) — Traefik responde a la validación de dominio directamente en el puerto 80, sin necesitar acceso a la API del proveedor DNS:

```yaml
# docker-compose.yml
services:
  traefik:
    image: 'traefik:v3.3'
    container_name: 'traefik'
    command:
      - '--providers.docker=true'
      - '--providers.docker.exposedbydefault=false'
      - '--entryPoints.web.address=:80'
      - '--entryPoints.websecure.address=:443'
      - '--certificatesresolvers.myresolver.acme.httpchallenge=true'
      - '--certificatesresolvers.myresolver.acme.httpchallenge.entrypoint=web'
      - '--certificatesresolvers.myresolver.acme.email=tu-email@tudominio.com'
      - '--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json'
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - './letsencrypt:/letsencrypt'
      - '/var/run/docker.sock:/var/run/docker.sock:ro'

  whoami:
    image: 'traefik/whoami'
    container_name: 'whoami'
    labels:
      - 'traefik.enable=true'
      - 'traefik.http.routers.whoami.rule=Host(`whoami.tudominio.com`)'
      - 'traefik.http.routers.whoami.entrypoints=websecure'
      - 'traefik.http.routers.whoami.tls.certresolver=myresolver'
```

```bash
docker compose up -d
```

En cuanto el contenedor `whoami` arranca, Traefik lee sus labels, crea el router `whoami` con la regla `Host()`, resuelve el certificado contra Let's Encrypt usando el `certresolver` llamado `myresolver` y empieza a servir tráfico HTTPS en `websecure` — sin tocar ningún fichero fuera del propio `docker-compose.yml`. Si ya conoces el proceso manual de validación ACME, la lógica es la misma que ves en la guía de [Certbot y Let's Encrypt](/blog/certificados-ssl-certbot-lets-encrypt/): Traefik automatiza exactamente ese reto HTTP-01 por ti.

> [!IMPORTANT]
> `--providers.docker.exposedbydefault=false` es la opción segura por defecto: sin ella, Traefik expondría automáticamente **cualquier** contenedor Docker del host a internet en cuanto arrancara, tenga o no labels de Traefik. Con `exposedbydefault=false`, un contenedor solo se publica si lleva explícitamente `traefik.enable=true`.

## Añadir un segundo servicio

Cada aplicación nueva solo necesita sus propias labels — no hay que editar la configuración de Traefik para nada. Añádela como un servicio más dentro del mismo `docker-compose.yml`:

```yaml
# dentro del bloque "services:" del docker-compose.yml
app:
  image: 'mi-app:latest'
  container_name: 'app'
  labels:
    - 'traefik.enable=true'
    - 'traefik.http.routers.app.rule=Host(`app.tudominio.com`)'
    - 'traefik.http.routers.app.entrypoints=websecure'
    - 'traefik.http.routers.app.tls.certresolver=myresolver'
    - 'traefik.http.services.app.loadbalancer.server.port=8080'
```

La última label es necesaria cuando el contenedor expone más de un puerto o el puerto interno no es el estándar (80): le dice a Traefik contra qué puerto del contenedor debe balancear, ya que Traefik no puede adivinarlo si hay ambigüedad.

## Middleware: encadenar redirects, autenticación y límite de peticiones

Un middleware es un paso de procesamiento que Traefik aplica a una petición antes de que llegue al servicio final — redirigir, exigir credenciales, limitar la tasa de peticiones. Se declaran como labels igual que routers y services, y se enganchan a un router con `traefik.http.routers.<nombre>.middlewares=`.

**Redirigir HTTP a HTTPS.** El ejemplo inicial de este artículo solo abre un router en `websecure`; si el mismo dominio también escucha en `web` (puerto 80), conviene redirigir en vez de servir HTTP en plano:

```yaml
labels:
  - 'traefik.http.middlewares.redirect-https.redirectscheme.scheme=https'
  - 'traefik.http.routers.whoami-http.rule=Host(`whoami.tudominio.com`)'
  - 'traefik.http.routers.whoami-http.entrypoints=web'
  - 'traefik.http.routers.whoami-http.middlewares=redirect-https'
```

**Autenticación básica**, útil para proteger paneles internos (como el propio dashboard de Traefik, más abajo). El hash de la contraseña se genera con `htpasswd` y, dentro de un `docker-compose.yml`, cada `$` literal hay que escaparlo duplicándolo (`$$`) porque Compose interpreta `$` como inicio de variable:

```bash
sudo apt install -y apache2-utils
htpasswd -nb admin 'contraseña-segura'
# admin:$apr1$H6uV#####...
```

```yaml
labels:
  - 'traefik.http.middlewares.panel-auth.basicauth.users=admin:$$apr1$$H6uV#####...'
  - 'traefik.http.routers.dashboard.middlewares=panel-auth'
```

**Límite de peticiones**, para amortiguar picos de tráfico o abuso contra un servicio concreto — `average` es peticiones por segundo sostenidas y `burst` el margen de ráfaga permitido por encima de esa media:

```yaml
labels:
  - 'traefik.http.middlewares.app-ratelimit.ratelimit.average=100'
  - 'traefik.http.middlewares.app-ratelimit.ratelimit.burst=50'
```

Varios middleware se encadenan en la misma label separándolos por comas — Traefik los aplica en el orden en que aparecen:

```yaml
labels:
  - 'traefik.http.routers.app.middlewares=redirect-https,app-ratelimit'
```

## El socket de Docker y el dashboard

Montar `/var/run/docker.sock` dentro del contenedor de Traefik es lo que le permite descubrir servicios automáticamente, pero ese socket equivale a acceso root sobre el host: cualquier proceso que pueda hablar con él puede lanzar contenedores privilegiados. Móntalo siempre en modo solo lectura (`:ro`, como en el ejemplo) y, si tu superficie de exposición te preocupa, evalúa un proxy de socket como `docker-socket-proxy` que solo reexpone los endpoints de la API que Traefik necesita.

> [!CAUTION]
> El dashboard de Traefik (`--api.insecure=true` en la documentación oficial) publica el panel de administración sin autenticación en el puerto 8080. Es útil para probar en local, pero **no lo actives así en un servidor expuesto a internet** — quita esa flag en producción o protégela detrás de autenticación básica con sus propias labels de router.

## Certificados wildcard con el reto DNS-01

El `httpChallenge` del primer ejemplo exige que Traefik pueda responder en el puerto 80 desde fuera — no sirve si el servidor está detrás de un NAT sin ese puerto abierto, o si necesitas un certificado wildcard (`*.tudominio.com`), porque Let's Encrypt solo emite wildcards contra el reto DNS-01. En ese reto, en vez de responder una petición HTTP, Traefik demuestra que controla el dominio creando un registro TXT en su zona DNS a través de la API del proveedor.

Con Cloudflare como proveedor, basta con un token de API con permiso `Zone.DNS: Edit` (no uses la API key global, que da acceso a toda la cuenta) pasado como variable de entorno al contenedor:

```yaml
# docker-compose.yml
services:
  traefik:
    image: 'traefik:v3.3'
    environment:
      - 'CF_API_EMAIL=tu-email@tudominio.com'
      - 'CF_DNS_API_TOKEN=tu-token-de-api-de-cloudflare'
    command:
      - '--providers.docker=true'
      - '--entryPoints.websecure.address=:443'
      - '--certificatesresolvers.myresolver.acme.dnschallenge=true'
      - '--certificatesresolvers.myresolver.acme.dnschallenge.provider=cloudflare'
      - '--certificatesresolvers.myresolver.acme.email=tu-email@tudominio.com'
      - '--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json'
```

Y para pedir el propio certificado wildcard, el router declara el dominio principal y el patrón `sans` (nombres alternativos) en vez de depender solo de la regla `Host()`:

```yaml
labels:
  - 'traefik.http.routers.app.tls.certresolver=myresolver'
  - 'traefik.http.routers.app.tls.domains[0].main=tudominio.com'
  - 'traefik.http.routers.app.tls.domains[0].sans=*.tudominio.com'
```

Es el mismo reto DNS-01 que documentamos con más detalle a nivel de proveedor en la guía de [Certbot y Let's Encrypt](/blog/certificados-ssl-certbot-lets-encrypt/) — aquí Traefik automatiza la parte de crear y limpiar el registro TXT en cada renovación, sin plugin ni cron aparte.

## Traefik vs Caddy vs Nginx: cuándo elegir cada uno

Los tres resuelven el mismo problema (poner HTTPS delante de tus servicios) con automatizaciones distintas. Traefik gana con claridad cuando la infraestructura ya vive en contenedores que se crean y destruyen a menudo — homelabs con varios stacks de Compose, entornos de staging dinámicos — porque el auto-discovery vía socket de Docker significa que nunca tocas la configuración de Traefik en sí, solo las labels del contenedor nuevo. Si en cambio manejas un puñado de dominios estáticos fuera de Docker que casi nunca cambian, [Caddy](/blog/caddy-proxy-inverso-https-automatico/) llega al mismo HTTPS automático con muchas menos piezas moviéndose (un Caddyfile de texto plano, sin proveedor de Docker ni resolvers que declarar). Nginx sigue siendo la opción con más control fino sobre cada detalle si ya lo dominas y no te importa gestionar Certbot como pieza aparte, como se ve en la [guía de proxy inverso con Nginx](/blog/proxy-inverso-nginx-guia-practica/).

## Solución de problemas comunes

- **El dashboard no responde.** Además de activar `--api.dashboard=true` en el comando de Traefik, hace falta un router propio que apunte al servicio interno especial `api@internal` — no basta con exponer el puerto 8080 del contenedor si no hay un router declarado para él.
- **El certificado no se emite.** Antes de sospechar de Traefik, comprueba que el registro DNS del dominio ya apunta a la IP pública del servidor (`dig +short tudominio.com`) y que el puerto usado por el challenge es accesible desde fuera. Si vas a probar varias veces seguidas, apunta temporalmente al entorno de pruebas de Let's Encrypt (`--certificatesresolvers.myresolver.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory`) para no toparte con el límite de 5 certificados fallidos por hora del entorno de producción.
- **Un contenedor no aparece en ningún router.** La causa más común es olvidar la label `traefik.enable=true` con `exposedbydefault=false` activo (visto más arriba). La segunda causa más común es que el contenedor no esté en la misma red de Docker que Traefik — si usas una red externa nombrada, tanto Traefik como el servicio deben declararla explícitamente con `networks:` en el `docker-compose.yml`, o Traefik no puede resolver su IP interna aunque las labels estén bien escritas.

## Siguiente paso

Con Traefik gestionando la capa de entrada, el siguiente paso natural es meter bajo su paraguas el resto de servicios que hayas montado siguiendo otras guías del blog — por ejemplo, poner detrás de Traefik la guía de [Docker en Linux](/blog/docker-guia-practica-contenedores-linux/) para cualquier stack de Compose que ya tengas corriendo, en vez de exponer cada uno con su propio puerto directo al host.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
