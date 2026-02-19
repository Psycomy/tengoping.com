# Diseño — Mejoras UX en artículos (alta prioridad)

> Fecha: 2026-02-19
> Estado: Aprobado

## Objetivo

Añadir dos mejoras de experiencia de lectura a los artículos del blog:

1. **Anclas en headings** — enlace `[#]` al hacer hover sobre `h2`/`h3`/`h4` que copia la URL con fragmento
2. **Progreso en la pestaña** — `document.title` muestra `[42%] Título del artículo` mientras se lee

## Enfoque elegido: JS dinámico (patrón CopyCodeButton)

Consistente con los patrones existentes del blog. Sin plugins de build nuevos.

---

## Feature 1: HeadingAnchors

### Archivo

`src/components/HeadingAnchors.astro` (nuevo)

### Comportamiento

- El JS busca todos los `h2, h3, h4` dentro de `.prose` que tengan atributo `id`
  (los IDs los genera `rehype-slug` automáticamente durante el build de Astro)
- Para cada heading, inserta al final un `<a class="heading-anchor" href="#{id}">[#]</a>`
- Al clicar: copia `window.location.href` con el fragmento al portapapeles
- Feedback: el texto cambia a `[✓]` durante 1.5s, luego restaura `[#]`
- Sigue el patrón `astro:after-swap` para navegación SPA

### Estética

- `[#]` en `var(--color-primary)`, font mono, `text-decoration: none`
- Invisible por defecto (`opacity: 0`), visible al hover en el heading padre
- Sin `border-radius`, sin sombras — convención terminal

### Integración

Se añade en `ArticleLayout.astro` junto a `<CopyCodeButton />` y `<ReadingProgress />`.

---

## Feature 2: Progreso en la pestaña

### Archivo

`src/components/ReadingProgress.astro` (modificación)

### Comportamiento

- En `init()`, leer `document.title` como `originalTitle`
- En el scroll handler, si `progress > 2`: `document.title = \`[${Math.round(progress)}%] ${originalTitle}\``
- Si `progress <= 2`: restaurar `originalTitle` (inicio del artículo)
- Si `progress >= 98`: restaurar `originalTitle` (final del artículo)
- Al cambiar de página (`astro:after-swap`), `init()` ya se re-ejecuta y lee el nuevo título

### Notas

- El umbral de 2% evita parpadeo al cargar la página
- El umbral de 98% restaura el título cuando el lector llega al final
- Cambio mínimo: ~6 líneas en el scroll handler existente
