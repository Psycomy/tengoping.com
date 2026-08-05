---
title: 'Automatizar servidores con Ansible: primeros pasos'
description: 'Ansible desde cero: comandos ad-hoc, playbooks, roles, variables por grupo, bucles y secretos con ansible-vault, paso a paso.'
author: 'antonio'
pubDate: 2026-01-08
updatedDate: 2026-08-05
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

## Comandos ad-hoc: antes de escribir un playbook

Para una tarea de una sola vez no hace falta un playbook — un comando ad-hoc aplica un módulo directamente contra el inventario:

```bash
ansible webservers -m ping                              # comprueba conectividad SSH + Python
ansible webservers -a "uptime"                           # ejecuta un comando arbitrario
ansible webservers -m package -a "name=htop state=present" --become
```

Es la forma más rápida de verificar que el inventario y las credenciales SSH están bien configurados antes de escribir nada más elaborado, y sigue siendo útil después para comprobaciones puntuales que no merece la pena convertir en un playbook.

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

## Variables por grupo y por host

En vez de repetir valores dentro del playbook, `group_vars/` y `host_vars/` los definen fuera, según a quién apliquen. Ansible los carga automáticamente si el nombre del archivo coincide con el grupo o host del inventario:

```
inventory/
├── hosts
├── group_vars/
│   └── webservers.yml   # variables para todo el grupo [webservers]
└── host_vars/
    └── web1.tengoping.com.yml   # variables solo para ese host
```

```yaml
# group_vars/webservers.yml
nginx_worker_processes: auto
nginx_port: 80
```

Dentro de una tarea o plantilla, se referencian igual que cualquier otra variable: `{{ nginx_port }}`.

## Bucles

Para repetir una tarea con distintos valores, `loop` es la forma recomendada actualmente (la sintaxis más antigua `with_items` sigue funcionando, pero `loop` es la que documenta Ansible como estándar):

```yaml
- name: Instalar varios paquetes
  ansible.builtin.package:
    name: '{{ item }}'
    state: present
  loop:
    - htop
    - curl
    - vim
```

## Secretos con ansible-vault

Una contraseña de base de datos o una clave de API no deberían acabar en texto plano en un repositorio Git, ni siquiera privado. `ansible-vault` cifra archivos o valores individuales:

```bash
ansible-vault encrypt_string --vault-password-file ~/.vault_pass 'S3cr3t0!' --name 'db_password'
ansible-vault edit group_vars/dbservers/vault.yml --vault-password-file ~/.vault_pass
```

```bash
ansible-playbook site.yml --vault-password-file ~/.vault_pass
```

> [!CAUTION]
> El archivo de contraseña del vault (`~/.vault_pass` en estos ejemplos) nunca debe subirse al repositorio — añádelo a `.gitignore`. Es la clave que descifra todos los secretos del proyecto; si se filtra, todos los secretos cifrados con ella quedan comprometidos.

## Ejecución selectiva con tags

Cuando un playbook crece y no quieres re-ejecutar todas sus tareas cada vez, las `tags` permiten lanzar solo un subconjunto:

```yaml
- name: Desplegar configuración personalizada
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  tags: [config]
```

```bash
ansible-playbook site.yml --tags config    # solo las tareas etiquetadas "config"
ansible-playbook site.yml --skip-tags config   # todo menos esas
```

## Conclusión

Ansible reduce el trabajo manual y garantiza consistencia en la configuración. Empieza con playbooks simples y evoluciona hacia roles reutilizables. Si quieres probarlos contra una VM desechable antes de tocar un servidor real, combínalos con [Vagrant](/blog/vagrant-entornos-desarrollo-reproducibles/), que ya soporta Ansible como provisioner.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
