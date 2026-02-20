---
title: 'Automatizar servidores con Ansible: primeros pasos'
description: 'Guía de inicio con Ansible para automatizar la configuración y gestión de servidores Linux de forma declarativa.'
author: 'antonio'
pubDate: 2026-01-08
category: 'Automatización'
tags: ['Ansible', 'Automatización', 'DevOps', 'Linux']
image: '../../assets/images/auto-ansible.jpg'
draft: false
---

## ¿Por qué Ansible?

Ansible permite automatizar la configuración de servidores de forma declarativa, sin agentes y usando SSH. Es ideal para sysadmins que quieren dar el salto a la infraestructura como código.

## Instalación

```bash
# RHEL / Rocky / Oracle Linux
sudo dnf install ansible-core -y

# Ubuntu / Debian
sudo apt install ansible -y

ansible --version
```

## Inventario

Definimos los servidores a gestionar en `/etc/ansible/hosts`:

```ini
[webservers]
web1.tengoping.com
web2.tengoping.com

[dbservers]
db1.tengoping.com
```

## Primer playbook

```yaml
# site.yml
- name: Configurar servidores web
  hosts: webservers
  become: true
  tasks:
    - name: Instalar nginx
      ansible.builtin.package:
        name: nginx
        state: present

    - name: Iniciar nginx
      systemd:
        name: nginx
        state: started
        enabled: true

    - name: Abrir puerto 80
      firewalld:
        port: 80/tcp
        permanent: true
        state: enabled
        immediate: true
```

```bash
ansible-playbook site.yml --check
ansible-playbook site.yml
```

## Roles para organizar

```bash
ansible-galaxy init roles/webserver
```

## Conclusión

Ansible reduce el trabajo manual y garantiza consistencia en la configuración. Empieza con playbooks simples y evoluciona hacia roles reutilizables.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
