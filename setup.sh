#!/usr/bin/env bash
# Rebuild both virtualenvs and download the Piper voices.
# Safe to re-run; it will reuse anything already in place.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
PIPER_VOICES=(
    en_US-lessac-medium en_US-amy-medium en_GB-alba-medium
    nl_NL-ronnie-medium nl_NL-pim-medium nl_BE-nathalie-medium
)

# Some Python builds (notably the python.org macOS installer) ship without a CA
# bundle, which makes every model download fail with CERTIFICATE_VERIFY_FAILED.
# Point each venv at certifi's bundle instead.
write_sitecustomize() {
    local site
    site="$("$1/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
    cat > "$site/sitecustomize.py" <<'PY'
# Point this Python at certifi's CA bundle so model downloads work.
import os
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except Exception:
    pass
PY
}

build_venv() {
    local venv="$1" reqs="$2"
    echo "==> $venv"
    [ -d "$venv" ] || "$PYTHON" -m venv "$venv"
    "$venv/bin/python" -m pip install --quiet --upgrade pip
    "$venv/bin/python" -m pip install --quiet -r "$reqs"
    write_sitecustomize "$venv"
}

# Piper + Kokoro share a venv. Coqui needs its own: it pins transformers<5,
# which would break Kokoro.
build_venv .venv requirements.txt
build_venv .venv-coqui requirements-coqui.txt

# espeak-ng (used by both Piper and Kokoro for grapheme-to-phoneme) keeps its
# data directory in a fixed 160-byte buffer. Past that it silently falls back to
# a path from its own build machine and every synthesis fails with a confusing
# "phontab: No such file or directory". Catch it here rather than at run time.
espeak_data="$(.venv/bin/python -c 'import sysconfig,os; print(os.path.join(sysconfig.get_paths()["purelib"], "piper", "espeak-ng-data"))')"
if [ ${#espeak_data} -ge 160 ]; then
    echo
    echo "WARNING: this checkout is too deeply nested for espeak-ng." >&2
    echo "  Its data path is ${#espeak_data} chars; the limit is 160." >&2
    echo "  Piper and Kokoro will fail here. Move the repo somewhere shorter." >&2
    echo
fi

echo "==> Piper voices"
mkdir -p voices out
missing=()
for voice in "${PIPER_VOICES[@]}"; do
    [ -f "voices/$voice.onnx" ] || missing+=("$voice")
done
if [ ${#missing[@]} -gt 0 ]; then
    .venv/bin/python -m piper.download_voices --download-dir voices "${missing[@]}"
else
    echo "all present"
fi

cat <<'DONE'

Done. Try:
    ./tts.py "Hello there"
    ./tts.py -e kokoro "Hello there"        # downloads ~330MB on first run

Coqui XTTS-v2 is installed but its weights are under a non-commercial
licence (https://coqui.ai/cpml). If you accept it:
    export COQUI_TOS_AGREED=1 && ./coqui.py --speakers
DONE
