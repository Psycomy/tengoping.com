# Performance — Plan de Implementación

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reducir 185KB de transferencia de fuentes en primera visita y eliminar el espacio vacío durante la carga lazy de imágenes en ArticleCard.

**Architecture:** Task 1 elimina 2 de los 4 pesos de JetBrains Mono (Medium 500, SemiBold 600) modificando `global.css` y `BaseLayout.astro`. Task 2 añade un color de fondo como skeleton en `ArticleCard.astro`. Cada task es independiente.

**Tech Stack:** Astro 5, CSS `@font-face`, woff2

**Nota previa al implementador:** Dos items del análisis original son falsos positivos ya resueltos:

- `prefers-reduced-motion` → **ya implementado** en `HeroSlider.astro`: CSS line 264 detiene la transición y JS line 315 comprueba `matchMedia('(prefers-reduced-motion: reduce)')` antes de llamar `startAutoplay()`.
- `sizes="100vw"` → **correcto** para un hero full-bleed sin max-width.

El item "Critical CSS inline" fue descartado: `global.css` pesa solo 3KB gzip; Astro no permite hacer el `<link rel="stylesheet">` no-blocking sin workarounds frágiles; la ganancia real en una CDN de Cloudflare sería <25ms. No vale la complejidad.

---

## Task 1: Eliminar pesos de fuente Medium (500) y SemiBold (600)

Las fuentes `JetBrainsMono-Medium.woff2` (92KB) y `JetBrainsMono-SemiBold.woff2` (93KB) se precargan y descargan en cada primera visita. Eliminándolas se ahorran **185KB** por visitante nuevo. Sin estas fuentes definidas en `@font-face`, el navegador aplica la regla estándar de fallback CSS:

- `font-weight: 500` → usa `400` (Regular) — impacto visual sutil (texto ligeramente más fino)
- `font-weight: 600` → usa `700` (Bold) — badges, TOC items y headings secundarios aparecen en Bold

Para un diseño terminal (monocromo, fuerte contraste) este fallback es aceptable y puede incluso mejorar la jerarquía visual.

**Files:**

- Modify: `src/styles/global.css:9-22` (eliminar los dos `@font-face` intermedios)
- Modify: `src/layouts/BaseLayout.astro:98-118` (eliminar los dos `<link rel="preload">` de esas fuentes)

**Step 1: Verificar el estado actual**

```bash
grep -n "woff2\|font-weight" src/styles/global.css | head -30
grep -n "preload.*woff2" src/layouts/BaseLayout.astro
```

Expected: ver 4 bloques `@font-face` (400, 500, 600, 700) y 4 `<link rel="preload">` en BaseLayout.

**Step 2: Eliminar los `@font-face` de Medium y SemiBold de `global.css`**

En `src/styles/global.css`, localizar y eliminar los dos bloques `@font-face` para `font-weight: 500` y `font-weight: 600` (aproximadamente líneas 9-22):

Pasar de:

```css
@font-face {
  font-family: 'JetBrains Mono';
  src: url('/fonts/JetBrainsMono-Regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'JetBrains Mono';
  src: url('/fonts/JetBrainsMono-Medium.woff2') format('woff2');
  font-weight: 500;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'JetBrains Mono';
  src: url('/fonts/JetBrainsMono-SemiBold.woff2') format('woff2');
  font-weight: 600;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'JetBrains Mono';
  src: url('/fonts/JetBrainsMono-Bold.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
```

A:

```css
@font-face {
  font-family: 'JetBrains Mono';
  src: url('/fonts/JetBrainsMono-Regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: 'JetBrains Mono';
  src: url('/fonts/JetBrainsMono-Bold.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
```

**Step 3: Eliminar los `<link rel="preload">` de Medium y SemiBold en `BaseLayout.astro`**

En `src/layouts/BaseLayout.astro`, localizar el bloque de preloads de fuentes (aproximadamente líneas 91-118) y eliminar los dos `<link rel="preload">` correspondientes a Medium y SemiBold. Pasar de 4 preloads a 2:

```astro
<!-- Fonts (self-hosted) -->
<link
  rel="preload"
  href="/fonts/JetBrainsMono-Regular.woff2"
  as="font"
  type="font/woff2"
  crossorigin
/>
<link
  rel="preload"
  href="/fonts/JetBrainsMono-Bold.woff2"
  as="font"
  type="font/woff2"
  crossorigin
/>
```

**Step 4: Verificar lint y build**

```bash
cd /home/antonio/Documentos/blog && npm run lint && npm run build 2>&1 | tail -5
```

Expected: 0 errores de lint, build sin errores.

**Step 5: Verificar en el HTML generado**

```bash
grep -c "preload.*woff2" dist/index.html
grep "preload.*woff2" dist/index.html
```

Expected: 2 líneas (Regular y Bold), sin Medium ni SemiBold.

**Step 6: Verificar visualmente (opcional)**

```bash
npm run preview
```

Abrir `http://localhost:4321` y revisar visualmente:

- Badges (`./blog`, categorías, tags): aparecen en Bold (700) en lugar de SemiBold (600) — más grueso, aceptable
- Nombres de autor en ArticleCard: aparecen en Regular (400) en lugar de Medium (500) — ligeramente más fino, apenas perceptible
- Si algún elemento se ve mal, es señal de que ese peso era importante — en ese caso, considerar restaurar solo ese `@font-face`

**Step 7: Commit**

```bash
git add src/styles/global.css src/layouts/BaseLayout.astro
git commit -m "perf: eliminar fuentes Medium/SemiBold — ahorro de 185KB por primera visita"
```

---

## Task 2: Skeleton/placeholder en ArticleCard durante carga lazy

Cuando una tarjeta de artículo tiene imagen lazy, el área de imagen (300×200px en desktop, 16/9 en móvil) aparece completamente vacía hasta que la imagen carga. Añadir `background-color` como skeleton evita el parpadeo de espacio vacío.

**Files:**

- Modify: `src/components/ArticleCard.astro:113-118` (CSS de `.card-image-link`)

**Step 1: Verificar el estado actual**

```bash
grep -n "card-image-link\|background\|skeleton" src/components/ArticleCard.astro
```

Expected: ver `.card-image-link` sin `background`.

**Step 2: Añadir `background` al `.card-image-link`**

En `src/components/ArticleCard.astro`, localizar la regla `.card-image-link` en el `<style>` (aproximadamente línea 113):

```css
.card-image-link {
  display: block;
  overflow: hidden;
  flex: 0 0 300px;
  min-height: 200px;
}
```

Añadir `background: var(--color-bg-secondary)` como color de skeleton:

```css
.card-image-link {
  display: block;
  overflow: hidden;
  flex: 0 0 300px;
  min-height: 200px;
  background: var(--color-bg-secondary);
}
```

Nota: `--color-bg-secondary` es `#e8ecf1` en light mode y `#161b22` en dark mode — un gris suave que actúa de placeholder mientras la imagen lazy se descarga.

**Step 3: Verificar lint y build**

```bash
cd /home/antonio/Documentos/blog && npm run lint && npm run build 2>&1 | tail -5
```

Expected: 0 errores, build sin errores.

**Step 4: Commit**

```bash
git add src/components/ArticleCard.astro
git commit -m "perf: añadir skeleton background en ArticleCard durante carga lazy de imagen"
```

---

## Verificación Final

```bash
# Build completo
npm run build

# Verificar preloads (deben ser solo 2)
grep "preload.*woff2" dist/index.html | wc -l

# Verificar que Medium/SemiBold no aparecen en el HTML
grep -i "medium\|semibold" dist/index.html

# Lint
npm run lint
```

Expected:

- 2 preloads de fuente (Regular + Bold)
- Sin referencias a Medium/SemiBold en el HTML generado
- Lint 0 errores
