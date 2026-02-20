---
title: 'Montar un servidor DNS autoritativo con BIND9'
description: 'Cómo instalar y configurar un servidor DNS autoritativo con BIND9 en Linux para gestionar tus propias zonas DNS.'
author: 'alois'
pubDate: 2026-01-15
category: 'Redes'
tags: ['DNS', 'BIND9', 'Redes', 'Linux']
image: '../../assets/images/redes-dns.jpg'
draft: false
---

## ¿Por qué un DNS propio?

Gestionar tu propio servidor DNS autoritativo te da control total sobre las zonas de tu dominio, reduce la dependencia de terceros y permite configuraciones avanzadas.

## Instalación de BIND9

```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install bind bind-utils -y
sudo systemctl enable --now named

# Ubuntu / Debian
sudo apt install bind9 bind9utils -y
sudo systemctl enable --now bind9
```

## Configuración principal

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

## Archivo de zona

```
; /var/named/tengoping.com.zone
$TTL 86400
@   IN  SOA ns1.tengoping.com. admin.tengoping.com. (
        2025020601  ; Serial
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
named-checkzone tengoping.com /var/named/tengoping.com.zone
dig @localhost tengoping.com
```

## Conclusión

BIND9 sigue siendo la referencia para servidores DNS en Linux. Con una configuración adecuada y buenas prácticas de seguridad, es una solución robusta y fiable.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
