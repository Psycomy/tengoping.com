# Seguridad — Plan de Implementación

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reforzar la seguridad del blog cerrando cuatro gaps confirmados: CSP incompleto, archivo `_headers` de repo con CSP débil, sin `npm audit` en CI, y sin Dependabot.

**Architecture:** Tres cambios en archivos existentes (`postbuild.mjs`, `public/_headers`, `ci.yml`) más un archivo nuevo (`.github/dependabot.yml`). Sin dependencias externas nuevas.

**Tech Stack:** Node.js (postbuild script), GitHub Actions (CI), Cloudflare Pages (\_headers)

**Contexto previo:** `scripts/postbuild.mjs` ya genera un CSP hash-based en producción (SHA-256 de inline scripts). El archivo `public/_headers` en el repo es solo una plantilla que se sobrescribe en build — pero actualmente contiene un CSP débil con `'unsafe-inline'` que podría usarse por error.

---

## Task 1: Completar directivas CSP en `postbuild.mjs`

El CSP generado actualmente en `scripts/postbuild.mjs` (línea 66) omite directivas de defensa en profundidad.

**Files:**

- Modify: `scripts/postbuild.mjs:56-69`

**Step 1: Leer el estado actual**

```bash
cat scripts/postbuild.mjs
```

Confirmar que la función `writeHeaders` genera el CSP en la línea con `Content-Security-Policy:`.

**Step 2: Actualizar `writeHeaders` en `scripts/postbuild.mjs`**

Reemplazar el contenido de la función `writeHeaders` (líneas 56-70) con la versión expandida:

```js
function writeHeaders(hashes) {
  const scriptSrc = ["'self'", ...hashes, "'wasm-unsafe-eval'", 'https://giscus.app'].join(' ');

  const csp = [
    "default-src 'self'",
    `script-src ${scriptSrc}`,
    "style-src 'self' 'unsafe-inline'",
    "font-src 'self'",
    "img-src 'self' data: https:",
    'frame-src https://giscus.app',
    "connect-src 'self' https://giscus.app https://api.github.com",
    "worker-src 'self'",
    "manifest-src 'self'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
    'upgrade-insecure-requests',
  ].join('; ');

  const content = `/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-XSS-Protection: 0
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Content-Security-Policy: ${csp}
`;

  writeFileSync(join(DIST, '_headers'), content);
}
```

Cambios respecto a la versión anterior:

- `connect-src` ahora incluye `https://api.github.com` (Giscus lo necesita para la autenticación OAuth)
- Añadido `worker-src 'self'` — permite que el service worker se registre
- Añadido `manifest-src 'self'` — permite que el PWA manifest se cargue
- Añadido `base-uri 'self'` — previene inyección de tag `<base>` con origen externo
- Añadido `form-action 'self'` — aunque no hay forms, es defensa en profundidad
- Añadido `object-src 'none'` — deshabilita plugins Flash/Java (obsoletos, máxima seguridad)
- Añadido `upgrade-insecure-requests` — fuerza HTTPS para recursos cargados

**Step 3: Verificar que el build genera el CSP correcto**

```bash
npm run build 2>&1 | tail -5
cat dist/_headers
```

Expected: el CSP en `dist/_headers` contiene `worker-src 'self'`, `object-src 'none'`, `upgrade-insecure-requests` y NO contiene `'unsafe-inline'` en `script-src`.

**Step 4: Commit**

```bash
git add scripts/postbuild.mjs
git commit -m "security: ampliar directivas CSP — worker-src, object-src, base-uri, form-action, upgrade-insecure-requests"
```

---

## Task 2: Actualizar `public/_headers` para reflejar el CSP de producción

El archivo `public/_headers` en el repo tiene `'unsafe-inline'` en `script-src`. Aunque en producción se sobrescribe por `postbuild.mjs`, el archivo en el repo es confuso y riesgoso (podría desplegarse por error sin el build).

**Files:**

- Modify: `public/_headers`

**Step 1: Reemplazar el contenido de `public/_headers`**

Sustituir el contenido actual por una nota clara y un CSP estricto de fallback. El CSP de fallback usa solo las directivas que no dependen de hashes (los hashes se añaden en postbuild):

```
# IMPORTANTE: Este archivo es solo una plantilla en el repositorio.
# En producción, `npm run build` ejecuta `scripts/postbuild.mjs` que genera
# `dist/_headers` con hashes SHA-256 calculados de los inline scripts.
# NO editar manualmente — los cambios se perderán en el próximo build.
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-XSS-Protection: 0
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval' https://giscus.app; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data: https:; frame-src https://giscus.app; connect-src 'self' https://giscus.app https://api.github.com; worker-src 'self'; manifest-src 'self'; base-uri 'self'; form-action 'self'; object-src 'none'; upgrade-insecure-requests
```

Nota: este fallback NO tiene `'unsafe-inline'` en `script-src`. Sin los hashes, los inline scripts no ejecutarán (aceptable — es un archivo de emergencia, no para uso directo).

**Step 2: Verificar**

```bash
head -15 public/_headers
```

Expected: el archivo empieza con el comentario explicativo y el CSP no tiene `'unsafe-inline'` en `script-src`.

**Step 3: Verificar que el build sigue produciendo el archivo correcto**

```bash
npm run build 2>&1 | tail -5
grep "unsafe-inline" dist/_headers
```

Expected: `grep` no devuelve nada en `script-src` (el postbuild.mjs genera hashes en su lugar).

**Step 4: Commit**

```bash
git add public/_headers
git commit -m "security: actualizar public/_headers — eliminar unsafe-inline del fallback, añadir comentario de uso"
```

---

## Task 3: Añadir `npm audit` al CI

El pipeline de CI no verifica vulnerabilidades en dependencias. Un `npm audit` con nivel `moderate` detecta CVEs conocidos sin bloquear por issues menores.

**Files:**

- Modify: `.github/workflows/ci.yml`

**Step 1: Leer el CI actual**

```bash
cat .github/workflows/ci.yml
```

Identificar el step "Install dependencies" (actualmente antes de "Type check").

**Step 2: Añadir step de audit después de install**

Insertar después de `- name: Install dependencies` y antes de `- name: Type check`:

```yaml
- name: Security audit
  run: npm audit --audit-level=moderate
```

El archivo `ci.yml` quedaría:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    name: Lint, Check & Build
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 24
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Security audit
        run: npm audit --audit-level=moderate

      - name: Type check
        run: npx astro check

      - name: Lint
        run: npm run lint

      - name: Format check
        run: npm run format:check

      - name: Build
        run: npm run build
```

**Step 3: Verificar el audit localmente**

```bash
npm audit --audit-level=moderate
```

Expected: salida sin vulnerabilidades `moderate` o superiores. Si hay vulnerabilidades, resolverlas con `npm audit fix` antes de continuar.

**Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: añadir npm audit --audit-level=moderate al pipeline"
```

---

## Task 4: Configurar Dependabot para actualizaciones automáticas

Sin Dependabot, las actualizaciones de dependencias son manuales. Dependabot abre PRs automáticos semanales con las versiones más recientes.

**Files:**

- Create: `.github/dependabot.yml`

**Step 1: Crear `.github/dependabot.yml`**

```yaml
version: 2
updates:
  - package-ecosystem: 'npm'
    directory: '/'
    schedule:
      interval: 'weekly'
      day: 'monday'
      time: '09:00'
      timezone: 'Europe/Madrid'
    open-pull-requests-limit: 5
    labels:
      - 'dependencies'
    commit-message:
      prefix: 'chore'
      include: 'scope'
    ignore:
      # Ignorar major versions de Astro hasta review manual
      - dependency-name: 'astro'
        update-types: ['version-update:semver-major']
      - dependency-name: '@astrojs/*'
        update-types: ['version-update:semver-major']
```

Notas:

- `weekly` los lunes a las 9:00 Madrid para batching de PRs
- `open-pull-requests-limit: 5` evita spam de PRs
- Major versions de Astro ignoradas — requieren revisión manual por breaking changes
- `commit-message.prefix: "chore"` para seguir convenciones del repo

**Step 2: Verificar la sintaxis del archivo**

```bash
cat .github/dependabot.yml
```

Expected: YAML válido, sin errores de indentación.

**Step 3: Commit**

```bash
git add .github/dependabot.yml
git commit -m "ci: añadir Dependabot para actualizaciones automáticas de dependencias"
```

---

## Verificación Final

Después de todos los commits:

```bash
# Verificar que el build completo pasa sin errores
npm run build

# Verificar el CSP generado
cat dist/_headers

# Verificar el audit
npm audit --audit-level=moderate

# Verificar lint
npm run lint
```

Expected:

- `dist/_headers` contiene todas las nuevas directivas CSP y NO `'unsafe-inline'` en `script-src`
- `npm audit` limpio o con warnings informativos (no errores)
- `npm run lint` con 0 errores
