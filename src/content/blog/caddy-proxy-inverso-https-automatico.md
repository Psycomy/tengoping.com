---
title: 'Caddy: proxy inverso con HTTPS automático'
description: "Caddy emite y renueva certificados HTTPS automáticamente vía Let's Encrypt sin tocar Certbot: Caddyfile, requisitos y comparativa con Nginx y Traefik."
author: 'antonio'
pubDate: 2026-08-06
category: 'Redes'
tags: ['Caddy', 'Proxy', 'Redes', 'HTTPS']
image: '../../assets/images/redes-caddy.jpg'
draft: false
---

Caddy es un servidor web y proxy inverso escrito en Go cuya característica distintiva es el HTTPS automático: en cuanto declaras un dominio en su configuración, Caddy pide, instala y renueva el certificado TLS por su cuenta contra Let's Encrypt o ZeroSSL, sin que tengas que instalar Certbot ni programar un cron de renovación. Si ya conoces [el proxy inverso con Nginx](/blog/proxy-inverso-nginx-guia-practica/) o [Traefik para contenedores](/blog/traefik-proxy-inverso-contenedores/), la diferencia principal de Caddy no está en el rendimiento ni en las funciones — está en cuánto tienes que configurar para llegar a un sitio funcionando en HTTPS.

## Qué diferencia a Caddy de Nginx y Traefik

Los tres son proxies inversos capaces de servir HTTPS, pero cada uno automatiza una capa distinta:

- **Nginx** no gestiona certificados por sí mismo: necesitas Certbot como pieza aparte, que edita la configuración de Nginx y deja un timer de systemd para renovar. Tú controlas cada detalle, pero son dos herramientas y dos configuraciones que mantener sincronizadas.
- **Traefik** automatiza la emisión de certificados igual que Caddy, pero su punto fuerte real es el descubrimiento de servicios: lee labels de Docker y genera la configuración de enrutado solo, sin que edites ningún fichero. A cambio, ese modelo dinámico tiene más piezas moviéndose (proveedor de Docker, resolvers, entryPoints).
- **Caddy** resuelve el certificado automáticamente igual que Traefik, pero con la configuración estática y explícita de Nginx: un fichero de texto, sin agente de contenedores de por medio salvo que instales un plugin aparte para ello.

En la práctica, si necesitas descubrimiento automático de contenedores Docker, Traefik lo trae de fábrica; Caddy solo lo consigue con un plugin de terceros (`caddy-docker-proxy`, mantenido por la comunidad, no por el proyecto oficial). Donde Caddy gana claramente es en instalaciones sencillas fuera de Docker — un VPS con dos o tres dominios — donde no quieres depender de un plugin externo ni mantener Certbot en paralelo.

## Instalación

Los paquetes oficiales de Caddy están en repositorios propios (Cloudsmith para Debian/Ubuntu, COPR para Fedora/RHEL), no en los repositorios base de la distribución:

```bash
# Debian / Ubuntu
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

```bash
# Fedora
sudo dnf install dnf5-plugins
sudo dnf copr enable @caddy/caddy
sudo dnf install caddy

# RHEL / CentOS Stream
sudo dnf install dnf-plugins-core
sudo dnf copr enable @caddy/caddy
sudo dnf install caddy
```

El paquete Debian/Ubuntu instala y activa el servicio systemd automáticamente, y arranca Caddy escuchando en el puerto 80 con una configuración mínima. El fichero de configuración vive en `/etc/caddy/Caddyfile`.

## Caddyfile básico: tu primer proxy inverso con HTTPS

La sintaxis de un Caddyfile es un bloque por dominio, con las directivas dentro. Para poner una aplicación interna en el puerto 3000 detrás de un dominio propio, con HTTPS incluido, basta con esto:

```caddyfile
app.tudominio.com {
    reverse_proxy localhost:3000
}
```

Nada más. En cuanto reinicias o recargas Caddy con este bloque, detecta que `app.tudominio.com` es un nombre de dominio público (no `localhost` ni una IP) y arranca el proceso de emisión del certificado sin ninguna directiva adicional — no hace falta un bloque `tls` explícito ni instalar nada aparte. Para varios servicios en el mismo servidor, añade un bloque por dominio:

```caddyfile
app.tudominio.com {
    reverse_proxy localhost:3000
}

api.tudominio.com {
    reverse_proxy localhost:8080
}
```

```
Clientes (HTTPS, 443)
   │
   ▼
Caddy — certificado gestionado por dominio, HTTP→HTTPS automático
   │
   ├── app.tudominio.com  → localhost:3000
   └── api.tudominio.com  → localhost:8080
```

Cada dominio obtiene su propio certificado de forma independiente. Si quieres fijar el correo de contacto que se registra en la cuenta ACME (Let's Encrypt lo usa para avisos de caducidad o problemas), va en un bloque de opciones globales al principio del fichero, antes de cualquier bloque de dominio:

```caddyfile
{
    email tu-email@tudominio.com
}

app.tudominio.com {
    reverse_proxy localhost:3000
}
```

## Cómo emite Caddy el certificado sin que hagas nada

Cuando Caddy carga la configuración, recorre cada nombre de dominio declarado y comprueba si ya tiene un certificado válido. Si no lo tiene, arranca una petición ACME contra Let's Encrypt (o ZeroSSL como alternativa si Let's Encrypt falla) usando uno de estos dos retos, habilitados por defecto:

```
1. Caddy detecta "app.tudominio.com" en el Caddyfile sin certificado vigente
   │
   ▼
2. Solicita un certificado a Let's Encrypt vía ACME
   │
   ▼
3. Let's Encrypt exige demostrar control sobre el dominio
   │
   ├── HTTP-01     → Caddy responde el reto en el puerto 80
   └── TLS-ALPN-01 → Caddy responde el reto en el puerto 443 (si el 80 no es accesible)
   │
   ▼
4. Certificado emitido, instalado y servido automáticamente
   │
   ▼
5. Renovación en segundo plano antes de que caduque, sin intervención
```

Si el primer reto falla, Caddy reintenta una vez y después prueba con el siguiente método habilitado; si todos fallan, cambia de autoridad certificadora (de Let's Encrypt a ZeroSSL) y reintenta con retroceso exponencial durante hasta 30 días. Toda esta máquina de estados corre sola: no hay un `certbot renew` que programar ni un timer que verificar, según la documentación oficial de [Automatic HTTPS](https://caddyserver.com/docs/automatic-https).

Para confirmar que el certificado se emitió correctamente, no hace falta esperar a probar el sitio en el navegador: `curl -vI https://app.tudominio.com` muestra la cadena de certificado en la salida, y `journalctl -u caddy -f` (o `docker compose logs -f caddy` si lo corres en contenedor) va mostrando en tiempo real el estado de cada paso ACME mientras Caddy lo procesa.

> [!TIP]
> Si necesitas un certificado wildcard (`*.tudominio.com`) o el servidor no es accesible públicamente por los puertos 80/443, Caddy también soporta el reto DNS-01 configurando un módulo del proveedor DNS — el mismo reto que documentamos con detalle en la guía de [Certbot y Let's Encrypt](/blog/certificados-ssl-certbot-lets-encrypt/), solo que aquí Caddy lo automatiza en lugar de exigirte un plugin y un cron aparte.

## Requisitos para que la emisión automática funcione

> [!IMPORTANT]
> Si te saltas cualquiera de estos tres puntos, la emisión automática de certificado falla silenciosamente y Caddy sirve el sitio solo por HTTP (o con un certificado autofirmado, según el caso) hasta que lo corrijas:
>
> 1. **El registro DNS del dominio (A o AAAA) apunta a la IP pública del servidor** antes de recargar Caddy — si el DNS todavía no ha propagado, el reto ACME no puede verificar el dominio.
> 2. **Los puertos 80 y 443 están abiertos hacia el servidor** desde internet, o redirigidos hacia los puertos internos de Caddy si usa otros distintos. Sin al menos uno de los dos accesible, ningún reto HTTP-01 ni TLS-ALPN-01 puede completarse.
> 3. **El directorio de datos de Caddy es persistente entre reinicios** (por defecto `/var/lib/caddy` en el paquete del sistema, o el volumen `/data` en la imagen Docker) — ahí es donde guarda los certificados y las claves privadas; si se borra, Caddy vuelve a pedir certificados nuevos y puede toparse con los límites de emisión de Let's Encrypt si lo repites demasiadas veces seguidas.

## Varios servicios y balanceo de carga

Igual que Nginx con un bloque `upstream`, `reverse_proxy` acepta varios backends en la misma directiva y reparte tráfico entre ellos:

```caddyfile
app.tudominio.com {
    reverse_proxy node1:8080 node2:8080 node3:8080 {
        lb_policy round_robin
    }
}
```

Otras políticas de balanceo disponibles son `random` (la que usa por defecto si no indicas ninguna), `least_conn` (envía a quien tenga menos conexiones activas) e `ip_hash` (misma IP de cliente siempre al mismo backend, útil si la aplicación no comparte sesión entre nodos). Caddy también soporta comprobaciones de salud activas para sacar automáticamente de la rotación un backend caído:

```caddyfile
app.tudominio.com {
    reverse_proxy node1:8080 node2:8080 node3:8080 {
        lb_policy round_robin
        health_uri /healthz
        health_interval 30s
    }
}
```

## Cabeceras y ajustes habituales

Para pasar la IP real del cliente y otras cabeceras que la aplicación backend necesita, `reverse_proxy` usa `header_up` — y a diferencia de Nginx, Caddy ya envía `X-Forwarded-For`, `X-Forwarded-Proto` y `X-Forwarded-Host` por defecto sin que tengas que declararlas una a una:

```caddyfile
app.tudominio.com {
    reverse_proxy localhost:3000 {
        header_up X-Real-IP {remote_host}
    }
}
```

Para comprimir las respuestas de texto, la directiva `encode` cubre lo que en Nginx serían varias líneas de `gzip`:

```caddyfile
app.tudominio.com {
    encode gzip
    reverse_proxy localhost:3000
}
```

## Aplicar cambios sin cortar el tráfico

Después de editar `/etc/caddy/Caddyfile`, no se recomienda reiniciar el servicio (`restart`), porque eso corta las conexiones activas mientras el proceso vuelve a arrancar. El paquete del sistema expone `reload`, que valida la nueva configuración y la aplica en caliente:

```bash
sudo systemctl reload caddy
```

Por debajo, esto ejecuta `caddy reload --config /etc/caddy/Caddyfile --force`, que aplica el nuevo Caddyfile al proceso en marcha sin interrumpir las conexiones existentes — la forma correcta de recargar según la propia documentación de Caddy, en lugar de parar y arrancar el servicio.

## Caddy con Docker

Si prefieres correr Caddy en un contenedor en lugar del paquete del sistema, la imagen oficial monta el Caddyfile y persiste dos rutas: `/data` (certificados y claves) y `/config`:

```yaml
# docker-compose.yml
services:
  caddy:
    image: 'caddy:2'
    container_name: 'caddy'
    restart: 'unless-stopped'
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - './Caddyfile:/etc/caddy/Caddyfile'
      - 'caddy_data:/data'
      - 'caddy_config:/config'

volumes:
  caddy_data:
  caddy_config:
```

```bash
docker compose up -d
```

> [!WARNING]
> No omitas el volumen `caddy_data`. Si el contenedor se recrea sin él, Caddy pierde los certificados y las claves privadas guardadas y vuelve a pedirlos desde cero en el próximo arranque — con dominios que cambian de contenedor a menudo, esto puede agotar los límites de emisión de Let's Encrypt (50 certificados por dominio registrado cada 7 días).

Este `docker-compose.yml` proxea solo el propio Caddyfile montado como fichero; para exponer contenedores por su nombre DNS interno en la misma red de Docker en lugar de `localhost:puerto`, apunta `reverse_proxy` al nombre del servicio (por ejemplo `reverse_proxy app:3000`) y conecta ambos contenedores a la misma red de Compose.

## Cuándo elegir Caddy y cuándo no

Ningún proxy inverso es la opción correcta en todos los casos:

- Si ya tienes Nginx en producción y te funciona, migrar solo por el HTTPS automático no suele compensar — Certbot con el plugin de Nginx (visto en la [guía de proxy inverso con Nginx](/blog/proxy-inverso-nginx-guia-practica/)) resuelve lo mismo en un comando, aunque como dos herramientas separadas en vez de una.
- Si tu infraestructura ya vive completamente en Docker Compose con contenedores que se crean y destruyen a menudo, Traefik sigue teniendo ventaja por el descubrimiento de servicios integrado sin plugins de terceros.
- Si arrancas un servidor nuevo, fuera de contenedores, con un puñado de dominios y quieres la menor cantidad de piezas que mantener sincronizadas, Caddy es la opción con menos fricción: un fichero de texto y ninguna herramienta adicional para HTTPS.

## Siguiente paso

Con Caddy sirviendo tráfico y renovando certificados solo, el siguiente paso natural es meter detrás suyo los servicios que ya tengas montados en el servidor — sustituye cada `localhost:puerto` de los ejemplos anteriores por el puerto real de cada aplicación y recarga con `systemctl reload caddy` tras cada cambio.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
