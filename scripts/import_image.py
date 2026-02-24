"""
import_image.py – Funciones puras para el script de importación de imágenes.

Uso del CLI: scripts/import-image.py  (archivo con guión, para el CLI)
Import Python: import import_image    (este archivo, con guión bajo)
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "src" / "content" / "blog"
PUBLIC_IMAGES_DIR = PROJECT_ROOT / "public" / "images" / "blog"
MAX_WIDTH = 750


def get_posts(content_dir: str) -> list[str]:
    """Devuelve slugs de posts ordenados (sin extensión) desde content_dir.

    Lee *.md y *.mdx de content_dir y devuelve los stems ordenados
    alfabéticamente.
    """
    base = Path(content_dir)
    stems = [
        p.stem
        for p in base.iterdir()
        if p.is_file() and p.suffix in {".md", ".mdx"}
    ]
    return sorted(stems)


def convert_and_save(src_path: str, dest_path: str, max_width: int = 750) -> int:
    """Convierte src_path a WebP, redimensiona si supera max_width.

    Crea carpetas intermedias. Devuelve el tamaño del archivo resultante
    en KB (entero, mínimo 1).
    """
    src = Path(src_path)
    dest = Path(dest_path)

    # Crear directorios intermedios si no existen
    dest.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(src)

    # Redimensionar solo si la imagen es más ancha que max_width
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    img.save(dest, "WEBP")

    size_bytes = dest.stat().st_size
    kb = max(1, size_bytes // 1024)
    return kb


def build_snippet(
    image_public_path: str,
    alt: str,
    kind: str,
    caption: str | None = None,
) -> str:
    """Genera el snippet Markdown/JSX para insertar la imagen en un post.

    kind='simple'  → '![alt](path)'
    kind='figure'  → '<Figure src="path" alt="alt" />'
                     o '<Figure src="path" alt="alt" caption="..." />'
                     si se proporciona caption.
    """
    if kind == "simple":
        return f"![{alt}]({image_public_path})"

    if kind == "figure":
        if caption is not None:
            return (
                f'<Figure src="{image_public_path}" alt="{alt}" caption="{caption}" />'
            )
        return f'<Figure src="{image_public_path}" alt="{alt}" />'

    raise ValueError(f"kind desconocido: {kind!r}. Usa 'simple' o 'figure'.")
