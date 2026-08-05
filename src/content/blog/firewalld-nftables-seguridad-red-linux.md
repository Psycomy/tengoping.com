---
title: 'Firewalld, UFW y nftables en Linux'
description: 'Firewalld, UFW y nftables: reglas permanentes vs runtime, rate limiting, persistencia tras reinicio y migración desde iptables.'
author: 'antonio'
pubDate: 2026-01-21
updatedDate: 2026-08-05
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

> [!IMPORTANT]
> `--permanent` escribe la regla en el archivo de configuración, pero **no la aplica** a la sesión de firewall que ya está corriendo — necesitas `--reload` (que no corta conexiones existentes) o un reinicio del servicio para que pase a ser efectiva. Ejecutar el comando sin `--permanent` sí actúa al instante, pero se pierde en el próximo reinicio. Si necesitas probar algo puntual, aplícalo primero sin `--permanent` y, cuando confirmes que es la regla correcta, repítelo con `--permanent --reload`.

### Reglas enriquecidas y NAT

Cuando una zona no es suficientemente específica —por ejemplo, permitir un puerto solo desde una IP concreta— las rich rules añaden condiciones adicionales:

```bash
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.50" port port="5432" protocol="tcp" accept'
sudo firewall-cmd --permanent --zone=public --add-masquerade   # NAT de salida, necesario si este host hace de router
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

### Restringir por origen y limitar la tasa de conexión

```bash
sudo ufw allow from 192.168.1.0/24 to any port 22       # solo esa subred puede llegar a SSH
sudo ufw limit ssh                                        # bloquea una IP que intente 6 conexiones en 30s
```

> [!TIP]
> `ufw limit` es la forma más simple de mitigar fuerza bruta contra SSH sin instalar nada adicional — bloquea temporalmente al origen que se pase de umbral. Para un control más fino (tiempos de baneo configurables, múltiples servicios, notificaciones), la combinación habitual sigue siendo [fail2ban](/blog/configurar-fail2ban-proteger-servicios/) por encima del firewall.

### Gestionar y eliminar reglas

```bash
sudo ufw status numbered      # ver el número de cada regla
sudo ufw delete 3             # eliminar la regla número 3
sudo ufw delete allow 8080/tcp  # o eliminar por especificación, sin buscar el número
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

### Persistir las reglas tras un reinicio

Las reglas creadas con `nft add` viven solo en memoria: un reinicio las borra. Para que sobrevivan, se guardan en un archivo que el servicio `nftables` carga en cada arranque:

```bash
sudo sh -c 'nft list ruleset > /etc/nftables.conf'
sudo systemctl enable --now nftables
```

### Conjuntos con nombre (sets)

Cuando una regla necesita comparar contra una lista larga de valores —puertos, IPs—, un set con nombre es más legible y más rápido de evaluar que repetir la regla para cada valor:

```bash
sudo nft add set inet filtro puertos_permitidos { type inet_service \; }
sudo nft add element inet filtro puertos_permitidos { 22, 80, 443 }
sudo nft add rule inet filtro input tcp dport @puertos_permitidos accept
```

### NAT: masquerade para salida a internet

Si este host hace de puerta de enlace para otra red (el mismo escenario que resuelve `--add-masquerade` en firewalld):

```bash
sudo nft add table ip nat
sudo nft add chain ip nat postrouting { type nat hook postrouting priority 100 \; }
sudo nft add rule ip nat postrouting oif "eth0" masquerade
```

### Migrar desde iptables

Si ya tienes reglas de iptables escritas y quieres su equivalente en sintaxis nftables sin reescribirlas a mano, `iptables-translate` hace la conversión mecánica:

```bash
iptables-translate -A INPUT -p tcp --dport 22 -j ACCEPT
# nft add rule ip filter INPUT tcp dport 22 counter accept
```

> [!NOTE]
> La traducción es literal: convierte cada regla tal cual, sin aprovechar las ventajas propias de nftables (como fusionar reglas IPv4 e IPv6 en una sola tabla `inet`, tal como hace el ejemplo de este artículo). Sirve como punto de partida para migrar, no como configuración final optimizada.

## Registrar los paquetes descartados

Antes de dar por buena una política restrictiva conviene ver qué se está bloqueando, sobre todo mientras ajustas las reglas:

```bash
# firewalld
sudo firewall-cmd --set-log-denied=all
journalctl -k -f | grep -i 'FINAL_REJECT\|FINAL_DROP'

# nftables: log explícito antes del drop, en la propia chain
sudo nft add rule inet filtro input log prefix "drop-input: " counter drop
```

> [!TIP]
> Registrar _todo_ lo descartado en un servidor con tráfico real puede llenar los logs rápido. Úsalo mientras depuras una política nueva y desactívalo (`--set-log-denied=off`) una vez confirmes que las reglas hacen lo esperado.

## ¿Cuál usar?

La elección depende más de la distro y la complejidad del escenario que de una preferencia técnica:

| Escenario                                      | Recomendación                                                                                                                |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Servidor estándar RHEL/Rocky/derivados         | firewalld — ya viene integrado y las zonas encajan con el resto de herramientas de Red Hat                                   |
| Servidor estándar Ubuntu/Debian                | ufw — sintaxis más directa, suficiente para reglas de puerto/servicio habituales                                             |
| Reglas complejas (NAT, sets, múltiples chains) | nftables directo — firewalld y ufw son frontends sobre nftables, y para lógica avanzada conviene saltarse la capa intermedia |
| Entornos cloud (AWS, GCP, Azure...)            | security groups del proveedor + firewall local como segunda capa, nunca solo uno de los dos                                  |

## Conclusión

firewalld y ufw simplifican la gestión del firewall para la mayoría de casos según la distro. Para escenarios avanzados, nftables ofrece la flexibilidad necesaria. Si vas a exponer servicios como una VPN —por ejemplo [WireGuard](/blog/wireguard-vpn-autoalojada/)— no olvides abrir también su puerto UDP correspondiente.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
