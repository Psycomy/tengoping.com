---
title: 'Firewalld, UFW y nftables: seguridad de red en Linux'
description: 'Aprende a configurar firewalld y nftables para proteger tus servidores Linux con reglas de filtrado de tráfico efectivas.'
author: 'antonio'
pubDate: 2026-01-21
category: 'Redes'
tags: ['Firewall', 'nftables', 'Seguridad', 'Redes']
image: '../../assets/images/redes-firewall.jpg'
draft: false
---

## Firewalld: gestión simplificada

Firewalld es el frontend estándar para gestionar el firewall en RHEL, CentOS y derivados. Usa zonas para agrupar reglas.

### Comandos básicos

```bash
sudo firewall-cmd --state
sudo firewall-cmd --list-all
sudo firewall-cmd --get-active-zones
```

### Abrir puertos y servicios

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

### Zonas

Las zonas de firewalld son un buen complemento a la segmentación de red con [VLANs](/blog/vlans-explicadas-segmentar-red/): cada zona puede mapear a una interfaz o VLAN distinta con sus propias reglas.

```bash
sudo firewall-cmd --zone=dmz --add-interface=eth1 --permanent
sudo firewall-cmd --zone=dmz --add-service=http --permanent
```

## UFW en Ubuntu/Debian

UFW (Uncomplicated Firewall) simplifica la gestión del firewall en Ubuntu y Debian con una sintaxis directa.

### Comandos básicos

```bash
sudo ufw status verbose
sudo ufw enable
```

### Abrir puertos y servicios

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 8080/tcp
sudo ufw reload
```

## nftables: control total

nftables es el sucesor de iptables y ofrece una sintaxis unificada.

```
paquete entra por la interfaz
   │
   ▼
PREROUTING            (DNAT, antes de decidir destino)
   │
   ▼
¿destino es este host?
   ├── sí → INPUT → proceso local (sshd, nginx...) → OUTPUT
   └── no → FORWARD  (tráfico enrutado; p. ej. un router/firewall entre redes)
   │
   ▼
POSTROUTING           (SNAT/masquerade, antes de salir —
   │                    llegan tanto INPUT→OUTPUT como FORWARD)
   ▼
paquete sale por la interfaz
```

El ejemplo de abajo engancha su regla justo en el hook `input`, el punto donde llega el tráfico dirigido a este host.

### Reglas básicas

El puerto 22 en el ejemplo es el de [SSH](/blog/configurar-servidor-ssh-seguro-linux/); cámbialo si ya lo has movido a otro puerto.

> [!CAUTION]
> La segunda línea aplica `policy drop` antes de que exista ninguna regla `accept`. Si ejecutas estos comandos uno a uno sobre una sesión SSH remota, te quedarás fuera nada más crear la chain, antes de llegar a la regla que permite el puerto 22. Pega el bloque completo de una vez, o ten una consola alternativa (acceso físico, IPMI) a mano.

```bash
sudo nft add table inet filtro
sudo nft add chain inet filtro input { type filter hook input priority 0 \; policy drop \; }
sudo nft add rule inet filtro input ct state established,related accept
sudo nft add rule inet filtro input tcp dport {22, 80, 443} accept
sudo nft add rule inet filtro input iif lo accept
```

### Listar reglas

```bash
sudo nft list ruleset
```

## ¿Cuál usar?

| Escenario         | Recomendación                    |
| ----------------- | -------------------------------- |
| Servidor estándar | firewalld o ufw                  |
| Reglas complejas  | nftables directo                 |
| Entornos cloud    | security groups + firewall local |

## Conclusión

firewalld y ufw simplifican la gestión del firewall para la mayoría de casos según la distro. Para escenarios avanzados, nftables ofrece la flexibilidad necesaria. Si vas a exponer servicios como una VPN —por ejemplo [WireGuard](/blog/wireguard-vpn-autoalojada/)— no olvides abrir también su puerto UDP correspondiente.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
