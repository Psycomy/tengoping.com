---
title: 'Montar un servidor DNS autoritativo con BIND9'
description: 'Cómo instalar y configurar un servidor DNS autoritativo con BIND9 en Linux para gestionar tus propias zonas DNS.'
author: 'alois'
pubDate: 2026-01-15
updatedDate: 2026-07-27
category: 'Redes'
tags: ['DNS', 'BIND9', 'Redes', 'Linux']
image: '../../assets/images/redes-dns.jpg'
draft: false
---

## ¿Por qué un DNS propio?

Gestionar tu propio servidor DNS autoritativo te da control total sobre las zonas de tu dominio, reduce la dependencia de terceros y permite configuraciones avanzadas. Si lo que buscas es un resolutor que bloquee publicidad en tu red local en vez de publicar zonas de un dominio, ese es el caso de uso de [Pi-hole](/blog/pihole-bloqueo-publicidad-red/), no el de BIND9.

```
Cliente ("www.tengoping.com?")
   │
   ▼
Resolver recursivo (tu ISP, 1.1.1.1, un Pi-hole...)
   │
   │  no tiene la respuesta en caché → pregunta a quien SÍ sabe
   ▼
Servidor autoritativo de la zona (este BIND9)
   ├── ns1.tengoping.com  → 203.0.113.10
   ├── ns2.tengoping.com  → 203.0.113.11
   └── www.tengoping.com  → A 203.0.113.10   (la respuesta)
```

## Instalación de BIND9

```bash
# RHEL/Rocky/Oracle Linux
sudo dnf install bind bind-utils -y
sudo systemctl enable --now named

# Ubuntu/Debian
sudo apt install bind9 bind9utils -y
sudo systemctl enable --now bind9
```

## Configuración principal

La ruta del archivo principal y el directorio de zonas cambian según la distribución.

En RHEL/Rocky/Oracle Linux:

```bash
sudo vi /etc/named.conf
```

```
options {
    listen-on port 53 { any; };
    directory "/var/named";
    allow-query { any; };
    recursion no;
};

zone "tengoping.com" IN {
    type master;
    file "tengoping.com.zone";
};
```

En Ubuntu/Debian (paquete `bind9`), la configuración se reparte en `/etc/bind/named.conf.options` y `/etc/bind/named.conf.local`, y AppArmor bloquea el acceso a `/var/named`, por lo que el directorio de zonas debe ser `/var/cache/bind`:

```bash
sudo vi /etc/bind/named.conf.options
```

```
options {
    listen-on port 53 { any; };
    directory "/var/cache/bind";
    allow-query { any; };
    recursion no;
};
```

```bash
sudo vi /etc/bind/named.conf.local
```

```
zone "tengoping.com" IN {
    type master;
    file "tengoping.com.zone";
};
```

## Archivo de zona

En RHEL/Rocky/Oracle Linux el archivo se guarda en `/var/named/tengoping.com.zone`; en Ubuntu/Debian, en `/var/cache/bind/tengoping.com.zone`.

```
$TTL 86400
@   IN  SOA ns1.tengoping.com. admin.tengoping.com. (
        2026020601  ; Serial
        3600        ; Refresh
        1800        ; Retry
        604800      ; Expire
        86400 )     ; Minimum TTL

    IN  NS  ns1.tengoping.com.
    IN  NS  ns2.tengoping.com.
    IN  A   203.0.113.10

ns1 IN  A   203.0.113.10
ns2 IN  A   203.0.113.11
www IN  A   203.0.113.10
```

## Verificación

```bash
named-checkconf

# RHEL/Rocky/Oracle Linux
named-checkzone tengoping.com /var/named/tengoping.com.zone

# Ubuntu/Debian
named-checkzone tengoping.com /var/cache/bind/tengoping.com.zone

dig @localhost tengoping.com
```

## Conclusión

BIND9 sigue siendo la referencia para servidores DNS en Linux. Con una configuración adecuada y buenas prácticas de seguridad, es una solución robusta y fiable. Si el servidor va a responder consultas desde fuera de tu red, no olvides abrir el puerto 53 (TCP/UDP) siguiendo la guía de [firewalld, UFW y nftables](/blog/firewalld-nftables-seguridad-red-linux/).

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
