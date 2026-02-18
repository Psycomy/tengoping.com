---
title: 'Git para sysadmins: control de versiones en infraestructura'
description: 'Guía práctica de Git orientada a administradores de sistemas: versiona configuraciones, gestiona infraestructura como código y colabora en equipo sin miedo a romper nada.'
author: 'antonio'
pubDate: 2026-02-16
category: 'Software'
tags: ['git', 'control-de-versiones', 'sysadmin', 'infraestructura-como-codigo']
image: '../../assets/images/soft-git.jpg'
draft: false
---

## Por qué un sysadmin necesita Git

Todos hemos estado ahí: `sshd_config.bak`, `sshd_config.bak2`, `sshd_config.FUNCIONA`. Si gestionas servidores y todavía versionas archivos con copias manuales, Git va a cambiar tu forma de trabajar.

Git no es solo para desarrolladores. Cualquier archivo de texto que modifiques con frecuencia — configuraciones de Nginx, playbooks de Ansible, reglas de firewall, scripts de mantenimiento — se beneficia de un historial de cambios rastreable, reversible y compartible.

## Requisitos previos

- Un sistema Linux con Git instalado (`sudo apt install git` o `sudo dnf install git`)
- Conocimientos básicos de terminal
- Ganas de dejar atrás los `.bak`

## Configuración inicial

Antes de tu primer commit, Git necesita saber quién eres:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```

Algunos ajustes útiles para sysadmins:

```bash
# Editor por defecto (vim, nano, lo que prefieras)
git config --global core.editor vim

# Rama por defecto
git config --global init.defaultBranch main

# Colores en la salida
git config --global color.ui auto
```

## Tu primer repositorio: versionando /etc

Imaginemos que quieres versionar la configuración de Nginx en un servidor:

```bash
# Crear un repo para las configs de nginx
mkdir -p ~/infra/nginx && cd ~/infra/nginx
git init

# Copiar las configs actuales
cp /etc/nginx/nginx.conf .
cp -r /etc/nginx/sites-available .

# Primer commit: el estado actual
git add .
git commit -m "feat: estado inicial de configuración nginx"
```

A partir de ahora, cada cambio que hagas queda registrado con autor, fecha y descripción.

## Los comandos esenciales

### Ver el estado actual

```bash
# Qué archivos han cambiado
git status

# Diferencias exactas línea a línea
git diff

# Historial de commits
git log --oneline --graph
```

### Registrar cambios

```bash
# Añadir archivos modificados al staging
git add nginx.conf

# Crear un commit con un mensaje descriptivo
git commit -m "fix: aumentar client_max_body_size a 50M"

# Añadir y commitear en un paso (solo archivos ya tracked)
git commit -am "fix: corregir timeout de proxy_pass"
```

### Deshacer errores

Aquí es donde Git brilla frente a los `.bak`:

```bash
# Descartar cambios no commiteados en un archivo
git checkout -- nginx.conf

# Volver a un commit anterior (ver el estado sin perder nada)
git log --oneline
git checkout abc1234 -- nginx.conf

# Revertir un commit entero creando uno nuevo inverso
git revert HEAD
```

## Ramas: experimenta sin miedo

Las ramas te permiten probar cambios sin tocar la configuración estable:

```bash
# Crear rama para experimentar con HTTP/3
git checkout -b feature/http3

# Hacer cambios y commits en la rama
vim nginx.conf
git commit -am "feat: habilitar HTTP/3 con QUIC"

# Si funciona, integrar en main
git checkout main
git merge feature/http3

# Si no funciona, descartar
git checkout main
git branch -d feature/http3
```

Este flujo es ideal para cambios en producción: preparas todo en una rama, pruebas, y solo si funciona lo integras.

## Repositorios remotos: colaboración y backup

Un repositorio remoto (en Gitea, GitLab o GitHub) te da backup automático y colaboración con el equipo:

```bash
# Conectar con un remoto
git remote add origin git@gitea.local:infra/nginx-config.git

# Subir tu rama main
git push -u origin main

# Traer cambios de un compañero
git pull origin main
```

### Flujo de trabajo en equipo

```
          ┌─────────┐
          │ Remoto   │  (Gitea/GitLab)
          │ (origin) │
          └────┬─────┘
         push ↑ ↓ pull
          ┌───┴──────┐
     ┌────┤  main    ├────┐
     │    └──────────┘    │
     ▼                    ▼
  ┌──────────┐    ┌──────────┐
  │ Sysadmin │    │ Sysadmin │
  │    A     │    │    B     │
  └──────────┘    └──────────┘
```

Cada sysadmin trabaja en su copia local, sube cambios al remoto y los demás los integran con `git pull`.

## .gitignore para infraestructura

No todo debe versionarse. Crea un `.gitignore` para excluir secretos y archivos generados:

```bash
# Secretos y credenciales
*.key
*.pem
*.secret
.env
vault-password

# Archivos generados
*.retry
*.pyc
__pycache__/

# Backups del editor
*~
*.swp
```

## Caso práctico: infraestructura como código

Si usas Ansible, Terraform o scripts de aprovisionamiento, Git es imprescindible. Una estructura típica:

```
infra/
├── ansible/
│   ├── inventory/
│   │   ├── production
│   │   └── staging
│   ├── playbooks/
│   │   ├── webservers.yml
│   │   └── monitoring.yml
│   └── roles/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── scripts/
│   ├── backup.sh
│   └── deploy.sh
└── .gitignore
```

Con esta estructura versionada:

- Cada cambio en la infraestructura tiene un autor y una razón
- Puedes volver atrás si un despliegue falla
- Los nuevos miembros del equipo ven la evolución de la infra
- Las revisiones de código aplican también a la configuración

## Buenas prácticas para sysadmins

**Commits descriptivos:** Usa mensajes que expliquen el _por qué_, no solo el _qué_.

```bash
# Mal
git commit -m "cambios nginx"

# Bien
git commit -m "fix: resolver timeout en proxy hacia backend API (504)"
```

**Commits atómicos:** Cada commit debe ser un cambio lógico completo. No mezcles la configuración de Nginx con las reglas del firewall en el mismo commit.

**Nunca versiones secretos:** Usa herramientas como `ansible-vault`, `sops` o variables de entorno para las credenciales. Si un secreto llega a Git por error, considera que está comprometido.

**Etiqueta las versiones estables:** Cuando una configuración está probada y en producción, márcala:

```bash
git tag -a v1.2.0 -m "Nginx con HTTP/2 y rate limiting"
git push origin v1.2.0
```

## Siguiente paso

Una vez que tengas tus configuraciones versionadas, el siguiente nivel es automatizar despliegues: que un `git push` dispare la aplicación de cambios en los servidores. Eso es CI/CD aplicado a infraestructura, y lo cubriremos en un próximo artículo.

Por ahora, el primer paso es sencillo: crea un repositorio, versiona lo que tienes, y empieza a hacer commits. Tu futuro yo te lo agradecerá la primera vez que necesites volver atrás.
