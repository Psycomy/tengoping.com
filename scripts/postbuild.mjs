#!/usr/bin/env node
/**
 * Post-build script: runs after `astro build` to:
 * 1. Compute SHA-256 hashes of all inline scripts/styles → CSP sin 'unsafe-inline'
 * 2. Inject build ID into service worker → invalidación automática de caché
 * 3. Write dist/_headers con CSP hash-based
 */
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DIST = join(__dirname, '..', 'dist');

// --- 1. Collect SHA-256 hashes of inline scripts/styles from built HTML ---

function collectInlineScriptHashes(dir, hashes = new Set()) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      collectInlineScriptHashes(fullPath, hashes);
    } else if (entry.name.endsWith('.html')) {
      const html = readFileSync(fullPath, 'utf-8');
      // Match inline <script> (no src=, no type="application/ld+json")
      const re =
        /<script(?![^>]*\bsrc\s*=)(?![^>]*type\s*=\s*["']application\/ld\+json["'])[^>]*>([\s\S]*?)<\/script>/gi;
      let match;
      while ((match = re.exec(html)) !== null) {
        const content = match[1];
        if (!content.trim()) continue;
        const hash = createHash('sha256').update(content, 'utf-8').digest('base64');
        hashes.add(`'sha256-${hash}'`);
      }
    }
  }
  return hashes;
}

function collectInlineStyleHashes(dir, hashes = new Set()) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      collectInlineStyleHashes(fullPath, hashes);
    } else if (entry.name.endsWith('.html')) {
      const html = readFileSync(fullPath, 'utf-8');
      const re = /<style[^>]*>([\s\S]*?)<\/style>/gi;
      let match;
      while ((match = re.exec(html)) !== null) {
        const content = match[1];
        if (!content.trim()) continue;
        const hash = createHash('sha256').update(content, 'utf-8').digest('base64');
        hashes.add(`'sha256-${hash}'`);
      }
    }
  }
  return hashes;
}

// --- 2. Update service worker cache version with build ID ---

function updateServiceWorker() {
  const swPath = join(DIST, 'sw.js');
  let sw = readFileSync(swPath, 'utf-8');
  const buildId = Date.now().toString(36);
  sw = sw.replace(
    /const CACHE_VERSION = '[^']+';/,
    `const CACHE_VERSION = 'tengoping-b${buildId}';`
  );
  writeFileSync(swPath, sw);
  return buildId;
}

// --- 3. Write _headers with hash-based CSP ---

function writeHeaders(scriptHashes, styleHashes) {
  const scriptSrc = ["'self'", ...scriptHashes, "'wasm-unsafe-eval'", 'https://giscus.app'].join(
    ' '
  );
  const styleSrc = ["'self'", ...styleHashes].join(' ');

  const csp = [
    "default-src 'self'",
    `script-src ${scriptSrc}`,
    `style-src ${styleSrc}`,
    "font-src 'self'",
    "img-src 'self' data: https:",
    'frame-src https://giscus.app',
    "connect-src 'self' https://giscus.app https://api.github.com",
    "worker-src 'self'",
    "manifest-src 'self'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
    'upgrade-insecure-requests',
    "frame-ancestors 'none'",
  ].join('; ');

  const content = `/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=(), serial=(), accelerometer=(), gyroscope=(), magnetometer=(), autoplay=()
  X-XSS-Protection: 0
  X-Permitted-Cross-Domain-Policies: none
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  Content-Security-Policy: ${csp}
`;

  writeFileSync(join(DIST, '_headers'), content);
}

// --- Run ---

const scriptHashes = collectInlineScriptHashes(DIST);
const styleHashes = collectInlineStyleHashes(DIST);
const buildId = updateServiceWorker();
writeHeaders([...scriptHashes], [...styleHashes]);

console.log(
  `postbuild: ${scriptHashes.size} script hashes, ${styleHashes.size} style hashes, SW build ID: ${buildId}`
);
