#!/usr/bin/env python3
"""
Pemeriksa kualitas hasil build (tanpa dependensi, hanya pustaka standar Python).

Memeriksa semua halaman HTML di folder hasil build:
  - tautan internal, gambar, CSS, dan JS yang rusak (404)
  - anchor (#bagian) yang tidak ada di halaman tujuan
  - SEO dasar: <title>, meta description, canonical, tepat satu <h1>, atribut lang
  - aksesibilitas dasar: <img> tanpa atribut alt, id ganda
  - sitemap.xml & robots.txt konsisten dengan halaman yang ada

Pemakaian:
    python scripts/check_site.py _site [--base /nama-repo]

Kode keluar 1 bila ada KESALAHAN (error). Peringatan (warning) tidak menggagalkan.
"""
from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag, urlparse
import xml.etree.ElementTree as ET


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.lang = ""
        self.h1 = 0
        self.ids: list[str] = []
        self.refs: list[tuple[str, str]] = []  # (tag, url)
        self.imgs_no_alt = 0
        self.imgs_total = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang", "")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            rel = a.get("rel", "")
            if rel == "canonical":
                self.canonical = a.get("href", "")
            elif a.get("href") and rel in {"stylesheet", "icon", "apple-touch-icon", "manifest", "preload"}:
                self.refs.append(("link", a["href"]))
        elif tag == "h1":
            self.h1 += 1
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "a" and a.get("href"):
            self.refs.append(("a", a["href"]))
        elif tag in {"script", "source", "img", "video", "audio", "iframe"} and a.get("src"):
            self.refs.append((tag, a["src"]))
        if tag in {"img", "source"} and a.get("srcset"):
            for part in a["srcset"].split(","):
                url = part.strip().split(" ")[0]
                if url:
                    self.refs.append((tag, url))
        if tag == "img":
            self.imgs_total += 1
            if "alt" not in a:
                self.imgs_no_alt += 1
        if tag == "form" and a.get("action"):
            self.refs.append(("form", a["action"]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default="_site")
    ap.add_argument("--base", default=None, help="awalan path situs, mis. /nama-repo (default: dari SITE_URL)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Folder {root} tidak ada. Jalankan `python build.py` dulu.")
        return 2

    base = args.base
    if base is None:
        import os
        base = urlparse(os.environ.get("SITE_URL", "")).path.rstrip("/")
    base = base.rstrip("/")

    errors: list[str] = []
    warnings: list[str] = []
    pages: dict[str, PageParser] = {}

    for f in sorted(root.rglob("*.html")):
        rel = f.relative_to(root).as_posix()
        if rel.startswith("admin/"):
            continue
        p = PageParser()
        p.feed(f.read_text(encoding="utf-8"))
        pages[rel] = p

    def resolve(url_path: str) -> Path | None:
        """Ubah path URL (sudah tanpa base) menjadi berkas di disk, atau None bila tidak ada."""
        path = unquote(url_path)
        cand = root / path.lstrip("/")
        if path.endswith("/") or path == "":
            cand = cand / "index.html"
        if cand.is_file():
            return cand
        if (cand / "index.html").is_file():
            return cand / "index.html"
        return None

    for rel, p in pages.items():
        where = f"/{rel}"
        noindex = "noindex" in p.meta.get("robots", "")
        if not p.lang:
            errors.append(f"{where}: atribut lang pada <html> tidak ada")
        title = p.title.strip()
        if not title:
            errors.append(f"{where}: <title> kosong")
        elif len(title) > 70:
            warnings.append(f"{where}: <title> {len(title)} karakter (disarankan ≤ 60-70)")
        desc = p.meta.get("description", "").strip()
        if not desc and not noindex:
            errors.append(f"{where}: meta description tidak ada")
        elif desc and len(desc) > 170:
            warnings.append(f"{where}: meta description {len(desc)} karakter (disarankan ≤ 160)")
        if not p.canonical and rel != "404.html":
            errors.append(f"{where}: link canonical tidak ada")
        if p.h1 != 1:
            errors.append(f"{where}: harus ada tepat satu <h1> (ditemukan {p.h1})")
        if p.imgs_no_alt:
            errors.append(f"{where}: {p.imgs_no_alt} gambar tanpa atribut alt")
        dup = {i for i in p.ids if p.ids.count(i) > 1}
        if dup:
            errors.append(f"{where}: id ganda: {', '.join(sorted(dup))}")

        for tag, url in p.refs:
            if re.match(r"^(mailto:|tel:|javascript:|data:|https?:|//)", url, re.I):
                continue
            clean, frag = urldefrag(url)
            if clean == "":
                target_page = p
                target_rel = rel
            else:
                u = urlparse(clean)
                path = u.path
                if not path.startswith("/"):
                    path = "/" + str((Path("/" + rel).parent / path).as_posix())
                if base and path.startswith(base + "/") or path == base:
                    path = path[len(base):] or "/"
                elif base and tag != "form":
                    errors.append(f"{where}: tautan internal tanpa awalan '{base}': {url}")
                    continue
                target = resolve(path)
                if target is None:
                    errors.append(f"{where}: <{tag}> menuju berkas yang tidak ada: {url}")
                    continue
                target_rel = target.relative_to(root).as_posix()
                target_page = pages.get(target_rel)
            if frag and target_page is not None and frag not in target_page.ids:
                errors.append(f"{where}: anchor #{frag} tidak ditemukan di /{target_rel} (dari {url})")

    # sitemap
    sm = root / "sitemap.xml"
    if not sm.is_file():
        errors.append("sitemap.xml tidak ada")
    else:
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        try:
            locs = [e.text or "" for e in ET.parse(sm).getroot().findall(".//s:loc", ns)]
        except ET.ParseError as exc:
            locs = []
            errors.append(f"sitemap.xml tidak valid: {exc}")
        for loc in locs:
            path = urlparse(loc).path
            if base and path.startswith(base):
                path = path[len(base):] or "/"
            if resolve(path) is None:
                errors.append(f"sitemap.xml: {loc} tidak punya halaman")
        if locs and len(locs) < 6:
            warnings.append(f"sitemap.xml hanya berisi {len(locs)} URL")
    robots = root / "robots.txt"
    if not robots.is_file():
        errors.append("robots.txt tidak ada")
    elif "Sitemap:" not in robots.read_text(encoding="utf-8"):
        warnings.append("robots.txt tidak mencantumkan Sitemap")

    for w in warnings:
        print(f"  ⚠ {w}")
    for e in errors:
        print(f"  ✗ {e}")
    print(f"\nDiperiksa {len(pages)} halaman: {len(errors)} kesalahan, {len(warnings)} peringatan.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
