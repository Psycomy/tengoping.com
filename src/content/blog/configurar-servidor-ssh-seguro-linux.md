---
title: 'Cómo configurar un servidor SSH seguro en Linux'
description: 'Guía paso a paso para configurar y securizar un servidor SSH en cualquier servidor Linux, incluyendo autenticación por clave, fail2ban y mejores prácticas.'
author: 'antonio'
pubDate: 2026-01-01
updatedDate: 2026-08-06
category: 'Linux'
tags: ['SSH', 'Linux', 'Seguridad', 'Sysadmin']
image: '../../assets/images/ssh-server.jpg'
draft: false
---

## Introducción

SSH (Secure Shell) es el protocolo estándar para la administración remota de servidores Linux. En esta guía configuraremos un servidor SSH seguro aplicando las mejores prácticas de seguridad, con instrucciones para las distribuciones más comunes.

Cualquier servidor con el puerto SSH expuesto a Internet recibe intentos de conexión automatizados desde el primer minuto: bots que prueban usuarios comunes (`root`, `admin`, `ubuntu`) y contraseñas de diccionario. Ninguna medida aislada elimina ese ruido por completo, así que esta guía combina varias capas — puerto no estándar, autenticación por clave, cifrados endurecidos, segundo factor y fail2ban — para que el fallo de una no comprometa el servidor.

Este artículo funciona como referencia central de "SSH seguro" en el blog: para reforzar el resto del sistema más allá de SSH, la guía de [hardening básico de servidores Linux](/blog/hardening-basico-servidores-linux/) es el complemento natural, y si el servidor está dentro de una red con más servicios expuestos, [firewalld, UFW y nftables](/blog/firewalld-nftables-seguridad-red-linux/) cubre la política de firewall completa.

```
Cliente SSH intenta conectar a servidor:2222
   │
   ▼
1. Negociación de sesión (KEX / cifrado / MAC)
   KexAlgorithms, Ciphers y MACs restringidos a los endurecidos
   │
   ▼
2. Autenticación por clave pública
   PasswordAuthentication no → clave privada obligatoria
   │
   ▼
3. Segundo factor (TOTP vía PAM)
   KbdInteractiveAuthentication yes + pam_google_authenticator
   │
   ├── código válido           → sesión autenticada; ClientAliveInterval vigila la inactividad
   └── código inválido/agotado → fail2ban banea la IP tras 3 intentos (bantime 3600s)
```

## Instalación y verificación

La mayoría de distribuciones incluyen OpenSSH por defecto. Para asegurarnos de que está instalado y activo:

```bash
# RHEL/Rocky/Oracle Linux
sudo dnf install openssh-server -y

# Ubuntu/Debian
sudo apt install openssh-server -y
```

Activar el servicio:

```bash
sudo systemctl enable --now sshd
sudo systemctl status sshd
```

## Configuración básica del servidor

> [!IMPORTANT]
> Antes de tocar `sshd_config`, confirma que tienes una vía de acceso al servidor que no dependa de SSH: la consola web del proveedor VPS, IPMI/iDRAC en hardware propio, o acceso físico. Los avisos de "no cierres la sesión actual" de esta guía ayudan, pero no cubren un corte de red o un error que ni siquiera deja levantar `sshd`. Sin esa segunda vía, un fallo de configuración puede dejarte fuera del servidor sin forma de arreglarlo remotamente.

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
ClientAliveInterval 300
ClientAliveCountMax 2
Banner /etc/issue.net
```

`ClientAliveInterval 300` hace que el servidor envíe una comprobación de actividad cada 5 minutos; si el cliente no responde durante `ClientAliveCountMax` comprobaciones seguidas (2, es decir 10 minutos de inactividad real), sshd cierra la sesión. Esto reduce el riesgo de una terminal abierta y olvidada en un puesto sin bloquear. `Banner` muestra el contenido de `/etc/issue.net` antes del login — útil para un aviso legal de acceso restringido, no para ocultar la versión del software (eso ya no es una defensa eficaz porque `sshd` sigue anunciando su versión durante el handshake).

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

## Gestión de claves desde el cliente

Si administras varios servidores, escribir `ssh -p 2222 admin@servidor` cada vez y llevar la cuenta de qué clave corresponde a cada uno se vuelve tedioso. El archivo `~/.ssh/config` del cliente resuelve esto con alias:

```
Host produccion
    HostName servidor.midominio.com
    Port 2222
    User admin
    IdentityFile ~/.ssh/id_ed25519_produccion
    IdentitiesOnly yes

Host homelab
    HostName 192.168.1.50
    Port 2222
    User admin
    IdentityFile ~/.ssh/id_ed25519_homelab
    IdentitiesOnly yes
```

Con esto, `ssh produccion` conecta usando el host, puerto, usuario y clave correctos sin repetirlos. `IdentitiesOnly yes` es importante si tienes varias claves cargadas en `ssh-agent`: sin esa línea, el cliente puede ofrecer al servidor una clave distinta a la indicada en `IdentityFile`, lo que en servidores con `MaxAuthTries` bajo puede agotar los intentos antes de probar la clave correcta.

> [!TIP]
> Genera una clave distinta por servidor o grupo de servidores en lugar de reutilizar la misma en todas partes. Si una clave privada se ve comprometida, el radio de impacto queda limitado a los servidores que la aceptan.

## Endurecer los algoritmos criptográficos

La configuración por defecto de OpenSSH acepta algoritmos de intercambio de claves, cifrado y verificación (MAC) más amplios de lo necesario, incluyendo alguno mantenido solo por compatibilidad con clientes muy antiguos. Restringir `sshd_config` a los algoritmos modernos reduce esa superficie:

```ini
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,umac-128-etm@openssh.com
HostKeyAlgorithms ssh-ed25519,rsa-sha2-512,rsa-sha2-256
```

> [!NOTE]
> El proyecto [ssh-audit](https://github.com/jtesta/ssh-audit) mantiene guías de referencia con recomendaciones más agresivas (incluyendo `sntrup761x25519-sha512`, un intercambio de claves resistente a computación cuántica). Lo dejamos fuera de la lista anterior porque requiere OpenSSH 9.x en ambos extremos de la conexión; si tu distribución ya lo trae, es una mejora adicional razonable.

Antes de reiniciar `sshd`, valida la sintaxis y comprueba que ningún cliente que necesites siga usando quedará excluido:

```bash
sudo sshd -t
ssh-audit servidor -p 2222
```

`ssh-audit` (instalable con `pip install ssh-audit` o el paquete de tu distribución) se conecta al servidor y puntúa cada algoritmo activo, señalando cuáles son débiles o están deprecados — es la forma más rápida de verificar que el endurecimiento tuvo efecto real y no solo copiaste una lista de otro sitio.

## Autenticación en dos factores (2FA) con TOTP

Añadir un segundo factor basado en TOTP (Time-based One-Time Password, el mismo mecanismo de Google Authenticator o Authy) hace que una clave privada robada por sí sola no baste para entrar. Se implementa con el módulo PAM `pam_google_authenticator`:

```bash
# Ubuntu/Debian
sudo apt install libpam-google-authenticator -y

# RHEL/Rocky/Oracle Linux (requiere EPEL)
sudo dnf install epel-release -y
sudo dnf install google-authenticator qrencode-libs -y
```

Cada usuario que vaya a usar 2FA ejecuta el asistente en su propia sesión (no como root):

```bash
google-authenticator
```

El asistente genera un código QR (escanéalo con una app TOTP) y una lista de códigos de un solo uso de emergencia — guárdalos fuera del servidor, son la única forma de entrar si pierdes el dispositivo con la app.

Añade el módulo en `/etc/pam.d/sshd`, antes de las líneas `@include`:

```
auth required pam_google_authenticator.so
```

Y en `/etc/ssh/sshd_config`:

```ini
KbdInteractiveAuthentication yes
AuthenticationMethods publickey,keyboard-interactive
```

> [!IMPORTANT]
> En OpenSSH 8.7 y posteriores, `KbdInteractiveAuthentication` sustituye a la antigua `ChallengeResponseAuthentication` (esta última se mantiene solo como alias por compatibilidad). Si tu distribución trae una versión anterior de OpenSSH, usa `ChallengeResponseAuthentication yes` en su lugar. Comprueba la versión con `sshd -V`.

`AuthenticationMethods publickey,keyboard-interactive` obliga a superar ambos factores en orden: primero la clave pública, después el código TOTP. Sin esta línea, PAM y la clave pública se validarían como alternativas independientes en lugar de exigir las dos.

```bash
sudo sshd -t
sudo systemctl restart sshd
```

> [!CAUTION]
> Igual que al cambiar de puerto, no cierres la sesión actual. Verifica el login completo (clave + código TOTP) desde una terminal distinta antes de desconectarte — un error en `AuthenticationMethods` puede dejarte fuera del servidor.

## Configuración del firewall

Abrimos el nuevo puerto antes de reiniciar SSH para no perder el acceso. Si quieres ir más allá de abrir un puerto suelto y aplicar una política de firewall completa, la guía de [firewalld, UFW y nftables](/blog/firewalld-nftables-seguridad-red-linux/) cubre las reglas con más detalle.

```bash
# RHEL/Rocky/Oracle Linux (firewalld)
sudo firewall-cmd --permanent --add-port=2222/tcp
sudo firewall-cmd --permanent --remove-service=ssh
sudo firewall-cmd --reload

# Ubuntu/Debian (ufw)
sudo ufw allow 2222/tcp
sudo ufw delete allow ssh
sudo ufw reload
```

Con el puerto ya abierto en el firewall, aplicamos los cambios reiniciando el servicio SSH:

```bash
sudo systemctl restart sshd
```

> [!CAUTION]
> No cierres la sesión SSH actual. Mantenla abierta como red de seguridad y verifica el nuevo acceso (puerto 2222, login por clave) desde una terminal distinta antes de desconectarte.

## Instalación de Fail2ban

[Fail2ban](/blog/configurar-fail2ban-proteger-servicios/) protege contra ataques de fuerza bruta:

```bash
# RHEL/Rocky/Oracle Linux
sudo dnf install epel-release -y
sudo dnf install fail2ban -y

# Ubuntu/Debian
sudo apt install fail2ban -y
```

Creamos la configuración local:

```bash
sudo tee /etc/fail2ban/jail.local << EOF
[sshd]
enabled = true
port = 2222
filter = sshd
backend = systemd
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

Para filtrar por rango de fechas, exportar a un fichero para análisis posterior, o entender el resto de opciones de `journalctl` más allá de lo básico, [journalctl: domina los logs de systemd](/blog/journalctl-domina-logs-systemd/) cubre el comando en detalle.

## Resumen de seguridad

| Medida                     | Descripción                                         |
| -------------------------- | --------------------------------------------------- |
| Cambiar puerto             | Reduce escaneos automáticos                         |
| Deshabilitar root          | Evita ataques directos a root                       |
| Claves públicas            | Más seguro que contraseñas                          |
| Cifrados endurecidos       | Elimina algoritmos débiles o solo de compatibilidad |
| Autenticación en dos pasos | Una clave robada por sí sola no basta               |
| Fail2ban                   | Bloquea IPs maliciosas                              |
| AllowUsers                 | Lista blanca de usuarios                            |
| ClientAliveInterval        | Cierra sesiones inactivas                           |

## Conclusión

Con estas capas combinadas — puerto no estándar, claves públicas, cifrados endurecidos, segundo factor y fail2ban — un servidor SSH pasa de ser un objetivo fácil para escaneos automatizados a requerir un compromiso previo de la clave privada y del dispositivo TOTP del usuario. Ninguna capa sustituye a las demás: revisa periódicamente los logs con `journalctl` y mantén el sistema actualizado, porque el propio software de OpenSSH sigue recibiendo parches de seguridad incluso con esta configuración endurecida al día. Si quieres seguir reforzando el servidor más allá de SSH, la guía de [hardening básico de servidores Linux](/blog/hardening-basico-servidores-linux/) es el siguiente paso lógico.

> La seguridad es un proceso continuo, no un estado. Revisa y actualiza tus configuraciones regularmente.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
