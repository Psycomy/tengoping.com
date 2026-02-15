# Diseño: Skills para generación de artículos del blog

**Fecha:** 2026-02-15
**Enfoque:** Dos skills separadas (blog-plan + blog-write)

## Contexto

tengoping.com es un blog técnico en español (Astro 5) con 36 artículos en 8 categorías, orientado a sysadmins y profesionales IT. Tiene un script `generate-images.py` para miniaturas con estética terminal.

## Skill 1: `blog-plan`

**Ubicación:** `~/.claude/skills/blog-plan/SKILL.md`

**Propósito:** Planificar el calendario editorial mensual de 4 artículos (1/semana).

### Flujo

1. Escanear posts existentes (`src/content/blog/`) — categorías, tags, fechas
2. Identificar huecos temáticos (categorías poco cubiertas, tags sin desarrollar)
3. Opcionalmente buscar tendencias web para temas de actualidad
4. Presentar análisis con sugerencias al usuario
5. Negociar los 4 temas interactivamente (usuario aprueba/modifica cada uno)
6. Preguntar autor para cada artículo (antonio, alois, eloculto)
7. Generar documento de planificación: `docs/plans/YYYY-MM-blog-plan.md`

### Salida (plan mensual)

Para cada artículo:
- Título tentativo
- Categoría
- Tags propuestos
- Autor
- Brief (2-3 líneas)
- Fecha tentativa de publicación
- Estado: pendiente/completado

## Skill 2: `blog-write`

**Ubicación:** `~/.claude/skills/blog-write/SKILL.md`

### Propósito

Investigar, redactar un artículo completo y generar su miniatura.

### Flujo

1. **Recibir tema** — del plan mensual o directamente del usuario
2. **Preguntar autor** — antonio, alois, eloculto
3. **Preguntar draft** — publicar (draft: false) o borrador (draft: true)
4. **Investigar** — según el tipo de tema:
   - Actualidad/tendencias: WebSearch
   - Técnicos estables: conocimiento propio
   - Mixto: combinar ambos
5. **Redactar** artículo markdown:
   - Frontmatter completo (title, description, author, pubDate, category, tags, image, draft)
   - Estructura h2/h3, código de ejemplo
   - Tono profesional, español, directo
   - Longitud variable según tipo (guías más largas, opiniones más cortas)
   - Slug kebab-case sin acentos
6. **Guardar** en `src/content/blog/{slug}.md`
7. **Generar miniatura** con `python3 scripts/generate-images.py --auto`
8. **Verificar** que archivo e imagen existen

### Estilo de contenido

- Español, tono profesional y práctico
- Ejemplos de código (bash, yaml, etc.)
- Audiencia: sysadmins con experiencia
- Sin relleno, directo al grano

## Interacción entre skills

- `blog-plan` genera `docs/plans/YYYY-MM-blog-plan.md`
- `blog-write` puede leer el plan y ofrecer artículos pendientes
- `blog-write` funciona independientemente con un tema directo
- Artículos escritos se marcan como completados en el plan

## Decisiones de diseño

| Decisión | Valor |
|----------|-------|
| Investigación | Adaptativa: web para actualidad, conocimiento propio para técnicos |
| Volumen mensual | 4 artículos (1/semana) |
| Autor | Preguntar cada vez |
| Miniaturas | Ejecutar `--auto` automáticamente |
| Publicación | Preguntar draft/publicar cada vez |
| Análisis de huecos | Siempre antes de planificar |
| Longitud | Variable según tema |
