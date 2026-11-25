# %% [markdown]
# # 🎬 Remotion 3D GPU Benchmark — Kaggle
#
# Tes apakah Chrome headless di Kaggle benar-benar memakai GPU (T4) untuk render
# three.js + postprocessing, sebelum kita commit ke video 67 detik 2K.
#
# **Persiapan:** Settings → Accelerator: **GPU T4 x2**, Internet: **On**.
#
# - Repo: https://github.com/IzumiXyo/remotion-app
# - Komposisi: `Bench` — 140 kubus + torus knot + Bloom + Vignette,
#   1080×1920, 30 fps, 90 frame.

# %% [markdown]
# ## 1. Cek lingkungan

# %%
import os
import json
import re
import subprocess
import time

WORK = "/kaggle/working"
APP = f"{WORK}/remotion-app"
TMP = f"{WORK}/remotion-tmp"
os.makedirs(TMP, exist_ok=True)
os.environ.update(TEMP=TMP, TMP=TMP, REMOTION_TMP=TMP)

ENV = os.environ.copy()


def run(cmd, **kwargs):
    print("$", " ".join(cmd) if isinstance(cmd, list) else cmd)
    p = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    print(p.stdout or "")
    if p.returncode != 0:
        print(p.stderr or "")
    return p


run(["nvidia-smi"])
run(["bash", "-lc", "ffmpeg -version | head -1; df -h /kaggle/working | tail -1"])

# %% [markdown]
# ## 2. Install Node.js 22

# %%
%%bash
set -e
if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nodejs
fi
node -v
npm -v

# %% [markdown]
# ## 3. Library sistem untuk Chrome

# %%
%%bash
set -e
. /etc/os-release
if [ "${VERSION_ID:-}" = "24.04" ]; then ASOUND=libasound2t64; else ASOUND=libasound2; fi
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
  libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libatspi2.0-0 libcups2 \
  libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
  libgbm1 $ASOUND libpango-1.0-0 libcairo2 libx11-6 libx11-xcb1 libxcb1 \
  libxext6 libxi6 libxtst6 libglib2.0-0 libdbus-1-3 libexpat1 \
  libegl1 libgles2 libgl1 libvulkan1 \
  fonts-liberation fonts-dejavu-core
echo "chrome deps ok"

# %% [markdown]
# ## 4. Clone repo + install dependency

# %%
%%bash
set -e
rm -rf /kaggle/working/remotion-app /kaggle/working/.npm
git clone --depth 1 https://github.com/IzumiXyo/remotion-app.git /kaggle/working/remotion-app
cd /kaggle/working/remotion-app
npm ci --no-audit --no-fund --cache /kaggle/working/.npm
echo "--- versi ---"
node -e "console.log('node', process.version)"
./node_modules/.bin/remotion versions 2>/dev/null | tail -3 || true

# %% [markdown]
# ## 5. Bundle sekali (dipakai ulang oleh semua render)

# %%
%%bash
set -e
cd /kaggle/working/remotion-app
export TEMP=/kaggle/working/remotion-tmp
export TMP=/kaggle/working/remotion-tmp
export REMOTION_TMP=/kaggle/working/remotion-tmp
time npx remotion bundle src/index.ts --out-dir build --log=info

# %% [markdown]
# ## 6. Benchmark backend GPU (1 still per backend)
#
# `chrome-for-testing` dipakai karena Remotion menyarankannya untuk mengakses
# driver GPU di Linux. Kita coba empat backend dan pilih yang tercepat.

# %%
backends = ["angle-egl", "egl", "angle", "swangle"]
results = {}

for gl in backends:
    out = f"{WORK}/still_{gl}.png"
    if os.path.exists(out):
        os.remove(out)
    cmd = [
        "npx", "remotion", "still", "build", "Bench", out,
        "--frame=45",
        "--chrome-mode=chrome-for-testing",
        f"--gl={gl}",
        "--log=error",
        "--timeout=180000",
    ]
    t0 = time.time()
    try:
        p = subprocess.run(
            cmd, cwd=APP, env=ENV, capture_output=True, text=True, timeout=900
        )
        secs = round(time.time() - t0, 1)
        ok = p.returncode == 0 and os.path.exists(out)
        results[gl] = {"ok": ok, "seconds": secs}
        if not ok:
            results[gl]["error"] = (p.stderr or p.stdout)[-700:]
    except subprocess.TimeoutExpired:
        results[gl] = {"ok": False, "seconds": None, "error": "timeout"}
    print(gl, results[gl])

print(json.dumps(results, indent=2))

# %% [markdown]
# ## 7. Render video benchmark 540×960 + pantau GPU

# %%
ok = [gl for gl in results if results[gl]["ok"]]
assert ok, "Tidak ada backend GL yang berhasil — lihat error di sel sebelumnya."
best = min(ok, key=lambda gl: results[gl]["seconds"])
print("Backend terpilih:", best, results[best])

gpu_path = f"{WORK}/gpu_usage.csv"
gpu_file = open(gpu_path, "w")
monitor = subprocess.Popen(
    [
        "nvidia-smi",
        "--query-gpu=timestamp,utilization.gpu,memory.used",
        "--format=csv,noheader",
        "-l", "1",
    ],
    stdout=gpu_file,
    stderr=subprocess.DEVNULL,
)

video_half = f"{WORK}/bench_0.5x.mp4"
cmd = [
    "npx", "remotion", "render", "build", "Bench", video_half,
    "--codec=h264",
    "--crf=18",
    "--scale=0.5",
    "--concurrency=4",
    "--chrome-mode=chrome-for-testing",
    f"--gl={best}",
    "--log=info",
]
t0 = time.time()
p = subprocess.run(cmd, cwd=APP, env=ENV, capture_output=True, text=True, timeout=3600)
elapsed = time.time() - t0
monitor.terminate()
gpu_file.close()

print(p.stdout[-2000:])
if p.returncode != 0:
    print(p.stderr[-2000:])
print("returncode:", p.returncode, "| elapsed:", round(elapsed, 1), "s")

lines = open(gpu_path).read().strip().splitlines()
utils = [int(m.group(1)) for line in lines if (m := re.search(r", (\d+) %", line))]
max_util = max(utils) if utils else None
print("GPU samples:", len(utils), "| max util:", max_util, "%")
if p.returncode == 0:
    print("fps (540x960):", round(90 / elapsed, 2))

# %% [markdown]
# ## 8. Still resolusi penuh 1080×1920

# %%
still_full = f"{WORK}/still_full.png"
cmd = [
    "npx", "remotion", "still", "build", "Bench", still_full,
    "--frame=45",
    "--chrome-mode=chrome-for-testing",
    f"--gl={best}",
    "--log=error",
]
p = subprocess.run(cmd, cwd=APP, env=ENV, capture_output=True, text=True, timeout=900)
print("returncode:", p.returncode)
if p.returncode != 0:
    print(p.stderr[-1500:])

from PIL import Image
im = Image.open(still_full)
print("ukuran:", im.size)
display(im)

# %% [markdown]
# ## 9. Sampel 2K (15 frame) untuk estimasi render penuh
#
# Output 1440×2560. Estimasi durasi video 67 detik = 2010 frame.

# %%
video_2k = f"{WORK}/bench_2k_sample.mp4"
cmd = [
    "npx", "remotion", "render", "build", "Bench", video_2k,
    "--frames=0-14",
    "--codec=h264",
    "--crf=18",
    "--scale=1.3333",
    "--concurrency=4",
    "--chrome-mode=chrome-for-testing",
    f"--gl={best}",
    "--log=info",
]
t0 = time.time()
p = subprocess.run(cmd, cwd=APP, env=ENV, capture_output=True, text=True, timeout=3600)
elapsed_2k = time.time() - t0
print(p.stdout[-1500:])
print("returncode:", p.returncode, "| 15 frame 2K:", round(elapsed_2k, 1), "s")
if p.returncode == 0:
    print("Estimasi 2010 frame:", round(elapsed_2k / 15 * 2010 / 60, 1), "menit")

# %% [markdown]
# ## 10. Ringkas + zip output

# %%
%%bash
cd /kaggle/working
zip -q -r remotion_benchmark.zip \
  bench_0.5x.mp4 bench_2k_sample.mp4 \
  still_angle-egl.png still_egl.png still_angle.png still_swangle.png \
  still_full.png gpu_usage.csv 2>/dev/null || true
ls -lh remotion_benchmark.zip bench_0.5x.mp4 bench_2k_sample.mp4 still_full.png
