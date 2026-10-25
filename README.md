# 🖱️ Auto Clicker Macro Pro

Aplikasi perekam dan pemutar jejak klik mouse otomatis yang dapat berjalan di latar belakang (background) dengan kontrol **Global Hotkey** dan pengaturan jeda waktu (delay) fleksibel per klik.

Cocok digunakan untuk mengotomatiskan tugas rutin harian, klik berulang pada aplikasi, input data berkala, atau game.

---

## 🚀 Fitur Utama

1. **Perekaman Jejak Klik (Click Recorder)**:
   - Rekam klik kiri, kanan, klik tengah, dan klik ganda.
   - Mengabaikan klik pada jendela aplikasi itu sendiri agar rekaman tetap rapi dan bersih.
   - Perekaman langsung di latar belakang (*background*) tanpa harus membuka-tutup aplikasi.

2. **Pengaturan Jeda Waktu (Delay) Fleksibel**:
   - Tiap langkah memiliki kolom input jeda waktu (dalam detik).
   - Anda bebas mengubah jeda tiap klik secara langsung (contoh: ubah Step 1 menjadi `2.5` detik, Step 2 menjadi `0.5` detik, dsb).
   - Tersedia estimasi total durasi per putaran.

3. **Global Shortcut (Hotkey) dari Background**:
   - `[F6]` : **Mulai / Selesai Rekam** (Bisa ditekan saat Anda sedang membuka aplikasi lain).
   - `[F7]` : **Putar (Play) / Jeda (Pause)** skrip makro.
   - `[F8]` : **Stop Darurat (Emergency Stop)** seketika menghentikan semua klik otomatis.

4. **Pengulangan (Looping)**:
   - Pilihan jumlah putaran: `1 Kali`, `2 Kali`, `3 Kali`, `5 Kali`, `10 Kali`, atau `Berulang Terus (Infinite)`.
   - Pengaturan jeda waktu antar putaran.
   - Opsi *Minimize otomatis saat Play* agar layar tidak tertutup.

5. **Simpan & Muat Script Harian (Save / Load JSON)**:
   - Simpan skrip ke file (misal: `tugas_harian.json`).
   - Setiap hari Anda cukup membuka aplikasi, memuat file tersebut, lalu menekan **Play (F7)**.
   - Sesi terakhir otomatis tersimpan (*auto-restore*), sehingga jika aplikasi ditutup, langkah Anda kemarin tidak akan hilang.

---

## 🖥️ Cara Menjalankan Aplikasi

### Cara 1: Menggunakan File EXE (Paling Praktis)
Langsung klik ganda file **`AutoClickerPro.exe`** di folder ini. Tidak memerlukan instalasi Python atau aplikasi pihak ketiga lainnya.

### Cara 2: Menggunakan File Batch
Klik ganda file **`run.bat`** di folder project.

### Cara 3: Lewat Terminal / PowerShell
```bash
python main.py
```

---

## 📖 Panduan Penggunaan Harian

1. **Merekam Jejak Klik Baru**:
   - Buka aplikasi atau layar yang ingin Anda klik.
   - Tekan tombol **`[F6]`** di keyboard (atau klik tombol *Rekam* di aplikasi).
   - Lakukan klik pada target sesuai urutan langkah Anda.
   - Setelah selesai, tekan **`[F6]`** kembali untuk menghentikan rekaman.

2. **Menyesuaikan Jeda Waktu**:
   - Lihat daftar langkah di aplikasi.
   - Ubah angka pada kolom jeda waktu jika ingin mempercepat atau memperlambat jeda sebelum klik tertentu dijalankan.
   - Anda juga bisa menekan tombol **`🎯 Tes`** di sebelah kanan tiap baris untuk menguji klik langkah tersebut saja.

3. **Menyimpan Skrip**:
   - Klik **`💾 Simpan Script`** dan simpan dengan nama yang Anda inginkan (misal `absen_pagi.json`).

4. **Menjalankan Setiap Hari**:
   - Buka aplikasi, klik **`📂 Buka Script`** (atau skrip terakhir akan langsung termuat otomatis).
   - Buka jendela target di layar Anda.
   - Tekan **`[F7]`** untuk memutar. Mouse akan mengklik otomatis sesuai urutan dan jeda waktu yang telah ditentukan!
   - Tekan **`[F8]`** kapan saja jika ingin membatalkan/menghentikan klik secara darurat.
