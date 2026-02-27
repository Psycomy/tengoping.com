<p align="center">
  <img src="public/images/logo-github.png" alt="root@tengoping:~$_" width="440">
</p>

<p align="center">
  Blog de tecnología, administración de sistemas y redes para profesionales IT.
</p>

<p align="center">
  <a href="https://tengoping.com">tengoping.com</a> ·
  <a href="https://tengoping.com/blog">Artículos</a> ·
  <a href="https://tengoping.com/categorias">Categorías</a>
</p>

---

## Stack

| Herramienta                      | Uso                                    |
| -------------------------------- | -------------------------------------- |
| [Astro 5](https://astro.build)   | Framework web estático                 |
| [MDX](https://mdxjs.com)         | Markdown con componentes               |
| [Pagefind](https://pagefind.app) | Búsqueda estática (~15KB)              |
| [Shiki](https://shiki.style)     | Resaltado de sintaxis con temas duales |
| [giscus](https://giscus.app)     | Comentarios vía GitHub Discussions     |
| [Claude](https://claude.ai)      | Asistencia en diseño y desarrollo      |

## Inicio rápido

```bash
# Clonar el repositorio
git clone https://github.com/Psycomy/tengoping.com.git
cd tengoping.com

# Instalar dependencias
npm install

# Servidor de desarrollo
npm run dev          # localhost:4321

# Build de producción
npm run build        # genera ./dist/

# Preview local
npm run preview
```

> La búsqueda (Pagefind) solo funciona tras ejecutar `npm run build`, ya que indexa el HTML generado.

## Variables de entorno (seguridad)

El script `scripts/postbuild.mjs` permite habilitar reporting de violaciones CSP de forma opcional:

- `CSP_REPORT_ENDPOINT` (opcional): URL HTTPS del endpoint receptor de reportes.
- `CSP_REPORT_GROUP` (opcional): nombre del grupo de reporting. Por defecto: `csp`.

Si `CSP_REPORT_ENDPOINT` no está definido (o no es una URL HTTPS válida), el build sigue funcionando y
se genera CSP sin `report-to`.

## Crear un artículo

Crea un archivo `.md` o `.mdx` en `src/content/blog/`:

```markdown
---
title: 'Título del artículo'
description: 'Descripción breve para SEO y tarjetas'
author: 'antonio'
pubDate: 2025-03-01
updatedDate: 2025-04-15
category: 'Linux'
tags: ['SSH', 'Seguridad']
image: '../../assets/images/mi-imagen.jpg'
draft: false
---

Contenido del artículo en Markdown...
```

### Frontmatter

| Campo         | Tipo     | Requerido | Descripción                                               |
| ------------- | -------- | --------- | --------------------------------------------------------- |
| `title`       | string   | Sí        | Título del artículo                                       |
| `description` | string   | Sí        | Descripción para SEO                                      |
| `author`      | string   | Sí        | ID del autor (ver `src/data/authors.json`)                |
| `pubDate`     | date     | Sí        | Fecha de publicación                                      |
| `updatedDate` | date     | No        | Fecha de última actualización (se muestra en el artículo) |
| `category`    | string   | Sí        | Categoría principal                                       |
| `tags`        | string[] | Sí        | Array de etiquetas                                        |
| `image`       | string   | No        | Ruta a imagen destacada                                   |
| `draft`       | boolean  | No        | `true` para ocultar el artículo                           |

## Añadir un autor

Edita `src/data/authors.json`:

```json
{
  "id": "nuevo-autor",
  "name": "Nombre Apellido",
  "avatar": "/images/nuevo-autor.svg",
  "bio": "Biografía completa del autor.",
  "bioShort": "Rol breve",
  "social": {
    "twitter": "https://twitter.com/usuario",
    "github": "https://github.com/usuario",
    "linkedin": "https://linkedin.com/in/usuario"
  }
}
```

## Comentarios

Los comentarios usan [giscus](https://giscus.app), que almacena las conversaciones en GitHub Discussions de este repositorio. La configuración está en `src/components/GiscusComments.astro`.

## Estructura del proyecto

```
src/
├── components/        # Header, Footer, ArticleCard, ShareButtons...
├── content/
│   └── blog/          # Artículos en Markdown/MDX
├── data/              # authors.json, site.json, navigation.ts
├── layouts/           # BaseLayout, ArticleLayout
├── pages/
│   ├── blog/          # Listado paginado + artículos individuales
│   ├── categorias/    # Páginas por categoría
│   ├── etiquetas/     # Páginas por etiqueta
│   └── autor/         # Páginas de autor
├── styles/            # CSS global (temas claro/oscuro)
├── utils/             # Helpers TypeScript
└── content.config.ts  # Schema de Content Collections

public/
├── fonts/             # JetBrains Mono (auto-alojada)
├── manifest.json      # PWA manifest
├── sw.js              # Service worker (cache-first assets, network-first HTML)
└── _headers           # Cabeceras de seguridad para Cloudflare Pages
```

## Funcionalidades

- **SEO**: OG images, RSS con enclosures, JSON-LD (BlogPosting, WebSite, Organization)
- **PWA**: manifest + service worker con estrategia de caché híbrida
- **Compartir**: botones nativos para Twitter/X, Telegram, WhatsApp, Reddit y LinkedIn
- **Seguridad**: cabeceras CSP, X-Frame-Options, Permissions-Policy vía `_headers`
- **Búsqueda**: indexación estática con Pagefind post-build
- **Comentarios**: giscus (GitHub Discussions)
- **Accesibilidad**: landmarks ARIA, navegación por teclado, breadcrumbs

## Tema y diseño

Inspirado en la estética de terminal:

- Tipografía monoespaciada (JetBrains Mono) en todo el sitio
- Sin bordes redondeados, sin sombras — bordes sólidos
- Encabezados con prefijos markdown (`## `, `### `)
- TOC con caracteres de árbol (`├──`, `└──`)
- Badges rectangulares, links en formato `[bracket]`
- Tema claro y oscuro con cambio automático

## Despliegue

El sitio se despliega automáticamente en **Cloudflare Pages** con cada push a `main`.

| Configuración    | Valor           |
| ---------------- | --------------- |
| Build command    | `npm run build` |
| Output directory | `dist`          |
| Node version     | `24`            |

## Hecho con Claude

Este blog ha sido diseñado y desarrollado con la asistencia de [Claude](https://claude.ai) de Anthropic, utilizando [Claude Code](https://claude.ai/code) como herramienta principal de desarrollo.

## Licencia

Contenido del blog bajo [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Código fuente bajo [MIT](LICENSE).

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Psycomy/tengoping.com)
