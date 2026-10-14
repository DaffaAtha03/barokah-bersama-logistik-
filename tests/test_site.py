"""
Pengujian otomatis situs BBL (pustaka standar + PyYAML, sama seperti build).

Jalankan:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
FAKE_URL = "https://contoh.github.io/bbl-site"


def run(*args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run([sys.executable, *args], cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)


class ContentTests(unittest.TestCase):
    def test_all_json_valid(self):
        for f in CONTENT.glob("*.json"):
            with self.subTest(file=f.name):
                json.loads(f.read_text(encoding="utf-8"))

    def test_site_identity_and_contact(self):
        site = json.loads((CONTENT / "site.json").read_text(encoding="utf-8"))
        self.assertTrue(site["nama"])
        self.assertRegex(site["whatsapp"], r"^62\d{8,13}$", "WhatsApp harus format internasional tanpa + (62…)")
        self.assertRegex(site["email"], r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        key = site.get("form_access_key", "")
        if key:
            self.assertRegex(key, r"^[0-9a-fA-F-]{36}$", "Access key Web3Forms berbentuk UUID")

    def test_every_uploaded_image_reference_exists(self):
        refs: set[str] = set()
        for f in list(CONTENT.rglob("*.json")) + list(CONTENT.rglob("*.md")):
            refs |= set(re.findall(r"/uploads/[A-Za-z0-9_./-]+\.(?:jpg|jpeg|png|webp|gif|pdf)", f.read_text(encoding="utf-8")))
        self.assertTrue(refs, "tidak ada referensi gambar ditemukan")
        for r in sorted(refs):
            with self.subTest(ref=r):
                self.assertTrue((STATIC / r.lstrip("/")).is_file(), f"{r} dirujuk konten tetapi tidak ada di static/uploads")

    def test_articles_have_required_front_matter(self):
        for f in (CONTENT / "artikel").glob("*.md"):
            text = f.read_text(encoding="utf-8")
            m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
            self.assertIsNotNone(m, f"{f.name}: front matter hilang")
            fm = yaml.safe_load(m.group(1))
            for k in ("title", "date", "summary"):
                self.assertIn(k, fm, f"{f.name}: field '{k}' wajib ada")

    def test_no_personal_identity_documents_published(self):
        """Dokumen identitas pribadi (KTP, NPWP pribadi, KK, paspor) tidak boleh masuk ke situs publik."""
        banned = re.compile(r"(^|[-_ ])(ktp|npwp|kk|paspor|passport|sim)([-_. ]|$)", re.I)
        for f in STATIC.rglob("*"):
            if f.is_file():
                self.assertIsNone(banned.search(f.name), f"{f.relative_to(ROOT)} tampak seperti dokumen identitas pribadi")


class CmsConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = yaml.safe_load((STATIC / "admin" / "config.yml").read_text(encoding="utf-8"))

    def test_backend_and_media(self):
        self.assertEqual(self.cfg["backend"]["name"], "github")
        self.assertEqual(self.cfg["backend"]["repo"], "OWNER/REPO")
        self.assertTrue((ROOT / self.cfg["media_folder"]).is_dir())

    def test_collections_point_to_existing_content(self):
        for col in self.cfg["collections"]:
            if "folder" in col:
                self.assertTrue((ROOT / col["folder"]).is_dir(), col["name"])
            for item in col.get("files", []):
                with self.subTest(file=item["file"]):
                    self.assertTrue((ROOT / item["file"]).is_file())

    def test_cms_fields_cover_content_keys(self):
        """Setiap kunci tingkat-atas di file JSON konten harus bisa diedit di CMS."""
        for col in self.cfg["collections"]:
            for item in col.get("files", []):
                data = json.loads((ROOT / item["file"]).read_text(encoding="utf-8"))
                cms_keys = {f["name"] for f in item["fields"]}
                missing = set(data) - cms_keys
                with self.subTest(file=item["file"]):
                    self.assertFalse(missing, f"Kunci tidak bisa diedit di CMS: {sorted(missing)}")

    def test_admin_page_pins_cms_version(self):
        html = (STATIC / "admin" / "index.html").read_text(encoding="utf-8")
        self.assertRegex(html, r"@sveltia/cms@\d+\.\d+\.\d+/", "versi CMS harus di-pin")
        self.assertIn("noindex", html)


class BuildTests(unittest.TestCase):
    """Membangun situs dengan URL berawalan path (seperti GitHub Pages project) dan memeriksanya."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "site"
        cls.build = run("build.py", env_extra={"SITE_URL": FAKE_URL, "BBL_OUT": str(cls.out), "GITHUB_REPOSITORY": "contoh/bbl-site"})

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_build_succeeds_without_warnings(self):
        self.assertEqual(self.build.returncode, 0, self.build.stdout + self.build.stderr)
        self.assertIn("0 peringatan", self.build.stdout)

    def test_expected_pages_exist(self):
        for rel in ("index.html", "tentang-kami/index.html", "layanan/index.html", "portofolio/index.html",
                    "artikel/index.html", "kontak/index.html", "kebijakan-privasi/index.html", "404.html",
                    "sitemap.xml", "robots.txt", ".nojekyll", "admin/index.html", "admin/config.yml"):
            with self.subTest(rel=rel):
                self.assertTrue((self.out / rel).is_file())

    def test_site_checker_passes_with_base_path(self):
        r = run("scripts/check_site.py", str(self.out), "--base", "/bbl-site")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_cms_config_is_filled_for_repo(self):
        cfg = (self.out / "admin" / "config.yml").read_text(encoding="utf-8")
        self.assertIn("repo: contoh/bbl-site", cfg)
        self.assertNotIn("OWNER/REPO", cfg)
        self.assertNotIn("__SITE_URL__", cfg)

    def test_robots_and_sitemap(self):
        robots = (self.out / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Disallow: /admin/", robots)
        self.assertIn(f"Sitemap: {FAKE_URL}/sitemap.xml", robots)
        self.assertNotRegex(robots, r"(?m)^Disallow:\s*/\s*$", "jangan blokir seluruh situs")
        sm = (self.out / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn(f"{FAKE_URL}/layanan/", sm)
        self.assertNotIn("/admin/", sm)

    def test_security_and_seo_markup_on_home(self):
        html = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn("Content-Security-Policy", html)
        self.assertIn("object-src 'none'", html)
        self.assertIn(f'<link rel="canonical" href="{FAKE_URL}/">', html)
        self.assertIn("application/ld+json", html)
        self.assertIn('property="og:image"', html)
        self.assertNotIn("<script>", html.replace('<script type="application/ld+json">', ""), "tidak boleh ada skrip inline (CSP)")

    def test_internal_links_use_base_path(self):
        html = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/bbl-site/layanan/', html)
        self.assertNotRegex(html, r'href="/layanan/')

    def test_default_build_has_no_base_path(self):
        with tempfile.TemporaryDirectory() as d:
            r = run("build.py", env_extra={"SITE_URL": "https://contoh.id", "BBL_OUT": d})
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            html = (Path(d) / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="/layanan/', html)
            self.assertIn('<link rel="canonical" href="https://contoh.id/">', html)

    def test_images_are_optimised(self):
        gen = list((self.out / "assets").rglob("*.webp"))
        self.assertGreater(len(gen), 10)
        total = sum(f.stat().st_size for f in self.out.rglob("*") if f.is_file())
        self.assertLess(total, 8 * 1024 * 1024, "ukuran situs > 8 MB, periksa gambar")


if __name__ == "__main__":
    unittest.main()
