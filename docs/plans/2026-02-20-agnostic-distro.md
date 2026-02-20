# Artículos agnósticos multi-distro — Plan de implementación

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Hacer que 6 artículos del blog muestren comandos para Oracle Linux / RHEL y Ubuntu Server, renombrando el artículo SSH para que sea genérico.

**Architecture:** Edición directa de archivos Markdown. El formato establecido en el proyecto es un único bloque bash con comentarios `# RHEL / Rocky / Oracle Linux` y `# Ubuntu / Debian` separando los comandos de cada distro.

**Tech Stack:** Markdown, Astro 5, script Python `scripts/generate-images.py`

---

## Referencia: formato estándar del proyecto

Todos los bloques de instalación deben seguir este patrón:

```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install <paquete> -y

# Ubuntu / Debian
sudo apt install <paquete> -y
```

---

### Task 1: Renombrar y ampliar el artículo SSH

**Files:**

- Delete + Create: `src/content/blog/configurar-servidor-ssh-oracle-linux-9.md` → `src/content/blog/configurar-servidor-ssh-seguro-linux.md`

**Step 1: Eliminar el archivo original**

```bash
git rm src/content/blog/configurar-servidor-ssh-oracle-linux-9.md
```

**Step 2: Crear el nuevo archivo con scope genérico**

Crear `src/content/blog/configurar-servidor-ssh-seguro-linux.md` con este contenido exacto:

````markdown
---
title: 'Cómo configurar un servidor SSH seguro en Linux'
description: 'Guía paso a paso para configurar y securizar un servidor SSH en cualquier servidor Linux, incluyendo autenticación por clave, fail2ban y mejores prácticas.'
author: 'antonio'
pubDate: 2026-01-01
category: 'Linux'
tags: ['SSH', 'Linux', 'Seguridad', 'Sysadmin']
image: '../../assets/images/ssh-server.jpg'
draft: false
---

## Introducción

SSH (Secure Shell) es el protocolo estándar para la administración remota de servidores Linux. En esta guía configuraremos un servidor SSH seguro aplicando las mejores prácticas de seguridad, con instrucciones para las distribuciones más comunes.

## Instalación y verificación

La mayoría de distribuciones incluyen OpenSSH por defecto. Para asegurarnos de que está instalado y activo:

```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install openssh-server -y

# Ubuntu / Debian
sudo apt install openssh-server -y
```
````

Activar el servicio:

```bash
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

Abrimos el nuevo puerto antes de reiniciar SSH para no perder el acceso.

```bash
# RHEL / Rocky / Oracle Linux (firewalld)
sudo firewall-cmd --permanent --add-port=2222/tcp
sudo firewall-cmd --permanent --remove-service=ssh
sudo firewall-cmd --reload

# Ubuntu / Debian (ufw)
sudo ufw allow 2222/tcp
sudo ufw delete allow ssh
sudo ufw reload
```

## Instalación de Fail2ban

Fail2ban protege contra ataques de fuerza bruta:

```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install epel-release -y
sudo dnf install fail2ban -y

# Ubuntu / Debian
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

## Resumen de seguridad

| Medida            | Descripción                   |
| ----------------- | ----------------------------- |
| Cambiar puerto    | Reduce escaneos automáticos   |
| Deshabilitar root | Evita ataques directos a root |
| Claves públicas   | Más seguro que contraseñas    |
| Fail2ban          | Bloquea IPs maliciosas        |
| AllowUsers        | Lista blanca de usuarios      |

## Conclusión

Con estas configuraciones tendremos un servidor SSH robusto y seguro. Recuerda mantener el sistema actualizado y revisar los logs periódicamente.

> La seguridad es un proceso continuo, no un estado. Revisa y actualiza tus configuraciones regularmente.
> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.

````

**Step 3: Commit**

```bash
git add src/content/blog/configurar-servidor-ssh-seguro-linux.md
git commit -m "content: renombrar SSH a genérico y añadir alternativas Ubuntu/Debian"
````

---

### Task 2: Ansible — añadir apt y cambiar módulo dnf

**Files:**

- Modify: `src/content/blog/automatizar-servidores-ansible-primeros-pasos.md:18-21` (bloque instalación)
- Modify: `src/content/blog/automatizar-servidores-ansible-primeros-pasos.md:44-47` (módulo dnf en YAML)

**Step 1: Reemplazar el bloque de instalación (líneas 18-21)**

Texto actual:

````markdown
```bash
sudo dnf install ansible-core -y
ansible --version
```
````

````

Reemplazar por:
```markdown
```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install ansible-core -y

# Ubuntu / Debian
sudo apt install ansible -y

ansible --version
````

````

**Step 2: Cambiar el módulo `dnf:` por `ansible.builtin.package:` en el playbook (líneas 44-47)**

Texto actual:
```yaml
    - name: Instalar nginx
      dnf:
        name: nginx
        state: present
````

Reemplazar por:

```yaml
- name: Instalar nginx
  ansible.builtin.package:
    name: nginx
    state: present
```

Aplicar el mismo cambio en `sysadmin-aprender-automatizacion-2025.md` (misma sustitución, líneas 39-42):

Texto actual:

```yaml
- name: Instalar Nginx
  dnf:
    name: nginx
    state: present
```

Reemplazar por:

```yaml
- name: Instalar Nginx
  ansible.builtin.package:
    name: nginx
    state: present
```

**Step 3: Commit**

```bash
git add src/content/blog/automatizar-servidores-ansible-primeros-pasos.md \
        src/content/blog/sysadmin-aprender-automatizacion-2025.md
git commit -m "content: usar ansible.builtin.package y añadir apt en artículos Ansible"
```

---

### Task 3: DNS BIND9 — añadir alternativa Ubuntu

**Files:**

- Modify: `src/content/blog/dns-bind9-servidor-autoritativo.md:18-21`

**Step 1: Reemplazar el bloque de instalación (líneas 18-21)**

Texto actual:

````markdown
```bash
sudo dnf install bind bind-utils -y
sudo systemctl enable --now named
```
````

````

Reemplazar por:
```markdown
```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install bind bind-utils -y
sudo systemctl enable --now named

# Ubuntu / Debian
sudo apt install bind9 bind9utils -y
sudo systemctl enable --now bind9
````

````

**Step 2: Commit**

```bash
git add src/content/blog/dns-bind9-servidor-autoritativo.md
git commit -m "content: añadir alternativa Ubuntu/Debian en artículo DNS BIND9"
````

---

### Task 4: Podman — añadir alternativa Ubuntu

**Files:**

- Modify: `src/content/blog/introduccion-contenedores-podman-linux.md:18-21`

**Step 1: Reemplazar el bloque de instalación (líneas 18-21)**

Texto actual:

````markdown
```bash
sudo dnf install podman -y
podman --version
```
````

````

Reemplazar por:
```markdown
```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install podman -y

# Ubuntu / Debian
sudo apt install podman -y

podman --version
````

````

**Step 2: Commit**

```bash
git add src/content/blog/introduccion-contenedores-podman-linux.md
git commit -m "content: añadir alternativa Ubuntu/Debian en artículo Podman"
````

---

### Task 5: Prometheus/Grafana — añadir alternativa Ubuntu para Grafana

**Files:**

- Modify: `src/content/blog/monitorizar-servidores-linux-prometheus-grafana.md:118-121`

**Step 1: Reemplazar el bloque de instalación de Grafana (líneas 118-121)**

Texto actual:

````markdown
```bash
sudo dnf install -y https://dl.grafana.com/oss/release/grafana-11.1.0-1.x86_64.rpm
sudo systemctl enable --now grafana-server
```
````

````

Reemplazar por:
```markdown
```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install -y https://dl.grafana.com/oss/release/grafana-11.1.0-1.x86_64.rpm

# Ubuntu / Debian
wget -q -O /usr/share/keyrings/grafana.key https://apt.grafana.com/gpg.key
echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://apt.grafana.com stable main" \
  | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install grafana -y
````

Activar el servicio:

```bash
sudo systemctl enable --now grafana-server
```

````

**Step 2: Commit**

```bash
git add src/content/blog/monitorizar-servidores-linux-prometheus-grafana.md
git commit -m "content: añadir alternativa Ubuntu/Debian para Grafana en artículo Prometheus"
````

---

### Task 6: Verificar build y comprobar imágenes

**Step 1: Build de producción**

```bash
npm run build
```

Esperado: sin errores. Si hay error de contenido, revisar el archivo con el problema.

**Step 2: Verificar imágenes con el script**

```bash
python3 scripts/generate-images.py --check
```

Esperado: no se reportan imágenes huérfanas ni faltantes relacionadas con los cambios.

**Step 3: Push**

```bash
git push
```
