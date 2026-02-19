---
title: 'Permisos en Linux: chmod, chown y ACLs explicados'
description: 'Entiende el sistema de permisos de Linux, desde los básicos con chmod y chown hasta las ACLs para control de acceso avanzado.'
author: 'antonio'
pubDate: 2025-02-10
category: 'Linux'
tags: ['Permisos', 'Linux', 'Seguridad', 'ACL']
image: '../../assets/images/linux-permissions.jpg'
draft: false
---

## Permisos básicos en Linux

Cada archivo tiene tres niveles de permisos: propietario (u), grupo (g) y otros (o), con tres acciones: lectura (r), escritura (w) y ejecución (x).

```bash
ls -la /etc/passwd
# -rw-r--r-- 1 root root 2847 ene 15 10:30 /etc/passwd
```

## chmod: cambiar permisos

### Notación octal

```bash
chmod 755 script.sh    # rwxr-xr-x
chmod 644 config.yml   # rw-r--r--
chmod 600 id_rsa       # rw-------
```

### Notación simbólica

```bash
chmod u+x script.sh
chmod g-w archivo.txt
chmod o= archivo.txt
```

## chown: cambiar propietario

```bash
sudo chown usuario:grupo archivo.txt
sudo chown -R www-data:www-data /var/www
```

## ACLs para control avanzado

Cuando los permisos básicos no son suficientes:

```bash
sudo setfacl -m u:deploy:rx /opt/app
sudo setfacl -m g:developers:rwx /opt/app/src
getfacl /opt/app
```

### ACLs por defecto en directorios

```bash
sudo setfacl -d -m g:developers:rwx /opt/app/src
```

## Permisos especiales

| Permiso | Octal | Uso                              |
| ------- | ----- | -------------------------------- |
| SUID    | 4000  | Ejecutar como propietario        |
| SGID    | 2000  | Heredar grupo del directorio     |
| Sticky  | 1000  | Solo el propietario puede borrar |

## Conclusión

Comprender los permisos en Linux es fundamental para la seguridad del sistema. Las ACLs complementan los permisos tradicionales cuando se necesita mayor granularidad.

> [!NOTE]
> ✍️ Transparencia: Este artículo ha sido creado con el apoyo de herramientas de inteligencia artificial. Toda la información técnica ha sido revisada y validada por el autor antes de su publicación.
