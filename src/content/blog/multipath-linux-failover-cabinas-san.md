---
title: 'Multipath en Linux: failover y HA con cabinas SAN'
description: 'Configura DM-Multipath en Linux para eliminar puntos únicos de fallo hacia la cabina SAN: instalación, multipath.conf y failover.'
author: 'antonio'
pubDate: 2026-08-01T14:00:00
category: 'Hardware'
tags: ['Multipath', 'SAN', 'Storage', 'Sysadmin']
image: '../../assets/images/multipath-san.jpg'
draft: false
---

Cuando un servidor se conecta a una cabina de almacenamiento por Fibre Channel o iSCSI, cada cable, HBA, switch y puerto de la controladora es un punto potencial de fallo. DM-Multipath agrupa varias rutas físicas hacia el mismo volumen en un único dispositivo lógico, de forma que si una ruta cae el sistema sigue sirviendo I/O por las que quedan, sin que la aplicación se entere. Es la pieza que convierte una SAN redundante en alta disponibilidad real a nivel de sistema operativo.

Si ya conoces [RAID por software con mdadm](/blog/raid-software-mdadm-guia-practica/), la idea es similar pero en otra capa: mdadm protege contra el fallo de un disco, multipath protege contra el fallo del _camino_ hacia un disco (o LUN) que, en sí mismo, ya suele estar protegido por RAID dentro de la cabina.

## Qué problema resuelve multipath

Una cabina SAN empresarial expone sus volúmenes (LUNs) a través de varias controladoras, y cada servidor suele tener dos o más HBA o interfaces de red conectadas a switches independientes. Sin multipath, el kernel ve cada ruta física como un dispositivo de bloques distinto: si un servidor tiene dos HBA conectadas a la misma LUN por dos switches distintos, Linux presenta `/dev/sda` y `/dev/sdb` como si fueran dos discos diferentes, cuando en realidad son la misma LUN vista dos veces.

DM-Multipath (Device Mapper Multipath) resuelve esto en dos frentes:

- **Redundancia (failover):** si una ruta falla —se desconecta un cable, se reinicia un switch, falla una controladora de la cabina—, el tráfico se redirige automáticamente a una ruta que siga activa, sin interrumpir el I/O de las aplicaciones.
- **Rendimiento (balanceo de carga):** en configuraciones activo-activo, el I/O se puede repartir entre varias rutas simultáneamente en lugar de dejar unas paradas como simple respaldo.

Todo esto se apoya en el subsistema **device-mapper** del kernel, el mismo que usa LVM para presentar volúmenes lógicos, y se administra con el paquete `multipath-tools` (Debian/Ubuntu) o `device-mapper-multipath` (RHEL/SUSE), junto con el demonio `multipathd`.

## WWID: cómo identifica multipath la misma LUN

Cada LUN expuesta por la cabina tiene un **WWID** (World Wide Identifier), un identificador único y persistente entre reinicios que no cambia aunque cambie el nombre del dispositivo (`/dev/sdX`) o el orden en que el kernel lo detecta. Multipath usa el WWID para reconocer que `/dev/sda`, `/dev/sdb`, `/dev/sdc` y `/dev/sdd` son en realidad la misma LUN vista por cuatro rutas distintas, y las agrupa bajo un único dispositivo lógico, típicamente en `/dev/mapper/`.

```
Servidor                                        Cabina SAN
  ├── HBA1 → Switch FC A → Controladora A   →   /dev/sda
  ├── HBA1 → Switch FC A → Controladora B   →   /dev/sdb
  ├── HBA2 → Switch FC B → Controladora A   →   /dev/sdc
  └── HBA2 → Switch FC B → Controladora B   →   /dev/sdd

multipath agrupa las 4 rutas por su WWID común
                     │
                     ▼
        /dev/mapper/datos-oracle
```

```bash
# Consultar el WWID que multipath asignaría a un dispositivo
scsi_id --whitelisted --device=/dev/sda
```

> [!NOTE]
> El comando `scsi_id` necesita que el dispositivo soporte las páginas VPD (Vital Product Data) de SCSI. Casi todas las cabinas empresariales las soportan; algunos discos locales o USB baratos no, por eso conviene excluirlos explícitamente de multipath (sección `blacklist` más abajo) para evitar mapeos erróneos.

## Instalación

En Debian/Ubuntu:

```bash
sudo apt install multipath-tools multipath-tools-boot
# Para iSCSI necesitarás además el iniciador:
sudo apt install open-iscsi
```

En RHEL/derivados:

```bash
sudo dnf install device-mapper-multipath
sudo mpathconf --enable --with_multipathd y
```

`mpathconf` genera un `/etc/multipath.conf` inicial razonable y habilita el servicio; en Debian/Ubuntu se parte de un archivo vacío o mínimo y se edita a mano.

```bash
sudo systemctl enable --now multipathd
systemctl status multipathd
```

## La estructura de /etc/multipath.conf

El archivo se organiza en secciones. No hace falta rellenarlas todas: para empezar, con `defaults` y `blacklist` suele bastar.

```conf
defaults {
    user_friendly_names yes
    find_multipaths yes
    path_grouping_policy failover
    path_checker tur
    failback immediate
    no_path_retry 5
}

blacklist {
    # Excluye discos locales que no son LUNs de la SAN
    devnode "^sd[a]$"
}

multipaths {
    multipath {
        wwid 3600d0230000000000e13954ed5f89300
        alias datos-oracle
    }
}
```

- **`defaults`**: valores globales aplicados a todos los mapas salvo que se sobrescriban en `devices` o `multipaths`.
- **`blacklist`**: dispositivos que multipath debe ignorar por completo (discos locales, USB, LUNs de arranque en algunos escenarios).
- **`multipaths`**: configuración por WWID concreto, típicamente para fijar un alias legible en vez del WWID crudo.
- **`devices`** (no mostrada arriba): ajustes específicos por modelo de cabina (fabricante/producto), útiles cuando el hardware necesita un `path_checker` o `hardware_handler` distinto al genérico.

### Parámetros que más importan

**`path_grouping_policy`** decide cómo se agrupan las rutas en grupos de prioridad:

| Valor                | Comportamiento                                                                      |
| -------------------- | ----------------------------------------------------------------------------------- |
| `failover`           | Un único path activo por grupo de prioridad; el resto queda en espera (por defecto) |
| `multibus`           | Todas las rutas válidas en un mismo grupo, balanceo activo-activo                   |
| `group_by_prio`      | Un grupo por cada valor de prioridad detectado                                      |
| `group_by_serial`    | Un grupo por número de serie detectado                                              |
| `group_by_node_name` | Un grupo por nombre de nodo destino                                                 |

**`no_path_retry`** define qué hacer cuando se caen _todas_ las rutas a la vez:

- `fail` — falla el I/O de inmediato, sin encolar.
- `queue` — encola el I/O indefinidamente hasta que vuelva alguna ruta.
- un número (p. ej. `5`) — reintenta ese número de ciclos de polling antes de fallar el I/O.

> [!WARNING]
> `no_path_retry queue` deja el I/O bloqueado indefinidamente si la SAN entera queda inaccesible, lo que puede colgar procesos o incluso el sistema completo hasta que las rutas vuelvan. Es una opción legítima cuando prefieres que la aplicación espere antes que ver errores de escritura, pero úsala con conocimiento: en la mayoría de despliegues es más seguro un valor numérico que acote la espera.

**`failback`** controla qué pasa cuando una ruta caída vuelve a estar disponible:

- `immediate` — vuelve a usarla en cuanto se detecta activa.
- `manual` — no hace failback automático; hay que forzarlo a mano.
- `followover` — solo hace failback automático si la primera ruta del grupo original vuelve activa (evita "flapping" cuando solo se recupera una ruta secundaria).
- un número — retrasa el failback ese número de segundos, útil para evitar oscilaciones si una ruta es inestable.

**`find_multipaths`** controla si multipath intenta crear mapas sobre cualquier dispositivo con más de una ruta detectada o solo sobre los ya conocidos. El valor por defecto interno de la herramienta es `off`, pero tanto `mpathconf` en RHEL como buena parte de las guías de referencia generan configuraciones con `find_multipaths yes` (o `on`), que simplifica la administración: solo hay que poner en la lista negra lo que _no_ quieres multipathear, en vez de dar de alta explícitamente cada LUN.

> [!IMPORTANT]
> Después de editar `multipath.conf` hay que regenerar el initramfs si el sistema arranca desde una LUN multipatheada, o el cambio no se aplicará en el siguiente arranque: `update-initramfs -u -k all` en Debian/Ubuntu, `dracut -f` en RHEL/SUSE.

## Interpretar la salida de multipath -ll

```bash
sudo multipath -ll
```

```
datos-oracle (3600d0230000000000e13954ed5f89300) dm-4 WINSYS,SF2372
size=233G features='1 queue_if_no_path' hwhandler='0' wp=rw
|-+- policy='service-time 0' prio=50 status=active
| |- 6:0:0:0 sdf 8:80  active ready running
| `- 7:0:0:0 sdh 8:112 active ready running
`-+- policy='service-time 0' prio=10 status=enabled
  |- 6:0:1:0 sdg 8:96  active ready running
  `- 7:0:1:0 sdi 8:128 active ready running
```

Lectura de arriba a abajo:

1. **Cabecera**: alias (`datos-oracle`), WWID entre paréntesis, nombre del dispositivo device-mapper (`dm-4`), fabricante/modelo reportado por la cabina, tamaño y modo de escritura (`wp=rw`).
2. **Grupos de rutas** (cada bloque `-+-`): cada grupo tiene una política de selección de path (`service-time 0` es el planificador por defecto en muchas configuraciones modernas), una prioridad (`prio`) y un estado de grupo — `active` es el grupo que está sirviendo I/O ahora mismo, `enabled` es un grupo disponible para failover pero no en uso.
3. **Rutas individuales**: cada línea es `<host:bus:target:lun> <dispositivo> <major:minor> <estado dm> <estado checker> <estado sysfs>`. `active ready running` es el estado sano: la ruta está en uso, el chequeo de salud responde y el dispositivo SCSI subyacente está operativo.

Si una ruta cae, su línea cambia a algo como `failed faulty running`, y si es el grupo activo entero el que cae, multipath promociona el siguiente grupo por prioridad (`enabled` → `active`) siguiendo la política de `failback` configurada.

## ALUA: de dónde salen los valores de prio

En el ejemplo anterior, el primer grupo tiene `prio=50` y el segundo `prio=10`. Esos números no salen de la nada: en cabinas que implementan **ALUA** (Asymmetric Logical Unit Access, un estándar SCSI-3), la propia controladora le informa al host, ruta a ruta, en qué estado está esa ruta respecto a la LUN:

- **active/optimized** — ruta hacia la controladora que posee la LUN en ese momento; latencia mínima. Normalmente se traduce en `prio=50`.
- **active/non-optimized** — ruta hacia la controladora "vecina"; funciona, pero añade un salto interno dentro de la cabina. Suele quedar en `prio=10`.
- **standby** / **unavailable** — ruta que no sirve I/O ahora mismo, reservada para failover.

Esto es lo que hace que multipath agrupe las rutas óptimas como grupo `active` y las no óptimas como `enabled`: no es una elección arbitraria, es la propia cabina indicando cuál es el mejor camino en cada momento (y ese "mejor camino" puede cambiar si la LUN migra de controladora).

Para que esto funcione hacen falta dos piezas, normalmente ya resueltas por udev pero que puedes fijar explícitamente por fabricante en la sección `devices`:

```conf
devices {
    device {
        vendor "NETAPP"
        product "LUN.*"
        hardware_handler "1 alua"
        prio alua
        path_grouping_policy group_by_prio
        failback immediate
    }
}
```

- **`hardware_handler`**: el módulo del kernel que traduce los comandos SCSI específicos del array. `"1 alua"` activa el manejador estándar ALUA; algunos arrays más antiguos usan variantes propietarias como `"1 rdac"` (LSI/NetApp E-Series) o `"1 emc"` (EMC Clariion/VNX clásico). Un `hwhandler='0'` en la salida de `multipath -ll` —como en el ejemplo de este artículo— significa que ese array no necesita manejador especial.
- **`prio alua`**: le dice a multipath que calcule la prioridad de cada ruta consultando el estado ALUA reportado por la cabina en lugar de usar un valor fijo.

> [!NOTE]
> Desde el kernel 4.3, Linux detecta automáticamente el soporte ALUA en dispositivos SCSI-3 compatibles y aplica `hardware_handler`/`prio alua` sin necesidad de declararlo a mano en la mayoría de los casos. Aun así, revisar la sección `devices` recomendada por el fabricante de tu cabina evita sorpresas si el autodetect falla o el array necesita un ajuste fino, como `no_path_retry queue` en vez de un valor numérico.

## Construir sobre el dispositivo multipath, no sobre /dev/sdX

Una vez que el mapa existe en `/dev/mapper/<alias>` (o su enlace persistente en `/dev/disk/by-id/dm-uuid-mpath-<wwid>`), cualquier filesystem o physical volume de LVM debe crearse sobre ese dispositivo agregado — nunca sobre una de las rutas físicas individuales (`/dev/sda`, `/dev/sdb`...).

```bash
# Correcto: PV sobre el dispositivo multipath
sudo pvcreate /dev/mapper/datos-oracle

# Incorrecto: PV sobre una única ruta física
# sudo pvcreate /dev/sdf
```

> [!WARNING]
> Si creas un filesystem o un PV directamente sobre `/dev/sda` en vez de `/dev/mapper/<alias>`, pierdes toda la redundancia: el sistema queda escribiendo por una única ruta física y, si esa ruta cae, el volumen se vuelve inaccesible aunque el resto de rutas a la misma LUN sigan funcionando perfectamente.

## Otras banderas útiles de multipath

Además de `-l`/`-ll`, el binario `multipath` tiene un buen puñado de flags para depurar y para limpiar mapas obsoletos:

```bash
# Comprobar si un dispositivo de bloques debería ser una ruta multipath
# (útil para depurar por qué algo no se agrupa como esperas)
sudo multipath -c /dev/sdX

# Dry run: simula sin crear ni modificar ningún devmap
sudo multipath -d

# Forzar el recálculo (reload) de todos los mapas existentes
sudo multipath -r

# Eliminar un mapa concreto que ya no está en uso
sudo multipath -f datos-oracle

# Eliminar TODOS los mapas multipath que no estén en uso
sudo multipath -F

# Gestionar /etc/multipath/wwids manualmente
sudo multipath -a /dev/sdX   # añade el WWID del dispositivo al fichero
sudo multipath -w /dev/sdX   # lo quita del fichero
sudo multipath -W            # reconstruye el fichero con solo los mapas actuales
```

El nivel de detalle de la salida se controla con `-v <nivel>`: `-v0` no imprime nada, `-v1` solo nombres y WWID, `-v2` es el nivel por defecto (topología), y `-v3` vuelca además todas las rutas detectadas durante el escaneo, el nivel que más se usa al depurar por qué una LUN no aparece.

> [!NOTE]
> Con `multipathd` en ejecución (el caso normal), `-f`, `-F` y `-r` delegan la operación en el demonio en vez de tocar los mapas directamente — por eso el resultado es el mismo que usar los comandos equivalentes de `multipathd` que ves a continuación.

## Comandos de administración con multipathd

`multipathd` acepta comandos interactivos o vía `-k`, sin necesidad de reiniciar el servicio para consultar estado o forzar una reconfiguración:

```bash
# Consultar estado de todas las rutas conocidas
sudo multipathd show paths

# Consultar los mapas (dispositivos multipath) configurados
sudo multipathd show maps

# Releer /etc/multipath.conf y aplicar cambios sin reiniciar el demonio
sudo multipathd reconfigure

# Forzar que se reevalúen TODOS los mapas, no solo los que cambiaron
sudo multipathd reconfigure all
```

Para retirar un mapa multipath (por ejemplo, antes de desconectar una LUN que ya no se usa):

```bash
sudo multipathd flush -f datos-oracle
```

> [!CAUTION]
> `multipathd flush` falla —correctamente— si el mapa o alguna de sus particiones está en uso (montado, con un LV activo encima, etc.). No fuerces el desmontaje solo para poder ejecutar el flush: si el volumen sigue en uso, hay datos o procesos dependiendo de él.

Cuando añades nuevas LUNs desde la cabina sin reiniciar el servidor, primero hay que forzar el reescaneo SCSI y luego que multipath las detecte:

```bash
# Reescanea el bus SCSI en busca de nuevos dispositivos (paquete sg3-utils / scsitools)
sudo rescan-scsi-bus.sh

# Fuerza a multipath a reconocer las LUNs nuevas
sudo multipath -v3
```

## Fibre Channel vs. iSCSI: qué cambia

La configuración de multipath en sí (`multipath.conf`, `multipathd`, `multipath -ll`) es idéntica para ambos protocolos, porque multipath opera por encima de las rutas SCSI ya establecidas, sin importar el transporte. La diferencia está en cómo se establecen esas rutas:

- **Fibre Channel**: las rutas dependen de las HBA físicas, el zoning en los switches FC y las conexiones de la cabina. Cada combinación HBA-switch-puerto de controladora es una ruta potencial; herramientas como `lsscsi` y `systool -c fc_host` ayudan a verificar qué HBA ven qué targets.
- **iSCSI**: las rutas se establecen por red IP mediante `open-iscsi` (`iscsiadm`), y cada sesión iSCSI hacia una IP/portal distinta de la cabina cuenta como una ruta independiente. Si segmentas el tráfico iSCSI en su propia VLAN —algo que conviene hacer, como se explica en el artículo sobre [VLANs para segmentar redes](/blog/vlans-explicadas-segmentar-red/)—, cada NIC/VLAN con una sesión iSCSI activa hacia un portal distinto de la cabina se convierte en una ruta más para multipath.

> [!TIP]
> En entornos iSCSI, verifica que cada NIC usada para las sesiones esté en una subred distinta o al menos en interfaces físicas separadas. Si dos "rutas" iSCSI comparten en realidad la misma NIC física, multipath cree que tienes redundancia cuando en verdad tienes un único punto de fallo.

## Troubleshooting habitual

- **Multipath no ve ninguna ruta nueva tras añadir una LUN**: revisa primero que el reescaneo SCSI (`rescan-scsi-bus.sh` o, en iSCSI, `iscsiadm -m session --rescan`) haya detectado el dispositivo a nivel de kernel (`lsscsi`, `dmesg`) antes de culpar a multipath.
- **Aparecen discos locales como dispositivos multipath**: normalmente indica `find_multipaths` mal ajustado o un `blacklist` incompleto; añade el `devnode` o el WWID del disco local a la sección `blacklist`.
- **El failback no ocurre aunque la ruta ya está `running`**: comprueba el valor de `failback` — con `manual` es comportamiento esperado y hay que forzarlo con `multipathd reconfigure`.
- **Logs del demonio**: `multipathd` registra vía syslog/journal; para revisar eventos de path down/up o reconfiguraciones, usa `journalctl -u multipathd`, que se explica con más detalle en el artículo sobre [journalctl y los logs de systemd](/blog/journalctl-domina-logs-systemd/).

## Cómo probar el failover de verdad

Tener `multipath -ll` con buena pinta no es lo mismo que confirmar que el failover funciona bajo carga. Antes de dar por buena una configuración en producción, conviene un test controlado en un entorno de pruebas:

1. **Genera I/O sostenido** contra el dispositivo multipath —nunca contra un `/dev/sdX` individual—:

   ```bash
   # Escritura secuencial continua durante la prueba
   sudo dd if=/dev/zero of=/dev/mapper/datos-oracle bs=1M count=10000 oflag=direct &

   # O, con fio, un patrón más realista de I/O aleatoria
   sudo fio --name=failover-test --filename=/dev/mapper/datos-oracle \
     --rw=randrw --bs=4k --iodepth=16 --numjobs=4 --runtime=120 --time_based
   ```

2. **Observa el estado de las rutas y el throughput en paralelo**, en otra terminal:

   ```bash
   watch -n 1 multipath -ll
   iostat -x 1
   ```

3. **Provoca el fallo de una ruta de forma controlada**: desactiva el puerto en el switch FC/Ethernet, baja la interfaz de una sesión iSCSI (`ip link set ethX down`) o desconecta físicamente un cable si el entorno lo permite.

4. **Confirma en `multipath -ll`** que la ruta caída pasa a `failed faulty running` (o desaparece del grupo activo) y que el I/O de `dd`/`fio` sigue avanzando sin errores. Con `no_path_retry` bien configurado, el throughput puede caer un momento pero el proceso no debería cortarse.

5. **Restaura la ruta** y confirma el failback según el valor de `failback` configurado: con `immediate` se recupera enseguida; con `manual` hay que forzarlo con `multipathd reconfigure`.

> [!TIP]
> Repite la prueba derribando cada ruta por turnos, no solo una. Es habitual que una configuración soporte perder una ruta sin problema pero tenga un error de zoning o de VLAN que deja huérfana a otra en cuanto también falla esa segunda ruta — solo se detecta probándolas todas.

## Siguiente paso

Documentar el WWID, el alias y el grupo de rutas esperado de cada LUN crítica ahorra tiempo cuando toque diagnosticar un incidente a las tres de la madrugada. Y si ya monitorizas tu infraestructura con [Zabbix](/blog/zabbix-monitorizacion-infraestructura/) o una herramienta similar, vale la pena añadir una comprobación periódica del número de rutas activas por dispositivo multipath: una ruta caída silenciosa no da ningún error hasta que cae también la segunda, y para entonces ya es una interrupción real.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
