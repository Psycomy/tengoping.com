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

Uso
---
  # Genera todas las imágenes en public/images/
  python3 scripts/generate-images.py

  # Genera solo una imagen concreta
  python3 scripts/generate-images.py fail2ban.jpg

  # Genera varias a la vez
  python3 scripts/generate-images.py fail2ban.jpg kvm-libvirt.jpg

  # Lista todas las imágenes disponibles
  python3 scripts/generate-images.py --list

Añadir una imagen nueva
-----------------------
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
