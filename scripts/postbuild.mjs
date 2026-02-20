#!/usr/bin/env node
/**
 * Post-build script: runs after `astro build` to:
 * 1. Compute SHA-256 hashes of all inline scripts/styles → CSP sin 'unsafe-inline'
 * 2. Inject build ID into service worker → invalidación automática de caché
 * 3. Write dist/_headers con CSP hash-based
 */
import { readFileSync, writeFileSync, readdirSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import {
  transformInlineStylesToClasses,
  renderStyleClassMap,
} from './utils/inline-style-transform.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DIST = join(__dirname, '..', 'dist');
const DEFAULT_REPORT_GROUP = 'csp';
const INLINE_STYLESHEET_HREF = '/assets/inline-styles.css';
const INLINE_STYLESHEET_PATH = join(DIST, 'assets', 'inline-styles.css');

function getHtmlFiles(dir, htmlFiles = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      getHtmlFiles(fullPath, htmlFiles);
    } else if (entry.name.endsWith('.html')) {
      htmlFiles.push(fullPath);
    }
  }
  return htmlFiles;
}

function externalizeInlineStyles() {
  const htmlFiles = getHtmlFiles(DIST);
  const styleClassMap = new Map();
  let transformedAttributes = 0;
  let transformedFiles = 0;

  for (const htmlPath of htmlFiles) {
    const html = readFileSync(htmlPath, 'utf-8');
    const { html: transformedHtml, transformedCount } = transformInlineStylesToClasses(html, {
      classPrefix: 'csp-style',
      stylesheetHref: INLINE_STYLESHEET_HREF,
      styleClassMap,
    });

    if (transformedCount > 0) {
      transformedAttributes += transformedCount;
      transformedFiles += 1;
      writeFileSync(htmlPath, transformedHtml);
    }
  }

  if (styleClassMap.size > 0) {
    mkdirSync(join(DIST, 'assets'), { recursive: true });
    writeFileSync(INLINE_STYLESHEET_PATH, renderStyleClassMap(styleClassMap));
  }

  return {
    transformedAttributes,
    transformedFiles,
    generatedClasses: styleClassMap.size,
  };
}

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

function getReportingConfig() {
  const endpoint = process.env.CSP_REPORT_ENDPOINT?.trim();
  if (!endpoint) return null;

  try {
    const parsed = new URL(endpoint);
    if (parsed.protocol !== 'https:') {
      console.warn(
        `postbuild: CSP reporting disabled, endpoint must use https (${process.env.CSP_REPORT_ENDPOINT})`
      );
      return null;
    }
  } catch {
    console.warn(
      `postbuild: CSP reporting disabled, invalid CSP_REPORT_ENDPOINT (${process.env.CSP_REPORT_ENDPOINT})`
    );
    return null;
  }

  const reportGroup = process.env.CSP_REPORT_GROUP?.trim() || DEFAULT_REPORT_GROUP;
  return { endpoint, reportGroup };
}

function writeHeaders(scriptHashes, styleHashes, reportingConfig) {
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
  const cspWithReporting = reportingConfig
    ? `${csp}; report-to ${reportingConfig.reportGroup}`
    : csp;
  const reportToHeader = reportingConfig
    ? JSON.stringify({
        group: reportingConfig.reportGroup,
        max_age: 10886400,
        endpoints: [{ url: reportingConfig.endpoint }],
      })
    : null;
  const reportingHeaders = reportingConfig
    ? `  Reporting-Endpoints: ${reportingConfig.reportGroup}="${reportingConfig.endpoint}"\n  Report-To: ${reportToHeader}\n`
    : '';

  const content = `/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), serial=(), accelerometer=(), gyroscope=(), magnetometer=(), autoplay=()
  X-XSS-Protection: 0
  X-Permitted-Cross-Domain-Policies: none
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  Content-Security-Policy: ${cspWithReporting}
${reportingHeaders}
`;

  writeFileSync(join(DIST, '_headers'), content);
}

// --- Run ---

const inlineStyleStats = externalizeInlineStyles();
const scriptHashes = collectInlineScriptHashes(DIST);
const styleHashes = collectInlineStyleHashes(DIST);
const buildId = updateServiceWorker();
const reportingConfig = getReportingConfig();
writeHeaders([...scriptHashes], [...styleHashes], reportingConfig);

console.log(
  `postbuild: ${inlineStyleStats.transformedAttributes} inline style attrs externalized in ${inlineStyleStats.transformedFiles} HTML files (${inlineStyleStats.generatedClasses} classes), ${scriptHashes.size} script hashes, ${styleHashes.size} style hashes, SW build ID: ${buildId}, CSP reporting: ${
    reportingConfig ? `enabled (${reportingConfig.reportGroup})` : 'disabled'
  }`
);
