# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev           # Dev server at localhost:4321
npm run build         # Production build to ./dist/ (also generates Pagefind search index)
npm run preview       # Preview production build locally
npm run lint          # ESLint (0 errors required)
npm run lint:fix      # ESLint --fix
npm run format        # Prettier --write
npm run format:check  # Prettier --check
```

Pagefind search only works after `npm run build` — it indexes the built HTML.

## Architecture

Astro 5 static blog in Spanish (es). Zero JS frameworks — all interactivity is vanilla JS in `<script>` tags. Terminal-inspired visual design: monospace font throughout (JetBrains Mono), sharp corners (border-radius: 0), solid borders instead of shadows.

**No View Transitions** — use the `setupFn(); document.addEventListener('astro:after-swap', setupFn);` pattern for script re-initialization, NOT `astro:page-load`.

### Content System

- **Content Collections** with glob loader: `src/content.config.ts` defines the `blog` collection loading `src/content/blog/*.{md,mdx}`
- Frontmatter validated via Zod schema: `title`, `description`, `author` (references an ID in `src/data/authors.json`), `pubDate`, `category`, `tags[]`, optional `image`, optional `draft`
- Posts filtered with `({ data }) => !data.draft` throughout all pages
- Reading time calculated in `src/utils/readingTime.ts` (200 words/min, min 1)
- GitHub-style callouts via local remark plugin `src/plugins/remark-github-alerts.mjs` — syntax: `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`

### Layout Hierarchy

`BaseLayout` → wraps every page (HTML shell, meta tags, OG/Twitter cards, JSON-LD, theme flash prevention script, self-hosted fonts, Header/Footer/Search). Accepts `section?: string` prop for article category meta and `canonicalOverride?: string` for paginated pages.

`ArticleLayout` → extends BaseLayout for blog posts (reading time, author lookup, sticky TOC sidebar, copy-code buttons, Giscus comments, prev/next nav). Uses a 3-column CSS grid (`1fr / 750px / 250px`) with sidebar sticky via `position: sticky` + `align-items: start` on the grid.

### Routing

- `/blog/[...page].astro` — paginated listing using Astro's `paginate()`, page size from `src/data/site.json` (`postsPerPage: 6`)
- `/blog/[id].astro` — individual posts with prev/next navigation
- `/categorias/[category].astro` and `/etiquetas/[tag].astro` — filtered listing pages; slugs are Unicode-normalized via `slugify()` in `src/utils/helpers.ts`
- `/autor/[id].astro` — author profile pages driven by `src/data/authors.json`

### Path Aliases

Defined in `tsconfig.json`: `@components/*`, `@layouts/*`, `@utils/*`, `@data/*`, `@styles/*` — all map to `src/` subdirectories.

### Theme System

- CSS custom properties in `src/styles/global.css` under `:root` (light) and `[data-theme='dark']` (dark)
- Light mode: primary `#1A73E8` (blue), accent `#FF6D00` (orange), bg `#F4F6F9`
- Dark mode: primary `#58D5A2` (green terminal), accent `#00BFFF` (electric blue), bg `#0D1117`
- Theme flash prevented by inline sync script in `<head>` that reads `localStorage.getItem('theme')` before paint
- Shiki code highlighting uses CSS variable-based dual themes (`github-light`/`github-dark`)
- HeroSlider and Search overlay use hardcoded dark colors (not CSS vars) — intentional for always-dark UI

### Terminal Design Conventions

- All text uses `--font-body: 'JetBrains Mono'` (monospace everywhere)
- `--radius-sm/md/lg` are all `0` — no rounded corners
- `--shadow-sm/md/lg` are all `none` — borders replace shadows
- Header logo: `root@tengoping:~$_` with blinking cursor
- Nav links prefixed with `./` (e.g., `./blog`, `./categorias`)
- Footer links in `[bracket]` format, copyright as shell echo command
- Prose headings have `::before` pseudo-elements with `## ` / `### ` markdown prefixes
- Code block headers show `$ ` prefix on language label, copy button text is `[copiar]`
- TOC uses tree characters (`├──`, `└──`, `│`)
- Badges are rectangular with solid borders (no border-radius)

### Pagefind Integration

Search uses `<script is:inline>` with dynamic `import('/pagefind/pagefind-ui.js')` to avoid Vite bundling the runtime-only Pagefind files. The `astro-pagefind` integration runs the indexer post-build. Content uses `data-pagefind-body` on article content and `data-pagefind-ignore` on nav/footer/TOC.

### Build Pipeline

`postbuild.mjs` runs after `astro build` and overwrites `public/_headers` with a CSP using real SHA-256 hashes of inline scripts. CSP uses hash-based `script-src` (no `'unsafe-inline'`). Fonts are self-hosted (no `fonts.googleapis.com` needed in CSP).

## Key Data Files

- `src/data/authors.json` — author profiles (id, name, avatar, bio, bioShort, social links); author `id` must match the `author` field in post frontmatter. Avatar WebP files live in `public/images/avatars/`.
- `src/data/site.json` — site-wide config (title, description, url, language, postsPerPage)
- `src/data/navigation.ts` — shared nav links arrays (`headerLinks`, `footerLinks`) used by Header and Footer components
