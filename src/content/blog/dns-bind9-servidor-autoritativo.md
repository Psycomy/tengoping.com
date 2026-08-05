---
title: 'Montar un servidor DNS autoritativo con BIND9'
description: 'BIND9 autoritativo en Linux: zonas directas e inversas, servidor secundario con TSIG, rndc y buenas prácticas de seguridad.'
author: 'alois'
pubDate: 2026-01-15
updatedDate: 2026-08-05
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

Los cinco valores del registro SOA controlan el ciclo de vida de la zona en cualquier secundario que la replique, no en el propio servidor primario:

- **Serial** — la versión de la zona. Un secundario solo pide una transferencia nueva si el serial del primario es mayor que el que ya tiene.
- **Refresh** — cada cuánto (en segundos) el secundario comprueba si hay un serial más nuevo.
- **Retry** — si esa comprobación falla (el primario no responde), cuánto espera antes de reintentar.
- **Expire** — si el primario sigue sin responder durante todo este tiempo, el secundario deja de servir la zona por considerarla obsoleta, en vez de arriesgarse a dar datos desactualizados indefinidamente.
- **Minimum TTL** — desde BIND 9, cuánto tiempo cachean los resolutores una respuesta _negativa_ (NXDOMAIN), no el TTL general de la zona — el `$TTL` de la primera línea ya cubre eso para los registros normales.

## Verificación

```bash
named-checkconf

# RHEL/Rocky/Oracle Linux
named-checkzone tengoping.com /var/named/tengoping.com.zone

# Ubuntu/Debian
named-checkzone tengoping.com /var/cache/bind/tengoping.com.zone

dig @localhost tengoping.com
```

## Registros más allá de A y NS

Una zona real casi nunca se queda en A y NS. Los tipos que más falta hacen:

```
; en el bloque de la zona, junto a los registros A ya existentes
www     IN  A       203.0.113.10
mail    IN  A       203.0.113.20
@       IN  MX  10  mail.tengoping.com.
blog    IN  CNAME   www.tengoping.com.
@       IN  TXT     "v=spf1 mx -all"
```

- **MX** — a qué servidor entregar el correo del dominio, con una prioridad (menor número = mayor prioridad).
- **CNAME** — un alias que apunta a otro nombre, no directamente a una IP; evita duplicar la A si `blog` y `www` deben resolver siempre igual.
- **TXT** — texto libre usado por convención para SPF, verificación de dominio de terceros, etc.

> [!IMPORTANT]
> Un nombre no puede tener a la vez un CNAME y cualquier otro tipo de registro (ni siquiera otro CNAME) — es una restricción del propio protocolo, no una limitación de BIND. Si `blog` necesita un CNAME, no puede tener también un TXT propio en ese mismo nombre.

## Zona inversa: de IP a nombre

La zona que has creado hasta ahora resuelve nombre → IP. La resolución inversa (IP → nombre, la que usa por ejemplo un servidor de correo para verificar el PTR del remitente) necesita su propia zona, bajo el dominio especial `in-addr.arpa`, con los octetos de la red en orden inverso:

```
# /etc/bind/named.conf.local (o named.conf en RHEL, mismo bloque)
zone "113.0.203.in-addr.arpa" IN {
    type master;
    file "203.0.113.rev";
};
```

```
$TTL 86400
@   IN  SOA ns1.tengoping.com. admin.tengoping.com. (
        2026020601 ; Serial
        3600       ; Refresh
        1800       ; Retry
        604800     ; Expire
        86400 )    ; Minimum TTL

    IN  NS  ns1.tengoping.com.

10  IN  PTR www.tengoping.com.
11  IN  PTR ns2.tengoping.com.
```

Solo se indica el último octeto en cada línea `PTR` — el resto de la red ya está fijado en el nombre de la zona.

## Servidor secundario: replicar la zona

Un único servidor autoritativo es un punto único de fallo. Un secundario (slave) mantiene una copia sincronizada por transferencia de zona (AXFR/IXFR) sin que edites nada a mano en él:

```
# En el PRIMARIO — named.conf.local
zone "tengoping.com" IN {
    type master;
    file "tengoping.com.zone";
    allow-transfer { 203.0.113.11; };   # solo el secundario puede pedir la zona completa
    also-notify { 203.0.113.11; };      # avisa al secundario en cuanto hay un cambio
};
```

```
# En el SECUNDARIO — named.conf.local
zone "tengoping.com" IN {
    type slave;
    file "slaves/tengoping.com.zone";   # BIND escribe aquí la copia, no la editas tú
    masters { 203.0.113.10; };
    allow-notify { 203.0.113.10; };
};
```

> [!TIP]
> Restringir `allow-transfer` a una IP concreta ya evita que cualquiera en internet descargue tu zona completa, pero la IP se puede falsificar. Para autenticar de verdad quién puede pedir la transferencia, añade una clave TSIG con `tsig-keygen` y referénciala en `allow-transfer { key nombre-clave; };` en vez de (o además de) la IP.

## Aplicar cambios sin reiniciar: rndc

Reiniciar el servicio corta todas las resoluciones en curso; `rndc` aplica cambios sin ese corte:

```bash
sudo rndc reload              # recarga todas las zonas (detecta ediciones en los archivos de zona)
sudo rndc reload tengoping.com  # recarga solo esa zona, más rápido con muchas zonas delegadas
sudo rndc reconfig             # relee named.conf: detecta zonas añadidas o quitadas, no cambios dentro de una zona ya cargada
```

> [!WARNING]
> Si editas un archivo de zona y no incrementas el campo `Serial` del registro SOA, `rndc reload` no aplicará el cambio en los secundarios — comparan el serial para decidir si necesitan una nueva transferencia. La convención más extendida es la fecha en formato `AAAAMMDDnn` (el `nn` final para poder hacer varios cambios el mismo día), aunque BIND solo exige que el número aumente respecto al anterior.

## Registrar la actividad y depurar

```bash
journalctl -u named -f    # RHEL/Rocky/Oracle Linux
journalctl -u bind9 -f    # Ubuntu/Debian

dig @localhost tengoping.com MX      # comprobar un tipo de registro concreto
dig +trace tengoping.com             # seguir la resolución desde los root servers, útil si algo falla fuera de tu red
```

## Buenas prácticas de seguridad

- **`recursion no;`** en un servidor autoritativo público — ya está en el ejemplo de este artículo — evita que se use tu BIND como resolutor abierto para consultas de terceros, un vector clásico de amplificación DDoS.
- **Ocultar la versión** de BIND que se anuncia por consulta (`version "no disponible";` dentro de `options {}`) reduce la información disponible para un atacante que huela binarios vulnerables de una versión concreta.
- **TSIG** en las transferencias de zona, como se ha visto arriba, en vez de confiar solo en el filtrado por IP.
- Si el servidor va a responder consultas desde fuera de tu red, abre el puerto 53 (TCP y UDP, no solo UDP: las respuestas grandes o las transferencias de zona usan TCP) siguiendo la guía de [firewalld, UFW y nftables](/blog/firewalld-nftables-seguridad-red-linux/).

## Conclusión

BIND9 sigue siendo la referencia para servidores DNS en Linux. Con zonas directas e inversas bien definidas, un secundario para redundancia y las prácticas de seguridad de este artículo, tienes una infraestructura DNS tan robusta como la de cualquier proveedor externo, con el control total en tus manos.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
