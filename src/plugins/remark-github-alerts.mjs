// src/plugins/remark-github-alerts.mjs

/** @typedef {import('mdast').Root} Root */

const ALERT_TYPES = {
  NOTE: 'Nota',
  TIP: 'Consejo',
  IMPORTANT: 'Importante',
  WARNING: 'Advertencia',
  CAUTION: 'Peligro',
};

const ALERT_RE = /^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\n?/;

/**
 * Recorre el árbol mdast buscando blockquotes con marcador [!TIPO].
 * @param {Root} tree
 */
function walk(tree) {
  if (tree.children) {
    for (const child of tree.children) {
      if (child.type === 'blockquote') {
        transformAlert(child);
      } else {
        walk(child);
      }
    }
  }
}

/**
 * Transforma un nodo blockquote si comienza con [!TIPO].
 */
function transformAlert(node) {
  const firstChild = node.children[0];
  if (!firstChild || firstChild.type !== 'paragraph') return;

  const firstInline = firstChild.children[0];
  if (!firstInline || firstInline.type !== 'text') return;

  const match = firstInline.value.match(ALERT_RE);
  if (!match) return;

  const type = match[1].toLowerCase();
  const title = ALERT_TYPES[match[1]];

  // Eliminar el marcador [!TIPO] del texto
  firstInline.value = firstInline.value.slice(match[0].length);

  // Si el primer párrafo quedó vacío, eliminarlo
  if (firstChild.children.length === 1 && firstInline.value.trim() === '') {
    node.children.shift();
  }

  // Insertar párrafo de título al inicio
  node.children.unshift({
    type: 'paragraph',
    children: [{ type: 'text', value: `## ${title}` }],
    data: {
      hProperties: { className: ['callout-title'] },
    },
  });

  // Añadir clases al blockquote
  if (!node.data) node.data = {};
  if (!node.data.hProperties) node.data.hProperties = {};
  node.data.hProperties.className = ['callout', `callout-${type}`];
}

/** @returns {(tree: Root) => void} */
export default function remarkGithubAlerts() {
  return (tree) => walk(tree);
}
