# Remotion App (Termux)

Proyek starter Remotion yang sudah terpasang di Termux.

## Versi terpasang
- Node.js: v26.4.0
- npm: 11.21.1
- FFmpeg/ffprobe: 9.0.2
- Remotion: 4.0.547 (remotion, @remotion/cli)
- React: 19.3.1
- TypeScript: 5.9 (TS 7 native tidak mendukung Android)

## Struktur
```
remotion-app/
├─ src/
│  ├─ index.ts    # entry point (registerRoot)
│  ├─ Root.tsx    # daftar komposisi
│  └─ Hello.tsx   # contoh komposisi 1080x1920, 30fps, 90 frame
├─ remotion.config.ts
├─ remotion.sh    # wrapper CLI untuk Termux
└─ package.json
```

## Perintah
Jalankan dari folder `~/remotion-app`:

```bash
cd ~/remotion-app

# Buka Remotion Studio (server lokal)
./remotion.sh studio

# Render komposisi "Hello" ke MP4
./remotion.sh render Hello out/hello.mp4

# Bundle saja (tanpa render)
./remotion.sh bundle src/index.ts --out-dir build
```

Bisa juga lewat npm:

```bash
npm run studio
npm run render -- Hello out/hello.mp4
npm run bundle
```

## Render via GitHub Actions (disarankan)

Workflow sudah tersedia di `.github/workflows/render.yml` dan dijalankan manual
(`workflow_dispatch`).

1. Login & buat repo (sekali saja):

```bash
cd ~/remotion-app
gh auth login
gh repo create remotion-app --public --source=. --remote=origin --push
```

2. Trigger render dari terminal:

```bash
gh workflow run render.yml -f composition=Hello -f output=out/hello.mp4
gh run watch
```

3. Unduh hasilnya (artifact `rendered-video`):

```bash
gh run download --name rendered-video
```

Bisa juga lewat tab **Actions → Render Video → Run workflow** di GitHub.

Atau pakai wrapper satu perintah (trigger + tunggu + unduh otomatis):

```bash
./render-cloud.sh Hello out/hello.mp4
```

Input workflow:
- `composition` — ID komposisi, default `Hello`
- `output` — path output, default `out/video.mp4`
- `frames` — opsional, mis. `0-89` untuk render sebagian

## Catatan penting


### 1. Wrapper `remotion.sh`
Shebang `#!/usr/bin/env node` tidak bekerja langsung di Termux (tidak ada `/usr/bin/env`).
Wrapper ini menjalankan CLI lewat `node` dengan `LD_PRELOAD=libtermux-exec.so`.

Kalau ingin memakai `npx remotion ...`, set dulu:

```bash
export LD_PRELOAD=$PREFIX/lib/libtermux-exec.so
npx remotion --help
```

### 2. Render butuh Chrome/Chromium headless
Remotion merender video dengan membuka halaman di Chrome headless. Di Termux
native (Android/bionic) Chrome headless tidak tersedia, jadi perintah `render`
kemungkinan akan gagal saat mencari browser.

Opsi kalau butuh render sungguhan:
- Jalankan proyek ini di Linux (PC/server) atau GitHub Actions.
- Gunakan proot-distro (mis. Ubuntu) lalu install Chromium di dalamnya.
- Untuk preview/animasi di HP, gunakan `./remotion.sh studio` lalu buka
  `http://localhost:3000` di browser Android.

FFmpeg sendiri sudah berfungsi normal dan bisa dipakai untuk konversi video
sehari-hari.
