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

Ansible permite automatizar la configuración de servidores de forma declarativa, sin agentes y usando SSH. Es ideal para sysadmins que quieren dar el salto a la infraestructura como código, versionada en [Git](/blog/git-control-versiones-sysadmins/) igual que cualquier otro proyecto.

Ansible usa una arquitectura sin agente: el equipo desde el que lanzas los comandos (el **control node**) se conecta por SSH a los servidores que gestiona (los **managed nodes**), sin instalar nada en ellos más allá de Python. Con el inventario de ejemplo que usaremos en este artículo, se ve así:

```
Control node (tu portátil o servidor de gestión)
   │
   │ SSH + Python — sin agente en los managed nodes
   │
   ├── web1.tengoping.com   (grupo [webservers])
   ├── web2.tengoping.com   (grupo [webservers])
   └── db1.tengoping.com    (grupo [dbservers])
```

## Instalación

```bash
# RHEL/Rocky/Oracle Linux
sudo dnf install ansible-core -y

# Ubuntu/Debian
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

    - name: Abrir puerto 80 en firewalld (RHEL/Rocky/Oracle)
      ansible.posix.firewalld:
        port: 80/tcp
        permanent: true
        state: enabled
        immediate: true
      when: ansible_os_family == "RedHat"

    - name: Abrir puerto 80 en ufw (Ubuntu/Debian)
      community.general.ufw:
        rule: allow
        port: '80'
        proto: tcp
      when: ansible_os_family == "Debian"
```

```bash
ansible-playbook site.yml --check
ansible-playbook site.yml
```

> [!TIP]
> `--check` simula la ejecución sin aplicar ningún cambio real (modo dry-run) y te muestra qué tareas se marcarían como "changed". Ejecútalo siempre antes del playbook real cuando toques un playbook nuevo o modificado — así detectas errores de sintaxis o cambios inesperados antes de que afecten al servidor.

## Roles para organizar

Un playbook plano como `site.yml` funciona bien para tareas puntuales, pero se vuelve difícil de mantener en cuanto crece: mezclas tareas de distintos servicios en el mismo fichero, no puedes reutilizar nada entre proyectos, y compartirlo con otro equipo significa copiar y pegar. Un **role** empaqueta tareas, handlers, plantillas, ficheros y variables relacionadas con un mismo propósito (por ejemplo, "instalar y configurar nginx") en una estructura de directorios estandarizada que Ansible sabe cargar automáticamente.

Genera el esqueleto de un role con `ansible-galaxy init`:

```bash
ansible-galaxy init roles/webserver
```

Esto crea la siguiente estructura:

```
roles/webserver/
├── tasks/main.yml       # tareas del role — el punto de entrada
├── handlers/main.yml    # handlers (p. ej. reiniciar nginx)
├── defaults/main.yml    # variables con valor por defecto, fáciles de sobrescribir
├── vars/main.yml        # variables del role, con más prioridad que defaults
├── templates/           # plantillas Jinja2 (p. ej. nginx.conf.j2)
├── files/                # ficheros estáticos que se copian tal cual
├── meta/main.yml        # metadatos: dependencias del role, plataformas soportadas
└── tests/                 # inventory y playbook mínimos para probar el role
```

Migrando las tareas de nginx del playbook anterior a `tasks/main.yml` del role:

```yaml
# roles/webserver/tasks/main.yml
- name: Instalar nginx
  ansible.builtin.package:
    name: nginx
    state: present
  notify: Reiniciar nginx

- name: Desplegar configuración personalizada
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  notify: Reiniciar nginx

- name: Iniciar y habilitar nginx
  ansible.builtin.systemd:
    name: nginx
    state: started
    enabled: true
```

```yaml
# roles/webserver/handlers/main.yml
- name: Reiniciar nginx
  ansible.builtin.systemd:
    name: nginx
    state: restarted
```

El `template` de la tarea anterior se resuelve contra `roles/webserver/templates/nginx.conf.j2`, y el handler solo se ejecuta si alguna tarea que lo invoca con `notify` termina en estado `changed` — así evitas reiniciar el servicio en cada ejecución del playbook si no hubo cambios reales.

Con el role creado, `site.yml` queda mucho más corto — solo referencia el role en vez de listar tareas sueltas:

```yaml
# site.yml
- name: Configurar servidores web
  hosts: webservers
  become: true
  roles:
    - webserver
```

Pasa a roles cuando un playbook empieza a repetir las mismas tareas en varios proyectos, cuando crece tanto que cuesta encontrar nada en él, o cuando quieres compartir una configuración probada con otro equipo o publicarla en Ansible Galaxy.

## Conclusión

Ansible reduce el trabajo manual y garantiza consistencia en la configuración. Empieza con playbooks simples y evoluciona hacia roles reutilizables. Si quieres probarlos contra una VM desechable antes de tocar un servidor real, combínalos con [Vagrant](/blog/vagrant-entornos-desarrollo-reproducibles/), que ya soporta Ansible como provisioner.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
