#!/data/data/com.termux/files/usr/bin/bash
# Wrapper Remotion untuk Termux.
# Menjalankan CLI lewat node + LD_PRELOAD agar shebang #!/usr/bin/env node tetap bekerja.
set -e
cd "$(dirname "$0")"
export LD_PRELOAD="${PREFIX:-/data/data/com.termux/files/usr}/lib/libtermux-exec.so${LD_PRELOAD:+:$LD_PRELOAD}"
exec node ./node_modules/@remotion/cli/remotion-cli.js "$@"
