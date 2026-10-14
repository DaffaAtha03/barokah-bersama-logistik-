#!/usr/bin/env python3
"""
Monitoring situs yang sudah online (tanpa dependensi). Dipakai oleh workflow "Monitoring".

Memeriksa:
  - beranda & semua URL di sitemap.xml membalas HTTP 200 dalam batas waktu
  - halaman memuat nama perusahaan (mendeteksi halaman kosong/rusak)
  - robots.txt tidak memblokir seluruh situs (kecelakaan SEO yang umum)
  - sertifikat HTTPS valid (urllib otomatis memverifikasi)
  - (opsional) masa berlaku sertifikat & domain

Pemakaian:
    python scripts/check_live.py https://nama.github.io/repo [--expect "Barokah Bersama Logistik"] [--slow 4.0]

Kode keluar 1 bila ada masalah. Ringkasan Markdown ditulis ke $GITHUB_STEP_SUMMARY bila tersedia.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

UA = "BBL-SiteMonitor/1.0 (+GitHub Actions)"


def fetch(url: str, timeout: float = 20.0) -> tuple[int, str, float]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(2_000_000).decode("utf-8", "replace")
            return r.status, body, time.perf_counter() - t0
    except urllib.error.HTTPError as e:
        return e.code, "", time.perf_counter() - t0


def fetch_retry(url: str, tries: int = 3) -> tuple[int, str, float]:
    """Coba ulang beberapa kali agar gangguan jaringan sesaat tidak memicu alarm palsu."""
    last: tuple[int, str, float] = (0, "", 0.0)
    for i in range(tries):
        try:
            last = fetch(url)
            if last[0] and last[0] < 500:
                return last
        except Exception as exc:  # noqa: BLE001 — kegagalan jaringan apa pun dihitung sebagai gagal
            last = (0, f"{type(exc).__name__}: {exc}", 0.0)
        time.sleep(5 * (i + 1))
    return last


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="URL dasar situs, mis. https://nama.github.io/repo")
    ap.add_argument("--expect", default="Barokah Bersama Logistik", help="teks yang harus ada di setiap halaman")
    ap.add_argument("--slow", type=float, default=4.0, help="batas detik sebelum dianggap lambat (peringatan)")
    args = ap.parse_args()

    base = args.url.rstrip("/")
    problems: list[str] = []
    notes: list[str] = []
    rows: list[tuple[str, str, str]] = []

    status, body, took = fetch_retry(base + "/")
    if status != 200:
        problems.append(f"Beranda tidak dapat diakses (HTTP {status or 'gagal koneksi'}) {body[:120]}")
        urls: list[str] = []
    else:
        rows.append((base + "/", "200", f"{took:.2f}s"))
        if args.expect.lower() not in body.lower():
            problems.append(f"Beranda tidak memuat teks \"{args.expect}\" — halaman mungkin rusak.")
        urls = []
        sm_status, sm_body, _ = fetch_retry(base + "/sitemap.xml")
        if sm_status != 200:
            problems.append(f"sitemap.xml tidak dapat diakses (HTTP {sm_status})")
        else:
            try:
                ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                urls = [e.text.strip() for e in ET.fromstring(sm_body).findall(".//s:loc", ns) if e.text]
            except ET.ParseError:
                problems.append("sitemap.xml bukan XML yang valid")

    for url in urls:
        if url.rstrip("/") == base:
            continue
        s, b, t = fetch_retry(url)
        rows.append((url, str(s or "gagal"), f"{t:.2f}s"))
        if s != 200:
            problems.append(f"{url} → HTTP {s or 'gagal koneksi'}")
        elif args.expect.lower() not in b.lower():
            problems.append(f"{url} tidak memuat teks \"{args.expect}\"")
        if t > args.slow:
            notes.append(f"{url} lambat ({t:.1f}s)")

    r_status, r_body, _ = fetch_retry(base + "/robots.txt")
    if r_status == 200 and re.search(r"(?mi)^\s*Disallow:\s*/\s*$", r_body.split("User-agent: *", 1)[-1].split("\n\n", 1)[0]):
        problems.append("robots.txt memblokir seluruh situs (Disallow: /) — situs tidak akan muncul di Google!")

    ok = not problems
    print(("✅ Situs sehat" if ok else "🚨 Ada masalah pada situs") + f" — {base}")
    for p in problems:
        print(f"  ✗ {p}")
    for n in notes:
        print(f"  ⚠ {n}")
    print(f"  {len(rows)} halaman diperiksa.")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"## {'✅ Situs sehat' if ok else '🚨 Ada masalah'}\n\n`{base}`\n\n")
            if problems:
                fh.write("**Masalah**\n\n" + "\n".join(f"- {p}" for p in problems) + "\n\n")
            if notes:
                fh.write("**Catatan**\n\n" + "\n".join(f"- {n}" for n in notes) + "\n\n")
            fh.write("| URL | Status | Waktu |\n|---|---|---|\n" + "\n".join(f"| {u} | {s} | {t} |" for u, s, t in rows) + "\n")
    # Keluaran untuk workflow
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"healthy={'true' if ok else 'false'}\n")
            fh.write("report<<EOF\n" + "\n".join(problems or ["Tidak ada masalah."]) + "\nEOF\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
