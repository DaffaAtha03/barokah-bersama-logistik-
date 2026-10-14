#!/usr/bin/env python3
"""
Generator situs statis CV. Barokah Bersama Logistik.

Membaca konten dari folder `content/` (diedit lewat CMS di /admin/),
merender template Jinja2 di `templates/`, mengoptimasi gambar (WebP +
ukuran responsif), lalu menulis hasilnya ke folder `_site/`.

Pemakaian:
    python build.py                 # build ke _site/
    python build.py --serve         # build lalu jalankan server lokal :8000

Variabel lingkungan (opsional):
    SITE_URL            URL publik lengkap, mis. https://nama.github.io/repo
    GITHUB_REPOSITORY   "pemilik/repo" — dipakai untuk mengisi config CMS
    BBL_OUT             folder keluaran (default: _site)
"""
from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import math
import os
import re
import shutil
import socketserver
import sys
from datetime import date, datetime
from functools import partial
from pathlib import Path
from urllib.parse import quote, urlparse

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt
from markupsafe import Markup, escape
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = Path(os.environ.get("BBL_OUT") or ROOT / "_site")
CACHE = ROOT / ".cache" / "images"

RASTER = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
WIDTHS = (320, 480, 640, 800, 960, 1280, 1600)
MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
          "Agustus", "September", "Oktober", "November", "Desember"]

WARNINGS: list[str] = []


def warn(msg: str) -> None:
    WARNINGS.append(msg)
    print(f"  ! {msg}")


# --------------------------------------------------------------------------
# Konten
# --------------------------------------------------------------------------
def load_json(name: str) -> dict:
    path = CONTENT / name
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"[ERROR] {name} bukan JSON yang valid: {exc}")
    except FileNotFoundError:
        sys.exit(f"[ERROR] File konten tidak ditemukan: {path}")


SITE = load_json("site.json")
HOME = load_json("home.json")
ABOUT = load_json("about.json")
LAYANAN = load_json("layanan.json")
ARMADA = load_json("armada.json")
PORTOFOLIO = load_json("portofolio.json")

SITE_URL = (os.environ.get("SITE_URL") or SITE.get("url") or "http://localhost:8000").strip().rstrip("/")
BASE = urlparse(SITE_URL).path.rstrip("/")  # "" atau "/nama-repo"


def u(path: str) -> str:
    """URL relatif-root dengan awalan base path (untuk GitHub Pages project site)."""
    if not path:
        return BASE + "/"
    if re.match(r"^(https?:|mailto:|tel:|#|//)", path):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return BASE + path


_parsed = urlparse(SITE_URL)
ORIGIN = f"{_parsed.scheme}://{_parsed.netloc}"


def abs_url(path: str) -> str:
    """URL absolut. Path yang sudah berawalan BASE (hasil u()) tidak digandakan."""
    if not path:
        return SITE_URL + "/"
    if re.match(r"^https?://", path):
        return path
    if not path.startswith("/"):
        path = "/" + path
    if BASE and path.startswith(BASE + "/"):
        return ORIGIN + path
    return SITE_URL + path


# --------------------------------------------------------------------------
# Gambar: WebP + varian responsif
# --------------------------------------------------------------------------
_IMG_CACHE: dict[str, dict | None] = {}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def process_image(src: str) -> dict | None:
    if src in _IMG_CACHE:
        return _IMG_CACHE[src]
    file = STATIC / src.lstrip("/")
    if not file.is_file():
        warn(f"Gambar tidak ditemukan: {src}")
        _IMG_CACHE[src] = None
        return None

    digest = hashlib.sha1(file.read_bytes()).hexdigest()[:8]
    stem = f"{_slug(file.stem)}-{digest}"
    CACHE.mkdir(parents=True, exist_ok=True)
    out_dir = OUT / "assets" / "gen"
    out_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(file) as im:
        im = ImageOps.exif_transpose(im)
        W, H = im.size
        has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        im = im.convert("RGBA" if has_alpha else "RGB")
        targets = [w for w in WIDTHS if w < W]
        targets.append(min(W, WIDTHS[-1]))
        variants = []
        for w in targets:
            h = round(H * w / W)
            fb_ext = "png" if has_alpha else "jpg"
            webp_name, fb_name = f"{stem}-{w}.webp", f"{stem}-{w}.{fb_ext}"
            for name in (webp_name, fb_name):
                cached = CACHE / name
                if not cached.exists():
                    resized = im if w == W else im.resize((w, h), Image.LANCZOS)
                    if name.endswith(".webp"):
                        resized.save(cached, "WEBP", quality=80, method=4)
                    elif name.endswith(".png"):
                        resized.save(cached, "PNG", optimize=True)
                    else:
                        resized.save(cached, "JPEG", quality=82, optimize=True, progressive=True)
                shutil.copyfile(cached, out_dir / name)
            variants.append({"w": w, "h": h,
                             "webp": u(f"/assets/gen/{webp_name}"),
                             "fb": u(f"/assets/gen/{fb_name}")})
    info = {"w": variants[-1]["w"], "h": variants[-1]["h"], "variants": variants}
    _IMG_CACHE[src] = info
    return info


def img(src: str, alt: str = "", sizes: str = "100vw", cls: str = "",
        eager: bool = False) -> Markup:
    info = process_image(src) if src else None
    if not info:
        return Markup("")
    v = info["variants"]
    webp_set = ", ".join(f"{x['webp']} {x['w']}w" for x in v)
    fb_set = ", ".join(f"{x['fb']} {x['w']}w" for x in v)
    mid = v[min(len(v) - 1, 2)]
    loading = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    class_attr = f' class="{escape(cls)}"' if cls else ""
    return Markup(
        f'<picture><source type="image/webp" srcset="{webp_set}" sizes="{escape(sizes)}">'
        f'<img src="{mid["fb"]}" srcset="{fb_set}" sizes="{escape(sizes)}" '
        f'width="{info["w"]}" height="{info["h"]}" alt="{escape(alt)}" '
        f'{loading} decoding="async"{class_attr}></picture>'
    )


def img_full(src: str) -> str:
    info = process_image(src) if src else None
    return info["variants"][-1]["webp"] if info else ""


def img_ratio(src: str) -> str:
    info = process_image(src) if src else None
    return f'{info["w"]} / {info["h"]}' if info else "4 / 3"


# --------------------------------------------------------------------------
# Ikon (SVG garis)
# --------------------------------------------------------------------------
ICONS = {
    "truck": '<path d="M3 6h11v10H3z"/><path d="M14 9h4l3 3v4h-7z"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
    "route": '<circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h8a3.5 3.5 0 000-7H8a3.5 3.5 0 010-7h8"/>',
    "file": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    "bolt": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "store": '<path d="M4 9l1-5h14l1 5"/><path d="M4 9a2.5 2.5 0 005 0 2.5 2.5 0 006 0 2.5 2.5 0 005 0"/><path d="M5 12v8h14v-8"/>',
    "box": '<path d="M12 3l9 4.5v9L12 21l-9-4.5v-9z"/><path d="M3 7.5l9 4.5 9-4.5M12 12v9"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "handshake": '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.5"/><path d="M17 14c2.5 0 4.5 2 4.5 4.5"/>',
    "scale": '<path d="M12 3v18M7 21h10M5 7h14"/><path d="M5 7l-3 7a3 3 0 006 0zM19 7l-3 7a3 3 0 006 0z"/>',
    "refresh": '<path d="M20 12a8 8 0 11-2.3-5.7"/><path d="M20 4v5h-5"/>',
    "check": '<path d="M5 12l5 5 9-10"/>',
    "phone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2z"/>',
    "whatsapp": '<path d="M3 21l1.6-4.6A8.5 8.5 0 1112 20.5a8.4 8.4 0 01-4-1z"/><path d="M9 9.5c0 3 2.5 5.5 5.5 5.5l1-1.5-2-1-1 .8a4 4 0 01-1.8-1.8l.8-1-1-2z"/>',
    "pin": '<path d="M12 21s7-6 7-11a7 7 0 10-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M8 3v4M16 3v4M3.5 10h17"/>',
    "zoom": '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4-4"/>',
    "chevron": '<path d="M6 9l6 6 6-6"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".6"/>',
    "facebook": '<path d="M14 8h2V4h-3a4 4 0 00-4 4v2H7v4h2v6h4v-6h2.5l.5-4h-3V8.5a.5.5 0 01.5-.5z"/>',
    "linkedin": '<rect x="3" y="9" width="4" height="12"/><circle cx="5" cy="5" r="2"/><path d="M10 9h4v2c1-1.5 2.5-2.4 4-2.4 2.5 0 3 1.8 3 4.4V21h-4v-6.5c0-1.2-.3-2-1.5-2S14 13.3 14 14.5V21h-4z"/>',
    "tiktok": '<path d="M14 3v11.5a3.5 3.5 0 11-3.5-3.5"/><path d="M14 3c.3 2.5 2 4.2 4.5 4.5"/>',
    "youtube": '<rect x="2.5" y="5.5" width="19" height="13" rx="4"/><path d="M10 9.5v5l4.5-2.5z"/>',
}


def icon(name: str, cls: str = "") -> Markup:
    body = ICONS.get(name)
    if body is None:
        warn(f"Ikon tidak dikenal: {name}")
        body = ICONS["box"]
    c = f"icon {cls}".strip()
    return Markup(
        f'<svg class="{c}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>'
    )


# --------------------------------------------------------------------------
# Helper tampilan
# --------------------------------------------------------------------------
def tanggal(value) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, str):
        value = date.fromisoformat(value[:10])
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}"


def iso_date(value) -> str:
    if isinstance(value, datetime):
        value = value.date()
    return value.isoformat()


def nl2p(text: str) -> Markup:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    return Markup("".join(f"<p>{escape(p).replace(chr(10), Markup('<br>'))}</p>" for p in parts))


def digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def phone_display(value: str) -> str:
    d = digits(value)
    if len(d) >= 10:
        return f"{d[:4]}-{d[4:8]}-{d[8:]}"
    return value


def phone_href(value: str) -> str:
    d = digits(value)
    if d.startswith("0"):
        d = "62" + d[1:]
    return f"tel:+{d}"


def wa_url(text: str | None = None) -> str:
    msg = text if text is not None else SITE.get("pesan_whatsapp", "")
    return f"https://wa.me/{digits(SITE.get('whatsapp', ''))}?text={quote(msg)}"


def highlight(text: str, part: str) -> Markup:
    """Bungkus bagian teks dengan <em> untuk sorotan warna."""
    safe = escape(text)
    if part and part in text:
        safe = safe.replace(escape(part), Markup(f"<em>{escape(part)}</em>"))
    return Markup(safe)


def json_ld(data: dict) -> Markup:
    raw = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return Markup(raw)


# --------------------------------------------------------------------------
# Markdown artikel
# --------------------------------------------------------------------------
def make_markdown() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": True})
    md.enable(["table", "strikethrough"])

    def render_image(self, tokens, idx, options, env):
        tok = tokens[idx]
        src = tok.attrGet("src") or ""
        alt = self.renderInlineAsText(tok.children, options, env)
        if src.startswith("/"):
            return str(img(src, alt, "(min-width: 820px) 760px, 100vw"))
        return f'<img src="{escape(src)}" alt="{escape(alt)}" loading="lazy" decoding="async">'

    def render_link_open(self, tokens, idx, options, env):
        tok = tokens[idx]
        href = tok.attrGet("href") or ""
        if href.startswith("/") and not href.startswith("//"):
            tok.attrSet("href", u(href))
        elif re.match(r"^https?://", href):
            tok.attrSet("rel", "noopener noreferrer")
        return self.renderToken(tokens, idx, options, env)

    md.add_render_rule("image", render_image)
    md.add_render_rule("link_open", render_link_open)
    return md


def load_articles() -> list[dict]:
    md = make_markdown()
    posts = []
    for path in sorted((CONTENT / "artikel").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
        if not m:
            warn(f"Artikel tanpa front matter dilewati: {path.name}")
            continue
        meta = yaml.safe_load(m.group(1)) or {}
        if meta.get("draft"):
            continue
        body = m.group(2).strip()
        d = meta.get("date") or date.today()
        if isinstance(d, datetime):
            d = d.date()
        elif isinstance(d, str):
            d = date.fromisoformat(d[:10])
        words = len(re.findall(r"\w+", body))
        posts.append({
            "slug": path.stem,
            "title": str(meta.get("title") or path.stem.replace("-", " ").title()),
            "date": d,
            "summary": str(meta.get("summary") or ""),
            "image": meta.get("image") or "",
            "image_alt": str(meta.get("image_alt") or meta.get("title") or ""),
            "html": Markup(md.render(body)),
            "minutes": max(1, math.ceil(words / 200)),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


# --------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------
NAV = [
    ("Home", "/"),
    ("Tentang Kami", "/tentang-kami/"),
    ("Layanan", "/layanan/"),
    ("Portofolio", "/portofolio/"),
    ("Artikel", "/artikel/"),
    ("Kontak", "/kontak/"),
]

SOCIAL_LABELS = {"instagram": "Instagram", "facebook": "Facebook", "linkedin": "LinkedIn",
                 "tiktok": "TikTok", "youtube": "YouTube"}


def build_env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                      autoescape=select_autoescape(["html", "xml"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.filters.update(tanggal=tanggal, iso_date=iso_date, nl2p=nl2p, digits=digits,
                       phone_display=phone_display, phone_href=phone_href,
                       highlight=highlight, json_ld=json_ld)
    socials = [(k, SOCIAL_LABELS[k], v) for k, v in (SITE.get("sosial") or {}).items()
               if v and k in SOCIAL_LABELS]
    asset_hash = hashlib.sha1()
    for p in sorted((STATIC / "css").glob("*.css")) + sorted((STATIC / "js").glob("*.js")):
        asset_hash.update(p.read_bytes())
    env.globals.update(
        site=SITE, home=HOME, about=ABOUT, layanan_data=LAYANAN, armada=ARMADA["armada"],
        portofolio=PORTOFOLIO, nav=NAV, socials=socials, u=u, abs_url=abs_url, img=img,
        img_full=img_full, img_ratio=img_ratio, icon=icon, wa_url=wa_url,
        year=date.today().year, build_id=asset_hash.hexdigest()[:8], site_url=SITE_URL,
        has_form_key=bool(SITE.get("form_access_key")),
    )
    return env


def org_jsonld() -> dict:
    addr = SITE.get("alamat", "")
    street = addr.split(",")[0:2]
    data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": abs_url("/#organisasi"),
        "name": SITE["nama"],
        "alternateName": SITE.get("singkatan", ""),
        "description": SITE.get("deskripsi", ""),
        "url": abs_url("/"),
        "logo": abs_url(img_full(SITE.get("logo", "")) or ""),
        "image": abs_url(SITE.get("og_image", "")),
        "telephone": "+" + digits(SITE.get("whatsapp", "")),
        "email": SITE.get("email", ""),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": ", ".join(s.strip() for s in street),
            "addressLocality": "Cibitung",
            "addressRegion": "Jawa Barat",
            "addressCountry": "ID",
        },
        "foundingDate": str(SITE.get("tahun_berdiri", "")),
    }
    same = [v for v in (SITE.get("sosial") or {}).values() if v]
    if same:
        data["sameAs"] = same
    return data


def breadcrumb(items: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": abs_url(path)}
            for i, (name, path) in enumerate(items)
        ],
    }


def write(rel: str, content: str) -> None:
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")


def copy_static() -> None:
    for sub in ("css", "js", "fonts", "img"):
        shutil.copytree(STATIC / sub, OUT / sub, dirs_exist_ok=True)
    # Unggahan: gambar raster diproses ke assets/gen; berkas lain (PDF dll) disalin apa adanya.
    up = STATIC / "uploads"
    if up.is_dir():
        for f in up.rglob("*"):
            if f.is_file() and f.suffix.lower() not in RASTER:
                dest = OUT / "uploads" / f.relative_to(up)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, dest)
        og = SITE.get("og_image", "")
        if og.startswith("/uploads/") and (STATIC / og.lstrip("/")).is_file():
            dest = OUT / og.lstrip("/")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(STATIC / og.lstrip("/"), dest)
    # Panel admin (CMS)
    admin_src = STATIC / "admin"
    if admin_src.is_dir():
        shutil.copytree(admin_src, OUT / "admin", dirs_exist_ok=True)
        cfg = OUT / "admin" / "config.yml"
        if cfg.is_file():
            text = cfg.read_text(encoding="utf-8")
            repo = os.environ.get("GITHUB_REPOSITORY")
            if repo:
                text = text.replace("OWNER/REPO", repo)
            text = text.replace("__SITE_URL__", SITE_URL)
            cfg.write_text(text, encoding="utf-8")
    cname = ROOT / "CNAME"
    if cname.is_file():
        shutil.copyfile(cname, OUT / "CNAME")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")


def build() -> None:
    print(f"Membangun situs → {SITE_URL}")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    env = build_env()
    articles = load_articles()
    org = org_jsonld()
    default_og = SITE.get("og_image", "")

    def fit(text: str, limit: int) -> str:
        """Pangkas di batas kata agar tampil utuh di hasil pencarian."""
        text = " ".join(str(text).split())
        if len(text) <= limit:
            return text
        return text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:-—|") + "…"

    def render(template: str, rel: str, path: str, title: str, description: str, **ctx) -> None:
        ctx.setdefault("jsonld", [])
        title, description = fit(title, 70), fit(description, 160)
        html = env.get_template(template).render(
            page_title=title, page_desc=description, page_path=path,
            og_image=ctx.pop("og_image", default_og), **ctx)
        write(rel, html)

    nama, pendek = SITE["nama"], SITE["nama_pendek"]
    sitemap: list[tuple[str, str]] = []
    today = date.today().isoformat()

    # Home
    render("index.html", "index.html", "/",
           f"Jasa {SITE['tagline'].split(' dan ')[0]} Bekasi | {nama}", SITE["deskripsi"],
           articles=articles[:3], jsonld=[org], is_home=True)
    sitemap.append(("/", today))

    # Tentang kami
    render("tentang.html", "tentang-kami/index.html", "/tentang-kami/",
           f"Tentang Kami | {pendek}",
           "Profil, visi, misi, dan legalitas CV. Barokah Bersama Logistik — mitra transportasi logistik dan perdagangan di Cibitung, Bekasi.",
           jsonld=[breadcrumb([("Home", "/"), ("Tentang Kami", "/tentang-kami/")])])
    sitemap.append(("/tentang-kami/", today))

    # Layanan
    render("layanan.html", "layanan/index.html", "/layanan/",
           f"Layanan & Armada | {pendek}",
           "Angkutan barang darat, ekspedisi muatan, jasa pengurusan transportasi, kurir, dan perdagangan. Armada CDE, CDD, Fuso, dan Wing Box.",
           jsonld=[breadcrumb([("Home", "/"), ("Layanan & Armada", "/layanan/")])])
    sitemap.append(("/layanan/", today))

    # Portofolio
    kategori = []
    for it in PORTOFOLIO.get("item", []):
        if it.get("kategori") and it["kategori"] not in kategori:
            kategori.append(it["kategori"])
    render("portofolio.html", "portofolio/index.html", "/portofolio/",
           f"Portofolio | {pendek}",
           "Dokumentasi armada dan operasional CV. Barokah Bersama Logistik.",
           kategori=kategori,
           jsonld=[breadcrumb([("Home", "/"), ("Portofolio", "/portofolio/")])])
    sitemap.append(("/portofolio/", today))

    # Artikel
    render("artikel_list.html", "artikel/index.html", "/artikel/",
           f"Artikel & Wawasan Logistik | {pendek}",
           "Panduan dan tips seputar pengiriman barang, pemilihan armada, pengemasan, dan dokumen logistik.",
           articles=articles,
           jsonld=[breadcrumb([("Home", "/"), ("Artikel", "/artikel/")])])
    sitemap.append(("/artikel/", articles[0]["date"].isoformat() if articles else today))
    for i, post in enumerate(articles):
        others = [p for p in articles if p["slug"] != post["slug"]][:2]
        path = f"/artikel/{post['slug']}/"
        og = post["image"] if post["image"] and process_image(post["image"]) else default_og
        if og and og.startswith("/uploads/") and og != default_og:
            # OG harus berupa berkas yang bisa diakses: pakai varian terbesar hasil optimasi.
            og = img_full(og)
        article_ld = {
            "@context": "https://schema.org", "@type": "BlogPosting",
            "headline": post["title"], "description": post["summary"],
            "datePublished": post["date"].isoformat(), "dateModified": post["date"].isoformat(),
            "mainEntityOfPage": abs_url(path),
            "image": abs_url(og) if og else "",
            "author": {"@type": "Organization", "name": nama},
            "publisher": {"@type": "Organization", "name": nama,
                          "logo": {"@type": "ImageObject", "url": abs_url(img_full(SITE.get("logo", "")) or "")}},
        }
        render("artikel_detail.html", f"artikel/{post['slug']}/index.html", path,
               (f"{post['title']} | {pendek}" if len(post["title"]) + len(pendek) + 3 <= 70 else post["title"]),
               post["summary"] or SITE["deskripsi"],
               post=post, others=others, og_image=og, og_type="article",
               jsonld=[article_ld, breadcrumb([("Home", "/"), ("Artikel", "/artikel/"), (post["title"], path)])])
        sitemap.append((path, post["date"].isoformat()))

    # Kontak
    render("kontak.html", "kontak/index.html", "/kontak/",
           f"Kontak & Minta Penawaran | {pendek}",
           "Hubungi CV. Barokah Bersama Logistik lewat formulir, WhatsApp, telepon, atau email. Minta penawaran pengiriman Anda.",
           services=[s["judul"] for s in LAYANAN["layanan"]],
           fleets=[a["nama"] for a in ARMADA["armada"]],
           jsonld=[breadcrumb([("Home", "/"), ("Kontak", "/kontak/")])])
    sitemap.append(("/kontak/", today))

    # Halaman pendukung
    render("terima_kasih.html", "terima-kasih/index.html", "/terima-kasih/",
           f"Terima Kasih | {pendek}", "Permintaan Anda telah kami terima.", noindex=True)
    render("privasi.html", "kebijakan-privasi/index.html", "/kebijakan-privasi/",
           f"Kebijakan Privasi | {pendek}",
           "Bagaimana CV. Barokah Bersama Logistik mengelola data yang Anda kirim lewat formulir.")
    sitemap.append(("/kebijakan-privasi/", today))
    render("404.html", "404.html", "/404.html", f"Halaman tidak ditemukan | {pendek}",
           "Halaman yang Anda cari tidak ditemukan.", noindex=True)

    # sitemap & robots
    urls = "\n".join(
        f"  <url><loc>{escape(abs_url(p))}</loc><lastmod>{d}</lastmod></url>" for p, d in sitemap)
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "\n</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: {SITE_URL}/sitemap.xml\n")

    copy_static()

    pages = len(sitemap) + 2
    print(f"Selesai: {pages} halaman, {len(articles)} artikel, "
          f"{len(_IMG_CACHE)} gambar dioptimasi, {len(WARNINGS)} peringatan.")
    if not SITE.get("form_access_key"):
        print("  i form_access_key kosong: formulir akan memakai WhatsApp sebagai cadangan.")


def serve(port: int) -> None:
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Server lokal: http://localhost:{port}{BASE}/  (Ctrl+C untuk berhenti)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serve", action="store_true", help="jalankan server lokal setelah build")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    build()
    if args.serve:
        serve(args.port)
