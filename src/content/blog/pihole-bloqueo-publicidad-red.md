---
title: 'Pi-hole: bloquea publicidad en toda tu red'
description: 'Cómo instalar Pi-hole como servidor DNS local para filtrar publicidad y rastreadores en todos los dispositivos de tu red.'
author: 'antonio'
pubDate: 2026-02-04
category: 'Self-Hosting'
tags: ['Pi-hole', 'DNS', 'Self-Hosting', 'Redes']
image: '../../assets/images/pihole-dns.jpg'
draft: false
---

## Que es Pi-hole

Pi-hole es un servidor DNS local que actua como sumidero de publicidad. Cuando un dispositivo de tu red intenta resolver un dominio de publicidad o rastreo, Pi-hole responde con una direccion nula y el anuncio nunca se carga. Funciona a nivel de red, asi que protege todos los dispositivos conectados sin necesidad de instalar extensiones en cada navegador.

## Requisitos

- Una Raspberry Pi, un servidor Linux o una maquina virtual con Debian/Ubuntu
- IP estatica en la red local
- Acceso root o sudo

## Instalacion

Pi-hole ofrece un script de instalacion automatica. Ejecutalo con:

```bash
curl -sSL https://install.pi-hole.net | sudo bash
```

El asistente te guiara por varios pasos:

1. **Interfaz de red**: selecciona la interfaz conectada a tu red local (por ejemplo `eth0`).
2. **Proveedor DNS upstream**: elige uno temporal como Google o Cloudflare. Mas adelante puedes cambiarlo.
3. **Listas de bloqueo**: acepta las listas por defecto. Despues podras anadir mas.
4. **Interfaz web**: acepta instalar el panel de administracion.
5. **Contrasena**: al finalizar, el script mostrara la contrasena del panel web. Anotala o cambiala con:

```bash
pihole -a -p
```

## Configurar Pi-hole como DNS en tu router

Para que todos los dispositivos usen Pi-hole sin configuracion individual, accede al panel de administracion de tu router y cambia el servidor DNS primario a la IP de Pi-hole. Por ejemplo, si Pi-hole esta en `192.168.1.100`:

- **DNS primario**: `192.168.1.100`
- **DNS secundario**: dejalo vacio o pon la misma IP. Si pones un DNS externo como secundario, los dispositivos podrian usarlo y saltarse el filtrado.

Reinicia el servicio DHCP del router para que los dispositivos renueven su configuracion.

## Panel de administracion

Accede al panel web en `http://192.168.1.100/admin`. Desde alli puedes ver:

- **Dashboard**: estadisticas en tiempo real con el porcentaje de consultas bloqueadas, total de peticiones y dominios mas frecuentes.
- **Query Log**: registro detallado de cada consulta DNS con su estado (permitida, bloqueada, cacheada).
- **Long-Term Data**: graficos historicos de actividad DNS.

## Gestionar listas de bloqueo

Las listas por defecto cubren los dominios mas comunes de publicidad y rastreo, pero puedes ampliarlas. Ve a **Group Management > Adlists** y anade URLs de listas adicionales:

```text
https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts
https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/pro.txt
```

Despues de anadir listas, actualiza la gravedad:

```bash
pihole -g
```

### Lista blanca

Algunos servicios pueden dejar de funcionar si bloqueas dominios que necesitan. Anade excepciones desde el panel web en **Whitelist** o por terminal:

```bash
pihole -w dominio.ejemplo.com
```

Para ver los dominios actualmente en lista blanca:

```bash
pihole -w -l
```

## Unbound como DNS recursivo

Por defecto, Pi-hole reenvia las consultas a un proveedor externo como Cloudflare o Google. Si quieres mayor privacidad, puedes instalar Unbound como resolver recursivo local que consulta directamente a los servidores raiz:

```bash
sudo apt install unbound
```

Crea el archivo de configuracion:

```bash
sudo nano /etc/unbound/unbound.conf.d/pi-hole.conf
```

```yaml
server:
  verbosity: 0
  interface: 127.0.0.1
  port: 5335
  do-ip4: yes
  do-ip6: no
  do-udp: yes
  do-tcp: yes
  harden-glue: yes
  harden-dnssec-stripped: yes
  use-caps-for-id: no
  edns-buffer-size: 1232
  prefetch: yes
  num-threads: 1
  cache-min-ttl: 3600
  cache-max-ttl: 86400
```

```bash
sudo systemctl enable --now unbound
```

En el panel de Pi-hole, ve a **Settings > DNS** y configura como upstream personalizado `127.0.0.1#5335`. Desactiva los demas proveedores.

## Mantener Pi-hole actualizado

Actualiza Pi-hole y sus componentes con un solo comando:

```bash
pihole -up
```

Revisa periodicamente que las listas de bloqueo esten actualizadas y que el sistema operativo tenga los parches de seguridad aplicados.

## Alternativa con Docker

Si prefieres contenedores, Pi-hole tiene imagen oficial. Crea un archivo `docker-compose.yml`:

```yaml
services:
  pihole:
    container_name: pihole
    image: pihole/pihole:latest
    ports:
      - '53:53/tcp'
      - '53:53/udp'
      - '80:80/tcp'
    environment:
      TZ: 'Europe/Madrid'
      WEBPASSWORD: 'tu_password_segura'
    volumes:
      - './etc-pihole:/etc/pihole'
      - './etc-dnsmasq.d:/etc/dnsmasq.d'
    restart: unless-stopped
```

```bash
docker compose up -d
```

## Resultado

Con Pi-hole funcionando como DNS de tu red, la navegacion sera mas rapida y limpia. Reduciras el consumo de ancho de banda, eliminaras rastreadores y tendras visibilidad total sobre las consultas DNS que generan tus dispositivos.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
