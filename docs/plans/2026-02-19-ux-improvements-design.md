# Diseño: Mejoras UX — tengoping.com

**Fecha:** 2026-02-19
**Enfoque elegido:** B — Mejoras completas y priorizadas
**Auto-implementar:** ítems fáciles (1–7, 10)
**Solo propuesta de código:** ítems medios (8, 9, 11, 12)

---

## Contexto

Blog técnico en español para sysadmins. Stack: Astro 5, vanilla JS, diseño terminal (JetBrains Mono, sin border-radius, sin shadows). El blog tiene buena base: TOC con scroll spy, reading progress, search Pagefind, dark mode, PWA, heading anchors. Los problemas identificados son refinamientos y correcciones de accesibilidad, no rediseños.

---

## Mejoras a implementar automáticamente (fáciles)

### 🔴 1. Botón de pausa en HeroSlider (WCAG 2.1 SC 2.2.2)

**Archivo:** `src/components/HeroSlider.astro`

**Problema:** El autoplay de 5s no tiene control visible para pausar. WCAG 2.2.2 es Level A — el incumplimiento es obligatorio corregir.

**Diseño:**

- Botón `[⏸]` posicionado en la esquina superior derecha del slider (encima del contenido, z-index 2).
- Cuando está pausado: muestra `[▶]`.
- HTML terminal: `<button class="slider-pause">[⏸]</button>`.
- En JS: `startAutoplay()` / `stopAutoplay()` ya existen. El botón llama a uno u otro y actualiza su texto.
- No se pausa al hover cuando el usuario ha pulsado el botón (pausa intencional vs. hover temporal).
- Se oculta en `prefers-reduced-motion` (el autoplay ya está desactivado en ese caso).

### 🔴 2. Heading anchors visibles en móvil

**Archivo:** `src/components/HeadingAnchors.astro`

**Problema:** `opacity: 0` + `opacity: 1 on hover` → en touch, nunca visibles.

**Diseño:**

```css
@media (hover: none) {
  :global(.heading-anchor) {
    opacity: 0.4;
  }
}
```

Usa `hover: none` (media query de capacidad, no tamaño) para detectar dispositivos touch sin afectar trackpads ni desktop.

### 🟡 3. Contador de slides en HeroSlider

**Archivo:** `src/components/HeroSlider.astro`

**Problema:** Los dots no comunican cuántos slides hay.

**Diseño:**

- Añadir `<span class="slider-counter" aria-live="polite" aria-atomic="true">[1/5]</span>` junto a los dots.
- Se actualiza en `goTo()`: `counter.textContent = \`[${current + 1}/${total}]\``.
- Posición: junto a la barra de dots en la parte inferior, a la izquierda de los mismos.
- Mismo estilo que los botones de arrow (terminal mono font, border, fondo semi-transparente).

### 🟡 4. "Ver todos →" con estética terminal

**Archivo:** `src/pages/index.astro` (línea 50)

**Problema:** `<a href=...>Ver todos →</a>` no sigue la convención terminal `[brackets]`.

**Diseño:** Cambiar a `[ver todos →]` con la clase CSS de los footer-links, o un span con estilo propio coherente con el header nav (`./categorias`).

### 🟡 5. CTA de RSS en artículos

**Archivo:** `src/layouts/ArticleLayout.astro`

**Problema:** No hay CTA de suscripción RSS al final de los artículos.

**Diseño:**

- Bloque simple entre `<ShareButtons>` y `<AuthorCard>`:

```html
<div class="rss-cta">
  <span class="prompt">$</span> curl tengoping.com/rss.xml | subscribe
  <a href="/rss.xml" ...>[suscribirse por RSS →]</a>
</div>
```

- Estilo: como `.meta-prompt` (color primary, font-size 0.8125rem). Separado por border-bottom como los demás elementos del footer.

### 🟡 6. TOC: indicador de overflow (fade CSS)

**Archivo:** `src/components/TableOfContents.astro`

**Problema:** `.toc-wrapper` tiene `overflow-y: auto` pero sin indicador visual de que hay más contenido abajo.

**Diseño:**

- Wrapper relativo + `::after` pseudo-elemento con gradiente descendente de `var(--color-bg)` a transparente.
- Solo visible cuando `.toc-wrapper` tiene más contenido (CSS puro con `overflow: auto` + `::after` posición sticky-bottom).
- Técnica: `position: sticky; bottom: 0` en el pseudo-elemento dentro de un wrapper.

### 🟡 7. Related articles: tiempo de lectura

**Archivo:** `src/components/RelatedArticles.astro`

**Problema:** Las tarjetas de relacionados solo tienen categoría + título, sin indicación de compromiso de tiempo.

**Diseño:**

- Importar `getReadingTime` (ya disponible en el proyecto).
- Añadir `{getReadingTime(post.body || '')} min` en `.related-content` debajo del h4, con estilo `.card-info` (font-size 0.75rem, color text-muted).

### 🟢 10. Print stylesheet

**Archivo:** `src/styles/global.css`

**Problema:** Al imprimir, header, footer, TOC sidebar, botones de compartir se incluyen.

**Diseño:**

```css
@media print {
  .site-header,
  .site-footer,
  .search-terminal,
  .article-sidebar,
  .share-buttons,
  .reading-progress-bar,
  .back-to-top,
  .article-nav,
  .related-articles {
    display: none !important;
  }
  .article-grid {
    grid-template-columns: 1fr !important;
  }
  a::after {
    content: ' (' attr(href) ')';
    font-size: 0.75em;
  }
}
```

---

## Mejoras propuestas (código, no auto-implementar)

### 🟡 8. Soporte de filename en code blocks

**Archivo:** `src/components/CopyCodeButton.astro`

Añadir extracción de metadato `title` del atributo del elemento `<code>` o de un comentario en primera línea. Requiere convención documentada en CLAUDE.md.

### 🟡 9. Números de línea en código (opt-in)

**Archivo:** `astro.config.mjs` (Shiki transformer)

Transformer que envuelve cada línea en `<span class="line">` y usa CSS `counter-increment` para mostrar números. Opt-in con clase `.code-block--linenos`.

### 🟢 11. Copy en inline code

Wrapper JS de todos los `<code>` que no estén dentro de `<pre>`, con tooltip de copia al hover.

### 🟢 12. Keyboard shortcut legend

Modal `[?]` en el header que lista: `Ctrl+K` buscar, `↑/↓` navegar resultados, `ESC` cerrar, `← →` cambiar slide.

---

## Archivos que se modifican (implementación automática)

| Archivo                                | Cambio                             |
| -------------------------------------- | ---------------------------------- |
| `src/components/HeroSlider.astro`      | Botón pausa + contador slides      |
| `src/components/HeadingAnchors.astro`  | Heading anchors visibles en móvil  |
| `src/components/TableOfContents.astro` | Fade overflow CSS                  |
| `src/components/RelatedArticles.astro` | Añadir tiempo de lectura           |
| `src/layouts/ArticleLayout.astro`      | CTA RSS                            |
| `src/pages/index.astro`                | "Ver todos →" → terminal aesthetic |
| `src/styles/global.css`                | Print stylesheet                   |

**Total: 7 archivos, todos cambios CSS/HTML/JS contenidos, sin cambios de routing ni de contenido.**
