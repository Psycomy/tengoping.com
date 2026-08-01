---
title: 'btop: monitoriza tu sistema en terminal'
description: 'Guía práctica de btop, el monitor de recursos para terminal: instalación, atajos de teclado esenciales y personalización básica.'
author: 'antonio'
pubDate: 2026-08-01T10:00:00
category: 'Software'
tags: ['Terminal', 'Sysadmin', 'Cheatsheet', 'Linux']
image: '../../assets/images/soft-btop.jpg'
draft: false
---

`top` lleva décadas siendo la herramienta por defecto para ver qué está consumiendo CPU o memoria en un servidor Linux, pero su interfaz apenas ha cambiado desde los 90. `btop` es la alternativa moderna: gráficos en tiempo real de CPU, memoria, disco y red, gestión de procesos con el ratón o el teclado, y una interfaz que se lee de un vistazo incluso con decenas de procesos en pantalla. En esta guía ves cómo instalarlo, los atajos que realmente vas a usar, y cómo encaja en tu flujo de trabajo diario.

## Qué es btop y de dónde viene

`btop` (también llamado btop++) es la tercera generación de una misma idea, escrita cada vez en un lenguaje distinto: primero fue `bashtop` (en Bash), después `bpytop` (reescrito en Python), y finalmente `btop`, reescrito en C++ por el mismo autor, [aristocratos](https://github.com/aristocratos/btop). Cada reescritura buscó lo mismo: más rendimiento y menos dependencias, manteniendo la misma filosofía visual de cajas con gráficos y colores.

A diferencia de `top` o `htop`, `btop` muestra de entrada:

- Gráficos históricos de uso de CPU (total y por núcleo)
- Memoria RAM y swap con desglose por tipo de uso
- Actividad de disco (E/S) y espacio ocupado
- Tráfico de red por interfaz
- Lista de procesos con árbol de jerarquía opcional

Todo se actualiza en vivo y admite tanto teclado como ratón para navegar, redimensionar cajas o matar procesos con un clic.

## Instalación

`btop` lleva unos años en los repositorios oficiales de las distribuciones más comunes, así que en la mayoría de casos no hace falta compilar nada:

```bash
# Debian/Ubuntu (22.04 o superior)
sudo apt install btop

# Fedora
sudo dnf install btop

# RHEL/Rocky/AlmaLinux 8+ (requiere el repositorio EPEL)
sudo dnf install epel-release
sudo dnf install btop

# Arch Linux
sudo pacman -S btop

```

> [!TIP]
> Si tu distribución no trae `btop` en sus repositorios o tienes una versión antigua, el proyecto también se puede compilar desde el código fuente con `cmake` — la documentación oficial en GitHub detalla los pasos exactos, que cambian según la versión del compilador disponible.

## Primer vistazo a la interfaz

Al lanzar `btop` sin argumentos, la pantalla se divide en cajas: CPU arriba, memoria y discos a un lado, red y lista de procesos ocupando el resto. Cada caja se puede redimensionar arrastrando sus bordes con el ratón, o alternar su visibilidad con las teclas numéricas.

```bash
btop
```

## Atajos de teclado esenciales

Estos son los que vas a usar en el día a día:

| Tecla                 | Acción                                                        |
| --------------------- | ------------------------------------------------------------- |
| `1` / `2` / `3` / `4` | Mostrar/ocultar la caja de CPU / memoria / red / procesos     |
| `Esc` o `M`           | Abrir el menú principal (opciones, ayuda, presets)            |
| `F`                   | Filtrar la lista de procesos por nombre, PID o usuario        |
| `E`                   | Alternar la vista de árbol de procesos (jerarquía padre-hijo) |
| `R`                   | Invertir el orden de la lista de procesos                     |
| `C`                   | Alternar el gráfico de CPU entre total y por núcleo           |
| `←` / `→`             | Cambiar la columna por la que se ordenan los procesos         |
| `P`                   | Rotar entre los presets de disposición guardados              |
| `T`                   | Terminar el proceso seleccionado (señal SIGTERM)              |
| `K`                   | Matar el proceso seleccionado (señal SIGKILL)                 |
| `S`                   | Enviar una señal concreta al proceso seleccionado             |
| `Q` o `Ctrl+C`        | Salir (con menú de confirmación)                              |

> [!CAUTION]
> `K` envía `SIGKILL` directamente, sin dar opción al proceso a cerrar limpiamente ni pedir confirmación adicional más allá de tener la fila seleccionada. Si trabajas con la lista de procesos filtrada u ordenada de forma distinta a la habitual, comprueba dos veces qué proceso tienes resaltado antes de pulsarla — usar `T` (SIGTERM) primero es más seguro cuando el proceso puede terminar de forma ordenada.

Si prefieres navegación estilo Vim, activa `vim_keys = true` en la configuración para usar `h`, `j`, `k`, `l`, `g` y `G` como alternativa a las flechas.

## Personalización básica

La configuración vive en `~/.config/btop/btop.conf` y se genera automáticamente la primera vez que ejecutas el programa. Desde el menú (`Esc` o `M` → `Options`) puedes ajustar sin tocar el archivo a mano:

- El tema de colores (btop trae varios preinstalados)
- La frecuencia de actualización de los gráficos
- Qué cajas se muestran por defecto al arrancar
- El comportamiento del gráfico de red (total acumulado vs. por interfaz)

Los cambios se guardan automáticamente en `btop.conf`, así que puedes copiar ese archivo a otro servidor para replicar tu configuración sin repetir el proceso a mano.

## btop dentro de tu flujo de trabajo

`btop` no sustituye a un multiplexor de terminal, pero combina muy bien con uno: si ya usas [tmux o screen](/blog/tmux-screen-multiplexores-terminal-sysadmins/), tener `btop` corriendo en un panel fijo mientras trabajas en otro te da visibilidad constante del sistema sin cambiar de ventana ni de sesión SSH.

Tampoco es un sustituto de una solución de monitorización de infraestructura: `btop` solo ve la máquina en la que se ejecuta, en el momento en que lo estás mirando, sin histórico más allá de lo que quepa en pantalla ni alertas cuando no estás delante. Para vigilar varios servidores a la vez, con histórico y alertas automáticas, necesitas algo como [Prometheus y Grafana](/blog/monitorizar-servidores-linux-prometheus-grafana/). Son herramientas complementarias, no competencia: una para el vistazo rápido local, otra para la vigilancia continua de la flota.

## Siguiente paso

Instala `btop`, déjalo abierto unos días en una sesión de tmux y acostúmbrate a los atajos de la tabla anterior — en menos de una semana sustituye por completo a `top` en tu rutina diaria. Si gestionas varios servidores, el paso lógico después es montar monitorización centralizada para no depender de conectarte a cada uno por SSH para ver cómo está.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
