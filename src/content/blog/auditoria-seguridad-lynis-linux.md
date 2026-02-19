---
title: 'Auditoría de seguridad con Lynis en Linux'
description: 'Cómo usar Lynis para auditar la seguridad de servidores Linux, interpretar resultados y aplicar las recomendaciones.'
author: 'antonio'
pubDate: 2025-09-12
category: 'Seguridad'
tags: ['Lynis', 'Auditoría', 'Hardening', 'Seguridad']
image: '../../assets/images/lynis-audit.jpg'
draft: false
---

## Que es Lynis

Lynis es una herramienta de auditoria de seguridad para sistemas Unix y Linux. Analiza la configuracion del sistema, los servicios en ejecucion, la gestion de usuarios, la configuracion de red, el kernel y muchos otros aspectos para generar un informe con puntuacion de hardening y recomendaciones concretas.

A diferencia de un escaner de vulnerabilidades externo, Lynis se ejecuta localmente con acceso completo al sistema, lo que le permite detectar problemas de configuracion que un escaner remoto no veria.

## Instalacion

Lynis esta disponible en los repositorios de la mayoria de distribuciones y tambien se puede ejecutar directamente desde el repositorio git.

### Desde el gestor de paquetes

```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install lynis -y

# Debian / Ubuntu
sudo apt install lynis -y
```

### Desde el repositorio git

Esta opcion te da siempre la version mas reciente:

```bash
cd /opt
sudo git clone https://github.com/CISOfy/lynis.git
cd lynis
sudo ./lynis audit system
```

Verifica la version instalada:

```bash
lynis show version
```

## Ejecutar una auditoria basica

La auditoria completa del sistema se lanza con un unico comando. Ejecutala como root para que Lynis tenga acceso a todos los archivos de configuracion:

```bash
sudo lynis audit system
```

La auditoria tarda entre uno y cinco minutos dependiendo del sistema. Lynis muestra el progreso en tiempo real, agrupando las comprobaciones por categorias: boot, kernel, memoria, usuarios, shells, sistema de archivos, USB, red, impresoras, correo, firewalls, servidores web, SSH, SNMP, bases de datos, LDAP, PHP, Squid, logging, cron y mas.

Al finalizar, muestra un resumen con el indice de hardening:

```text
  Hardening index : 67 [#############       ]
  Tests performed : 275
  Plugins enabled : 0
```

## Interpretar el informe

El informe completo se guarda en `/var/log/lynis.log` y los datos estructurados en `/var/log/lynis-report.dat`. Los elementos clave del informe son:

### Indice de hardening

Una puntuacion de 0 a 100 que refleja el estado general de seguridad. Un servidor recien instalado suele puntuar entre 55 y 65. Con un hardening basico puedes superar los 80 puntos.

### Warnings

Son los hallazgos mas criticos que requieren atencion inmediata. Puedes listar solo las advertencias con:

```bash
sudo grep Warning /var/log/lynis.log
```

### Suggestions

Recomendaciones de mejora ordenadas por prioridad. Cada sugerencia incluye un identificador, una descripcion y en muchos casos un enlace a documentacion adicional:

```bash
sudo grep Suggestion /var/log/lynis-report.dat
```

Ejemplo de sugerencia tipica:

```text
suggestion[]=BOOT-5122|Set a password on GRUB boot loader to prevent altering boot configuration|-|-|
suggestion[]=SSH-7408|Consider hardening SSH configuration: AllowTcpForwarding (set NO)|-|-|
```

### Secciones clave

Centrate primero en estas areas para obtener el mayor impacto:

- **SSH configuration**: desactivar root login, forzar claves, limitar cifrados debiles.
- **File permissions**: archivos con permisos excesivos, SUID/SGID innecesarios.
- **Kernel hardening**: parametros sysctl como `net.ipv4.conf.all.rp_filter` o `kernel.randomize_va_space`.
- **Authentication**: politica de contrasenas, cuentas sin password, usuarios inactivos.
- **Firewall**: verificar que hay un firewall activo y configurado.
- **Logging and auditing**: comprobar que rsyslog/journald y auditd estan activos.

## Automatizar auditorias con cron

Programar auditorias periodicas permite detectar regresiones de seguridad cuando se instalan nuevos paquetes o se modifica la configuracion.

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

Programalo en cron para que se ejecute semanalmente:

```bash
sudo crontab -e
```

```text
0 3 * * 1 /opt/lynis-audit.sh
```

La opcion `--cronjob` suprime la interactividad y `--quiet` reduce la salida a lo esencial.

## Comparar informes a lo largo del tiempo

Guardar los archivos `lynis-report.dat` con fecha permite comparar la evolucion del hardening. Puedes extraer el indice de cada informe con:

```bash
for f in /var/log/lynis-reports/lynis-report-*.dat; do
    fecha=$(basename "$f" | grep -oP '\d{8}')
    indice=$(grep hardening_index "$f" | cut -d= -f2)
    echo "$fecha: $indice"
done
```

Esto produce una salida como:

```text
20250901: 67
20250908: 72
20250915: 78
```

Si el indice baja entre dos ejecuciones, revisa las diferencias en los archivos `.dat` para identificar que ha cambiado.

## Perfiles personalizados

Lynis soporta perfiles de auditoria que definen que tests ejecutar y cuales omitir. El perfil por defecto esta en `/etc/lynis/default.prf`. Puedes crear un perfil personalizado para tu organizacion:

```bash
sudo cp /etc/lynis/default.prf /etc/lynis/custom.prf
```

Edita `custom.prf` para ajustar opciones como tests a omitir o directorios adicionales a analizar, y ejecuta Lynis con tu perfil:

```bash
sudo lynis audit system --profile /etc/lynis/custom.prf
```

## Recomendaciones para maximizar el impacto

- Ejecuta Lynis **antes y despues** de cada cambio de configuracion importante para medir el efecto.
- No persigas una puntuacion de 100; algunas sugerencias pueden no aplicar a tu caso de uso. Evalua cada recomendacion en tu contexto.
- Combina Lynis con otras herramientas: `rkhunter` para rootkits, `aide` para integridad de archivos y `auditd` para registrar accesos a archivos criticos.
- Mantiene Lynis actualizado. Las versiones nuevas incorporan tests para vulnerabilidades y configuraciones recientes.

Lynis no corrige los problemas automaticamente, pero te da un mapa claro de donde estan las debilidades de tu sistema y que hacer para resolverlas.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
