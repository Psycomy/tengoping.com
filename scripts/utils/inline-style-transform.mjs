function normalizeStyleValue(styleValue) {
  return styleValue.trim().replace(/;+\s*$/g, '');
}

function ensureTrailingSemicolon(styleValue) {
  const trimmed = styleValue.trim();
  if (!trimmed) return '';
  return trimmed.endsWith(';') ? trimmed : `${trimmed};`;
}

function ensureClassAttribute(attrs, className) {
  const classAttrRe = /\sclass=(["'])([\s\S]*?)\1/i;
  const classMatch = attrs.match(classAttrRe);

  if (classMatch) {
    const existing = classMatch[2].trim();
    const nextValue = existing ? `${existing} ${className}` : className;
    return attrs.replace(classAttrRe, ` class="${nextValue}"`);
  }

  return `${attrs} class="${className}"`;
}

function createClassForStyle(styleValue, styleClassMap, classPrefix) {
  const normalized = normalizeStyleValue(styleValue);
  if (!normalized) return null;

  if (!styleClassMap.has(normalized)) {
    const className = `${classPrefix}-${styleClassMap.size + 1}`;
    styleClassMap.set(normalized, className);
  }

  return styleClassMap.get(normalized);
}

function injectStylesheetLink(html, stylesheetHref) {
  if (!stylesheetHref) return html;
  if (html.includes('data-inline-style-sheet="true"')) return html;

  const linkTag = `<link rel="stylesheet" href="${stylesheetHref}" data-inline-style-sheet="true">`;

  if (html.includes('</head>')) {
    return html.replace('</head>', `  ${linkTag}\n</head>`);
  }

  if (html.includes('</body>')) {
    return html.replace('</body>', `  ${linkTag}\n</body>`);
  }

  return `${linkTag}\n${html}`;
}

export function renderStyleClassMap(styleClassMap) {
  let cssText = '';
  for (const [styleValue, className] of styleClassMap.entries()) {
    cssText += `.${className}{${ensureTrailingSemicolon(styleValue)}}\n`;
  }
  return cssText;
}

export function transformInlineStylesToClasses(
  html,
  { classPrefix = 'csp-style', stylesheetHref, styleClassMap = new Map() } = {}
) {
  let transformedCount = 0;

  let transformedHtml = html.replace(
    /<([A-Za-z][A-Za-z0-9-]*)([^>]*?)>/g,
    (fullMatch, tagName, attrs) => {
      const styleAttrRe = /\sstyle=(["'])([\s\S]*?)\1/i;
      const styleMatch = attrs.match(styleAttrRe);
      if (!styleMatch) return fullMatch;

      const className = createClassForStyle(styleMatch[2], styleClassMap, classPrefix);
      if (!className) return fullMatch;

      let nextAttrs = attrs.replace(styleAttrRe, '');
      nextAttrs = ensureClassAttribute(nextAttrs, className);
      transformedCount += 1;

      return `<${tagName}${nextAttrs}>`;
    }
  );

  if (transformedCount > 0) {
    transformedHtml = injectStylesheetLink(transformedHtml, stylesheetHref);
  }

  return {
    html: transformedHtml,
    cssText: renderStyleClassMap(styleClassMap),
    transformedCount,
    styleClassMap,
  };
}
