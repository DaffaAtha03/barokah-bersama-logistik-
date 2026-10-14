# Pemeliharaan: pengujian, monitoring, backup, pembaruan, SEO, keamanan

Semua otomatis di **GitHub Actions** (tab *Actions* di repo). Anda hanya perlu memperhatikan email dari GitHub dan melakukan tinjauan ringan berkala.

## 1. Pengujian otomatis (setiap perubahan)

Workflow **Deploy situs** menjalankan, sebelum publikasi:

1. **18 pengujian** (`tests/`): konten valid, setiap gambar yang dirujuk ada, konfigurasi admin cocok dengan konten, sitemap/robots benar, CSP terpasang, tidak ada dokumen identitas pribadi, build berhasil dengan awalan path GitHub Pages.
2. **Pemeriksa hasil build** (`scripts/check_site.py`): tautan/gambar/anchor rusak, `<title>`, meta description, canonical, satu `<h1>`, atribut `alt`, `id` ganda.

Bila ada yang gagal, **situs lama tetap tayang** (tidak rusak) dan Anda melihat ❌ di Actions beserta alasannya. Perubahan lewat *Pull Request* menjalankan pemeriksaan yang sama (`ci.yml`).

## 2. Monitoring (tiap 6 jam)

Workflow **Monitoring situs** (`monitor.yml`) membuka semua halaman di `sitemap.xml` dan memastikan: HTTP 200, memuat nama perusahaan, tidak lambat (> 4 dtk = catatan), dan `robots.txt` tidak memblokir seluruh situs.

- **Bila gagal** → otomatis membuat **Issue "🚨 Situs tidak sehat"** → GitHub mengirim email ke Anda.
- **Bila pulih** → Issue ditutup otomatis.
- Coba manual: *Actions → Monitoring situs → Run workflow*.

Variabel opsional: *Settings → Secrets and variables → Actions → Variables → `SITE_URL`* (mis. `https://barokahlogistik.co.id`) bila alamat tidak terdeteksi otomatis.

> **Penting:** GitHub menonaktifkan workflow terjadwal setelah **60 hari tanpa aktivitas repo**. Karena Anda rutin mengubah konten (commit) dan ada backup, ini jarang terjadi; bila ada email "scheduled workflows disabled", klik *Enable* di tab Actions.

Pemantau luar (disarankan sebagai lapisan kedua, gratis): **UptimeRobot** atau **Better Stack** → pantau `https://ALAMAT-SITUS/` tiap 5 menit dengan email/WhatsApp alert.

## 3. Backup (mingguan)

Workflow **Backup mingguan** (`backup.yml`, Senin dini hari WIB) membuat **GitHub Release** `backup-YYYY-MM-DD` berisi:
- `bbl-website-….bundle` — salinan git penuh dengan seluruh riwayat,
- `bbl-website-….zip` — berkas terkini (mudah dibuka).

Disimpan **12 backup terakhir**. Selain itu, **setiap perubahan konten sudah tercatat di Git** sehingga bisa dikembalikan ke versi mana pun.

**Memulihkan:**
- *Satu perubahan salah* → repo → *Commits* → **Revert**.
- *Repo terhapus/rusak* → unduh `.bundle` dari Release (atau dari salinan Anda) → `git clone bbl-website-….bundle bbl-website` → buat repo baru & `git push`.
- Sebagai pengaman tambahan: sekali per bulan unduh `.zip` terbaru dan simpan di Google Drive/penyimpanan perusahaan.

## 4. Pembaruan

| Komponen | Cara diperbarui |
|---|---|
| GitHub Actions & pustaka Python | **Dependabot** membuat Pull Request tiap minggu. Pastikan pemeriksaan ✅ lalu *Merge*. |
| Panel admin (Sveltia CMS) | Versi di-**pin** di `static/admin/index.html` (`@sveltia/cms@0.237.0`). Per 3–6 bulan: cek rilis di <https://github.com/sveltia/sveltia-cms/releases>, ganti nomor versi, buka `/admin/` dan uji ubah+simpan satu konten. |
| Font | Self-hosted (Inter, lisensi OFL) — tidak perlu pembaruan. |
| Domain | Perpanjang tahunan; aktifkan *auto-renew* dan kunci domain (registrar lock). |
| Token admin | Fine-grained token kedaluwarsa — buat ulang sebelum habis (catat tanggalnya). |

## 5. Kecepatan & kualitas (bulanan)

Workflow **Audit Lighthouse** (tanggal 1 tiap bulan, atau manual) menilai Performance, Accessibility, Best Practices, SEO untuk Home/Layanan/Kontak. Lihat ringkasan & artifact di run-nya. Target: semua ≥ 90. Penyebab skor turun yang paling umum: foto baru berukuran sangat besar (kompres < 1 MB sebelum unggah), skrip pihak ketiga yang ditambahkan.

## 6. SEO — langkah sekali jalan setelah situs live

1. **Google Search Console** → tambah properti (URL-prefix) → verifikasi (metode *HTML tag*: tempel meta ke `templates/base.html` atau minta developer; atau verifikasi lewat DNS bila punya domain) → **Sitemaps → kirim `sitemap.xml`**.
2. **Google Business Profile** (gratis): daftarkan lokasi *Jl. Garuda Raya GB 4, Wanasari, Cibitung, Bekasi*, kategori "Perusahaan pengangkutan/ekspedisi", isi nomor & tautan situs. Ini paling berpengaruh untuk pencarian lokal ("ekspedisi Cibitung").
3. Pastikan nama, alamat, telepon (NAP) **sama persis** di situs, Google Business, dan media sosial.
4. Tulis 1–2 artikel per bulan yang menjawab pertanyaan pelanggan nyata.
5. Pasang tautan situs di bio WhatsApp Business, Instagram, dan marketplace/direktori bisnis.

Sudah otomatis: sitemap, robots, canonical, JSON-LD, Open Graph, judul/deskripsi unik per halaman, URL bersih, gambar responsif, HTTPS.

## 7. Keamanan

- Situs **statis** — tidak ada server, database, atau plugin yang dapat diretas. Risiko utama ada di **akun GitHub** → wajib 2FA, token fine-grained, cabut token yang tidak dipakai.
- **Content-Security-Policy** membatasi skrip/gambar/koneksi hanya ke sumber yang dibutuhkan (situs sendiri, Web3Forms, Google Maps). Bila menambah layanan pihak ketiga baru (mis. widget chat), CSP di `templates/base.html` perlu diperbarui.
- Data formulir hanya melewati Web3Forms ke email Anda; tidak disimpan di situs. Cantumkan hal ini di **Kebijakan Privasi** (sudah ada halamannya — sesuaikan bila Anda menambah Analytics).
- Jangan menaruh kata sandi, token, atau dokumen pribadi di repo. Fitur *Secret scanning* GitHub membantu mendeteksi.
- Bila akun staf berhenti bekerja → hapus dari *Collaborators* dan cabut tokennya.

## 8. Jadwal pemeliharaan ringkas

| Kapan | Tugas | ± Waktu |
|---|---|---|
| Setiap email peringatan | Baca Issue "Situs tidak sehat"/gagal deploy, ikuti pemecahan masalah di bawah | 5–15 mnt |
| Mingguan | Merge PR Dependabot yang ✅ | 5 mnt |
| Bulanan | Cek laporan Lighthouse & Search Console; unduh backup .zip; tambah artikel | 30 mnt |
| 3–6 bulan | Perbarui versi Sveltia CMS; periksa masa berlaku token; tinjau konten (kontak, armada, legalitas) | 30 mnt |
| Tahunan | Perpanjang domain; tinjau Kebijakan Privasi & dokumen legalitas yang ditampilkan | 30 mnt |

## 9. Pemecahan masalah

| Gejala | Penyebab umum | Solusi |
|---|---|---|
| Deploy ❌ "check_site" | Tautan/anchor rusak setelah mengubah slug layanan/armada | Baca log, perbaiki ID tautan di panel |
| Deploy ❌ "unittest … image … tidak ada" | Menghapus foto yang masih dipakai | Pulihkan foto atau ganti referensinya di konten |
| Situs tampil tanpa gaya (CSS hilang) | URL dasar salah (mis. domain diganti tanpa `CNAME`) | Pastikan file `CNAME` benar & Pages memakai domain itu; jalankan ulang Deploy |
| Admin: "Sign In with Token" gagal | Token kedaluwarsa / izin kurang / repo salah | Buat token baru: *Contents: Read and write* hanya untuk repo ini |
| Admin menyimpan tapi situs tak berubah | Deploy gagal atau cabang bukan `main` | Cek tab Actions; cek `branch:` di `static/admin/config.yml` |
| Formulir: email tak datang | Access Key kosong/salah; email masuk Spam | Periksa Pengaturan Situs → Access Key; cek dasbor Web3Forms |
| Formulir langsung membuka WhatsApp | Access Key kosong (mode cadangan) | Isi Access Key |
| Peta kosong | Pemblokir iklan/privasi browser | Gunakan tautan "Buka di Google Maps" |
| Email Issue "Situs tidak sehat" | Pages down sementara atau deploy rusak | Buka Actions → *Monitoring situs* → lihat laporan; jalankan ulang *Deploy situs* |

## 10. Catatan konten & hukum yang perlu ditinjau pemilik

- **Legalitas:** halaman *Tentang Kami* menampilkan daftar dokumen (Akta, SK Kemenkumham, NPWP, SKT, NIB, Izin Usaha & Izin Lokasi OSS). Pada salinan 2019 yang diberikan, **Izin Usaha tertulis "belum berlaku efektif"** sampai komitmen dipenuhi. Perbarui ke status terkini di OSS (oss.go.id) dan sesuaikan teks bila perlu sebelum mengklaim "legalitas lengkap".
- **Kapasitas armada** sengaja dikosongkan; isi hanya dengan angka yang pasti.
- **Sambutan pimpinan** adalah teks awal yang perlu disetujui/diganti oleh pimpinan; isi juga nama & jabatan bila berkenan.
- **Portofolio** memuat dokumentasi armada; tambahkan proyek/klien nyata dengan persetujuan klien.
- **Statistik beranda** (mis. tahun berdiri 2019) diambil dari dokumen resmi; ubah di panel bila perlu.
