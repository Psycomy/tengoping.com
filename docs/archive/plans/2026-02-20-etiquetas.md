# Etiquetas Page Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reemplazar la nube de tags por un grid de 3 secciones (Populares / Frecuentes / Ocasionales) con tarjetas uniformes y borde izquierdo de color, y añadir encabezado terminal + back-link a la página individual de tag.

**Architecture:** Dos archivos Astro modificados: `index.astro` rediseño completo con percentiles dinámicos calculados en build time, `[tag].astro` mejoras menores de navegación. Sin JS del lado del cliente. Sin dependencias nuevas.

**Tech Stack:** Astro 5, TypeScript (frontmatter), CSS custom properties del proyecto (`--color-border`, `--color-primary`, `--color-text`, etc.). Colores de nivel hardcoded como en HeroSlider y Search.

---

### Task 1: Rediseñar `src/pages/etiquetas/index.astro`

**Files:**

- Modify: `src/pages/etiquetas/index.astro`

**Step 1: Leer el archivo actual**

```bash
# Ya leído en sesión de diseño — confirmar contenido en líneas 1-140
```

**Step 2: Reemplazar el contenido completo del archivo**

Reemplazar `src/pages/etiquetas/index.astro` con:

```astro
---
import BaseLayout from '@layouts/BaseLayout.astro';
import { getCollection } from 'astro:content';
import { getUniqueTags, slugify } from '@utils/helpers';

const posts = await getCollection('blog', ({ data }) => !data.draft);
const tags = getUniqueTags(posts);
const tagCounts = tags
  .map((tag) => ({
    name: tag,
    slug: slugify(tag),
    count: posts.filter((p) => p.data.tags.includes(tag)).length,
  }))
  .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));

// Umbrales dinámicos por percentil (escalan con el crecimiento del blog)
const counts = tagCounts.map((t) => t.count);
const sorted = [...counts].sort((a, b) => a - b);
const p33 = sorted[Math.floor(sorted.length * 0.33)];
const p66 = sorted[Math.floor(sorted.length * 0.66)];

const populares = tagCounts.filter((t) => t.count > p66);
const frecuentes = tagCounts.filter((t) => t.count <= p66 && t.count >= p33);
const ocasionales = tagCounts.filter((t) => t.count < p33);

const sections = [
  { id: 'populares', label: 'Populares', tags: populares, level: 3 },
  { id: 'frecuentes', label: 'Frecuentes', tags: frecuentes, level: 2 },
  { id: 'ocasionales', label: 'Ocasionales', tags: ocasionales, level: 1 },
].filter((s) => s.tags.length > 0);
---

<BaseLayout title="Etiquetas" description="Todas las etiquetas del blog">
  <section class="container page-section">
    <div class="page-header">
      <span class="meta-prompt">$ ls -la /etiquetas/ | sort -rn</span>
      <h1>Etiquetas</h1>
      <p class="subtitle">{tagCounts.length} etiquetas en {posts.length} artículos</p>
    </div>

    {
      sections.map((section) => (
        <div class="tags-section" id={section.id}>
          <h2 class={`section-title level-${section.level}`}>{section.label}</h2>
          <div class="tags-grid">
            {section.tags.map((tag) => (
              <a href={`/etiquetas/${tag.slug}`} class={`tag-card level-${section.level}`}>
                <span class="tag-name">{tag.name}</span>
                <span class="tag-count">[{tag.count}]</span>
              </a>
            ))}
          </div>
        </div>
      ))
    }
  </section>
</BaseLayout>

<style>
  .page-section {
    padding: 3rem 0 4rem;
  }

  .page-header {
    text-align: center;
    margin-bottom: 3rem;
  }

  .meta-prompt {
    display: block;
    color: var(--color-primary);
    font-size: 0.8125rem;
    margin-bottom: 0.5rem;
  }

  .page-header h1 {
    margin-bottom: 0.5rem;
  }

  .subtitle {
    color: var(--color-text-muted);
    font-size: 0.875rem;
  }

  /* Secciones */
  .tags-section {
    margin-bottom: 2.5rem;
  }

  .section-title {
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--color-border);
  }

  .section-title::before {
    content: '## ';
    color: var(--color-text-muted);
    font-weight: 400;
  }

  .section-title.level-3::after {
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #58d5a2;
    margin-left: 0.5rem;
    vertical-align: middle;
  }

  .section-title.level-2::after {
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #00bfff;
    margin-left: 0.5rem;
    vertical-align: middle;
  }

  /* Grid de tarjetas */
  .tags-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 0.75rem;
  }

  /* Tarjeta de tag */
  .tag-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    padding: 0.6rem 0.875rem;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-left-width: 3px;
    text-decoration: none;
    transition:
      background-color 0.2s,
      border-color 0.2s;
  }

  .tag-card.level-3 {
    border-left-color: #58d5a2;
  }

  .tag-card.level-2 {
    border-left-color: #00bfff;
  }

  .tag-card.level-1 {
    border-left-color: var(--color-border);
  }

  .tag-card:hover {
    background-color: color-mix(in srgb, var(--color-primary) 6%, transparent);
    border-color: var(--color-primary);
    border-left-color: var(--color-primary);
  }

  .tag-name {
    font-size: 0.8125rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--color-text);
    transition: color 0.2s;
  }

  .tag-card:hover .tag-name {
    color: var(--color-primary);
  }

  .tag-count {
    font-size: 0.75rem;
    color: var(--color-text-muted);
    white-space: nowrap;
    transition: color 0.2s;
  }

  .tag-card:hover .tag-count {
    color: var(--color-primary);
  }
</style>
```

**Step 3: Verificar build sin errores**

```bash
npm run build 2>&1 | tail -20
```

Esperado: build exitoso, sin errores TypeScript ni Astro.

**Step 4: Verificar lint y formato**

```bash
npm run lint && npm run format:check
```

Esperado: 0 errores de lint, 0 diferencias de formato.

**Step 5: Commit**

```bash
git add src/pages/etiquetas/index.astro
git commit -m "feat(etiquetas): rediseño índice con grid por popularidad (3 niveles)"
```

---

### Task 2: Mejorar `src/pages/etiquetas/[tag].astro`

**Files:**

- Modify: `src/pages/etiquetas/[tag].astro`

**Step 1: Leer el archivo actual**

El archivo tiene ~57 líneas. Sección template actual (líneas 26-33):

```astro
<BaseLayout title={`Etiqueta: ${tag}`} description={`Artículos con la etiqueta ${tag}`}>
  <section class="container page-section">
    <h1>Etiqueta: <span class="highlight">{tag}</span></h1>
    <p class="subtitle">{posts.length} {posts.length === 1 ? 'artículo' : 'artículos'}</p>
    <div class="posts-grid">
      {posts.map((post) => <ArticleCard post={post} />)}
    </div>
  </section>
</BaseLayout>
```

**Step 2: Añadir `metaPrompt` en el frontmatter**

Añadir justo antes del cierre `---` (línea 23), tras `const { tag, posts } = Astro.props;`:

```typescript
const metaPrompt = `$ grep -r "${tag}" /blog/`;
```

**Step 3: Reemplazar el bloque del template**

Reemplazar las líneas 26-34 con:

```astro
<BaseLayout title={`Etiqueta: ${tag}`} description={`Artículos con la etiqueta ${tag}`}>
  <section class="container page-section">
    <div class="page-header">
      <span class="meta-prompt">{metaPrompt}</span>
      <h1>Etiqueta: <span class="highlight">{tag}</span></h1>
      <p class="subtitle">{posts.length} {posts.length === 1 ? 'artículo' : 'artículos'}</p>
      <a href="/etiquetas/" class="back-link">← Todas las etiquetas</a>
    </div>
    <div class="posts-grid">
      {posts.map((post) => <ArticleCard post={post} />)}
    </div>
  </section>
</BaseLayout>
```

**Step 4: Actualizar el bloque `<style>`**

Reemplazar el bloque `<style>` existente con:

```astro
<style>
  .page-section {
    padding: 3rem 0 4rem;
  }

  .page-header {
    text-align: center;
    margin-bottom: 2.5rem;
  }

  .meta-prompt {
    display: block;
    color: var(--color-primary);
    font-size: 0.8125rem;
    margin-bottom: 0.5rem;
  }

  .page-header h1 {
    margin-bottom: 0.5rem;
  }

  .highlight {
    color: var(--color-primary);
  }

  .subtitle {
    color: var(--color-text-muted);
    margin-bottom: 0.75rem;
  }

  .back-link {
    display: inline-block;
    font-size: 0.8125rem;
    color: var(--color-text-muted);
    text-decoration: none;
    transition: color 0.2s;
  }

  .back-link:hover {
    color: var(--color-primary);
  }

  .posts-grid {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
</style>
```

**Step 5: Verificar build y lint**

```bash
npm run build 2>&1 | tail -20 && npm run lint && npm run format:check
```

Esperado: build exitoso, 0 errores lint, 0 diferencias formato.

**Step 6: Commit**

```bash
git add src/pages/etiquetas/[tag].astro
git commit -m "feat(etiquetas): añadir meta-prompt y back-link a página individual de tag"
```

---

### Task 3: Verificación visual (opcional pero recomendada)

**Step 1: Preview de producción**

```bash
npm run build && npm run preview
```

Abrir en el navegador:

- `http://localhost:4321/etiquetas/` — verificar las 3 secciones, tarjetas uniformes, colores de borde
- `http://localhost:4321/etiquetas/bash` (o cualquier tag existente) — verificar meta-prompt y back-link
- Modo oscuro y claro: alternar con el toggle del blog

**Step 2: Comprobar edge cases**

- Que ninguna sección quede vacía si hay pocas tags con el mismo count
- Que el grid se adapte bien en móvil (< 768px)
