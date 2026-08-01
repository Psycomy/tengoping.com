---
title: 'tcpdump: analiza tráfico de red en terminal'
description: 'Guía práctica de tcpdump: sintaxis de filtros, lectura de paquetes y captura en archivos pcap para depurar problemas de red desde terminal.'
author: 'antonio'
pubDate: 2026-08-01T12:00:00
category: 'Redes'
tags: ['tcpdump', 'Redes', 'Sysadmin', 'Linux']
image: '../../assets/images/redes-tcpdump.jpg'
draft: false
---

Cuando un firewall no filtra lo que crees, un servicio no responde en el puerto esperado, o simplemente necesitas confirmar qué está pasando en el cable antes de seguir adivinando, `tcpdump` te da la respuesta indiscutible: lo que realmente circula por la interfaz, sin depender de logs de aplicación ni de lo que una regla debería estar haciendo en teoría. Es la herramienta de captura de paquetes que viene preinstalada o disponible en cualquier distribución Linux, y con un puñado de filtros cubre el 90% de las depuraciones de red del día a día.

## Instalación

`tcpdump` suele venir preinstalado en la mayoría de distribuciones de servidor. Si no está disponible:

```bash
# Debian/Ubuntu
sudo apt install tcpdump -y

# RHEL/Rocky/Oracle Linux
sudo dnf install tcpdump -y
```

## Captura básica y elegir la interfaz

El flag `-i` selecciona la interfaz de red a escuchar:

```bash
# Listar las interfaces disponibles
tcpdump -D

# Capturar en una interfaz concreta
sudo tcpdump -i eth0

# Capturar en todas las interfaces regulares a la vez (Linux, macOS, Solaris)
sudo tcpdump -i any
```

> [!IMPORTANT]
> Capturar tráfico de una interfaz requiere privilegios especiales — normalmente `root`. Leer un archivo de captura ya guardado (con `-r`) no los requiere. Si quieres evitar escribir `sudo` cada vez, más abajo tienes la alternativa con `setcap`.

## Sintaxis de filtros: host, port, net y proto

Sin filtro, `tcpdump` muestra todo lo que pasa por la interfaz — en un servidor con tráfico real, eso es ruido inmanejable en segundos. Los filtros (definidos en `pcap-filter`) acotan la captura a lo que te interesa:

```bash
# Todo el tráfico hacia o desde una IP
sudo tcpdump -i eth0 host 192.168.1.50

# Tráfico en un puerto concreto (acepta nombre de servicio o número)
sudo tcpdump -i eth0 port 443

# Tráfico de una red completa, en notación CIDR
sudo tcpdump -i eth0 net 192.168.1.0/24

# Filtrar por protocolo
sudo tcpdump -i eth0 proto tcp
```

`port` y `host` matchean tanto origen como destino por defecto; para acotar a una sola dirección, antepón `src` o `dst`:

```bash
# Solo paquetes que salen hacia el puerto 80
sudo tcpdump -i eth0 dst port 80

# Solo paquetes que llegan desde esa IP
sudo tcpdump -i eth0 src host 192.168.1.50
```

## Otros filtros útiles

Además de `host`/`port`/`net`/`proto`, hay primitivas específicas que ahorran tener que recordar números de protocolo:

```bash
# Solo tráfico ICMP (ping, traceroute)
sudo tcpdump -i eth0 icmp

# Solo tráfico ARP (útil para depurar problemas de resolución en la LAN)
sudo tcpdump -i eth0 arp

# Tráfico broadcast (ej: DHCP discover, antes de tener IP asignada)
sudo tcpdump -i eth0 ether broadcast

# Paquetes por tamaño: mayores de 1500 bytes (posible fragmentación) o menores/iguales a 128
sudo tcpdump -i eth0 greater 1500
sudo tcpdump -i eth0 less 128
```

## Combinar filtros con and, or y not

Los filtros se combinan con `and`, `or` y `not` (también válidos como `&&`, `||`, `!`) para expresiones más precisas:

```bash
# Tráfico HTTPS que no venga de tu propia red local
sudo tcpdump -i eth0 "tcp port 443 and not src net 192.168.0.0/16"

# Tráfico entre dos hosts concretos
sudo tcpdump -i eth0 "host 10.0.0.5 and host 10.0.0.10"

# Varios puertos de destino a la vez
sudo tcpdump -i eth0 "tcp dst port 80 or 443 or 8080"
```

## Entender el formato de cada línea

Antes de tocar más flags, conviene saber qué significa cada campo de una línea de captura típica. Un paquete TCP se ve así:

```text
14:32:01.123456 IP 192.168.1.50.54321 > 192.168.1.1.443: Flags [S], seq 123456789, win 64240, length 0
```

- **`14:32:01.123456`** — timestamp con microsegundos
- **`192.168.1.50.54321 > 192.168.1.1.443`** — origen y destino, con el puerto pegado tras el último punto (`.54321` y `.443`)
- **`Flags [S]`** — flags TCP: `S` = SYN (inicio de conexión), `.` = ACK, `P` = PSH (datos), `F` = FIN (cierre), `R` = RST (reset). `[S.]` es un SYN-ACK; ver un `[S]` sin respuesta suele significar que el destino no está escuchando en ese puerto o algo lo está bloqueando por el camino
- **`seq` / `ack`** — números de secuencia y confirmación, útiles para seguir una conversación TCP paquete a paquete
- **`win`** — tamaño de la ventana de recepción anunciada
- **`length`** — bytes de datos en el paquete (0 en un SYN, que no lleva payload)

Con esto ya puedes distinguir, sin necesidad de `-A`/`-X`, si una conexión llega a establecerse (`[S]` seguido de `[S.]` y luego `[.]`) o se queda colgada en el primer `[S]` sin respuesta — la firma más común de un firewall descartando el tráfico en silencio.

## Leer la salida: -n, -nn, -A y -X

Por defecto `tcpdump` intenta resolver nombres de host y de servicio, lo que ralentiza la captura y añade ruido en un análisis rápido:

```bash
# No resuelve nombres de host, pero sí nombres de puerto (ej: "https" en vez de "443")
sudo tcpdump -i eth0 -n port 443

# Tampoco resuelve nombres de puerto: solo direcciones IP y números
sudo tcpdump -i eth0 -nn port 443
```

Para ver el contenido de los paquetes, no solo las cabeceras:

```bash
# Contenido en ASCII (útil para tráfico HTTP en texto plano)
sudo tcpdump -i eth0 -A port 80

# Contenido en hexadecimal y ASCII (útil para depurar protocolos binarios)
sudo tcpdump -i eth0 -X port 80
```

## Guardar y releer capturas con -w y -r

Para analizar tráfico con calma, o para pasárselo a otra herramienta como Wireshark, guarda la captura en un archivo `.pcap` en vez de imprimirla en pantalla:

```bash
# Guardar en un archivo
sudo tcpdump -i eth0 -w captura.pcap port 443

# Releer el archivo después
tcpdump -r captura.pcap -n
```

> [!CAUTION]
> Capturar sin filtro y sin límite en una interfaz con tráfico real (`sudo tcpdump -i eth0 -w todo.pcap`, sin más) puede llenar el disco en minutos si el volumen es alto. Acota siempre con un filtro y, si es una captura puntual, añade `-c <número>` para cortar tras un número fijo de paquetes: `sudo tcpdump -i eth0 -w captura.pcap -c 1000 port 443`.

## Casos prácticos de depuración

**Confirmar si un firewall está bloqueando tráfico.** Después de aplicar una regla en [firewalld o nftables](/blog/firewalld-nftables-seguridad-red-linux/), `tcpdump` te dice la verdad sin depender de lo que la regla debería hacer en teoría: si el paquete no aparece en la interfaz de salida, el firewall lo está descartando; si aparece pero no hay respuesta, el problema está en otro sitio.

```bash
# Ves si los intentos de conexión llegan siquiera a la interfaz
sudo tcpdump -i eth0 -nn port 8080
```

**Verificar el etiquetado VLAN.** Si segmentas tu red con [VLANs y 802.1Q](/blog/vlans-explicadas-segmentar-red/), una captura te confirma sin ambigüedad si el tag realmente está llegando al puerto que esperas, en vez de fiarte de la configuración del switch. `-e` imprime la cabecera de enlace completa (incluida la etiqueta 802.1Q), que por defecto tcpdump no muestra:

```bash
sudo tcpdump -i eth0 -e vlan
```

> [!IMPORTANT]
> Captura en la interfaz física (`eth0`), no en una subinterfaz VLAN tipo `eth0.120`. El kernel de Linux quita la etiqueta 802.1Q antes de entregar el paquete a la subinterfaz, así que ahí nunca la verás — solo es visible capturando en el enlace físico de donde viene.

**Depurar consultas DNS.** Si administras tu propio [servidor DNS autoritativo con BIND9](/blog/dns-bind9-servidor-autoritativo/), filtrar por el puerto 53 muestra exactamente qué consultas está recibiendo y si está respondiendo:

```bash
sudo tcpdump -i eth0 -n port 53
```

## Capturar sin sudo

> [!TIP]
> Si capturas a menudo y quieres evitar escribir `sudo` cada vez, puedes dar a `tcpdump` las capabilities de Linux necesarias en vez de privilegios de root completos: `sudo setcap cap_net_raw,cap_net_admin=eip $(which tcpdump)`. A partir de ahí, cualquier usuario puede ejecutar `tcpdump` directamente.

## Siguiente paso

Con `host`, `port`, `net`, `-n`/`-nn` y `-w`/`-r` ya cubres la gran mayoría de las depuraciones de red del día a día. Para un análisis más visual de capturas guardadas — seguir sesiones TCP completas, ver gráficos de latencia — el siguiente paso natural es abrir esos mismos archivos `.pcap` en Wireshark, que reutiliza exactamente la misma sintaxis de filtros que acabas de aprender aquí.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
