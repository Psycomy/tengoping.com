# Plan Editorial — Agosto 2026 (ronda 2)

> Generado el 2026-08-06. 4 artículos planificados.

## Análisis de gaps

Escaneo de los 46 posts existentes (`src/content/blog/*.{md,mdx}`, 1 en draft):

| Categoría      | Posts        |
| -------------- | ------------ |
| Opinión        | 3            |
| Monitorización | 3            |
| Software       | 4            |
| Virtualización | 4 (+1 draft) |
| Seguridad      | 5            |
| Hardware       | 5            |
| Self-Hosting   | 5            |
| Automatización | 7            |
| Linux          | 7            |
| Redes          | 8            |

**Opinión** y **Monitorización** son los mayores huecos (3 posts cada una, sin actualizar desde febrero 2026). Investigación de tendencias (WebSearch, ago 2026) identificó herramientas homelab/self-hosting en auge no cubiertas aún en el blog: Beszel, Caddy, Immich, Jellyfin, K3s, Ollama.

Se seleccionaron 4 temas, los 4 de tipo **searchable** (guías técnicas de herramienta) — el usuario confirmó explícitamente mantener el mix así en vez de introducir una pieza _shareable_, pese a que no refuerza el hueco de Opinión.

**Nota sobre fechas:** el usuario pidió las 4 fechas objetivo el mismo día (2026-08-06) en vez de la cadencia habitual de 1/semana — decisión explícita, documentada aquí como desviación intencional del proceso estándar.

## Artículos planificados

### 1. Beszel: monitorización ligera para Docker

- **Categoría:** Monitorización
- **Tags:** Beszel, Monitorización, Docker, Sysadmin
- **Autor:** antonio
- **Posts relacionados:** monitorizar-servidores-linux-prometheus-grafana, zabbix-monitorizacion-infraestructura
- **Fecha objetivo:** 2026-08-06
- **Tipo:** searchable
- **Brief:** Instalar y usar Beszel para monitorizar servidores y contenedores Docker; alternativa ligera (diseño hub-and-agent) frente a stacks pesados como Prometheus/Grafana o Zabbix, ya cubiertos en el blog.
- **Estado:** completado

### 2. Caddy: proxy inverso con HTTPS automático

- **Categoría:** Redes
- **Tags:** Caddy, Proxy, Redes, HTTPS
- **Autor:** antonio
- **Posts relacionados:** proxy-inverso-nginx-guia-practica, traefik-proxy-inverso-contenedores
- **Fecha objetivo:** 2026-08-06
- **Tipo:** searchable
- **Brief:** Configurar Caddy como proxy inverso con certificados HTTPS automáticos; comparar su simplicidad frente a Nginx y Traefik, ya cubiertos en el blog.
- **Estado:** completado

### 3. Immich: tu galería de fotos autoalojada

- **Categoría:** Self-Hosting
- **Tags:** Immich, Self-Hosting, Fotos, IA
- **Autor:** antonio
- **Posts relacionados:** nextcloud-servidor-nube-personal
- **Fecha objetivo:** 2026-08-06
- **Tipo:** searchable
- **Brief:** Instalar Immich como alternativa autoalojada a Google Fotos, con reconocimiento facial y búsqueda por IA ejecutándose en local.
- **Estado:** completado

### 4. K3s: Kubernetes ligero para tu homelab

- **Categoría:** Virtualización
- **Tags:** K3s, Kubernetes, Virtualización, Homelab
- **Autor:** antonio
- **Posts relacionados:** proxmox-ve-hipervisor-casero, incus-lxc-contenedores-sistema-linux
- **Fecha objetivo:** 2026-08-06
- **Tipo:** searchable
- **Brief:** Desplegar un clúster K3s en un homelab como alternativa ligera a un Kubernetes completo, sobre la base de contenedores/hipervisor ya cubierta en el blog.
- **Estado:** completado
