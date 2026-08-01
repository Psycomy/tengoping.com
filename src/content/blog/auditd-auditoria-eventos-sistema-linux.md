---
title: 'auditd: audita el sistema en Linux'
description: 'auditd registra en el kernel quién cambió qué archivo y cuándo. Aprende reglas -w y -a/-S, ausearch, aureport y el modo inmutable -e 2.'
author: 'antonio'
pubDate: 2026-08-01T11:00:00
category: 'Seguridad'
tags: ['Auditoría', 'Seguridad', 'Hardening', 'Linux']
image: '../../assets/images/linux-auditd.jpg'
draft: false
---

Cuando algo cambia en un servidor — un fichero de configuración editado, un binario ejecutado, un usuario que lee un archivo que no debería — los logs habituales rara vez dicen quién lo hizo y cómo. `auditd` es el subsistema de auditoría del kernel Linux: engancha las llamadas al sistema y los accesos a archivos que tú decidas vigilar, y deja un rastro con usuario, proceso y momento exacto. En la [guía de hardening básico](/blog/hardening-basico-servidores-linux/) ya vimos cómo activarlo con unas reglas mínimas; aquí profundizamos en cómo escribir reglas propias y consultar lo que auditd va registrando.

## Instalar y activar auditd

En RHEL, Rocky u Oracle Linux el paquete se llama `audit`; en Debian y Ubuntu, `auditd`. En ambos casos el servicio que arranca se llama `auditd`:

```bash
# RHEL/Rocky/Oracle Linux
sudo dnf install audit -y

# Ubuntu/Debian
sudo apt install auditd -y

# Activar y arrancar en ambos casos
sudo systemctl enable --now auditd
```

Los eventos van a `/var/log/audit/audit.log`, y la configuración del propio demonio (rotación, espacio máximo, qué hacer si el disco se llena) vive en `/etc/audit/auditd.conf`. Para las reglas de qué auditar, en cambio, se usan ficheros aparte.

## Dos tipos de reglas: archivos y llamadas al sistema

`auditd` distingue entre vigilar un archivo concreto y vigilar una llamada al sistema (syscall) en cualquier proceso.

### Reglas `-w`: vigilar archivos y directorios

Una regla `-w` (`--watch`) engancha el acceso a una ruta concreta. Se combina con `-p` para decir qué tipo de acceso te interesa:

```bash
# -p acepta cualquier combinación de r (lectura), w (escritura),
# x (ejecución) y a (cambio de atributos/permisos)
sudo auditctl -w /etc/passwd -p wa -k identity
sudo auditctl -w /etc/shadow -p wa -k identity
sudo auditctl -w /etc/sudoers -p wa -k sudoers
```

> [!NOTE]
> `-p` no son los permisos habituales de Unix (`rwx` de `chmod`) — son el tipo de syscall que dispararía la regla. Por ejemplo `w` cubre tanto escribir contenido como truncar el archivo.

### Reglas `-a`/`-S`: vigilar llamadas al sistema

Cuando lo que te interesa no es una ruta fija sino una acción — por ejemplo, cualquier proceso que use `execve` para lanzar un programa, sin importar dónde esté — usas una regla de syscall con `-a` (acción y lista) y `-S` (la syscall):

```bash
# Registra cada ejecución de un programa en el sistema
sudo auditctl -a always,exit -S execve -k exec_log

# Registra cambios de propietario en cualquier archivo
sudo auditctl -a always,exit -S chown -S fchown -S lchown -k perm_mod
```

`always,exit` significa "genera siempre un registro al salir de la syscall" — es la combinación que vas a usar en el 90% de los casos; las otras combinaciones de acción/lista existen para casos más específicos de filtrado en el kernel.

## Etiquetar reglas con -k

El `-k` (`--key`) que aparece en todos los ejemplos anteriores no es opcional en la práctica: es una etiqueta de hasta 31 caracteres que te permite luego buscar "todos los eventos de esta regla" sin tener que recordar la ruta o la syscall exacta. Sin una key consistente, cada búsqueda en `ausearch` se vuelve mucho más manual.

## Reglas persistentes con augenrules

Las reglas que cargas con `auditctl` viven solo en memoria y desaparecen al reiniciar. Para que sobrevivan a un reinicio, se definen en ficheros `.rules` dentro de `/etc/audit/rules.d/`:

```bash
sudo tee /etc/audit/rules.d/custom.rules <<'EOF'
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k sudoers
-a always,exit -S execve -k exec_log
EOF

# Compila los .rules de rules.d/ en /etc/audit/audit.rules y las carga
sudo augenrules --load
```

`augenrules` combina todos los ficheros de `rules.d/` (puedes tener varios, por ejemplo uno por categoría) en un único `/etc/audit/audit.rules`, que es el que se aplica en cada arranque. Comprueba qué quedó activo con:

```bash
sudo auditctl -l
```

## Bloquear la configuración con -e 2

`auditctl -e` controla el estado del propio subsistema: `0` lo desactiva temporalmente, `1` lo deja activo (el estado normal). El valor `2` es distinto a los otros dos:

> [!CAUTION]
> `-e 2` bloquea la configuración de auditoría de forma inmutable: cualquier intento posterior de añadir, borrar o modificar reglas se audita y se rechaza, **y la única forma de volver a cambiarla es reiniciar la máquina**. Es una protección real contra un atacante con acceso root que intente desactivar la auditoría para cubrir su rastro, pero también te bloquea a ti si lo activas antes de terminar de ajustar tus reglas. Actívalo como último paso, no como el primero.

## Consultar eventos con ausearch

`ausearch` es la herramienta para leer `/var/log/audit/audit.log` sin parsearlo a mano. Los filtros más útiles:

```bash
# Todos los eventos con una key concreta
sudo ausearch -k identity

# Eventos de hoy
sudo ausearch -ts today

# Eventos de un usuario concreto (acepta UID o nombre)
sudo ausearch -ui antonio

# Combinando key y rango de tiempo
sudo ausearch -k exec_log -ts "1 hour ago"
```

## Informes resumidos con aureport

Cuando no buscas un evento concreto sino una visión general, `aureport` genera resúmenes en vez de listar cada línea:

```bash
# Resumen de intentos de autenticación
sudo aureport -au

# Qué archivos se han tocado
sudo aureport -f

# Qué ejecutables se han lanzado
sudo aureport -x

# Totales generales de todo lo registrado
sudo aureport --summary
```

Es el punto de partida habitual tras un incidente: primero `aureport --summary` para ver el volumen y dónde mirar, luego `ausearch` con la key o el rango de tiempo concretos que te haya señalado el resumen.

## auditd frente a journalctl

Si acabas de leer la guía de [`journalctl`](/blog/journalctl-domina-logs-systemd/), es razonable preguntarse por qué esto no es lo mismo. `journalctl` lee el journal de systemd: logs de servicios, del arranque y del kernel, pensados para depurar "por qué falló esto". `auditd` vive en un nivel distinto — engancha el propio kernel para registrar accesos y syscalls concretas que tú defines de antemano, pensado para responder "quién hizo esto y cuándo" con valor forense y de cumplimiento normativo. Un servidor bien configurado normalmente usa los dos: `journalctl` para operación del día a día, `auditd` para las rutas y acciones que de verdad importan si algo sale mal.

## Siguiente paso

Con `-w` para archivos concretos, `-a`/`-S` para syscalls, reglas persistentes en `rules.d/` y `ausearch`/`aureport` para consultarlas, ya tienes lo necesario para auditar lo que de verdad te preocupa en un servidor — sin generar tanto ruido que el log se vuelva inútil. Si además ejecutas [Lynis](/blog/auditoria-seguridad-lynis-linux/) periódicamente, comprobará que `auditd` sigue activo y con reglas cargadas, cerrando el círculo entre configurarlo una vez y verificar que sigue así con el tiempo.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
