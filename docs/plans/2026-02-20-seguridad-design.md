# Diseño: Mejoras de seguridad — tengoping.com

**Fecha**: 2026-02-20
**Enfoque aprobado**: Opción B (equilibrada)
**Estado**: Aprobado para implementación

---

## 1. Contexto

Análisis de seguridad completo del blog Astro 5 (tengoping.com). El proyecto parte de una
base sólida: CSP hash-based, HSTS, X-Frame-Options, fuentes self-hosted, sin dependencias CDN
externas, y todos los `target="_blank"` con `rel="noopener noreferrer"`.

### Lo que ya funciona correctamente

- CSP hash-based en producción via `scripts/postbuild.mjs` (sin `unsafe-inline` para scripts)
- HSTS + X-Frame-Options + X-Content-Type-Options + `frame-ancestors 'none'`
- Fuentes JetBrains Mono self-hosted (sin Google Fonts)
- Todos los enlaces externos con `rel="noopener noreferrer"`
- Sin secretos ni variables de entorno expuestas
- 7 dependencias de producción, todas oficiales Astro/Sharp
- Validación Zod en content collections

---

## 2. Hallazgos

### 🔴 Alta prioridad

| ID   | Archivo             | Problema                                                                                            | CVE/Referencia                           |
| ---- | ------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| S-01 | `package-lock.json` | `devalue ≤5.6.2`: amplificación CPU/memoria por arrays dispersos + prototype pollution vía `uneval` | GHSA-33hq-fvwr-56pm, GHSA-8qm3-746x-r74r |

**Nota**: Para este blog estático sin islands/hidratación de componentes, `devalue` se usa
en build time, no en runtime con datos de usuario. Riesgo práctico bajo, pero CVE conocido
con fix disponible.

### 🟡 Media prioridad

| ID   | Archivo                        | Problema                                                                                                                                        | Dificultad |
| ---- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| S-02 | `scripts/postbuild.mjs`        | `style-src 'unsafe-inline'` debilita la CSP                                                                                                     | Media-alta |
| S-03 | `scripts/postbuild.mjs`        | `Permissions-Policy` incompleta — faltan `payment`, `usb`, `bluetooth`, `serial`, `accelerometer`, `gyroscope`, `camera` (chromium), `autoplay` | Fácil      |
| S-04 | `scripts/postbuild.mjs`        | HSTS sin directiva `preload`                                                                                                                    | Fácil      |
| S-05 | `scripts/postbuild.mjs`        | Falta header `X-Permitted-Cross-Domain-Policies: none`                                                                                          | Fácil      |
| S-06 | `src/layouts/BaseLayout.astro` | `meta name="generator"` expone versión exacta de Astro                                                                                          | Fácil      |

### 🟢 Nice to have

| ID   | Archivo                       | Problema                                                                     | Dificultad                                     |
| ---- | ----------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------- |
| S-07 | `src/components/Search.astro` | `container.innerHTML` con string hardcoded (no XSS real, pero mala práctica) | Fácil                                          |
| S-08 | `scripts/postbuild.mjs`       | Sin `report-to` en CSP para monitorización de violaciones                    | Media (requiere endpoint externo)              |
| S-09 | `scripts/postbuild.mjs`       | `img-src https:` demasiado amplio                                            | Difícil (posts pueden tener imágenes externas) |

---

## 3. Decisiones de diseño

### S-01: devalue CVE — npm audit fix

Acción: `npm audit fix` (non-breaking).

- `devalue 5.6.2 → 5.6.3`
- `astro` lock-file sync (5.17.2 → 5.17.3 en node_modules)
- No requiere cambios de código
- CI usa `--omit=dev --audit-level=moderate`, este fix elimina el único aviso de producción

### S-03: Permissions-Policy — expandir API browser restrictions

Añadir a `postbuild.mjs` en la directiva `Permissions-Policy`:

```
camera=(), microphone=(), geolocation=(), payment=(), usb=(),
bluetooth=(), serial=(), accelerometer=(), gyroscope=(),
magnetometer=(), ambient-light-sensor=(), autoplay=()
```

Esto sigue la especificación W3C Permissions Policy. No rompe funcionalidad del blog
(ninguna de estas APIs es usada).

### S-04: HSTS preload

Añadir `preload` al final del header HSTS:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

**Acción requerida post-deploy**: registrar `tengoping.com` en
[hstspreload.org](https://hstspreload.org) para que los navegadores lo incluyan en su lista
built-in. El header por sí solo no activa el preload — requiere registro manual.

### S-05: X-Permitted-Cross-Domain-Policies

Añadir header:

```
X-Permitted-Cross-Domain-Policies: none
```

Previene que Adobe Flash/Acrobat (y clientes similares) lean datos cross-domain desde este
origen. Riesgo teórico bajo pero header estándar de hardening.

### S-06: meta name="generator" — reducir info disclosure

Cambiar de `{Astro.generator}` (que produce `"Astro v5.17.3"`) a `"Astro"` sin versión.

Esto reduce el fingerprinting de versión exacta que podría usarse para identificar CVEs
específicos de la versión instalada.

### S-07: Search.astro innerHTML → createElement

```javascript
// Antes
container.innerHTML = '<p class="terminal-error">error: ...</p>';

// Después
const p = document.createElement('p');
p.className = 'terminal-error';
p.textContent = 'error: índice no encontrado. Ejecuta npm run build primero.';
const code = document.createElement('code');
code.textContent = 'npm run build';
p.appendChild(code);
container.appendChild(p);
```

### S-02: style-src 'unsafe-inline' — NO SE IMPLEMENTA AHORA

Eliminar `style-src 'unsafe-inline'` requeriría:

1. Auditar todos los `<style>` inline generados por Astro (componentes) y Shiki
   (syntax highlighting).
2. Convertir estilos de componentes a archivos CSS externos, o
3. Implementar nonces en el servidor (incompatible con site estático), o
4. Computar hashes SHA-256 de todos los `<style>` tags en `postbuild.mjs` (similar
   al sistema ya existente para `<script>`).

**La opción 4 es la más viable para este proyecto**. Código de referencia para
implementación futura:

```javascript
// En postbuild.mjs — extender collectInlineScriptHashes para styles también
function collectInlineStyleHashes(dir, hashes = new Set()) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      collectInlineStyleHashes(fullPath, hashes);
    } else if (entry.name.endsWith('.html')) {
      const html = readFileSync(fullPath, 'utf-8');
      const re = /<style(?![^>]*\bsrc\s*=)[^>]*>([\s\S]*?)<\/style>/gi;
      let match;
      while ((match = re.exec(html)) !== null) {
        const content = match[1];
        if (!content.trim()) continue;
        const hash = createHash('sha256').update(content, 'utf-8').digest('base64');
        hashes.add(`'sha256-${hash}'`);
      }
    }
  }
  return hashes;
}
```

Luego en `writeHeaders()`:

```javascript
const styleHashes = collectInlineStyleHashes(DIST);
const styleSrc = ["'self'", ...styleHashes].join(' ');
// Reemplazar 'unsafe-inline' en style-src con los hashes
```

**Riesgo**: si algún estilo inline varía en cada build (por ejemplo con timestamps),
los hashes fallarían. Requiere testing exhaustivo antes de desplegar en producción.

### S-08: CSP report-to — NO SE IMPLEMENTA AHORA

Requiere un endpoint para recibir los reportes (e.g. report-uri.com, o un worker
propio en Cloudflare). Fuera del alcance de este análisis.

---

## 4. Cambios a implementar automáticamente

| #   | Archivo                        | Cambio                                                |
| --- | ------------------------------ | ----------------------------------------------------- |
| 1   | `package-lock.json`            | `npm audit fix` → devalue 5.6.3                       |
| 2   | `scripts/postbuild.mjs`        | HSTS: añadir `; preload`                              |
| 3   | `scripts/postbuild.mjs`        | Permissions-Policy: añadir 9 APIs adicionales         |
| 4   | `scripts/postbuild.mjs`        | Añadir `X-Permitted-Cross-Domain-Policies: none`      |
| 5   | `public/_headers`              | Actualizar plantilla para reflejar los nuevos headers |
| 6   | `src/layouts/BaseLayout.astro` | `meta name="generator"` sin versión                   |
| 7   | `src/components/Search.astro`  | `innerHTML` → `createElement`                         |

---

## 5. Cambios NO implementados (requieren revisión manual)

| #    | Cambio                               | Motivo                                     |
| ---- | ------------------------------------ | ------------------------------------------ |
| S-02 | Eliminar `style-src 'unsafe-inline'` | Complejidad alta, riesgo de ruptura visual |
| S-08 | CSP report-to                        | Requiere endpoint externo                  |
| S-09 | Restringir `img-src`                 | Rompería imágenes externas en posts        |
