# Plan Editorial — Agosto 2026

> Generado el 2026-08-03. 4 artículos planificados.
>
> **Nota de publicación:** los 4 artículos se publican el mismo día (2026-08-03), fuera de la cadencia semanal habitual, a petición explícita del usuario. Cada uno debe incluir imágenes y/o diagramas ilustrativos donde el contenido lo justifique (p. ej. diagramas de arquitectura para Incus/LXC y Unikernels, capturas o diagramas de red para Traefik).

## Análisis de gaps

Distribución por categoría a fecha de 2026-08-03 (45 posts publicados, sin drafts):

| Categoría      | Posts |
| -------------- | ----- |
| Linux          | 7     |
| Redes          | 6     |
| Seguridad      | 5     |
| Automatización | 5     |
| Hardware       | 5     |
| Self-Hosting   | 4     |
| Software       | 4     |
| Opinión        | 3     |
| Virtualización | 3     |
| Monitorización | 3     |

Gap más claro: Opinión, Virtualización y Monitorización empatadas al fondo con 3 posts cada una. Además, agosto ya concentró 9 posts nuevos en Linux/Redes/Hardware/Seguridad, así que este ciclo se centra en equilibrar Virtualización y Self-Hosting, con una pieza conceptual (Unikernels) que además ayuda a variar el tipo de contenido del mes.

## Artículos planificados

### 1. Incus/LXC: contenedores de sistema en Linux

- **Categoría:** Virtualización
- **Tags:** LXC, Incus, Virtualización, Linux, Contenedores
- **Autor:** antonio
- **Posts relacionados:** kvm-libvirt-virtualizacion-nativa-linux, introduccion-contenedores-podman-linux
- **Fecha objetivo:** 2026-08-03
- **Tipo:** searchable
- **Brief:** Qué es Incus (fork de LXD tras la salida de Canonical), contenedores de sistema vs contenedores de aplicación (Docker/Podman) vs VMs completas (KVM). Instalación, gestión con `incus`/`lxc` CLI, storage pools, redes, y cuándo elegir LXC sobre Docker en un homelab.
- **Estado:** completado

### 2. Vaultwarden: tu propio gestor de contraseñas autoalojado

- **Categoría:** Self-Hosting
- **Tags:** Vaultwarden, Bitwarden, Self-Hosting, Seguridad
- **Autor:** antonio
- **Posts relacionados:** wireguard-vpn-autoalojada, gitea-servidor-git-autoalojado
- **Fecha objetivo:** 2026-08-03
- **Tipo:** searchable
- **Brief:** Despliegue de Vaultwarden con Docker Compose, hardening (HTTPS obligatorio, admin token, deshabilitar registro), backup de la base de datos y conexión con los clientes oficiales de Bitwarden.
- **Estado:** completado

### 3. Traefik como proxy inverso para contenedores

- **Categoría:** Redes
- **Tags:** Traefik, Proxy, Redes, Docker
- **Autor:** antonio
- **Posts relacionados:** proxy-inverso-nginx-guia-practica, docker-guia-practica-contenedores-linux
- **Fecha objetivo:** 2026-08-03
- **Tipo:** searchable
- **Brief:** Traefik configurado por labels de Docker con descubrimiento automático de servicios, certificados TLS automáticos vía Let's Encrypt, y en qué se diferencia de configurar Nginx manualmente como proxy inverso.
- **Estado:** completado

### 4. Unikernels: qué son y por qué importan

- **Categoría:** Virtualización
- **Tags:** Unikernels, Virtualización, Linux
- **Autor:** antonio
- **Posts relacionados:** kvm-libvirt-virtualizacion-nativa-linux, introduccion-contenedores-podman-linux
- **Fecha objetivo:** 2026-08-03
- **Tipo:** shareable
- **Brief:** Qué son los unikernels, en qué se diferencian de contenedores (Podman/LXC) y máquinas virtuales (KVM), panorama de herramientas (Unikraft, MirageOS, Nanos) y si merece la pena mirarlos hoy en un homelab o en producción.
- **Estado:** completado
