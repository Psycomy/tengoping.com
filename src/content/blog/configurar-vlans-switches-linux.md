---
title: 'Configurar VLANs en switches gestionados y Linux'
description: 'Guía práctica para configurar VLANs tanto en switches gestionados como en interfaces de red Linux con ip y nmcli.'
author: 'alois'
pubDate: 2026-01-05
category: 'Redes'
tags: ['VLAN', 'Redes', 'Switch', 'Linux']
image: '../../assets/images/redes-vlan.jpg'
draft: false
---

## ¿Qué es una VLAN?

Una VLAN (Virtual LAN) segmenta una red física en redes lógicas independientes. Esto mejora la seguridad, el rendimiento y la organización de la red.

## VLANs en Linux

### Crear una VLAN con ip

```bash
sudo ip link add link eth0 name eth0.100 type vlan id 100
sudo ip addr add 192.168.100.1/24 dev eth0.100
sudo ip link set eth0.100 up
```

### Crear una VLAN con nmcli

```bash
sudo nmcli connection add type vlan \
  con-name vlan100 \
  dev eth0 \
  id 100 \
  ipv4.addresses 192.168.100.1/24 \
  ipv4.method manual
```

## Trunk y access ports

- **Access port**: pertenece a una sola VLAN, tráfico sin tag
- **Trunk port**: transporta múltiples VLANs con tags 802.1Q

## Verificación

```bash
cat /proc/net/vlan/config
ip -d link show eth0.100
bridge vlan show
```

## Buenas prácticas

- Usar VLAN nativa solo para gestión
- Documentar el esquema de VLANs
- Separar tráfico de gestión, datos y VoIP

## Conclusión

Las VLANs son fundamentales para una red bien organizada. Dominar su configuración tanto en switches como en Linux es esencial para cualquier administrador de redes.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
