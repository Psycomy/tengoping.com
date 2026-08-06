# Auditoría técnica jul/ago 2026 — pendiente

Informe completo (SEO, contenido, enlazado interno, rendimiento, accesibilidad, E-E-A-T):
https://claude.ai/code/artifact/8e356790-9cb5-4845-b592-55d85166cf5e

19 de los 20 hallazgos originales están resueltos (ver commit de esta sesión). Solo queda
uno, y uno descartado por decisión del usuario.

---

## 🟡 Pendiente: ampliar los 5 artículos más flojos en profundidad

**Por qué importa:** en agosto 2026 ya se detectó vía Search Console que 15 de 49 posts no
indexaban por tener menos de 1000 palabras ([[gsc-thin-content-fix-aug-2026]] en memoria);
se ampliaron 10. Estos 5 son, con alta probabilidad, parte de los que quedaron pendientes de
esa tanda — misma causa raíz reapareciendo.

**Por qué no se hizo en esta sesión:** requiere reescritura real de contenido (no un fix de
código), mejor abordado con la skill `blog-write` en una sesión dedicada.

**Artículos, por orden de prioridad (extensión actual):**

1. `configurar-servidor-ssh-seguro-linux.md` — 554 palabras. Es artículo "hub": `fail2ban`,
   `firewalld-nftables`, `hardening-basico` y `journalctl` enlazan aquí como referencia
   canónica de "SSH seguro", pero es de los menos desarrollados del sitio. Prioridad alta por
   su rol de pilar temático.
2. `scripts-bash-utiles-sysadmin.md` — 530 palabras, 12 encabezados. Cubre "10 scripts Bash
   útiles" en ~44 palabras de contexto por script — casi todo el peso recae en el código, sin
   explicar por qué importa cada uno o qué matices tiene.
3. `backup-incremental-rsync-servidores-linux.md` — 738 palabras. Otro "hub" (enlazado desde
   `nas-openmediavault`, `raid-mdadm`, `cron-systemd-timers`, `scripts-bash`, `nextcloud`,
   `vaultwarden`), notablemente más ligero que `rclone-sincroniza-cifra-nube` (1826 palabras)
   sobre un tema hermano. La estrategia de retención y verificación queda con poco detalle.
4. `monitorizar-servidores-linux-prometheus-grafana.mdx` — 776 palabras. El más superficial
   de la categoría Monitorización: Zabbix (1235), Beszel (1797) y Uptime Kuma (2051) tratan
   temas comparables con bastante más profundidad. PromQL y alertas quedan resueltos casi de
   pasada.
5. `recuperar-contrasena-root-livecd-lvm.md` — 262 palabras, 1 solo encabezado. El post más
   corto del blog con diferencia. Es una chuleta de rescate para un caso concreto — antes de
   ampliarlo, decidir con el usuario si de verdad necesita más desarrollo o si, como
   `comandos-esenciales-lvm-guia-rapida.md`, se acepta como cheatsheet corto intencional
   ([[feedback-own-notes-no-ai-disclosure]]: los apuntes LVM son cheatsheets 100% del
   usuario).

**Cómo abordarlo:** `blog-write` sobre cada slug existente (ampliar, no reescribir desde
cero), respetando frontmatter y slug actuales — no tocar URLs ya indexadas.

---

## Descartado (decisión del usuario)

| Hallazgo                                            | Motivo                                        |
| --------------------------------------------------- | --------------------------------------------- |
| Añadir redes sociales de Alois (coautor) al JSON-LD | El propio Alois no quiere añadirlas por ahora |

## Fuera de alcance (sin acción)

| Hallazgo                                                                                   | Motivo                                                                                             |
| ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Posts `.md` no pueden llevar imágenes ilustrativas en el cuerpo (`Figure` requiere `.mdx`) | Limitación de formato, no un bug; solo aplicaría si se decide homogeneizar migrando posts a `.mdx` |
