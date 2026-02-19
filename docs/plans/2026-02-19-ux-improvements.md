# UX Improvements — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 7 targeted UX improvements across accessibility, aesthetics, and reading experience without touching routing, content, or Giscus.

**Architecture:** Each task modifies exactly one file. Changes are CSS/HTML/vanilla JS only. No new dependencies. No new pages. Verification after each commit: `npm run lint`. Final gate: `npm run build`.

**Tech Stack:** Astro 5, vanilla JS TypeScript in `<script>` tags, CSS custom properties, JetBrains Mono, Pagefind.

---

## Pre-flight

```bash
cd /home/antonio/Documentos/blog
git status   # should be clean
npm run lint # should be 0 errors
```

---

### Task 1: HeadingAnchors — anchors visibles en dispositivos touch

**Files:**

- Modify: `src/components/HeadingAnchors.astro`

**Context:** The `[#]` anchor links have `opacity: 0` and only appear on hover. On touch devices there is no hover state, so users can never discover or copy section permalinks. Fix: use `@media (hover: none)` (a capability media query, not a size breakpoint) to always show them at reduced opacity on touch devices.

**Step 1: Add the media query**

In `HeadingAnchors.astro`, inside `<style>`, after the existing `:global(.heading-anchor:hover)` rule (currently around line 65), add:

```css
@media (hover: none) {
  :global(.heading-anchor) {
    opacity: 0.4;
  }
}
```

Full `<style>` block after the change (for reference):

```html
<style>
  :global(.prose h2),
  :global(.prose h3),
  :global(.prose h4) {
    position: relative;
  }

  :global(.heading-anchor) {
    display: inline-block;
    margin-left: 0.5rem;
    font-size: 0.75em;
    font-family: var(--font-mono);
    color: var(--color-primary);
    text-decoration: none;
    opacity: 0;
    transition: opacity 0.15s ease;
    vertical-align: middle;
    user-select: none;
  }

  :global(.prose h2:hover .heading-anchor),
  :global(.prose h3:hover .heading-anchor),
  :global(.prose h4:hover .heading-anchor) {
    opacity: 1;
  }

  :global(.heading-anchor:hover) {
    opacity: 1;
  }

  /* Touch devices: always show anchors at reduced opacity (no hover state) */
  @media (hover: none) {
    :global(.heading-anchor) {
      opacity: 0.4;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    :global(.heading-anchor) {
      transition: none;
    }
  }
</style>
```

**Step 2: Verify**

```bash
npm run lint
```

Expected: 0 errors.

**Step 3: Commit**

```bash
git add src/components/HeadingAnchors.astro
git commit -m "fix(a11y): mostrar heading anchors en dispositivos touch con opacidad reducida"
```

---

### Task 2: HeroSlider — botón de pausa (WCAG 2.2.2) + contador de slides

**Files:**

- Modify: `src/components/HeroSlider.astro`

**Context:** WCAG 2.1 SC 2.2.2 Level A requires a visible control to pause auto-updating content. Also adding a `[N/total]` counter so users know how many slides there are.

This task has three parts: (A) restructure the bottom controls HTML, (B) update CSS, (C) update JS.

---

**Part A — HTML changes**

The `<div class="slider-dots">` block (currently absolute-positioned by CSS) will move inside a new `<div class="slider-controls">` wrapper that also contains the counter and pause button.

Find the existing dots block in the template (currently after the two `slider-arrow` buttons):

```html
<div class="slider-dots" role="tablist" aria-label="Navegación del slider">
  {
    posts.map((_, i) => (
      <button
        class={`slider-dot${i === 0 ? ' active' : ''}`}
        role="tab"
        aria-selected={i === 0 ? 'true' : 'false'}
        aria-label={`Diapositiva ${i + 1}`}
        data-dot={i}
      />
    ))
  }
</div>
```

Replace it with:

```html
<div class="slider-controls">
  <span
    class="slider-counter"
    aria-live="polite"
    aria-atomic="true"
    aria-label={`Diapositiva 1 de ${posts.length}`}
  >[1/{posts.length}]</span>
  <div class="slider-dots" role="tablist" aria-label="Navegación del slider">
    {
      posts.map((_, i) => (
        <button
          class={`slider-dot${i === 0 ? ' active' : ''}`}
          role="tab"
          aria-selected={i === 0 ? 'true' : 'false'}
          aria-label={`Diapositiva ${i + 1}`}
          data-dot={i}
        />
      ))
    }
  </div>
  <button class="slider-pause" type="button" aria-label="Pausar autoplay" aria-pressed="false">
    [⏸]
  </button>
</div>
```

---

**Part B — CSS changes**

**Remove** the old `.slider-dots` rule (the one with `position: absolute`, `bottom: 1rem`, `left: 50%`, etc.).

**Add** these new rules in the `<style>` block, after the `.slider-dot` rules:

```css
/* Bottom controls bar */
.slider-controls {
  position: absolute;
  bottom: 1rem;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  z-index: 2;
  padding: 0 1rem;
}

.slider-dots {
  display: flex;
  gap: 0.5rem;
}

.slider-counter {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--color-text);
  background: var(--hero-arrow-bg);
  border: 1px solid var(--color-border);
  padding: 0.2rem 0.45rem;
  white-space: nowrap;
}

.slider-pause {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  background: var(--hero-arrow-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  padding: 0.2rem 0.45rem;
  cursor: pointer;
  transition:
    border-color 0.2s,
    color 0.2s;
  line-height: 1;
}

.slider-pause:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

@media (prefers-reduced-motion: reduce) {
  .slider-pause {
    display: none;
  }
}
```

In the existing `@media (max-width: 768px)` block, add:

```css
.slider-counter,
.slider-pause {
  display: none;
}
```

---

**Part C — JS changes**

Inside `setupHeroSlider()`, after the line `const nextBtn = slider.querySelector('.slider-next');`, add:

```typescript
const pauseBtn = slider.querySelector<HTMLButtonElement>('.slider-pause');
const counter = slider.querySelector<HTMLSpanElement>('.slider-counter');
let isPausedByUser = false;
```

In the `goTo()` function, add at the **end** of the function body (after the `dots.forEach` block):

```typescript
if (counter) {
  counter.textContent = `[${current + 1}/${total}]`;
  counter.setAttribute('aria-label', `Diapositiva ${current + 1} de ${total}`);
}
```

In `startAutoplay()`, add `if (isPausedByUser) return;` as the **second** line (after the `if (reducedMotion) return;` check):

```typescript
function startAutoplay() {
  if (reducedMotion) return;
  if (isPausedByUser) return; // ← add this line
  stopAutoplay();
  autoplayId = window.setInterval(next, 5000);
}
```

After the existing `dots.forEach(...)` event listener block, add:

```typescript
pauseBtn?.addEventListener('click', () => {
  isPausedByUser = !isPausedByUser;
  if (isPausedByUser) {
    stopAutoplay();
  } else {
    startAutoplay();
  }
  if (pauseBtn) {
    pauseBtn.textContent = isPausedByUser ? '[▶]' : '[⏸]';
    pauseBtn.setAttribute('aria-pressed', String(isPausedByUser));
    pauseBtn.setAttribute('aria-label', isPausedByUser ? 'Reanudar autoplay' : 'Pausar autoplay');
  }
});
```

**Step 2: Verify**

```bash
npm run lint
```

Expected: 0 errors. If there are TypeScript warnings about null checks, use optional chaining (`pauseBtn?.textContent = ...` — but note you can't assign to `?.`, so check the `if (pauseBtn)` guard is in place as written above).

**Step 3: Commit**

```bash
git add src/components/HeroSlider.astro
git commit -m "feat(a11y): añadir botón de pausa WCAG 2.2.2 y contador de slides en HeroSlider"
```

---

### Task 3: TableOfContents — fade indicator de overflow

**Files:**

- Modify: `src/components/TableOfContents.astro`

**Context:** The TOC sidebar has `max-height` and `overflow-y: auto`, but no visual cue when there's more content below the fold. Fix: wrap the desktop nav in a new `.toc-wrapper` scrollable div, keep the outer `<aside>` as `.toc-outer`, and use CSS + a small JS addition to show a fade gradient when overflow exists.

**Step 1: Restructure HTML**

Current outer element:

```html
<aside class="toc-wrapper" aria-label="Tabla de contenidos">
  <nav class="toc-desktop">...</nav>
  <details class="toc-mobile">...</details>
</aside>
```

New structure — rename `toc-wrapper` to `toc-outer` on the `<aside>`, add inner `<div class="toc-wrapper">` wrapping only the `<nav>`:

```html
<aside class="toc-outer" aria-label="Tabla de contenidos">
  <div class="toc-wrapper">
    <nav class="toc-desktop">... {/* unchanged content */}</nav>
  </div>
  <details class="toc-mobile">... {/* unchanged content */}</details>
</aside>
```

**Step 2: Update CSS**

Replace the old `.toc-wrapper` rule:

Old:

```css
.toc-wrapper {
  max-height: calc(100vh - var(--header-height) - 4rem);
  overflow-y: auto;
  font-size: 0.8125rem;
  line-height: 1.6;
}
```

New — split into outer + inner + fade:

```css
.toc-outer {
  position: relative;
  font-size: 0.8125rem;
  line-height: 1.6;
}

.toc-wrapper {
  max-height: calc(100vh - var(--header-height) - 4rem);
  overflow-y: auto;
}

/* Fade gradient shown when there is more content below */
.toc-outer::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 8px; /* leave space for scrollbar */
  height: 2.5rem;
  background: linear-gradient(to bottom, transparent, var(--color-bg));
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s;
}

.toc-outer.show-fade::after {
  opacity: 1;
}
```

**Step 3: Add JS to initScrollSpy()**

At the **beginning** of the `initScrollSpy()` function, before the existing IntersectionObserver setup, add:

```typescript
// Fade indicator: show when TOC has scrollable overflow
const tocOuter = document.querySelector<HTMLElement>('.toc-outer');
const tocWrapper = document.querySelector<HTMLElement>('.toc-wrapper');
if (tocOuter && tocWrapper) {
  const updateFade = () => {
    const hasMore = tocWrapper.scrollTop + tocWrapper.clientHeight < tocWrapper.scrollHeight - 4;
    tocOuter.classList.toggle('show-fade', hasMore);
  };
  updateFade();
  tocWrapper.addEventListener('scroll', updateFade, { passive: true });
}
```

**Step 4: Verify**

```bash
npm run lint
```

Expected: 0 errors.

**Step 5: Commit**

```bash
git add src/components/TableOfContents.astro
git commit -m "feat(ux): añadir indicador de overflow con fade en la sidebar TOC"
```

---

### Task 4: RelatedArticles — añadir tiempo de lectura

**Files:**

- Modify: `src/components/RelatedArticles.astro`

**Context:** Related article cards show category badge + title only. Adding reading time lets users decide if they want to click.

**Step 1: Import getReadingTime**

In the frontmatter (`---` block), add after the existing imports:

```html
import { getReadingTime } from '@utils/readingTime';
```

**Step 2: Add readingTime to the scored map**

The current `.map()` returns `{ post, baseScore, score }`. Extend to include `readingTime`:

```html
const scored = allPosts .filter((post) => post.id !== currentId) .map((post) => { const sharedTags =
post.data.tags.filter((tag) => currentTags.includes(tag)).length; const sameCategory =
post.data.category === currentCategory ? 1 : 0; const baseScore = sharedTags * TAG_SCORE_WEIGHT +
sameCategory; const daysSincePublished = (now.valueOf() - post.data.pubDate.valueOf()) / (1000 * 60
* 60 * 24); const recencyBoost = Math.max(0, 1 - daysSincePublished / RECENCY_DAYS) *
RECENCY_WEIGHT; const readingTime = getReadingTime(post.body || ''); // ← add this line return {
post, baseScore, score: baseScore + recencyBoost, readingTime }; // ← add readingTime }) .filter(({
baseScore }) => baseScore > 0) .sort((a, b) => b.score - a.score) .slice(0, MAX_RELATED);
```

**Step 3: Destructure readingTime in the template**

The scored.map() in the JSX currently uses `({ post })`. Change to `({ post, readingTime })`:

```html
{scored.map(({ post, readingTime }) => (
  <a href={`/blog/${post.id}`} class="related-card card-hover">
    {post.data.image && (
      <Image ... />
    )}
    <div class="related-content">
      <span class="badge badge-category">{post.data.category}</span>
      <h4>{post.data.title}</h4>
      <span class="related-time">{readingTime} min</span>
    </div>
  </a>
))}
```

**Step 4: Add CSS for `.related-time`**

In the `<style>` block, after `.related-content h4`:

```css
.related-time {
  font-size: 0.7rem;
  color: var(--color-text-muted);
}
```

**Step 5: Verify**

```bash
npm run lint
```

Expected: 0 errors.

**Step 6: Commit**

```bash
git add src/components/RelatedArticles.astro
git commit -m "feat(ux): mostrar tiempo de lectura en tarjetas de artículos relacionados"
```

---

### Task 5: index.astro — estética terminal en "ver todos"

**Files:**

- Modify: `src/pages/index.astro`

**Context:** The category section header has `<a href="...">Ver todos →</a>` which doesn't follow the terminal bracket convention used everywhere else.

**Step 1: Change the link text and add a class**

Find line 50 (approximately):

```html
<a href={`/categorias/${slugify(category)}`}>Ver todos →</a>
```

Replace with:

```html
<a href={`/categorias/${slugify(category)}`} class="cat-link">[ver todos →]</a>
```

**Step 2: Update CSS**

The existing CSS for `.category-header a` is:

```css
.category-header a {
  font-weight: 600;
  font-size: 0.9rem;
  white-space: nowrap;
}
```

Replace with (adds text-decoration override and hover color, keeping the same selector):

```css
.category-header .cat-link {
  font-weight: 600;
  font-size: 0.8125rem;
  white-space: nowrap;
  text-decoration: none;
  color: var(--color-primary);
  transition: color 0.2s;
}

.category-header .cat-link:hover {
  color: var(--color-accent);
}
```

**Step 3: Verify**

```bash
npm run lint
```

Expected: 0 errors.

**Step 4: Commit**

```bash
git add src/pages/index.astro
git commit -m "fix(ux): aplicar estética terminal [brackets] al enlace de categorías en homepage"
```

---

### Task 6: ArticleLayout — CTA de suscripción RSS

**Files:**

- Modify: `src/layouts/ArticleLayout.astro`

**Context:** Readers who finish an article have no visible way to subscribe to future content. Adding an RSS CTA in the article footer, between `<ShareButtons>` and `<AuthorCard>`.

**Step 1: Add the RSS CTA block in the template**

In `ArticleLayout.astro`, the `article-footer` section currently looks like:

```html
<footer class="article-footer" data-pagefind-ignore>
  <div class="article-tags">...</div>

  <ShareButtons title="{title}" url="{canonicalURL}" />

  {authorData && <AuthorCard author="{authorData}" />} ...
</footer>
```

Add the RSS block **between** `<ShareButtons>` and the `{authorData && ...}` line:

```html
<ShareButtons title="{title}" url="{canonicalURL}" />

<div class="rss-cta">
  <span class="rss-prompt">$ curl tengoping.com/rss.xml</span>
  <a href="/rss.xml" class="rss-link" aria-label="Suscribirse al feed RSS de tengoping.com">
    [suscribirse por RSS →]
  </a>
</div>

{authorData && <AuthorCard author="{authorData}" />}
```

**Step 2: Add CSS in the `<style>` block**

After the `.article-tags` rule in the `<style>` block:

```css
.rss-cta {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.rss-prompt {
  color: var(--color-primary);
  font-size: 0.8125rem;
}

.rss-link {
  font-size: 0.8125rem;
  font-weight: 600;
  text-decoration: none;
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  padding: 0.25rem 0.6rem;
  transition:
    color 0.2s,
    border-color 0.2s;
}

.rss-link:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
}
```

**Step 3: Verify**

```bash
npm run lint
```

Expected: 0 errors.

**Step 4: Commit**

```bash
git add src/layouts/ArticleLayout.astro
git commit -m "feat(ux): añadir CTA de suscripción RSS al pie de cada artículo"
```

---

### Task 7: global.css — print stylesheet

**Files:**

- Modify: `src/styles/global.css`

**Context:** Printing an article currently includes header, footer, TOC sidebar, share buttons, etc. Adding a print stylesheet that strips all navigation chrome and shows only the article content.

**Step 1: Append print rules at the end of global.css**

Add the following after the last existing rule (currently the `@media (prefers-reduced-motion: reduce)` block):

```css
/* ===== Print ===== */
@media print {
  .site-header,
  .site-footer,
  .search-terminal,
  .article-sidebar,
  .share-buttons,
  .rss-cta,
  .reading-progress-bar,
  .back-to-top,
  .article-nav,
  .related-articles,
  .giscus,
  .breadcrumbs,
  [data-pagefind-ignore]:not(article) {
    display: none !important;
  }

  .article-grid {
    grid-template-columns: 1fr !important;
  }

  body {
    background: #fff !important;
    color: #000 !important;
  }

  /* Show full URL for external links */
  a[href^='http']::after {
    content: ' (' attr(href) ')';
    font-size: 0.8em;
    color: #555;
    word-break: break-all;
  }

  .prose pre {
    white-space: pre-wrap;
    border: 1px solid #ccc;
  }
}
```

Note: The selectors exclude internal (`/`) and anchor (`#`) links from URL printing by only targeting `http` external links. The `[data-pagefind-ignore]:not(article)` exception keeps the article body visible (the `<article>` element has `data-pagefind-body` but the footer has `data-pagefind-ignore`).

**Step 2: Verify**

```bash
npm run lint
```

Expected: 0 errors.

**Step 3: Commit**

```bash
git add src/styles/global.css
git commit -m "feat(ux): añadir print stylesheet para imprimir artículos sin chrome de navegación"
```

---

## Final verification

After all 7 tasks:

```bash
npm run lint         # 0 errors, 0 warnings
npm run format:check # all files formatted
npm run build        # clean build, no type errors
```

If `npm run build` shows TypeScript errors in any of the modified files, fix the reported lines. Common issue: TypeScript may flag the `isPausedByUser` variable if `reducedMotion` is `const` inside `setupHeroSlider` — the variable is fine since it's a `const` assigned from `window.matchMedia(...).matches`.

---

## Code proposals for medium-difficulty items (do NOT implement automatically)

### Item 8: filename support in code blocks

Requires: add `data-title` extraction in `CopyCodeButton.astro` + document the markdown convention.

Convention to document: ``bash title="/etc/nginx/nginx.conf"`

```javascript
// In CopyCodeButton.astro initCopyButtons(), after langMatch extraction:
const titleMatch = code?.dataset.title || '';
const langLabel = document.createElement('span');
langLabel.textContent = titleMatch ? titleMatch : lang || 'code';
```

Astro passes fenced code block meta through `data-*` attributes on the `<code>` element when using remark/rehype plugins. Requires a rehype plugin to parse the meta string.

### Item 9: line numbers (opt-in)

Add to `astro.config.mjs` Shiki transformers:

```javascript
{
  name: 'line-numbers',
  pre(node) {
    // Only apply if the code block has a 'linenos' class
    if (!this.options.meta?.__raw?.includes('linenos')) return;
    node.properties['data-linenos'] = '';
  },
  line(node, line) {
    node.children.unshift({
      type: 'element',
      tagName: 'span',
      properties: { class: ['line-number'] },
      children: [{ type: 'text', value: String(line) }],
    });
  },
}
```

CSS:

```css
pre[data-linenos] .line-number {
  display: inline-block;
  width: 2.5rem;
  color: var(--color-text-muted);
  user-select: none;
  text-align: right;
  margin-right: 1rem;
  font-size: 0.75em;
}
```

Usage in markdown: ``bash linenos`

### Item 11: copy inline code

Requires wrapping all `<code>` elements not inside `<pre>` with a tooltip container. Complex due to the quantity of inline code in articles and the CSS needed for the tooltip.

### Item 12: keyboard shortcut legend

Add `<button class="shortcuts-help">[?]</button>` to `Header.astro` and a modal component. The modal content is static HTML. Medium effort (~60 lines JS + 30 lines CSS).
