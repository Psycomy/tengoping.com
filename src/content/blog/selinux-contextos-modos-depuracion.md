---
title: 'SELinux: contextos, modos y depuración'
description: 'SELinux explicado para sysadmins: contextos de tipo, modos enforcing/permissive, gestión de políticas y cómo depurar denegaciones con ausearch y sealert.'
author: 'antonio'
pubDate: 2026-09-18T13:00:00
category: 'Seguridad'
tags: ['SELinux', 'Seguridad', 'Hardening', 'Linux']
image: '../../assets/images/selinux-linux.jpg'
draft: false
---

SELinux (_Security-Enhanced Linux_) es el mecanismo de control de acceso obligatorio (MAC) que trae por defecto RHEL y toda su familia de derivados. A diferencia de los permisos tradicionales de Linux, que dependen de lo que decida el propietario de cada archivo, SELinux aplica una política centralizada que ni root puede saltarse sin cambiarla explícitamente — y es una de las causas más habituales de que un servicio "funcione en Ubuntu pero no en un RHEL recién instalado".

## Por qué SELinux no es "lo mismo" que AppArmor

Si vienes de administrar Ubuntu o Debian, ya conoces el otro gran mecanismo MAC de Linux: AppArmor. Los dos resuelven el mismo problema —una política del administrador que se aplica por encima de los permisos DAC tradicionales—, pero con una diferencia de fondo que determina todo lo demás: AppArmor confina por **ruta de archivo**, SELinux confina por **etiquetas** (contextos) aplicadas a cada objeto del sistema, sin importar dónde esté ese archivo en el árbol de directorios. Mover un archivo de sitio no cambia su contexto SELinux; sí puede cambiar qué perfil de AppArmor lo cubre.

SELinux nació en la NSA, que liberó el código bajo GPL el 22 de diciembre de 2000 como parche externo al kernel; se integró en el árbol principal de Linux el 8 de agosto de 2003, con el kernel 2.6.0-test3, tras un desarrollo conjunto con Red Hat y otros colaboradores. Por eso RHEL, Fedora, CentOS Stream, Rocky Linux y AlmaLinux lo traen activado por defecto — es, literalmente, parte de la identidad técnica de esa familia de distribuciones.

> [!NOTE]
> openSUSE y SUSE Linux Enterprise usaban AppArmor por defecto tradicionalmente, pero eso cambió en 2025: openSUSE Leap 16, Tumbleweed y SLES 16 ya traen SELinux de serie. Si administras alguna de esas distros en su versión actual, este artículo te aplica directamente a ti también.

## Contextos: el corazón de SELinux

Cada proceso, archivo, puerto y socket lleva una **etiqueta de seguridad** o contexto, con el formato `usuario:rol:tipo:nivel`. En la práctica, el campo que decide casi todo es el **tipo** (_type_): la política de **Type Enforcement** (TE) compara el tipo del proceso que pide acceso contra el tipo del recurso al que quiere acceder, y solo lo permite si existe una regla explícita que lo autorice. El resto son 0 hasta que hay una regla que dice lo contrario.

Comprueba el contexto de un proceso o archivo con `-Z`:

```bash
ps -eZ | grep nginx
# system_u:system_r:httpd_t:s0    1234 ?  00:00:02 nginx

ls -Z /var/www/html/index.html
# system_u:object_r:httpd_sys_content_t:s0 /var/www/html/index.html
```

Aquí `httpd_t` es el tipo del proceso de Nginx y `httpd_sys_content_t` el tipo esperado para contenido web servido por Apache/Nginx. Si ese mismo archivo tuviera el tipo `user_home_t` (el que llevan los archivos normales de un directorio personal), SELinux bloquearía el acceso aunque los permisos `chmod` fueran perfectos — es exactamente el escenario que provoca el clásico "403 Forbidden con permisos 644 correctos" en un servidor recién migrado.

## Modos: enforcing, permissive y disabled

SELinux tiene tres estados, y confundirlos genera buena parte de los tickets de "SELinux no me deja hacer nada":

- **Enforcing** — la política se aplica de verdad: lo que no está permitido, se bloquea y se registra.
- **Permissive** — todo se permite, pero cada violación que se habría bloqueado en Enforcing se registra igual. Es el modo de depuración por excelencia.
- **Disabled** — SELinux no carga ninguna política; el kernel ni siquiera evalúa contextos.

```bash
# Comprobar el estado actual
getenforce
# Enforcing

sestatus
```

> [!CAUTION]
> `setenforce 0`/`setenforce 1` cambian entre Enforcing y Permissive en caliente, pero **no puedes pasar a o desde Disabled sin reiniciar** — y ni siquiera con `setenforce` se puede llegar a Disabled: hace falta editar `SELINUX=disabled` en `/etc/selinux/config` y reiniciar. Desactivar SELinux por completo para "que funcione" es el equivalente a quitarle las pilas a la alarma porque suena demasiado: resuelve el síntoma y elimina la protección real. Si algo falla, cambia a `permissive` temporalmente, revisa qué se estaba bloqueando (siguiente sección) y corrige la política — no apagues el mecanismo entero.

Para hacer el cambio de modo persistente entre reinicios, edita el fichero de configuración:

```bash
# /etc/selinux/config
SELINUX=enforcing      # enforcing | permissive | disabled
SELINUXTYPE=targeted   # tipo de política, ver siguiente sección
```

## Políticas: por qué "targeted" es casi siempre la que ves

SELinux soporta varios tipos de política, seleccionables en `SELINUXTYPE`:

- **targeted** — la que trae por defecto toda la familia RHEL. Solo los procesos "objetivo" (daemons de red, servicios con superficie de ataque relevante: httpd, sshd, named, dhcpd...) corren en un dominio confinado; el resto de procesos de usuario corren en un dominio prácticamente sin restricciones adicionales.
- **mls** (_Multi-Level Security_) — pensada para entornos que necesitan certificación EAL4+/LSPP (gubernamental, defensa): añade un nivel de sensibilidad obligatorio (`s0`-`s15`) y categorías (`c0`-`c255`) a cada contexto, siguiendo el modelo Bell-LaPadula. Es sensiblemente más estricta y compleja de administrar; casi ningún homelab o servidor de empresa normal la necesita.
- **minimum** — una variante de `targeted` con aún menos procesos confinados, pensada como punto de partida mínimo.

Salvo que trabajes en un entorno con requisitos de certificación explícitos, vas a estar usando `targeted` — es lo que verás en `getenforce`/`sestatus` en cualquier RHEL, Fedora, Rocky o AlmaLinux recién instalado.

## Gestionar contextos de archivos: semanage, restorecon y chcon

Cuando mueves contenido web a una ruta no estándar, o instalas un servicio que escribe fuera de sus directorios habituales, el contexto que trae el archivo por defecto (heredado del directorio padre) casi nunca es el que la política espera. Hay tres herramientas, y confundir cuál usar es uno de los errores más habituales de quien empieza con SELinux:

```bash
# chcon: cambia el contexto YA, pero NO sobrevive a un restorecon
# ni a un relabel completo del sistema de archivos — solo para pruebas rápidas
sudo chcon -t httpd_sys_content_t /var/www/miapp/index.html

# semanage fcontext: define la REGLA persistente (qué contexto debería
# tener esa ruta), pero no toca ningún archivo todavía
sudo semanage fcontext -a -t httpd_sys_content_t "/var/www/miapp(/.*)?"

# restorecon: aplica esa regla, relabeling los archivos en disco
sudo restorecon -Rv /var/www/miapp
```

> [!IMPORTANT]
> `semanage fcontext` por sí solo **no cambia ningún archivo** — solo registra la regla en `/etc/selinux/targeted/contexts/files/file_contexts.local`. Si te saltas el `restorecon` final, los ficheros existentes se quedan con su contexto viejo y el problema sigue ahí; solo los archivos que se creen _después_ de la regla heredarán el contexto correcto automáticamente. El flujo siempre es "define con semanage, aplica con restorecon".

## Booleans: ajustar el comportamiento sin tocar la política

Muchas decisiones habituales (¿puede Nginx hacer conexiones salientes? ¿puede Samba compartir directorios personales?) ya están pensadas como interruptores en la propia política, sin necesidad de escribir reglas nuevas. Son los **booleans**:

```bash
# Listar todos los booleans y su estado actual
getsebool -a | grep httpd

# Permitir que httpd/nginx abra conexiones salientes (proxy inverso, API externa...)
sudo setsebool -P httpd_can_network_connect on
```

El flag `-P` (_persistent_) es importante: sin él, el cambio se pierde en el siguiente reinicio, igual que pasaba con `setenforce`. Antes de escribir una regla de política a mano, comprueba siempre si lo que necesitas ya existe como boolean — `getsebool -a | grep <palabra_clave>` suele ahorrar mucho trabajo.

## Depurar una denegación: de audit.log a la política aplicada

Cuando SELinux bloquea algo, no fallas a ciegas: cada denegación (AVC, _Access Vector Cache_) queda registrada en `/var/log/audit/audit.log`, con el mismo subsistema de auditoría del kernel que cubrimos en el artículo de [auditd](/blog/auditd-auditoria-eventos-sistema-linux/). El flujo de depuración habitual tiene una rama de decisión clara según qué tipo de denegación sea:

```
Un servicio falla de forma rara (permission denied sin motivo aparente)
   │
   ▼
1. ausearch -m avc -ts recent
   │  (busca denegaciones AVC recientes en el log de auditoría)
   ▼
2. sealert -a /var/log/audit/audit.log
   │  (traduce la denegación cruda a una explicación humana + sugerencia)
   ▼
3. ¿Qué tipo de problema sugiere sealert?
   │
   ├── Falta un boolean → setsebool -P <boolean> on
   ├── Contexto de archivo incorrecto → semanage fcontext + restorecon
   └── Falta una regla de política real → audit2allow (con cautela, ver aviso)
   │
   ▼
4. ausearch -m avc -ts recent de nuevo → confirma que ya no aparecen denegaciones
```

```bash
sudo ausearch -m avc -ts recent
sudo sealert -a /var/log/audit/audit.log
```

> [!WARNING]
> `audit2allow` genera automáticamente una regla de política a partir de lo que encuentra en el log de denegaciones — pero una denegación no siempre es un falso positivo de una app legítima: también puede ser exactamente SELinux haciendo su trabajo y bloqueando un intento de explotación real. La propia documentación de Red Hat recomienda no usar `audit2allow` como primera opción: revisa primero la sugerencia de `sealert`, y solo si confirmas que el acceso es legítimo, genera el módulo con algo como `audit2allow -a -M nombremodulo` y revisa el `.te` resultante _antes_ de cargarlo con `semodule -i nombremodulo.pp`. Generar y cargar módulos de política a ciegas a partir de tráfico que no entiendes es la forma más rápida de convertir SELinux en una alarma que autoriza lo que sea con tal de dejar de sonar.

## SELinux y contenedores: sVirt, Podman/Docker y las etiquetas :z / :Z

Si ya usas [Docker](/blog/docker-guia-practica-contenedores-linux/) o [Podman](/blog/introduccion-contenedores-podman-linux/) sobre una distro con SELinux, probablemente ya te has encontrado con un `Permission denied` al montar un volumen aunque los permisos Unix sean correctos. El motivo: cada proceso de contenedor corre con el tipo `container_t`, y los archivos del host suelen tener tipos como `user_home_t` o `var_t` — tipos que la política no deja leer ni escribir a `container_t` por defecto, precisamente para que un contenedor comprometido no pueda salirse a leer el resto del sistema de archivos del host.

La solución no es desactivar SELinux ni el contenedor, sino relabeling explícito del volumen al montarlo:

```bash
# :z (minúscula) — etiqueta compartida (container_file_t): varios
# contenedores pueden montar el mismo volumen con este flag
docker run -v /datos/app:/data:z mi-imagen

# :Z (mayúscula) — etiqueta privada para ESTE contenedor en concreto;
# otro contenedor no podrá acceder al mismo volumen aunque lo monte
docker run -v /datos/app:/data:Z mi-imagen
```

Este mismo mecanismo, aplicado a máquinas virtuales en vez de contenedores, se llama **sVirt** y es lo que usa libvirt/KVM (cubierto en el artículo de [KVM y libvirt](/blog/kvm-libvirt-virtualizacion-nativa-linux/)) para aislar los procesos `qemu-kvm` de cada VM entre sí con su propio contexto — el mismo principio de Type Enforcement, aplicado a un problema distinto.

## Siguiente paso

SELinux se hace manejable en cuanto interiorizas el flujo: nunca desactivarlo para "que funcione", siempre `ausearch`/`sealert` antes de tocar nada, y booleans antes que reglas de política nuevas. Si administras varios servidores RHEL o Rocky, el siguiente paso natural es meter esa comprobación en tu rutina de auditoría periódica — tanto [Lynis](/blog/auditoria-seguridad-lynis-linux/) como el propio `sealert` pueden ejecutarse desde un timer de systemd para avisarte de denegaciones nuevas sin tener que ir a buscarlas a mano.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
