# Panduan Setup GitHub (sekali saja)

Estimasi waktu: 20–30 menit. Semua gratis.

## 1. Buat akun & repositori

1. Daftar di <https://github.com> (gunakan email perusahaan, mis. `barokahbersamalogistic165@gmail.com`).
2. **Aktifkan verifikasi 2 langkah (2FA)**: *Settings → Password and authentication*. Ini perlindungan terpenting untuk situs Anda.
3. Klik **New repository** → nama: `bbl-website` → **Public** (GitHub Pages gratis memerlukan repo publik untuk akun gratis) → *Create*.
4. Unggah seluruh isi folder proyek ke cabang **`main`** (via *Add file → Upload files*, atau `git push`). Pastikan folder `.github/` ikut terunggah.

> **Catatan privasi:** repo publik berarti kode dan konten situs terlihat publik — sama seperti situsnya. Jangan pernah mengunggah dokumen pribadi/rahasia ke repo ini.

## 2. Aktifkan GitHub Pages

*Settings → Pages → Build and deployment → Source: **GitHub Actions***.

Buka tab **Actions**: workflow **Deploy situs** akan berjalan (±1–2 menit). Setelah hijau ✅, alamat situs muncul di *Settings → Pages*, biasanya:

- `https://NAMA-AKUN.github.io/bbl-website/` (repo biasa), atau
- `https://NAMA-AKUN.github.io/` jika repo bernama `NAMA-AKUN.github.io`.

Kedua bentuk didukung otomatis — tidak ada yang perlu diubah di kode.

## 3. Aktifkan notifikasi email formulir (Web3Forms)

Tanpa langkah ini, tombol *Kirim permintaan* otomatis mengarahkan pengunjung ke WhatsApp (tetap berfungsi), tetapi Anda tidak mendapat email.

1. Buka <https://web3forms.com> → masukkan email penerima (mis. `barokahbersamalogistic165@gmail.com`) → *Create Access Key*.
2. Cek email, salin **Access Key** (berbentuk `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).
3. Buka panel admin (langkah 5) → **Pengaturan Situs → Access Key Web3Forms** → tempel → *Save*.
4. Tunggu deploy selesai, lalu kirim formulir uji dari halaman Kontak. Email masuk ke kotak masuk (cek juga *Spam* untuk pertama kali).

Access Key memang **bersifat publik** (aman ada di kode); Web3Forms hanya mengirim ke email yang Anda daftarkan. Untuk perlindungan spam tambahan, aktifkan hCaptcha di dasbor Web3Forms.

## 4. (Opsional) Domain sendiri, mis. `barokahlogistik.co.id`

1. Beli domain di registrar (mis. Niagahoster, Rumahweb, Namecheap, atau Cloudflare Registrar).
2. Di pengaturan DNS domain, tambahkan:
   - 4 record **A** untuk `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - 1 record **CNAME** untuk `www` → `NAMA-AKUN.github.io`
   (Periksa alamat IP terbaru di dokumentasi GitHub: *"Managing a custom domain for your GitHub Pages site"*.)
3. Di repo, buat file bernama **`CNAME`** di folder utama, isinya satu baris: `barokahlogistik.co.id`.
4. *Settings → Pages → Custom domain* → isi domain → centang **Enforce HTTPS** (muncul setelah sertifikat terbit, ±15 menit–24 jam).
5. Buat variabel repo `SITE_URL` bila perlu (lihat PEMELIHARAAN.md) — biasanya tidak perlu karena workflow otomatis membaca alamat dari GitHub.

Setelah domain aktif, daftarkan juga di **Google Search Console** (lihat *Pemeliharaan → SEO*).

## 5. Login ke panel admin

Alamat: `https://ALAMAT-SITUS/admin/`

Panel ini memakai **login dengan token GitHub** (tanpa server tambahan, jadi tetap gratis):

1. Buat token: GitHub → *Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token*.
   - *Repository access*: **Only select repositories** → pilih `bbl-website`.
   - *Permissions → Repository permissions → **Contents: Read and write*** (Metadata: Read otomatis).
   - Masa berlaku: 90 hari atau 1 tahun (buat ulang saat habis).
2. Salin token (hanya tampil sekali!), simpan di *password manager*.
3. Buka `/admin/` → klik **Sign In with Token** → tempel token. Token tersimpan di browser Anda saja.

**Aturan keamanan token:** jangan dibagikan lewat chat/email; satu token per orang; cabut (*Revoke*) segera bila perangkat hilang. Untuk memberi akses staf, undang akun GitHub mereka sebagai *Collaborator* (*Settings → Collaborators*) — mereka membuat token sendiri.

> Bila nama cabang utama bukan `main`, ubah `branch: main` di `static/admin/config.yml`.

## 6. Pengaturan keamanan yang disarankan

- **Branch protection** (opsional, untuk tim): *Settings → Branches → Add rule* untuk `main`.
- **Notifikasi**: pastikan Anda *Watch → All activity* di repo agar email peringatan (monitoring) tiba.
- Aktifkan **Dependabot alerts** (*Settings → Code security*) — gratis.
- Aktifkan **Secret scanning** bila tersedia.

## 7. Verifikasi cepat

- [ ] Situs terbuka dengan HTTPS (gembok)
- [ ] Semua 6 menu berfungsi, tampilan rapi di HP
- [ ] Tombol WhatsApp membuka chat ke 0853-1222-6023 dengan pesan awal
- [ ] Formulir uji → email masuk
- [ ] `/admin/` bisa login & ubah satu teks → situs terbarui dalam ±2 menit
- [ ] Tab *Actions*: Deploy ✅, jalankan manual *Monitoring situs* ✅ dan *Backup mingguan* ✅
