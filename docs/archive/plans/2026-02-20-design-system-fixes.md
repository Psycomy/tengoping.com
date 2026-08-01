# Design System Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Corregir tres inconsistencias del design system: placeholder SVG fuera de estilo, color `#10b981` hardcoded en botón de copiar, y truncado de texto por JS reemplazado por CSS `line-clamp`.

**Architecture:** Cambios independientes en 4 archivos. Sin nueva lógica JS. Sin nuevas dependencias. Las verificaciones son `npm run lint && npm run format:check && npm run build` (no hay test suite).

**Tech Stack:** Astro 5, vanilla JS, CSS custom properties, SVG con `<style>` interno.

---

### Task 1: Reescribir placeholder-article.svg

**Files:**

- Modify: `public/images/placeholder-article.svg` (reescritura completa)

**Context:**
El SVG actual usa colores hardcoded fuera de la paleta (`#2d2d3f`, `#6c63ff`), tiene `rx="10"` (esquinas redondeadas — el diseño exige `border-radius: 0`), y `font-family="Arial"`. Los SVG servidos como `<img>` no acceden a las CSS vars del documento, pero sí pueden usar `@media (prefers-color-scheme: dark)` internamente.

**Step 1: Verificar el problema visualmente**

Abrir `http://localhost:4321` en modo claro. Las tarjetas sin imagen deben mostrar un fondo oscuro `#2d2d3f` completamente fuera de lugar. Confirmar que es el SVG.

**Step 2: Reemplazar el contenido del archivo**

Escribir exactamente:

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

**Step 3: Verificar**

```bash
npm run build
```

Expected: build exits 0. Revisar visualmente en `npm run preview` que artículos sin imagen muestran el nuevo placeholder.

**Step 4: Commit**

```bash
git add public/images/placeholder-article.svg
git commit -m "fix(design): reescribir placeholder SVG con estética terminal y soporte dark mode"
```

---

### Task 2: Registrar `--color-success` en el design system

**Files:**

- Modify: `src/styles/global.css`

**Context:**
`.copy-button.copied` tiene `background: #10b981` y `border-color: #10b981` hardcoded (líneas ~423-427). Ninguna variable CSS de "éxito" existe. El verde `#10b981` funciona bien semánticamente (señal de éxito clara), pero debe estar en el design system.

**Step 1: Añadir la variable a `:root`**

En `src/styles/global.css`, buscar el bloque `:root { ... }`. Al final del bloque, antes del `}` de cierre, añadir:

```css
--color-success: #10b981;
```

**Step 2: Añadir override para dark mode**

En el bloque `[data-theme='dark'] { ... }`, al final antes del `}` de cierre, añadir:

```css
--color-success: #3dba7a;
```

**Step 3: Usar la variable en `.copy-button.copied`**

Localizar (aproximadamente línea 423):

```css
.copy-button.copied {
  background: #10b981;
  color: var(--color-bg);
  border-color: #10b981;
}
```

Reemplazar por:

```css
.copy-button.copied {
  background: var(--color-success);
  color: var(--color-bg);
  border-color: var(--color-success);
}
```

**Step 4: Verificar**

```bash
npm run lint && npm run format:check
```

Expected: 0 errors, all files match Prettier.

**Step 5: Commit**

```bash
git add src/styles/global.css
git commit -m "refactor(design): formalizar color de éxito como --color-success en design system"
```

---

### Task 3: Sustituir truncado JS por CSS `line-clamp`

**Files:**

- Modify: `src/components/ArticleCard.astro`
- Modify: `src/components/HeroSlider.astro`

**Context:**
Dos componentes truncan descripciones por JS:

- `ArticleCard.astro:63` — `description.slice(0, 120) + '...'`
- `HeroSlider.astro:61-63` — `description.slice(0, 140) + '...'`

Ambos cortan entre caracteres (pueden partir palabras), y el texto truncado no queda en el DOM (Pagefind no lo indexa). CSS `-webkit-line-clamp` es soporte universal desde 2020, corta en límite de línea y el texto completo está en el DOM.

**Step 1: Corregir `ArticleCard.astro` — template**

Localizar línea ~63:

```astro
{description.length > 120 ? description.slice(0, 120) + '...' : description}
```

Reemplazar por:

```astro
{description}
```

**Step 2: Corregir `ArticleCard.astro` — CSS**

En el `<style>` del componente, localizar `.card-description`:

```css
.card-description {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.6;
  color: var(--color-text-secondary);
}
```

Reemplazar por:

```css
.card-description {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.6;
  color: var(--color-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

**Step 3: Corregir `HeroSlider.astro` — template**

Localizar líneas ~61-63:

```astro
{
  post.data.description.length > 140
    ? post.data.description.slice(0, 140) + '...'
    : post.data.description
}
```

Reemplazar por:

```astro
{post.data.description}
```

**Step 4: Corregir `HeroSlider.astro` — CSS desktop**

En el `<style>` del componente, localizar `.slide-description` (bloque sin media query):

```css
.slide-description {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}
```

Reemplazar por:

```css
.slide-description {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

Nota: el `@media (max-width: 768px)` ya tiene `line-clamp: 2` — no tocarlo, sirve como override mobile.

**Step 5: Verificar**

```bash
npm run lint && npm run format:check && npm run build
```

Expected: build exits 0, 0 lint errors, formatting OK. En preview, las descripciones largas deben cortarse visualmente al final de la 3ª línea con `…` nativo.

**Step 6: Commit**

```bash
git add src/components/ArticleCard.astro src/components/HeroSlider.astro
git commit -m "refactor(ux): reemplazar truncado JS por CSS line-clamp en ArticleCard y HeroSlider"
```
