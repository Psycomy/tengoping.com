# Diseño: Mejora de la página de etiquetas

**Fecha:** 2026-02-20
**Estado:** Aprobado

## Problema

La página `/etiquetas` (índice de tags) tiene dos fallos de experiencia:

1. **Difícil de escanear** — la nube de tags con tamaños de fuente variables (0.8rem–1.4rem) crea ruido visual; no hay agrupación ni estructura clara.
2. **Diseño poco trabajado** — contrasta negativamente con la página de categorías, que tiene tarjetas estructuradas con icono, descripción y badges.

## Solución elegida: Grid por popularidad (3 niveles)

Reemplazar la nube de tags por 3 secciones visuales claras basadas en popularidad, con tarjetas uniformes.

## Diseño

### Sección 1: Estructura y datos

Las 3 secciones se calculan dinámicamente con percentiles sobre el array de counts:

- **Populares**: tags en el percentil ≥ 66 (los más escritos)
- **Frecuentes**: tags entre percentil 33 y 66
- **Ocasionales**: tags en el percentil < 33

Los umbrales son dinámicos: se recalculan en build time, escalan solos si el blog crece.

Cada sección tiene encabezado estilo terminal con pseudo-elemento `##` (igual que headings del blog).

Meta-prompt de la página: `$ ls -la /etiquetas/ | sort -rn`

### Sección 2: Visual de tarjetas

Cada tag es una tarjeta rectangular (`border-radius: 0`):

- Nombre en `text-transform: uppercase`
- Badge contador `[n]` alineado a la derecha
- **Borde izquierdo 3px** con color según nivel:
  - Populares → `#58D5A2` (verde terminal)
  - Frecuentes → `#00BFFF` (azul eléctrico)
  - Ocasionales → `var(--color-border)` (muted)
- Hover: fondo sutil (`color + 0A` opacidad) + borde completo del color del nivel

Layout: `grid` con `repeat(auto-fill, minmax(160px, 1fr))`, gap `0.75rem`. Responsive sin media queries explícitas.

### Sección 3: Página individual `/etiquetas/[tag]`

Mejoras menores de consistencia:

1. **Meta-prompt terminal** en el encabezado: `$ grep -r "tag" /blog/`
2. **Enlace de vuelta** `← Todas las etiquetas` debajo del título

Sin paginación (tags individuales raramente superan 10 artículos). Sin tags relacionadas (YAGNI).

## Archivos a modificar

- `src/pages/etiquetas/index.astro` — rediseño completo
- `src/pages/etiquetas/[tag].astro` — mejoras menores de encabezado y navegación
