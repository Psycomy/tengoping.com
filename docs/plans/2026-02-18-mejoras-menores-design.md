# Mejoras Menores — offline.html + Breadcrumbs Design

**Date:** 2026-02-18

## offline.html

Mover los botones de acción al interior de `.terminal-body` para que la ventana terminal sea autocontenida. Los botones externos (`.actions` div) desaparecen.

**Estructura nueva de `.terminal-body`:**

- Líneas existentes (ping, echo, output) — sin cambios
- Nueva línea: `$ [reintentar]` → `<button>` con `onclick="location.reload()"`
- Nueva línea: `$ [volver_al_inicio]` → `<a href="/">`
- Línea final: `$ _` (cursor parpadeante) — se mantiene

**Estilos:**

- `.terminal-cmd`: sin border ni background, color `#58d5a2`, cursor pointer, font heredado
- Eliminar bloque CSS `.actions` y `.terminal-btn`
- El hover invierte colores: fondo `#58d5a2`, texto `#0d1117`

## Breadcrumbs

Simplificar `src/components/Breadcrumbs.astro` eliminando el patrón `${site.url}/ruta` + `new URL(item.url).pathname`.

**Cambio en `breadcrumbItems`:** usar rutas relativas directamente (`/`, `/blog`, `/categorias/${categorySlug}`, `Astro.url.pathname`).

**JSON-LD:** construir una lista separada `jsonLdItems` que sí usa `site.url` completo (requerido por schema.org).

**Template:** `href={item.url}` directamente, sin `new URL()`.
