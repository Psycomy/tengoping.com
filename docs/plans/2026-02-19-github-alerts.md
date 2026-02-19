# GitHub Alerts Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar callouts estilo GitHub Alerts (`> [!NOTE]`, etc.) en artículos del blog
mediante un plugin remark local sin dependencias externas.

**Architecture:** Un archivo `src/plugins/remark-github-alerts.mjs` recorre el AST de Markdown,
detecta blockquotes con marcador `[!TIPO]`, elimina el marcador, inserta un nodo título con
clase `callout-title`, y añade clases `callout callout-{tipo}` al blockquote. Los estilos
viven en `global.css` bajo `.prose`.

**Tech Stack:** Astro 5, remark (AST de Markdown), vanilla CSS, ESLint + Prettier (lint-staged).

---

### Task 1: Crear el plugin remark local

**Files:**

- Create: `src/plugins/remark-github-alerts.mjs`

**Contexto del AST remark:**

Dado este Markdown:

```markdown
> [!NOTE]
> Esto es una nota.
```

remark genera:

```json
{
  "type": "blockquote",
  "children": [
    {
      "type": "paragraph",
      "children": [{ "type": "text", "value": "[!NOTE]\nEsto es una nota." }]
    }
  ]
}
```

Sin blank line entre `[!NOTE]` y el texto, están en el mismo nodo párrafo/texto.
Con blank line, son dos párrafos separados (el primero contiene solo `[!NOTE]`).
El plugin debe manejar ambos casos.

**Step 1: Crear el archivo**

```javascript
// src/plugins/remark-github-alerts.mjs

/** @typedef {import('mdast').Root} Root */

const ALERT_TYPES = {
  NOTE: 'Nota',
  TIP: 'Consejo',
  IMPORTANT: 'Importante',
  WARNING: 'Advertencia',
  CAUTION: 'Peligro',
};

const ALERT_RE = /^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\n?/;

/**
 * Recorre el árbol mdast buscando blockquotes con marcador [!TIPO].
 * @param {Root} tree
 */
function walk(tree) {
  if (tree.children) {
    for (const child of tree.children) {
      if (child.type === 'blockquote') {
        transformAlert(child);
      } else {
        walk(child);
      }
    }
  }
}

/**
 * Transforma un nodo blockquote si comienza con [!TIPO].
 */
function transformAlert(node) {
  const firstChild = node.children[0];
  if (!firstChild || firstChild.type !== 'paragraph') return;

  const firstInline = firstChild.children[0];
  if (!firstInline || firstInline.type !== 'text') return;

  const match = firstInline.value.match(ALERT_RE);
  if (!match) return;

  const type = match[1].toLowerCase();
  const title = ALERT_TYPES[match[1]];

  // Eliminar el marcador [!TIPO] del texto
  firstInline.value = firstInline.value.slice(match[0].length);

  // Si el primer párrafo quedó vacío, eliminarlo
  if (firstChild.children.length === 1 && firstInline.value.trim() === '') {
    node.children.shift();
  }

  // Insertar párrafo de título al inicio
  node.children.unshift({
    type: 'paragraph',
    children: [{ type: 'text', value: `## ${title}` }],
    data: {
      hProperties: { className: ['callout-title'] },
    },
  });

  // Añadir clases al blockquote
  if (!node.data) node.data = {};
  if (!node.data.hProperties) node.data.hProperties = {};
  node.data.hProperties.className = ['callout', `callout-${type}`];
}

/** @returns {(tree: Root) => void} */
export default function remarkGithubAlerts() {
  return (tree) => walk(tree);
}
```

**Step 2: Verificar que el archivo no tiene errores de lint**

```bash
npx eslint src/plugins/remark-github-alerts.mjs
```

Esperado: 0 errores, 0 warnings.

**Step 3: Commit**

```bash
git add src/plugins/remark-github-alerts.mjs
git commit -m "feat: plugin remark local para GitHub Alerts"
```

---

### Task 2: Registrar el plugin en astro.config.mjs

**Files:**

- Modify: `astro.config.mjs`

**Step 1: Añadir el import y registrar el plugin**

Cambiar `astro.config.mjs` de:

```javascript
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import pagefind from 'astro-pagefind';

export default defineConfig({
  site: 'https://tengoping.com',
  integrations: [mdx(), sitemap(), pagefind()],
  markdown: {
    shikiConfig: { ... },
  },
});
```

A:

```javascript
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import pagefind from 'astro-pagefind';
import remarkGithubAlerts from './src/plugins/remark-github-alerts.mjs';

export default defineConfig({
  site: 'https://tengoping.com',
  integrations: [mdx(), sitemap(), pagefind()],
  markdown: {
    remarkPlugins: [remarkGithubAlerts],
    shikiConfig: { ... },
  },
});
```

**Step 2: Verificar lint**

```bash
npx eslint astro.config.mjs
```

Esperado: 0 errores.

**Step 3: Verificar que el build no falla**

```bash
npm run build 2>&1 | tail -5
```

Esperado: `dist/` generado sin errores.

**Step 4: Commit**

```bash
git add astro.config.mjs
git commit -m "feat: registrar plugin remarkGithubAlerts en astro.config"
```

---

### Task 3: Añadir estilos CSS para los callouts

**Files:**

- Modify: `src/styles/global.css`

**Contexto:** Los estilos deben ir dentro del bloque `.prose` (las clases son generadas
dentro del contenido de artículos). El blockquote base ya existe en `.prose blockquote`.

**Step 1: Añadir los estilos al final del bloque `.prose` en global.css**

Buscar el bloque `.prose blockquote { ... }` (línea ~225) y añadir después:

```css
/* --- GitHub Alerts / Callouts --- */

.prose blockquote.callout {
  font-style: normal;
  color: inherit;
  border-left-width: 4px;
}

.prose blockquote.callout .callout-title {
  font-weight: 700;
  margin-bottom: 0.5rem;
  font-style: normal;
}

/* NOTE — verde terminal */
.prose blockquote.callout-note {
  border-left-color: #58d5a2;
  background: #58d5a21a;
}

.prose blockquote.callout-note .callout-title {
  color: #58d5a2;
}

/* TIP — azul eléctrico */
.prose blockquote.callout-tip {
  border-left-color: #00bfff;
  background: #00bfff1a;
}

.prose blockquote.callout-tip .callout-title {
  color: #00bfff;
}

/* IMPORTANT — púrpura */
.prose blockquote.callout-important {
  border-left-color: #a78bfa;
  background: #a78bfa1a;
}

.prose blockquote.callout-important .callout-title {
  color: #a78bfa;
}

/* WARNING — ámbar */
.prose blockquote.callout-warning {
  border-left-color: #f59e0b;
  background: #f59e0b1a;
}

.prose blockquote.callout-warning .callout-title {
  color: #f59e0b;
}

/* CAUTION — rojo */
.prose blockquote.callout-caution {
  border-left-color: #ef4444;
  background: #ef44441a;
}

.prose blockquote.callout-caution .callout-title {
  color: #ef4444;
}
```

**Step 2: Verificar formato**

```bash
npx prettier --check src/styles/global.css
```

Si hay diferencias: `npx prettier --write src/styles/global.css`

**Step 3: Commit**

```bash
git add src/styles/global.css
git commit -m "feat: estilos CSS para GitHub Alerts callouts"
```

---

### Task 4: Verificación manual end-to-end

**Files:**

- Create (temporal): `src/content/blog/_test-alerts.md`

**Step 1: Crear post de prueba**

```markdown
---
title: 'Test: GitHub Alerts'
description: 'Verificación visual de callouts'
author: antonio
pubDate: 2026-02-19
category: 'Seguridad'
tags: ['test']
draft: true
---

Blockquote normal (no debe cambiar):

> Esto es un blockquote normal sin tipo.

Callout NOTE (sin blank line):

> [!NOTE]
> Esto es una nota informativa.

Callout TIP (sin blank line):

> [!TIP]
> Un consejo útil para el lector.

Callout IMPORTANT:

> [!IMPORTANT]
> Información clave que no debe ignorarse.

Callout WARNING:

> [!WARNING]
> Precaución antes de continuar.

Callout CAUTION:

> [!CAUTION]
> Esto puede causar daños irreversibles.

Callout con blank line (dos párrafos en el mismo blockquote):

> [!NOTE]
>
> Nota con blank line entre marcador y contenido.
```

**Step 2: Build y preview**

```bash
npm run build && npm run preview
```

Abrir `http://localhost:4321/blog/_test-alerts` y verificar:

- Blockquote normal → mismo estilo de siempre (borde azul, fondo gris, italic)
- NOTE → borde y título verdes (`#58D5A2`), fondo verde tenue, título `## Nota`
- TIP → borde y título azul eléctrico, título `## Consejo`
- IMPORTANT → borde y título púrpura, título `## Importante`
- WARNING → borde y título ámbar, título `## Advertencia`
- CAUTION → borde y título rojo, título `## Peligro`
- El marcador `[!TIPO]` no aparece en el contenido visible
- Callout con blank line → mismo resultado que sin blank line

**Step 3: Verificar que el HTML generado es correcto**

```bash
grep -A5 'callout-note' dist/blog/_test-alerts/index.html | head -20
```

Esperado: `<blockquote class="callout callout-note">` con `<p class="callout-title">`.

**Step 4: Eliminar el post de prueba**

```bash
rm src/content/blog/_test-alerts.md
```

**Step 5: Suite completa de checks**

```bash
npm run lint && npx astro check && npm run build
```

Esperado: 0 errores en lint, 0 errores en astro check, build exitoso.

**Step 6: Commit final**

```bash
git add -A
git commit -m "feat: GitHub Alerts — verificación end-to-end OK"
```

---

## Checklist final

- [ ] `src/plugins/remark-github-alerts.mjs` creado
- [ ] Plugin registrado en `astro.config.mjs`
- [ ] Estilos añadidos en `global.css`
- [ ] Los 5 tipos renderizan correctamente (color, título en español)
- [ ] Blockquotes normales no se ven afectados
- [ ] `npm run lint` → 0 errores
- [ ] `astro check` → 0 errores
- [ ] `npm run build` → OK
