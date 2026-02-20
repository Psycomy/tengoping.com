#!/usr/bin/env python3
"""
Genera imágenes de portada para los artículos del blog con estética terminal.

Uso:
  python3 scripts/generate-images.py                          # Genera todas del catálogo
  python3 scripts/generate-images.py fail2ban.jpg             # Genera solo una
  python3 scripts/generate-images.py --auto                   # Auto-genera desde frontmatter
  python3 scripts/generate-images.py --auto --force           # Regenera todas
  python3 scripts/generate-images.py --new                    # Modo interactivo
  python3 scripts/generate-images.py --check                  # Detecta huérfanas/faltantes
  python3 scripts/generate-images.py --list                   # Lista el catálogo
  python3 scripts/generate-images.py --category Seguridad     # Filtra por categoría

Requisitos:
  pip install Pillow
"""

import argparse
import os
import re
import sys
from PIL import Image, ImageDraw, ImageFont

# --- Configuración -----------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..")
OUT_DIR = os.path.join(PROJECT_ROOT, "src", "assets", "images")
CONTENT_DIR = os.path.join(PROJECT_ROOT, "src", "content", "blog")
WIDTH, HEIGHT = 800, 500

# Fuentes (monospace del sistema)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# Colores del tema del blog
BG = "#0D1117"
TERMINAL_BG = "#161B22"
BORDER = "#30363D"
TEXT = "#E6EDF3"
GREEN = "#58D5A2"
MUTED = "#8B949E"
DOT_RED = "#FF5F56"
DOT_YELLOW = "#FFBD2E"
DOT_GREEN = "#27C93F"

# Color de acento por categoría
CAT_COLORS = {
    "Automatización": "#00BFFF",
    "Linux": "#58D5A2",
    "Opinión": "#FF6D00",
    "Redes": "#1A73E8",
    "Virtualización": "#A78BFA",
    "Seguridad": "#F87171",
    "Self-Hosting": "#34D399",
    "Hardware": "#FBBF24",
    "Software": "#C084FC",
    "Monitorización": "#F472B6",
}

# Stop words para extraer título de imagen desde el título del post
STOP_WORDS = {
    "cómo", "como", "guía", "guia", "para", "en", "de", "del", "con", "los",
    "las", "una", "un", "tu", "tus", "por", "qué", "que", "y", "o", "a",
    "el", "la", "es", "su", "sus", "al", "se", "no", "si", "más", "mas",
    "sin", "sobre", "entre", "desde", "hasta", "hacia", "donde", "dónde",
    "primeros", "pasos", "configurar", "instalar", "usar",
}

# --- Catálogo de artículos (override manual) ---------------------------------
# (filename, title, subtitle, category, [tree_items])

ARTICLES = [
    # Automatización
    ("auto-bash.jpg", "BASH SCRIPTS", "10 scripts útiles para sysadmin", "Automatización",
     ["├── disk-usage.sh", "├── log-rotate.sh", "└── backup.sh"]),
    ("auto-ansible.jpg", "ANSIBLE", "automatizar servidores", "Automatización",
     ["├── inventory.ini", "├── playbook.yml", "└── roles/"]),
    ("auto-backup.jpg", "RSYNC BACKUPS", "backups incrementales", "Automatización",
     ["├── rsync -avz", "├── --delete", "└── crontab -e"]),
    ("auto-cron.jpg", "CRON vs TIMERS", "tareas programadas", "Automatización",
     ["├── /etc/crontab", "├── systemd-timer", "└── OnCalendar="]),
    ("lvm-storage.jpg", "LVM", "volúmenes lógicos en linux", "Automatización",
     ["├── pvcreate", "├── vgcreate", "└── lvextend"]),
    # Linux
    ("ssh-server.jpg", "SSH SERVER", "configuración segura", "Linux",
     ["├── sshd_config", "├── authorized_keys", "└── fail2ban"]),
    ("linux-systemd.jpg", "SYSTEMD", "gestión de servicios", "Linux",
     ["├── systemctl", "├── journalctl", "└── unit files"]),
    ("linux-hardening.jpg", "HARDENING", "securing linux servers", "Linux",
     ["├── config/", "├── scripts/", "└── docs/"]),
    ("linux-containers.jpg", "PODMAN", "contenedores sin root", "Linux",
     ["├── podman run", "├── Containerfile", "└── pods/"]),
    ("linux-monitoring.jpg", "PROMETHEUS", "monitorización con grafana", "Monitorización",
     ["├── prometheus.yml", "├── node_exporter", "└── grafana:3000"]),
    ("linux-permissions.jpg", "PERMISOS", "chmod, chown y acls", "Linux",
     ["├── chmod 750", "├── chown user:group", "└── setfacl -m"]),
    # Opinión
    ("opinion-devops.jpg", "DEVOPS", "cultura en equipos pequeños", "Opinión",
     ["├── ci-cd/", "├── iac/", "└── monitoring/"]),
    ("opinion-cloud.jpg", "CLOUD 2025", "tendencias clave", "Opinión",
     ["├── edge computing", "├── serverless", "└── multi-cloud"]),
    ("opinion-ia.jpg", "IA & SYSADMIN", "¿oportunidad o amenaza?", "Opinión",
     ["├── chatops/", "├── aiops/", "└── automation/"]),
    ("sysadmin-automation.jpg", "AUTOMATIZACIÓN", "por qué aprender en 2025", "Opinión",
     ["├── ansible/", "├── terraform/", "└── scripts/"]),
    ("por-que-este-blog.jpg", "ESTE BLOG", "por qué existe este sitio", "Opinión",
     ["├── notas/", "├── tutoriales/", "└── cheat-sheets/"]),
    # Redes
    ("redes-vlan.jpg", "VLANS", "switches y linux", "Redes",
     ["├── trunk ports", "├── ip link add", "└── bridge vlan"]),
    ("redes-firewall.jpg", "FIREWALLD", "seguridad de red", "Redes",
     ["├── firewall-cmd", "├── nft list", "└── zones/"]),
    ("network-routes.jpg", "RUTAS ESTÁTICAS", "networkmanager y nmcli", "Redes",
     ["├── nmcli con mod", "├── ip route add", "└── /etc/sysconfig/"]),
    ("redes-dns.jpg", "BIND9", "servidor dns autoritativo", "Redes",
     ["├── named.conf", "├── zone files", "└── rndc reload"]),
    ("redes-proxy.jpg", "NGINX PROXY", "proxy inverso", "Redes",
     ["├── proxy_pass", "├── upstream {}", "└── ssl_certificate"]),
    # Virtualización
    ("kvm-libvirt.jpg", "KVM & LIBVIRT", "virtualización en linux", "Virtualización",
     ["├── /etc/libvirt/", "├── qemu-kvm", "└── virt-install"]),
    ("proxmox-ve.jpg", "PROXMOX VE", "virtualización profesional", "Virtualización",
     ["├── /etc/pve/", "├── qm / pct", "└── vzdump"]),
    ("vagrant-dev.jpg", "VAGRANT", "entornos reproducibles", "Virtualización",
     ["├── Vagrantfile", "├── vagrant up", "└── provisioners/"]),
    ("vm-snapshots.jpg", "SNAPSHOTS", "protege tus máquinas virtuales", "Virtualización",
     ["├── virsh snapshot", "├── qcow2 backing", "└── clone --full"]),
    # Seguridad
    ("fail2ban.jpg", "FAIL2BAN", "protege tus servicios", "Seguridad",
     ["├── jail.local", "├── filter.d/", "└── action.d/"]),
    ("luks-cifrado.jpg", "LUKS", "cifrado de discos linux", "Seguridad",
     ["├── cryptsetup", "├── /etc/crypttab", "└── luksFormat"]),
    ("lynis-audit.jpg", "LYNIS", "auditoría de seguridad", "Seguridad",
     ["├── lynis audit", "├── hardening index", "└── suggestions[]"]),
    ("letsencrypt-ssl.jpg", "LET'S ENCRYPT", "certificados ssl gratuitos", "Seguridad",
     ["├── certbot --nginx", "├── systemd timer", "└── wildcard DNS"]),
    # Self-Hosting
    ("nextcloud-server.jpg", "NEXTCLOUD", "tu nube personal", "Self-Hosting",
     ["├── /var/www/nextcloud/", "├── occ maintenance", "└── cron.php"]),
    ("pihole-dns.jpg", "PI-HOLE", "bloqueo dns de publicidad", "Self-Hosting",
     ["├── pihole -up", "├── /etc/dnsmasq.d/", "└── unbound"]),
    ("gitea-server.jpg", "GITEA", "servidor git autoalojado", "Self-Hosting",
     ["├── app.ini", "├── postgresql", "└── git@server"]),
    ("wireguard-vpn.jpg", "WIREGUARD", "vpn autoalojada", "Self-Hosting",
     ["├── wg genkey", "├── wg0.conf", "└── wg-quick up"]),
    # Hardware
    ("raspberry-pi-server.jpg", "RASPBERRY PI", "servidor doméstico", "Hardware",
     ["├── raspi-config", "├── boot/config.txt", "└── usb-ssd"]),
    ("nas-omv.jpg", "NAS CASERO", "openmediavault", "Hardware",
     ["├── mdadm RAID", "├── smb.conf", "└── smartctl"]),
    ("homelab-hardware.jpg", "HOMELAB", "elige tu hardware", "Hardware",
     ["├── mini-pc/", "├── poweredge/", "└── watts.log"]),
    ("linux-hardware-diag.jpg", "DIAGNÓSTICO", "hardware en linux", "Hardware",
     ["├── lscpu / lsblk", "├── smartctl -a", "└── sensors"]),
    # Software
    ("soft-git.jpg", "GIT", "control de versiones para sysadmins", "Software",
     ["├── git init", "├── git branch", "└── git merge"]),
    ("soft-python.jpg", "PYTHON", "administración de sistemas", "Software",
     ["├── subprocess", "├── paramiko", "└── psutil"]),
    ("soft-cicd.jpg", "GITHUB ACTIONS", "ci/cd guía práctica", "Software",
     ["├── .github/workflows/", "├── jobs:", "└── secrets"]),
    # Monitorización
    ("mon-observabilidad.jpg", "OBSERVABILIDAD", "métricas, logs y trazas", "Monitorización",
     ["├── metrics/", "├── logs/", "└── traces/"]),
    ("mon-alertmanager.jpg", "ALERTMANAGER", "alertas inteligentes", "Monitorización",
     ["├── alertmanager.yml", "├── route:", "└── silence/"]),
    ("mon-uptimekuma.jpg", "UPTIME KUMA", "monitorizar servicios web", "Monitorización",
     ["├── docker-compose.yml", "├── monitors/", "└── notifications/"]),
]

# Índice rápido por filename para lookups
_CATALOG_INDEX = {a[0]: a for a in ARTICLES}


# --- Parseo de frontmatter ---------------------------------------------------

def parse_frontmatter(filepath):
    """Parsea frontmatter YAML de un .md sin depender de PyYAML."""
    result = {}
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Extraer bloque entre --- delimiters
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return result

    block = match.group(1)
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # key: value
        m = re.match(r'^(\w+):\s*(.+)$', line)
        if not m:
            continue

        key, val = m.group(1), m.group(2).strip()

        # Quitar comillas
        if (val.startswith('"') and val.endswith('"')) or \
           (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]

        # Tags: parsear lista YAML inline ["tag1", "tag2"]
        if key == "tags":
            tags_match = re.findall(r'"([^"]+)"|\'([^\']+)\'', val)
            result["tags"] = [t[0] or t[1] for t in tags_match]
            continue

        # Booleanos
        if val.lower() in ("true", "false"):
            result[key] = val.lower() == "true"
            continue

        result[key] = val

    return result


def extract_title_from_frontmatter(title):
    """Extrae palabras significativas del título para usar como título de imagen."""
    words = title.split()
    significant = [w for w in words if w.lower().strip(":") not in STOP_WORDS]
    # Tomar las primeras 1-3 palabras significativas
    result = significant[:3] if significant else words[:2]
    return " ".join(result).upper()


def truncate_subtitle(text, max_len=45):
    """Trunca texto a max_len chars, cortando por palabra."""
    if len(text) <= max_len:
        return text
    truncated = text[:max_len].rsplit(" ", 1)[0]
    return truncated + "…"


def tags_to_tree(tags):
    """Convierte lista de tags a formato tree."""
    if not tags:
        return ["└── (sin tags)"]
    items = []
    for i, tag in enumerate(tags[:3]):  # máximo 3 items
        prefix = "└──" if i == len(tags[:3]) - 1 else "├──"
        items.append(f"{prefix} {tag.lower()}")
    return items


def article_from_frontmatter(fm, filepath):
    """Genera tupla de artículo desde frontmatter parseado."""
    image = fm.get("image", "")
    if not image:
        return None

    filename = os.path.basename(image)

    # Si está en el catálogo manual, usar ese como override
    if filename in _CATALOG_INDEX:
        return _CATALOG_INDEX[filename]

    title = extract_title_from_frontmatter(fm.get("title", "SIN TÍTULO"))
    subtitle = truncate_subtitle(fm.get("description", ""))
    category = fm.get("category", "Linux")
    tags = fm.get("tags", [])
    tree_items = tags_to_tree(tags)

    return (filename, title, subtitle, category, tree_items)


# --- Generación --------------------------------------------------------------

def generate_image(filename, title, subtitle, category, tree_items):
    font_regular = ImageFont.truetype(FONT_PATH, 16)
    font_title = ImageFont.truetype(FONT_BOLD_PATH, 36)
    font_subtitle = ImageFont.truetype(FONT_PATH, 18)
    font_tree = ImageFont.truetype(FONT_PATH, 15)

    accent = CAT_COLORS.get(category, GREEN)

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # Borde exterior con color de acento
    draw.rectangle([20, 20, WIDTH - 21, HEIGHT - 21], outline=accent, width=2)

    # Ventana de terminal
    term_x, term_y = 50, 45
    term_w, term_h = WIDTH - 100, HEIGHT - 90
    draw.rectangle([term_x, term_y, term_x + term_w, term_y + term_h],
                    fill=TERMINAL_BG, outline=BORDER, width=1)

    # Barra de título
    bar_h = 32
    draw.rectangle([term_x, term_y, term_x + term_w, term_y + bar_h],
                    fill="#1C2128", outline=BORDER, width=1)

    # Dots (semáforo macOS)
    dot_y = term_y + bar_h // 2
    draw.ellipse([term_x + 14, dot_y - 5, term_x + 24, dot_y + 5], fill=DOT_RED)
    draw.ellipse([term_x + 32, dot_y - 5, term_x + 42, dot_y + 5], fill=DOT_YELLOW)
    draw.ellipse([term_x + 50, dot_y - 5, term_x + 60, dot_y + 5], fill=DOT_GREEN)

    # Prompt
    prompt_y = term_y + bar_h + 20
    draw.text((term_x + 20, prompt_y), "root@tengoping:~$ _", fill=MUTED, font=font_regular)

    # Título centrado
    title_y = prompt_y + 50
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_x = (WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((title_x, title_y), title, fill=accent, font=font_title)

    # Subtítulo centrado
    sub_y = title_y + 52
    bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    sub_x = (WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((sub_x, sub_y), subtitle, fill=TEXT, font=font_subtitle)

    # Árbol de ficheros
    tree_y = sub_y + 50
    for i, item in enumerate(tree_items):
        color = GREEN if "└" in item else MUTED
        draw.text((term_x + 60, tree_y + i * 24), item, fill=color, font=font_tree)

    path = os.path.join(OUT_DIR, filename)
    img.save(path, "JPEG", quality=90)
    return path


# --- Comandos ----------------------------------------------------------------

def cmd_list(args):
    """Lista las entradas del catálogo."""
    articles = ARTICLES
    if args.category:
        articles = [a for a in articles if a[3] == args.category]
    if not articles:
        print("No hay entradas para esa categoría.")
        return
    for a in articles:
        exists = "✓" if os.path.exists(os.path.join(OUT_DIR, a[0])) else "✗"
        print(f"  {exists} {a[0]:<30} [{a[3]}] {a[1]}")


def cmd_check(args):
    """Detecta imágenes huérfanas y faltantes."""
    # Recopilar imágenes referenciadas en frontmatter
    referenced = {}  # filename -> post filepath
    posts_sin_image = []

    for fname in sorted(os.listdir(CONTENT_DIR)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(CONTENT_DIR, fname)
        fm = parse_frontmatter(fpath)
        image = fm.get("image", "")
        if image:
            referenced[os.path.basename(image)] = fname
        else:
            posts_sin_image.append(fname)

    # Imágenes existentes en disco (solo .jpg generadas por este script)
    existing = set()
    if os.path.isdir(OUT_DIR):
        existing = {f for f in os.listdir(OUT_DIR) if f.endswith(".jpg")}

    # Faltantes: referenciadas pero no existen
    missing = {f: post for f, post in referenced.items() if f not in existing}

    # Huérfanas: existen pero no referenciadas (solo las .jpg que parecen generadas)
    orphans = existing - set(referenced.keys())

    print("=== Comprobación de imágenes ===\n")

    if missing:
        print(f"FALTANTES ({len(missing)}):")
        for img, post in sorted(missing.items()):
            print(f"  ✗ {img:<30} ← {post}")
    else:
        print("FALTANTES: ninguna ✓")

    print()
    if orphans:
        print(f"HUÉRFANAS ({len(orphans)}):")
        for img in sorted(orphans):
            print(f"  ? {img}")
    else:
        print("HUÉRFANAS: ninguna ✓")

    print()
    if posts_sin_image:
        print(f"POSTS SIN IMAGEN ({len(posts_sin_image)}):")
        for post in posts_sin_image:
            print(f"  - {post}")
    else:
        print("POSTS SIN IMAGEN: ninguno ✓")


def cmd_auto(args):
    """Auto-genera imágenes desde frontmatter de los .md."""
    articles = []
    for fname in sorted(os.listdir(CONTENT_DIR)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(CONTENT_DIR, fname)
        fm = parse_frontmatter(fpath)

        if fm.get("draft", False):
            continue

        article = article_from_frontmatter(fm, fpath)
        if not article:
            continue

        articles.append(article)

    if args.category:
        articles = [a for a in articles if a[3] == args.category]

    if not articles:
        print("No se encontraron artículos para generar.")
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    generated = 0
    skipped = 0

    for filename, title, subtitle, category, tree_items in articles:
        path = os.path.join(OUT_DIR, filename)
        if os.path.exists(path) and not args.force:
            skipped += 1
            continue
        generate_image(filename, title, subtitle, category, tree_items)
        print(f"  OK {filename:<30} [{category}] {title}")
        generated += 1

    print(f"\nGeneradas: {generated}  Omitidas: {skipped}  Total: {len(articles)}")


def cmd_new(args):
    """Modo interactivo para crear una imagen nueva."""
    print("=== Nueva imagen de portada ===\n")

    filename = input("Nombre del fichero (ej: mi-imagen.jpg): ").strip()
    if not filename:
        print("Nombre vacío, abortando.")
        return
    if not filename.endswith(".jpg"):
        filename += ".jpg"

    title = input("Título (texto grande en la imagen): ").strip().upper()
    if not title:
        print("Título vacío, abortando.")
        return

    subtitle = input("Subtítulo (texto pequeño): ").strip()

    # Menú de categorías
    cats = list(CAT_COLORS.keys())
    print("\nCategorías disponibles:")
    for i, cat in enumerate(cats, 1):
        print(f"  {i}. {cat}")
    try:
        choice = int(input("Elige categoría (número): ").strip())
        category = cats[choice - 1]
    except (ValueError, IndexError):
        print("Categoría inválida, usando 'Linux'.")
        category = "Linux"

    print("\nTree items (3 líneas, sin prefijo ├── / └──):")
    tree_items = []
    for i in range(3):
        item = input(f"  Item {i+1}: ").strip()
        if not item:
            break
        prefix = "└──" if i == 2 or (i < 2 and not item) else "├──"
        tree_items.append(f"{prefix} {item}")

    # Corregir último item
    if tree_items:
        last = tree_items[-1]
        if "├──" in last:
            tree_items[-1] = last.replace("├──", "└──")

    if not tree_items:
        tree_items = ["└── ..."]

    os.makedirs(OUT_DIR, exist_ok=True)
    path = generate_image(filename, title, subtitle, category, tree_items)
    print(f"\n  OK {path}")


def cmd_catalog(args):
    """Genera imágenes del catálogo ARTICLES."""
    articles = ARTICLES

    if args.category:
        articles = [a for a in articles if a[3] == args.category]

    # Filtrar por filenames específicos
    if args.files:
        articles = [a for a in articles if a[0] in args.files]
        if not articles:
            print(f"No se encontraron artículos para: {', '.join(args.files)}")
            print("Usa --list para ver los disponibles.")
            sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    for filename, title, subtitle, category, tree_items in articles:
        path = generate_image(filename, title, subtitle, category, tree_items)
        print(f"  OK {path}")

    print(f"\nGeneradas {len(articles)} imágenes en {OUT_DIR}")


# --- CLI ---------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Genera imágenes de portada con estética terminal para el blog.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s                          Genera todas las del catálogo
  %(prog)s fail2ban.jpg             Genera solo una del catálogo
  %(prog)s --auto                   Auto-genera desde frontmatter
  %(prog)s --auto --force           Regenera todas (sobreescribe)
  %(prog)s --auto --category Linux  Auto-genera solo las de Linux
  %(prog)s --new                    Modo interactivo
  %(prog)s --check                  Comprueba huérfanas/faltantes
  %(prog)s --list                   Lista el catálogo
        """,
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--auto", action="store_true",
                      help="auto-genera desde frontmatter de los .md")
    mode.add_argument("--new", action="store_true",
                      help="modo interactivo para crear una imagen nueva")
    mode.add_argument("--check", action="store_true",
                      help="detecta imágenes huérfanas y faltantes")
    mode.add_argument("--list", action="store_true",
                      help="lista las entradas del catálogo")

    parser.add_argument("--category", type=str, default=None,
                        help="filtra por categoría")
    parser.add_argument("--force", action="store_true",
                        help="sobreescribe imágenes existentes (con --auto)")
    parser.add_argument("files", nargs="*", metavar="fichero.jpg",
                        help="ficheros específicos del catálogo a generar")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.auto:
        cmd_auto(args)
    elif args.new:
        cmd_new(args)
    elif args.check:
        cmd_check(args)
    elif args.list:
        cmd_list(args)
    else:
        cmd_catalog(args)


if __name__ == "__main__":
    main()
