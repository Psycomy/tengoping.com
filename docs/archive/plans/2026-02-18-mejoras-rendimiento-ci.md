# Mejoras de Rendimiento, Accesibilidad y CI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Aplicar 6 mejoras de prioridad alta/media identificadas en el análisis del blog: preconnect a Giscus, aria-hidden en SVGs, sizes en imágenes responsivas, limpieza de PAGES_CACHE en SW, y workflow de GitHub Actions CI.

**Architecture:** Cambios quirúrgicos en archivos existentes — sin nuevas dependencias, sin refactors. El SW se modifica en `public/sw.js` (fuente) y el postbuild lo copia al dist. GitHub Actions corre `npm ci && npm run build && npx astro check` en cada push/PR.

**Tech Stack:** Astro 5, vanilla JS, Service Worker API, GitHub Actions

---

### Task 1: preconnect a giscus.app en BaseLayout

**Files:**

- Modify: `src/layouts/BaseLayout.astro:82-88` (bloque de fonts/prefetch)

**Step 1: Añadir preconnect**

En `BaseLayout.astro`, después de `<link rel="manifest" href="/manifest.json" />` (línea 44), añadir antes del bloque de fonts:

```astro
<link rel="preconnect" href="https://giscus.app" crossorigin />
```

Quedaría así (entre línea 44 y el bloque de fonts línea 83):

```astro
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#1A73E8" />
<link rel="canonical" href={canonicalURL} />
...
<!-- Preconnect -->
<link rel="preconnect" href="https://giscus.app" crossorigin />

<!-- Fonts (self-hosted) -->
<link rel="preload" href="/fonts/JetBrainsMono-Regular.woff2" ...
```

**Step 2: Verificar visualmente**

```bash
npm run dev
# Abrir DevTools → Network → buscar "giscus.app"
# Debe aparecer la conexión pre-establecida
```

**Step 3: Commit**

```bash
git add src/layouts/BaseLayout.astro
git commit -m "perf: preconnect a giscus.app para reducir latencia de comentarios"
```

---

### Task 2: aria-hidden en SVGs de ShareButtons

**Files:**

- Modify: `src/components/ShareButtons.astro:52`

**Step 1: Añadir aria-hidden al SVG**

Línea 52 actual:

```astro
<svg
  width="18"
  height="18"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  set:html={net.icon}
/>
```

Cambiar a:

```astro
<svg
  aria-hidden="true"
  focusable="false"
  width="18"
  height="18"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  set:html={net.icon}
/>
```

El `aria-label` ya está en el `<a>` padre — el SVG debe ser invisible para lectores de pantalla.

**Step 2: Commit**

```bash
git add src/components/ShareButtons.astro
git commit -m "a11y: aria-hidden en SVGs de ShareButtons para evitar duplicación con aria-label del enlace"
```

---

### Task 3: sizes attribute en ArticleCard

**Files:**

- Modify: `src/components/ArticleCard.astro:33`

**Step 1: Añadir sizes al Image**

Línea 33 actual:

```astro
? <Image
  src={image}
  alt={title}
  class="card-image"
  loading="lazy"
  width={300}
  height={200}
  format="webp"
/>
```

Cambiar a:

```astro
? <Image
  src={image}
  alt={title}
  class="card-image"
  loading="lazy"
  width={300}
  height={200}
  format="webp"
  sizes="(max-width: 768px) 100vw, 300px"
/>
```

**Razonamiento:** En desktop la imagen ocupa `flex: 0 0 300px` → 300px fijo. En mobile (`max-width: 768px`) la tarjeta es columna → imagen ocupa 100vw.

**Step 2: Commit**

```bash
git add src/components/ArticleCard.astro
git commit -m "perf: añadir sizes a ArticleCard para responsive image selection óptima"
```

---

### Task 4: sizes attribute en HeroSlider

**Files:**

- Modify: `src/components/HeroSlider.astro:27`

**Step 1: Añadir sizes al Image del slider**

Línea 27 actual:

```astro
? <Image
  src={post.data.image}
  alt={post.data.title}
  class="slide-image"
  loading={i === 0 ? 'eager' : 'lazy'}
  fetchpriority={i === 0 ? 'high' : 'auto'}
  format="webp"
  width={1200}
  height={450}
/>
```

Cambiar a:

```astro
? <Image
  src={post.data.image}
  alt={post.data.title}
  class="slide-image"
  loading={i === 0 ? 'eager' : 'lazy'}
  fetchpriority={i === 0 ? 'high' : 'auto'}
  format="webp"
  width={1200}
  height={450}
  sizes="100vw"
/>
```

**Razonamiento:** El slider siempre ocupa el ancho completo del viewport tanto en desktop como en mobile.

**Step 2: Commit**

```bash
git add src/components/HeroSlider.astro
git commit -m "perf: añadir sizes=100vw a HeroSlider para selección óptima de imagen responsiva"
```

---

### Task 5: Limpieza de PAGES_CACHE en Service Worker

**Files:**

- Modify: `public/sw.js`

**Problema:** El PAGES_CACHE (páginas HTML visitadas) crece indefinidamente. Cada página visitada se guarda pero nunca se elimina salvo que cambie `CACHE_VERSION`.

**Step 1: Añadir función limitCache**

Añadir esta función después de la función `isHashedAsset` (después de línea 16):

```js
const MAX_PAGES = 50;

async function limitPagesCache() {
  const cache = await caches.open(PAGES_CACHE);
  const keys = await cache.keys();
  if (keys.length > MAX_PAGES) {
    const toDelete = keys.slice(0, keys.length - MAX_PAGES);
    await Promise.all(toDelete.map((k) => cache.delete(k)));
  }
}
```

**Step 2: Llamar limitPagesCache tras cada put en el handler de documentos**

En el handler `request.destination === 'document'` (línea ~51-54), el bloque `.then` que hace `cache.put` queda así:

```js
caches.open(PAGES_CACHE).then((cache) => {
  cache.put(request, clone);
  limitPagesCache();
});
```

**Resultado final del bloque fetch de documentos:**

```js
if (request.destination === 'document') {
  event.respondWith(
    fetch(request)
      .then((response) => {
        const clone = response.clone();
        caches.open(PAGES_CACHE).then((cache) => {
          cache.put(request, clone);
          limitPagesCache();
        });
        return response;
      })
      .catch(() => caches.match(request).then((cached) => cached || caches.match('/offline.html')))
  );
}
```

**Step 3: Verificar que el SW se actualiza**

El `postbuild.mjs` inyecta un nuevo `CACHE_VERSION` automáticamente en cada build, lo que fuerza al SW a actualizarse. No hay nada extra que hacer.

**Step 4: Commit**

```bash
git add public/sw.js
git commit -m "fix: limitar PAGES_CACHE a 50 entradas para evitar crecimiento indefinido"
```

---

### Task 6: GitHub Actions CI workflow

**Files:**

- Create: `.github/workflows/ci.yml`

**Objetivo:** Validar que el build no se rompe en cada push a `main` y en PRs. Cloudflare Pages despliega solo; este workflow añade type checking con `astro check` que Cloudflare no ejecuta.

**Step 1: Crear el workflow**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    name: Build & Type Check
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Type check
        run: npx astro check
```

**Notas:**

- `npm ci` (no `npm install`) — más rápido y determinista en CI
- `node-version: 22` — coincide con la versión LTS actual que usa Cloudflare Pages por defecto
- `npm run build` ejecuta `astro build && node scripts/postbuild.mjs` completo
- `npx astro check` valida tipos TypeScript y sintaxis de componentes Astro sin necesitar instalación extra

**Step 2: Verificar que astro check funciona localmente**

```bash
npx astro check
# Expected: No errors found
```

**Step 3: Commit y push**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: añadir GitHub Actions workflow para build y type check"
git push
# Ir a github.com/Psycomy/tengoping.com → Actions → verificar que el workflow se ejecuta correctamente
```

---

## Orden de ejecución recomendado

Tasks 1-4 son independientes entre sí — se pueden hacer en cualquier orden.
Task 5 (SW) es independiente también.
Task 6 (Actions) debe ir al final para poder verificar que el build pasa antes de configurar CI.

```
Task 1 → preconnect giscus
Task 2 → aria-hidden SVGs
Task 3 → sizes ArticleCard
Task 4 → sizes HeroSlider
Task 5 → limit PAGES_CACHE
Task 6 → GitHub Actions
```
