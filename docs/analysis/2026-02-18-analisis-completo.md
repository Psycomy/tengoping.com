# Análisis Completo de Mejoras — tengoping.com

> Generado: 2026-02-18
> Propósito: Preservar el análisis de áreas de mejora para planificación futura.

---

## Estado General

El proyecto está **bien construido** — arquitectura sólida Astro 5, buenas convenciones, CI funcional. Las mejoras identificadas son refinamientos, no problemas críticos de funcionamiento.

---

## 1. Seguridad

> Plan de implementación: `docs/plans/2026-02-18-seguridad.md`

### Confirmado e implementado (no requiere acción)

- ✅ CSP hash-based en producción — `scripts/postbuild.mjs` calcula SHA-256 de inline scripts y escribe `dist/_headers` sin `'unsafe-inline'`
- ✅ X-Frame-Options, HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy

### Pendiente

| Severidad | Issue                                                                                                                                          | Archivo                               |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Alta      | `npm audit` no está en CI — vulnerabilidades de dependencias sin detección automática                                                          | `.github/workflows/ci.yml`            |
| Alta      | `public/_headers` (repo) tiene CSP débil con `'unsafe-inline'` — se sobreescribe en build pero confuso y riesgoso si alguien deploya sin build | `public/_headers`                     |
| Media     | CSP en `postbuild.mjs` incompleto — faltan `worker-src`, `base-uri`, `form-action`, `object-src`, `upgrade-insecure-requests`                  | `scripts/postbuild.mjs`               |
| Media     | Sin Dependabot — actualizaciones de dependencias manuales                                                                                      | `.github/dependabot.yml` (no existe)  |
| Baja      | SRI para Giscus — script dinámico, complejo de implementar. Ya mitigado por CSP que allowlistea `https://giscus.app`                           | `src/components/GiscusComments.astro` |
| Baja      | `'wasm-unsafe-eval'` en CSP — requerido por Pagefind WASM, difícil de eliminar                                                                 | `scripts/postbuild.mjs`               |

---

## 2. Accesibilidad

> Plan pendiente de implementación

| Severidad | Issue                                                                                          | Archivo                           |
| --------- | ---------------------------------------------------------------------------------------------- | --------------------------------- |
| Alta      | Sin `aria-live="polite"` en resultados de búsqueda                                             | `src/components/Search.astro`     |
| Alta      | Sin `focus-visible` rings visibles en botones (theme toggle, hamburger, flechas slider)        | `src/styles/global.css`           |
| Alta      | Sin gestión de focus en menú móvil — al abrir debería entrar el foco                           | `src/components/Header.astro`     |
| Media     | `aria-hidden` del HeroSlider usa string `'true'`/`'false'` — JS debería actualizar con boolean | `src/components/HeroSlider.astro` |
| Media     | Sin `aria-describedby` en input de búsqueda                                                    | `src/components/Search.astro`     |
| Media     | Slider dots usan solo color como indicador de estado activo (sin otro indicador)               | `src/components/HeroSlider.astro` |
| Baja      | `lang="es"` debería ser `lang="es-ES"` para screen readers                                     | `src/layouts/BaseLayout.astro`    |

---

## 3. SEO

> Plan pendiente de implementación

| Severidad | Issue                                                                                             | Archivo                                                                    |
| --------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Media     | Falta `og:image:alt` en Open Graph                                                                | `src/layouts/BaseLayout.astro`                                             |
| Media     | Sin canonical URL en páginas de categorías/tags con paginación (page 2, 3 = URLs duplicadas)      | `src/pages/categorias/[category].astro`, `src/pages/etiquetas/[tag].astro` |
| Media     | Páginas de categoría, tag y autor pueden no tener meta `description` si no se pasa explícitamente | varias páginas                                                             |
| Baja      | `author:section` meta tag faltante en artículos                                                   | `src/layouts/ArticleLayout.astro`                                          |

---

## 4. Performance

> Plan pendiente de implementación

| Severidad | Issue                                                                                                 | Archivo                            |
| --------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Media     | Sin Critical CSS inline — todo el CSS llega después del HTML, impacta FCP                             | `src/layouts/BaseLayout.astro`     |
| Media     | 4 pesos de fuente cargados (Regular, Medium, SemiBold, Bold) — se podría reducir con `font-synthesis` | `src/layouts/BaseLayout.astro`     |
| Media     | Sin skeleton/placeholder en ArticleCard durante carga lazy de imagen                                  | `src/components/ArticleCard.astro` |
| Media     | HeroSlider: `sizes="100vw"` demasiado genérico                                                        | `src/components/HeroSlider.astro`  |
| Baja      | Sin `prefers-reduced-motion` que detenga autoplay del slider                                          | `src/components/HeroSlider.astro`  |

---

## 5. CI/CD

> Algunas mejoras incluidas en plan de seguridad (npm audit, Dependabot)

| Severidad | Issue                                                                          | Archivo                    |
| --------- | ------------------------------------------------------------------------------ | -------------------------- |
| Media     | Sin Lighthouse en CI — no hay tracking automatizado de performance/SEO         | `.github/workflows/ci.yml` |
| Media     | Sin detección de broken links post-build                                       | `.github/workflows/ci.yml` |
| Baja      | Sin caché de node_modules en CI (aunque `actions/setup-node@v4` ya cachea npm) | `.github/workflows/ci.yml` |

---

## 6. Code Quality

| Severidad | Issue                                                                                      | Archivo                                |
| --------- | ------------------------------------------------------------------------------------------ | -------------------------------------- |
| Media     | Color hardcoded `rgba(26, 115, 232, 0.4)` en HeroSlider en lugar de `var(--color-primary)` | `src/components/HeroSlider.astro`      |
| Media     | Sin feedback visual en botón `[copiar]` de código (CopyCodeButton)                         | `src/components/CopyCodeButton.astro`  |
| Baja      | Magic numbers en scoring de RelatedArticles sin constantes nombradas                       | `src/components/RelatedArticles.astro` |

---

## 7. PWA

| Severidad | Issue                                                                              | Archivo                                        |
| --------- | ---------------------------------------------------------------------------------- | ---------------------------------------------- |
| Baja      | Sin notificación de nueva versión disponible (update detection)                    | `public/sw.js`, `src/layouts/BaseLayout.astro` |
| Baja      | `theme_color` en manifest hardcoded a dark — no responde a preferencia del usuario | `public/manifest.json`                         |
| Baja      | Sin shortcuts en manifest                                                          | `public/manifest.json`                         |

---

## Prioridades de Implementación Sugeridas

1. **Seguridad** — Semana 1 (plan disponible)
2. **Accesibilidad** — Semana 2 (crítico para usuarios con discapacidad)
3. **SEO** — Semana 3 (impacto en posicionamiento)
4. **Performance** — Semana 4 (impacto en Core Web Vitals)
5. **CI/CD adicional** — Semana 5 (Lighthouse, broken links)
6. **Code Quality + PWA** — Semana 6 (refinamientos)
