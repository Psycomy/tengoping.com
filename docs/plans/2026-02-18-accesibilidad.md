# Accesibilidad — Plan de Implementación

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Corregir cuatro gaps de accesibilidad confirmados: sin anuncio de resultados de búsqueda para lectores de pantalla, sin gestión de foco en menú móvil, sin descripción accesible en el input de búsqueda, y atributo `lang` incompleto.

**Architecture:** Tres cambios en componentes Astro existentes (`Search.astro`, `Header.astro`, `BaseLayout.astro`) — solo HTML y JS inline, sin dependencias nuevas. Cada task es independiente y puede hacerse en cualquier orden.

**Tech Stack:** Astro 5, vanilla JS, ARIA attributes, WCAG 2.1 AA

**Nota:** Los focus rings ya están implementados en `global.css` via `*:focus-visible`. Los `aria-hidden` del HeroSlider son correctos. Estos dos items del análisis original son falsos positivos.

---

## Task 1: `aria-live` en contador de resultados de búsqueda

Cuando Pagefind actualiza resultados, `#search-results-count` cambia su texto pero los screen readers no lo anuncian porque no hay `aria-live`. Añadir `aria-live="polite"` y `aria-atomic="true"` al span del contador.

**Files:**

- Modify: `src/components/Search.astro:39-42`

**Step 1: Leer el estado actual**

```bash
grep -n "search-results-count\|search-status\|aria-live" src/components/Search.astro
```

Expected: encontrar `id="search-results-count"` sin `aria-live`.

**Step 2: Añadir `aria-live` al span del contador**

En `src/components/Search.astro`, localizar el `<span>` con `id="search-results-count"` (dentro de `.terminal-status`, aproximadamente línea 40):

```html
<span class="status-results" id="search-results-count"></span>
```

Cambiarlo a:

```html
<span class="status-results" id="search-results-count" aria-live="polite" aria-atomic="true"></span>
```

**Step 3: Verificar lint**

```bash
cd /home/antonio/Documentos/blog && npm run lint
```

Expected: 0 errores.

**Step 4: Verificar con build**

```bash
npm run build 2>&1 | grep -E "error|warning" | grep -v "hint"
```

Expected: sin errores de build.

**Step 5: Commit**

```bash
git add src/components/Search.astro
git commit -m "a11y: añadir aria-live al contador de resultados de búsqueda"
```

---

## Task 2: `aria-describedby` en input de búsqueda

El input de búsqueda tiene `aria-label="Buscar artículos"` pero no tiene `aria-describedby` con instrucciones adicionales. Los screen readers se benefician de un texto de ayuda que explique el comportamiento del campo.

**Files:**

- Modify: `src/components/Search.astro`

**Step 1: Leer el estado actual del template HTML**

```bash
grep -n "terminal-body\|terminal-prompt\|aria-described\|search-help" src/components/Search.astro | head -20
```

Expected: encontrar `.terminal-body` sin `id="search-help"`.

**Step 2: Añadir el elemento de ayuda oculto al HTML**

En `src/components/Search.astro`, dentro del `<div class="terminal-body">` y antes del `<div class="terminal-prompt-line">` (aproximadamente línea 28-29), insertar:

```html
<div class="terminal-body">
  <span id="search-help" class="sr-only">
    Escribe para buscar artículos. Los resultados aparecen debajo del prompt.
  </span>
  <div class="terminal-prompt-line"></div>
</div>
```

La clase `sr-only` ya existe en `global.css` (visually hidden, accesible a screen readers).

**Step 3: Vincular el input al texto de ayuda en el JS**

En `src/components/Search.astro`, dentro del `<script is:inline>`, en la función `loadPagefind()`, en el `setTimeout` donde se accede al input (aproximadamente línea 73-83), añadir `setAttribute('aria-describedby', 'search-help')` junto al `aria-label` existente:

```js
setTimeout(function () {
  const input = document.querySelector('.pagefind-ui__search-input');
  if (input) {
    input.setAttribute('aria-label', 'Buscar artículos');
    input.setAttribute('aria-describedby', 'search-help');
    input.focus();
    input.addEventListener('input', function () {
      if (queryMirror) queryMirror.textContent = this.value;
      updateResultCount();
    });
  }
}, 100);
```

**Step 4: Verificar lint y build**

```bash
cd /home/antonio/Documentos/blog && npm run lint && npm run build 2>&1 | tail -3
```

Expected: lint 0 errores, build sin errores.

**Step 5: Commit**

```bash
git add src/components/Search.astro
git commit -m "a11y: añadir aria-describedby al input de búsqueda"
```

---

## Task 3: Gestión de foco en menú móvil

Cuando el usuario pulsa el botón hamburger en móvil, el menú se abre pero el foco no se mueve al primer enlace. Para usuarios de teclado/screen reader, el menú parece no responder. Además no hay tecla ESC para cerrar el menú móvil.

**Files:**

- Modify: `src/components/Header.astro`

**Step 1: Leer el estado actual del JS de Header**

```bash
grep -n "hamburger\|navMobile\|aria-expanded\|is-open\|focus\|Escape" src/components/Header.astro
```

Expected: ver el handler del hamburger sin `focus()` ni handler de `Escape`.

**Step 2: Actualizar la función `setupHeader` en el `<script>`**

Localizar la función `setupHeader()` en `src/components/Header.astro`. El bloque del hamburger actualmente es:

```js
const hamburger = document.querySelector('.hamburger');
const navMobile = document.querySelector('.nav-mobile');
hamburger?.addEventListener('click', () => {
  const expanded = hamburger.getAttribute('aria-expanded') === 'true';
  hamburger.setAttribute('aria-expanded', String(!expanded));
  navMobile?.classList.toggle('is-open');
});
```

Reemplazarlo con:

```js
const hamburger = document.querySelector < HTMLButtonElement > '.hamburger';
const navMobile = document.querySelector < HTMLElement > '.nav-mobile';

function openMobileNav() {
  hamburger?.setAttribute('aria-expanded', 'true');
  navMobile?.classList.add('is-open');
  // Mover foco al primer enlace del menú
  const firstLink = navMobile?.querySelector < HTMLAnchorElement > 'a';
  if (firstLink) setTimeout(() => firstLink.focus(), 50);
}

function closeMobileNav() {
  hamburger?.setAttribute('aria-expanded', 'false');
  navMobile?.classList.remove('is-open');
  hamburger?.focus();
}

hamburger?.addEventListener('click', () => {
  const expanded = hamburger.getAttribute('aria-expanded') === 'true';
  if (expanded) closeMobileNav();
  else openMobileNav();
});

// Cerrar con ESC cuando el menú móvil está abierto
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && navMobile?.classList.contains('is-open')) {
    closeMobileNav();
  }
});
```

**Step 3: Añadir `aria-controls` al hamburger para relación ARIA explícita**

En el HTML de `Header.astro`, el botón hamburger (aproximadamente línea 93-110) no tiene `aria-controls`. Añadir también `id` al `nav-mobile`:

Cambiar el botón hamburger:

```html
<button
  class="btn-icon hamburger"
  type="button"
  aria-label="Abrir menú"
  aria-expanded="false"
  aria-controls="nav-mobile"
></button>
```

Cambiar el `<nav class="nav-mobile">`:

```html
<nav class="nav-mobile" id="nav-mobile" aria-label="Navegación móvil"></nav>
```

**Step 4: Verificar TypeScript y lint**

```bash
cd /home/antonio/Documentos/blog && npx astro check 2>&1 | grep -E "error|Error" | grep -v "hint"
npm run lint
```

Expected: 0 errores en ambos comandos.

**Step 5: Verificar build**

```bash
npm run build 2>&1 | tail -3
```

Expected: build sin errores.

**Step 6: Commit**

```bash
git add src/components/Header.astro
git commit -m "a11y: gestión de foco en menú móvil — focus al abrir, ESC para cerrar, aria-controls"
```

---

## Task 4: `lang="es-ES"` en BaseLayout

El atributo `lang="es"` es válido pero `lang="es-ES"` es más específico y mejora la pronunciación en algunos screen readers (TTS engines). Es un cambio de una línea.

**Files:**

- Modify: `src/layouts/BaseLayout.astro`

**Step 1: Localizar el `<html>` tag**

```bash
grep -n "^<html" src/layouts/BaseLayout.astro
```

Expected: encontrar `<html lang="es"` en la primera línea del HTML (tras el frontmatter).

**Step 2: Cambiar `lang="es"` a `lang="es-ES"`**

En `src/layouts/BaseLayout.astro`, cambiar:

```html
<html lang="es" data-theme="light"></html>
```

por:

```html
<html lang="es-ES" data-theme="light"></html>
```

**Step 3: Verificar lint y build**

```bash
cd /home/antonio/Documentos/blog && npm run lint && npm run build 2>&1 | tail -3
```

Expected: 0 errores.

**Step 4: Commit**

```bash
git add src/layouts/BaseLayout.astro
git commit -m "a11y: lang=\"es-ES\" para mejor pronunciación en screen readers"
```

---

## Verificación Final

Después de todos los commits:

```bash
# Build completo
npm run build

# Lint
npm run lint

# Resumen de commits del área
git log --oneline -6
```

Expected:

- Build sin errores
- Lint 0 errores
- 4 commits de a11y presentes
