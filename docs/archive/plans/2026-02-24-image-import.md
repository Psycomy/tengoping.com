# Image Import Script + Figure Component Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Script interactivo `scripts/import-image.py` para importar imágenes al blog (cualquier formato → WebP organizada por post, snippet Markdown listo para copiar) + componente `Figure.astro` con estética terminal.

**Architecture:** Dos piezas independientes: (1) componente Astro puro sin JS para renderizar imágenes con marco terminal usando CSS variables del proyecto; (2) script Python con flujo interactivo y funciones puras testeables por separado del I/O.

**Tech Stack:** Python 3 + Pillow (ya instalado), Astro 5, CSS custom properties del proyecto (`--color-border`, `--color-text-muted`, `--color-surface`, `--font-body`).

---

### Task 1: Componente Figure.astro

**Files:**

- Create: `src/components/Figure.astro`

**Step 1: Crear el componente**

```astro
---
interface Props {
  src: string;
  alt: string;
  caption?: string;
}

const { src, alt, caption } = Astro.props;
const filename = src.split('/').at(-1) ?? src;
---

<figure class="figure-block">
  <div class="figure-header">
    <span class="figure-title">$ {filename}</span>
  </div>
  <div class="figure-body">
    <img src={src} alt={alt} loading="lazy" decoding="async" />
  </div>
  {caption && <figcaption class="figure-caption">{caption}</figcaption>}
</figure>

<style>
  .figure-block {
    margin: 2rem 0;
    border: 1px solid var(--color-border);
    font-family: var(--font-body);
  }

  .figure-header {
    padding: 0.4rem 0.75rem;
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
  }

  .figure-title {
    font-size: 0.8rem;
    color: var(--color-text-muted);
  }

  .figure-body {
    padding: 1rem;
    background: var(--color-surface);
    text-align: center;
  }

  .figure-body img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
  }

  .figure-caption {
    padding: 0.5rem 0.75rem;
    font-size: 0.8rem;
    color: var(--color-text-muted);
    border-top: 1px solid var(--color-border);
    background: var(--color-surface);
    margin: 0;
  }
</style>
```

**Step 2: Verificar visualmente**

Abrir cualquier artículo `.mdx` existente y añadir temporalmente al final:

```mdx
import Figure from '@components/Figure.astro';

<Figure src="/images/og-default.png" alt="Prueba" caption="Pie de foto de prueba" />
<Figure src="/images/og-default.png" alt="Sin caption" />
```

Ejecutar `npm run dev` y comprobar en `localhost:4321` que:

- El marco aparece con borde sólido
- El header muestra `$ og-default.png`
- El caption aparece con la barra separadora
- Sin caption, no aparece la barra inferior
- Funciona en modo claro y oscuro (cambiar con el toggle del blog)

Revertir los cambios de prueba al `.mdx` antes de continuar.

**Step 3: Commit**

```bash
git add src/components/Figure.astro
git commit -m "feat: añadir componente Figure con estética terminal"
```

---

### Task 2: Tests del script import-image.py

**Files:**

- Create: `scripts/tests/__init__.py` (vacío)
- Create: `scripts/tests/test_import_image.py`

**Step 1: Crear carpeta de tests**

```bash
mkdir -p scripts/tests
touch scripts/tests/__init__.py
```

**Step 2: Escribir los tests**

Las funciones que se testean son las tres puras del script (sin I/O interactivo):

- `get_posts(content_dir)` → lista de slugs
- `convert_and_save(src_path, dest_path, max_width)` → guarda WebP, devuelve KB
- `build_snippet(image_public_path, alt, kind, caption)` → string Markdown

```python
# scripts/tests/test_import_image.py
import os
import sys
from pathlib import Path

import pytest
from PIL import Image

# Añadir scripts/ al path para poder importar import_image
sys.path.insert(0, str(Path(__file__).parent.parent))
import import_image


# ---------------------------------------------------------------------------
# get_posts
# ---------------------------------------------------------------------------

def test_get_posts_returns_slugs(tmp_path):
    """Devuelve los slugs de los .md y .mdx, ordenados, sin extensión."""
    (tmp_path / "configurar-ssh.md").write_text("---\ntitle: test\n---")
    (tmp_path / "fail2ban.mdx").write_text("---\ntitle: test\n---")
    (tmp_path / "borrador.md").write_text("---\ntitle: test\n---")

    result = import_image.get_posts(str(tmp_path))

    assert result == ["borrador", "configurar-ssh", "fail2ban"]


def test_get_posts_empty_dir(tmp_path):
    """Con carpeta vacía devuelve lista vacía."""
    result = import_image.get_posts(str(tmp_path))
    assert result == []


def test_get_posts_ignores_other_extensions(tmp_path):
    """Ignora archivos que no sean .md o .mdx."""
    (tmp_path / "notas.txt").write_text("hola")
    (tmp_path / "config.json").write_text("{}")

    result = import_image.get_posts(str(tmp_path))
    assert result == []


# ---------------------------------------------------------------------------
# convert_and_save
# ---------------------------------------------------------------------------

def _make_image(path: Path, width: int, height: int, fmt: str = "PNG") -> None:
    """Crea una imagen sintética de prueba."""
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    img.save(path, fmt)


def test_convert_and_save_creates_webp(tmp_path):
    """Convierte PNG a WebP y lo guarda en dest_path."""
    src = tmp_path / "foto.png"
    dest = tmp_path / "out" / "foto.webp"
    _make_image(src, 400, 300)

    import_image.convert_and_save(str(src), str(dest))

    assert dest.exists()
    img = Image.open(dest)
    assert img.format == "WEBP"


def test_convert_and_save_resizes_wide_image(tmp_path):
    """Imagen más ancha que max_width se redimensiona manteniendo proporción."""
    src = tmp_path / "grande.jpg"
    dest = tmp_path / "grande.webp"
    _make_image(src, 1200, 800, "JPEG")

    import_image.convert_and_save(str(src), str(dest), max_width=750)

    img = Image.open(dest)
    assert img.width == 750
    assert img.height == 500  # 800 * (750/1200) = 500


def test_convert_and_save_does_not_upscale(tmp_path):
    """Imagen más pequeña que max_width no se amplía."""
    src = tmp_path / "pequena.png"
    dest = tmp_path / "pequena.webp"
    _make_image(src, 400, 300)

    import_image.convert_and_save(str(src), str(dest), max_width=750)

    img = Image.open(dest)
    assert img.width == 400
    assert img.height == 300


def test_convert_and_save_creates_parent_dirs(tmp_path):
    """Crea carpetas intermedias si no existen."""
    src = tmp_path / "img.png"
    dest = tmp_path / "blog" / "mi-post" / "img.webp"
    _make_image(src, 200, 200)

    import_image.convert_and_save(str(src), str(dest))

    assert dest.exists()


def test_convert_and_save_returns_kb(tmp_path):
    """Devuelve el tamaño del archivo en KB (entero, ≥ 1)."""
    src = tmp_path / "img.png"
    dest = tmp_path / "img.webp"
    _make_image(src, 400, 300)

    kb = import_image.convert_and_save(str(src), str(dest))

    assert isinstance(kb, int)
    assert kb >= 1


# ---------------------------------------------------------------------------
# build_snippet
# ---------------------------------------------------------------------------

def test_build_snippet_simple():
    """Tipo 'simple' genera Markdown estándar."""
    result = import_image.build_snippet(
        "/images/blog/mi-post/foto.webp",
        alt="Mi foto",
        kind="simple",
    )
    assert result == "![Mi foto](/images/blog/mi-post/foto.webp)"


def test_build_snippet_figure_with_caption():
    """Tipo 'figure' genera tag <Figure> con caption."""
    result = import_image.build_snippet(
        "/images/blog/mi-post/foto.webp",
        alt="Mi foto",
        kind="figure",
        caption="Descripción de la imagen",
    )
    assert '<Figure' in result
    assert 'src="/images/blog/mi-post/foto.webp"' in result
    assert 'alt="Mi foto"' in result
    assert 'caption="Descripción de la imagen"' in result


def test_build_snippet_figure_without_caption():
    """Tipo 'figure' sin caption omite el atributo caption."""
    result = import_image.build_snippet(
        "/images/blog/mi-post/foto.webp",
        alt="Mi foto",
        kind="figure",
    )
    assert 'caption' not in result
```

**Step 3: Ejecutar tests para verificar que fallan**

```bash
cd /home/antonio/Documentos/blog
python -m pytest scripts/tests/test_import_image.py -v
```

Resultado esperado: `ModuleNotFoundError: No module named 'import_image'` — correcto, el script aún no existe.

---

### Task 3: Implementar import-image.py (funciones puras)

**Files:**

- Create: `scripts/import-image.py`

**Step 1: Escribir las funciones puras**

```python
#!/usr/bin/env python3
"""
Importa imágenes al blog: convierte a WebP, organiza por post y genera snippet Markdown.

Uso:
  python3 scripts/import-image.py ~/Descargas/mi-foto.jpg
"""

import math
import os
import sys
from pathlib import Path

from PIL import Image

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "src" / "content" / "blog"
PUBLIC_IMAGES_DIR = PROJECT_ROOT / "public" / "images" / "blog"
MAX_WIDTH = 750


# ---------------------------------------------------------------------------
# Funciones puras (testeables)
# ---------------------------------------------------------------------------

def get_posts(content_dir: str) -> list[str]:
    """Devuelve slugs de posts ordenados (sin extensión) desde content_dir."""
    p = Path(content_dir)
    slugs = sorted(
        f.stem for f in p.iterdir() if f.suffix in (".md", ".mdx")
    )
    return slugs


def convert_and_save(src_path: str, dest_path: str, max_width: int = MAX_WIDTH) -> int:
    """
    Convierte src_path a WebP, redimensiona si supera max_width y guarda en dest_path.
    Crea carpetas intermedias si no existen.
    Devuelve el tamaño del archivo guardado en KB.
    """
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(src_path).convert("RGB")

    if img.width > max_width:
        ratio = max_width / img.width
        new_height = math.floor(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    img.save(dest_path, "WEBP")

    kb = math.ceil(dest.stat().st_size / 1024)
    return max(kb, 1)


def build_snippet(
    image_public_path: str,
    alt: str,
    kind: str,
    caption: str | None = None,
) -> str:
    """
    Genera el snippet Markdown para insertar en el artículo.
    kind: 'simple' → Markdown estándar | 'figure' → componente <Figure>
    """
    if kind == "simple":
        return f"![{alt}]({image_public_path})"

    attrs = f'src="{image_public_path}" alt="{alt}"'
    if caption:
        attrs += f' caption="{caption}"'
    return f"<Figure {attrs} />"
```

**Step 2: Ejecutar tests**

```bash
python -m pytest scripts/tests/test_import_image.py -v
```

Resultado esperado: todos los tests en PASS.

**Step 3: Commit**

```bash
git add scripts/import-image.py scripts/tests/__init__.py scripts/tests/test_import_image.py
git commit -m "feat: añadir funciones puras de import-image con tests"
```

---

### Task 4: Implementar main() — flujo interactivo

**Files:**

- Modify: `scripts/import-image.py` — añadir función `main()` y bloque `if __name__ == "__main__"`

**Step 1: Añadir la función main() al final del archivo**

```python
# ---------------------------------------------------------------------------
# Flujo interactivo
# ---------------------------------------------------------------------------

def _ask_choice(prompt: str, options: list[str]) -> int:
    """Muestra opciones numeradas y devuelve el índice (0-based) elegido."""
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    while True:
        raw = input("→ ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(f"  Introduce un número entre 1 y {len(options)}")


def _slug_from_filename(filename: str) -> str:
    """Convierte nombre de archivo a slug sin extensión."""
    stem = Path(filename).stem
    return stem.replace(" ", "-").replace("_", "-").lower()


def _resolve_conflict(dest: Path) -> Path | None:
    """
    Gestiona conflicto de nombre. Devuelve la ruta final o None si se cancela.
    """
    while dest.exists():
        choice = _ask_choice(
            f"⚠  Ya existe: {dest.relative_to(PROJECT_ROOT)}",
            ["sobreescribir", "cambiar nombre", "cancelar"],
        )
        if choice == 0:  # sobreescribir
            return dest
        elif choice == 2:  # cancelar
            return None
        else:  # cambiar nombre
            new_name = input("\nNuevo nombre (sin extensión): ").strip()
            if not new_name:
                print("  El nombre no puede estar vacío.")
                continue
            dest = dest.parent / f"{new_name}.webp"
    return dest


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python3 scripts/import-image.py <ruta-imagen>")
        sys.exit(1)

    src_path = Path(sys.argv[1])
    if not src_path.exists():
        print(f"Error: no existe el archivo '{src_path}'")
        sys.exit(1)

    # Validar que Pillow puede abrir la imagen
    try:
        Image.open(src_path).verify()
    except Exception:
        print(f"Error: '{src_path.name}' no es una imagen válida")
        sys.exit(1)

    # Elegir post
    posts = get_posts(str(CONTENT_DIR))
    if not posts:
        print("Error: no se encontraron posts en src/content/blog/")
        sys.exit(1)

    post_idx = _ask_choice("¿A qué artículo pertenece esta imagen?", posts)
    post_slug = posts[post_idx]

    # Texto alternativo
    default_alt = _slug_from_filename(src_path.name).replace("-", " ")
    raw_alt = input(f"\nTexto alternativo [{default_alt}]: ").strip()
    alt = raw_alt if raw_alt else default_alt

    # Tipo de inserción
    kind_idx = _ask_choice(
        "Tipo de inserción:",
        ["imagen suelta", "figura con caption"],
    )
    kind = "simple" if kind_idx == 0 else "figure"

    caption: str | None = None
    if kind == "figure":
        caption = input("\nCaption: ").strip() or None

    # Destino
    stem = _slug_from_filename(src_path.name)
    dest = PUBLIC_IMAGES_DIR / post_slug / f"{stem}.webp"

    # Resolver conflicto si existe
    dest = _resolve_conflict(dest)
    if dest is None:
        print("Cancelado.")
        return

    # Convertir y guardar
    kb = convert_and_save(str(src_path), str(dest))
    public_path = "/" + str(dest.relative_to(PROJECT_ROOT / "public"))

    print(f"\n✓ {dest.relative_to(PROJECT_ROOT)} ({kb} KB)")
    print("\nCopia esto en tu .md" + ("x" if kind == "figure" else "") + ":\n")
    print(build_snippet(public_path, alt, kind, caption))

    if kind == "figure":
        print("\nNota: <Figure> requiere que el artículo sea .mdx, no .md")
        print("      Renombra el archivo si es necesario.")


if __name__ == "__main__":
    main()
```

**Step 2: Ejecutar los tests de regresión**

```bash
python -m pytest scripts/tests/test_import_image.py -v
```

Resultado esperado: todos en PASS (la función `main()` no afecta a las puras).

**Step 3: Prueba manual de extremo a extremo**

Descargar o usar cualquier imagen del sistema:

```bash
# Con una imagen existente del proyecto como ejemplo
python3 scripts/import-image.py public/images/antonio.png
```

Seguir el flujo interactivo y verificar:

- La imagen aparece en `public/images/blog/[slug-elegido]/antonio.webp`
- El snippet se imprime correctamente
- La imagen es WebP y tiene ≤ 750px de ancho (`file` o `identify` para comprobar)

Para probar el conflicto de nombre, ejecutar el mismo comando dos veces con la misma imagen.

**Step 4: Commit**

```bash
git add scripts/import-image.py
git commit -m "feat: añadir flujo interactivo a import-image.py"
```

---

### Task 5: Actualizar scripts/README.txt

**Files:**

- Modify: `scripts/README.txt`

**Step 1: Añadir sección para import-image.py**

Abrir `scripts/README.txt` y añadir al final:

```
--------------------------------------------------------------------------------
import-image.py — Importador de imágenes para artículos del blog
--------------------------------------------------------------------------------

Convierte cualquier imagen (JPG, PNG, GIF...) a WebP, la organiza en
public/images/blog/[slug-post]/ y genera el snippet Markdown para pegar
directamente en el artículo.

Uso:
  python3 scripts/import-image.py <ruta-imagen>

Ejemplo:
  python3 scripts/import-image.py ~/Descargas/diagrama.png

Flujo:
  1. Elige el artículo al que pertenece la imagen
  2. Escribe el texto alternativo (alt)
  3. Elige tipo: imagen suelta o figura con caption
  4. Si elige figura: escribe el caption
  5. Recibe el snippet listo para copiar en el .md / .mdx

Notas:
  - El componente <Figure> solo funciona en archivos .mdx, no en .md
  - Requiere: pip install Pillow
  - Tests: python -m pytest scripts/tests/ -v
```

**Step 2: Commit**

```bash
git add scripts/README.txt
git commit -m "docs: documentar import-image.py en scripts/README.txt"
```
