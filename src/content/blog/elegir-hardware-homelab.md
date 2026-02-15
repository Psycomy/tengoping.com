---
title: "Cómo elegir hardware para tu homelab"
description: "Consejos prácticos para montar un homelab sin arruinarte: mini PCs, servidores usados, almacenamiento y consumo eléctrico."
author: "alois"
pubDate: 2025-10-30
category: "Hardware"
tags: ["Homelab", "Hardware", "Servidores", "Self-Hosting"]
image: "/images/homelab-hardware.jpg"
draft: false
---

## Que es un homelab

Un homelab es un laboratorio doméstico donde experimentas con tecnología de servidores, redes y servicios que normalmente encontrarías en un entorno empresarial. Puede ser algo tan sencillo como una Raspberry Pi corriendo Pi-hole o tan complejo como un rack con varios servidores, switches gestionables y almacenamiento compartido. El objetivo es aprender, practicar y autohospedar servicios sin depender de la nube.

## Mini PCs: la opción silenciosa y eficiente

Los mini PCs de segunda mano son probablemente la mejor relación calidad-precio para un homelab doméstico. Los modelos más populares en la comunidad:

### Lenovo ThinkCentre Tiny (M720q, M920q, M75q)

Compactos, fiables y fáciles de encontrar en el mercado de segunda mano. Los modelos con procesador Intel de octava o novena generación ofrecen un rendimiento excelente para virtualización. Soportan hasta 64 GB de RAM (SO-DIMM DDR4) y tienen una bahía para disco M.2 NVMe más una bahía SATA de 2.5 pulgadas.

### HP EliteDesk 800 G5/G6 Mini

Similar al Lenovo Tiny en prestaciones. Buena ventilación para su tamaño y opción de doble NIC en algunos modelos, lo que es ideal si quieres usarlo como router o firewall con OPNsense.

### Dell OptiPlex Micro (3080, 5080, 7080)

La gama OptiPlex Micro es otra alternativa sólida. Los modelos de gama alta incluyen vPro para gestión remota (KVM sobre IP), algo muy útil cuando el equipo no tiene pantalla conectada.

Precio orientativo: entre 80 y 200 EUR en plataformas de segunda mano, dependiendo del procesador y la RAM incluida.

## Servidores enterprise usados

Si necesitas más potencia, más bahías de disco o funcionalidades avanzadas como IPMI/iLO/iDRAC para gestión remota, los servidores enterprise de segunda mano son una opción:

### Dell PowerEdge (R720, R730, R740)

Los PowerEdge son los más populares en homelabs. Un R730 con dos Xeon E5-2680v3 y 128 GB de RAM DDR4 ECC se puede encontrar por menos de 300 EUR. Incluyen iDRAC para gestión remota completa (consola virtual, encendido/apagado, monitorización).

### HP ProLiant (DL360, DL380)

Equivalentes a los PowerEdge de Dell. Los modelos Gen9 y Gen10 ofrecen procesadores modernos y buen soporte de RAM. La interfaz iLO es excelente para gestión fuera de banda.

El inconveniente principal de estos servidores es el ruido y el consumo. Un R730 en reposo puede consumir entre 100 y 150W y sus ventiladores son audibles. No es ideal si el homelab está en el salón o el dormitorio.

## RAM y CPU: que priorizar

Para virtualización con Proxmox, ESXi o KVM, la RAM es generalmente más importante que la CPU. Cada máquina virtual o contenedor necesita su porción de memoria, y quedarse sin RAM es el cuello de botella más habitual.

Orientaciones según uso:

| Uso | RAM mínima | CPU recomendada |
|---|---|---|
| Pi-hole, DNS, pequeños servicios | 4-8 GB | Cualquier x86_64 moderno |
| Docker con 10-15 contenedores | 16-32 GB | 4+ cores |
| Proxmox con 5-10 VMs | 32-64 GB | 8+ cores, VT-x/VT-d |
| Cluster Kubernetes casero | 64+ GB (repartido) | Varios nodos con 4+ cores |

Comprueba siempre que el procesador soporte virtualización por hardware:

```bash
# Verificar soporte de virtualización
grep -cE '(vmx|svm)' /proc/cpuinfo
# Si el resultado es mayor que 0, tienes soporte de virtualización
```

## Almacenamiento: HDD vs SSD

### SSD para el sistema operativo y VMs

Un SSD NVMe de 256-512 GB para el sistema operativo y las máquinas virtuales marca una diferencia enorme en rendimiento. Los tiempos de arranque de las VMs pasan de minutos a segundos.

### HDD para almacenamiento masivo

Los discos duros mecánicos siguen siendo imbatibles en coste por terabyte para almacenamiento de datos, backups y multimedia. Un disco de 4 TB cuesta alrededor de 80 EUR.

### Planificación de capacidad

Calcula cuánto espacio necesitas y multiplica por 1.5 como margen. Si vas a usar RAID 1, necesitas el doble de discos. Con RAID 5 o RAID-Z1, pierdes la capacidad equivalente a un disco del total.

```bash
# Ver los discos disponibles y su capacidad
lsblk -d -o NAME,SIZE,MODEL,ROTA
# ROTA=1 es HDD rotacional, ROTA=0 es SSD
```

## Red: no subestimes el networking

### Switch gestionable

Un switch gestionable barato (TP-Link TL-SG108E, Netgear GS308E) por 30-40 EUR permite crear VLANs para segmentar tu red: una VLAN para los servicios del homelab, otra para IoT, otra para el tráfico doméstico normal.

### 2.5 GbE

Si vas a mover archivos grandes entre equipos, considera tarjetas de red y switches de 2.5 GbE. Las tarjetas PCIe Realtek RTL8125B cuestan menos de 15 EUR y los switches 2.5GbE empiezan en 50 EUR. La diferencia frente a Gigabit es notable cuando haces backups o transferencias de archivos grandes.

```bash
# Comprobar la velocidad de enlace de tu interfaz de red
ethtool eth0 | grep Speed
```

## Consumo electrico y ruido

El consumo eléctrico es un factor que muchos ignoran hasta que llega la factura. La diferencia entre opciones es considerable:

| Equipo | Consumo en reposo | Ruido |
|---|---|---|
| Raspberry Pi 5 | 5-10W | Silencioso |
| Mini PC (Lenovo Tiny) | 8-15W | Silencioso |
| PC sobremesa reconvertido | 30-60W | Moderado |
| Servidor enterprise (1U/2U) | 80-200W | Alto |

Para calcular el coste anual aproximado:

```bash
# Formula: Vatios * 24h * 365 dias / 1000 * precio_kWh
# Ejemplo: mini PC a 12W con electricidad a 0.15 EUR/kWh
echo "scale=2; 12 * 24 * 365 / 1000 * 0.15" | bc
# Resultado: 15.77 EUR/anio
```

Un servidor enterprise a 150W con el mismo precio de electricidad cuesta unos 197 EUR al año solo en electricidad. Merece la pena tenerlo en cuenta.

## Builds recomendados por presupuesto

### Presupuesto bajo (menos de 100 EUR)

- Raspberry Pi 5 8GB + SSD USB de 256 GB + carcasa con ventilador
- Ideal para: Pi-hole, WireGuard VPN, Home Assistant, contenedores ligeros

### Presupuesto medio (150-300 EUR)

- Mini PC Lenovo Tiny M720q de segunda mano + 32 GB RAM + SSD NVMe 512 GB
- Ideal para: Proxmox con varias VMs, Docker, NAS ligero

### Presupuesto alto (400-600 EUR)

- Dos mini PCs para cluster + switch gestionable + NAS dedicado con 2 discos en RAID 1
- Ideal para: Kubernetes casero, alta disponibilidad, almacenamiento redundante

## Conclusion

No necesitas gastar una fortuna para montar un homelab funcional. Un mini PC de segunda mano con suficiente RAM puede ser todo lo que necesitas para empezar. Prioriza la RAM sobre la CPU, elige SSD para el sistema y HDDs para almacenamiento masivo, y ten siempre en cuenta el consumo eléctrico a largo plazo. El mejor homelab es el que usas, no el que tiene más luces LED en un rack.
