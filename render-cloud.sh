#!/data/data/com.termux/files/usr/bin/bash
# Render video di GitHub Actions lalu unduh hasilnya.
# Pemakaian: ./render-cloud.sh [Komposisi] [output.mp4]
# Contoh:    ./render-cloud.sh Hello out/hello.mp4
set -euo pipefail
cd "$(dirname "$0")"

COMP="${1:-Hello}"
OUT="${2:-out/video.mp4}"

if ! gh auth status >/dev/null 2>&1; then
  echo "Belum login GitHub. Jalankan: gh auth login" >&2
  exit 1
fi

echo "▶ Trigger render '$COMP' → '$OUT'"
BEFORE=$(gh run list --workflow=render.yml --limit=1 --json databaseId -q '.[0].databaseId // 0')
gh workflow run render.yml -f composition="$COMP" -f output="$OUT"

echo "⏳ Menunggu run baru..."
RUN_ID=""
for _ in $(seq 1 20); do
  sleep 3
  RUN_ID=$(gh run list --workflow=render.yml --limit=1 --json databaseId -q '.[0].databaseId // 0')
  if [ -n "$RUN_ID" ] && [ "$RUN_ID" != "$BEFORE" ]; then
    break
  fi
  RUN_ID=""
done
if [ -z "$RUN_ID" ]; then
  echo "Gagal menemukan run. Cek: gh run list --workflow=render.yml" >&2
  exit 1
fi

echo "▶ Run: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runs/$RUN_ID"
gh run watch "$RUN_ID" --exit-status --interval 10

echo "⬇ Mengunduh artifact..."
rm -rf downloaded
gh run download "$RUN_ID" --name rendered-video -D downloaded

SRC=$(find downloaded -name '*.mp4' | head -1)
if [ -z "$SRC" ]; then
  echo "Artifact tidak berisi MP4." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
cp "$SRC" "$OUT"
echo "✅ Selesai: $OUT"
