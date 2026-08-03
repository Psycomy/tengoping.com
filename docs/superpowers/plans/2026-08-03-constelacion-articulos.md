# Constelación de artículos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `/constelacion/`, a page that renders the blog's real internal links as an interactive force-directed graph (Obsidian-style), where hovering/tapping a node highlights its direct connections and clicking navigates to the article.

**Architecture:** At build time, a pure utility (`src/utils/graph.ts`) parses each post's raw markdown body for `](/blog/<slug>/)` links and builds a node/edge graph, embedding it as JSON in the page. A vanilla client-side `<script>` runs a small force simulation (repulsion + spring edges + gravity) until it converges, freezes, then draws to `<canvas>`. Hover/tap highlights neighbors; click navigates. No frameworks, no external physics library — matches the project's zero-JS-framework, CSP hash-based conventions.

**Tech Stack:** Astro 7 (page + frontmatter), TypeScript (utility + inline client script), `<canvas>` 2D context, vanilla DOM APIs. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-08-03-constelacion-articulos-design.md`

## Global Constraints

- Zero JS frameworks — all interactivity is vanilla JS/TS inside `<script>` tags (per CLAUDE.md).
- No View Transitions: every client script must follow `setupFn(); document.addEventListener('astro:after-swap', setupFn);` and clean up any `window`/`document`-level listener or observer it owns before re-attaching (canvas-attached listeners don't need manual cleanup — the canvas element itself is replaced on swap).
- CSP is hash-based, computed automatically by `scripts/postbuild.mjs` from whatever inline `<script>` content ends up in the built HTML — no manual hash list to maintain, but every new inline script must in fact stay inline (no `import` from `@utils/*` inside a client `<script>` — that pattern doesn't exist anywhere in this codebase; keep client scripts self-contained).
- No border-radius anywhere (`--radius-*: 0`), no shadows (`--shadow-*: none`), monospace font throughout — terminal design conventions apply to every new element (canvas wrapper, tooltip, fallback list).
- **This repo has no test framework** (confirmed: no vitest/jest/playwright in `package.json`, no `test` script). Do not add one. Where this plan says "write the failing test," it means a throwaway Node script using `node:assert` run directly via `node <script>.ts` — Node 24 (confirmed installed) strips TypeScript types natively, no flags needed. These scratch scripts live in the scratchpad directory, not in the repo, and are not committed.
- Verification for everything else follows the approved spec: `npm run lint` (0 errors), `npm run build` (must succeed, including postbuild's CSP hashing), and manual browser checks (light/dark theme, desktop + mobile viewport).
- Category → color mapping is computed at **build time** (in `graph.ts`) and embedded per-node in the JSON (`colorLight`/`colorDark`), so the client script never needs to import color logic — it just picks the right precomputed string based on the live theme attribute.

---

### Task 1: Graph data utility (`src/utils/graph.ts`)

**Files:**

- Create: `src/utils/graph.ts`
- Test: scratch-only, `/tmp/claude-1000/-home-antonio-Documentos-blog/1d6a43bf-5b6b-4c3d-bcbd-cf3acad31054/scratchpad/graph-test.ts` (not committed)

**Interfaces:**

- Produces (consumed by Task 2): `GraphNode { id: string; title: string; category: string; degree: number; colorLight: string; colorDark: string }`, `GraphEdge { source: string; target: string }`, `GraphData { nodes: GraphNode[]; edges: GraphEdge[] }`, `GraphPostInput { id: string; body: string; data: { title: string; category: string } }`, `buildGraph(posts: GraphPostInput[]): GraphData`, `extractLinkedSlugs(body: string): string[]`, `getCategoryColor(category: string, theme: 'light' | 'dark'): string`.

- [ ] **Step 1: Write the failing scratch test**

Create `/tmp/claude-1000/-home-antonio-Documentos-blog/1d6a43bf-5b6b-4c3d-bcbd-cf3acad31054/scratchpad/graph-test.ts`:

```ts
import assert from 'node:assert/strict';
import {
  extractLinkedSlugs,
  buildGraph,
  getCategoryColor,
} from '/home/antonio/Documentos/blog/src/utils/graph.ts';

// extractLinkedSlugs
assert.deepEqual(
  extractLinkedSlugs('ver [guía](/blog/foo-bar/) y también [otra](/blog/baz)').sort(),
  ['baz', 'foo-bar']
);
assert.deepEqual(extractLinkedSlugs('sin enlaces aquí'), []);
assert.deepEqual(extractLinkedSlugs('[dup](/blog/foo/) y de nuevo [dup](/blog/foo/)'), ['foo']);

// buildGraph
const posts = [
  { id: 'a', body: 'enlaza a [b](/blog/b/)', data: { title: 'A', category: 'Linux' } },
  { id: 'b', body: 'sin enlaces', data: { title: 'B', category: 'Redes' } },
  { id: 'c', body: 'enlace roto a [x](/blog/no-existe/)', data: { title: 'C', category: 'Linux' } },
];
const graph = buildGraph(posts);
assert.equal(graph.nodes.length, 3);
assert.equal(graph.edges.length, 1);
assert.deepEqual(graph.edges[0], { source: 'a', target: 'b' });

const nodeA = graph.nodes.find((n) => n.id === 'a');
const nodeB = graph.nodes.find((n) => n.id === 'b');
const nodeC = graph.nodes.find((n) => n.id === 'c');
assert.equal(nodeA?.degree, 1);
assert.equal(nodeB?.degree, 1);
assert.equal(nodeC?.degree, 0);

// getCategoryColor: estable para la misma categoría, distinto entre categorías
assert.equal(getCategoryColor('Linux', 'light'), getCategoryColor('Linux', 'light'));
assert.notEqual(getCategoryColor('Linux', 'light'), getCategoryColor('Redes', 'light'));

console.log('OK: todos los checks de graph.ts pasaron');
```

- [ ] **Step 2: Run it to verify it fails**

Run: `node /tmp/claude-1000/-home-antonio-Documentos-blog/1d6a43bf-5b6b-4c3d-bcbd-cf3acad31054/scratchpad/graph-test.ts`
Expected: fails with a module-not-found error (`src/utils/graph.ts` doesn't exist yet).

- [ ] **Step 3: Implement `src/utils/graph.ts`**

```ts
export interface GraphNode {
  id: string;
  title: string;
  category: string;
  degree: number;
  colorLight: string;
  colorDark: string;
}

export interface GraphEdge {
  source: string;
  target: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphPostInput {
  id: string;
  body: string;
  data: {
    title: string;
    category: string;
  };
}

// Orden fijo: determina el hue asignado a cada categoría en getCategoryColor.
// Una categoría nueva que no esté en esta lista simplemente cae en hue 0
// (comparte color con la primera) hasta que se añada aquí explícitamente.
const CATEGORY_ORDER = [
  'Linux',
  'Redes',
  'Seguridad',
  'Self-Hosting',
  'Automatización',
  'Virtualización',
  'Monitorización',
  'Hardware',
  'Software',
  'Opinión',
];

const BLOG_LINK_PATTERN = /\]\(\/blog\/([a-z0-9-]+)\/?\)/g;

export function extractLinkedSlugs(body: string): string[] {
  const slugs = new Set<string>();
  const pattern = new RegExp(BLOG_LINK_PATTERN);
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(body)) !== null) {
    slugs.add(match[1]);
  }
  return [...slugs];
}

export function getCategoryColor(category: string, theme: 'light' | 'dark'): string {
  const index = CATEGORY_ORDER.indexOf(category);
  const hue = index >= 0 ? (index * 36) % 360 : 0;
  const saturation = 65;
  const lightness = theme === 'dark' ? 68 : 40;
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

export function buildGraph(posts: GraphPostInput[]): GraphData {
  const validIds = new Set(posts.map((post) => post.id));
  const edgeKeys = new Set<string>();
  const edges: GraphEdge[] = [];
  const degree = new Map<string, number>();

  for (const post of posts) {
    const linkedSlugs = extractLinkedSlugs(post.body).filter(
      (slug) => slug !== post.id && validIds.has(slug)
    );

    for (const target of linkedSlugs) {
      const key = [post.id, target].sort().join('|');
      if (edgeKeys.has(key)) continue;
      edgeKeys.add(key);
      edges.push({ source: post.id, target });
      degree.set(post.id, (degree.get(post.id) ?? 0) + 1);
      degree.set(target, (degree.get(target) ?? 0) + 1);
    }
  }

  const nodes: GraphNode[] = posts.map((post) => ({
    id: post.id,
    title: post.data.title,
    category: post.data.category,
    degree: degree.get(post.id) ?? 0,
    colorLight: getCategoryColor(post.data.category, 'light'),
    colorDark: getCategoryColor(post.data.category, 'dark'),
  }));

  return { nodes, edges };
}
```

- [ ] **Step 4: Run the scratch test again to verify it passes**

Run: `node /tmp/claude-1000/-home-antonio-Documentos-blog/1d6a43bf-5b6b-4c3d-bcbd-cf3acad31054/scratchpad/graph-test.ts`
Expected: prints `OK: todos los checks de graph.ts pasaron`, exit code 0.

- [ ] **Step 5: Lint**

Run: `npm run lint`
Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add src/utils/graph.ts
git commit -m "feat(constelacion): añade utilidad de extracción de grafo de enlaces"
```

---

### Task 2: Page skeleton — `/constelacion/`

**Files:**

- Create: `src/pages/constelacion.astro`

**Interfaces:**

- Consumes: `buildGraph` from `@utils/graph` (Task 1).
- Produces (consumed by Task 4): a page containing `<canvas id="constellation-canvas">`, `<div id="graph-label" hidden>`, and `<script type="application/json" id="graph-data">` whose `textContent` is a JSON string matching `GraphData`.

- [ ] **Step 1: Create the page**

```astro
---
import BaseLayout from '@layouts/BaseLayout.astro';
import { getCollection } from 'astro:content';
import { buildGraph } from '@utils/graph';

const posts = await getCollection('blog', ({ data }) => !data.draft);

const graph = buildGraph(
  posts.map((post) => ({
    id: post.id,
    body: post.body ?? '',
    data: { title: post.data.title, category: post.data.category },
  }))
);

// Escapamos '<' para que un título con "</script>" no rompa el bloque JSON embebido.
const graphJson = JSON.stringify(graph).replace(/</g, '\\u003c');

const categorized = new Map<string, typeof posts>();
for (const post of [...posts].sort((a, b) => a.data.title.localeCompare(b.data.title))) {
  const existing = categorized.get(post.data.category) ?? [];
  existing.push(post);
  categorized.set(post.data.category, existing);
}
const categorizedEntries = [...categorized.entries()].sort((a, b) => a[0].localeCompare(b[0]));
---

<BaseLayout
  title="Constelación de artículos"
  description="Explora el blog como un grafo interactivo: cada nodo es un artículo, cada conexión es un enlace real que aparece en el propio contenido."
  section="Constelación"
>
  <section class="container page-section">
    <div class="page-header">
      <span class="meta-prompt">$ graph ./blog --edges=real</span>
      <h1>Constelación de artículos</h1>
      <p class="subtitle">
        Cada nodo es un artículo del blog. Cada línea es un enlace real que aparece en el propio
        contenido — no una relación calculada. Pasa el ratón (o toca en móvil) sobre un nodo para
        ver sus conexiones directas.
      </p>
    </div>

    <div class="graph-wrapper" data-pagefind-ignore>
      <canvas id="constellation-canvas"></canvas>
      <div class="graph-label" id="graph-label" hidden></div>
    </div>

    <section class="graph-fallback">
      <h2>Todos los artículos</h2>
      {
        categorizedEntries.map(([category, categoryPosts]) => (
          <div class="fallback-group">
            <h3>{category}</h3>
            <ul>
              {categoryPosts.map((post) => (
                <li>
                  <a href={`/blog/${post.id}/`}>{post.data.title}</a>
                </li>
              ))}
            </ul>
          </div>
        ))
      }
    </section>
  </section>

  <script type="application/json" id="graph-data" set:html={graphJson} />
</BaseLayout>

<style>
  .page-section {
    padding: 3rem 0 4rem;
  }

  .page-header {
    text-align: center;
    margin-bottom: 2rem;
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
    max-width: 640px;
    margin: 0 auto;
  }

  .graph-wrapper {
    position: relative;
    width: 100%;
    height: 60vh;
    min-height: 400px;
    max-height: 650px;
    border: 1px solid var(--color-border);
    background: var(--color-surface);
    margin-bottom: 3rem;
    overflow: hidden;
  }

  #constellation-canvas {
    display: block;
    width: 100%;
    height: 100%;
    cursor: default;
  }

  .graph-label {
    position: absolute;
    top: 0;
    left: 0;
    transform: translate(-50%, -140%);
    background: var(--color-bg);
    border: 1px solid var(--color-border);
    color: var(--color-text);
    padding: 0.25rem 0.5rem;
    font-size: 0.8125rem;
    white-space: nowrap;
    pointer-events: none;
    max-width: 280px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .graph-fallback h2 {
    font-size: 1rem;
    color: var(--color-text-muted);
    margin-bottom: 1.5rem;
  }

  .fallback-group {
    margin-bottom: 1.5rem;
  }

  .fallback-group h3 {
    font-size: 0.875rem;
    color: var(--color-primary);
    margin-bottom: 0.5rem;
  }

  .fallback-group ul {
    list-style: none;
    padding: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 0.25rem 1.5rem;
  }

  .fallback-group li {
    padding: 0.25rem 0;
  }

  @media (max-width: 768px) {
    .graph-wrapper {
      height: 50vh;
      min-height: 320px;
    }
  }
</style>
```

- [ ] **Step 2: Build and inspect the output**

Run: `npm run build`
Expected: succeeds. Then run:
`grep -o '<script type="application/json" id="graph-data">.\{0,80\}' dist/constelacion/index.html`
Expected: shows the start of a JSON object beginning `{"nodes":[...`.

Then: `grep -c '<li><a href="/blog/' dist/constelacion/index.html` (adjust the grep to however Astro serializes the `<li>`/`<a>` — check with a plain `grep -c 'fallback-group'` if the exact tag spacing doesn't match) — confirm the fallback list contains all 45 non-draft posts, grouped under the 10 known categories.

- [ ] **Step 3: Lint**

Run: `npm run lint`
Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add src/pages/constelacion.astro
git commit -m "feat(constelacion): añade página con grafo embebido y listado de respaldo"
```

---

### Task 3: Navigation entry

**Files:**

- Modify: `src/data/navigation.ts`

- [ ] **Step 1: Add the link to both nav arrays**

```ts
export const headerLinks = [
  { href: '/blog', label: './blog' },
  { href: '/categorias', label: './categorias' },
  { href: '/etiquetas', label: './etiquetas' },
  { href: '/constelacion', label: './constelacion' },
  { href: '/sobre-nosotros', label: './sobre-nosotros' },
];

export const footerLinks = [
  { href: '/constelacion', label: 'constelacion' },
  { href: '/privacidad', label: 'privacidad' },
  { href: '/terminos', label: 'terminos' },
];
```

- [ ] **Step 2: Verify in the dev server**

Run: `npm run dev`, open `http://localhost:4321/`, confirm `./constelacion` appears in the header nav and `constelacion` in the footer, and clicking it loads the page from Task 2.

- [ ] **Step 3: Lint**

Run: `npm run lint`
Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add src/data/navigation.ts
git commit -m "feat(constelacion): enlaza la constelación desde header y footer"
```

---

### Task 4: Force simulation and canvas rendering

**Files:**

- Modify: `src/pages/constelacion.astro` (insert a `<script>` block immediately after the `<script type="application/json" id="graph-data" ...>` line, still inside `</BaseLayout>`)

**Interfaces:**

- Consumes: DOM elements `#constellation-canvas`, `#graph-data`, `#graph-label` (Task 2); `GraphData`/`GraphNode` JSON shape (Task 1).
- Produces (consumed by Task 5): within `initConstellation()`'s scope — `nodes: SimNode[]`, `neighbors: Map<string, Set<string>>`, `canvas: HTMLCanvasElement`, `label: HTMLElement`, `let highlightId: string | null`, `render(): void`, constant `HIT_PADDING`.

- [ ] **Step 1: Add the simulation + rendering script**

Insert right after the `graph-data` script tag, still before `</BaseLayout>`:

```astro
<script>
  interface GraphNode {
    id: string;
    title: string;
    category: string;
    degree: number;
    colorLight: string;
    colorDark: string;
  }

  interface GraphEdge {
    source: string;
    target: string;
  }

  interface GraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
  }

  interface SimNode extends GraphNode {
    x: number;
    y: number;
    vx: number;
    vy: number;
    radius: number;
  }

  interface SimEdge {
    source: SimNode;
    target: SimNode;
  }

  const MIN_RADIUS = 4;
  const MAX_RADIUS = 12;
  const REPULSION = 2400;
  const SPRING_LENGTH = 90;
  const SPRING_STRENGTH = 0.02;
  const GRAVITY_STRENGTH = 0.0006;
  const DAMPING = 0.85;
  const CONVERGENCE_THRESHOLD = 0.2;
  const MAX_ITERATIONS = 500;
  const HIT_PADDING = 6;

  let rafId: number | null = null;
  let resizeHandler: (() => void) | null = null;
  let themeObserver: MutationObserver | null = null;

  function currentTheme(): 'light' | 'dark' {
    return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  function initConstellation(): void {
    const canvas = document.getElementById('constellation-canvas');
    const dataEl = document.getElementById('graph-data');
    const label = document.getElementById('graph-label');
    if (!(canvas instanceof HTMLCanvasElement) || !dataEl || !(label instanceof HTMLElement)) {
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    if (rafId !== null) cancelAnimationFrame(rafId);
    if (resizeHandler) window.removeEventListener('resize', resizeHandler);
    if (themeObserver) themeObserver.disconnect();

    let graph: GraphData;
    try {
      graph = JSON.parse(dataEl.textContent || '{"nodes":[],"edges":[]}') as GraphData;
    } catch {
      return;
    }
    if (graph.nodes.length === 0) return;

    let width = 0;
    let height = 0;

    function measure(): void {
      const rect = canvas.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
    }

    function applyDpr(): void {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    measure();
    applyDpr();

    const maxDegree = Math.max(1, ...graph.nodes.map((n) => n.degree));
    const nodesById = new Map<string, SimNode>();

    const nodes: SimNode[] = graph.nodes.map((n, i) => {
      const angle = (i / graph.nodes.length) * Math.PI * 2;
      const spread = Math.min(width, height) * 0.35;
      const node: SimNode = {
        ...n,
        x: width / 2 + Math.cos(angle) * spread,
        y: height / 2 + Math.sin(angle) * spread,
        vx: 0,
        vy: 0,
        radius: MIN_RADIUS + (MAX_RADIUS - MIN_RADIUS) * (n.degree / maxDegree),
      };
      nodesById.set(n.id, node);
      return node;
    });

    const edges: SimEdge[] = [];
    const neighbors = new Map<string, Set<string>>();
    for (const n of nodes) neighbors.set(n.id, new Set());

    for (const e of graph.edges) {
      const source = nodesById.get(e.source);
      const target = nodesById.get(e.target);
      if (!source || !target) continue;
      edges.push({ source, target });
      neighbors.get(source.id)?.add(target.id);
      neighbors.get(target.id)?.add(source.id);
    }

    function stepSimulation(): number {
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          let distSq = dx * dx + dy * dy;
          if (distSq < 1) distSq = 1;
          const dist = Math.sqrt(distSq);
          const force = REPULSION / distSq;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx += fx;
          a.vy += fy;
          b.vx -= fx;
          b.vy -= fy;
        }
      }

      for (const edge of edges) {
        const dx = edge.target.x - edge.source.x;
        const dy = edge.target.y - edge.source.y;
        const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        const displacement = dist - SPRING_LENGTH;
        const fx = (dx / dist) * displacement * SPRING_STRENGTH;
        const fy = (dy / dist) * displacement * SPRING_STRENGTH;
        edge.source.vx += fx;
        edge.source.vy += fy;
        edge.target.vx -= fx;
        edge.target.vy -= fy;
      }

      let totalMovement = 0;
      for (const node of nodes) {
        node.vx += (width / 2 - node.x) * GRAVITY_STRENGTH;
        node.vy += (height / 2 - node.y) * GRAVITY_STRENGTH;

        node.vx *= DAMPING;
        node.vy *= DAMPING;

        node.x += node.vx;
        node.y += node.vy;

        node.x = Math.max(node.radius, Math.min(width - node.radius, node.x));
        node.y = Math.max(node.radius, Math.min(height - node.radius, node.y));

        totalMovement += Math.abs(node.vx) + Math.abs(node.vy);
      }

      return totalMovement;
    }

    let highlightId: string | null = null;

    function render(): void {
      ctx.clearRect(0, 0, width, height);
      const theme = currentTheme();
      const highlightSet = highlightId
        ? new Set([highlightId, ...(neighbors.get(highlightId) ?? [])])
        : null;

      ctx.strokeStyle =
        getComputedStyle(document.documentElement).getPropertyValue('--color-border') || '#888888';
      for (const edge of edges) {
        const dimmed =
          highlightSet && !(highlightSet.has(edge.source.id) && highlightSet.has(edge.target.id));
        ctx.globalAlpha = dimmed ? 0.08 : 0.35;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(edge.source.x, edge.source.y);
        ctx.lineTo(edge.target.x, edge.target.y);
        ctx.stroke();
      }

      for (const node of nodes) {
        const dimmed = highlightSet && !highlightSet.has(node.id);
        ctx.globalAlpha = dimmed ? 0.25 : 1;
        ctx.fillStyle = theme === 'dark' ? node.colorDark : node.colorLight;
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.globalAlpha = 1;
    }

    function runSimulationLoop(): void {
      let iteration = 0;

      function frame(): void {
        const movement = stepSimulation();
        render();
        iteration += 1;
        if (movement > CONVERGENCE_THRESHOLD && iteration < MAX_ITERATIONS) {
          rafId = requestAnimationFrame(frame);
        } else {
          rafId = null;
        }
      }

      rafId = requestAnimationFrame(frame);
    }

    runSimulationLoop();

    resizeHandler = (() => {
      let resizeTimeout: ReturnType<typeof setTimeout> | undefined;
      return () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
          const prevWidth = width;
          const prevHeight = height;
          measure();
          applyDpr();
          const scaleX = prevWidth > 0 ? width / prevWidth : 1;
          const scaleY = prevHeight > 0 ? height / prevHeight : 1;
          for (const node of nodes) {
            node.x = Math.max(node.radius, Math.min(width - node.radius, node.x * scaleX));
            node.y = Math.max(node.radius, Math.min(height - node.radius, node.y * scaleY));
          }
          render();
        }, 150);
      };
    })();
    window.addEventListener('resize', resizeHandler);

    themeObserver = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.attributeName === 'data-theme') {
          render();
        }
      }
    });
    themeObserver.observe(document.documentElement, { attributes: true });
  }

  initConstellation();
  document.addEventListener('astro:after-swap', initConstellation);
</script>
```

- [ ] **Step 2: Manual verification in the browser**

Run: `npm run dev`, open `http://localhost:4321/constelacion/`.
Expected:

- ~45 colored dots appear inside the bordered box, spread out and settling into a stable layout within roughly a second (not collapsed into one clump, not flying off-screen).
- The isolated post (`por-que-este-blog`) sits visibly apart from the rest, unconnected.
- Toggle the theme switcher: node/edge colors update immediately.
- Resize the browser window: the graph reflows without errors in the console.

If the layout looks too clumped or too sparse, adjust `REPULSION`, `SPRING_LENGTH`, or `GRAVITY_STRENGTH` and reload until it reads clearly as a "constellation" — this is expected visual tuning, not a bug.

- [ ] **Step 3: Build and lint**

Run: `npm run build && npm run lint`
Expected: both succeed with 0 errors.

- [ ] **Step 4: Commit**

```bash
git add src/pages/constelacion.astro
git commit -m "feat(constelacion): añade simulación de fuerzas y render en canvas"
```

---

### Task 5: Hover / tap / click interaction

**Files:**

- Modify: `src/pages/constelacion.astro` (insert code inside `initConstellation()`, immediately before the `runSimulationLoop();` call added in Task 4 — after the `render()` function definition, so `render` and `highlightId` are already in scope)

**Interfaces:**

- Consumes (from Task 4, same function scope): `nodes: SimNode[]`, `neighbors: Map<string, Set<string>>`, `canvas: HTMLCanvasElement`, `label: HTMLElement`, `let highlightId`, `render(): void`, `HIT_PADDING`.

- [ ] **Step 1: Add interaction handling**

Insert immediately before the `runSimulationLoop();` call from Task 4 (after the `render()` function definition, still inside `initConstellation()`):

```ts
const pointerIsCoarse = window.matchMedia('(pointer: coarse)').matches;
let selectedId: string | null = null;

function findNodeAt(clientX: number, clientY: number): SimNode | null {
  const rect = canvas.getBoundingClientRect();
  const x = clientX - rect.left;
  const y = clientY - rect.top;
  let closest: SimNode | null = null;
  let closestDist = Infinity;
  for (const node of nodes) {
    const dx = node.x - x;
    const dy = node.y - y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist <= node.radius + HIT_PADDING && dist < closestDist) {
      closest = node;
      closestDist = dist;
    }
  }
  return closest;
}

function showLabel(node: SimNode, clientX: number, clientY: number): void {
  const rect = canvas.getBoundingClientRect();
  label.textContent = node.title;
  label.style.left = `${clientX - rect.left}px`;
  label.style.top = `${clientY - rect.top}px`;
  label.hidden = false;
}

function hideLabel(): void {
  label.hidden = true;
}

canvas.addEventListener('mousemove', (event) => {
  if (pointerIsCoarse) return;
  const node = findNodeAt(event.clientX, event.clientY);
  highlightId = node ? node.id : null;
  canvas.style.cursor = node ? 'pointer' : 'default';
  if (node) {
    showLabel(node, event.clientX, event.clientY);
  } else {
    hideLabel();
  }
  render();
});

canvas.addEventListener('mouseleave', () => {
  if (pointerIsCoarse) return;
  highlightId = null;
  hideLabel();
  canvas.style.cursor = 'default';
  render();
});

canvas.addEventListener('click', (event) => {
  const node = findNodeAt(event.clientX, event.clientY);

  if (!node) {
    selectedId = null;
    highlightId = null;
    hideLabel();
    render();
    return;
  }

  if (!pointerIsCoarse) {
    window.location.href = `/blog/${node.id}/`;
    return;
  }

  if (selectedId === node.id) {
    window.location.href = `/blog/${node.id}/`;
    return;
  }

  selectedId = node.id;
  highlightId = node.id;
  showLabel(node, event.clientX, event.clientY);
  render();
});
```

- [ ] **Step 2: Manual verification — desktop**

Run: `npm run dev`, open `/constelacion/` in a normal desktop browser window.
Expected: hovering near a node highlights it and its direct neighbors (rest dims), shows a label with the article title near the cursor, cursor becomes a pointer; clicking navigates straight to that article's `/blog/<slug>/` page.

- [ ] **Step 3: Manual verification — mobile/touch**

In Chrome DevTools, toggle device toolbar (any mobile device preset, which reports a coarse pointer).
Expected: first tap on a node highlights it + neighbors and shows the label (no navigation yet); a second tap on the _same_ node navigates to its article; tapping empty space clears the highlight.

- [ ] **Step 4: Build and lint**

Run: `npm run build && npm run lint`
Expected: both succeed with 0 errors.

- [ ] **Step 5: Commit**

```bash
git add src/pages/constelacion.astro
git commit -m "feat(constelacion): añade interacción hover/tap y navegación por click"
```

---

### Task 6: Final end-to-end verification

**Files:** none (verification only).

- [ ] **Step 1: Full build + lint + format check**

Run: `npm run lint && npm run format:check && npm run build`
Expected: all three succeed with 0 errors/warnings requiring fixes.

- [ ] **Step 2: CSP sanity check**

Run: `npm run preview`, open `http://localhost:4321/constelacion/` in a real browser, open DevTools → Console.
Expected: no Content-Security-Policy violation errors logged (confirms `postbuild.mjs` correctly hashed the new inline `<script>` blocks — this is automatic, there's no hash list to edit manually).

- [ ] **Step 3: Accessibility/no-JS fallback check**

In the same preview, view page source (`Ctrl+U` or `curl -s http://localhost:4321/constelacion/`) and confirm:

- The `.graph-wrapper` element has `data-pagefind-ignore`.
- The `.graph-fallback` section lists all 45 published articles as real `<a href="/blog/.../">` links, grouped under the 10 categories — this content is present in the raw HTML regardless of JS.

- [ ] **Step 4: Cross-check against the spec**

Re-read `docs/superpowers/specs/2026-08-03-constelacion-articulos-design.md` section by section and confirm each requirement has a corresponding implemented behavior (data source = real links only, color by category, size by degree, hover/tap/click behavior, isolated node handling, theme switching, Pagefind exclusion, nav entry). No further code changes expected at this step — this is a read-only cross-check.

- [ ] **Step 5: Commit (only if Step 4 surfaced fixes)**

If Step 4 required any fix, commit it separately with a message describing exactly what was missing. If nothing needed fixing, skip this step — there's nothing to commit.
