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

### Reglas básicas

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

firewalld y ufw simplifican la gestión del firewall para la mayoría de casos según la distro. Para escenarios avanzados, nftables ofrece la flexibilidad necesaria.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
