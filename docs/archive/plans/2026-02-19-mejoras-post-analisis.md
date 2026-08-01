# Mejoras Post-Análisis — Plan de Implementación

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolver todos los issues descubiertos en el análisis del 2026-02-19: memory leaks de listeners, bugs funcionales, accesibilidad, calidad de código, performance y CI/CD.

**Architecture:** Cada tarea es atómica e independiente. Se puede implementar en cualquier orden dentro de su grupo, pero los grupos están ordenados por impacto. No se requieren nuevas dependencias — todo vanilla JS y CSS.

**Tech Stack:** Astro 5, Vanilla JS, CSS custom properties, GitHub Actions

---

## Verificación estándar (usar en cada tarea)

```bash
npm run lint          # 0 errores obligatorio
npm run build         # debe completar sin errores
```

Para verificaciones visuales usar `npm run build && npm run preview` y abrir http://localhost:4321.

---

## GRUPO 1 — Memory Leaks / Bugs de Navegación

> **Por qué primero:** Bugs reales que afectan a todos los usuarios que navegan entre páginas. Cada navegación acumula listeners fantasma.

---

### Tarea 1: Search.astro — guard contra acumulación de listeners

**Problema:** `initSearch()` se llama en cada `astro:after-swap`. Cada llamada añade nuevos listeners de `click` (triggers), `keydown` (doc) y `click` (overlay) sin eliminar los anteriores. Tras 3 navegaciones hay 4 copias de cada uno.

**Archivo:** `src/components/Search.astro`

**Patrón de referencia:** `Header.astro` usa `let escListenerRegistered = false` a nivel de módulo.

**Solución:** Añadir un guard booleano a nivel de módulo. Los listeners del documento y del overlay se registran solo una vez. Los triggers (`[data-search-trigger]`) se re-bind en cada swap porque el DOM cambia.

**Paso 1: Leer el estado actual del script**

Ubicar la función `initSearch()` en `src/components/Search.astro` (líneas ~86–177). La estructura es:

```js
function initSearch() {
  const overlay = ...;
  const closeBtn = ...;
  const resultsCount = ...;

  // listeners de triggers (DOM cambia en swap → OK re-bind)
  document.querySelectorAll('[data-search-trigger]').forEach(btn => {
    btn.addEventListener('click', openSearch);
  });

  if (closeBtn) closeBtn.addEventListener('click', closeSearch);

  // listeners de documento (acumulan en cada swap → BUG)
  overlay.addEventListener('click', ...);
  document.addEventListener('keydown', ...);
}

initSearch();
document.addEventListener('astro:after-swap', initSearch);
```

**Paso 2: Aplicar el fix**

Añadir `let globalListenersRegistered = false;` antes de `initSearch()`. Mover los listeners del documento y overlay fuera de `initSearch` (o guardarlos con el guard). Los triggers sí se re-registran en cada swap.

El resultado debe quedar así:

```js
let globalListenersRegistered = false;

function initSearch() {
  // Re-bind triggers en cada swap (el DOM cambia)
  document.querySelectorAll('[data-search-trigger]').forEach(function (btn) {
    btn.addEventListener('click', openSearch);
  });

  const closeBtn = document.getElementById('search-close');
  if (closeBtn) closeBtn.addEventListener('click', closeSearch);

  // Solo registrar listeners globales una vez
  if (globalListenersRegistered) return;
  globalListenersRegistered = true;

  const overlay = document.getElementById('search-overlay');
  if (overlay) {
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeSearch();
    });
  }

  document.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      openSearch();
    }
    if (e.key === 'Escape') closeSearch();
    trapFocus(e);
  });
}

initSearch();
document.addEventListener('astro:after-swap', initSearch);
```

> **Nota importante:** `openSearch`, `closeSearch`, `trapFocus` deben estar definidas ANTES del guard (siguen igual). Los IDs de los elementos (`search-overlay`, `search-close`) — verificar que coincidan con el HTML del componente.

**Paso 3: Verificar**

```bash
npm run lint
npm run build
```

Navegar manualmente: Home → artículo → categoría → artículo. Abrir búsqueda en cada página. No debe haber comportamiento duplicado (múltiples cierres, múltiples aperturas).

**Paso 4: Commit**

```bash
git add src/components/Search.astro
git commit -m "fix: evitar acumulación de listeners en Search tras astro:after-swap"
```

---

### Tarea 2: ReadingProgress.astro — re-inicializar tras navegación

**Problema:** Los listeners de `scroll` y el cálculo de altura se configuran al cargar el script, pero no hay `astro:after-swap`. Al navegar a otro artículo, la barra de progreso queda desincronizada (calcula la altura del artículo anterior).

**Archivo:** `src/components/ReadingProgress.astro`

**Paso 1: Refactorizar en función `init`**

El código actual (líneas 6–25) ejecuta todo en el nivel de módulo. Hay que envolverlo en una función `init()` que limpie y re-registre. El listener de `scroll` debe limpiarse antes de añadir el nuevo.

```js
let scrollHandler = null;

function init() {
  const progressBar = document.getElementById('reading-progress');
  const backToTop = document.getElementById('back-to-top');

  if (!progressBar || !backToTop) return;

  const pb = progressBar;
  const bt = backToTop;

  // Limpiar listener anterior antes de añadir uno nuevo
  if (scrollHandler) {
    window.removeEventListener('scroll', scrollHandler);
  }

  scrollHandler = function updateProgress() {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    pb.style.width = `${progress}%`;
    bt.classList.toggle('visible', scrollTop > 300);
  };

  window.addEventListener('scroll', scrollHandler, { passive: true });

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  bt.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: prefersReduced ? 'instant' : 'smooth' });
  });

  scrollHandler(); // estado inicial
}

init();
document.addEventListener('astro:after-swap', init);
```

> **Nota:** La línea `bt.addEventListener('click', ...)` se añadirá múltiples veces en cada swap. Para evitarlo, cambiar a `onclick`:
>
> ```js
> bt.onclick = () => window.scrollTo({ top: 0, behavior: prefersReduced ? 'instant' : 'smooth' });
> ```

Esta tarea también resuelve **A6** (back-to-top sin reduced motion check).

**Paso 2: Verificar**

```bash
npm run lint
npm run build
```

Navegar entre artículos y verificar que la barra de progreso se resetea a 0% al entrar en un artículo nuevo.

**Paso 3: Commit**

```bash
git add src/components/ReadingProgress.astro
git commit -m "fix: re-inicializar ReadingProgress tras navegación y respetar prefers-reduced-motion"
```

---

### Tarea 3: GiscusComments.astro — desconectar MutationObserver de tema

**Problema:** El `observer` que escucha cambios de `data-theme` en `document.documentElement` (línea 65–70) nunca se desconecta. En cada `astro:after-swap` → `initGiscus()` → nuevo `observer` sin desconectar el anterior. Se acumulan observers.

**Archivo:** `src/components/GiscusComments.astro`

**Paso 1: Guardar referencia al observer y desconectarlo antes de crear uno nuevo**

Cambiar el script para que el observer del tema sea una variable de módulo reutilizable:

```js
// Guardar referencia al observer del tema a nivel de módulo
let themeObserver = null;

function setupThemeObserver() {
  // Desconectar el anterior si existe
  if (themeObserver) {
    themeObserver.disconnect();
  }
  themeObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.attributeName === 'data-theme') updateGiscusTheme();
    }
  });
  themeObserver.observe(document.documentElement, { attributes: true });
}

// En initGiscus también llamar a setupThemeObserver
function initGiscus() {
  const section = document.getElementById('giscus-section');
  if (!section || section.querySelector('script[src*="giscus"]')) return;

  // ... (resto del código existente igual)

  // Re-setup observer de tema
  setupThemeObserver();
}

// Llamada inicial (fuera de initGiscus para que ocurra siempre)
setupThemeObserver();

initGiscus();
document.addEventListener('astro:after-swap', initGiscus);
```

> **Importante:** El observer del `iframeDiv` ya gestiona correctamente su `disconnect()`. Solo hay que arreglar el `themeObserver`.

**Paso 2: Verificar**

```bash
npm run lint
npm run build
```

**Paso 3: Commit**

```bash
git add src/components/GiscusComments.astro
git commit -m "fix: desconectar MutationObserver de tema Giscus para evitar memory leak"
```

---

### Tarea 4: TableOfContents.astro — desconectar IntersectionObserver

**Problema:** `initScrollSpy()` crea un nuevo `IntersectionObserver` (línea 111) en cada `astro:after-swap` sin desconectar el anterior. Los observers muertos siguen observando secciones del artículo anterior.

**Archivo:** `src/components/TableOfContents.astro`

**Paso 1: Guardar referencia y desconectar**

Añadir una variable de módulo para el observer:

```js
let scrollObserver = null;

function initScrollSpy() {
  // Desconectar observer anterior si existe
  if (scrollObserver) {
    scrollObserver.disconnect();
    scrollObserver = null;
  }

  const desktopLinks = document.querySelectorAll < HTMLAnchorElement > '.toc-desktop a[data-slug]';
  const mobileLinks = document.querySelectorAll < HTMLAnchorElement > '.toc-mobile a[data-slug]';
  const mobileSummary = document.querySelector < HTMLElement > '.toc-mobile summary';

  // ... (código de slugsToObserve sin cambios)

  if (!slugsToObserve.size) return;

  scrollObserver = new IntersectionObserver(
    (entries) => {
      /* ... código existente sin cambios ... */
    },
    { rootMargin: '-80px 0px -60% 0px', threshold: 0 }
  );

  slugsToObserve.forEach((slug) => {
    const target = document.getElementById(slug);
    if (target) scrollObserver.observe(target);
  });
}

initScrollSpy();
document.addEventListener('astro:after-swap', initScrollSpy);
```

**Paso 2: Verificar**

```bash
npm run lint
npm run build
```

Navegar entre 3 artículos con TOC y verificar que el resaltado activo del TOC funciona correctamente en todos.

**Paso 3: Commit**

```bash
git add src/components/TableOfContents.astro
git commit -m "fix: desconectar IntersectionObserver del TOC al navegar entre artículos"
```

---

## GRUPO 2 — Bugs Funcionales

---

### Tarea 5: SearchAction JSON-LD — eliminar o corregir

**Problema:** `BaseLayout.astro` emite un `potentialAction` de tipo `SearchAction` con `urlTemplate: "${site.url}/?q={search_term_string}"`. Pagefind es un overlay client-side — no existe esa ruta. Google mostraría un sitelinks searchbox roto.

**Archivo:** `src/layouts/BaseLayout.astro`

**Paso 1: Buscar el bloque JSON-LD con SearchAction**

```bash
grep -n "SearchAction\|potentialAction\|search_term" src/layouts/BaseLayout.astro
```

**Paso 2: Eliminar el bloque `potentialAction`**

Quitar solo el bloque `"potentialAction"` del JSON-LD de Organization/WebSite. El resto del JSON-LD queda igual.

Antes:

```json
{
  "@type": "WebSite",
  ...
  "potentialAction": {
    "@type": "SearchAction",
    "target": { "@type": "EntryPoint", "urlTemplate": "..." },
    "query-input": "required name=search_term_string"
  }
}
```

Después: eliminar todo el bloque `"potentialAction"` (incluyendo la coma anterior).

**Paso 3: Verificar**

```bash
npm run lint
npm run build
```

Verificar con: `grep -r "SearchAction" dist/` → debe devolver vacío.

**Paso 4: Commit**

```bash
git add src/layouts/BaseLayout.astro
git commit -m "fix: eliminar SearchAction JSON-LD que apunta a ruta inexistente"
```

---

### Tarea 6: Blockquote — quitar font-style italic sin fuente itálica

**Problema:** `global.css` aplica `font-style: italic` a `.prose blockquote` pero JetBrains Mono Italic no está cargada. El browser aplica faux-italic (oblicuo sintético) que queda mal en monoespaciado. Los callouts ya corrigen esto con `font-style: normal`.

**Archivo:** `src/styles/global.css`

**Paso 1: Localizar la regla**

```bash
grep -n "font-style: italic" src/styles/global.css
```

**Paso 2: Cambiar a `normal`**

Localizar `.prose blockquote` y cambiar `font-style: italic` a `font-style: normal`.

**Paso 3: Verificar visualmente**

```bash
npm run build && npm run preview
```

Abrir un artículo que tenga `>` blockquotes normales (no callouts) y verificar que el texto no aparece oblicuo.

**Paso 4: Commit**

```bash
git add src/styles/global.css
git commit -m "fix: quitar font-style italic en blockquotes (no hay variante itálica cargada)"
```

---

### Tarea 7: Hover de botones — color: white → var(--color-bg)

**Problema:** Varios elementos usan `color: white` como texto sobre fondo `var(--color-primary)`. En dark mode, `--color-primary` es `#58D5A2` (verde claro) — `white` sobre verde claro tiene contraste WCAG insuficiente.

**Archivos:** `src/styles/global.css`, `src/components/ReadingProgress.astro`, `src/pages/404.astro`, `src/components/Pagination.astro`

**Paso 1: Buscar todas las instancias**

```bash
grep -n "color: white" src/styles/global.css src/components/ReadingProgress.astro src/pages/404.astro src/components/Pagination.astro
```

**Paso 2: Reemplazar**

Para cada instancia en contextos de hover sobre `var(--color-primary)`, cambiar:

```css
/* Antes */
color: white;

/* Después */
color: var(--color-bg);
```

> **Criterio:** Cambiar solo donde el fondo es `var(--color-primary)` o `var(--color-accent)`. Si el fondo es siempre oscuro (offline.html, OG images), dejar `white`.

**Paso 3: Verificar en ambos temas**

```bash
npm run build && npm run preview
```

Verificar hover de botones en modo claro Y modo oscuro. El texto debe ser legible en ambos.

**Paso 4: Commit**

```bash
git add src/styles/global.css src/components/ReadingProgress.astro src/pages/404.astro src/components/Pagination.astro
git commit -m "fix: usar var(--color-bg) en lugar de color: white para contraste correcto en dark mode"
```

---

## GRUPO 3 — Accesibilidad

---

### Tarea 8: prefers-reduced-motion global en global.css

**Problema:** Animaciones `fadeIn`, `blink` y la transición de `body` se ejecutan aunque el usuario prefiera sin movimiento. Solo `HeroSlider` respeta esta preferencia.

**Archivo:** `src/styles/global.css`

**Paso 1: Añadir bloque `@media (prefers-reduced-motion: reduce)` al final**

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }

  body {
    transition: none;
  }
}
```

> **Nota:** Este bloque usa `!important` porque las animaciones individuales pueden tener alta especificidad. Es aceptable aquí y es el patrón recomendado por MDN para este media query.

**Paso 2: Verificar**

```bash
npm run lint
npm run build
```

En DevTools → Rendering → Emulate CSS media: `prefers-reduced-motion: reduce`. Verificar que el cursor del header no parpadea y las transiciones son instantáneas.

**Paso 3: Commit**

```bash
git add src/styles/global.css
git commit -m "feat: respetar prefers-reduced-motion en animaciones globales"
```

---

### Tarea 9: Copy button — feedback aria-live para lectores de pantalla

**Problema:** El botón `[copiar]` cambia su `textContent` a `[copiado!]` pero ningún lector de pantalla lo anuncia automáticamente. Se necesita una región `aria-live` separada.

**Archivo:** `src/components/CopyCodeButton.astro`

**Paso 1: Añadir región aria-live al DOM (una sola vez)**

En `initCopyButtons()`, antes del forEach, crear la región si no existe:

```js
function initCopyButtons() {
  // Crear región aria-live si no existe
  if (!document.getElementById('copy-announce')) {
    const announce = document.createElement('div');
    announce.id = 'copy-announce';
    announce.setAttribute('aria-live', 'polite');
    announce.setAttribute('aria-atomic', 'true');
    announce.className = 'sr-only';
    document.body.appendChild(announce);
  }

  document.querySelectorAll('.prose pre').forEach((pre) => {
    // ... código existente
    copyBtn.addEventListener('click', async () => {
      const text = code?.textContent || '';
      try {
        await navigator.clipboard.writeText(text);
        copyBtn.textContent = '[copiado!]';
        copyBtn.classList.add('copied');

        // Anunciar para lectores de pantalla
        const announce = document.getElementById('copy-announce');
        if (announce) announce.textContent = 'Código copiado al portapapeles';

        setTimeout(() => {
          copyBtn.textContent = '[copiar]';
          copyBtn.classList.remove('copied');
          if (announce) announce.textContent = '';
        }, 2000);
      } catch {
        copyBtn.textContent = '[error]';
      }
    });
    // ... resto igual
  });
}
```

**Paso 2: Verificar**

```bash
npm run lint
npm run build
```

**Paso 3: Commit**

```bash
git add src/components/CopyCodeButton.astro
git commit -m "feat: anunciar éxito de copia con aria-live para lectores de pantalla"
```

---

### Tarea 10: HeroSlider — aria-label en español

**Problema:** `aria-label={`Slide ${i + 1}`}` en inglés. Todo el UI es en español.

**Archivo:** `src/components/HeroSlider.astro`

**Paso 1: Cambiar en la plantilla**

Buscar (línea ~83):

```astro
aria-label={`Slide ${i + 1}`}
```

Cambiar a:

```astro
aria-label={`Diapositiva ${i + 1}`}
```

**Paso 2: Verificar**

```bash
npm run lint
npm run build
```

**Paso 3: Commit**

```bash
git add src/components/HeroSlider.astro
git commit -m "fix: aria-label de dots del slider en español"
```

---

### Tarea 11: color-scheme meta tag

**Problema:** Sin `<meta name="color-scheme" content="light dark">` ni `color-scheme: light dark` en CSS, los scrollbars, inputs y controles nativos del browser no se adaptan al tema OS hasta que carga el JS.

**Archivo:** `src/layouts/BaseLayout.astro` y `src/styles/global.css`

**Paso 1: Añadir meta tag en `<head>`**

En `BaseLayout.astro`, dentro del `<head>`, justo después del `<meta charset>`:

```html
<meta name="color-scheme" content="light dark" />
```

**Paso 2: Añadir propiedad CSS en `:root`**

En `global.css`, en el bloque `:root`:

```css
:root {
  color-scheme: light dark;
  /* ... resto de variables existentes */
}
```

**Paso 3: Verificar**

```bash
npm run lint
npm run build
```

**Paso 4: Commit**

```bash
git add src/layouts/BaseLayout.astro src/styles/global.css
git commit -m "feat: añadir color-scheme para adaptar controles nativos del browser al tema OS"
```

---

## GRUPO 4 — Calidad de Código

---

### Tarea 12: Validar campo `author` con enum en content.config.ts

**Problema:** El schema Zod usa `z.string()` para `author`. Un typo silencioso rompe el author card en runtime. Debería fallar en build time.

**Archivo:** `src/content.config.ts`

**Paso 1: Leer el archivo**

```bash
cat src/content.config.ts
```

**Paso 2: Cambiar `z.string()` a `z.enum()`**

```typescript
// Antes
author: z.string(),

// Después
author: z.enum(['antonio', 'alois', 'eloculto']),
```

> **Nota:** Verificar los IDs exactos en `src/data/authors.json` antes de escribir el enum.

**Paso 3: Verificar**

```bash
npx astro check
npm run build
```

Si algún post tiene un `author` inválido, el build fallará con un mensaje claro. Corregir el post si es necesario.

**Paso 4: Commit**

```bash
git add src/content.config.ts
git commit -m "fix: validar campo author contra enum de IDs válidos en el schema Zod"
```

---

### Tarea 13: Typos — "articulos" → "artículos"

**Problema:** 3 instancias sin tilde.

**Archivos:**

- `src/components/AuthorCard.astro` — `[ver todos los articulos]`
- `src/pages/autor/[id].astro` — `{posts.length} articulos`
- `src/components/Search.astro` — `placeholder: 'buscar articulos...'`

**Paso 1: Corregir los tres archivos**

En cada archivo, buscar `articulos` (sin tilde) y reemplazar por `artículos`.

```bash
grep -rn "articulos" src/
```

**Paso 2: Verificar**

```bash
npm run lint
npm run build
```

**Paso 3: Commit**

```bash
git add src/components/AuthorCard.astro src/pages/autor/[id].astro src/components/Search.astro
git commit -m "fix: corregir tilde en \"artículos\" (3 instancias)"
```

---

### Tarea 14: sobre-nosotros.astro — quitar border-radius: 50%

**Problema:** Los avatares en `/sobre-nosotros` tienen `border-radius: 50%` (circular), rompiendo la convención terminal de 0 border-radius.

**Archivo:** `src/pages/sobre-nosotros.astro`

**Paso 1: Localizar y eliminar**

```bash
grep -n "border-radius" src/pages/sobre-nosotros.astro
```

Eliminar o cambiar a `border-radius: 0`.

**Paso 2: Verificar visualmente**

```bash
npm run build && npm run preview
```

Abrir `/sobre-nosotros` y verificar que los avatares son cuadrados.

**Paso 3: Commit**

```bash
git add src/pages/sobre-nosotros.astro
git commit -m "fix: quitar border-radius en avatares de sobre-nosotros (convención terminal)"
```

---

### Tarea 15: CSS — limpiar dead code y reglas redundantes

**Problema:**

- `--color-success` definida en ambos temas pero nunca usada
- Reglas `*:focus-visible` redefinidas innecesariamente para `.copy-button`, `.badge-tag`, `.card-hover`

**Archivo:** `src/styles/global.css`

**Paso 1: Eliminar `--color-success`**

```bash
grep -n "color-success" src/styles/global.css
```

Eliminar las líneas de declaración en `:root` y `[data-theme='dark']`.

**Paso 2: Eliminar focus-visible redundantes**

```bash
grep -n "focus-visible" src/styles/global.css
```

Verificar que `.copy-button:focus-visible`, `.badge-tag:focus-visible`, `.card-hover:focus-visible` no añaden nada que no cubra ya `*:focus-visible`. Si son idénticas, eliminarlas.

**Paso 3: Verificar**

```bash
npm run lint
npm run build
```

Verificar que el focus ring sigue siendo visible en esos elementos en el preview.

**Paso 4: Commit**

```bash
git add src/styles/global.css
git commit -m "chore: eliminar --color-success no usada y reglas focus-visible redundantes"
```

---

## GRUPO 5 — Performance

---

### Tarea 16: Añadir width, height y loading a imágenes de autor

**Problema:** `src/pages/sobre-nosotros.astro` y `src/pages/autor/[id].astro` renderizan `<img>` de avatares sin `width`, `height`, ni `loading`. Causa CLS (Cumulative Layout Shift).

**Archivos:**

- `src/pages/sobre-nosotros.astro`
- `src/pages/autor/[id].astro`

**Paso 1: Leer los dos archivos y localizar los `<img>` de avatares**

```bash
grep -n "<img" src/pages/sobre-nosotros.astro src/pages/autor/[id].astro
```

**Paso 2: Añadir atributos**

Para cada `<img>` de avatar (no para imágenes de posts):

```html
<!-- Antes -->
<img src="{author.avatar}" alt="{author.name}" />

<!-- Después -->
<img
  src="{author.avatar}"
  alt="{author.name}"
  width="80"
  height="80"
  loading="lazy"
  decoding="async"
/>
```

> **Nota:** Ajustar `width`/`height` al tamaño real que se muestra en el CSS. Verificar con DevTools el tamaño renderizado.

**Paso 3: Verificar**

```bash
npm run lint
npm run build
```

En Lighthouse del preview, verificar que "Avoid large layout shifts" no reporta los avatares.

**Paso 4: Commit**

```bash
git add src/pages/sobre-nosotros.astro "src/pages/autor/[id].astro"
git commit -m "perf: añadir width, height, loading y decoding a imágenes de autor"
```

---

### Tarea 17: ArticleCard — placeholder de aspecto para evitar CLS

**Problema:** Las cards de artículo sin imagen muestran un `placeholder-article.svg` pero las cards con imagen lazy-loaded no tienen bloqueo de aspecto en el `<img>`. Puede causar CLS.

**Archivo:** `src/components/ArticleCard.astro`

**Paso 1: Leer el componente**

```bash
cat src/components/ArticleCard.astro
```

**Paso 2: Añadir `aspect-ratio` al img dentro de la card**

Si el `<img>` no tiene `width`/`height` explícitos, añadirlos para que el browser reserve espacio. Las imágenes de portada son 800×500 (ratio 8:5):

```html
<!-- Añadir width/height para que el browser reserve espacio -->
<img
  src="{post.data.image}"
  alt="{post.data.title}"
  width="800"
  height="500"
  loading="lazy"
  decoding="async"
/>
```

Si ya tiene `loading="lazy"`, solo añadir `width`/`height` y `decoding`.

**Paso 3: Verificar**

```bash
npm run build && npm run preview
```

Scroll rápido por `/blog` — las cards no deben saltar de tamaño al cargar las imágenes.

**Paso 4: Commit**

```bash
git add src/components/ArticleCard.astro
git commit -m "perf: añadir width/height a imágenes de ArticleCard para prevenir CLS"
```

---

## GRUPO 6 — CI/CD

---

### Tarea 18: Broken links checker en CI

**Problema:** No hay verificación automática de enlaces rotos post-build. Un artículo con un enlace interno roto pasa CI sin detectarse.

**Archivo:** `.github/workflows/ci.yml`

**Paso 1: Leer el workflow actual**

```bash
cat .github/workflows/ci.yml
```

**Paso 2: Añadir paso check-links tras el build**

Añadir este paso después del paso `npm run build` y antes de cualquier deploy:

```yaml
- name: Check internal links
  run: |
    npx broken-link-checker-local dist/ \
      --recursive \
      --exclude-external \
      --get \
      2>&1 | tee /tmp/links.txt
    ! grep -q "BROKEN" /tmp/links.txt
```

> **Alternativa más ligera:** usar `lychee` (más rápido, binario Rust):
>
> ```yaml
> - name: Check links
>   uses: lycheeverse/lychee-action@v1
>   with:
>     args: --offline dist/
> ```

Elegir la opción que mejor se integre con las dependencias actuales.

**Paso 3: Verificar localmente**

```bash
npm run build
npx broken-link-checker-local dist/ --recursive --exclude-external
```

Revisar la salida. Si hay falsos positivos (ej. `/pagefind/` o anchors de Giscus), añadir `--exclude` para esas rutas.

**Paso 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: añadir verificación de enlaces internos rotos post-build"
```

---

## GRUPO 7 — Seguridad

---

### Tarea 19: Giscus strict mode

**Problema:** `data-strict="0"` permite que comentarios de staging/preview URLs con pathname similar hereden el thread de producción. `data-strict="1"` hace matching exacto.

**Archivo:** `src/components/GiscusComments.astro`

**Paso 1: Cambiar el atributo**

Localizar (línea ~31):

```js
script.setAttribute('data-strict', '0');
```

Cambiar a:

```js
script.setAttribute('data-strict', '1');
```

**Paso 2: Verificar**

```bash
npm run lint
npm run build
```

En producción, verificar que los comentarios existentes siguen visibles en sus artículos (el strict mode puede afectar al mapping si Giscus usaba URL fuzzy antes).

> **Nota de precaución:** Si hay artículos con comentarios existentes, verificar en un artículo de prueba antes de desplegar para confirmar que no se pierden threads.

**Paso 3: Commit**

```bash
git add src/components/GiscusComments.astro
git commit -m "security: activar strict mode en Giscus para evitar thread spoofing"
```

---

## GRUPO 8 — PWA (Opcional / Baja prioridad)

---

### Tarea 20: Notificación de nueva versión disponible

**Problema:** Cuando el service worker detecta una nueva versión, los visitantes continúan viendo la versión cacheada sin saberlo.

**Archivos:** `public/sw.js`, `src/layouts/BaseLayout.astro`

**Paso 1: Añadir mensaje de update en sw.js**

En `sw.js`, en el event `activate`, enviar mensaje a todos los clientes:

```js
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
      )
      .then(() => {
        // Notificar a todos los clientes que hay nueva versión
        self.clients.matchAll({ type: 'window' }).then((clients) => {
          clients.forEach((client) => client.postMessage({ type: 'SW_UPDATED' }));
        });
      })
  );
});
```

**Paso 2: Añadir listener en BaseLayout y mostrar banner**

En `BaseLayout.astro`, en el script de registro del SW, añadir:

```js
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.addEventListener('message', (event) => {
    if (event.data?.type === 'SW_UPDATED') {
      // Mostrar banner no intrusivo
      const banner = document.getElementById('sw-update-banner');
      if (banner) banner.style.display = 'flex';
    }
  });
}
```

Y añadir el HTML del banner (oculto por defecto):

```html
<div id="sw-update-banner" style="display:none" role="alert" aria-live="polite">
  <span>Nueva versión disponible.</span>
  <button onclick="window.location.reload()">[ actualizar ]</button>
  <button onclick="this.parentElement.style.display='none'">[ cerrar ]</button>
</div>
```

**Paso 3: Commit**

```bash
git add public/sw.js src/layouts/BaseLayout.astro
git commit -m "feat: notificar al usuario cuando hay nueva versión del service worker"
```

---

## Resumen de Prioridades

| Grupo | Tarea                             | Impacto | Esfuerzo |
| ----- | --------------------------------- | ------- | -------- |
| 1     | T1: Search listener guard         | Alto    | Bajo     |
| 1     | T2: ReadingProgress re-init       | Alto    | Bajo     |
| 1     | T3: Giscus observer leak          | Medio   | Bajo     |
| 1     | T4: TOC observer leak             | Medio   | Bajo     |
| 2     | T5: SearchAction JSON-LD          | Medio   | Bajo     |
| 2     | T6: Blockquote italic             | Medio   | Mínimo   |
| 2     | T7: color:white → var(--color-bg) | Medio   | Bajo     |
| 3     | T8: prefers-reduced-motion        | Medio   | Bajo     |
| 3     | T9: Copy button aria-live         | Medio   | Bajo     |
| 3     | T10: Slider aria-label ES         | Bajo    | Mínimo   |
| 3     | T11: color-scheme meta            | Bajo    | Mínimo   |
| 4     | T12: Author enum validation       | Medio   | Mínimo   |
| 4     | T13: Typos artículos              | Bajo    | Mínimo   |
| 4     | T14: border-radius sobre-nosotros | Bajo    | Mínimo   |
| 4     | T15: Dead code CSS                | Bajo    | Bajo     |
| 5     | T16: Avatar img attributes        | Medio   | Bajo     |
| 5     | T17: ArticleCard CLS              | Medio   | Bajo     |
| 6     | T18: Broken links CI              | Medio   | Medio    |
| 7     | T19: Giscus strict mode           | Bajo    | Mínimo   |
| 8     | T20: PWA update banner            | Bajo    | Medio    |
