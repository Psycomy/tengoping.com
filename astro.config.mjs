import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import pagefind from 'astro-pagefind';

export default defineConfig({
  site: 'https://tengoping.com',
  integrations: [mdx(), sitemap(), pagefind()],
  markdown: {
    shikiConfig: {
      themes: {
        light: 'github-light',
        dark: 'github-dark',
      },
      transformers: [
        {
          // Fix WCAG AA contrast for code comment tokens.
          // span() receives the merged dual-theme style string for each token.
          name: 'accessible-comment-color',
          span(node) {
            // Light: github-light #6A737D (4.13:1 on #EDF0F5) → #57606a (5.61:1)
            // Dark:  github-dark  #6A737D (3.04:1 on #24292e) → #8b949e (4.91:1)
            if (typeof node.properties.style === 'string') {
              node.properties.style = node.properties.style
                .replace(/\bcolor:#6A737D\b/g, 'color:#57606a')
                .replace(/--shiki-dark:#6A737D\b/g, '--shiki-dark:#8b949e');
            }
          },
        },
      ],
    },
  },
});
