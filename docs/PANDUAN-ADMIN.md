# Panduan Admin — mengubah isi website tanpa kode

Buka **`https://ALAMAT-SITUS/admin/`** → **Sign In with Token** (lihat [SETUP-GITHUB.md](SETUP-GITHUB.md) bagian 5).

Setiap kali Anda menekan **Save / Publish**, perubahan tersimpan ke GitHub dan situs otomatis diperbarui dalam **±1–3 menit**. Setiap perubahan tercatat (siapa, kapan, apa) di riwayat GitHub dan bisa dibatalkan.

## Peta menu panel

| Menu di panel | Yang diubah |
|---|---|
| **Artikel** | Tulis, ubah, hapus artikel/berita |
| **Konten Halaman → Halaman Home** | Judul & foto utama, statistik, keunggulan, langkah proses, ajakan (CTA) |
| **Konten Halaman → Halaman Tentang Kami** | Profil, visi, misi, sambutan pimpinan, daftar legalitas |
| **Konten Halaman → Halaman Layanan** | Daftar layanan, poin unggulan, FAQ |
| **Konten Halaman → Armada** | Jenis armada, deskripsi, kapasitas, foto & galeri |
| **Konten Halaman → Portofolio** | Proyek/dokumentasi + kategori filter |
| **Pengaturan Situs** | Nama, logo, telepon, WhatsApp, email, alamat, jam operasional, media sosial, Web3Forms, Google Analytics |

## Tugas yang paling sering

### Menulis artikel
1. **Artikel → New Artikel**.
2. Isi **Judul**, **Tanggal terbit**, **Ringkasan** (1–2 kalimat, ±160 karakter — tampil di Google), **Gambar utama** (+ deskripsi gambar), lalu **Isi artikel**.
3. Di editor: gunakan *Heading 2* untuk sub-judul, daftar, tebal, dan tautan. Hindari memakai Heading 1 (judul sudah otomatis).
4. Ingin menyimpan dulu tanpa tayang? Aktifkan **Simpan sebagai draf**.
5. **Publish**.

Tips artikel yang disukai Google: 500+ kata, jawab satu pertanyaan nyata pelanggan (mis. "biaya kirim CDD ke…", "cara memilih armada"), gunakan kata yang dicari orang, tambahkan tautan ke halaman [Kontak](/kontak/) di akhir.

### Mengganti foto
- Klik kolom gambar → **Upload** (atau pilih dari yang sudah ada).
- Ukuran ideal: **lebar ≥ 1200 px**, format JPG/PNG, < 5 MB. Sistem otomatis membuat versi WebP yang ringan untuk HP.
- **Selalu isi "Deskripsi foto"** (alt text) — penting untuk SEO & pembaca layar. Contoh: *"Truk CDD hijau di area gudang Cibitung"*.
- Foto utama hero sebaiknya landscape (rasio ± 5:4). Foto pimpinan potret (4:5).

### Menambah layanan baru
**Halaman Layanan → Daftar layanan → Add**: isi *ID tautan* (huruf kecil tanpa spasi, mis. `gudang`), pilih *Ikon*, *Nama layanan*, *Deskripsi singkat*, dan *Poin unggulan*. Layanan baru otomatis muncul di Home, halaman Layanan, dan footer.

### Menambah/ubah armada
**Armada → Daftar armada → Add**: nama (mis. *Tronton*), jenis, deskripsi, **Kapasitas muatan** (opsional — isi hanya bila angka sudah pasti, mis. `±2,5 ton`), foto utama, dan galeri.

### Menambah portofolio / proyek
**Portofolio → Daftar portofolio → Add**: judul, **Kategori** (dipakai sebagai tombol filter; tulis konsisten, mis. `Armada`, `Proyek`, `Kegiatan`), deskripsi, klien (hanya jika **klien mengizinkan nama dicantumkan**), tahun, dan gambar.

> Portofolio saat ini berisi dokumentasi armada dari company profile. Tambahkan proyek/klien nyata setelah ada izin untuk menampilkannya — jangan mencantumkan klien tanpa persetujuan.

### Mengubah kontak & WhatsApp
**Pengaturan Situs**: ubah *Nomor telepon*, *Nomor WhatsApp* (format internasional **tanpa +**, mis. `6285312226023`), *Email*, *Alamat*, dan *Pesan awal tombol WhatsApp*. Kosongkan *Jam operasional* bila tidak ingin ditampilkan.

### Mengaktifkan media sosial
Isi URL lengkap (mis. `https://instagram.com/akunanda`) di **Pengaturan Situs → Media sosial**. Ikon hanya tampil untuk kolom yang terisi.

### Mengaktifkan email notifikasi formulir
**Pengaturan Situs → Access Key Web3Forms** (lihat SETUP-GITHUB.md bagian 3).

### Statistik pengunjung (opsional)
Isi **ID Google Analytics 4** (`G-XXXXXXXXXX`) di Pengaturan Situs. Bila kosong, tidak ada pelacak sama sekali (lebih privat & lebih cepat). Bila diisi, sebutkan hal ini di Kebijakan Privasi.

## Aturan agar situs tetap rapi

- Judul beranda ≤ ±70 karakter dan deskripsi ≤ ±155 karakter (dipangkas otomatis, tetapi lebih baik ditulis ringkas).
- Teks tombol singkat (1–3 kata).
- "Bagian judul yang diberi warna" di Hero harus **persis sama** dengan sebagian kalimat judul.
- Jangan unggah dokumen identitas pribadi (KTP, NPWP pribadi, KK, paspor) — situs ini publik. Sistem pengujian otomatis akan menolak berkas bernama seperti itu.
- Dokumen legalitas perusahaan: tampilkan sebagai daftar (sudah tersedia). Bila ingin menayangkan salinan, sensor nomor/QR sensitif lebih dulu.

## Bila sesuatu tidak tampil / salah

1. Tunggu 3 menit, muat ulang dengan **Ctrl+F5** (HP: tutup tab, buka lagi).
2. Buka repo GitHub → tab **Actions**: bila ada ❌ merah pada *Deploy situs*, klik untuk melihat penyebabnya (biasanya kolom terisi tidak valid). Perbaiki di panel & simpan lagi.
3. Ingin membatalkan perubahan? Repo → *Commits* → pilih perubahan → **Revert**. Atau minta bantuan developer dengan menyebutkan waktu perubahan.
