---
title: 'VLANs explicadas: segmenta tu red doméstica o de laboratorio'
description: 'Qué son las VLANs y el etiquetado 802.1Q, cómo configurarlas en un switch gestionado y en Linux, y cuándo merece la pena segmentar tu red de homelab.'
author: 'antonio'
pubDate: 2026-07-27
category: 'Redes'
tags: ['VLAN', 'Redes', 'Segmentación', 'Switching']
image: '../../assets/images/redes-vlan.jpg'
draft: false
---

Una VLAN (Virtual LAN) divide una red física en varias redes lógicas independientes que comparten el mismo cableado y los mismos switches, pero no ven el tráfico entre sí salvo que un router lo permita explícitamente. Es la herramienta estándar para separar, por ejemplo, tu red de IoT de tus servidores de homelab sin tener que tirar cable nuevo ni comprar switches adicionales.

Ya la mencionamos de pasada al hablar del bridge `vmbr0` de Proxmox y al elegir hardware de homelab; aquí es donde entramos en cómo funciona realmente el etiquetado 802.1Q, cómo configurar puertos trunk y access en un switch gestionado, y cómo crear interfaces VLAN en Linux.

## Cómo funciona el etiquetado 802.1Q

El estándar IEEE 802.1Q define cómo un switch distingue a qué VLAN pertenece cada trama Ethernet: inserta una etiqueta de 4 bytes entre la dirección MAC de origen y el campo EtherType, que incluye un identificador de VLAN (VLAN ID o VID) de 12 bits. Eso da un rango teórico de 0 a 4095, pero el 0 y el 4095 están reservados por el estándar, dejando **1 a 4094** como IDs de VLAN utilizables.

Los puertos de un switch gestionado se comportan de una de estas dos formas:

- **Puerto access (no etiquetado)**: pertenece a una única VLAN. El switch añade la etiqueta al recibir tráfico y la quita antes de entregarlo al dispositivo conectado, que nunca ve ninguna etiqueta 802.1Q. Es el modo normal para conectar un PC, una impresora o un dispositivo IoT.
- **Puerto trunk (etiquetado)**: transporta tráfico de varias VLANs por el mismo cable físico, manteniendo la etiqueta en cada trama para que el switch o dispositivo del otro extremo sepa a qué VLAN pertenece. Se usa entre switches, o entre un switch y un hipervisor/router que necesita distinguir varias VLANs en una sola interfaz de red.

Cada puerto tiene además un **PVID** (Port VLAN ID): la VLAN a la que se asigna el tráfico que llega sin etiquetar por ese puerto. En un puerto access, el PVID coincide con la única VLAN configurada. El PVID por defecto en la mayoría de switches es la VLAN 1 (la "VLAN nativa"), y es buena práctica no dejar dispositivos importantes en la VLAN 1 por defecto, precisamente porque es el valor que todo el mundo asume.

## Configurar VLANs en un switch gestionado

El proceso varía según el fabricante, pero el flujo es el mismo en switches gestionables económicos (TP-Link Easy Smart/Omada, Netgear GS-series, Cisco pequeños):

1. **Crea las VLANs** en la sección de gestión de VLANs, asignando un ID a cada una (por ejemplo: VLAN 10 = Homelab, VLAN 20 = IoT, VLAN 30 = Invitados).
2. **Configura cada puerto** como access de una VLAN concreta (para dispositivos finales) o como trunk (para el enlace hacia el router o hacia otro switch), indicando qué VLANs permite el trunk y cuál es su PVID para tráfico sin etiquetar.
3. **Verifica que el router o firewall** que conecta las VLANs tenga una interfaz o subinterfaz por cada VLAN que necesite enrutar tráfico entre ellas — sin esto, las VLANs quedan aisladas entre sí, que es precisamente el objetivo si no necesitas que se hablen.

Un error habitual: dejar el puerto que conecta al router en modo access de una sola VLAN cuando en realidad necesitas que routee varias. Si el router debe ver tráfico de VLAN 10 y VLAN 20 por el mismo cable físico, ese puerto debe configurarse como trunk en el switch, y el router necesita una subinterfaz etiquetada por cada VLAN.

## Crear interfaces VLAN en Linux

El kernel de Linux soporta 802.1Q de forma nativa a través del módulo `8021q`. Para crear una subinterfaz VLAN sobre una interfaz física:

```bash
# Carga el módulo si no está cargado
sudo modprobe 8021q

# Crea la subinterfaz VLAN 10 sobre eth0
sudo ip link add link eth0 name eth0.10 type vlan id 10

# Actívala y asígnale una IP
sudo ip link set eth0.10 up
sudo ip addr add 192.168.10.1/24 dev eth0.10
```

Esto es temporal — desaparece al reiniciar. Para que persista, defínelo con Netplan (Ubuntu Server) en `/etc/netplan/01-netcfg.yaml`:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
  vlans:
    eth0.10:
      id: 10
      link: eth0
      addresses: [192.168.10.1/24]
```

Aplica el cambio con `sudo netplan apply`. En sistemas con `systemd-networkd` o Debian con `ifupdown`, el mismo concepto se define en sus respectivos ficheros de configuración de red.

Para que esto funcione, la interfaz física `eth0` debe estar conectada a un puerto trunk del switch que incluya la VLAN 10 — si el puerto está en modo access de otra VLAN, el tráfico etiquetado nunca llegará.

## VLANs y Proxmox

En el post sobre Proxmox VE ya vimos que el bridge `vmbr0` se crea sobre la interfaz física durante la instalación. Para asignar una VM a una VLAN concreta sin crear subinterfaces manuales, basta con indicar el VLAN Tag en la configuración de red de esa VM (campo `VLAN Tag` en la pestaña de red del hardware de la VM). Proxmox etiqueta el tráfico de esa VM con el ID indicado sobre el mismo bridge, siempre que el puerto físico al que está conectado el host esté configurado como trunk en el switch.

## Casos de uso en un homelab

Segmentar la red no es solo un ejercicio técnico; resuelve problemas concretos:

- **Aislar IoT**: cámaras, enchufes inteligentes y demás dispositivos IoT suelen tener seguridad pobre y actualizaciones irregulares. Ponerlos en su propia VLAN limita el daño si uno se ve comprometido — no podrá alcanzar directamente tus servidores ni tu NAS.
- **Separar homelab de la red doméstica**: así un experimento que rompa el DNS o el DHCP de tu VLAN de pruebas no tira la conexión a internet del resto de la casa.
- **Red de invitados**: acceso a internet sin visibilidad de ningún dispositivo interno.
- **Tráfico de gestión vs tráfico de datos**: en clústeres de virtualización o almacenamiento, separar la VLAN de administración (acceso a las interfaces de gestión) del tráfico de las VMs reduce superficie de ataque.

## Siguiente paso

Con el etiquetado 802.1Q, los puertos trunk/access y las interfaces VLAN de Linux ya tienes lo necesario para segmentar tu red de homelab. El siguiente paso natural es definir reglas de firewall entre VLANs (qué VLAN puede iniciar conexiones hacia cuál) usando lo que ya vimos en el post de firewalld/nftables, para que la segmentación sea real y no solo una separación de broadcast domains.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
