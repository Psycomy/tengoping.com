---
title: 'MikroBlockList: blocklist diaria para MikroTik'
description: 'MikroBlockList genera cada día una lista de IPs maliciosas y la carga en el firewall raw de tu MikroTik con RouterOS v7, con validación y modo solo-log.'
author: 'antonio'
pubDate: 2026-11-03
category: 'Seguridad'
tags: ['Seguridad', 'Redes', 'Homelab', 'Auditoría']
image: '../../assets/images/seg-mikroblocklist.jpg'
draft: false
---

**MikroBlockList** es un proyecto open source (GPL-3.0) que cada día descarga varias listas públicas de amenazas, las limpia y publica una única lista de IPs de atacantes y servidores de mando y control (C2) de botnets. Un script en tu router MikroTik con RouterOS v7 la descarga, la valida y la aplica en el firewall `raw`. Es un **proyecto personal**, creado por mí de principio a fin, y este artículo explica cómo funciona, cómo instalarlo sin sustos y qué decisiones de diseño hay detrás.

El código está en [github.com/Psycomy/MikroBlockList](https://github.com/Psycomy/MikroBlockList).

## Un proyecto personal del que estoy orgulloso

MikroBlockList no es un producto de empresa ni un fork de nada: lo he diseñado, programado, probado y documentado yo, y lo mantengo en mi tiempo libre. Parte de una necesidad real, proteger un router MikroTik doméstico con una lista de amenazas que se mantenga sola, y por el camino se ha convertido en algo de lo que estoy genuinamente orgulloso.

No lo digo por presumir, sino por lo que me ha obligado a hacer bien: comparar 44 feeds antes de elegir fuentes, respetar sus licencias (y retirar las que no permiten redistribuir), validar cada línea que llega al router, probarlo en una CHR con RouterOS 7.24.5 y 7.25 y, por último, en un RB2011UiAS físico. Es el tipo de proyecto en el que cada detalle lo has decidido tú, y eso se nota al final.

Lo publico con licencia GPL-3.0 por si a alguien más le sirve. Si lo usas y algo falla, o tienes una idea, las incidencias del repositorio están abiertas.

> [!WARNING]
> Es un proyecto **para uso doméstico y no comercial**. Varias fuentes (DShield, Turris Sentinel, C2IntelFeeds) son CC BY-NC-SA o prohíben el uso comercial, y otras no declaran licencia de redistribución. Si lo necesitas en una empresa, contrata los feeds con licencia comercial. Tampoco está afiliado a MikroTik.

## Qué problema resuelve

Un router doméstico recibe escaneos constantes desde Internet, y dentro de la LAN siempre puede haber un dispositivo (una cámara barata, un IoT olvidado) que acabe hablando con un servidor C2. Una blocklist actualizada corta las dos cosas en el borde de la red:

- **Entrada:** descarta paquetes que llegan desde la interfaz `WAN` con origen en una IP listada.
- **Salida:** descarta, y registra en el log, el tráfico de tus dispositivos de `LAN` hacia una IP listada. Ese log es útil de verdad: una entrada `MBL-OUT` te dice qué equipo de tu red intentó contactar con un host malicioso conocido.
- **Router:** también bloquea el tráfico que genera el propio router hacia esas IPs.

Si ya usas [Fail2Ban](/blog/configurar-fail2ban-proteger-servicios/) en tus servidores, esto es el complemento a otro nivel: Fail2Ban reacciona a lo que ya ha llegado al servicio; una blocklist en el router lo corta antes de que entre en la red.

## Cómo funciona de principio a fin

El proceso tiene dos mitades: una en GitHub, que construye la lista, y otra en tu router, que la consume.

```
GitHub Action (todos los días, 04:17 UTC)
   │
   ▼
1. Descarga fuentes: Spamhaus DROP, DShield, Emerging Threats, CINS Army...
   │
   ▼
2. Limpieza: quita rangos privados/reservados/CGNAT y todo lo más ancho que un /8,
   resta allowlist.txt y los rangos de Cloudflare, Fastly y CloudFront
   │
   ▼
3. Comprobaciones de seguridad
   │
   ├── lista dentro de los límites  → se publica en la rama "lists"
   └── lista rota o sospechosa      → no se publica nada, el router conserva la anterior
   │
   ▼
4. Router (una vez al día, a hora aleatoria): descarga por HTTPS, valida cada línea
   y la carga en una address-list que el firewall raw descarta
```

### Las fuentes

La selección salió de comparar 44 feeds gratuitos por tamaño, solapamiento, falsos positivos frente a rangos de CDN y al top 5.000 de webs, frescura y licencia (el estudio está en `docs/source-study-2026-10-20.md` del repositorio). Hoy se usan, entre otras:

- **Spamhaus DROP**: bloques de red secuestrados o cedidos a operaciones de spam y cibercrimen. Es la única fuente obligatoria: si falla, no se publica nada.
- **Emerging Threats (compromised)**, **DShield**, **CINS Army**, **blocklist.de**, **IPsum nivel 3** y **Turris Sentinel**, de ataques y escaneos.
- **ThreatCluster** y **C2IntelFeeds**, de servidores C2.

Cada fuente descartada tiene su motivo documentado: por ejemplo GreenSnow y Dataplane.org prohíben la redistribución, y ThreatFox se desactivó el 22 de octubre de 2026 porque los términos de abuse.ch no permiten republicar sus datos sin consentimiento.

### Dos variantes: `full` y `lite`

| Variante             | Entradas (3-nov-2026) | Para quién                                                |
| -------------------- | --------------------- | --------------------------------------------------------- |
| `full` (por defecto) | ~34.500               | Routers con RAM suficiente: atacantes, escáneres y C2     |
| `lite`               | ~2.500                | Routers modestos, o si solo quieres lo más grave y los C2 |

Las cifras salen del `stats.json` que se publica en la rama `lists`. El proyecto mide el consumo: en una CHR de 256 MiB con 40.000 entradas quedaban unos 36,7 MiB libres, y nunca menos de 30,5 MiB mientras conviven la lista vieja y la nueva durante la actualización. En un RB2011UiAS (MIPS a 600 MHz, 128 MiB), una actualización diaria `full` mantuvo la CPU al 100 % unos 18 minutos; la `lite` tardó 41 segundos. Por eso el instalador avisa si instalas `full` en un equipo pequeño.

IPv6 es opcional y está desactivado por defecto; es _best effort_ y nunca afecta a las listas IPv4.

## Instalación

### Requisitos previos

- **RouterOS v7.21 o superior** (v6 no está soportado). El proyecto está probado en CHR 7.24.5 y 7.25, y en un RB2011UiAS con 7.25.
- Listas de interfaces llamadas **`WAN`** y **`LAN`**. La configuración por defecto de un MikroTik doméstico ya las tiene.

> [!IMPORTANT]
> Si faltan las listas `WAN` o `LAN`, el instalador se detiene sin cambiar nada. Compruébalo antes con `/interface list print`.

### Instalar en modo solo-log (recomendado)

Antes de bloquear nada, mira qué bloquearía. Pega esto en el terminal de RouterOS (Winbox, WebFig o SSH):

```routeros
:global mblMode "log"; /tool fetch url="https://raw.githubusercontent.com/Psycomy/MikroBlockList/main/routeros/install.rsc" check-certificate=yes; /import install.rsc
```

Al terminar, en unos 20 segundos, imprime algo como `MBL: installed (script 3.5.1, variant full, ipv6 no, mode log)`.

> [!CAUTION]
> `/import install.rsc` **ejecuta** un script descargado de Internet con permisos de administrador. Es lo normal en RouterOS, pero léelo antes en el repositorio ([`routeros/install.rsc`](https://github.com/Psycomy/MikroBlockList/blob/main/routeros/install.rsc)). Lo que sí está diseñado como dato inerte es la _lista_ que se descarga después, no el instalador.

En modo `log` se crean las mismas reglas, pero no se descarta nada: las reglas de entrada solo cuentan y las de salida registran `MBL-OUT` y `MBL-ROUTER`. Ahí es donde aparecerá un falso positivo, es decir, un dispositivo tuyo (o el propio router) intentando llegar a una IP listada.

Cuando estés conforme, pasa a bloquear:

```routeros
:global mblMode "block"; /tool fetch url="https://raw.githubusercontent.com/Psycomy/MikroBlockList/main/routeros/install.rsc" check-certificate=yes; /import install.rsc
```

No hay hueco de protección: las reglas antiguas siguen hasta que las nuevas están puestas. El instalador es idempotente, así que repetirlo sirve también para actualizar o reparar, y conserva tu allowlist.

### Elegir variante o activar IPv6

Se hace con variables globales delante del mismo comando:

```routeros
# Variante lite
:global mblVariant "lite"; /tool fetch url="https://raw.githubusercontent.com/Psycomy/MikroBlockList/main/routeros/install.rsc" check-certificate=yes; /import install.rsc

# IPv6 (se puede combinar con mblVariant)
:global mblIpv6 true; /tool fetch url="https://raw.githubusercontent.com/Psycomy/MikroBlockList/main/routeros/install.rsc" check-certificate=yes; /import install.rsc
```

Cualquier valor no reconocido hace que el instalador pare antes de tocar nada. Las variables viven hasta el próximo reinicio del router, así que si reinstalas en la misma sesión, indica el valor explícitamente.

> [!TIP]
> ¿Error de certificado en el primer `fetch`? En RouterOS 7.21–7.23, o con un almacén de confianza personalizado, el almacén integrado puede no cubrir `fetch` todavía. Mira el valor con `/certificate settings print` y añade `fetch`: `/certificate settings set builtin-trust-store=fetch` (o, si ya hay valores, `fetch,dns,www`).

## Qué crea en tu router

Seis reglas **al principio** de `/ip firewall raw`:

| Comentario                    | Cadena     | Qué hace                                                       |
| ----------------------------- | ---------- | -------------------------------------------------------------- |
| `MBL: allow-in` / `allow-out` | prerouting | Tu allowlist (`mbl-allow`) siempre gana, en entrada y salida   |
| `MBL: in`                     | prerouting | Desde `WAN`, origen en la lista activa → drop                  |
| `MBL: out`                    | prerouting | Desde `LAN`, destino en la lista activa → drop y log `MBL-OUT` |
| `MBL: allow-router-out`       | output     | Allowlist para el tráfico del propio router                    |
| `MBL: router-out`             | output     | Tráfico del router hacia la lista → drop                       |

Además crea las address lists `mbl-a` y `mbl-b` (se alternan en cada actualización), `mbl-allow`, el script `mbl-update`, los schedulers `mbl-daily` y `mbl-boot`, y el fichero `mbl-last.txt` con la última lista buena. Todo lleva el prefijo `mbl` o el comentario `MBL:`, de modo que el desinstalador solo toca lo suyo.

### Por qué en `raw` y no en `filter`

La tabla `raw` actúa antes del seguimiento de conexiones (_connection tracking_). Según la [documentación de MikroTik](https://help.mikrotik.com/docs/spaces/ROS/pages/328513/Building+Advanced+Firewall), permite descartar paquetes antes de que lleguen a ese seguimiento y así reduce notablemente la carga de CPU, algo especialmente útil frente a ataques de denegación de servicio. Con una lista de decenas de miles de entradas, que un escaneo ni siquiera genere entradas en la tabla de conexiones es una ventaja clara. El contrapunto es que `raw` no puede usar matchers que dependan del estado de la conexión, y no hace falta aquí: solo comparamos origen y destino.

## Cómo comprobar que funciona

Compruébalo tras instalar y de vez en cuando:

```routeros
# Todo lo que registra el proyecto (actualizaciones, errores)
/log print where message~"MBL"

# Dispositivos de la LAN que intentaron llegar a un host listado
/log print where message~"MBL-OUT"

# Contadores de paquetes y bytes de cada regla
/ip firewall raw print stats where comment~"MBL"
```

Cada actualización registra además un resumen con lo que han capturado las reglas desde la anterior, por ejemplo: `MBL: dropped since 2026-10-22 03:14:15: in 5120, out 2, router-out 0 packets`. Si la lista en GitHub dejara de actualizarse, el router conserva la última y avisa con `MBL: list is N days old` pasados 3 días.

Para saber si una IP concreta está en la lista, el proyecto incluye una [página de consulta](https://psycomy.github.io/MikroBlockList/) que busca en tu navegador sin enviar nada a ningún sitio.

### Si algo legítimo queda bloqueado

Añádelo a `mbl-allow` (una IP o un CIDR). Las actualizaciones y reinstalaciones nunca borran tus entradas:

```routeros
/ip firewall address-list add list=mbl-allow address=203.0.113.10 comment="mi oficina"
```

Durante la instalación se añaden también las IPs de tus sesiones de administración abiertas, con el comentario `MBL: admin`, para que no puedas quedarte fuera de tu propio router.

## Seguridad: la lista es dato, no código

Descargar una lista de Internet y aplicarla a un firewall es un riesgo si se hace sin cuidado. El diseño parte de una regla: **el router nunca importa ni ejecuta nada del fichero de la lista**. `mbl-update`:

1. Descarga por HTTPS con `check-certificate=yes`. Si falla, no cambia nada.
2. Exige una cabecera con formato conocido y un pie con el mismo número de entradas, de modo que una página de error HTML nunca se acepta.
3. Valida cada línea: debe ser una IPv4 o un CIDR con prefijo de 8 a 32. Una línea como `/system reboot` es simplemente una línea inválida.
4. Rechaza la carga y mantiene la lista activa si falta la cabecera o el pie, si los contadores no cuadran, si más del 1 % de las líneas son inválidas o si se añaden menos de 1.000 entradas.
5. Solo entonces cambia las reglas a la lista nueva y vacía la vieja.

En el lado del servidor hay otro conjunto de barreras: la lista `full` debe tener entre 5.000 y 150.000 entradas, no puede caer más del 50 % ni crecer más de 2× respecto a la anterior, y la fuente Spamhaus DROP debe haber funcionado. También hay un tope del 10 %: si la allowlist (estática más CDN) eliminaría más del 10 % de las direcciones o tocaría más del 10 % de las entradas, el build falla en vez de publicar. Normalmente significa que un feed ha empezado a listar rangos de CDN o de nube enteros.

El riesgo residual lo documenta el propio proyecto: si alguien comprometiera la cuenta del publicador, lo peor sería una lista falsa que bloquee direcciones (por ejemplo, tu resolutor DNS), nunca ejecución de código en tu router. Por eso conviene tener en `mbl-allow` lo que no puedes perder. Si montas tus redes con [VLANs](/blog/vlans-explicadas-segmentar-red/), recuerda que las listas `LAN` y `WAN` deben cubrir también esas interfaces.

## Usarla fuera de MikroTik

La rama `lists` publica también `blocklist.txt` (una IPv4 o CIDR por línea, sin cabecera) y `blocklist6.txt`. Sirven como fuente para otros firewalls: pfSense, OPNsense, `ipset` o [nftables](/blog/firewalld-nftables-seguridad-red-linux/), con las mismas limitaciones de licencia.

## Desinstalar

```routeros
/tool fetch url="https://raw.githubusercontent.com/Psycomy/MikroBlockList/main/routeros/uninstall.rsc" check-certificate=yes; /import uninstall.rsc
```

Elimina solo lo que creó el instalador (nombres `mbl-*`, comentarios `MBL:`, ficheros `mbl-*` y las entradas `MBL: admin`). Tus entradas de `mbl-allow` se conservan. No revierte el componente `fetch` añadido a `builtin-trust-store`: si quieres, hazlo a mano.

## Conclusión

MikroBlockList intenta que una blocklist en el router sea aburrida, que es lo que quieres de una pieza de seguridad: se instala con una línea, se prueba antes en modo log, se actualiza sola, valida todo lo que descarga y, ante cualquier duda, conserva la última lista buena. Si lo pruebas, empieza por `mblMode "log"` unos días y revisa los `MBL-OUT`. Y si encuentras un falso positivo o un fallo, el repositorio tiene plantillas de incidencia para ambos.

Para mí es mucho más que un script: es un proyecto propio que ha crecido a base de pequeñas decisiones, y me hace ilusión compartirlo. Si te resulta útil, una estrella en [GitHub](https://github.com/Psycomy/MikroBlockList) o un comentario con tu experiencia me ayudan a seguir mejorándolo.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
