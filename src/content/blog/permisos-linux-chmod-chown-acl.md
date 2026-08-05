---
title: 'Permisos en Linux: chmod, chown y ACLs explicados'
description: 'Permisos en Linux en profundidad: cómo se resuelven owner/group/others, umask, la trampa de chmod -R, ACLs con mask y chattr.'
author: 'antonio'
pubDate: 2026-01-18
updatedDate: 2026-08-05
category: 'Linux'
tags: ['Permisos', 'Linux', 'Seguridad', 'ACL']
image: '../../assets/images/linux-permissions.jpg'
draft: false
---

Los permisos son la primera línea de defensa de cualquier sistema Linux: deciden quién puede leer, modificar o ejecutar cada archivo, y un descuido aquí es una de las causas más comunes tanto de brechas de seguridad como de esos "Permission denied" que te hacen perder media hora depurando un servicio. Este artículo repasa `chmod` y `chown` para el día a día, cómo el kernel resuelve realmente esos permisos, y las ACLs y atributos extendidos para cuando el modelo clásico de propietario/grupo/otros se queda corto.

## Permisos básicos en Linux

Cada archivo tiene tres niveles de permisos: propietario (u), grupo (g) y otros (o), con tres acciones: lectura (r), escritura (w) y ejecución (x).

```bash
ls -la /etc/passwd
# -rw-r--r-- 1 root root 2847 ene 15 10:30 /etc/passwd
```

Esa cadena de diez caracteres se lee en bloques: el primero indica el tipo (`-` archivo normal, `d` directorio, `l` enlace simbólico), y los tres siguientes bloques de tres son owner, group y others respectivamente.

### r, w, x no significan lo mismo en un directorio que en un archivo

Es la confusión más habitual al empezar con permisos: en un directorio, `x` no significa "ejecutar" en el sentido de un binario, sino **poder entrar y acceder a lo que hay dentro** (por ejemplo con `cd` o para que un proceso abra un archivo por su ruta completa).

| Permiso | En un archivo                   | En un directorio                           |
| ------- | ------------------------------- | ------------------------------------------ |
| `r`     | Leer su contenido               | Listar los nombres de sus entradas (`ls`)  |
| `w`     | Modificar su contenido          | Crear, borrar o renombrar entradas dentro  |
| `x`     | Ejecutarlo como programa/script | Atravesarlo para acceder a lo que contiene |

Por eso un directorio con `r-x` permite listar y entrar, pero no crear ni borrar nada dentro; y uno con `--x` (sin `r`) permite acceder a un archivo si conoces su nombre exacto, pero no listar qué contiene.

### El orden en que el kernel resuelve los permisos

> [!IMPORTANT]
> El kernel evalúa owner, group y others **en ese orden, y se detiene en el primer nivel que coincida con tu identidad** — no sigue probando los siguientes aunque serían más permisivos. Si eres el propietario de un archivo con permisos `---rwxrwx` (0077), se te deniega el acceso: el kernel comprueba que eres el owner, aplica los permisos de owner (vacíos) y para ahí, sin mirar los de group aunque te darían acceso completo.

```
Proceso pide acceso a un archivo
   │
   ▼
1. ¿El UID del proceso coincide con el owner del archivo?
   │
   ├── sí → se aplican los bits de owner, fin de la comprobación
   │
   └── no → 2. ¿Alguno de los GID del proceso coincide con el group del archivo?
              │
              ├── sí → se aplican los bits de group, fin de la comprobación
              │
              └── no → se aplican los bits de others
```

## chmod: cambiar permisos

### Notación octal

```bash
chmod 755 script.sh    # rwxr-xr-x
chmod 644 config.yml   # rw-r--r--
chmod 600 id_rsa       # rw-------
```

### Notación simbólica

```bash
chmod u+x script.sh
chmod g-w archivo.txt
chmod o= archivo.txt
chmod u+rwx,g+rx,o+r archivo.txt   # combinar varios "quién" en una sola llamada
```

### El flag -R y la trampa de la X mayúscula

Aplicar permisos recursivamente con minúscula es una de las formas más rápidas de romper un árbol de directorios:

```bash
chmod -R 755 /opt/app   # ¡convierte TODOS los archivos en ejecutables, no solo los directorios!
```

Esto deja binarios, imágenes de configuración y archivos de texto marcados como ejecutables, lo cual no solo es innecesario sino que puede activar avisos en auditorías de seguridad como las que hace [Lynis](/blog/auditoria-seguridad-lynis-linux/). La `X` mayúscula resuelve esto: solo añade el bit de ejecución a directorios, o a archivos que **ya** tuvieran al menos un bit `x` activado para alguien:

```bash
chmod -R u+rwX,g+rX,o+rX /opt/app   # directorios y ejecutables existentes ganan x; el resto de archivos no
```

## chown y chgrp: cambiar propietario y grupo

```bash
sudo chown usuario:grupo archivo.txt
sudo chown -R www-data:www-data /var/www
sudo chgrp developers proyecto/          # cambiar solo el grupo
sudo chown --reference=modelo.txt destino.txt   # copiar owner:group de otro archivo
```

## umask: qué permisos reciben los archivos nuevos

`chmod` cambia permisos de algo que ya existe; `umask` decide con qué permisos **nace** cada archivo o directorio nuevo. Es una máscara que se resta de los permisos máximos por defecto: 666 (`rw-rw-rw-`) para archivos y 777 (`rwxrwxrwx`) para directorios — los archivos nunca nacen ejecutables por defecto, aunque el umask lo permitiera.

```bash
umask        # ver el valor actual, típicamente 022 en Ubuntu/Debian
umask 027    # aplicar uno más restrictivo para la sesión actual
```

Con el valor por defecto `022`:

```
Archivo nuevo:     666 - 022 = 644  (rw-r--r--)
Directorio nuevo:  777 - 022 = 755  (rwxr-xr-x)
```

Un `umask 027` es habitual en servidores donde no quieres que "otros" pueda leer nada de lo que crees: deja los archivos en `640` y los directorios en `750`. Para que el cambio sea permanente, se define en `/etc/profile`, `~/.bashrc` o el servicio concreto (por ejemplo, `UMask=` en la sección `[Service]` de una unidad systemd), no solo en la sesión de shell actual.

## Permisos especiales

Los permisos SUID/SGID excesivos son precisamente uno de los puntos que revisa Lynis al auditar un servidor.

| Permiso | Octal | Uso                                                                                                        |
| ------- | ----- | ---------------------------------------------------------------------------------------------------------- |
| SUID    | 4000  | El archivo se ejecuta con los privilegios de su propietario, no de quien lo lanza                          |
| SGID    | 2000  | En un ejecutable, corre con el grupo del archivo; en un directorio, los archivos nuevos heredan su grupo   |
| Sticky  | 1000  | En un directorio con permisos de escritura para todos, cada usuario solo puede borrar sus propios archivos |

El ejemplo clásico de SUID es `/usr/bin/passwd`: cualquier usuario necesita escribir en `/etc/shadow` (solo escribible por root) para cambiar su contraseña, y el bit SUID le presta temporalmente los privilegios del propietario del binario (root) mientras se ejecuta:

```bash
ls -l /usr/bin/passwd
# -rwsr-xr-x 1 root root ... /usr/bin/passwd   # la 's' en vez de 'x' indica SUID activo
chmod u+s script     # activar SUID
chmod g+s directorio # activar SGID
chmod +t directorio  # activar sticky bit (el caso típico es /tmp)
```

> [!CAUTION]
> Un binario con SUID root y una vulnerabilidad de escritura de archivos arbitraria es una vía directa a escalada de privilegios. Localiza los que existen en tu sistema con `find / -perm -4000 -type f 2>/dev/null` y confirma que cada uno es realmente necesario.

## ACLs para control avanzado

Cuando los permisos básicos no son suficientes —por ejemplo, dar acceso a un usuario o grupo concreto sin cambiar el owner ni el group principal del archivo—, las ACL (Access Control Lists) añaden entradas adicionales:

```bash
sudo setfacl -m u:deploy:rx /opt/app
sudo setfacl -m g:developers:rwx /opt/app/src
getfacl /opt/app
```

```
# file: opt/app
# owner: root
# group: root
user::rwx
user:deploy:r-x
group::r-x
mask::rwx
other::r-x
```

La línea `mask::` es la que más confusión genera: define el **límite superior efectivo** para todas las entradas de usuario y grupo con nombre (no afecta a `user::` del propietario ni a `other::`). El permiso real de una entrada es el AND bit a bit entre lo que pide esa entrada y lo que permite la máscara — si `user:deploy` tiene `rwx` pero la máscara es `r-x`, el permiso efectivo de `deploy` es `r-x`, y `getfacl` lo marca añadiendo `#effective:` junto a la entrada recortada. `setfacl` recalcula la máscara automáticamente al añadir entradas, salvo que uses `-n` para desactivarlo.

```bash
sudo setfacl -x u:deploy /opt/app   # quitar una entrada concreta
sudo setfacl -b /opt/app            # eliminar todas las ACLs y volver a los permisos clásicos
```

### ACLs por defecto en directorios

Sin una ACL por defecto, los archivos que se crean dentro de un directorio con ACL no heredan esas entradas automáticamente. `-d` fija una ACL por defecto que sí se propaga a todo lo que se cree después:

```bash
sudo setfacl -d -m g:developers:rwx /opt/app/src
```

## Atributos extendidos con chattr

Por debajo de los permisos y las ACL, algunos sistemas de archivos (ext4, XFS, Btrfs) soportan atributos adicionales que ni siquiera dependen del propietario:

```bash
sudo chattr +i /etc/resolv.conf   # inmutable: nadie, ni root, puede modificarlo o borrarlo
lsattr /etc/resolv.conf
sudo chattr -i /etc/resolv.conf   # quitar la inmutabilidad para volver a poder editarlo
```

> [!WARNING]
> `chattr +i` bloquea también a `root`: ni `rm`, ni sobrescribir el archivo, ni crear un enlace hacia él funcionan hasta que ejecutes `chattr -i` primero. Es útil para archivos de configuración críticos que alguna automatización podría pisar por error (`/etc/resolv.conf` gestionado a mano en vez de por un DNS local, por ejemplo), pero documenta dónde lo has usado — un `chattr +i` olvidado parece un permiso corrupto cuando falla algo tres meses después.

Otro atributo útil es `+a` (append-only): permite añadir datos al final del archivo pero no modificar ni borrar lo ya escrito, un patrón habitual para archivos de log que no deberían poder alterarse retroactivamente.

## Auditar permisos con find

`find` es la herramienta más rápida para detectar configuraciones de riesgo en un árbol de directorios completo:

```bash
find / -perm -4000 -type f 2>/dev/null      # binarios con SUID activo
find /var/www -perm -o+w -type f 2>/dev/null  # archivos escribibles por "otros" (world-writable)
find /opt/app -not -user appuser              # archivos que no pertenecen al usuario esperado
```

## Errores comunes

> [!WARNING]
> `chmod 777` no es una solución, es la ausencia de una: da lectura, escritura y ejecución a cualquier usuario del sistema. Si el objetivo real es "que un grupo concreto pueda escribir aquí", la respuesta casi siempre es `chown :grupo`, `chmod 775` y, si hace falta más granularidad todavía, una ACL — no abrir el archivo a todo el mundo.

## Conclusión

Comprender los permisos en Linux —incluyendo cómo se resuelven realmente owner/group/others, qué hereda cada archivo nuevo según el `umask` y cuándo recurrir a ACLs o `chattr`— es una de las bases de cualquier [hardening básico de un servidor](/blog/hardening-basico-servidores-linux/). El modelo clásico cubre la mayoría de los casos; las ACLs y los atributos extendidos están ahí para cuando necesitas algo más fino sin reestructurar toda la jerarquía de grupos.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
