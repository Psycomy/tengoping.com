---
title: 'Hardening básico de servidores Linux'
description: 'Checklist de hardening en el orden correcto: SSH, firewall, usuarios, kernel, AIDE, chrony y verificación final con Lynis.'
author: 'antonio'
pubDate: 2026-01-22
updatedDate: 2026-08-05
category: 'Seguridad'
tags: ['Linux', 'Hardening', 'SSH', 'Sysadmin']
image: '../../assets/images/linux-hardening.jpg'
draft: false
---

## Por qué hacer hardening

Un servidor Linux con la instalación por defecto no está preparado para producción. Los valores predeterminados priorizan la compatibilidad sobre la seguridad. Un hardening básico reduce drásticamente la superficie de ataque sin complicar la administración diaria.

Cada medida individual —SSH, firewall, fail2ban— tiene su propia guía dedicada en este blog con el detalle completo; lo que aporta este artículo es el **orden en que aplicarlas** y por qué ese orden importa. Aplicarlas en el orden equivocado es la forma más habitual de quedarte fuera de tu propio servidor a mitad de proceso:

```
1. Actualizar el sistema
   │
   ▼
2. Securizar SSH (editar sshd_config, NO reiniciar todavía)
   │
   ▼
3. Abrir el nuevo puerto SSH en el firewall
   │
   ├── puerto abierto y sesión de respaldo activa → reiniciar sshd
   └── sin verificar → NO reiniciar: te quedarías sin acceso remoto
   │
   ▼
4. Resto del firewall, usuarios, sudo, kernel, servicios, fail2ban, auditoría
   │
   ▼
5. Verificar el resultado completo con Lynis
```

El paso 3 es el que más cuesta arreglar si se salta: si reinicias `sshd` con la configuración nueva antes de haber abierto el puerto correspondiente en el firewall, pierdes la conexión SSH activa y no tienes forma de abrir uno nuevo salvo por acceso físico o consola del proveedor.

## 1. Mantener el sistema actualizado

Lo más básico y lo más efectivo:

```bash
# RHEL/Rocky/Oracle Linux
sudo dnf update -y
sudo dnf install dnf-automatic
sudo systemctl enable --now dnf-automatic-install.timer

# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

## 2. Securizar SSH

Para una guía completa paso a paso —incluyendo claves públicas y verificación de la conexión antes de cerrar la sesión— consulta [cómo configurar un servidor SSH seguro](/blog/configurar-servidor-ssh-seguro-linux/). Aquí el resumen: edita `/etc/ssh/sshd_config`:

```text
Port 2222
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers admin deploy
```

> [!CAUTION]
> Antes de reiniciar SSH, abre el nuevo puerto en el firewall para no quedarte fuera (se detalla en el siguiente apartado). Si reinicias el servicio sin haber abierto el puerto o sin mantener una sesión activa como red de seguridad, puedes perder el acceso remoto al servidor.

```bash
sudo firewall-cmd --permanent --remove-service=ssh
sudo firewall-cmd --permanent --add-port=2222/tcp
sudo firewall-cmd --reload
```

Aplica los cambios:

```bash
sudo systemctl restart sshd
```

## 3. Configurar el firewall

El puerto SSH ya se abrió en el paso anterior; ahora abre el resto de lo necesario. Si necesitas reglas más avanzadas que abrir servicios sueltos, la guía de [firewalld, UFW y nftables](/blog/firewalld-nftables-seguridad-red-linux/) entra en más detalle:

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

## 4. Política de usuarios

```bash
# Eliminar usuarios innecesarios
sudo userdel -r games
sudo userdel -r ftp

# Forzar contraseñas fuertes
sudo dnf install libpwquality
```

Edita `/etc/security/pwquality.conf`:

```text
minlen = 12
dcredit = -1
ucredit = -1
lcredit = -1
ocredit = -1
```

Configura expiración de contraseñas:

```bash
sudo chage -M 90 -W 14 admin
```

Comprueba también qué algoritmo de hash usa el sistema para las contraseñas nuevas — muchas distros modernas ya traen SHA-512 o `yescrypt` por defecto, pero vale la pena confirmarlo en vez de asumirlo:

```bash
grep ENCRYPT_METHOD /etc/login.defs
```

## 5. Limitar sudo

Evita dar `ALL=(ALL) ALL` a todos. Usa permisos granulares en `/etc/sudoers.d/`:

```bash
# /etc/sudoers.d/deploy
deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart app, /usr/bin/journalctl -u app
```

Así el usuario `deploy` solo puede reiniciar la app y ver sus logs.

## 6. Parámetros de kernel

Añade a `/etc/sysctl.d/90-hardening.conf`:

```text
# Desactivar IP forwarding (si no es un router)
net.ipv4.ip_forward = 0

# Ignorar ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Protección contra SYN flood
net.ipv4.tcp_syncookies = 1

# Ignorar pings broadcast
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Protección contra IP spoofing
net.ipv4.conf.all.rp_filter = 1

# Desactivar source routing
net.ipv4.conf.all.accept_source_route = 0
```

Aplicar:

```bash
sudo sysctl --system
```

## 7. Desactivar servicios innecesarios

```bash
# Ver servicios activos
systemctl list-units --type=service --state=running

# Desactivar lo que no necesites
sudo systemctl disable --now cups
sudo systemctl disable --now avahi-daemon
sudo systemctl disable --now bluetooth
```

## 8. Configurar fail2ban

Configuración mínima aquí; para filtros personalizados, jails adicionales y gestión de baneos consulta la [guía dedicada de Fail2Ban](/blog/configurar-fail2ban-proteger-servicios/).

```bash
sudo dnf install epel-release -y
sudo dnf install fail2ban
```

Crea `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 2222
```

```bash
sudo systemctl enable --now fail2ban
```

Comprobar IPs baneadas:

```bash
sudo fail2ban-client status sshd
```

## 9. Auditoría con auditd

```bash
sudo dnf install audit
sudo systemctl enable --now auditd
```

Reglas básicas en `/etc/audit/rules.d/hardening.rules`:

```text
# Monitorizar cambios en /etc/passwd y /etc/shadow
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity

# Monitorizar cambios en sudoers
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d/ -p wa -k sudoers

# Monitorizar cambios en sshd_config
-w /etc/ssh/sshd_config -p wa -k sshd
```

Cargar las reglas:

```bash
sudo augenrules --load
```

Consultar eventos:

```bash
sudo ausearch -k identity -ts recent
```

Esto son solo tres reglas básicas para arrancar. Si quieres profundizar en reglas más completas, `ausearch`/`aureport` y cómo interpretar los logs de auditd, tienes la guía dedicada en [auditoría de eventos con auditd](/blog/auditd-auditoria-eventos-sistema-linux/).

## 10. Reducir la superficie: deshabilitar sistemas de archivos que no usas

La mayoría de servidores nunca necesitan montar un CD-ROM antiguo (`cramfs`), un disco Mac (`hfs`/`hfsplus`) o un DVD (`udf`). Tener el módulo del kernel disponible aunque no se use es superficie de ataque gratuita. Añade a `/etc/modprobe.d/hardening-filesystems.conf`:

```text
install cramfs /bin/true
install freevxfs /bin/true
install hfs /bin/true
install hfsplus /bin/true
install udf /bin/true
```

`install <módulo> /bin/true` hace que, si algo intenta cargar ese módulo, el kernel ejecute `/bin/true` (que no hace nada) en vez del módulo real — de facto lo deshabilita sin necesidad de recompilar el kernel.

## 11. Vigilar la integridad de archivos con AIDE

auditd (paso 9) registra _quién_ cambió un archivo mientras el sistema está en marcha; AIDE responde a una pregunta distinta: _¿ha cambiado algo_ desde la última vez que lo comprobaste, incluso si el cambio ocurrió con el sistema apagado o auditd desactivado?

```bash
sudo dnf install aide      # RHEL/Rocky/Oracle Linux
sudo apt install aide      # Ubuntu/Debian

sudo aide --init
sudo mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz
sudo aide --check
```

> [!IMPORTANT]
> Inicializa la base de datos de AIDE justo después de instalar el servidor, con el sistema en un estado que sabes que es limpio — nunca después de sospechar un compromiso, porque en ese punto ya no puedes confiar en que el estado "de referencia" sea realmente limpio.

Programa la comprobación periódica con un [timer de systemd](/blog/tareas-programadas-cron-systemd-timers/) que ejecute `aide --check` y notifique si hay diferencias.

## 12. Sincronizar el reloj con chrony

Un reloj desincronizado no parece un problema de seguridad hasta que necesitas correlacionar eventos entre el log de auditd, el de fail2ban y el de otro servidor tras un incidente, y los timestamps no cuadran entre sí:

```bash
sudo dnf install chrony -y   # RHEL/Rocky/Oracle Linux (suele venir preinstalado)
sudo apt install chrony -y   # Ubuntu/Debian

sudo systemctl enable --now chronyd
chronyc tracking             # comprobar el estado de la sincronización
```

## Verificar el resultado con Lynis

Después de aplicar los pasos anteriores, [Lynis](/blog/auditoria-seguridad-lynis-linux/) audita el sistema completo y señala qué queda pendiente, en vez de fiarte de memoria de haber cubierto todo:

```bash
sudo lynis audit system
```

## Checklist rápido

| Medida               | Comando de verificación                     |
| -------------------- | ------------------------------------------- |
| Sistema actualizado  | `dnf check-update`                          |
| Root SSH desactivado | `grep PermitRootLogin /etc/ssh/sshd_config` |
| Firewall activo      | `firewall-cmd --list-all`                   |
| fail2ban corriendo   | `fail2ban-client status`                    |
| Servicios mínimos    | `systemctl list-units --state=running`      |
| Auditoría activa     | `auditctl -l`                               |
| AIDE inicializado    | `aide --check`                              |
| Reloj sincronizado   | `chronyc tracking`                          |

## Conclusión

Estas medidas cubren lo esencial, aplicadas en un orden que evita el error más común: quedarte fuera del servidor a mitad de proceso. No hacen el servidor invulnerable, pero elevan significativamente el nivel de esfuerzo necesario para comprometerlo, y Lynis te da un punto de partida objetivo para medir cuánto falta. El siguiente paso natural sería implementar SELinux en modo enforcing y configurar un SIEM centralizado para correlacionar los logs de auditoría.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
