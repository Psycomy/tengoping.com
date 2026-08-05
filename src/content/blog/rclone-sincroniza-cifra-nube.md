---
title: 'rclone: sincroniza y cifra tus datos en la nube'
description: 'Guía práctica de rclone: instala, configura remotos, sincroniza con cifrado y automatiza copias hacia almacenamiento en la nube desde Linux.'
author: 'antonio'
pubDate: 2026-08-05
category: 'Automatización'
tags: ['Backup', 'rclone', 'Storage', 'Sysadmin']
image: '../../assets/images/auto-rclone.jpg'
draft: false
---

`rclone` es una herramienta de línea de comandos que gestiona archivos en más de 70 proveedores de almacenamiento en la nube (S3, Google Drive, Backblaze B2, OneDrive, Azure, servidores SFTP/WebDAV propios, etc.) con una sintaxis casi idéntica a `rsync`. Es la pieza que falta si ya usas `rsync` para copias locales pero necesitas mandar esos backups fuera de tu red, cifrados, sin depender de un cliente gráfico ni de un servicio de terceros con su propia app.

## Instalación

El propio proyecto desaconseja instalar `rclone` desde los repositorios de la distribución, porque suelen llevar versiones desactualizadas frente al ritmo de publicación del proyecto. El método recomendado es el script oficial:

```bash
sudo -v ; curl https://rclone.org/install.sh | sudo bash
```

El script comprueba la versión ya instalada y no vuelve a descargar si no hace falta, así que es seguro volver a ejecutarlo para actualizar. Comprueba la instalación:

```bash
rclone version
```

## Configurar un remote

Un "remote" en `rclone` es una conexión nombrada a un backend concreto (un bucket S3, una cuenta de Google Drive, un servidor SFTP...). Se define con el asistente interactivo:

```bash
rclone config
```

El asistente pregunta el tipo de backend, las credenciales y, según el proveedor, abre el navegador para completar un flujo OAuth (Google Drive, Dropbox, OneDrive) o pide directamente claves de API (S3, B2). El resultado se guarda en `~/.config/rclone/rclone.conf`.

> [!IMPORTANT]
> Si vas a guardar una contraseña o token a mano en `rclone.conf` en lugar de usar el asistente, ofúscala primero con `rclone obscure 'tu-contraseña'`. No es cifrado fuerte —evita que quede en texto plano a simple vista en el fichero— pero `rclone` espera ese formato y falla si pegas la contraseña sin procesar.

> [!TIP]
> La ofuscación no sustituye a los permisos del fichero: la propia documentación de rclone advierte que es reversible por diseño, pensada solo para evitar que la contraseña salte a la vista al mirar el fichero por encima, no como cifrado seguro. Restringe el acceso con `chmod 600 ~/.config/rclone/rclone.conf` justo después de configurar el primer remote.

Para listar los remotes ya configurados:

```bash
rclone listremotes
```

## Copiar, sincronizar y verificar: no son lo mismo

`rclone` distingue tres operaciones que se confunden fácilmente y que no son intercambiables:

- **`rclone copy origen destino`** — copia los archivos nuevos o modificados de origen a destino. Nunca borra nada en destino.
- **`rclone sync origen destino`** — deja destino idéntico a origen, incluyendo **borrar en destino** cualquier archivo que ya no exista en origen.
- **`rclone check origen destino`** — compara ambos lados y reporta diferencias, sin transferir ni borrar nada.

```bash
# Copia segura: nunca borra en el remoto
rclone copy /home/usuario/documentos remoto-s3:backups/documentos --progress

# Sincronización: el remoto queda igual que el origen
rclone sync /home/usuario/documentos remoto-s3:backups/documentos --progress
```

> [!CAUTION]
> `rclone sync` puede borrar datos en el destino si el origen tiene menos archivos de los esperados (por ejemplo, si un disco no está montado y el directorio origen aparece vacío). La propia documentación de rclone es explícita en esto: prueba siempre primero con `--dry-run`, que simula la operación y lista qué haría sin tocar nada:
>
> ```bash
> rclone sync /home/usuario/documentos remoto-s3:backups/documentos --dry-run -v
> ```

## Filtros y control de ancho de banda

Para excluir rutas o tipos de archivo, `rclone` usa patrones similares a `.gitignore`:

```bash
rclone sync /var/www remoto-s3:backups/www \
  --exclude '*.log' \
  --exclude 'cache/**' \
  --progress
```

En una conexión compartida con otros servicios, limita el ancho de banda para no saturar la subida (por ejemplo, 5 MB/s de subida sin límite de bajada):

```bash
rclone sync /var/www remoto-s3:backups/www --bwlimit 5M:off
```

También puedes ajustar el paralelismo: `--transfers` controla cuántos archivos se transfieren a la vez (por defecto 4) y `--checkers` cuántas comprobaciones de igualdad corren en paralelo (por defecto 8). Subir muchos archivos pequeños se beneficia de subir ambos valores; con pocos archivos grandes no aporta gran cosa.

## Cifrar los datos antes de subirlos: remote crypt

Si el proveedor de nube no es de tu confianza total —o simplemente no quieres que un proveedor externo pueda leer tus archivos—, `rclone` permite envolver cualquier remote existente en una capa de cifrado con el backend `crypt`. Se crea como un remote más, encadenado sobre el remote real:

```bash
rclone config
# n) New remote
# name> secreto
# Storage> crypt
# remote> remoto-s3:backups/cifrado   ← el remote/ruta real que envuelve
# filename_encryption> standard        ← cifra también los nombres de archivo
# password> (contraseña, se ofusca automáticamente en el asistente)
```

A partir de ahí trabajas contra `secreto:` como si fuera una carpeta normal, y `rclone` cifra al subir y descifra al bajar de forma transparente:

```bash
rclone copy /home/usuario/documentos secreto:documentos --progress
```

En el remote real (`remoto-s3:backups/cifrado`), los nombres de archivo y su contenido quedan cifrados; nadie con acceso al bucket puede leer ni siquiera la estructura de carpetas sin la contraseña.

`filename_encryption` acepta tres valores con compromisos distintos: `standard` (el usado arriba) cifra los nombres por completo pero los limita a unos 143 caracteres, un problema solo si ya tienes rutas muy largas; `obfuscate` aplica una simple rotación reversible del nombre y no debe considerarse cifrado real, aunque permite nombres más largos; `off` deja los nombres en claro y solo cifra el contenido, útil si necesitas que el propio proveedor pueda indexar o listar archivos por nombre. Para backups, `standard` es la opción razonable por defecto. Ten en cuenta también que el cifrado añade una cabecera fija de 32 bytes por archivo más una pequeña sobrecarga por bloque de 64 KiB: en archivos grandes es insignificante (en torno al 0,03%), pero en carpetas con miles de archivos diminutos el espacio extra se nota.

> [!WARNING]
> Guarda la contraseña del remote `crypt` en un gestor de contraseñas o similar, fuera del propio servidor. Si pierdes esa contraseña, los datos cifrados en el remoto son irrecuperables: no hay puerta trasera ni recuperación por parte de rclone ni del proveedor de nube.

## Verificar la integridad de las copias

Copiar sin errores no garantiza que los datos lleguen intactos: una conexión inestable puede truncar un archivo sin que la transferencia falle visiblemente. `rclone check` compara tamaños y hashes (MD5 o SHA1, según lo que soporte el backend) entre origen y destino sin modificar ninguno de los dos lados, y reporta cualquier archivo que no coincida:

```bash
rclone check /var/www secreto:www
```

Para remotes que no exponen hashes propios, o cuando quieres una verificación exhaustiva byte a byte, añade `--download`: descarga los datos de ambos lados y los compara sobre la marcha, a costa de mucho más tráfico. En el otro extremo, `--size-only` compara solo tamaños y es más rápido pero no detecta corrupción con el mismo tamaño de archivo.

```bash
# Verificación exhaustiva (más lenta, más tráfico)
rclone check /var/www secreto:www --download

# Verificación rápida, solo tamaños
rclone check /var/www secreto:www --size-only
```

## Reducir llamadas a la API y evitar el rate limiting

Backends como Google Drive limitan el número de peticiones por minuto; superar ese límite devuelve errores `429` (demasiadas peticiones). Dos flags ayudan a mantenerte dentro de la cuota:

- `--fast-list` — lista los directorios de forma recursiva en menos peticiones, a cambio de más memoria. Reduce directamente el número de llamadas a la API en listados grandes.
- `--tpslimit N` — limita las transacciones por segundo que `rclone` envía al backend, independientemente de `--transfers` y `--checkers`.

```bash
rclone sync /var/www secreto:www --fast-list --tpslimit 10
```

Si ves errores `429` de forma repetida contra Google Drive u otro backend con cuota agresiva, baja `--tpslimit` antes de tocar cualquier otro parámetro: es la causa más común y la más fácil de descartar primero.

## Montar almacenamiento en la nube como sistema de archivos

`rclone mount` usa FUSE para presentar un remote como un directorio local navegable con cualquier programa, en lugar de tener que usar siempre la CLI:

```bash
mkdir -p /mnt/nube
rclone mount remoto-s3:backups /mnt/nube --vfs-cache-mode writes --daemon
```

El flag `--vfs-cache-mode` controla cómo se gestiona la caché local:

- `off` (por defecto): lee y escribe directo contra el remoto, sin caché local. No permite abrir un archivo simultáneamente para lectura y escritura.
- `writes`: los archivos de solo lectura se sirven directo del remoto; los que se escriben se cachean primero en disco local. Cubre la mayoría de casos de uso normales.
- `full`: cachea en disco tanto lecturas como escrituras, con descarga bajo demanda de solo las partes accedidas. Es el modo más compatible, útil para reproducir vídeo o abrir archivos grandes por partes.

> [!NOTE]
> No ejecutes dos instancias de `rclone` usando la misma caché VFS sobre remotes que se solapan: la documentación oficial advierte que puede corromper los datos cacheados.

## Automatizar con systemd timer

Para que las copias corran solas, combina `rclone` con un `systemd timer` en vez de una tarea cron clásica —tal como se explica en [cron vs systemd timers](/blog/tareas-programadas-cron-systemd-timers/), un timer registra en el log si el servicio falló, cosa que cron no hace por defecto.

```ini
# /etc/systemd/system/rclone-backup.service
[Unit]
Description=Backup cifrado a la nube con rclone

[Service]
Type=oneshot
ExecStart=/usr/bin/rclone sync /var/www secreto:www --exclude '*.log'
```

```ini
# /etc/systemd/system/rclone-backup.timer
[Unit]
Description=Ejecuta rclone-backup.service cada noche

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now rclone-backup.timer
```

El flujo completo, de origen local a la nube cifrada, queda así:

```
/var/www (origen local)
   │
   ▼
1. systemd timer (OnCalendar=daily) dispara rclone-backup.service
   │
   ▼
2. rclone sync /var/www secreto:www --exclude '*.log'
   │
   ▼
3. Remote crypt cifra contenido y nombres de archivo en local
   │
   ▼
4. Subida al remote real (remoto-s3:backups/cifrado)
   │
   ├── transferencia correcta   → destino queda sincronizado
   └── error de red/credenciales → journalctl -u rclone-backup registra el fallo
```

## rclone frente a rsync

Si ya usas [backups incrementales con rsync](/blog/backup-incremental-rsync-servidores-linux/) entre tus propios servidores, la pregunta natural es cuándo cambiar a `rclone`. La diferencia no es de rendimiento sino de destino: `rsync` habla el protocolo rsync (o SSH) contra otro host Linux con `rsync` instalado; `rclone` habla las APIs nativas de más de 70 proveedores de nube, así que es la herramienta correcta cuando el destino es un bucket S3, Google Drive, Backblaze B2 o similar, no otro servidor bajo tu control. Ambas herramientas son complementarias: `rsync` para réplicas rápidas entre tus propias máquinas, `rclone` para sacar una copia fuera de tu infraestructura.

## Siguiente paso

Con el remote configurado, el cifrado en marcha y el timer corriendo cada noche, el único hueco que queda es verificar la restauración: un backup que nunca se ha restaurado no es un backup verificado. Programa un `rclone check` periódico contra el remote y, de vez en cuando, restaura manualmente un archivo de prueba con `rclone copy secreto:www/index.html /tmp/prueba/` para confirmar que el ciclo completo funciona de extremo a extremo.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
