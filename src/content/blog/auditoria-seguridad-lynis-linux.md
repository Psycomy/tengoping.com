---
title: 'Auditoría de seguridad con Lynis en Linux'
description: 'Cómo usar Lynis para auditar la seguridad de servidores Linux, interpretar resultados y aplicar las recomendaciones.'
author: 'antonio'
pubDate: 2026-02-07
updatedDate: 2026-07-27
category: 'Seguridad'
tags: ['Lynis', 'Auditoría', 'Hardening', 'Seguridad']
image: '../../assets/images/lynis-audit.jpg'
draft: false
---

## Qué es Lynis

Lynis es una herramienta de auditoría de seguridad para sistemas Unix y Linux. Analiza la configuración del sistema, los servicios en ejecución, la gestión de usuarios, la configuración de red, el kernel y muchos otros aspectos para generar un informe con puntuación de hardening y recomendaciones concretas.

A diferencia de un escáner de vulnerabilidades externo, Lynis se ejecuta localmente con acceso completo al sistema, lo que le permite detectar problemas de configuración que un escáner remoto no vería.

## Instalación

Lynis está disponible en los repositorios de la mayoría de distribuciones y también se puede ejecutar directamente desde el repositorio git.

### Desde el gestor de paquetes

```bash
# RHEL/Rocky/Oracle Linux
sudo dnf install lynis -y

# Ubuntu/Debian
sudo apt install lynis -y
```

### Desde el repositorio git

Esta opción te da siempre la versión más reciente:

```bash
cd /opt
sudo git clone https://github.com/CISOfy/lynis.git
cd lynis
sudo ./lynis audit system
```

Verifica la versión instalada:

```bash
lynis show version
```

> [!NOTE]
> Los comandos de las siguientes secciones (`lynis show version`, `sudo lynis audit system`, `--profile /etc/lynis/custom.prf`) asumen que Lynis está en el PATH, como ocurre con la instalación por paquete. Si lo instalaste clonando el repositorio en /opt/lynis, invoca `./lynis` desde ese directorio o crea un symlink: `sudo ln -s /opt/lynis/lynis /usr/local/bin/lynis`.

## Ejecutar una auditoría básica

El flujo completo de una auditoría con Lynis, desde que la lanzas hasta que vuelves a comprobar el resultado, es siempre el mismo:

```
sudo lynis audit system
   │
   ▼
1. Detecta la distribución y el sistema instalado
   │
   ▼
2. Ejecuta los tests por categoría (boot, kernel, red, SSH,
   firewalls, logging, cron...)
   │
   ▼
3. Genera el informe
   ├── /var/log/lynis.log        → detalle legible y warnings
   └── /var/log/lynis-report.dat → datos estructurados (hardening_index, suggestion[]=...)
   │
   ▼
4. Revisas warnings y suggestions, aplicas el hardening que corresponda
   │
   ▼
5. Vuelves a auditar para medir el efecto del cambio
```

La auditoría completa del sistema se lanza con un único comando. Ejecútala como root para que Lynis tenga acceso a todos los archivos de configuración:

```bash
sudo lynis audit system
```

La auditoría tarda entre uno y cinco minutos dependiendo del sistema. Lynis muestra el progreso en tiempo real, agrupando las comprobaciones por categorías: boot, kernel, memoria, usuarios, shells, sistema de archivos, USB, red, impresoras, correo, firewalls, servidores web, SSH, SNMP, bases de datos, LDAP, PHP, Squid, logging, cron y más.

Al finalizar, muestra un resumen con el indice de hardening:

```text
  Hardening index : 67 [#############       ]
  Tests performed : 275
  Plugins enabled : 0
```

## Interpretar el informe

El informe completo se guarda en `/var/log/lynis.log` y los datos estructurados en `/var/log/lynis-report.dat`. Los elementos clave del informe son:

### Índice de hardening

Una puntuación de 0 a 100 que refleja el estado general de seguridad. Un servidor recién instalado suele puntuar entre 55 y 65. Con un [hardening básico](/blog/hardening-basico-servidores-linux/) puedes superar los 80 puntos.

### Warnings

Son los hallazgos más críticos que requieren atención inmediata. Puedes listar solo las advertencias con:

```bash
sudo grep Warning /var/log/lynis.log
```

### Suggestions

Recomendaciones de mejora ordenadas por prioridad. Cada sugerencia incluye un identificador, una descripción y en muchos casos un enlace a documentación adicional:

```bash
sudo grep 'suggestion\[\]=' /var/log/lynis-report.dat
```

Ejemplo de sugerencia típica:

```text
suggestion[]=BOOT-5122|Set a password on GRUB boot loader to prevent altering boot configuration|-|-|
suggestion[]=SSH-7408|Consider hardening SSH configuration: AllowTcpForwarding (set NO)|-|-|
```

### Secciones clave

Céntrate primero en estas áreas para obtener el mayor impacto:

- **SSH configuration**: [desactivar root login, forzar claves](/blog/configurar-servidor-ssh-seguro-linux/), limitar cifrados débiles.
- **File permissions**: archivos con permisos excesivos, SUID/SGID innecesarios.
- **Kernel hardening**: parámetros sysctl como `net.ipv4.conf.all.rp_filter` o `kernel.randomize_va_space`.
- **Authentication**: política de contraseñas, cuentas sin password, usuarios inactivos.
- **Firewall**: verificar que hay un [firewall activo y configurado](/blog/firewalld-nftables-seguridad-red-linux/).
- **Logging and auditing**: comprobar que rsyslog/journald y auditd están activos.

## Automatizar auditorías con cron

Programar auditorías periódicas permite detectar regresiones de seguridad cuando se instalan nuevos paquetes o se modifica la configuración.

Crea un script wrapper:

```bash
sudo tee /opt/lynis-audit.sh << 'EOF'
#!/bin/bash
FECHA=$(date +%Y%m%d)
REPORT_DIR="/var/log/lynis-reports"
mkdir -p "$REPORT_DIR"
cd /opt/lynis || exit 1
./lynis audit system --cronjob --quiet > "$REPORT_DIR/lynis-$FECHA.log" 2>&1
cp /var/log/lynis-report.dat "$REPORT_DIR/lynis-report-$FECHA.dat"
EOF
sudo chmod +x /opt/lynis-audit.sh
```

Prográmalo en cron para que se ejecute semanalmente:

```bash
sudo crontab -e
```

```text
0 3 * * 1 /opt/lynis-audit.sh
```

La opción `--cronjob` suprime la interactividad y `--quiet` reduce la salida a lo esencial.

## Comparar informes a lo largo del tiempo

Guardar los archivos `lynis-report.dat` con fecha permite comparar la evolución del hardening. Puedes extraer el índice de cada informe con:

```bash
for f in /var/log/lynis-reports/lynis-report-*.dat; do
    fecha=$(basename "$f" | grep -oP '\d{8}')
    indice=$(grep hardening_index "$f" | cut -d= -f2)
    echo "$fecha: $indice"
done
```

Esto produce una salida como:

```text
20260901: 67
20260908: 72
20260915: 78
```

Si el índice baja entre dos ejecuciones, revisa las diferencias en los archivos `.dat` para identificar qué ha cambiado.

## Perfiles personalizados

Lynis soporta perfiles de auditoría que definen qué tests ejecutar y cuáles omitir. El perfil por defecto está en `/etc/lynis/default.prf`. Puedes crear un perfil personalizado para tu organización:

```bash
sudo cp /etc/lynis/default.prf /etc/lynis/custom.prf
```

Edita `custom.prf` para ajustar opciones como tests a omitir o directorios adicionales a analizar, y ejecuta Lynis con tu perfil:

```bash
sudo lynis audit system --profile /etc/lynis/custom.prf
```

## Recomendaciones para maximizar el impacto

- Ejecuta Lynis **antes y después** de cada cambio de configuración importante para medir el efecto.
- No persigas una puntuación de 100; algunas sugerencias pueden no aplicar a tu caso de uso. Evalúa cada recomendación en tu contexto.
- Combina Lynis con otras herramientas: `rkhunter` para rootkits, `aide` para integridad de archivos y `auditd` para registrar accesos a archivos críticos.
- Mantén Lynis actualizado. Las versiones nuevas incorporan tests para vulnerabilidades y configuraciones recientes.

Lynis no corrige los problemas automáticamente, pero te da un mapa claro de dónde están las debilidades de tu sistema y qué hacer para resolverlas.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
