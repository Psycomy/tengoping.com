# Diseño: Artículos agnósticos multi-distro

**Fecha**: 2026-02-20
**Estado**: Aprobado

## Objetivo

Hacer agnósticos los artículos que solo muestran comandos de Oracle Linux / RHEL (dnf),
añadiendo alternativas para Ubuntu Server (apt). Mantener consistencia con el formato
ya establecido en los 8 artículos que ya tienen cobertura dual.

## Formato estándar

Un único bloque de código con comentarios de distro como cabecera:

```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install ...

# Ubuntu / Debian
sudo apt install ...
```

Este formato ya está en uso en 8 artículos del blog y es el patrón canónico.

## Artículos a modificar

### 1. configurar-servidor-ssh-oracle-linux-9.md → configurar-servidor-ssh-seguro-linux.md

Rename del archivo + ampliación de scope:

| Campo       | Antes                                       | Después                                   |
| ----------- | ------------------------------------------- | ----------------------------------------- |
| filename    | `configurar-servidor-ssh-oracle-linux-9.md` | `configurar-servidor-ssh-seguro-linux.md` |
| title       | `...en Oracle Linux 9`                      | `...en Linux`                             |
| description | `...en Oracle Linux 9...`                   | `...en cualquier servidor Linux...`       |
| tags        | `SSH, Oracle Linux, Seguridad, Sysadmin`    | `SSH, Linux, Seguridad, Sysadmin`         |
| image       | `ssh-server.jpg`                            | `ssh-server.jpg` (sin cambio)             |
| contenido   | Solo Oracle Linux / dnf                     | Bloques duales RHEL + Ubuntu              |

### 2. automatizar-servidores-ansible-primeros-pasos.md

- Añadir `apt install ansible` como alternativa al `dnf install ansible-core`
- Cambiar el módulo `dnf:` en el snippet YAML → `ansible.builtin.package:` (genérico)

### 3. dns-bind9-servidor-autoritativo.md

- Añadir `apt install bind9 bind9utils` como alternativa al `dnf install bind bind-utils`

### 4. introduccion-contenedores-podman-linux.md

- Añadir `apt install podman` como alternativa al `dnf install podman`

### 5. monitorizar-servidores-linux-prometheus-grafana.md

- Sustituir el `dnf install` del RPM de Grafana por un bloque dual:
  RHEL (dnf + RPM) y Ubuntu/Debian (apt + repositorio oficial)

### 6. sysadmin-aprender-automatizacion-2025.md

- Cambiar `dnf:` → `ansible.builtin.package:` en el snippet YAML de Ansible

## Script de imágenes

Sin cambios necesarios. La entrada `ssh-server.jpg` en el catálogo ya usa texto
genérico ("SSH SERVER / configuración segura / Linux"). Tras los cambios, ejecutar:

```bash
python3 scripts/generate-images.py --check
```

## Lo que NO se toca

Los 8 artículos que ya tienen el formato correcto con ambas distros:

- `configurar-fail2ban-proteger-servicios.md`
- `hardening-basico-servidores-linux.md`
- `auditoria-seguridad-lynis-linux.md`
- `certificados-ssl-lets-encrypt-certbot.md`
- `cifrado-discos-luks-linux.md`
- `introduccion-kvm-libvirt-linux.md`
- `proxy-inverso-nginx-guia-practica.md`
- `wireguard-vpn-autoalojada.md`
