# Mejoras Menores Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Mejorar `offline.html` para que los botones queden dentro de la ventana terminal, y simplificar `Breadcrumbs.astro` eliminando la construcción de URLs completas + extracción de pathname.

**Architecture:** Dos cambios quirúrgicos en ficheros independientes. Sin nuevas dependencias. Sin refactors adicionales.

**Tech Stack:** HTML/CSS vanilla, Astro 5

---

### Task 1: Mover acciones al interior de la ventana en offline.html

**Files:**

- Modify: `public/offline.html`

**Contexto:**

Actualmente el fichero tiene un `<div class="actions">` fuera del `<div class="terminal-window">` con dos botones flotantes. El objetivo es moverlos dentro de `.terminal-body` como líneas de terminal interactivas (`$ [reintentar]`, `$ [volver_al_inicio]`), eliminar el div externo y limpiar los estilos CSS que ya no aplican.

**Step 1: Localizar las secciones a modificar**

Abrir `public/offline.html`. Las secciones relevantes son:

```html
<!-- Línea final del terminal-body (mantener al final) -->
<p class="terminal-line"><span class="prompt">$</span> <span class="cursor-blink">_</span></p>
```

```html
<!-- Div externo a eliminar (líneas 148-151) -->
<div class="actions">
  <button class="terminal-btn" onclick="location.reload()">[reintentar]</button>
  <a href="/" class="terminal-btn">[volver_al_inicio]</a>
</div>
```

**Step 2: Insertar las líneas de acción en terminal-body**

Justo ANTES de la línea del cursor parpadeante (`$ _`), añadir:

```html
<p class="terminal-line">&nbsp;</p>
<p class="terminal-line">
  <span class="prompt">$</span>
  <button class="terminal-cmd" onclick="location.reload()">[reintentar]</button>
</p>
<p class="terminal-line">
  <span class="prompt">$</span>
  <a href="/" class="terminal-cmd">[volver_al_inicio]</a>
</p>
```

El bloque completo del final de `.terminal-body` queda:

```html
<p class="terminal-line">&nbsp;</p>
<p class="terminal-line">
  <span class="prompt">$</span>
  <button class="terminal-cmd" onclick="location.reload()">[reintentar]</button>
</p>
<p class="terminal-line">
  <span class="prompt">$</span>
  <a href="/" class="terminal-cmd">[volver_al_inicio]</a>
</p>
<p class="terminal-line"><span class="prompt">$</span> <span class="cursor-blink">_</span></p>
```

**Step 3: Eliminar el div .actions externo**

Eliminar completamente estas líneas (fuera del `</div>` de `.terminal-window`):

```html
<div class="actions">
  <button class="terminal-btn" onclick="location.reload()">[reintentar]</button>
  <a href="/" class="terminal-btn">[volver_al_inicio]</a>
</div>
```

**Step 4: Reemplazar estilos CSS**

Eliminar los bloques:

```css
.actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}
.terminal-btn {
  padding: 0.6rem 1.25rem;
  background: #161b22;
  color: #58d5a2;
  border: 1px solid #30363d;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 0.875rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
}
.terminal-btn:hover {
  background: #58d5a2;
  color: #0d1117;
  border-color: #58d5a2;
}
```

Y también el bloque dentro del `@media (max-width: 480px)`:

```css
.actions {
  flex-direction: column;
  width: 100%;
  max-width: 700px;
}
.terminal-btn {
  text-align: center;
}
```

Añadir en su lugar (antes del bloque `@media`):

```css
.terminal-cmd {
  background: none;
  border: none;
  color: #58d5a2;
  font-family: 'JetBrains Mono', monospace;
  font-size: inherit;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
  text-decoration: none;
  transition: opacity 0.2s;
}
.terminal-cmd:hover {
  background: #58d5a2;
  color: #0d1117;
}
```

**Step 5: Verificar visualmente**

```bash
npm run dev
# Abrir http://localhost:4321/offline.html
# Verificar:
# - La ventana terminal contiene todo: output + acciones + cursor
# - No hay div flotante fuera de la ventana
# - [reintentar] y [volver_al_inicio] tienen prefijo $ y color verde
# - Hover cambia a fondo verde / texto oscuro
```

**Step 6: Commit**

```bash
git add public/offline.html
git commit -m "fix: mover acciones dentro de la ventana terminal en offline.html"
```

---

### Task 2: Simplificar URLs en Breadcrumbs.astro

**Files:**

- Modify: `src/components/Breadcrumbs.astro`

**Contexto:**

El componente construye `breadcrumbItems` con URLs completas (`${site.url}/blog`) y luego en el template extrae solo el pathname con `new URL(item.url).pathname`. Además el JSON-LD reutiliza los mismos items. El objetivo es separar los dos usos: paths relativos para los links del DOM, URLs completas solo para JSON-LD.

**Step 1: Leer el fichero actual**

```bash
cat src/components/Breadcrumbs.astro
```

Confirmar que el frontmatter actual contiene:

```ts
const breadcrumbItems = [
  { name: '~', url: site.url },
  { name: 'blog', url: `${site.url}/blog` },
  { name: category, url: `${site.url}/categorias/${categorySlug}` },
  { name: title, url: `${site.url}${Astro.url.pathname}` },
];

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: breadcrumbItems.map((item, index) => ({
    '@type': 'ListItem',
    position: index + 1,
    name: item.name,
    item: item.url,
  })),
};
```

Y que el template usa `new URL(item.url).pathname`:

```astro
<a href={new URL(item.url).pathname}>{item.name}</a>
```

**Step 2: Reemplazar el bloque de datos en el frontmatter**

Cambiar `breadcrumbItems` a rutas relativas y construir `jsonLdItems` separado para el schema:

```ts
const breadcrumbItems = [
  { name: '~', url: '/' },
  { name: 'blog', url: '/blog' },
  { name: category, url: `/categorias/${categorySlug}` },
  { name: title, url: Astro.url.pathname },
];

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    { '@type': 'ListItem', position: 1, name: '~', item: site.url },
    { '@type': 'ListItem', position: 2, name: 'blog', item: `${site.url}/blog` },
    {
      '@type': 'ListItem',
      position: 3,
      name: category,
      item: `${site.url}/categorias/${categorySlug}`,
    },
    {
      '@type': 'ListItem',
      position: 4,
      name: title,
      item: `${site.url}${Astro.url.pathname}`,
    },
  ],
};
```

**Step 3: Simplificar el template**

Cambiar en el `<ol>` la línea del enlace:

```astro
<!-- Antes -->
<a href={new URL(item.url).pathname}>{item.name}</a>

<!-- Después -->
<a href={item.url}>{item.name}</a>
```

**Step 4: Verificar que el build no tiene errores**

```bash
npm run build 2>&1 | tail -5
```

Expected: `[build] Complete!` sin errores.

**Step 5: Verificar los breadcrumbs en una página de artículo**

```bash
npm run preview
# Abrir cualquier artículo en http://localhost:4321/blog/[id]
# Verificar que los breadcrumbs muestran: ~ / blog / categoría / título
# Verificar que los links navegan correctamente
```

**Step 6: Commit**

```bash
git add src/components/Breadcrumbs.astro
git commit -m "refactor: simplificar URLs en Breadcrumbs — paths relativos en DOM, URLs completas solo en JSON-LD"
```

---

## Orden de ejecución

Tasks independientes — se pueden hacer en cualquier orden.

```
Task 1 → offline.html acciones dentro de terminal
Task 2 → Breadcrumbs URLs simplificadas
```
