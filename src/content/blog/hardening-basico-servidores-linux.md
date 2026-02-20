---
title: 'Hardening básico de servidores Linux'
description: 'Lista de medidas esenciales para securizar un servidor Linux recién instalado: SSH, usuarios, firewall, kernel y auditoría.'
author: 'antonio'
pubDate: 2026-01-22
category: 'Seguridad'
tags: ['Linux', 'Hardening', 'SSH', 'Sysadmin']
image: '../../assets/images/linux-hardening.jpg'
draft: false
---

## Por qué hacer hardening

Un servidor Linux con la instalación por defecto no está preparado para producción. Los valores predeterminados priorizan la compatibilidad sobre la seguridad. Un hardening básico reduce drásticamente la superficie de ataque sin complicar la administración diaria.

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

Edita `/etc/ssh/sshd_config`:

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

Aplica los cambios:

```bash
sudo systemctl restart sshd
```

Recuerda abrir el nuevo puerto en el firewall **antes** de reiniciar SSH para no quedarte fuera.

## 3. Configurar el firewall

Abre solo lo necesario:

```bash
sudo firewall-cmd --permanent --remove-service=ssh
sudo firewall-cmd --permanent --add-port=2222/tcp
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

```bash
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

## Checklist rápido

| Medida               | Comando de verificación                     |
| -------------------- | ------------------------------------------- |
| Sistema actualizado  | `dnf check-update`                          |
| Root SSH desactivado | `grep PermitRootLogin /etc/ssh/sshd_config` |
| Firewall activo      | `firewall-cmd --list-all`                   |
| fail2ban corriendo   | `fail2ban-client status`                    |
| Servicios mínimos    | `systemctl list-units --state=running`      |
| Auditoría activa     | `auditctl -l`                               |

## Conclusión

Estas medidas cubren lo esencial. No hacen el servidor invulnerable, pero elevan significativamente el nivel de esfuerzo necesario para comprometerlo. El siguiente paso sería implementar SELinux en modo enforcing y configurar un SIEM centralizado para correlacionar los logs de auditoría.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
