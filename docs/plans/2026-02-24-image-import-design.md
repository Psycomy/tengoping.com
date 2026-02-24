# Diseño: Script de importación de imágenes + componente Figure

**Fecha:** 2026-02-24
**Estado:** Aprobado

## Objetivo

Automatizar el proceso de incluir imágenes dentro de los artículos del blog:
convertir cualquier formato de imagen a WebP, organizarla en la carpeta correcta
y generar el snippet Markdown listo para pegar en el `.md`.

## Componentes

### 1. Script `scripts/import-image.py`

**Uso:**

```bash
python3 scripts/import-image.py ~/Descargas/mi-foto.jpg
```

**Flujo interactivo completo:**

1. Recibe la ruta de la imagen como argumento posicional
2. Valida que el archivo existe y es una imagen reconocida por Pillow
3. Lista los posts disponibles (leídos de `src/content/blog/*.{md,mdx}`) y pide al usuario que elija uno por número
4. Pide el texto alternativo (alt); por defecto: nombre del archivo sin extensión, con guiones en lugar de espacios
5. Pregunta el tipo de inserción:
   - `[1] imagen suelta` → genera Markdown estándar
   - `[2] figura con caption` → pide el texto del caption; genera `<Figure>` component
6. Convierte la imagen a WebP con Pillow, redimensiona a máx. 750 px de ancho manteniendo proporción
7. Destino: `public/images/blog/[slug-del-post]/[nombre].webp`
   - Crea la carpeta automáticamente si no existe
8. **Conflicto de nombre**: si ya existe un archivo con ese nombre, ofrece:
   - `[1] sobreescribir`
   - `[2] cambiar nombre` → pide nuevo nombre y vuelve a comprobar
   - `[3] cancelar` → sale sin hacer nada
9. Guarda la imagen y muestra confirmación con ruta y tamaño en KB
10. Imprime el snippet final para copiar

**Output imagen suelta:**

```
✓ public/images/blog/configurar-ssh/diagrama.webp (38 KB)

Copia esto en tu .md:

![Diagrama de red SSH](/images/blog/configurar-ssh/diagrama.webp)
```

**Output figura con caption:**

```
✓ public/images/blog/configurar-ssh/diagrama.webp (38 KB)

Copia esto en tu .md:

<Figure src="/images/blog/configurar-ssh/diagrama.webp"
        alt="Diagrama de red SSH"
        caption="Topología de red con túnel SSH activo" />
```

**Dependencias:**

- Pillow (ya requerido por `generate-images.py`)
- Sin dependencias adicionales

---

### 2. Componente `src/components/Figure.astro`

Renderiza una imagen con marco de estética terminal.

**Props:**
| Prop | Tipo | Requerido | Descripción |
|------|------|-----------|-------------|
| `src` | `string` | Sí | Ruta pública de la imagen |
| `alt` | `string` | Sí | Texto alternativo |
| `caption` | `string` | No | Pie de foto. Si se omite, no se renderiza la barra inferior |

**Aspecto visual:**

```
┌─ $ nombre-archivo.webp ─────────────────┐
│                                         │
│  [imagen]                               │
│                                         │
├─────────────────────────────────────────┤
│  Texto del caption                      │
└─────────────────────────────────────────┘
```

**Convenciones de diseño** (consistente con el resto del blog):

- Borde sólido `1px solid var(--color-border)`
- Fuente monospace (`var(--font-body)`)
- Título del header con prefijo `$ `
- Sin border-radius (igual que el resto del proyecto)
- Sin sombra (igual que el resto del proyecto)
- Caption en color `var(--color-text-muted)`

**Uso en `.md` / `.mdx`:**

```mdx
import Figure from '@components/Figure.astro';

<Figure
  src="/images/blog/configurar-ssh/diagrama.webp"
  alt="Diagrama de red SSH"
  caption="Topología de red con túnel SSH activo"
/>
```

> Nota: Los archivos `.md` estándar no soportan imports de componentes Astro.
> Para usar `<Figure>`, el artículo debe ser `.mdx`.
> Si el artículo es `.md`, usar imagen suelta (Markdown estándar).

---

## Estructura de carpetas resultante

```
public/
  images/
    blog/
      configurar-ssh/
        diagrama.webp
        captura-logs.webp
      fail2ban/
        arquitectura.webp
```

---

## Decisiones de diseño

| Decisión               | Alternativa considerada          | Motivo                                                         |
| ---------------------- | -------------------------------- | -------------------------------------------------------------- |
| Script separado        | Integrar en `generate-images.py` | Responsabilidades distintas; más fácil de mantener             |
| Pillow para conversión | ImageMagick (shell)              | Ya disponible; consistente con tooling existente               |
| Carpeta por artículo   | Todo en `public/images/blog/`    | Organización más clara; fácil de limpiar si se elimina un post |
| Interactivo puro       | Flags CLI (`--post`, `--type`)   | Flujo de uso ocasional; el usuario no necesita recordar flags  |
| Renombrar en conflicto | Solo sobreescribir               | Más flexible; evita pérdidas accidentales                      |
