import test from 'node:test';
import assert from 'node:assert/strict';

import { transformInlineStylesToClasses } from '../utils/inline-style-transform.mjs';

test('replaces inline style attributes with deterministic classes and css rules', () => {
  const input = `
<html>
  <head></head>
  <body>
    <pre class="astro-code" style="background-color:#fff;color:#111"><code>
      <span style="color:#d73a49">import</span>
      <span style="color:#d73a49">from</span>
    </code></pre>
  </body>
</html>`;

  const { html, cssText, transformedCount } = transformInlineStylesToClasses(input, {
    classPrefix: 'csp-style',
  });

  assert.equal(transformedCount, 3);
  assert.equal(html.includes(' style='), false);
  assert.match(html, /class="astro-code csp-style-1"/);
  assert.match(html, /class="csp-style-2"/);
  assert.equal((html.match(/csp-style-2/g) || []).length, 2);

  assert.match(cssText, /\.csp-style-1\s*\{background-color:#fff;color:#111;\}/);
  assert.match(cssText, /\.csp-style-2\s*\{color:#d73a49;\}/);
});

test('injects generated stylesheet link into head once', () => {
  const input =
    '<html><head><title>x</title></head><body><span style="color:#000">x</span></body></html>';
  const { html } = transformInlineStylesToClasses(input, {
    classPrefix: 'csp-style',
    stylesheetHref: '/assets/inline-styles.css',
  });

  assert.match(
    html,
    /<link rel="stylesheet" href="\/assets\/inline-styles\.css" data-inline-style-sheet="true"\s*\/?>/
  );
});
