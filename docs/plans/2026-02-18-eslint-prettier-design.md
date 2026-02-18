# ESLint + Prettier Design

**Goal:** Añadir linting y formatting al proyecto con ESLint v9 flat config + Prettier, pre-commit hooks con husky + lint-staged, y steps de lint en CI.

**Approach:** ESLint v9 flat config (`eslint.config.mjs`) + Prettier como herramienta independiente. `eslint-config-prettier` desactiva las reglas de ESLint que conflictan con Prettier. `eslint-plugin-astro` añade reglas específicas de Astro.

## Paquetes

```
npm install -D eslint @eslint/js typescript-eslint eslint-plugin-astro eslint-config-prettier prettier prettier-plugin-astro husky lint-staged
```

## Ficheros nuevos

### `eslint.config.mjs`

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

### `.prettierrc`

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

### `.prettierignore`

```
dist/
.astro/
node_modules/
public/pagefind/
```

## Modificaciones

### `package.json` — scripts + lint-staged

```json
"scripts": {
  "dev": "astro dev",
  "build": "astro build && node scripts/postbuild.mjs",
  "preview": "astro preview",
  "astro": "astro",
  "lint": "eslint .",
  "lint:fix": "eslint . --fix",
  "format": "prettier --write .",
  "format:check": "prettier --check ."
},
"lint-staged": {
  "*.{ts,mjs,js}": ["eslint --fix", "prettier --write"],
  "*.astro": ["eslint --fix", "prettier --write"],
  "*.{json,css,md}": ["prettier --write"]
}
```

### `.github/workflows/ci.yml` — añadir steps de lint

Después del step "Type check":

```yaml
- name: Lint
  run: npm run lint

- name: Format check
  run: npm run format:check
```

### `src/components/RelatedArticles.astro` — eliminar import sin usar

Eliminar la línea: `import { slugify } from '@utils/helpers';`

## Husky setup

```bash
npx husky init
# Reemplazar contenido de .husky/pre-commit con:
npx lint-staged
```

## Notas

- Prettier formateará el código existente — puede haber cambios de estilo menores (trailing commas, quote style en CSS, etc.)
- Si alguna regla de ESLint da falsos positivos, se puede desactivar con `// eslint-disable-next-line`
- Los archivos JSON-LD inline (`<script type="application/ld+json">`) generarán hints de astro(4000) — ya conocidos, no errores
