---
title: 'Proxmox VE Helper-Scripts: guía y buenas prácticas'
description: 'Qué son los Proxmox VE Helper-Scripts de community-scripts.org, cómo despliegan LXC y VMs con un solo comando y qué riesgos de seguridad debes valorar.'
author: 'antonio'
pubDate: 2026-08-04
category: 'Virtualización'
tags: ['Proxmox', 'LXC', 'Homelab', 'Automatización']
image: '../../assets/images/virt-proxmox.jpg'
draft: false
---

Los Proxmox VE Helper-Scripts son una colección de scripts Bash mantenida por la comunidad en [community-scripts.org](https://community-scripts.org/) que despliegan aplicaciones autohospedadas ya configuradas —en contenedores LXC o en máquinas virtuales QEMU, según el script— con un único comando pegado en el shell de Proxmox. Lo que antes eran quince o veinte minutos creando un contenedor o una VM a mano, instalando dependencias y ajustando la red, se reduce a copiar una línea y esperar. A cambio, estás ejecutando código de terceros como root en tu hipervisor, así que conviene entender qué hace el script antes de pegarlo.

## Qué son los Proxmox VE Helper-Scripts

El proyecto nació como el repositorio personal de [tteck](https://github.com/tteck), que durante años fue la referencia para automatizar despliegues en Proxmox VE. Tras su fallecimiento a finales de 2024, la comunidad archivó el repositorio original de mutuo acuerdo con él y continuó el trabajo bajo la organización [community-scripts/ProxmoxVE](https://github.com/community-scripts/ProxmoxVE) en GitHub, con licencia MIT y mantenimiento por voluntarios. Hoy el repositorio suma más de 500 scripts solo para desplegar aplicaciones, organizados en varias carpetas según lo que crean:

- `ct/` — contenedores LXC (la mayoría de los scripts)
- `vm/` — máquinas virtuales QEMU completas
- `install/` — lógica de instalación que usan los scripts de `ct/`, uno por aplicación (`adguard-install.sh`, `docker-install.sh`...)
- `tools/pve/` — scripts que configuran el propio host Proxmox, no un invitado
- `turnkey/` — un único script (`turnkey.sh`) que despliega como LXC cualquier plantilla TurnKey Linux disponible, en vez de un script por aplicación

Cada aplicación tiene su propia ficha en community-scripts.org con la descripción, los recursos por defecto (CPU, RAM, disco) y el comando exacto para instalarla.

## Cómo funciona el script principal

La forma habitual de usarlos es pegar un comando como este directamente en el shell del nodo Proxmox (no dentro de un contenedor):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/adguard.sh)"
```

`curl -fsSL` descarga el script silenciando la barra de progreso (`-s`), mostrando errores (`-S`), siguiendo redirecciones (`-L`) y fallando limpiamente si el servidor devuelve un error HTTP (`-f`). `bash -c` ejecuta ese contenido inmediatamente. El script descargado (`adguard.sh` en este ejemplo) es solo un punto de entrada: carga `build.func`, la librería compartida que dibuja el menú de configuración, valida que el nodo tenga espacio y plantillas disponibles, y finalmente llama a `pct create` para levantar el contenedor. Una vez creado, ejecuta dentro el script correspondiente de `install/` que instala y configura la aplicación.

```
$ bash -c "$(curl -fsSL .../ct/adguard.sh)"
   │
   ▼
1. curl descarga adguard.sh → bash lo ejecuta al vuelo
   │
   ▼
2. build.func muestra el menú de configuración
   │
   ├── "Default Settings" → usa CPU/RAM/disco recomendados por la app
   └── "Advanced Settings" → permite fijar CTID, hostname, red, storage...
   │
   ▼
3. pct create crea el contenedor LXC con la plantilla Debian/Ubuntu
   │
   ▼
4. Dentro del contenedor se ejecuta install/adguard-install.sh
   │
   ▼
5. Contenedor listo, con AdGuard Home escuchando en su IP
```

Este patrón —descarga, `build.func`, `pct create`, script de `install/`— es el que siguen los scripts de `ct/`, que son la mayoría del repositorio; solo cambia qué instala el paso 4. Los scripts de `vm/` comparten la misma capa de menú y validaciones, pero a partir de ahí el flujo es distinto, como se explica a continuación.

### Personalizar recursos sin usar el menú

Si ya sabes qué recursos necesita el contenedor, puedes saltarte el menú interactivo pasando variables de entorno antes del comando:

```bash
var_cpu=4 var_ram=8192 var_disk=20 bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/adguard.sh)"
```

También existen `VERBOSE=yes` para ver el detalle de cada paso y `DEV_MODE_LOGS=true` para depurar un script que falla. Para actualizar una aplicación ya instalada, se vuelve a ejecutar el mismo comando añadiendo `-s update` **después** de la comilla de cierre, no dentro de la URL:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/adguard.sh)" -s update
```

El script detecta que el contenedor ya existe y ejecuta la rutina de actualización en vez de crear uno nuevo.

## Máquinas virtuales y herramientas del host

No todo el catálogo crea contenedores LXC: un grupo más reducido de scripts, agrupados en `vm/`, crea máquinas virtuales QEMU completas en su lugar, útiles cuando la aplicación necesita passthrough de hardware, un kernel propio o simplemente no está pensada para correr en un contenedor (por ejemplo, sistemas operativos completos como openSUSE o Home Assistant OS). El flujo interno cambia respecto al de los contenedores: en vez de `pct create`, estos scripts usan `qm create` para definir la VM y, en muchos casos, descargan e importan directamente una imagen de disco ya preparada (un `.qcow2`, por ejemplo) con `qm disk import`, en lugar de ejecutar un script de `install/` dentro del invitado — la aplicación ya viene lista en esa imagen. Si ya usas máquinas virtuales fuera de Proxmox, la lógica de fondo es la misma que la que se explica en [KVM y libvirt: virtualización nativa en Linux](/blog/kvm-libvirt-virtualizacion-nativa-linux/) — Proxmox añade encima una capa de gestión y estos scripts automatizan la creación de la VM sobre esa base.

Por otro lado, `tools/pve/` no toca los invitados: configura el propio nodo Proxmox. El más usado es el script de post-instalación:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/tools/pve/post-pve-install.sh)"
```

Ofrece desactivar el repositorio "enterprise" (que requiere suscripción de pago) y activar el "no-subscription" gratuito, quitar el aviso de suscripción en la interfaz web y aplicar algunas optimizaciones habituales. Como modifica los repositorios `apt` del host, revisa qué opciones marcas antes de confirmar.

## PVEScripts-Local: un catálogo con interfaz web

Para no depender de tener la web de community-scripts.org abierta en otra pestaña, el proyecto ofrece un contenedor LXC que despliega un catálogo local:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/pve-scripts-local.sh)"
```

Se instala con 4 GB de disco, 2 vCPU y 4096 MB de RAM por defecto, y queda accesible en `http://IP_DEL_CONTENEDOR:3000`. Es importante entender su límite: la interfaz te muestra el comando `bash -c "..."` de cada script para que lo copies y pegues en el shell del nodo — no ejecuta nada por ti automáticamente. Sigue siendo el mismo modelo de "revisa y pega", solo que con buscador y categorías.

## Seguridad: qué implica ejecutar `curl | bash` como root

El patrón `curl -fsSL URL | bash` (o su variante `bash -c "$(curl ...)"`, funcionalmente equivalente) es cómodo pero tiene dos problemas conocidos que conviene separar:

> [!WARNING]
> Estos comandos se ejecutan en el **shell del nodo Proxmox con privilegios root**, no dentro de un contenedor aislado. Un script malicioso o con un bug grave puede afectar a todo el hipervisor y, por extensión, a todas las VMs y contenedores que aloja.

- **Confianza en la fuente:** al pegar el comando estás confiando en que el mantenedor del repositorio no ha introducido código malicioso ni ha sido comprometido. `community-scripts/ProxmoxVE` es un proyecto abierto con licencia MIT y cientos de colaboradores, lo que da visibilidad, pero no es una garantía absoluta frente a un commit malicioso puntual.
- **Ejecución parcial:** técnicamente es posible que un servidor detecte que la petición viene de una tubería hacia `bash` y sirva contenido distinto al que se mostraría al abrir la misma URL en un navegador. Es un vector poco probable en un repositorio público y versionado como este, pero es la razón técnica detrás de la recomendación general de no encadenar `curl | bash` a ciegas con cualquier fuente.

### Buenas prácticas antes de pegar un comando

- **Descarga y lee el script antes de ejecutarlo** si es la primera vez que usas uno de un repositorio nuevo para ti: `curl -fsSL URL -o script.sh && less script.sh`. Para los scripts de `community-scripts/ProxmoxVE` en concreto, el código es público y auditable en GitHub.
- **No ejecutes estos comandos dentro de un contenedor o VM ya existente** salvo que el script esté explícitamente pensado para ello (algunos, como el de post-instalación, sí van dirigidos al host).
- **Fija los recursos con variables (`var_cpu`, `var_ram`, `var_disk`)** en vez de aceptar los valores por defecto sin mirarlos, especialmente en un nodo con recursos ajustados.
- **Haz un snapshot o backup del nodo/contenedor antes de una actualización (`-s update`)** si la aplicación es crítica; una actualización que falla a mitad puede dejar el contenedor en un estado inconsistente.
- **Revisa periódicamente qué contenedores creaste con estos scripts** — es fácil acumular una docena de LXC de prueba y perder la cuenta de cuáles siguen recibiendo actualizaciones de seguridad del sistema operativo base.

> [!TIP]
> Si vas a levantar varios servicios de este catálogo, merece la pena planificar antes qué hardware necesitas realmente — la guía [Cómo elegir hardware para tu homelab](/blog/elegir-hardware-homelab/) cubre CPU, RAM y almacenamiento para este tipo de uso.

## LXC vs. contenedor Docker dentro de LXC

Un contenedor LXC creado por estos scripts es un contenedor de sistema completo (con su propio init, usuarios y systemd), no un contenedor de aplicación como los que gestiona Docker. Si vienes de Docker, la diferencia de modelo es la misma que se explica en [Incus/LXC: contenedores de sistema en Linux](/blog/incus-lxc-contenedores-sistema-linux/): un LXC se comporta como una VM ligera, mientras que Docker empaqueta un solo proceso y sus dependencias. De hecho, uno de los scripts más usados del catálogo (`docker.sh`) simplemente crea un LXC y le instala Docker dentro, combinando ambos modelos.

## Conclusión

Los Proxmox VE Helper-Scripts son la forma más rápida de probar un servicio autohospedado en Proxmox sin perder media tarde configurando un contenedor a mano, y su continuidad tras la comunidad que asumió el proyecto en 2024 lo confirma como una herramienta madura y con buen mantenimiento. La contrapartida es que cada comando que pegas se ejecuta como root en tu hipervisor: trátalos con la misma cautela que cualquier otro script de terceros, revisa el código cuando pruebes una aplicación por primera vez y mantén copias de seguridad antes de actualizar servicios que ya estén en producción en tu homelab.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
