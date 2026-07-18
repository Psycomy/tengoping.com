---
title: 'tmux y screen: multiplexores de terminal para sysadmins'
description: 'Guía práctica de tmux y screen para mantener sesiones vivas tras cortes de SSH, dividir la terminal en paneles y trabajar más rápido en producción.'
author: 'antonio'
pubDate: 2026-07-18
category: 'Software'
tags: ['tmux', 'screen', 'Terminal', 'Cheatsheet']
image: '../../assets/images/tmux-screen.jpg'
draft: false
---

Si alguna vez se te ha caído el SSH a mitad de una actualización de kernel o una migración larga, ya sabes por qué existe un multiplexor de terminal: te permite mantener sesiones vivas en el servidor, seguir trabajando aunque se corte la conexión, y dividir la pantalla en varios paneles sin abrir diez terminales distintas. En esta guía vemos `tmux` a fondo — el estándar de facto en 2026 — y cuándo todavía tiene sentido recurrir a `screen`.

## Requisitos previos

- Acceso a un servidor Linux por SSH (o terminal local)
- Permisos para instalar paquetes (`sudo apt install` o `sudo dnf install`)
- Comodidad básica con la terminal

## Por qué necesitas un multiplexor de terminal

Sin multiplexor, cada sesión SSH controla un único proceso en primer plano. Si se corta la conexión — VPN inestable, portátil que se suspende, timeout del router — el proceso que lanzaste (una compilación larga, un `rsync`, una migración de base de datos) muere con la sesión, salvo que lo hayas lanzado con `nohup` o `disown`.

Un multiplexor de terminal resuelve esto ejecutando un proceso servidor en la máquina remota que sobrevive a la desconexión. Tu terminal SSH se convierte en un simple cliente que se conecta y desconecta de ese proceso. Además, ambos programas permiten dividir la pantalla en varios paneles y gestionar múltiples "ventanas" dentro de la misma sesión, así que dejas de depender de abrir una conexión SSH nueva por cada tarea que quieras vigilar en paralelo.

## tmux o screen: cuál elegir

|                     | tmux                                                                  | screen                                                         |
| ------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------- |
| Primera versión     | 2007                                                                  | 1987                                                           |
| Arquitectura        | Cliente-servidor, permite varios clientes en la misma sesión a la vez | Cliente-servidor, un modelo más simple                         |
| División de paneles | Nativa y flexible (splits anidados)                                   | Limitada, requiere parches o versiones recientes               |
| Configuración       | `~/.tmux.conf`, sintaxis propia bien documentada                      | `~/.screenrc`, sintaxis más antigua                            |
| Desarrollo activo   | Sí, releases cada pocos meses                                         | Prácticamente parado desde 2023 (última versión estable 4.9.1) |
| Disponibilidad      | Requiere instalación en la mayoría de distros                         | Preinstalado en muchos sistemas antiguos                       |

En la práctica: usa `tmux` salvo que trabajes en un servidor bloqueado donde no puedas instalar paquetes y `screen` ya esté disponible. Es el escenario donde `screen` sigue ganando — no por mejor, sino por estar ya ahí.

## Instalación

```bash
# Debian/Ubuntu
sudo apt install tmux

# RHEL/Fedora/AlmaLinux
sudo dnf install tmux

# Arch
sudo pacman -S tmux
```

Para `screen`, sustituye `tmux` por `screen` en cualquiera de los comandos anteriores.

## Conceptos básicos de tmux

tmux organiza el trabajo en tres niveles:

- **Sesión**: el contenedor principal. Sobrevive a la desconexión SSH. Puedes tener varias sesiones a la vez, cada una para un proyecto o tarea distinta.
- **Ventana**: como una pestaña del navegador dentro de una sesión. Cada ventana ocupa toda la pantalla disponible.
- **Panel**: subdivisión de una ventana. Puedes tener varios paneles visibles a la vez, cada uno con su propio shell independiente.

Todos los comandos de tmux se lanzan con una tecla de prefijo, por defecto `Ctrl+b`. Primero pulsas el prefijo, sueltas, y luego pulsas la tecla del comando.

## Comandos esenciales de tmux

### Gestión de sesiones

```bash
tmux new -s despliegue        # Crea una sesión llamada "despliegue"
tmux ls                       # Lista las sesiones activas
tmux attach -t despliegue     # Vuelve a conectar a esa sesión
tmux kill-session -t despliegue  # Elimina la sesión
```

Dentro de una sesión activa:

- `Ctrl+b d` — te desconecta de la sesión (detach), el proceso sigue corriendo
- `Ctrl+b $` — renombra la sesión actual

### Ventanas

- `Ctrl+b c` — crea una ventana nueva
- `Ctrl+b n` / `Ctrl+b p` — siguiente / anterior ventana
- `Ctrl+b 0-9` — salta directamente a la ventana con ese número
- `Ctrl+b ,` — renombra la ventana actual
- `Ctrl+b &` — cierra la ventana actual (pide confirmación)

### Paneles

- `Ctrl+b %` — crea dos columnas lado a lado (tmux lo llama "split horizontal" porque los paneles quedan dispuestos en horizontal, aunque la línea divisoria sea vertical — es la confusión más habitual con tmux)
- `Ctrl+b "` — crea dos filas, una encima de la otra ("split vertical" en la terminología de tmux)
- `Ctrl+b flechas` — mueve el foco entre paneles
- `Ctrl+b z` — maximiza/restaura el panel actual (zoom)
- `Ctrl+b x` — cierra el panel actual (pide confirmación)

### Copiar y navegar por el histórico

- `Ctrl+b [` — entra en modo copia (puedes usar las flechas o `PgUp`/`PgDn` para desplazarte)
- `q` — sale del modo copia
- `Ctrl+b ]` — pega lo copiado

## Configuración personalizada: ~/.tmux.conf

La configuración por defecto de tmux es funcional pero mejorable. Un `~/.tmux.conf` mínimo pero útil para trabajo en servidores:

```bash
# Cambiar el prefijo de Ctrl+b a Ctrl+a (más cómodo, como screen)
set -g prefix C-a
unbind C-b
bind C-a send-prefix

# Empezar a numerar ventanas y paneles desde 1, no desde 0
set -g base-index 1
setw -g pane-base-index 1

# Habilitar el ratón (cambiar de panel, redimensionar, hacer scroll)
set -g mouse on

# Historial de scroll más largo
set -g history-limit 10000

# Recargar la configuración sin reiniciar tmux
bind r source-file ~/.tmux.conf \; display "Configuración recargada"

# Divisiones más intuitivas, manteniendo el directorio actual
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
```

Aplica los cambios sin salir de tmux con `Ctrl+a r` (o reinicia el servidor tmux con `tmux kill-server` si prefieres empezar de cero).

## screen: lo esencial

Si trabajas en un sistema donde solo tienes `screen` disponible, estos comandos cubren el 90% del uso diario:

```bash
screen -S backup          # Crea una sesión llamada "backup"
screen -ls                # Lista las sesiones activas
screen -r backup          # Reconecta a la sesión "backup"
```

Dentro de la sesión, el prefijo por defecto es `Ctrl+a`:

- `Ctrl+a d` — detach (se desconecta, el proceso sigue vivo)
- `Ctrl+a c` — crea una ventana nueva
- `Ctrl+a n` / `Ctrl+a p` — siguiente / anterior ventana
- `Ctrl+a S` — divide la pantalla horizontalmente
- `Ctrl+a Tab` — cambia el foco entre paneles

`screen` no permite renombrar sesiones tan fácilmente ni anidar paneles con la flexibilidad de tmux, pero para "lanzar un proceso y no perderlo si se corta la conexión" cumple perfectamente.

## Casos de uso reales para sysadmins

**Actualizaciones y migraciones largas.** Lanza el proceso dentro de una sesión tmux, haz `Ctrl+b d`, cierra el portátil si hace falta, y vuelve más tarde con `tmux attach`.

**Paneles de monitorización.** Divide la ventana en cuatro paneles con `htop`, `journalctl -f`, `tail -f /var/log/nginx/access.log` y un shell libre — todo visible a la vez sin cambiar de terminal.

**Sesiones compartidas para pair-troubleshooting.** Como tmux permite que varios clientes se conecten a la misma sesión simultáneamente, dos personas pueden compartir la misma vista del servidor conectándose a la misma sesión desde SSH distintos — útil para depurar un incidente en tiempo real sin compartir pantalla por otra vía.

**Trabajo desconectado en redes inestables.** En una VPN que se cae con frecuencia, mantener el trabajo dentro de tmux evita perder el contexto (directorio, variables de entorno del shell, procesos en marcha) cada vez que la conexión se recupera.

## Automatizar layouts con tmuxinator

Si abres la misma combinación de ventanas y paneles cada vez que empiezas a trabajar en un servidor — un panel con logs, otro con `htop`, otro con el shell principal — reconstruirla a mano cada vez es una pérdida de tiempo. `tmuxinator` arranca un layout completo desde un archivo YAML.

```bash
# Instalación (requiere Ruby)
gem install tmuxinator

# Crea una plantilla para un proyecto llamado "servidor-web"
tmuxinator new servidor-web
```

Esto abre un archivo de configuración para el proyecto — normalmente en `~/.config/tmuxinator/servidor-web.yml`, o en `~/.tmuxinator/servidor-web.yml` si tu instalación ya usaba esa ruta antigua. Un ejemplo funcional:

```yaml
name: servidor-web
root: /var/www

windows:
  - logs:
      layout: even-horizontal
      panes:
        - tail -f /var/log/nginx/access.log
        - tail -f /var/log/nginx/error.log
  - monitor:
      panes:
        - htop
  - shell:
      panes:
        - ''
```

A partir de ahí, `tmuxinator start servidor-web` levanta la sesión completa —tres ventanas, sus paneles y los comandos ya en marcha— en segundos, en lugar de repetir manualmente `Ctrl+b %`, `Ctrl+b "` y los comandos uno por uno cada vez que te conectas.

## Siguiente paso

Con lo anterior ya puedes sustituir `nohup` y sesiones SSH frágiles por sesiones tmux persistentes, y automatizar los layouts que uses a diario. Si administras varios servidores con el mismo flujo de trabajo, vale la pena mantener tus archivos `.tmux.conf` y de `tmuxinator` versionados en Git — el mismo enfoque de infraestructura como código que se explica en la guía de Git para sysadmins.
