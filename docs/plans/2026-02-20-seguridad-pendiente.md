# Seguridad — Tareas pendientes

Trabajo completado: `docs/plans/2026-02-20-seguridad-design.md` y `2026-02-20-seguridad.md`

---

## 🟡 Tarea 1: Eliminar `style-src 'unsafe-inline'` de la CSP

**Por qué importa:** `style-src 'unsafe-inline'` permite inyectar estilos arbitrarios si
alguna vez hubiera XSS. Eliminarla cierra ese vector.

**Por qué no se implementó:** Requiere computar hashes SHA-256 de todos los `<style>` tags
inline generados por Astro (componentes) y Shiki. Si algún estilo varía por build, los hashes
fallan. Necesita testing exhaustivo antes de desplegar.

**Cómo implementarlo** (extensión de `scripts/postbuild.mjs`):

```javascript
// Añadir función paralela a collectInlineScriptHashes:
function collectInlineStyleHashes(dir, hashes = new Set()) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      collectInlineStyleHashes(fullPath, hashes);
    } else if (entry.name.endsWith('.html')) {
      const html = readFileSync(fullPath, 'utf-8');
      const re = /<style(?![^>]*\bsrc\s*=)[^>]*>([\s\S]*?)<\/style>/gi;
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
```

En `writeHeaders()`, reemplazar `"style-src 'self' 'unsafe-inline'"` por:

```javascript
const styleHashes = collectInlineStyleHashes(DIST);
const styleSrc = ["'self'", ...styleHashes].join(' ');
// ...
`style-src ${styleSrc}`,
```

**Riesgo a mitigar:** Verificar que los hashes son estables entre builds (ejecutar
`npm run build` dos veces y comparar el contenido de `dist/_headers`).

---

## ⚠️ Tarea 2: Registrar tengoping.com en el HSTS Preload List

**Por qué importa:** El header `Strict-Transport-Security: ...; preload` ya está desplegado
(commit `0de4e33`), pero sin registro en la lista los navegadores no lo aplican en la primera
visita de un usuario nuevo (primera petición HTTP → redirect HTTPS → vulnerable a MITM en
ese instante).

**Cómo hacerlo:**

1. Ir a <https://hstspreload.org>
2. Introducir `tengoping.com`
3. Leer y aceptar los requisitos (el header ya los cumple)
4. Enviar la solicitud

**Tiempo de propagación:** semanas a meses hasta llegar a Chrome/Firefox/Safari.
Una vez en la lista, es difícil salir (considerar antes de enviar).

---

## 🟢 Tarea 3: CSP `report-to` para monitorización de violaciones

**Por qué importa:** Sin un endpoint de reporting, si la CSP bloquea algo en producción no
hay forma de enterarse hasta que un usuario lo reporta.

**Cómo implementarlo:**

1. Crear endpoint de reporting (opciones: [report-uri.com](https://report-uri.com),
   Cloudflare Worker propio, o Sentry).
2. Añadir a la CSP en `scripts/postbuild.mjs`:

```javascript
`report-to default`,
```

3. Añadir header `Reporting-Endpoints`:

```
Reporting-Endpoints: default="https://TU-ENDPOINT/csp-reports"
```

---

## Descartadas (no aplican a este proyecto)

| Cambio                                     | Motivo                                                             |
| ------------------------------------------ | ------------------------------------------------------------------ |
| `img-src` restringido a dominios concretos | Posts pueden referenciar imágenes externas                         |
| SRI para script de Giscus                  | Giscus actualiza CDN con frecuencia; hash rompería los comentarios |
