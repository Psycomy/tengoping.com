# ESLint + Prettier Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Añadir ESLint v9 + Prettier al blog Astro con pre-commit hooks (husky + lint-staged) y steps de lint en CI.

**Architecture:** ESLint v9 flat config (`eslint.config.mjs`) con plugins para TypeScript y Astro. Prettier como formatter independiente con `prettier-plugin-astro`. `eslint-config-prettier` desactiva las reglas de ESLint que conflictan con Prettier. Husky ejecuta lint-staged en pre-commit para lintear/formatear solo los archivos staged.

**Tech Stack:** eslint v9, @eslint/js, typescript-eslint, eslint-plugin-astro, eslint-config-prettier, prettier, prettier-plugin-astro, husky, lint-staged

---

### Task 1: Instalar paquetes

**Files:**

- Modify: `package.json` (devDependencies)
- Modify: `package-lock.json`

**Step 1: Instalar todos los paquetes de una vez**

```bash
npm install -D eslint @eslint/js typescript-eslint eslint-plugin-astro eslint-config-prettier prettier prettier-plugin-astro husky lint-staged
```

**Step 2: Verificar que se instalaron**

```bash
npm ls eslint prettier husky lint-staged --depth=0
```

Expected: lista con versiones de todos los paquetes sin errores.

**Step 3: Commit**

```bash
git add package.json package-lock.json
git commit -m "chore: instalar eslint, prettier, husky y lint-staged"
```

---

### Task 2: Crear eslint.config.mjs

**Files:**

- Create: `eslint.config.mjs`

**Step 1: Crear el fichero**

Contenido exacto de `eslint.config.mjs`:

```js
import js from '@eslint/js';
import ts from 'typescript-eslint';
import astro from 'eslint-plugin-astro';
import prettier from 'eslint-config-prettier';

export default [
  js.configs.recommended,
  ...ts.configs.recommended,
  ...astro.configs.recommended,
  prettier,
  {
    rules: {
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    },
  },
  {
    ignores: ['dist/', '.astro/', 'node_modules/'],
  },
];
```

Notas:

- `js.configs.recommended` — reglas base de JS
- `ts.configs.recommended` — reglas TypeScript (spread porque es array)
- `astro.configs.recommended` — reglas específicas de Astro (spread porque es array)
- `prettier` — desactiva reglas de ESLint que conflictan con Prettier (debe ir al final)
- `@typescript-eslint/no-unused-vars` en warn con `argsIgnorePattern: '^_'` — evita falsos positivos en parámetros prefijados con `_`
- `ignores` — no lintear build output ni tipos generados

**Step 2: Verificar que ESLint arranca sin error de config**

```bash
npx eslint --print-config src/utils/helpers.ts
```

Expected: JSON con la config efectiva (sin error de parseo).

**Step 3: Commit**

```bash
git add eslint.config.mjs
git commit -m "chore: añadir ESLint v9 flat config con plugins de TypeScript y Astro"
```

---

### Task 3: Crear .prettierrc y .prettierignore

**Files:**

- Create: `.prettierrc`
- Create: `.prettierignore`

**Step 1: Crear .prettierrc**

Contenido exacto (basado en el estilo actual del código: single quotes, semicolons, 2 spaces):

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "plugins": ["prettier-plugin-astro"],
  "overrides": [
    {
      "files": "*.astro",
      "options": { "parser": "astro" }
    }
  ]
}
```

**Step 2: Crear .prettierignore**

```
dist/
.astro/
node_modules/
public/pagefind/
```

**Step 3: Verificar que Prettier reconoce los ficheros Astro**

```bash
npx prettier --check src/components/Header.astro 2>&1 | head -5
```

Expected: alguna diferencia de formato (o "All matched files use Prettier code style!") — lo importante es que NO dé error de "No parser could be inferred".

**Step 4: Commit**

```bash
git add .prettierrc .prettierignore
git commit -m "chore: añadir configuración de Prettier con plugin para Astro"
```

---

### Task 4: Actualizar package.json — scripts + lint-staged

**Files:**

- Modify: `package.json`

**Step 1: Añadir scripts**

En la sección `"scripts"` de `package.json`, añadir después de `"astro": "astro"`:

```json
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
```

**Step 2: Añadir configuración de lint-staged**

Añadir al nivel raíz de `package.json` (al mismo nivel que `"scripts"`, `"dependencies"`, etc.):

```json
  "lint-staged": {
    "*.{ts,mjs,js}": ["eslint --fix", "prettier --write"],
    "*.astro": ["eslint --fix", "prettier --write"],
    "*.{json,css,md}": ["prettier --write"]
  }
```

**Step 3: Verificar que los scripts existen**

```bash
npm run lint -- --version
```

Expected: versión de ESLint sin error.

**Step 4: Commit**

```bash
git add package.json
git commit -m "chore: añadir scripts de lint/format y configuración de lint-staged"
```

---

### Task 5: Configurar husky

**Files:**

- Create: `.husky/pre-commit`

**Step 1: Inicializar husky**

```bash
npx husky init
```

Este comando crea `.husky/pre-commit` con contenido por defecto (`npm test`) y añade el script `"prepare": "husky"` en `package.json`.

**Step 2: Reemplazar contenido de .husky/pre-commit**

El fichero `.husky/pre-commit` debe contener exactamente:

```sh
npx lint-staged
```

(Reemplazar cualquier contenido previo del `npx husky init`.)

**Step 3: Verificar que husky está instalado**

```bash
cat .husky/pre-commit
```

Expected: `npx lint-staged`

**Step 4: Commit**

```bash
git add .husky/pre-commit package.json
git commit -m "chore: configurar husky con pre-commit hook para lint-staged"
```

---

### Task 6: Fix unused import en RelatedArticles.astro

**Files:**

- Modify: `src/components/RelatedArticles.astro:4`

**Step 1: Eliminar import sin usar**

Línea 4 actual:

```astro
import {slugify} from '@utils/helpers';
```

Eliminar esa línea. El componente no usa `slugify` en ningún sitio.

**Step 2: Verificar que el componente sigue funcionando**

```bash
npm run build 2>&1 | tail -5
```

Expected: `[build] Complete!` sin errores.

**Step 3: Commit**

```bash
git add src/components/RelatedArticles.astro
git commit -m "fix: eliminar import slugify sin usar en RelatedArticles"
```

---

### Task 7: Primera pasada de formato (Prettier en todo el codebase)

**Files:**

- Modify: múltiples ficheros (Prettier reformateará lo que no cumpla su config)

**Step 1: Ejecutar Prettier en todo el proyecto**

```bash
npm run format
```

Expected: lista de ficheros modificados. Prettier aplicará su estilo consistentemente.

**Step 2: Revisar los cambios**

```bash
git diff --stat
```

Revisar que los cambios son solo de formato (espacios, comillas, trailing commas, etc.) — no lógica.

**Step 3: Verificar que format:check pasa limpio**

```bash
npm run format:check
```

Expected: `All matched files use Prettier code style!` (sin diferencias pendientes).

**Step 4: Commit**

```bash
git add -A
git commit -m "style: aplicar formato de Prettier al codebase existente"
```

---

### Task 8: Primera pasada de lint (ESLint --fix en todo el codebase)

**Files:**

- Modify: múltiples ficheros (ESLint corregirá lo que pueda auto-fix)

**Step 1: Ejecutar lint:fix**

```bash
npm run lint:fix
```

Expected: ESLint corregirá automáticamente lo que pueda. Puede haber warnings residuales.

**Step 2: Verificar el estado de lint**

```bash
npm run lint 2>&1 | tail -20
```

Expected: 0 errors. Puede haber warnings — son aceptables (no bloquean CI).

**Step 3: Si hay errores (no warnings), corregirlos manualmente**

Los errores más probables:

- `@typescript-eslint/no-explicit-any` — cambiar `any` por el tipo concreto o `unknown`
- `no-undef` — import faltante
- Errores de `eslint-plugin-astro` — seguir la sugerencia del mensaje

**Step 4: Commit**

```bash
git add -A
git commit -m "style: aplicar eslint --fix al codebase existente"
```

---

### Task 9: Actualizar CI — añadir steps de lint y format:check

**Files:**

- Modify: `.github/workflows/ci.yml`

**Step 1: Añadir steps al workflow**

El fichero actual termina con:

```yaml
- name: Type check
  run: npx astro check
```

Añadir después:

```yaml
- name: Lint
  run: npm run lint

- name: Format check
  run: npm run format:check
```

**Step 2: Verificar la indentación del YAML**

```bash
cat .github/workflows/ci.yml
```

Confirmar que los nuevos steps tienen exactamente 6 espacios de indentación (igual que los existentes).

**Step 3: Commit y push**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: añadir steps de lint y format:check al workflow de GitHub Actions"
git push origin main
```

**Step 4: Verificar que el workflow pasa en GitHub Actions**

```bash
gh run list --repo Psycomy/tengoping.com --limit 1
```

Esperar a que el run complete y verificar que está en `completed / success`.

---

## Orden de ejecución

```
Task 1 → instalar paquetes
Task 2 → eslint.config.mjs
Task 3 → .prettierrc + .prettierignore
Task 4 → package.json scripts + lint-staged
Task 5 → husky
Task 6 → fix RelatedArticles import
Task 7 → primera pasada Prettier
Task 8 → primera pasada ESLint --fix
Task 9 → actualizar CI + push
```

Tasks 2-5 son independientes entre sí pero deben ir tras Task 1.
Tasks 7-8 deben ir tras Tasks 2-6.
Task 9 debe ir al final.
