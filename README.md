# Website CV. Barokah Bersama Logistik (BBL)

Situs perusahaan profesional: **Home, Tentang Kami, Layanan & Armada, Portofolio, Artikel, Kontak** — responsif (HP & komputer), cepat, dan **gratis di-hosting di GitHub Pages**. Konten diubah lewat **panel admin `/admin/`** tanpa menyentuh kode.

| Kebutuhan | Solusi di proyek ini | Biaya |
|---|---|---|
| Hosting + HTTPS | GitHub Pages (otomatis dari repo) | Gratis |
| Panel admin / CMS | Sveltia CMS di `/admin/` (menyimpan ke GitHub) | Gratis |
| Formulir calon pelanggan + email | Web3Forms (notifikasi ke email) | Gratis (paket dasar) |
| WhatsApp | Tombol mengambang, tautan di setiap halaman, dan "Kirim via WhatsApp" di formulir | Gratis |
| Database | **Tidak diperlukan** — konten disimpan sebagai file di Git (lengkap dengan riwayat perubahan) | Gratis |
| Domain sendiri (opsional) | Beli di registrar, arahkan ke GitHub Pages | ± Rp 150–300 rb/tahun |
| Backup, monitoring, audit | GitHub Actions (terjadwal, otomatis) | Gratis |

## Mulai cepat

1. Buat repositori GitHub baru (mis. `bbl-website`), unggah seluruh isi folder ini ke cabang `main`.
2. Aktifkan **Settings → Pages → Source: GitHub Actions**.
3. Selesai — setiap *push* ke `main` otomatis membangun & mempublikasikan situs.

Langkah lengkap (termasuk domain, email formulir, dan login admin): **[docs/SETUP-GITHUB.md](docs/SETUP-GITHUB.md)**.

## Dokumentasi

| Dokumen | Isi |
|---|---|
| [docs/SETUP-GITHUB.md](docs/SETUP-GITHUB.md) | Publikasi pertama, domain, Web3Forms, login admin, keamanan akun |
| [docs/PANDUAN-ADMIN.md](docs/PANDUAN-ADMIN.md) | Cara mengubah teks, foto, layanan, armada, artikel, dan kontak |
| [docs/PEMELIHARAAN.md](docs/PEMELIHARAAN.md) | Pengujian, monitoring, backup, pembaruan, SEO, keamanan, pemecahan masalah |

## Struktur proyek

```
content/            Konten (JSON + artikel .md) — diedit lewat /admin/
static/uploads/     Foto & logo (juga lewat /admin/)
static/css|js|fonts Tampilan & skrip (situs publik tanpa framework static/css|js|fonts Tampilan & skrip (tanpa framework, tanpa CDN) tanpa CDN)
static/admin/       Panel admin (Sveltia CMS) + config.yml
templates/          Templat halaman (Jinja2)
build.py            Pembuat situs statis → folder _site/
scripts/            check_site.py (pemeriksa hasil build), check_live.py (monitoring)
tests/              Pengujian otomatis
.github/workflows/  deploy · pemeriksaan PR · monitoring · backup · Lighthouse
```

## Perintah lokal (opsional, untuk developer)

```bash
pip install -r requirements.txt
python build.py --serve                       # build + buka http://localhost:8000
python -m unittest discover -s tests -v       # jalankan 18 pengujian
python scripts/check_site.py _site            # periksa tautan, SEO, aksesibilitas
```

## Fitur teknis

- **Cepat**: tanpa framework JS; gambar otomatis jadi WebP berukuran responsif (320–1600 px) dengan `srcset`, lazy-loading, font disajikan sendiri (tanpa Google Fonts), CSS/JS kecil.
- **SEO**: judul & deskripsi per halaman, canonical, Open Graph/Twitter Card, JSON-LD (Organisasi, Artikel, Breadcrumb), `sitemap.xml`, `robots.txt`, struktur heading rapi.
- **Aman**: situs statis (tanpa server/database yang bisa diretas), Content-Security-Policy ketat, tanpa skrip inline, tautan eksternal `noopener`, honeypot anti-spam, HTTPS dari GitHub Pages.
- **Aksesibel**: tautan lompat, fokus terlihat, label formulir, dukungan *reduced motion*, kontras warna terjaga.
- **Privasi**: dokumen identitas pribadi (KTP, NPWP pribadi) **tidak** dipublikasikan; pengujian otomatis menjaga hal ini.
