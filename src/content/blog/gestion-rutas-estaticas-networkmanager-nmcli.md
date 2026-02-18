---
title: 'Gestión de rutas estáticas con NetworkManager y nmcli'
description: 'Aprende a gestionar rutas estáticas en Linux usando NetworkManager y nmcli. Guía completa con ejemplos prácticos para administradores de redes.'
author: 'alois'
pubDate: 2025-01-22
category: 'Redes'
tags: ['NetworkManager', 'nmcli', 'Routing', 'Linux']
image: '../../assets/images/network-routes.jpg'
draft: false
---

## Introducción

La gestión de rutas estáticas es fundamental para cualquier administrador de redes. NetworkManager y su herramienta de línea de comandos `nmcli` proporcionan una forma moderna y consistente de gestionar la configuración de red en distribuciones Linux actuales.

## Conceptos básicos de enrutamiento

Antes de empezar, revisemos la tabla de rutas actual:

```bash
ip route show
nmcli connection show
```

### Tipos de rutas

Existen varios tipos de rutas que podemos configurar:

- **Rutas de host**: Apuntan a un host específico (`/32`)
- **Rutas de red**: Apuntan a una subred completa
- **Ruta por defecto**: El gateway de último recurso

## Añadir rutas estáticas con nmcli

### Ruta a una red específica

```bash
nmcli connection modify "ens192" \
  +ipv4.routes "10.10.0.0/16 192.168.1.1"
```

### Ruta con métrica personalizada

```bash
nmcli connection modify "ens192" \
  +ipv4.routes "172.16.0.0/12 192.168.1.254 100"
```

### Aplicar los cambios

```bash
nmcli connection up "ens192"
```

## Verificar rutas configuradas

Podemos verificar las rutas de varias formas:

```bash
# Ver rutas del sistema
ip route show

# Ver rutas configuradas en la conexión
nmcli -f ipv4.routes connection show "ens192"

# Ver detalle completo
nmcli connection show "ens192" | grep route
```

## Eliminar rutas estáticas

Para eliminar una ruta específica:

```bash
nmcli connection modify "ens192" \
  -ipv4.routes "10.10.0.0/16 192.168.1.1"

nmcli connection up "ens192"
```

## Rutas múltiples

Podemos añadir varias rutas en un solo comando:

```bash
nmcli connection modify "ens192" \
  ipv4.routes \
    "10.10.0.0/16 192.168.1.1, \
     172.16.0.0/12 192.168.1.254, \
     192.168.100.0/24 192.168.1.1"
```

## Archivos de configuración

NetworkManager almacena la configuración en archivos keyfile:

```bash
cat /etc/NetworkManager/system-connections/ens192.nmconnection
```

```ini
[ipv4]
method=manual
address1=192.168.1.10/24,192.168.1.1
route1=10.10.0.0/16,192.168.1.1
route2=172.16.0.0/12,192.168.1.254
```

## Troubleshooting

### Comandos útiles para diagnóstico

```bash
# Verificar conectividad
nmcli general status

# Mostrar dispositivos
nmcli device status

# Logs de NetworkManager
journalctl -u NetworkManager -f

# Trazar ruta
traceroute 10.10.1.1
```

## Tabla resumen de comandos

| Acción            | Comando                                   |
| ----------------- | ----------------------------------------- |
| Listar conexiones | `nmcli connection show`                   |
| Añadir ruta       | `nmcli con mod "conn" +ipv4.routes "..."` |
| Eliminar ruta     | `nmcli con mod "conn" -ipv4.routes "..."` |
| Aplicar cambios   | `nmcli connection up "conn"`              |
| Ver rutas         | `ip route show`                           |

## Conclusión

`nmcli` es una herramienta potente y flexible para la gestión de rutas estáticas. Su integración con NetworkManager garantiza la persistencia de las configuraciones entre reinicios y proporciona una interfaz consistente en todas las distribuciones Linux modernas.
