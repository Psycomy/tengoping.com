"""
import_image.py – Funciones puras para el script de importación de imágenes.

Uso del CLI: scripts/import-image.py  (archivo con guión, para el CLI)
Import Python: import import_image    (este archivo, con guión bajo)
"""

from __future__ import annotations

import sys
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


def _resolve_conflict(dest: Path, project_root: Path) -> Path | None:
    """
    Gestiona conflicto de nombre. Devuelve la ruta final o None si se cancela.
    """
    while dest.exists():
        choice = _ask_choice(
            f"⚠  Ya existe: {dest.relative_to(project_root)}",
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
        print("Uso: python3 scripts/import_image.py <ruta-imagen>")
        sys.exit(1)

    src_path = Path(sys.argv[1])
    if not src_path.exists():
        print(f"Error: no existe el archivo '{src_path}'")
        sys.exit(1)

    # Validar que Pillow puede abrir la imagen
    try:
        with Image.open(src_path) as img:
            img.verify()
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
    dest = _resolve_conflict(dest, PROJECT_ROOT)
    if dest is None:
        print("Cancelado.")
        return

    # Convertir y guardar
    kb = convert_and_save(str(src_path), str(dest))
    public_path = "/" + str(dest.relative_to(PROJECT_ROOT / "public"))

    print(f"\n✓ {dest.relative_to(PROJECT_ROOT)} ({kb} KB)")
    ext = "x" if kind == "figure" else ""
    print(f"\nCopia esto en tu .md{ext}:\n")
    print(build_snippet(public_path, alt, kind, caption))

    if kind == "figure":
        print("\nNota: <Figure> requiere que el artículo sea .mdx, no .md")
        print("      Renombra el archivo si es necesario.")


if __name__ == "__main__":
    main()
