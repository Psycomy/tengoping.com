---
title: 'WireGuard: monta tu propia VPN en minutos'
description: 'Guía paso a paso para configurar un servidor VPN con WireGuard en Linux y conectar clientes de forma segura.'
author: 'alois'
pubDate: 2026-02-12
category: 'Redes'
tags: ['WireGuard', 'VPN', 'Self-Hosting', 'Seguridad']
image: '../../assets/images/wireguard-vpn.jpg'
draft: false
---

## Por qué WireGuard y no OpenVPN

OpenVPN lleva años siendo el estándar, pero WireGuard lo supera en varios aspectos:

- **Código mínimo**: unas 4000 líneas frente a las más de 100000 de OpenVPN. Menos código significa menos superficie de ataque y auditorías más fáciles.
- **Rendimiento**: WireGuard opera en el kernel de Linux y usa criptografía moderna (ChaCha20, Curve25519, BLAKE2s). El rendimiento y la latencia son notablemente mejores.
- **Configuración simple**: un archivo de configuración corto en cada extremo, sin gestionar certificados PKI complejos.
- **Conexión instantánea**: el handshake se completa en milisegundos. Ideal para dispositivos móviles que cambian entre WiFi y datos.

## Requisitos

- Servidor Linux con IP pública (VPS o servidor dedicado)
- Puerto UDP abierto en el firewall (por defecto 51820)
- Acceso root en servidor y cliente
- Kernel 5.6+ (WireGuard incluido) o el módulo DKMS para kernels anteriores

## Instalar WireGuard

### En el servidor

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install wireguard -y

# RHEL / Rocky / Alma
sudo dnf install epel-release -y
sudo dnf install wireguard-tools -y
```

### En el cliente

Instala el mismo paquete `wireguard` o `wireguard-tools` en la máquina cliente. WireGuard también tiene aplicaciones oficiales para Windows, macOS, Android e iOS.

## Generar pares de claves

Cada extremo (servidor y cliente) necesita su propio par de claves. Genera las del servidor:

```bash
wg genkey | tee /etc/wireguard/server_private.key | wg pubkey > /etc/wireguard/server_public.key
chmod 600 /etc/wireguard/server_private.key
```

Y las del cliente:

```bash
wg genkey | tee /etc/wireguard/client_private.key | wg pubkey > /etc/wireguard/client_public.key
chmod 600 /etc/wireguard/client_private.key
```

Guarda las claves públicas de ambos extremos. Las necesitarás para la configuración cruzada.

```
Cliente                          Internet                    Servidor
wg0: 10.0.0.2/24                                        wg0: 10.0.0.1/24
   │                                                             │
   └── túnel cifrado (UDP) ──► IP_PUBLICA_SERVIDOR:51820 ───────┘
        AllowedIPs = 0.0.0.0/0                    PostUp: nft masquerade
        (todo el tráfico del cliente                     hacia eth0 (NAT)
         sale por la VPN)
```

## Configurar el servidor

Crea el archivo de configuración de la interfaz WireGuard:

```bash
sudo nano /etc/wireguard/wg0.conf
```

```ini
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <clave_privada_del_servidor>

PostUp = nft add table ip wireguard; nft add chain ip wireguard forward { type filter hook forward priority 0 \; }; nft add rule ip wireguard forward iifname wg0 accept; nft add rule ip wireguard forward oifname wg0 accept; nft add table ip nat; nft add chain ip nat postrouting { type nat hook postrouting priority 100 \; }; nft add rule ip nat postrouting oifname eth0 masquerade
PostDown = nft delete table ip wireguard; nft delete table ip nat

[Peer]
# Cliente 1
PublicKey = <clave_publica_del_cliente>
AllowedIPs = 10.0.0.2/32
```

Sustituye `eth0` por la interfaz de red pública de tu servidor. Verifícala con `ip route show default`.

### Alternativa con iptables

Si tu servidor usa iptables en lugar de nftables:

```ini
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
```

## Habilitar el reenvío de paquetes

WireGuard necesita IP forwarding para enrutar tráfico entre la VPN e internet:

```bash
echo "net.ipv4.ip_forward = 1" | sudo tee /etc/sysctl.d/99-wireguard.conf
sudo sysctl -p /etc/sysctl.d/99-wireguard.conf
```

Verifica que está activo:

```bash
sysctl net.ipv4.ip_forward
```

La salida debe ser `net.ipv4.ip_forward = 1`.

## Configurar el cliente

En la máquina cliente, crea su archivo de configuración:

```bash
sudo nano /etc/wireguard/wg0.conf
```

```ini
[Interface]
Address = 10.0.0.2/24
PrivateKey = <clave_privada_del_cliente>
DNS = 1.1.1.1

[Peer]
PublicKey = <clave_publica_del_servidor>
Endpoint = IP_PUBLICA_SERVIDOR:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
```

- **AllowedIPs = 0.0.0.0/0**: enruta todo el tráfico a través de la VPN (full tunnel). Si solo quieres acceder a la red del servidor, usa `10.0.0.0/24`.
- **PersistentKeepalive**: mantiene el túnel activo cuando el cliente está detrás de NAT.
- **DNS**: en lugar de un resolutor público como `1.1.1.1`, puedes apuntar a un servidor [Pi-hole](/blog/pihole-bloqueo-publicidad-red/) de tu propia red para filtrar publicidad también cuando estás conectado en remoto.

## Levantar y bajar el túnel

### Con wg-quick

```bash
# Levantar la interfaz
sudo wg-quick up wg0

# Verificar el estado
sudo wg show

# Bajar la interfaz
sudo wg-quick down wg0
```

### Con systemd

Para que el túnel se levante automáticamente al arrancar:

```bash
sudo systemctl enable --now wg-quick@wg0
```

Comprueba el estado del servicio:

```bash
sudo systemctl status wg-quick@wg0
```

## Verificar la conexión

Desde el cliente, haz ping al servidor a través del túnel:

```bash
ping -c 4 10.0.0.1
```

Para confirmar que todo el tráfico sale por la VPN:

```bash
curl ifconfig.me
```

La IP devuelta debe ser la IP pública del servidor, no la del cliente.

## Añadir más clientes

Para cada nuevo cliente, genera un par de claves y añade un bloque `[Peer]` en la configuración del servidor:

```ini
[Peer]
# Cliente 2
PublicKey = <clave_publica_cliente_2>
AllowedIPs = 10.0.0.3/32
```

Recarga la configuración sin interrumpir las conexiones existentes:

```bash
sudo wg syncconf wg0 <(sudo wg-quick strip wg0)
```

Cada cliente debe tener una IP única dentro de la subred `10.0.0.0/24`.

## Abrir el puerto en el firewall

Asegúrate de que el puerto UDP de WireGuard esté accesible; si necesitas repasar la sintaxis de cada herramienta, consulta la guía de [firewalld, UFW y nftables](/blog/firewalld-nftables-seguridad-red-linux/):

```bash
# Con nftables
sudo nft add rule inet filter input udp dport 51820 accept

# Con firewalld
sudo firewall-cmd --add-port=51820/udp --permanent
sudo firewall-cmd --reload

# Con ufw
sudo ufw allow 51820/udp
```

## Resumen

Con WireGuard tienes una VPN moderna, rápida y fácil de mantener. La configuración es mínima comparada con OpenVPN, el rendimiento es superior y añadir nuevos clientes se reduce a generar claves y agregar un bloque `[Peer]`. Todo tu tráfico viaja cifrado entre tus dispositivos y tu servidor, sin depender de servicios VPN de terceros — un uso habitual es acceder de forma segura a servicios autoalojados como [Nextcloud](/blog/nextcloud-servidor-nube-personal/) cuando estás fuera de casa.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
