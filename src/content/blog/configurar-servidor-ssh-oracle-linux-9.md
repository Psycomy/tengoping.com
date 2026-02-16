---
title: "Cómo configurar un servidor SSH seguro en Oracle Linux 9"
description: "Guía paso a paso para configurar y securizar un servidor SSH en Oracle Linux 9, incluyendo autenticación por clave, fail2ban y mejores prácticas."
author: "antonio"
pubDate: 2025-01-15
category: "Linux"
tags: ["SSH", "Oracle Linux", "Seguridad", "Sysadmin"]
image: "/images/ssh-server.jpg"
draft: false
---

## Introducción

SSH (Secure Shell) es el protocolo estándar para la administración remota de servidores Linux. En esta guía configuraremos un servidor SSH seguro en Oracle Linux 9, aplicando las mejores prácticas de seguridad.

## Instalación y verificación

Oracle Linux 9 incluye OpenSSH por defecto. Verificamos que esté instalado y activo:

```bash
sudo dnf install openssh-server -y
sudo systemctl enable --now sshd
sudo systemctl status sshd
```

## Configuración básica del servidor

Editamos el archivo de configuración principal:

```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
sudo vi /etc/ssh/sshd_config
```

### Parámetros recomendados

Los parámetros más importantes a configurar:

```ini
Port 2222
PermitRootLogin no
MaxAuthTries 3
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
X11Forwarding no
AllowUsers admin deploy
```

## Autenticación por clave pública

Generamos un par de claves en el cliente:

```bash
ssh-keygen -t ed25519 -C "admin@tengoping.com"
ssh-copy-id -p 2222 admin@servidor
```

### Verificar la conexión

```bash
ssh -p 2222 admin@servidor
```

## Configuración del firewall

Abrimos el nuevo puerto en firewalld:

```bash
sudo firewall-cmd --permanent --add-port=2222/tcp
sudo firewall-cmd --permanent --remove-service=ssh
sudo firewall-cmd --reload
```

## Instalación de Fail2ban

Fail2ban protege contra ataques de fuerza bruta:

```bash
sudo dnf install epel-release -y
sudo dnf install fail2ban -y
```

Creamos la configuración local:

```bash
sudo tee /etc/fail2ban/jail.local << EOF
[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/secure
maxretry = 3
bantime = 3600
findtime = 600
EOF
```

```bash
sudo systemctl enable --now fail2ban
sudo fail2ban-client status sshd
```

## Monitorización de accesos

Revisamos los logs de acceso regularmente:

```bash
sudo journalctl -u sshd -f
sudo lastlog
sudo last -n 20
```

## Resumen de seguridad

| Medida | Descripción |
|--------|-------------|
| Cambiar puerto | Reduce escaneos automáticos |
| Deshabilitar root | Evita ataques directos a root |
| Claves públicas | Más seguro que contraseñas |
| Fail2ban | Bloquea IPs maliciosas |
| AllowUsers | Lista blanca de usuarios |

## Conclusión

Con estas configuraciones tendremos un servidor SSH robusto y seguro. Recuerda mantener el sistema actualizado y revisar los logs periódicamente.

> La seguridad es un proceso continuo, no un estado. Revisa y actualiza tus configuraciones regularmente.
