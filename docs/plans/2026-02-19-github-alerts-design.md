# GitHub Alerts — Design

**Fecha**: 2026-02-19
**Estado**: Aprobado

## Objetivo

Implementar callouts estilo GitHub Alerts en los artículos del blog, usando un plugin
remark local (sin dependencias externas) que procesa la sintaxis `> [!TIPO]` en
archivos `.md` y `.mdx`.

## Sintaxis de uso

```markdown
> [!NOTE]
> Esto es una nota informativa.

> [!TIP]
> Un consejo útil para el lector.

> [!IMPORTANT]
> Información clave que no debe ignorarse.

> [!WARNING]
> Precaución antes de continuar.

> [!CAUTION]
> Esto puede causar daños irreversibles.
```

## Archivos afectados

| Archivo                                | Acción                                  |
| -------------------------------------- | --------------------------------------- |
| `src/plugins/remark-github-alerts.mjs` | Crear — plugin remark local             |
| `src/styles/global.css`                | Modificar — añadir estilos `.callout-*` |
| `astro.config.mjs`                     | Modificar — registrar el plugin         |

## Flujo de transformación

```
.md / .mdx
  → remark-github-alerts
      1. Busca nodos blockquote cuyo primer párrafo empiece por [!TIPO]
      2. Elimina el marcador [!TIPO] del texto
      3. Añade atributo hast data-callout="tipo" al blockquote
      4. Inserta nodo párrafo con class="callout-title" y texto "## Título"
  → remark → rehype → HTML
  → CSS aplica estilos .callout-*
```

## HTML generado

```html
<blockquote class="callout callout-note">
  <p class="callout-title">## Nota</p>
  <p>Esto es una nota informativa.</p>
</blockquote>
```

## Tipos y estilos

| Tipo        | Título ES   | Borde     | Fondo       |
| ----------- | ----------- | --------- | ----------- |
| `note`      | Nota        | `#58D5A2` | verde 10%   |
| `tip`       | Consejo     | `#00BFFF` | azul 10%    |
| `important` | Importante  | `#A78BFA` | púrpura 10% |
| `warning`   | Advertencia | `#F59E0B` | ámbar 10%   |
| `caution`   | Peligro     | `#EF4444` | rojo 10%    |

Colores hardcoded (como HeroSlider/Search): no usan CSS vars del tema para
garantizar contraste independientemente del modo claro/oscuro.

Estructura visual: igual que `.prose blockquote` actual (borde izquierdo, padding,
sin border-radius), pero borde de `4px` de ancho y color según tipo.

## Criterios de éxito

- Blockquotes normales (sin `[!TIPO]`) no se ven afectados
- Los 5 tipos renderizan con su color y título en español
- Pasa `npm run lint`, `npm run build` y `astro check` sin errores
