---
title: "Introducción a contenedores con Podman en Linux"
description: "Aprende a usar Podman como alternativa a Docker para gestionar contenedores en Linux sin necesidad de un daemon root."
author: "antonio"
pubDate: 2025-01-20
category: "Linux"
tags: ["Podman", "Contenedores", "Linux", "Docker"]
image: "/images/linux-containers.jpg"
draft: false
---

## ¿Qué es Podman?

Podman es una herramienta para gestionar contenedores OCI que no requiere un daemon corriendo como root. Es compatible con la CLI de Docker, lo que facilita la transición.

## Instalación

```bash
sudo dnf install podman -y
podman --version
```

## Primeros pasos

### Descargar una imagen

```bash
podman pull docker.io/library/nginx:alpine
podman images
```

### Ejecutar un contenedor

```bash
podman run -d --name web -p 8080:80 nginx:alpine
podman ps
curl http://localhost:8080
```

### Gestión básica

```bash
podman stop web
podman start web
podman logs web
podman rm -f web
```

## Pods en Podman

Podman soporta pods de forma nativa, similar a Kubernetes:

```bash
podman pod create --name mi-pod -p 8080:80
podman run -d --pod mi-pod --name web nginx:alpine
podman pod ps
```

## Conclusión

Podman es una alternativa sólida a Docker, especialmente en entornos donde la seguridad y la ejecución sin root son prioritarias.
