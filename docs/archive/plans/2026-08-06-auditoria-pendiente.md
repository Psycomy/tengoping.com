# Auditoría técnica jul/ago 2026 — pendiente

Informe completo (SEO, contenido, enlazado interno, rendimiento, accesibilidad, E-E-A-T):
https://claude.ai/code/artifact/8e356790-9cb5-4845-b592-55d85166cf5e

19 de los 20 hallazgos originales están resueltos (ver commit de esta sesión). Solo queda
uno, y uno descartado por decisión del usuario.

---

## ✅ Hecho (2026-08-06): ampliados 4 de los 5 artículos más flojos en profundidad

**Por qué importaba:** en agosto 2026 ya se detectó vía Search Console que 15 de 49 posts no
indexaban por tener menos de 1000 palabras ([[gsc-thin-content-fix-aug-2026]] en memoria);
se ampliaron 10. Estos 5 eran, con alta probabilidad, parte de los que quedaron pendientes de
esa tanda — misma causa raíz reapareciendo.

**Cómo se abordó:** `blog-write` sobre cada slug existente (ampliar, no reescribir desde
cero), respetando frontmatter y slug actuales — sin tocar URLs ya indexadas. Fact-check con
WebSearch en cada claim técnico nuevo (2FA/PAM, cifrados SSH, comportamiento de `du` con
hardlinks, `rate()` vs `irate()`, Alertmanager). `npm run build` + `lint` + `prettier` en
verde para los 4.

1. **`configurar-servidor-ssh-seguro-linux.md`** — 554 → ~1600 palabras. Añadido: 2FA/TOTP vía
   PAM, cifrados/algoritmos endurecidos (+ `ssh-audit`), gestión de claves con
   `~/.ssh/config`, `ClientAliveInterval`/Banner, diagrama de flujo ASCII, enlace a
   `journalctl`.
2. **`scripts-bash-utiles-sysadmin.md`** — 530 → ~1580 palabras. Cada uno de los 10 scripts
   ganó contexto real (por qué importa, matices, gotchas) en vez de solo código: inodos vs
   espacio en disco, `truncate` vs `rm`, `Restart=on-failure` de systemd, `free` y
   `procps 3.3.10`, barra final en `rsync`, seguridad del inventario SSH.
3. **`backup-incremental-rsync-servidores-linux.md`** — 738 → ~1350 palabras. Retención GFS
   (script abuelo-padre-hijo) reemplaza el borrado por antigüedad simple; verificación de
   integridad explicada a fondo (quick-check de rsync, `du` y deduplicación de hardlinks);
   advertencias sobre editar snapshots y filesystems sin soporte de hardlinks (exFAT/FAT32).
4. **`monitorizar-servidores-linux-prometheus-grafana.mdx`** — 776 → ~1590 palabras. Sección
   de Alertmanager completa (instalación, routing por `severity`, diagrama de flujo de
   alertas) que antes solo se mencionaba como "siguiente paso"; más consultas PromQL (carga,
   errores de red, I/O de disco) y explicación counter/gauge + `rate()` vs `irate()`.

**Punto 5 — decidido por el usuario (2026-08-06): se deja como está.**

`recuperar-contrasena-root-livecd-lvm.md` — 262 palabras, 1 solo encabezado. Se confirma como
cheatsheet corto intencional, igual que `comandos-esenciales-lvm-guia-rapida.md`: no es una
guía a medio terminar, es una chuleta de rescate pensada para copiar-pegar en el momento
exacto de un incidente, no para leerse de cabo a rabo. Puede seguir sin indexar bien en
Google por su longitud — se acepta ese coste a cambio de mantener el formato apropiado para
su propósito. Sin acción pendiente.

## Estado final

Los 5 hallazgos de esta auditoría están resueltos: 4 artículos ampliados (commit `2f1c597`,
2026-08-06) y 1 confirmado como cheatsheet corto intencional sin necesidad de cambios.

---

## Descartado (decisión del usuario)

| Hallazgo                                            | Motivo                                        |
| --------------------------------------------------- | --------------------------------------------- |
| Añadir redes sociales de Alois (coautor) al JSON-LD | El propio Alois no quiere añadirlas por ahora |

## Fuera de alcance (sin acción)

| Hallazgo                                                                                   | Motivo                                                                                             |
| ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Posts `.md` no pueden llevar imágenes ilustrativas en el cuerpo (`Figure` requiere `.mdx`) | Limitación de formato, no un bug; solo aplicaría si se decide homogeneizar migrando posts a `.mdx` |
