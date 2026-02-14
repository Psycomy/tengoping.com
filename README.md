# `root@tengoping:~$` tengoping.com

```
$ cat /etc/motd

  Blog de tecnologia, administracion de sistemas y redes
  para profesionales IT.

  Construido con Astro 5 | Alojado en Cloudflare Pages
```

---

## Stack

| Herramienta | Uso |
|---|---|
| [Astro 5](https://astro.build) | Framework web estatico |
| [MDX](https://mdxjs.com) | Markdown con componentes |
| [Pagefind](https://pagefind.app) | Busqueda estatica (~15KB) |
| [Shiki](https://shiki.style) | Resaltado de sintaxis con temas duales |
| [giscus](https://giscus.app) | Comentarios via GitHub Discussions |
| [Claude](https://claude.ai) | Asistencia en diseno y desarrollo |

## Inicio rapido

```bash
# Clonar el repositorio
git clone https://github.com/Psycomy/tengoping.com.git
cd tengoping.com

# Instalar dependencias
npm install

# Servidor de desarrollo
npm run dev          # localhost:4321

# Build de produccion
npm run build        # genera ./dist/

# Preview local
npm run preview
```

> La busqueda (Pagefind) solo funciona tras ejecutar `npm run build`, ya que indexa el HTML generado.

## Crear un articulo

Crea un archivo `.md` o `.mdx` en `src/content/blog/`:

```markdown
---
title: "Titulo del articulo"
description: "Descripcion breve para SEO y tarjetas"
author: "antonio"
pubDate: 2025-03-01
updatedDate: 2025-04-15
category: "Linux"
tags: ["SSH", "Seguridad"]
image: "/images/mi-imagen.svg"
draft: false
---

Contenido del articulo en Markdown...
```

### Frontmatter

| Campo | Tipo | Requerido | Descripcion |
|---|---|---|---|
| `title` | string | Si | Titulo del articulo |
| `description` | string | Si | Descripcion para SEO |
| `author` | string | Si | ID del autor (ver `src/data/authors.json`) |
| `pubDate` | date | Si | Fecha de publicacion |
| `updatedDate` | date | No | Fecha de ultima actualizacion (se muestra en el articulo) |
| `category` | string | Si | Categoria principal |
| `tags` | string[] | Si | Array de etiquetas |
| `image` | string | No | Ruta a imagen destacada |
| `draft` | boolean | No | `true` para ocultar el articulo |

## Anadir un autor

Edita `src/data/authors.json`:

```json
{
  "id": "nuevo-autor",
  "name": "Nombre Apellido",
  "avatar": "/images/nuevo-autor.svg",
  "bio": "Biografia completa del autor.",
  "bioShort": "Rol breve",
  "social": {
    "twitter": "https://twitter.com/usuario",
    "github": "https://github.com/usuario",
    "linkedin": "https://linkedin.com/in/usuario"
  }
}
```

## Comentarios

Los comentarios usan [giscus](https://giscus.app), que almacena las conversaciones en GitHub Discussions de este repositorio. La configuracion esta en `src/components/GiscusComments.astro`.

## Estructura del proyecto

```
src/
├── components/        # Header, Footer, ArticleCard, ShareButtons...
├── content/
│   └── blog/          # Articulos en Markdown/MDX
├── data/              # authors.json, site.json, navigation.ts
├── layouts/           # BaseLayout, ArticleLayout
├── pages/
│   ├── blog/          # Listado paginado + articulos individuales
│   ├── categorias/    # Paginas por categoria
│   ├── etiquetas/     # Paginas por etiqueta
│   └── autor/         # Paginas de autor
├── styles/            # CSS global (temas claro/oscuro)
├── utils/             # Helpers TypeScript
└── content.config.ts  # Schema de Content Collections

public/
├── manifest.json      # PWA manifest
├── sw.js              # Service worker (cache-first assets, network-first HTML)
└── _headers           # Cabeceras de seguridad para Cloudflare Pages
```

## Funcionalidades

- **SEO**: OG images con dimensiones, RSS con enclosures, JSON-LD (BlogPosting, WebSite, Organization)
- **PWA**: manifest + service worker con estrategia de cache hibrida
- **Compartir**: botones nativos para Twitter/X, Telegram, WhatsApp, Reddit y LinkedIn
- **Seguridad**: cabeceras CSP, X-Frame-Options, Permissions-Policy via `_headers`
- **Busqueda**: indexacion estatica con Pagefind post-build
- **Comentarios**: giscus (GitHub Discussions)
- **Accesibilidad**: landmarks ARIA, navegacion por teclado, breadcrumbs

## Tema y diseno

Inspirado en la estetica de terminal:

- Tipografia monoespaciada (JetBrains Mono) en todo el sitio
- Sin bordes redondeados, sin sombras — bordes solidos
- Encabezados con prefijos markdown (`## `, `### `)
- TOC con caracteres de arbol (`├──`, `└──`)
- Badges rectangulares, links en formato `[bracket]`
- Tema claro y oscuro con cambio automatico

## Despliegue

El sitio se despliega automaticamente en **Cloudflare Pages** con cada push a `main`.

| Configuracion | Valor |
|---|---|
| Build command | `npm run build` |
| Output directory | `dist` |
| Node version | `20` |

## Hecho con Claude

Este blog ha sido disenado y desarrollado con la asistencia de [Claude](https://claude.ai) de Anthropic, utilizando [Claude Code](https://claude.ai/code) como herramienta principal de desarrollo.

## Licencia

Contenido del blog bajo [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Codigo fuente bajo [MIT](https://opensource.org/licenses/MIT).
