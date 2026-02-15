---
title: "Raspberry Pi como servidor doméstico"
description: "Cómo convertir una Raspberry Pi en un servidor doméstico para DNS, VPN, almacenamiento y más."
author: "antonio"
pubDate: 2025-05-03
category: "Hardware"
tags: ["Raspberry Pi", "Homelab", "Hardware", "Linux"]
image: "/images/raspberry-pi-server.jpg"
draft: false
---

## Introduccion

La Raspberry Pi es una de las mejores opciones para montar un servidor doméstico de bajo consumo. Por menos de 100 euros puedes tener funcionando un DNS local, una VPN, almacenamiento en red o incluso un pequeño cluster de contenedores. En esta guía veremos cómo elegir el modelo adecuado, configurarlo sin pantalla y ponerlo a trabajar.

## Raspberry Pi 4 vs Raspberry Pi 5

La elección del modelo depende de tu presupuesto y del uso que le vayas a dar:

| Característica | Raspberry Pi 4 | Raspberry Pi 5 |
|---|---|---|
| CPU | Cortex-A72 (4 cores, 1.8 GHz) | Cortex-A76 (4 cores, 2.4 GHz) |
| RAM | 1/2/4/8 GB | 4/8 GB |
| USB | 2x USB 3.0, 2x USB 2.0 | 2x USB 3.0, 2x USB 2.0 |
| PCIe | No | PCIe 2.0 x1 (vía HAT) |
| Consumo | ~6W en carga | ~10W en carga |
| Precio aprox. | 45-75 EUR | 60-90 EUR |

Para servicios ligeros como Pi-hole o WireGuard, una Pi 4 con 2 GB es más que suficiente. Si planeas correr contenedores Docker o un NAS con Samba, la Pi 5 con 8 GB merece la inversión. El soporte PCIe de la Pi 5 permite conectar un SSD NVMe mediante un HAT, lo que mejora drásticamente el rendimiento de disco.

## Instalación del sistema operativo

Descarga Raspberry Pi Imager desde la web oficial e instálalo en tu equipo. Inserta la tarjeta microSD y selecciona el sistema operativo:

```bash
# En Linux puedes instalar el imager con snap
sudo snap install rpi-imager
```

Selecciona **Raspberry Pi OS Lite (64-bit)** como sistema operativo. Es la versión sin escritorio, ideal para servidores. Antes de escribir la imagen, pulsa el icono de configuración avanzada y activa:

- **SSH** con autenticación por contraseña o clave pública
- **Nombre de host** personalizado (por ejemplo, `piserver`)
- **Usuario y contraseña** (evita el usuario `pi` por defecto)
- **Configuración WiFi** si no usarás cable Ethernet

Escribe la imagen en la tarjeta SD y arráncala en la Raspberry Pi.

## Configuración inicial sin pantalla (headless)

Si habilitaste SSH en el imager, solo necesitas encontrar la IP de tu Pi en la red:

```bash
# Escanear la red local en busca de la Pi
nmap -sn 192.168.1.0/24 | grep -i raspberry

# Conectar por SSH
ssh tu_usuario@piserver.local
```

Una vez dentro, actualiza el sistema y configura los ajustes básicos:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo raspi-config
```

En `raspi-config` revisa estos ajustes:

- **Localisation Options**: zona horaria y locale (es_ES.UTF-8)
- **Performance Options**: memoria GPU a 16 MB (sin escritorio no necesitas más)
- **Advanced Options**: expandir el sistema de archivos si no se hizo automáticamente

## Casos de uso prácticos

### Pi-hole: DNS y bloqueo de anuncios

```bash
curl -sSL https://install.pi-hole.net | bash
```

Pi-hole convierte tu Raspberry Pi en un servidor DNS que bloquea anuncios y rastreadores para toda tu red. Tras la instalación, configura tu router para que use la IP de la Pi como DNS primario.

### WireGuard: VPN doméstica

```bash
sudo apt install wireguard -y
wg genkey | tee /etc/wireguard/private.key | wg pubkey > /etc/wireguard/public.key
```

Con WireGuard puedes acceder a tu red local desde cualquier lugar. Combínalo con Pi-hole y tendrás DNS sin anuncios también fuera de casa.

### Samba: almacenamiento en red

```bash
sudo apt install samba -y
sudo mkdir -p /srv/nas/compartido
sudo chown nobody:nogroup /srv/nas/compartido
```

Añade la configuración del recurso compartido en `/etc/samba/smb.conf`:

```ini
[compartido]
path = /srv/nas/compartido
browseable = yes
read only = no
guest ok = no
valid users = tu_usuario
```

Activa el usuario de Samba y reinicia el servicio:

```bash
sudo smbpasswd -a tu_usuario
sudo systemctl restart smbd
```

## Mejoras de rendimiento

### Arrancar desde SSD por USB

La tarjeta microSD es el cuello de botella principal. Para arrancar desde un SSD USB:

```bash
# Verificar que el bootloader está actualizado
sudo rpi-eeprom-update -a

# En la Pi 5, editar el orden de arranque
sudo raspi-config
# Advanced Options > Boot Order > USB Boot
```

Clona la tarjeta SD al SSD con `rpi-imager` o con `dd`, retira la microSD y reinicia. La diferencia en velocidad de lectura es brutal: de ~40 MB/s a más de 300 MB/s.

### Overclock conservador

En `/boot/firmware/config.txt` (Pi 5) o `/boot/config.txt` (Pi 4):

```ini
# Pi 5 - overclock moderado
arm_freq=2600
over_voltage=4

# Pi 4 - overclock moderado
arm_freq=2000
over_voltage=4
```

Monitoriza la temperatura tras el overclock:

```bash
vcgencmd measure_temp
# Si supera los 80 grados, necesitas mejor refrigeración
```

## Alimentación y refrigeración

La alimentación insuficiente es la causa número uno de problemas con la Raspberry Pi. Usa una fuente oficial o de al menos 5V/3A para la Pi 4 y 5V/5A (USB-C PD) para la Pi 5. Un icono de rayo en pantalla o el mensaje `Under-voltage detected` en `dmesg` indican alimentación insuficiente:

```bash
dmesg | grep -i voltage
```

Para refrigeración, un disipador pasivo de aluminio es suficiente para uso normal. Si haces overclock o tienes cargas sostenidas, usa un ventilador activo o una carcasa con refrigeración integrada como la carcasa oficial de la Pi 5.

## Conclusión

Una Raspberry Pi es el punto de entrada perfecto al mundo del homelab. Con un consumo inferior a 10W puedes tener un servidor funcionando las 24 horas del día sin impacto notable en la factura de la luz. Empieza con un servicio sencillo como Pi-hole, familiarízate con la administración remota por SSH y ve añadiendo servicios según tus necesidades.
