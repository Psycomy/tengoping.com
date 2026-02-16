# Diseño: Nuevas categorías "Software" y "Monitorización"

**Fecha**: 2026-02-16
**Estado**: Aprobado

## Objetivo

Añadir dos nuevas categorías al blog tengoping.com:

- **Software** — Desarrollo de software: lenguajes, frameworks, CI/CD, buenas prácticas de programación
- **Monitorización** — Observabilidad, métricas, alertas, logging y dashboards

## Cambios en infraestructura

### 1. `src/data/categories.ts`

Añadir 2 entradas al objeto `categoryMeta`:

```typescript
'Software': {
  icon: `<svg>...</svg>`,  // Icono estilo Lucide: llaves { } (Code)
  description: 'Desarrollo de software, lenguajes, frameworks y buenas prácticas de programación',
},
'Monitorización': {
  icon: `<svg>...</svg>`,  // Icono estilo Lucide: línea de pulso (Activity)
  description: 'Observabilidad, métricas, alertas y dashboards para tus sistemas',
},
```

### 2. `scripts/generate-images.py` — `CAT_COLORS`

Añadir 2 colores al diccionario:

```python
"Software": "#C084FC",       # Violeta claro
"Monitorización": "#F472B6", # Rosa
```

### 3. `scripts/generate-images.py` — `ARTICLES`

Añadir entradas al catálogo para los nuevos artículos (6 entradas, 3 por categoría).

### 4. Reclasificación de posts existentes

| Post | Categoría actual | Nueva categoría |
|------|-----------------|-----------------|
| `monitorizar-servidores-linux-prometheus-grafana.md` | Linux | Monitorización |

Cambiar el campo `category` en el frontmatter.

## Colores

| Categoría | Color | Hex |
|-----------|-------|-----|
| Software | Violeta claro | `#C084FC` |
| Monitorización | Rosa | `#F472B6` |

Paleta existente de referencia:
- Automatización: `#00BFFF`, Linux: `#58D5A2`, Opinión: `#FF6D00`
- Redes: `#1A73E8`, Virtualización: `#A78BFA`, Seguridad: `#F87171`
- Self-Hosting: `#34D399`, Hardware: `#FBBF24`

## Iconos SVG

**Software** (Code/llaves):
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="16 18 22 12 16 6"/>
  <polyline points="8 6 2 12 8 18"/>
</svg>
```

> Nota: Este icono es similar al de Automatización (que usa code-slash con línea diagonal).
> Diferenciación: Automatización tiene la línea diagonal `<line x1="14" y1="4" x2="10" y2="20"/>`,
> Software solo tiene las llaves angulares `< >`.

**Monitorización** (Activity/pulso):
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
</svg>
```

## Artículos iniciales

### Software (3 artículos)

1. **Introducción a Git para sysadmins**
   - Slug: `git-control-versiones-sysadmins`
   - Tags: `[git, control-de-versiones, sysadmin, infraestructura-como-codigo]`
   - Contenido: repos, branches, merge, uso práctico para configs e IaC

2. **Python para administración de sistemas**
   - Slug: `python-administracion-sistemas`
   - Tags: `[python, scripting, automatizacion, sysadmin]`
   - Contenido: scripts útiles, bibliotecas (subprocess, paramiko, psutil), ejemplos reales

3. **CI/CD con GitHub Actions**
   - Slug: `cicd-github-actions-guia-practica`
   - Tags: `[ci-cd, github-actions, devops, automatizacion]`
   - Contenido: workflows básicos, despliegue automatizado, secrets, matrices

### Monitorización (3 artículos)

1. **Introducción a la observabilidad**
   - Slug: `introduccion-observabilidad-metricas-logs-trazas`
   - Tags: `[observabilidad, metricas, logs, trazas, monitoring]`
   - Contenido: los tres pilares, por qué importa, herramientas del ecosistema

2. **Alertas inteligentes con Alertmanager**
   - Slug: `alertas-inteligentes-alertmanager-prometheus`
   - Tags: `[alertmanager, prometheus, alertas, monitoring]`
   - Contenido: configuración, routing, silencing, evitar fatiga de alertas

3. **Monitorizar servicios con Uptime Kuma**
   - Slug: `uptime-kuma-monitorizar-servicios-web`
   - Tags: `[uptime-kuma, monitoring, self-hosting, disponibilidad]`
   - Contenido: instalación, configurar checks, notificaciones, dashboard

## No se necesitan cambios en

- Rutas (`/categorias/[category].astro`) — generación dinámica automática
- Componentes (ArticleCard, HeroSlider, etc.) — usan categoría del frontmatter
- Navegación (`navigation.ts`) — enlace genérico a `/categorias`
- Layouts — sin cambios
- Estilos CSS — sin cambios
