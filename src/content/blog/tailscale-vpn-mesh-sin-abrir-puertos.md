---
title: 'Tailscale: VPN mesh sin abrir puertos'
description: 'Cómo Tailscale usa WireGuard, un servidor de coordinación y relés DERP para crear una VPN mesh sin abrir puertos ni tocar el firewall.'
author: 'antonio'
pubDate: 2026-09-18T10:00:00
category: 'Redes'
tags: ['Tailscale', 'VPN', 'Redes', 'WireGuard', 'Homelab']
image: '../../assets/images/redes-tailscale.jpg'
draft: false
---

Tailscale es una VPN mesh construida sobre [WireGuard](/blog/wireguard-vpn-autoalojada/): en lugar de configurar manualmente un túnel punto a punto, un servidor de coordinación reparte las claves públicas y cada dispositivo negocia una conexión directa con los demás, aunque estén detrás de NAT o de un firewall restrictivo. El resultado práctico es que conectas tu portátil, tu móvil y tu servidor de casa entre sí sin abrir un solo puerto en tu router.

Esa es la diferencia real frente a WireGuard "a pelo": no es un protocolo distinto ni más seguro, es la misma criptografía con una capa de coordinación, descubrimiento de rutas y traducción de NAT encima. Vamos a ver cómo funciona esa capa, cuándo te conviene más que WireGuard puro y cómo montar los casos de uso típicos de un homelab: acceso remoto, exit nodes, subnet routers y control de acceso con ACLs.

## Cómo funciona Tailscale por debajo

Cada dispositivo que instalas ejecuta el cliente `tailscaled`, que genera un par de claves WireGuard y las publica en el servidor de coordinación de Tailscale (`login.tailscale.com` en el caso de la nube gestionada). Ese servidor actúa como un directorio compartido de claves públicas: cada nodo autorizado descarga las claves y últimas ubicaciones de red de los demás nodos de tu red privada (tu "tailnet"), y con eso configura localmente su interfaz WireGuard. Las claves privadas nunca salen del dispositivo — el servidor de coordinación jamás ve tráfico ni puede descifrarlo, solo intercambia metadatos de conexión.

Con las claves ya intercambiadas, cada par de nodos intenta establecer una conexión directa usando técnicas de NAT traversal basadas en los estándares STUN e ICE (agujereado de NAT o "hole punching"): ambos extremos prueban combinaciones de IP y puerto públicos hasta encontrar una ruta que atraviese sus respectivos routers sin necesidad de abrir puertos ni activar UPnP. Según datos técnicos publicados por Tailscale, esta negociación directa tiene éxito en más del 90% de las conexiones en condiciones normales de red.

Cuando la conexión directa no es posible — redes corporativas muy restrictivas, doble NAT en cascada, firewalls que bloquean UDP saliente — el tráfico se reenvía a través de un servidor DERP (_Designated Encrypted Relay for Packets_). Es importante entender qué hace y qué no hace un DERP: reenvía paquetes que ya están cifrados con WireGuard, nunca los descifra ni puede inspeccionarlos, así que actúa como un simple repetidor ciego. Es el mismo papel que cumple un servidor TURN en VoIP/WebRTC, pero implementado sobre HTTPS y las propias claves de WireGuard en vez del protocolo TURN clásico.

```
Panel de control (login.tailscale.com)
   │
   │  reparte claves públicas WireGuard + última IP:puerto conocida de cada nodo
   │
   ├── movil — 100.64.10.3
   ├── laptop-trabajo — 100.64.10.2 (detrás de NAT/CGNAT restrictivo)
   └── home-server — 100.64.10.1 (subnet router + exit node)

Establecer túnel laptop-trabajo → home-server
   │
   ▼
1. Intento de conexión directa (STUN/ICE, hole punching)
   │
   ├── éxito (más del 90% de los casos) → túnel WireGuard cifrado, tráfico peer-to-peer
   └── NAT/firewall bloquea el UDP       → relé vía el servidor DERP más cercano
       (el DERP reenvía paquetes ya cifrados; nunca puede leerlos)
```

Cada dispositivo recibe además una IP fija dentro del rango `100.64.0.0/10`, reservado por la [RFC 6598](https://www.rfc-editor.org/rfc/rfc6598) para direccionamiento CGNAT (Carrier-Grade NAT). Esa IP no cambia aunque el dispositivo salte de WiFi a datos móviles o cambie de red, y no choca con los rangos privados habituales (`10.0.0.0/8`, `192.168.0.0/16`). Sobre ese rango funciona MagicDNS: Tailscale expone un resolutor interno en la IP `100.100.100.100` ("Quad100") que te deja usar el nombre del dispositivo (`home-server` en vez de `100.64.10.1`) sin montar tu propio servidor DNS.

> [!NOTE]
> El servidor de coordinación por defecto es el SaaS de Tailscale, pero el protocolo y el cliente son compatibles con [Headscale](https://github.com/juanfont/headscale), una implementación open source del control server que puedes autoalojar. Sigue usando los clientes oficiales de Tailscale en tus dispositivos, pero el plano de control queda en tu propia infraestructura — a cambio de mantenerlo tú mismo, con menos funciones que el servicio gestionado.

## Tailscale frente a WireGuard puro: cuándo usar cada uno

Si ya conoces [cómo montar WireGuard manualmente](/blog/wireguard-vpn-autoalojada/), la pregunta lógica es cuándo merece la pena añadir esta capa. No son alternativas que compitan por el mismo caso de uso — resuelven problemas distintos:

- **WireGuard puro** te da control total y cero dependencias externas: tú generas las claves, tú escribes los `[Peer]`, tú abres el puerto UDP en tu firewall y configuras el NAT/masquerade. Es la opción correcta para un túnel fijo entre dos o tres servidores donde ya sabes las IPs públicas y no necesitas gestionar altas y bajas de dispositivos con frecuencia.
- **Tailscale** añade valor cuando la topología es dinámica: muchos dispositivos personales que entran y salen de redes con NAT que no controlas (el WiFi de un hotel, datos móviles, una oficina ajena), donde no puedes abrir puertos ni sabes de antemano la IP pública de cada extremo. También aporta MagicDNS, ACLs centralizadas y exit nodes sin tener que escribir reglas de `PostUp`/`PostDown` a mano.

El coste de esa comodidad es la dependencia del servidor de coordinación de un tercero (salvo que autoalojes Headscale) y una superficie de confianza mayor: Tailscale ve metadatos de tu red — qué dispositivos existen, cuándo se conectan, qué rutas anuncian — aunque nunca vea el contenido del tráfico cifrado. Para un túnel simple entre tu VPS y tu casa, WireGuard puro sigue siendo la opción más ligera y con menos piezas de las que fiarte.

## Instalación en Linux

El instalador oficial detecta la distribución y añade el repositorio correspondiente (`apt`, `dnf`, `zypper`, etc.):

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

> [!TIP]
> Si prefieres no ejecutar un script descargado por `curl` directamente, la [página de paquetes de Tailscale](https://tailscale.com/download/linux) enlaza las instrucciones manuales de repositorio para cada distribución, que añaden el mismo paquete sin el paso intermedio del script.

Con el paquete instalado, arranca el cliente y autentica el dispositivo:

```bash
sudo tailscale up
```

El comando imprime una URL de autenticación en el navegador; al aceptarla, el dispositivo queda registrado en tu tailnet y recibe su IP `100.x.y.z`. En un servidor sin navegador (headless), genera antes una clave de autenticación desde el panel de administración y sáltate el paso interactivo:

```bash
sudo tailscale up --authkey=tskey-auth-XXXXXXXXXXXX
```

> [!CAUTION]
> Una clave de autenticación (`authkey`) da de alta un dispositivo nuevo en tu tailnet sin pedir confirmación interactiva. Trátala como un secreto: no la dejes en scripts versionados en un repositorio público ni en el historial de shell de una máquina compartida, y usa claves de un solo uso (`--pre-authorized` reusable = false en el panel) cuando solo la necesites para un aprovisionamiento puntual.

Comprueba el estado de la red y la lista de dispositivos conectados:

```bash
tailscale status
```

## Casos de uso en el homelab

### Acceso remoto directo

Con el cliente instalado en tu portátil y en tu servidor de casa, ambos aparecen el uno para el otro con su IP `100.x.y.z` (o su nombre vía MagicDNS) sin ninguna configuración adicional de red. Es el reemplazo directo de un WireGuard punto a punto cuando quieres acceder por SSH o a un panel web autoalojado — por ejemplo [Nextcloud](/blog/nextcloud-servidor-nube-personal/) — desde fuera de casa sin abrir el puerto 22 o 443 al público.

### Subnet router: acceder a toda la LAN sin instalar Tailscale en cada equipo

Un subnet router es un dispositivo de tu tailnet que anuncia rutas hacia tu red local, para que el resto de nodos lleguen a máquinas que no tienen el cliente de Tailscale instalado (una impresora, una cámara IP, un NAS antiguo). Es conceptualmente similar a segmentar tráfico entre [VLANs](/blog/vlans-explicadas-segmentar-red/): en vez de exponer cada dispositivo individualmente, un único nodo hace de puerta de enlace hacia todo un rango.

En el dispositivo que hará de subnet router necesitas habilitar el reenvío de paquetes en el kernel:

```bash
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

Y anunciar la subred de tu LAN:

```bash
sudo tailscale set --advertise-routes=192.168.1.0/24
```

> [!IMPORTANT]
> Anunciar la ruta no es suficiente: por defecto, un administrador debe aprobarla manualmente desde el panel de administración (_Machines_ → el dispositivo → _Edit route settings_) antes de que el resto de la tailnet pueda usarla. Es una medida de seguridad deliberada para que un dispositivo comprometido no pueda anunciar rutas hacia redes internas sin que nadie se entere.

### Exit node: salir a Internet por otra ubicación

Un exit node convierte un dispositivo de tu tailnet en la puerta de salida a Internet para el resto — el equivalente a "todo el tráfico por la VPN" (`AllowedIPs = 0.0.0.0/0`) en WireGuard, pero seleccionable por dispositivo y sin tocar configuración manual en el cliente. Útil para salir con la IP pública de tu casa desde una red WiFi que no controlas.

En el nodo que hará de salida:

```bash
sudo tailscale set --advertise-exit-node
```

Tras aprobarlo en el panel de administración, cualquier otro dispositivo puede enrutar su tráfico por él:

```bash
sudo tailscale set --exit-node=100.64.10.1
```

Para volver a salir por tu conexión local:

```bash
sudo tailscale set --exit-node=
```

Para confirmar que el tráfico realmente sale por el exit node y no por tu conexión local, comprueba la IP pública desde el cliente:

```bash
curl ifconfig.me
```

La IP devuelta debe corresponder a la red donde vive el exit node, no a la tuya. Para el subnet router, la verificación equivalente es intentar llegar a un dispositivo de la LAN remota que no tiene Tailscale instalado (por ejemplo, `ping 192.168.1.50`) y confirmar en `tailscale status` que la ruta aparece como aprobada, no solo anunciada.

## Control de acceso con ACLs

Por defecto, todos los dispositivos de tu tailnet se ven entre sí. En cuanto añades más de un par de máquinas o algún dispositivo compartido, conviene restringir quién llega a dónde con una política de acceso (ACL), un archivo en formato HuJSON que editas desde el panel de administración:

```json
{
  "tagOwners": {
    "tag:server": ["autogroup:admin"]
  },
  "acls": [
    {
      "action": "accept",
      "src": ["group:familia"],
      "dst": ["tag:server:22,443"]
    }
  ]
}
```

Este ejemplo etiqueta el servidor de casa como `tag:server` y solo permite que los miembros del grupo `familia` lleguen a los puertos 22 (SSH) y 443 (HTTPS) de ese dispositivo — el resto del tráfico queda bloqueado por defecto una vez que defines al menos una regla `acls`. Tailscale también ofrece una sintaxis más reciente llamada _grants_, pensada para sustituir progresivamente a `acls` con reglas más expresivas, aunque el formato clásico sigue siendo totalmente funcional y es más sencillo de leer en una tailnet pequeña.

> [!NOTE]
> Las ACLs no sirven para restringir qué exit node puede usar cada usuario — esa restricción concreta requiere la sintaxis `grants` con la cláusula `via`. Si necesitas limitar el exit node por grupo de usuarios, revisa la [documentación de grants](https://tailscale.com/docs/reference/syntax/grants) antes de asumir que una regla `acls` normal lo cubre.

## Claves, expiración y el plan gratuito

Las claves de nodo de Tailscale expiran a los 180 días por defecto; pasado ese plazo, el dispositivo necesita volver a autenticarse para seguir formando parte de la tailnet. Puedes acortar ese periodo o desactivar la expiración para dispositivos concretos (un subnet router en producción, por ejemplo) desde la sección _Key Expiry_ del panel de administración — desactivarla tiene sentido en infraestructura fija que no quieres que se caiga de la red por olvido, pero reduce la rotación de credenciales, así que resérvalo para los nodos que de verdad lo necesiten.

Para uso personal, el plan gratuito de Tailscale permite hasta 6 usuarios en una misma tailnet con dispositivos de usuario ilimitados, hasta 50 recursos etiquetados y subnet routers/exit nodes incluidos — más que suficiente para un homelab doméstico sin pagar nada.

## Siguiente paso

Tailscale no sustituye a WireGuard, lo envuelve: sigue siendo el mismo túnel cifrado por debajo, con una capa de coordinación que resuelve el problema tedioso de NAT traversal y distribución de claves. Si ya tienes un WireGuard funcionando entre dos o tres servidores fijos, probablemente no necesitas cambiar nada; si tu lista de dispositivos crece, cambia de red constantemente o quieres dar acceso puntual a alguien sin tocar configuración a mano, esa capa de coordinación es exactamente lo que te ahorra tiempo. Un buen siguiente paso una vez tengas la tailnet montada es revisar las ACLs con calma y pasar de "todos ven a todos" a una política explícita por grupo y etiqueta, antes de que el número de dispositivos haga que perder de vista quién llega a dónde sea un problema real.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
