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
    assert result == '<Figure src="/images/blog/mi-post/foto.webp" alt="Mi foto" caption="Descripción de la imagen" />'


def test_build_snippet_figure_without_caption():
    """Tipo 'figure' sin caption omite el atributo caption."""
    result = import_image.build_snippet(
        "/images/blog/mi-post/foto.webp",
        alt="Mi foto",
        kind="figure",
    )
    assert 'caption' not in result
