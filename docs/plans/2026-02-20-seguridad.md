# Mejoras de Seguridad — Opción B Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Aplicar 7 correcciones de seguridad fáciles y no-breaking sobre el blog Astro 5
(tengoping.com): fix CVE devalue, headers HTTP endurecidos, reducir info disclosure y
eliminar un `innerHTML` innecesario.

**Architecture:** Blog estático Astro 5 en Cloudflare Pages. Headers HTTP servidos por
`public/_headers` (plantilla en repo) que `npm run build` sobrescribe via
`scripts/postbuild.mjs` con CSP hash-based. No hay server-side ni unit tests — la
verificación es lint + astro check + build exitoso + inspección del `dist/_headers` generado.

**Tech Stack:** Astro 5, TypeScript, Node.js 24, Cloudflare Pages `_headers` format

---

## Contexto previo al plan

- Diseño aprobado: `docs/plans/2026-02-20-seguridad-design.md`
- Archivo de headers plantilla: `public/_headers` (NO editar a mano — lo sobrescribe postbuild)
- El archivo que genera los headers reales: `scripts/postbuild.mjs`
- Comandos de verificación: `npm run lint`, `npm run build`, `npx astro check`
- Resultado esperado tras build: `dist/_headers` con los nuevos headers

---

### Task 1: Actualizar devalue (CVE GHSA-33hq-fvwr-56pm, GHSA-8qm3-746x-r74r)

**Files:**

- Modify: `package-lock.json` (vía npm, no editar a mano)

**Paso 1: Ejecutar npm audit fix (non-breaking)**

```bash
cd /home/antonio/Documentos/blog
npm audit fix
```

Resultado esperado:

```
added 1 package, removed 1 package, changed 2 packages
devalue 5.6.2 → 5.6.3
```

**Paso 2: Verificar que el CVE está resuelto**

```bash
npm audit --omit=dev --audit-level=low
```

Resultado esperado: `found 0 vulnerabilities` (o solo avisos de devDependencies).

**Paso 3: Verificar que el build sigue funcionando**

```bash
npm run lint
```

Resultado esperado: 0 errors.

**Paso 4: Commit**

```bash
git add package-lock.json
git commit -m "fix(deps): actualizar devalue 5.6.2→5.6.3 (GHSA-33hq-fvwr-56pm, GHSA-8qm3-746x-r74r)"
```

---

### Task 2: Endurecer headers HTTP en postbuild.mjs

Tres cambios en `scripts/postbuild.mjs` dentro de la función `writeHeaders()`:

1. HSTS: añadir `; preload`
2. Permissions-Policy: ampliar con 6 APIs modernas
3. Nuevo header `X-Permitted-Cross-Domain-Policies: none`

**Files:**

- Modify: `scripts/postbuild.mjs` (función `writeHeaders`, lines 56-87)
- Modify: `public/_headers` (plantilla del repo — actualizar para reflejar los cambios)

**Paso 1: Editar scripts/postbuild.mjs**

Localizar la función `writeHeaders` y aplicar estos tres cambios:

**Cambio A — HSTS preload** (línea ~82):

```javascript
// ANTES:
'  Strict-Transport-Security: max-age=31536000; includeSubDomains\n',

// DESPUÉS:
'  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload\n',
```

**Cambio B — Permissions-Policy ampliada** (línea ~80):

```javascript
// ANTES:
'  Permissions-Policy: camera=(), microphone=(), geolocation=()\n',

// DESPUÉS:
'  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=(), serial=(), accelerometer=(), gyroscope=(), magnetometer=(), autoplay=()\n',
```

**Cambio C — X-Permitted-Cross-Domain-Policies** (añadir después de X-XSS-Protection):

```javascript
// AÑADIR esta línea tras '  X-XSS-Protection: 0\n':
'  X-Permitted-Cross-Domain-Policies: none\n',
```

**Código completo de la función `writeHeaders` actualizada** (para sustituir entera):

```javascript
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
    "frame-ancestors 'none'",
  ].join('; ');

  const content = `/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=(), serial=(), accelerometer=(), gyroscope=(), magnetometer=(), autoplay=()
  X-XSS-Protection: 0
  X-Permitted-Cross-Domain-Policies: none
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  Content-Security-Policy: ${csp}
`;

  writeFileSync(join(DIST, '_headers'), content);
}
```

**Paso 2: Actualizar plantilla public/\_headers**

El archivo `public/_headers` es solo una plantilla de referencia (postbuild la sobreescribe
en dist/). Actualizar igualmente para que el repo refleje los headers esperados:

```
# IMPORTANTE: Este archivo es una plantilla en el repositorio.
# `npm run build` ejecuta `scripts/postbuild.mjs` que sobrescribe
# `dist/_headers` con los hashes SHA-256 reales de los inline scripts.
# NO editar manualmente — los cambios se perderán en el próximo build.

/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=(), serial=(), accelerometer=(), gyroscope=(), magnetometer=(), autoplay=()
  X-XSS-Protection: 0
  X-Permitted-Cross-Domain-Policies: none
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval' https://giscus.app; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data: https:; frame-src https://giscus.app; connect-src 'self' https://giscus.app https://api.github.com; worker-src 'self'; manifest-src 'self'; base-uri 'self'; form-action 'self'; object-src 'none'; upgrade-insecure-requests; frame-ancestors 'none'
```

**Paso 3: Build y verificar dist/\_headers**

```bash
npm run build
```

Resultado esperado: build sin errores.

Verificar el archivo generado:

```bash
grep -E "Permissions-Policy|HSTS|X-Permitted" dist/_headers
```

Resultado esperado (las tres líneas deben aparecer):

```
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=(), serial=(), accelerometer=(), gyroscope=(), magnetometer=(), autoplay=()
  X-Permitted-Cross-Domain-Policies: none
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

**Paso 4: Lint y format check**

```bash
npm run lint && npm run format:check
```

Resultado esperado: 0 errors, 0 warnings sobre los archivos modificados.

**Paso 5: Commit**

```bash
git add scripts/postbuild.mjs public/_headers
git commit -m "security(headers): HSTS preload, Permissions-Policy ampliada, X-Permitted-Cross-Domain-Policies"
```

---

### Task 3: Reducir information disclosure — meta generator

**Files:**

- Modify: `src/layouts/BaseLayout.astro` (línea 64 aprox.)

**Paso 1: Localizar la línea**

En `src/layouts/BaseLayout.astro`, buscar:

```astro
<meta name="generator" content={Astro.generator} />
```

Esto produce en el HTML generado: `<meta name="generator" content="Astro v5.17.3" />`,
exponiendo la versión exacta de Astro.

**Paso 2: Sustituir por versión sin número**

```astro
<meta name="generator" content="Astro" />
```

Esto mantiene la semántica del tag (indica que el sitio está construido con Astro) sin
revelar la versión exacta.

**Paso 3: Verificar con astro check**

```bash
npx astro check
```

Resultado esperado: 0 errors (solo hints informativos sobre JSON-LD, son esperados).

**Paso 4: Commit**

```bash
git add src/layouts/BaseLayout.astro
git commit -m "security: eliminar versión de Astro del meta generator"
```

---

### Task 4: Eliminar innerHTML innecesario en Search.astro

**Files:**

- Modify: `src/components/Search.astro` (línea 95-100 aprox., dentro del bloque `.catch`)

**Paso 1: Localizar el bloque**

En `src/components/Search.astro`, dentro de la función `loadPagefind()`, el bloque `.catch`:

```javascript
.catch(function () {
  const container = document.getElementById('search-pagefind');
  if (container) {
    container.innerHTML =
      '<p class="terminal-error">error: índice no encontrado. Ejecuta <code>npm run build</code> primero.</p>';
  }
});
```

**Paso 2: Reemplazar con createElement**

```javascript
.catch(function () {
  const container = document.getElementById('search-pagefind');
  if (container) {
    const p = document.createElement('p');
    p.className = 'terminal-error';
    p.textContent = 'error: índice no encontrado. Ejecuta ';
    const code = document.createElement('code');
    code.textContent = 'npm run build';
    p.appendChild(code);
    p.appendChild(document.createTextNode(' primero.'));
    container.appendChild(p);
  }
});
```

El resultado HTML es idéntico al anterior pero generado sin `innerHTML`.

**Paso 3: Verificar lint**

```bash
npm run lint
```

Resultado esperado: 0 errors.

**Paso 4: Commit**

```bash
git add src/components/Search.astro
git commit -m "refactor(search): reemplazar innerHTML con createElement en mensaje de error"
```

---

### Task 5: Build final y verificación completa

**Paso 1: Lint completo**

```bash
npm run lint
```

Resultado esperado: 0 errors.

**Paso 2: Astro type check**

```bash
npx astro check
```

Resultado esperado: 0 errors (hints sobre JSON-LD son esperados y no bloquean CI).

**Paso 3: Format check**

```bash
npm run format:check
```

Resultado esperado: todos los archivos pasan.

**Paso 4: Build de producción**

```bash
npm run build
```

Resultado esperado:

- Build completo sin errores
- `postbuild: N script hashes, SW build ID: XXXXXX` en la salida

**Paso 5: Verificar dist/\_headers generado**

```bash
cat dist/_headers
```

Verificar que están presentes:

- `X-Permitted-Cross-Domain-Policies: none`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `Permissions-Policy:` con payment, usb, bluetooth, serial, etc.
- `script-src` con hashes SHA-256 (múltiples `'sha256-...'`)

**Paso 6: Verificar npm audit limpio (producción)**

```bash
npm audit --omit=dev --audit-level=moderate
```

Resultado esperado: 0 vulnerabilities en producción.

**Paso 7: Commit si no se hizo en pasos anteriores**

(Cada task ya tiene su propio commit — este paso es solo de verificación final.)

---

## Post-deploy: Acción manual requerida

Tras desplegar en producción, registrar el dominio en el HSTS Preload List:

1. Ir a https://hstspreload.org
2. Introducir `tengoping.com`
3. El header ya tiene la directiva `preload` — cumple los requisitos
4. Enviar la solicitud (puede tardar semanas en propagarse a todos los navegadores)

Esto es opcional pero completa la protección HSTS para usuarios que nunca han visitado el
sitio (primera visita directamente HTTPS en lugar de HTTP→redirect).

---

## Cambios explícitamente fuera del alcance de este plan

| Cambio                         | Motivo                                              | Referencia  |
| ------------------------------ | --------------------------------------------------- | ----------- |
| `style-src 'unsafe-inline'`    | Complejidad alta, riesgo de ruptura visual en Shiki | Diseño S-02 |
| CSP `report-to`                | Requiere endpoint externo                           | Diseño S-08 |
| `img-src` restringido          | Rompería imágenes en posts                          | Diseño S-09 |
| Modificar configuración Giscus | Explícitamente excluido por el usuario              | —           |
