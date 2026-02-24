generate-images.py — Generador de imágenes de portada
=====================================================

Genera imágenes 800x500 con estética terminal (fondo oscuro, prompt
root@tengoping, árbol de ficheros) para los artículos del blog.
Cada categoría tiene un color de acento distinto.

Requisitos
----------
  Python 3 + Pillow
  pip install Pillow

  Fuente: DejaVu Sans Mono (incluida en la mayoría de distros Linux)
  Si no la tienes: sudo apt install fonts-dejavu-core

Modos de uso
------------
  # Genera todas las imágenes del catálogo ARTICLES
  python3 scripts/generate-images.py

  # Genera solo una imagen concreta del catálogo
  python3 scripts/generate-images.py fail2ban.jpg

  # Auto-genera desde frontmatter de los .md (solo las faltantes)
  python3 scripts/generate-images.py --auto

  # Auto-genera forzando sobreescritura
  python3 scripts/generate-images.py --auto --force

  # Modo interactivo: wizard para crear una imagen nueva
  python3 scripts/generate-images.py --new

  # Detecta imágenes huérfanas y faltantes
  python3 scripts/generate-images.py --check

  # Lista todas las entradas del catálogo
  python3 scripts/generate-images.py --list

Filtros
-------
  # Filtra por categoría (funciona con catálogo, --auto y --list)
  python3 scripts/generate-images.py --category Seguridad
  python3 scripts/generate-images.py --auto --category Linux

Modo --auto
-----------
  Lee los .md de src/content/blog/, parsea el frontmatter y genera
  imágenes automáticamente:

  - Filename: se extrae del campo image del frontmatter
  - Título: palabras significativas del título, en mayúsculas
  - Subtítulo: description truncado a ~45 chars
  - Categoría: campo category → color de acento
  - Tree items: generados a partir de los tags[]

  Si el filename coincide con una entrada del catálogo ARTICLES,
  se usa esa entrada manual como override.

  Por defecto solo genera las que faltan. Con --force regenera todas.

Modo --check
------------
  Compara las imágenes referenciadas en frontmatter vs las existentes
  en public/images/. Reporta:

  - Faltantes: referenciadas en frontmatter pero no existen en disco
  - Huérfanas: existen en disco pero ningún post las referencia
  - Posts sin campo image en el frontmatter

Modo --new
----------
  Wizard interactivo que pregunta paso a paso:
  1. Nombre del fichero
  2. Título (texto grande)
  3. Subtítulo (texto pequeño)
  4. Categoría (menú numerado)
  5. Tree items (3 líneas)

Añadir una imagen al catálogo manual
-------------------------------------
  1. Abre scripts/generate-images.py

  2. Añade una entrada a la lista ARTICLES:

     ("mi-imagen.jpg", "TÍTULO", "subtítulo", "Categoría",
      ["├── item1", "├── item2", "└── item3"]),

  3. Si la categoría es nueva, añade su color a CAT_COLORS:

     "MiCategoría": "#HEXCOLOR",

  4. Ejecuta el script:

     python3 scripts/generate-images.py mi-imagen.jpg

  5. Referencia la imagen en el frontmatter del artículo:

     image: "/images/mi-imagen.jpg"

Colores por categoría
---------------------
  Automatización   #00BFFF  (azul eléctrico)
  Linux            #58D5A2  (verde terminal)
  Opinión          #FF6D00  (naranja)
  Redes            #1A73E8  (azul)
  Virtualización   #A78BFA  (morado)
  Seguridad        #F87171  (rojo)
  Self-Hosting     #34D399  (verde)
  Hardware         #FBBF24  (amarillo)
  Software         #C084FC  (violeta)
  Monitorización   #F472B6  (rosa)

--------------------------------------------------------------------------------
import_image.py — Importador de imágenes para artículos del blog
--------------------------------------------------------------------------------

Convierte cualquier imagen (JPG, PNG, GIF...) a WebP, la organiza en
public/images/blog/[slug-post]/ y genera el snippet Markdown para pegar
directamente en el artículo.

Uso:
  python3 scripts/import_image.py <ruta-imagen>

Ejemplo:
  python3 scripts/import_image.py ~/Descargas/diagrama.png

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
