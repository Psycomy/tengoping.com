# Nuevas categorías "Software" y "Monitorización" — Plan de implementación

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Añadir las categorías "Software" y "Monitorización" al blog, reclasificar el post existente de Prometheus/Grafana, actualizar el generador de imágenes y crear 6 artículos iniciales (3 por categoría).

**Architecture:** Sistema de categorías híbrido — metadata centralizada en `src/data/categories.ts`, colores de imagen en `scripts/generate-images.py`, contenido en frontmatter de posts. Las rutas y componentes se generan dinámicamente sin cambios.

**Tech Stack:** Astro 5, TypeScript, Python (Pillow), Markdown

**Design doc:** `docs/plans/2026-02-16-nuevas-categorias-design.md`

---

### Task 1: Añadir categorías a `src/data/categories.ts`

**Files:**
- Modify: `src/data/categories.ts:38` (antes del cierre `};`)

**Step 1: Añadir las dos entradas**

Insertar antes de la línea `};` al final del archivo:

```typescript
  'Software': {
    icon: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
    description: 'Desarrollo de software, lenguajes, frameworks y buenas prácticas de programación',
  },
  'Monitorización': {
    icon: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
    description: 'Observabilidad, métricas, alertas y dashboards para tus sistemas',
  },
```

**Step 2: Verificar que el dev server no da errores**

Run: `npm run dev` (comprobar que arranca sin errores, parar después)

**Step 3: Commit**

```bash
git add src/data/categories.ts
git commit -m "feat: añadir categorías Software y Monitorización a categories.ts"
```

---

### Task 2: Actualizar `scripts/generate-images.py`

**Files:**
- Modify: `scripts/generate-images.py:48-58` (diccionario `CAT_COLORS`)
- Modify: `scripts/generate-images.py:72-153` (lista `ARTICLES`)

**Step 1: Añadir colores a `CAT_COLORS`**

Añadir 2 entradas al diccionario `CAT_COLORS` (después de `"Hardware": "#FBBF24",`):

```python
    "Software": "#C084FC",
    "Monitorización": "#F472B6",
```

**Step 2: Reclasificar la entrada existente de Prometheus en `ARTICLES`**

Cambiar la entrada `linux-monitoring.jpg` (actualmente en el bloque `# Linux`):

Antes:
```python
    ("linux-monitoring.jpg", "PROMETHEUS", "monitorización con grafana", "Linux",
     ["├── prometheus.yml", "├── node_exporter", "└── grafana:3000"]),
```

Después (mover al nuevo bloque `# Monitorización`):
```python
    ("linux-monitoring.jpg", "PROMETHEUS", "monitorización con grafana", "Monitorización",
     ["├── prometheus.yml", "├── node_exporter", "└── grafana:3000"]),
```

**Step 3: Añadir entradas de nuevos artículos a `ARTICLES`**

Añadir dos bloques nuevos al final de la lista `ARTICLES` (antes de `]`):

```python
    # Software
    ("soft-git.jpg", "GIT", "control de versiones para sysadmins", "Software",
     ["├── git init", "├── git branch", "└── git merge"]),
    ("soft-python.jpg", "PYTHON", "administración de sistemas", "Software",
     ["├── subprocess", "├── paramiko", "└── psutil"]),
    ("soft-cicd.jpg", "GITHUB ACTIONS", "ci/cd guía práctica", "Software",
     ["├── .github/workflows/", "├── jobs:", "└── secrets"]),
    # Monitorización
    ("mon-observabilidad.jpg", "OBSERVABILIDAD", "métricas, logs y trazas", "Monitorización",
     ["├── metrics/", "├── logs/", "└── traces/"]),
    ("mon-alertmanager.jpg", "ALERTMANAGER", "alertas inteligentes", "Monitorización",
     ["├── alertmanager.yml", "├── route:", "└── silence/"]),
    ("mon-uptimekuma.jpg", "UPTIME KUMA", "monitorizar servicios web", "Monitorización",
     ["├── docker-compose.yml", "├── monitors/", "└── notifications/"]),
```

**Step 4: Verificar que el script funciona**

Run: `python3 scripts/generate-images.py --list --category Software`
Expected: muestra las 3 entradas de Software

Run: `python3 scripts/generate-images.py --list --category Monitorización`
Expected: muestra las 4 entradas de Monitorización (3 nuevas + Prometheus reclasificado)

**Step 5: Commit**

```bash
git add scripts/generate-images.py
git commit -m "feat: añadir colores y catálogo de imágenes para Software y Monitorización"
```

---

### Task 3: Reclasificar post existente

**Files:**
- Modify: `src/content/blog/monitorizar-servidores-linux-prometheus-grafana.md:7`

**Step 1: Cambiar categoría en frontmatter**

Antes:
```yaml
category: "Linux"
```

Después:
```yaml
category: "Monitorización"
```

**Step 2: Verificar**

Run: `npm run build` (debe generar la ruta `/categorias/monitorizacion/` con este post)

**Step 3: Commit**

```bash
git add src/content/blog/monitorizar-servidores-linux-prometheus-grafana.md
git commit -m "refactor: reclasificar post de Prometheus/Grafana a categoría Monitorización"
```

---

### Task 4: Escribir artículo — Git para sysadmins (Software)

**Files:**
- Create: `src/content/blog/git-control-versiones-sysadmins.md`

**Step 1: Escribir el artículo**

Usar el skill `blog-write` con estos parámetros:
- Título: "Git para sysadmins: control de versiones en infraestructura"
- Categoría: Software
- Tags: git, control-de-versiones, sysadmin, infraestructura-como-codigo
- Autor: antonio
- Enfoque: uso práctico de Git para gestionar configuraciones, IaC, trabajo en equipo

**Step 2: Generar imagen de portada**

Run: `python3 scripts/generate-images.py soft-git.jpg`

**Step 3: Commit**

```bash
git add src/content/blog/git-control-versiones-sysadmins.md public/images/soft-git.jpg
git commit -m "feat: añadir artículo Git para sysadmins (categoría Software)"
```

---

### Task 5: Escribir artículo — Python para administración de sistemas (Software)

**Files:**
- Create: `src/content/blog/python-administracion-sistemas.md`

**Step 1: Escribir el artículo**

Usar el skill `blog-write` con estos parámetros:
- Título: "Python para administración de sistemas: scripts y automatización"
- Categoría: Software
- Tags: python, scripting, automatizacion, sysadmin
- Autor: antonio
- Enfoque: bibliotecas clave (subprocess, paramiko, psutil), scripts reales, ejemplos prácticos

**Step 2: Generar imagen de portada**

Run: `python3 scripts/generate-images.py soft-python.jpg`

**Step 3: Commit**

```bash
git add src/content/blog/python-administracion-sistemas.md public/images/soft-python.jpg
git commit -m "feat: añadir artículo Python para sysadmins (categoría Software)"
```

---

### Task 6: Escribir artículo — CI/CD con GitHub Actions (Software)

**Files:**
- Create: `src/content/blog/cicd-github-actions-guia-practica.md`

**Step 1: Escribir el artículo**

Usar el skill `blog-write` con estos parámetros:
- Título: "CI/CD con GitHub Actions: guía práctica"
- Categoría: Software
- Tags: ci-cd, github-actions, devops, automatizacion
- Autor: antonio
- Enfoque: workflows básicos, despliegue automatizado, secrets, matrices, ejemplos reales

**Step 2: Generar imagen de portada**

Run: `python3 scripts/generate-images.py soft-cicd.jpg`

**Step 3: Commit**

```bash
git add src/content/blog/cicd-github-actions-guia-practica.md public/images/soft-cicd.jpg
git commit -m "feat: añadir artículo CI/CD con GitHub Actions (categoría Software)"
```

---

### Task 7: Escribir artículo — Introducción a la observabilidad (Monitorización)

**Files:**
- Create: `src/content/blog/introduccion-observabilidad-metricas-logs-trazas.md`

**Step 1: Escribir el artículo**

Usar el skill `blog-write` con estos parámetros:
- Título: "Introducción a la observabilidad: métricas, logs y trazas"
- Categoría: Monitorización
- Tags: observabilidad, metricas, logs, trazas, monitoring
- Autor: antonio
- Enfoque: los tres pilares, por qué importa, herramientas del ecosistema, comparativa

**Step 2: Generar imagen de portada**

Run: `python3 scripts/generate-images.py mon-observabilidad.jpg`

**Step 3: Commit**

```bash
git add src/content/blog/introduccion-observabilidad-metricas-logs-trazas.md public/images/mon-observabilidad.jpg
git commit -m "feat: añadir artículo Introducción a la observabilidad (categoría Monitorización)"
```

---

### Task 8: Escribir artículo — Alertas inteligentes con Alertmanager (Monitorización)

**Files:**
- Create: `src/content/blog/alertas-inteligentes-alertmanager-prometheus.md`

**Step 1: Escribir el artículo**

Usar el skill `blog-write` con estos parámetros:
- Título: "Alertas inteligentes con Alertmanager y Prometheus"
- Categoría: Monitorización
- Tags: alertmanager, prometheus, alertas, monitoring
- Autor: antonio
- Enfoque: configuración, routing, silencing, evitar fatiga de alertas, ejemplos de reglas

**Step 2: Generar imagen de portada**

Run: `python3 scripts/generate-images.py mon-alertmanager.jpg`

**Step 3: Commit**

```bash
git add src/content/blog/alertas-inteligentes-alertmanager-prometheus.md public/images/mon-alertmanager.jpg
git commit -m "feat: añadir artículo Alertas con Alertmanager (categoría Monitorización)"
```

---

### Task 9: Escribir artículo — Uptime Kuma (Monitorización)

**Files:**
- Create: `src/content/blog/uptime-kuma-monitorizar-servicios-web.md`

**Step 1: Escribir el artículo**

Usar el skill `blog-write` con estos parámetros:
- Título: "Monitorizar servicios web con Uptime Kuma"
- Categoría: Monitorización
- Tags: uptime-kuma, monitoring, self-hosting, disponibilidad
- Autor: antonio
- Enfoque: instalación con Docker, configurar checks HTTP/TCP/ping, notificaciones, dashboard

**Step 2: Generar imagen de portada**

Run: `python3 scripts/generate-images.py mon-uptimekuma.jpg`

**Step 3: Commit**

```bash
git add src/content/blog/uptime-kuma-monitorizar-servicios-web.md public/images/mon-uptimekuma.jpg
git commit -m "feat: añadir artículo Uptime Kuma (categoría Monitorización)"
```

---

### Task 10: Verificación final

**Step 1: Build completo**

Run: `npm run build`
Expected: sin errores, se generan las rutas:
- `/categorias/software/`
- `/categorias/monitorizacion/`

**Step 2: Verificar visualmente**

Run: `npm run preview`
- Comprobar `/categorias/` muestra las 10 categorías con iconos
- Comprobar `/categorias/software/` muestra 3 artículos
- Comprobar `/categorias/monitorizacion/` muestra 4 artículos (3 nuevos + Prometheus)
- Comprobar homepage muestra secciones de ambas categorías

**Step 3: Generar todas las imágenes faltantes**

Run: `python3 scripts/generate-images.py --auto --category Software`
Run: `python3 scripts/generate-images.py --auto --category Monitorización`

**Step 4: Commit final si hay cambios pendientes**

```bash
git add -A
git commit -m "feat: verificación final — nuevas categorías Software y Monitorización completas"
```
