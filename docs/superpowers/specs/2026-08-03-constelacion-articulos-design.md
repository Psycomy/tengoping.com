# Constelación de artículos — grafo de enlaces del blog

## Contexto y objetivo

El blog enlaza artículos entre sí de forma orgánica: 44 de los 45 posts contienen
al menos un enlace `[texto](/blog/<slug>/)` hacia otro artículo, escrito como
parte natural de la redacción (ej. "ya vimos cómo [systemd gestiona
servicios](/blog/guia-systemd-servicios-linux/)"). Esta spec define una nueva
página, `/constelacion/`, que visualiza esos enlaces como un grafo interactivo
tipo "graph view" de Obsidian: cada artículo es un nodo, cada enlace real en el
contenido es una conexión (edge).

El objetivo es una herramienta de **navegación y descubrimiento real**, no solo
una pieza vistosa: debe ayudar a encontrar artículos relacionados explorando el
grafo, con el mismo nivel de cuidado visual y de rendimiento que el resto del
sitio (zero JS frameworks, CSP hash-based, estética terminal).

## Fuente de datos: enlaces reales, no similitud calculada

A diferencia de `RelatedArticles.astro` (que infiere relación por tags/categoría
compartidos), este grafo usa **los enlaces que ya existen en el markdown** de
cada post. Es una decisión deliberada: refleja el hilo editorial real —qué guía
menciona a cuál— en vez de una heurística de similitud temática. No se
inventan relaciones nuevas ni se modifica el contenido existente para esta
funcionalidad.

## Arquitectura

### 1. Extracción de enlaces (build-time)

En el frontmatter de `src/pages/constelacion.astro` (se ejecuta en Node
durante el build, sin coste en cliente):

- `getCollection('blog', ({ data }) => !data.draft)` obtiene los posts.
- Para cada post, una regex sobre `post.body` (markdown crudo) captura
  `\]\(/blog/([^/)]+)/?\)` → lista de slugs destino.
- Se descartan matches que no correspondan a un slug real de la colección
  (enlaces rotos o a otras secciones del sitio no cuentan como edge).
- Se construye el grafo:
  - **Nodos**: `{ id, title, slug, category }` por cada post.
  - **Edges**: un par `(origen, destino)` por cada enlace encontrado. El
    grafo se trata como no dirigido a efectos de layout/resaltado (un enlace
    A→B conecta visualmente A y B, sin distinguir sentido).
  - **Grado de nodo**: nº total de conexiones (entrantes + salientes),
    usado más adelante para el tamaño del nodo.
- El grafo resultante se serializa a JSON y se embebe en la página dentro de
  `<script type="application/json" id="graph-data">` (JSON puro, no
  ejecutable — evita interpolar datos dentro de un `<script>` de lógica y
  simplifica el hash CSP).

### 2. Layout: simulación de fuerzas en cliente

Script vanilla (sin librerías), inicializado con el patrón estándar del
proyecto (`setupFn(); document.addEventListener('astro:after-swap', setupFn)`
por convención, aunque esta página no navega internamente):

- Posición inicial de cada nodo: distribución circular dentro del área del
  canvas (punto de partida más ordenado que aleatorio puro).
- Algoritmo tipo Fruchterman-Reingold simplificado, por iteración:
  - **Repulsión** entre todos los pares de nodos (O(n²) — trivial con 45
    nodos, sin necesidad de quadtree/Barnes-Hut).
  - **Atracción tipo muelle** entre nodos conectados por un edge.
  - **Gravedad leve** hacia el centro del canvas, para evitar que el grafo
    se disperse fuera del viewport.
- Bucle en `requestAnimationFrame` hasta que el desplazamiento total por
  frame cae bajo un umbral de convergencia (~200-400 iteraciones típico) →
  la simulación se **congela** (se detiene el loop, cero coste de CPU en
  reposo). No hay arrastre manual de nodos (fuera de alcance, ver sección
  "Fuera de alcance").
- En `resize` (con debounce): se reescala el canvas y se reutilizan las
  posiciones ya asentadas como punto de partida, sin reiniciar la
  simulación desde cero.

### 3. Renderizado visual

- `<canvas>` a ancho completo del área de contenido, con `devicePixelRatio`
  aplicado para nitidez en pantallas de alta densidad.
- **Color por categoría**: se reutiliza la misma paleta que ya usan los
  badges de categoría del sitio. Como canvas no puede leer CSS directamente,
  los colores se obtienen vía `getComputedStyle` sobre las custom properties
  correspondientes, y se releen cuando cambia el tema (mismo listener de
  tema que usa el resto del sitio) — solo se repinta, no se recongela la
  simulación.
- **Tamaño por grado**: radio del nodo interpolado entre un mínimo y máximo
  (ej. 4px–12px) según el nº de conexiones del nodo.
- **Edges**: líneas de 1px, color `--color-border` con opacidad baja —
  visibles pero discretas, sin gradientes ni sombras (coherente con
  `--shadow-*: none` del sistema de diseño).
- Fondo del canvas: `--color-bg`/`--color-surface`. Ningún elemento del
  grafo (nodo, tooltip, panel) usa `border-radius` — coherencia con
  `--radius-*: 0`.

### 4. Interacción

- **Desktop (hover)**: hit-test por distancia del puntero a cada nodo. Al
  entrar en el radio de un nodo:
  - Se resalta ese nodo y sus vecinos directos (mayor opacidad/brillo).
  - El resto del grafo se atenúa (opacity reducida).
  - Aparece el título del artículo como label flotante junto al nodo
    (posicionado para no salirse del viewport en los bordes del canvas).
  - Cursor cambia a `pointer`.
- **Click** sobre un nodo resaltado → navega a `/blog/<slug>/` (enlace
  directo, como cualquier otro enlace del sitio).
- **Mobile/táctil**: no hay hover, así que:
  - Primer `tap` sobre un nodo → resalta vecinos + muestra título (simula
    el estado de hover).
  - Segundo `tap` sobre el mismo nodo → navega al artículo.
  - `tap` fuera de cualquier nodo → deselecciona.
- Sin zoom/pan en esta versión: 45 nodos caben en pantalla sin necesitar
  navegación adicional del propio canvas.

### 5. Ruta y navegación

- Nueva página `src/pages/constelacion.astro`, usando `BaseLayout`.
- Enlace añadido a `headerLinks` y `footerLinks` en
  `src/data/navigation.ts`, como `./constelacion`, junto a `./blog`,
  `./categorias`, etc. — sección de primer nivel del sitio, no un enlace
  oculto.

### 6. Casos borde

- **Nodo aislado** (`por-que-este-blog.md`, sin enlaces entrantes ni
  salientes con ningún otro post): la gravedad leve lo mantiene dentro del
  viewport pero sin nada que lo atraiga hacia el resto del grafo — queda
  visiblemente periférico. Es el comportamiento correcto y esperado, no un
  bug a corregir.
- **Enlaces rotos o hacia slugs inexistentes**: se descartan al construir
  el grafo (no generan edges), no rompen el build.
- **Accesibilidad / sin JS**: dado que un canvas interactivo no es
  accesible por teclado/lector de pantalla de forma trivial, se incluye
  una sección visible debajo del grafo (no oculta, no colapsada por
  defecto) con un listado plano de `<a href="/blog/<slug>/">` a todos los
  artículos, agrupado por categoría — el contenido sigue siendo navegable
  sin depender del canvas, coherente con la filosofía "contenido primero"
  del sitio.
- **Pagefind**: el contenedor del grafo lleva `data-pagefind-ignore` — no es
  contenido indexable, es una herramienta de navegación.
- **CSP**: el script inline de la página pasa por el mecanismo existente de
  `postbuild.mjs` (hash SHA-256 automático), sin cambios necesarios en ese
  pipeline.

## Fuera de alcance (YAGNI)

- Arrastrar/fijar nodos manualmente (paridad total con Obsidian) — no aporta
  valor de navegación real en un blog, se añadiría complejidad de eventos de
  arrastre y gestión de rendimiento sin beneficio claro.
- Zoom/pan del canvas — innecesario con 45 nodos.
- Edges "débiles" por tags/categoría compartidos junto a los enlaces reales
  — se descartó en brainstorming para mantener el grafo fiel al hilo
  editorial real y evitar una lectura confusa de dos tipos de conexión.
- Filtros interactivos por categoría/tag en esta primera versión.

## Verificación

- `npm run lint` (0 errores).
- `npm run build` debe completar sin errores, incluyendo que
  `postbuild.mjs` calcule el hash CSP del nuevo script inline.
- Prueba manual en navegador (claro y oscuro, desktop y viewport móvil):
  - El grafo se asienta y se congela correctamente.
  - Hover (desktop) y tap (mobile) resaltan vecinos y muestran título.
  - Click/segundo-tap navega al artículo correcto.
  - El listado de fallback sin JS/accesible funciona y enlaza a los
    artículos correctos.
