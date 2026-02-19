---
title: "Certificados SSL gratuitos con Let's Encrypt y Certbot"
description: 'Guía paso a paso para obtener y renovar certificados SSL gratuitos con Certbot en servidores Nginx y Apache.'
author: 'antonio'
pubDate: 2025-12-20
category: 'Seguridad'
tags: ['SSL', "Let's Encrypt", 'Certbot', 'Nginx']
image: '../../assets/images/letsencrypt-ssl.jpg'
draft: false
---

## Por que HTTPS es imprescindible

HTTPS no es solo para tiendas online o bancos. Los navegadores modernos marcan como "No seguro" cualquier sitio que use HTTP plano. Ademas de cifrar el trafico entre el cliente y el servidor, HTTPS protege contra ataques man-in-the-middle, mejora el posicionamiento SEO y es requisito para funcionalidades como HTTP/2, service workers y geolocation.

Let's Encrypt es una autoridad certificadora gratuita y automatizada que emite certificados SSL/TLS validos para cualquier dominio. Certbot es el cliente oficial que automatiza la obtencion y renovacion de estos certificados.

## Instalar Certbot

La forma recomendada de instalar Certbot es mediante `snap`, que garantiza tener siempre la version mas reciente:

```bash
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

Si prefieres usar el gestor de paquetes de tu distribucion:

```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install certbot python3-certbot-nginx -y

# Debian / Ubuntu
sudo apt install certbot python3-certbot-nginx -y
```

Para Apache, sustituye `python3-certbot-nginx` por `python3-certbot-apache`.

## Obtener un certificado para Nginx

Certbot puede configurar Nginx automaticamente. Solo necesitas que tu dominio apunte al servidor y que Nginx este sirviendo ese dominio:

```bash
sudo certbot --nginx -d ejemplo.com -d www.ejemplo.com
```

Certbot realiza los siguientes pasos automaticamente:

1. Verifica que controlas el dominio respondiendo al reto HTTP-01.
2. Obtiene el certificado de Let's Encrypt.
3. Modifica la configuracion de Nginx para usar el certificado.
4. Configura la redireccion de HTTP a HTTPS (te preguntara si la quieres).

Verifica que la configuracion de Nginx es correcta y recarga el servicio:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Obtener un certificado para Apache

El proceso para Apache es igual de directo:

```bash
sudo certbot --apache -d ejemplo.com -d www.ejemplo.com
```

Certbot modificara la configuracion del virtualhost de Apache para incluir las directivas SSL y opcionalmente anadira la redireccion HTTP a HTTPS.

## Modo standalone

Si no tienes un servidor web en ejecucion o prefieres no modificar su configuracion automaticamente, puedes usar el modo standalone. Certbot levanta temporalmente su propio servidor web en el puerto 80 para responder al reto de validacion:

```bash
# Detener el servidor web si esta usando el puerto 80
sudo systemctl stop nginx

# Obtener el certificado
sudo certbot certonly --standalone -d ejemplo.com -d www.ejemplo.com

# Reiniciar el servidor web
sudo systemctl start nginx
```

Los certificados se guardan en `/etc/letsencrypt/live/ejemplo.com/`. Tendras que configurar manualmente tu servidor web para usarlos:

```nginx
server {
    listen 443 ssl;
    server_name ejemplo.com www.ejemplo.com;

    ssl_certificate     /etc/letsencrypt/live/ejemplo.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ejemplo.com/privkey.pem;

    # Configuracion SSL recomendada
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
}
```

## Renovacion automatica con systemd timer

Los certificados de Let's Encrypt tienen una validez de 90 dias. Certbot instala automaticamente un timer de systemd que intenta la renovacion dos veces al dia. Verifica que esta activo:

```bash
sudo systemctl list-timers | grep certbot
```

Deberias ver algo como:

```text
NEXT                         LEFT          LAST                         PASSED  UNIT
2025-12-21 03:24:00 UTC      8h left       2025-12-20 15:24:00 UTC      4h ago  snap.certbot.renew.timer
```

Si usaste el paquete del sistema en lugar de snap, el timer puede llamarse `certbot.timer`:

```bash
sudo systemctl enable --now certbot.timer
sudo systemctl status certbot.timer
```

## Probar la renovacion

Antes de confiar en la renovacion automatica, prueba que funciona correctamente con un ensayo en seco:

```bash
sudo certbot renew --dry-run
```

Si el dry-run termina sin errores, la renovacion real funcionara igual. Si falla, los motivos mas comunes son:

- El puerto 80 no esta accesible desde Internet (firewall, proveedor cloud).
- La configuracion del servidor web ha cambiado y el reto HTTP-01 no se puede completar.
- El dominio ya no apunta al servidor.

Para que Nginx o Apache recarguen la configuracion tras la renovacion, anade un hook:

```bash
sudo certbot renew --deploy-hook "systemctl reload nginx"
```

O de forma permanente editando `/etc/letsencrypt/renewal/ejemplo.com.conf`:

```ini
[renewalparams]
deploy_hook = systemctl reload nginx
```

## Certificados wildcard con DNS challenge

Si necesitas un certificado para todos los subdominios (`*.ejemplo.com`), debes usar el reto DNS-01 en lugar de HTTP-01. Esto requiere que puedas crear registros TXT en tu zona DNS:

```bash
sudo certbot certonly --manual --preferred-challenges dns -d "*.ejemplo.com" -d ejemplo.com
```

Certbot te pedira que crees un registro TXT con un valor especifico en `_acme-challenge.ejemplo.com`. Una vez creado el registro y propagado, Certbot verificara y emitira el certificado.

Para automatizar la renovacion de wildcards, necesitas un plugin DNS para tu proveedor. Por ejemplo, para Cloudflare:

```bash
sudo snap install certbot-dns-cloudflare

# Crear archivo de credenciales
sudo tee /etc/letsencrypt/cloudflare.ini << 'EOF'
dns_cloudflare_api_token = TU_API_TOKEN
EOF
sudo chmod 600 /etc/letsencrypt/cloudflare.ini

# Obtener el certificado wildcard con renovacion automatica
sudo certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d "*.ejemplo.com" -d ejemplo.com
```

## Verificar el certificado

Una vez instalado el certificado, verifica que todo funciona correctamente:

```bash
# Comprobar la fecha de expiracion
sudo certbot certificates

# Verificar la conexion SSL desde la linea de comandos
openssl s_client -connect ejemplo.com:443 -servername ejemplo.com < /dev/null 2>/dev/null | openssl x509 -noout -dates
```

Tambien puedes usar servicios web como SSL Labs (ssllabs.com/ssltest) para obtener un informe completo de la configuracion SSL de tu servidor, incluyendo la cadena de certificados, los protocolos soportados y la puntuacion global.

## Buenas practicas

- Usa siempre **TLS 1.2 y 1.3** como minimo. Desactiva TLS 1.0 y 1.1 que estan obsoletos.
- Configura cabeceras de seguridad complementarias: `Strict-Transport-Security` (HSTS), `X-Content-Type-Options`, `X-Frame-Options`.
- Monitoriza la fecha de expiracion de tus certificados con alguna herramienta de alertas para detectar fallos de renovacion antes de que el certificado caduque.
- Nunca compartas ni expongas la clave privada (`privkey.pem`). Si sospechas que se ha comprometido, revoca el certificado con `certbot revoke` y genera uno nuevo.
  > [!NOTE]
  > ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
