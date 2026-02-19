# Diseño: Correcciones del Design System — tengoping.com

**Fecha:** 2026-02-20
**Aprobado por:** usuario ("todas")

---

## Contexto

Tres inconsistencias identificadas en el diseño del blog tras análisis del código:
dos colores hardcoded fuera del design system, un SVG placeholder que viola las
convenciones visuales del blog, y truncado de texto por JS cuando CSS `line-clamp`
es más robusto y beneficia el indexado de Pagefind.

---

## Mejora 1 — Placeholder SVG (Visual / Design System)

**Archivo:** `public/images/placeholder-article.svg`

**Problema:**

- `fill="#2d2d3f"` — fondo oscuro fijo, no funciona en modo claro
- `rx="10"` — esquinas redondeadas, viola `border-radius: 0` del diseño
- `fill="#6c63ff"` — color fuera de la paleta
- `font-family="Arial"` — no JetBrains Mono

**Diseño:**
SVG con `<style>` interno y `@media (prefers-color-scheme: dark)`. Responde al tema
del OS (suficiente para un elemento estático). Sin `rx`, sin colores fuera de paleta.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400">
  <style>
    .bg     { fill: #f4f6f9; }
    .border { fill: none; stroke: #d1d9e6; stroke-width: 1; }
    .prompt { fill: #1a73e8; }
    .dim    { fill: #8b949e; }
    @media (prefers-color-scheme: dark) {
      .bg     { fill: #161b22; }
      .border { stroke: #30363d; }
      .prompt { fill: #58d5a2; }
    }
  </style>
  <rect class="bg" width="800" height="400"/>
  <rect class="border" x="280" y="130" width="240" height="140"/>
  <text x="300" y="175" font-family="JetBrains Mono, monospace" font-size="15" class="prompt">$ cat ./imagen</text>
  <text x="300" y="210" font-family="JetBrains Mono, monospace" font-size="13" class="dim">No such file</text>
  <text x="300" y="245" font-family="JetBrains Mono, monospace" font-size="13" class="dim">or directory</text>
</svg>
```

---

## Mejora 2 — `--color-success` en design system

**Archivo:** `src/styles/global.css`

**Problema:**
`.copy-button.copied` usa `background: #10b981` y `border-color: #10b981` hardcoded.
No existe ninguna variable CSS de "éxito" en el sistema.

**Diseño:**
Añadir `--color-success` a `:root` y `[data-theme='dark']`, luego usarla:

```css
/* :root */
--color-success: #10b981;

/* [data-theme='dark'] */
--color-success: #3dba7a;

/* .copy-button.copied */
.copy-button.copied {
  background: var(--color-success);
  color: var(--color-bg);
  border-color: var(--color-success);
}
```

---

## Mejora 3 — CSS `line-clamp` en lugar de truncado JS

**Archivos:** `src/components/ArticleCard.astro`, `src/components/HeroSlider.astro`

**Problema:**

- `description.slice(0, 120) + '...'` en ArticleCard corta entre caracteres
- `description.slice(0, 140) + '...'` en HeroSlider (desktop) hace lo mismo
- El texto truncado no queda en el DOM → Pagefind no lo indexa
- HeroSlider mobile ya usa `-webkit-line-clamp: 2`, desktop usa JS: inconsistencia

**Diseño:**

`ArticleCard.astro`: eliminar expresión ternaria, pasar `{description}` completo.
Añadir al CSS de `.card-description`:

```css
display: -webkit-box;
-webkit-line-clamp: 3;
-webkit-box-orient: vertical;
overflow: hidden;
```

`HeroSlider.astro`: eliminar expresión ternaria, pasar `{post.data.description}` completo.
Añadir al CSS de `.slide-description` (bloque de escritorio):

```css
display: -webkit-box;
-webkit-line-clamp: 3;
-webkit-box-orient: vertical;
overflow: hidden;
```

El `@media (max-width: 768px)` ya sobreescribe con `line-clamp: 2` — queda como override.

---

## Archivos modificados

| Archivo                                 | Cambio                             |
| --------------------------------------- | ---------------------------------- |
| `public/images/placeholder-article.svg` | Reescritura completa               |
| `src/styles/global.css`                 | +2 vars CSS + 2 líneas modificadas |
| `src/components/ArticleCard.astro`      | Eliminar ternario + añadir CSS     |
| `src/components/HeroSlider.astro`       | Eliminar ternario + añadir CSS     |
