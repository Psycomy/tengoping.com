---
title: 'Beszel: monitorización ligera para Docker'
description: 'Instala Beszel, monitorización ligera con arquitectura hub-and-agent para vigilar CPU, RAM, disco y contenedores Docker sin montar un stack pesado.'
author: 'antonio'
pubDate: 2026-08-06
category: 'Monitorización'
tags: ['Beszel', 'Monitorización', 'Docker', 'Sysadmin']
image: '../../assets/images/mon-beszel.jpg'
draft: false
---

Beszel es una plataforma de monitorización de servidores autoalojada, ligera y de código abierto, que muestra métricas de CPU, memoria, disco, red y contenedores Docker en un dashboard web sencillo. Su diseño hub-and-agent — un panel central que recibe datos de un pequeño agente instalado en cada máquina — la hace especialmente atractiva si ya has probado stacks más completos como [Prometheus y Grafana](/blog/monitorizar-servidores-linux-prometheus-grafana/) o [Zabbix](/blog/zabbix-monitorizacion-infraestructura/) y te han parecido sobredimensionados para un homelab o un puñado de VPS.

## Qué es Beszel y cuándo tiene sentido usarlo

Beszel es un proyecto open source (licencia MIT) mantenido por Henry Gressmann, con el código en [github.com/henrygd/beszel](https://github.com/henrygd/beszel). Según su propia documentación, está pensado para ser "más pequeño y menos exigente en recursos que las soluciones líderes" del sector, con configuración mínima y listo para usar nada más desplegarlo.

El proyecto está construido sobre [PocketBase](https://pocketbase.io/) (Go) para el hub, con un frontend en SvelteKit. Eso explica dos cosas: por qué se distribuye como binario único o imagen Docker sin dependencias externas, y por qué no necesita una base de datos separada como sí requieren Zabbix o el propio Prometheus con su almacenamiento de series temporales.

Tiene sentido elegir Beszel cuando:

- Monitorizas un homelab, varios VPS o un clúster pequeño y no quieres mantener una base de datos de métricas aparte.
- Ya usas Docker en tus hosts y te interesa ver estadísticas de contenedores (CPU, memoria, red) sin instrumentar cada uno con exporters.
- Prefieres un panel que funcione "de fábrica" antes que una plataforma de observabilidad completamente personalizable.

Si necesitas alertas muy configurables con integraciones tipo PagerDuty/Opsgenie, gestión de usuarios avanzada por departamentos, o vas a construir dashboards de negocio complejos, un stack tipo Prometheus/Grafana o Zabbix sigue siendo la opción más madura — Beszel no compite en ese terreno, compite en simplicidad de despliegue y footprint.

> [!NOTE]
> Beszel no sustituye a [Uptime Kuma](/blog/uptime-kuma-monitorizar-servicios-web/) si lo que necesitas es comprobar la disponibilidad externa de un servicio web (HTTP, TCP, ping). Beszel mide el estado interno del host y sus contenedores; Uptime Kuma comprueba si un servicio responde desde fuera. Son complementarios, no alternativas.

## Arquitectura hub-and-agent

Beszel separa el sistema en dos componentes que se instalan por separado:

- **Hub**: la aplicación web (PocketBase) que expone el dashboard, guarda el histórico de métricas y gestiona usuarios, alertas y tokens de registro. Se instala una sola vez.
- **Agente**: un proceso ligero que corre en cada máquina que quieres monitorizar, lee las métricas del sistema (y del socket de Docker, si está disponible) y las envía al hub.

La comunicación entre hub y agente puede darse de dos formas, según la documentación oficial:

- **Modo SSH**: el hub inicia la conexión SSH hacia el agente. Útil cuando el hub puede alcanzar la red del agente pero no al revés.
- **Modo WebSocket**: el agente inicia la conexión hacia la URL del hub. Es el modo recomendado cuando el agente está detrás de NAT o un firewall que no permite conexiones entrantes.

En modo SSH, el agente levanta un servidor SSH minimalista basado en claves ED25519 que el hub genera en su primer arranque. Ese servidor SSH está deliberadamente capado: no ofrece pseudo-terminal ni acepta comandos, así que aunque alguien comprometiera la clave privada del hub no podría ejecutar nada en el agente a través de ese canal. En modo WebSocket, el hub firma un token con su clave privada para demostrar su identidad al agente, y el agente responde con un fingerprint (hash de identificadores de la máquina) que ata su registro a ese host concreto, dificultando que alguien clone o migre un agente registrado a otra máquina.

```
Hub Beszel (puerto 8090, PocketBase + dashboard web)
   │
   │   conexión SSH (la inicia el hub) o WebSocket (la inicia el agente)
   ▼
Agentes (uno por host, puerto 45876 por defecto)
   ├── vps-web-01     → CPU, RAM, disco, red, contenedores Docker
   ├── vps-db-01      → CPU, RAM, disco, red, contenedores Docker
   └── raspberry-nas  → CPU, RAM, disco, temperatura, S.M.A.R.T.
```

> [!TIP]
> No tienes que elegir el modo de conexión a mano en cada agente: si el hub puede alcanzar el agente por red, SSH suele funcionar sin tocar nada; si no, cambia a WebSocket configurando `HUB_URL` en el agente. La documentación oficial señala un caso concreto a vigilar: un host con `iptables -P FORWARD DROP` puede romper el modo SSH de forma silenciosa, sin errores obvios — si un agente no aparece como conectado y usas SSH, revisa esa regla antes de nada.

## Instalar el hub con Docker Compose

El hub es el único componente que necesitas instalar antes de añadir hosts. Necesitas [Docker](/blog/docker-guia-practica-contenedores-linux/) funcionando en el host. Crea un directorio de trabajo y un `docker-compose.yml`:

```yaml
services:
  beszel:
    image: henrygd/beszel
    container_name: beszel
    restart: unless-stopped
    environment:
      - APP_URL=http://tu-servidor:8090 # cambia por tu dominio o IP real
    ports:
      - 8090:8090
    volumes:
      - ./beszel_data:/beszel_data
```

Levanta el contenedor:

```bash
docker compose up -d
```

Abre `http://tu-servidor:8090` en el navegador. La primera vez tendrás que crear el usuario administrador. Desde ese momento, el hub ya genera automáticamente el par de claves ED25519 que usará para autenticar agentes.

> [!IMPORTANT]
> Ajusta siempre `APP_URL` a la dirección real por la que vas a acceder al hub (dominio con HTTPS detrás de un proxy inverso, o IP:puerto si lo usas solo en red local). Si lo dejas en `localhost` y accedes desde otra máquina, algunas funciones internas del hub que dependen de esa URL (como los enlaces generados para OAuth) no funcionarán correctamente.

Si prefieres el binario nativo en lugar de Docker, el proyecto también publica releases descargables en [github.com/henrygd/beszel/releases](https://github.com/henrygd/beszel/releases) — comprueba ahí la versión más reciente antes de fijar una en tus scripts de despliegue.

## Añadir un agente a cada host

Una vez el hub está arriba, cada sistema que quieras vigilar necesita el agente. Desde el dashboard del hub puedes generar un token — incluido un "token universal" en `/settings/tokens` que permite registrar agentes sin tener que crear el sistema de antemano en el panel, cómodo si vas a automatizar el alta de varios hosts a la vez.

### Opción 1: agente con Docker Compose (recomendado si el host ya usa Docker)

```yaml
services:
  beszel-agent:
    image: henrygd/beszel-agent
    container_name: beszel-agent
    restart: unless-stopped
    network_mode: host # necesario para leer estadísticas de red del host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro # solo lectura, para las stats de contenedores
      - ./beszel_agent_data:/var/lib/beszel-agent
    environment:
      - LISTEN=45876
      - KEY=ssh-ed25519-clave-publica-copiada-del-hub
      - HUB_URL=http://tu-servidor:8090
      - TOKEN=el-token-generado-en-settings-tokens
```

```bash
docker compose up -d
```

> [!CAUTION]
> El volumen `/var/run/docker.sock` da al agente visibilidad sobre los contenedores del host — móntalo siempre en modo lectura (`:ro`) como en el ejemplo. Montar el socket de Docker en un contenedor equivale a darle un control muy amplio sobre el host si ese contenedor llegara a verse comprometido; el modo lectura no elimina el riesgo de exponer el socket, pero al menos evita que el agente pueda usarlo para lanzar o modificar contenedores.

### Opción 2: script de instalación (sin Docker, en el propio host)

```bash
# Comprueba la última versión y el contenido del script en
# https://github.com/henrygd/beszel antes de ejecutarlo en producción
curl -sL https://get.beszel.dev -o /tmp/install-agent.sh
chmod +x /tmp/install-agent.sh
sudo /tmp/install-agent.sh -k "ssh-ed25519-clave-publica..." -url "http://tu-servidor:8090" -t "el-token..."
```

Este script instala el agente como binario nativo y lo registra como servicio del sistema, útil en hosts donde no quieres o no puedes correr Docker (por ejemplo, el propio hipervisor).

En ambos casos, el sistema debería aparecer en el dashboard del hub en pocos segundos, mostrando ya las primeras métricas de CPU, memoria y disco. Si tarda más de un minuto en aparecer y usas modo SSH, revisa conectividad y reglas de firewall entre hub y agente antes de sospechar de la configuración del token.

## Qué métricas ofrece y cómo configurar alertas

Beszel recoge, tanto del host como de los contenedores Docker/Podman cuando el socket está disponible:

- Uso de CPU (host y por contenedor)
- Memoria, incluyendo swap y ZFS ARC
- Uso y E/S de disco, con soporte para varias particiones
- Red (host y por contenedor)
- Carga media del sistema
- Temperatura de sensores del host
- GPU (Nvidia, AMD, Intel) y batería, cuando aplica
- Salud S.M.A.R.T. del disco

Las alertas se configuran desde el propio dashboard, por sistema o por defecto para todos: eliges la métrica (CPU, memoria, disco, ancho de banda, temperatura, carga o estado del sistema), un umbral y cuánto tiempo debe mantenerse superado antes de notificar. Beszel soporta autenticación OAuth/OIDC y multiusuario, con la posibilidad de que un administrador comparta sistemas concretos con otros usuarios — algo pensado para equipos donde distintas personas solo deben ver sus propios servidores.

## Beszel frente a Prometheus/Grafana y Zabbix

Ya cubrimos en este blog cómo montar un stack de [Prometheus y Grafana](/blog/monitorizar-servidores-linux-prometheus-grafana/) y cómo desplegar [Zabbix](/blog/zabbix-monitorizacion-infraestructura/) para vigilar infraestructura. Beszel no busca sustituir a ninguno de los dos en entornos donde ya encajan bien — la diferencia está en el punto de partida:

- **Prometheus + Grafana** es un conjunto de piezas independientes (Prometheus para recolectar y almacenar series temporales, Grafana para visualizar, Node Exporter y cAdvisor para exponer métricas) que montas tú mismo y personalizas al detalle. Es la opción con más potencia de consulta (PromQL) y más flexibilidad para dashboards a medida, a cambio de más piezas que mantener.
- **Zabbix** es una plataforma todo-en-uno con servidor, base de datos, frontend web y agentes propios, con más de 20 años de desarrollo y un sistema de triggers y escalado de alertas muy maduro — pero también más pesada de desplegar y administrar.
- **Beszel** apuesta por un binario o imagen única sin base de datos externa, configuración mínima y un dashboard que ya viene hecho. A cambio, no tiene ni de lejos la potencia de consulta de PromQL ni el ecosistema de integraciones de Zabbix.

Si ya tienes Prometheus/Grafana o Zabbix funcionando y cubriendo tus necesidades, no hay motivo para migrar. Pero si tu objetivo real es "quiero ver de un vistazo si mis VPS o contenedores están bien" sin invertir una tarde en configurar exporters y dashboards, Beszel resuelve eso en minutos.

## Siguiente paso

Con el hub y un par de agentes en marcha ya tienes visibilidad básica de tus servidores y contenedores. El siguiente paso lógico es afinar los umbrales de alerta por sistema (no todos los hosts deberían dispararse con el mismo porcentaje de CPU) y decidir si vas a exponer el hub detrás de un proxy inverso con HTTPS en lugar de dejarlo en HTTP plano en red local — sobre todo si vas a acceder desde fuera de tu LAN.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
