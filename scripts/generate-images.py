#!/usr/bin/env python3
"""
Genera imágenes de portada para los artículos del blog con estética terminal.

Uso:
  python3 scripts/generate-images.py                    # Genera todas
  python3 scripts/generate-images.py fail2ban.jpg       # Genera solo una
  python3 scripts/generate-images.py --list              # Lista las disponibles

Requisitos:
  pip install Pillow
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# --- Configuración -----------------------------------------------------------

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "images")
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
}

# --- Catálogo de artículos ----------------------------------------------------
# (filename, title, subtitle, category, [tree_items])

ARTICLES = [
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
]


# --- Generación ---------------------------------------------------------------

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


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    if "--list" in sys.argv:
        for a in ARTICLES:
            print(f"  {a[0]:<30} [{a[3]}] {a[1]}")
        return

    # Filtrar por nombre si se pasan argumentos
    targets = [a for a in sys.argv[1:] if not a.startswith("-")]
    articles = ARTICLES
    if targets:
        articles = [a for a in ARTICLES if a[0] in targets]
        if not articles:
            print(f"No se encontraron artículos para: {', '.join(targets)}")
            print("Usa --list para ver los disponibles")
            sys.exit(1)

    for filename, title, subtitle, category, tree_items in articles:
        path = generate_image(filename, title, subtitle, category, tree_items)
        print(f"OK {path}")

    print(f"\nGeneradas {len(articles)} imágenes en {OUT_DIR}")


if __name__ == "__main__":
    main()
