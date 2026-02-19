# Code Quality & PWA — Plan de Implementación

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminar dos smell de código (CSS duplicado y magic numbers) y añadir dos mejoras PWA (shortcuts en manifest y notificación de actualización del service worker).

**Architecture:** Task 1 elimina CSS duplicado en HeroSlider usando `color-mix()` (soporte ~97% en 2026, sin fallback necesario). Task 2 extrae constantes nombradas en RelatedArticles. Task 3 añade `shortcuts` al manifest PWA. Task 4 añade notificación de actualización SW (postMessage en sw.js + banner en BaseLayout). Cada task es independiente.

**Tech Stack:** Astro 5, CSS `color-mix()`, PWA Web App Manifest, Service Worker postMessage

**Nota previa al implementador:** Dos ítems del análisis original son falsos positivos ya resueltos:

- `CopyCodeButton` feedback → **ya implementado**: `copyBtn.textContent = '[copiado!]'` + clase `.copied` (fondo verde 2s) presente en el código actual.
- `manifest.json` `theme_color` hardcoded → **descartado**: difícil de hacer responsive sin JS; `<meta name="theme-color">` en BaseLayout ya gestiona el color de la barra del navegador por tema. No vale la complejidad.

---

## Task 1: Simplificar CSS de dot hover en HeroSlider

En `src/components/HeroSlider.astro` hay 3 reglas CSS para el color hover del punto inactivo: una con rgba hardcoded (light), otra con rgba hardcoded (dark), y una con `@supports color-mix`. El `color-mix()` ya resuelve el problema elegantemente y tiene ~97% de soporte global en 2026 (Chrome 111+, Firefox 113+, Safari 16.2+). Las dos reglas de fallback son innecesarias.

**Files:**

- Modify: `src/components/HeroSlider.astro:250-262`

**Step 1: Verificar el estado actual**

```bash
grep -n "slider-dot:hover" src/components/HeroSlider.astro
```

Expected: 3 bloques (rgba light, :global dark, @supports color-mix).

**Step 2: Reemplazar las 3 reglas por 1**

En `src/components/HeroSlider.astro`, localizar el bloque (líneas 250-262):

```css
.slider-dot:hover:not(.active)::after {
  background: rgba(26, 115, 232, 0.4);
}

:global([data-theme='dark']) .slider-dot:hover:not(.active)::after {
  background: rgba(88, 213, 162, 0.4);
}

@supports (background: color-mix(in srgb, red 50%, transparent)) {
  .slider-dot:hover:not(.active)::after {
    background: color-mix(in srgb, var(--color-primary) 40%, transparent);
  }
}
```

Reemplazar por:

```css
.slider-dot:hover:not(.active)::after {
  background: color-mix(in srgb, var(--color-primary) 40%, transparent);
}
```

**Step 3: Verificar lint y build**

```bash
cd /home/antonio/Documentos/blog && npm run lint && npm run build 2>&1 | tail -5
```

Expected: 0 errores, build sin errores.

**Step 4: Commit**

```bash
git add src/components/HeroSlider.astro
git commit -m "style: simplificar dot hover en HeroSlider — color-mix reemplaza 3 reglas CSS por 1"
```

---

## Task 2: Extraer constantes nombradas en RelatedArticles

En `src/components/RelatedArticles.astro` hay 4 números mágicos en el algoritmo de scoring: `2` (peso de tags compartidos), `365` (días para recency), `0.5` (peso del boost de recency) y `3` (máximo de artículos relacionados). Deben ser constantes nombradas.

**Files:**

- Modify: `src/components/RelatedArticles.astro:15-30`

**Step 1: Verificar el estado actual**

```bash
grep -n "sharedTags \* 2\|/ 365\|\* 0\.5\|slice(0, 3)" src/components/RelatedArticles.astro
```

Expected: 4 líneas con los números mágicos.

**Step 2: Añadir constantes antes de `const scored`**

En `src/components/RelatedArticles.astro`, tras `const now = new Date();` (línea 15) y antes de `const scored = ...` (línea 17), insertar:

```js
const TAG_SCORE_WEIGHT = 2;
const RECENCY_DAYS = 365;
const RECENCY_WEIGHT = 0.5;
const MAX_RELATED = 3;
```

**Step 3: Actualizar los usos**

En el bloque `.map()` (líneas 19-27), reemplazar los números mágicos:

Pasar de:

```js
const baseScore = sharedTags * 2 + sameCategory;
const daysSincePublished = (now.valueOf() - post.data.pubDate.valueOf()) / (1000 * 60 * 60 * 24);
const recencyBoost = Math.max(0, 1 - daysSincePublished / 365) * 0.5;
```

A:

```js
const baseScore = sharedTags * TAG_SCORE_WEIGHT + sameCategory;
const daysSincePublished = (now.valueOf() - post.data.pubDate.valueOf()) / (1000 * 60 * 60 * 24);
const recencyBoost = Math.max(0, 1 - daysSincePublished / RECENCY_DAYS) * RECENCY_WEIGHT;
```

Y `.slice(0, 3)` → `.slice(0, MAX_RELATED)`.

El bloque completo quedaría:

```js
const TAG_SCORE_WEIGHT = 2;
const RECENCY_DAYS = 365;
const RECENCY_WEIGHT = 0.5;
const MAX_RELATED = 3;

const now = new Date();

const scored = allPosts
  .filter((post) => post.id !== currentId)
  .map((post) => {
    const sharedTags = post.data.tags.filter((tag) => currentTags.includes(tag)).length;
    const sameCategory = post.data.category === currentCategory ? 1 : 0;
    const baseScore = sharedTags * TAG_SCORE_WEIGHT + sameCategory;
    const daysSincePublished =
      (now.valueOf() - post.data.pubDate.valueOf()) / (1000 * 60 * 60 * 24);
    const recencyBoost = Math.max(0, 1 - daysSincePublished / RECENCY_DAYS) * RECENCY_WEIGHT;
    return { post, baseScore, score: baseScore + recencyBoost };
  })
  .filter(({ baseScore }) => baseScore > 0)
  .sort((a, b) => b.score - a.score)
  .slice(0, MAX_RELATED);
```

**Step 4: Verificar lint y build**

```bash
cd /home/antonio/Documentos/blog && npm run lint && npm run build 2>&1 | tail -5
```

Expected: 0 errores, build sin errores.

**Step 5: Commit**

```bash
git add src/components/RelatedArticles.astro
git commit -m "refactor: extraer constantes nombradas en RelatedArticles — TAG_SCORE_WEIGHT, RECENCY_DAYS, RECENCY_WEIGHT, MAX_RELATED"
```

---

## Task 3: Añadir shortcuts al manifest PWA

El archivo `public/manifest.json` no tiene shortcuts. Los shortcuts permiten acceder directamente a `/blog/` y `/categorias/` desde el ícono de la app instalada (Android, Windows, macOS Sonoma+).

**Files:**

- Modify: `public/manifest.json`

**Step 1: Verificar el estado actual**

```bash
cat public/manifest.json
```

Expected: sin campo `shortcuts`.

**Step 2: Añadir shortcuts**

El archivo `public/manifest.json` completo:

```json
{
  "name": "tengoping.com",
  "short_name": "tengoping",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0D1117",
  "theme_color": "#58D5A2",
  "icons": [
    {
      "src": "/favicon.svg",
      "sizes": "any",
      "type": "image/svg+xml",
      "purpose": "any"
    },
    {
      "src": "/apple-touch-icon.png",
      "sizes": "180x180",
      "type": "image/png",
      "purpose": "maskable"
    }
  ],
  "shortcuts": [
    {
      "name": "Blog",
      "short_name": "Blog",
      "description": "Todos los artículos del blog",
      "url": "/blog/",
      "icons": [{ "src": "/favicon.svg", "sizes": "any" }]
    },
    {
      "name": "Categorías",
      "short_name": "Categorías",
      "description": "Artículos por categoría",
      "url": "/categorias/",
      "icons": [{ "src": "/favicon.svg", "sizes": "any" }]
    }
  ]
}
```

**Step 3: Verificar formato (Prettier)**

```bash
cd /home/antonio/Documentos/blog && npx prettier --check public/manifest.json
```

Si falla: `npx prettier --write public/manifest.json`

**Step 4: Verificar build**

```bash
npm run build 2>&1 | tail -5
```

Expected: build sin errores.

**Step 5: Commit**

```bash
git add public/manifest.json
git commit -m "feat: añadir shortcuts PWA al manifest — blog y categorías"
```

---

## Task 4: Notificación de actualización del service worker

Cuando el SW se actualiza, los visitantes con la versión anterior cacheada no saben que hay contenido nuevo. Añadir una notificación en la parte inferior de la pantalla que permite recargar con un clic.

Flujo:

1. `sw.js`: en el evento `activate`, tras limpiar cachés antiguas, si se eliminaron cachés viejas (= update, no primera instalación), envía `postMessage({ type: 'SW_UPDATED' })` a todas las ventanas.
2. `BaseLayout.astro`: añade un banner oculto `#sw-update-banner` y escucha el mensaje para mostrarlo. El botón `[actualizar]` llama a `location.reload()`.
3. Bump `CACHE_VERSION` de `'tengoping-v3'` a `'tengoping-v4'` para que el activate se dispare en los visitantes existentes.

**Files:**

- Modify: `public/sw.js:1,36-49`
- Modify: `src/layouts/BaseLayout.astro:213-219`

**Step 1: Leer el estado actual**

```bash
grep -n "CACHE_VERSION\|activate\|clients.claim\|postMessage" public/sw.js
grep -n "serviceWorker\|sw-update" src/layouts/BaseLayout.astro
```

Expected: `CACHE_VERSION = 'tengoping-v3'`, activate sin postMessage, BaseLayout sin banner ni mensaje listener.

**Step 2: Modificar `public/sw.js`**

2a. Cambiar la línea 1:

```js
const CACHE_VERSION = 'tengoping-v4';
```

2b. Reemplazar el bloque `activate` (líneas 36-49) con la versión que notifica tras la limpieza:

```js
// Activate: clean old caches and notify clients of update
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => {
        const oldKeys = keys.filter((key) => key !== STATIC_CACHE && key !== PAGES_CACHE);
        return Promise.all(oldKeys.map((key) => caches.delete(key))).then(() => oldKeys.length > 0);
      })
      .then((wasUpdated) => {
        if (wasUpdated) {
          return self.clients
            .matchAll({ type: 'window' })
            .then((clients) =>
              clients.forEach((client) => client.postMessage({ type: 'SW_UPDATED' }))
            );
        }
      })
  );
  self.clients.claim();
});
```

**Step 3: Modificar `src/layouts/BaseLayout.astro`**

Añadir el banner HTML y actualizar el script de registro. Reemplazar el bloque final del `<body>` (líneas 213-219):

De:

```astro
<script is:inline>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
  }
</script>
```

A:

```astro
<div id="sw-update-banner" role="alert" aria-live="polite" hidden>
  <span>$ nueva versión disponible</span>
  <button id="sw-reload-btn">[actualizar]</button>
</div>
<script is:inline>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data?.type !== 'SW_UPDATED') return;
      const banner = document.getElementById('sw-update-banner');
      if (banner) banner.hidden = false;
    });
    const reloadBtn = document.getElementById('sw-reload-btn');
    if (reloadBtn) {
      reloadBtn.addEventListener('click', () => location.reload());
    }
  }
</script>
```

3b. Añadir estilos en BaseLayout.astro. Localizar el `<style>` existente (o añadir uno al final del fichero, antes de `</html>`). Si BaseLayout.astro ya tiene un bloque `<style>`, añadir al final de ese bloque. Si no, añadir:

```astro
<style>
  #sw-update-banner {
    position: fixed;
    bottom: 1rem;
    right: 1rem;
    z-index: 9999;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    background: var(--color-surface);
    border: 1px solid var(--color-primary);
    font-family: var(--font-mono);
    font-size: 0.875rem;
    color: var(--color-text);
  }

  #sw-update-banner[hidden] {
    display: none;
  }

  #sw-reload-btn {
    background: none;
    border: 1px solid var(--color-primary);
    color: var(--color-primary);
    font-family: var(--font-mono);
    font-size: 0.875rem;
    padding: 0.25rem 0.5rem;
    cursor: pointer;
  }

  #sw-reload-btn:hover {
    background: var(--color-primary);
    color: var(--color-bg);
  }
</style>
```

**Step 4: Verificar lint**

```bash
cd /home/antonio/Documentos/blog && npm run lint
```

Expected: 0 errores. `public/sw.js` usa `globals.serviceworker` en ESLint config — `self`, `caches`, `clients` son globals válidos.

**Step 5: Verificar build**

```bash
npm run build 2>&1 | tail -5
```

Expected: build sin errores.

**Step 6: Verificar en el HTML generado**

```bash
grep -c "sw-update-banner" dist/index.html
```

Expected: al menos 1 (el banner está en el HTML).

**Step 7: Commit**

```bash
git add public/sw.js src/layouts/BaseLayout.astro
git commit -m "feat: notificación de actualización del service worker — banner con [actualizar], bump a v4"
```

---

## Verificación Final

```bash
# Build limpio
npm run build

# Lint
npm run lint

# Verificar que dot hover usa color-mix (sin rgba hardcoded)
grep -n "rgba\|color-mix" src/components/HeroSlider.astro | grep -v "hero-overlay\|hero-arrow"

# Verificar constantes en RelatedArticles
grep -n "TAG_SCORE_WEIGHT\|RECENCY_DAYS\|RECENCY_WEIGHT\|MAX_RELATED" src/components/RelatedArticles.astro

# Verificar shortcuts en manifest
grep -A 20 "shortcuts" public/manifest.json

# Verificar CACHE_VERSION bumped
grep "CACHE_VERSION" public/sw.js

# Ver los últimos commits
git log --oneline -6
```

Expected:

- HeroSlider: solo `color-mix` en dot hover, sin rgba hardcoded para ese selector
- RelatedArticles: 4 constantes nombradas presentes
- manifest.json: shortcuts con blog y categorías
- sw.js: `CACHE_VERSION = 'tengoping-v4'`
- 4 commits nuevos
