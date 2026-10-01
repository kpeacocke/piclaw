#!/bin/bash -eu

fuzzer="$SRC/piclaw/fuzz/hailo_proxy_fuzzer.py"
fuzzer_basename="$(basename -s .py "$fuzzer")"
fuzzer_package="${fuzzer_basename}.pkg"

pyinstaller --distpath "$OUT" --onefile --name "$fuzzer_package" \
  --add-data "$SRC/piclaw/hailo-sanitize-proxy.py:." \
  --hidden-import http.server \
  --hidden-import itertools \
  --hidden-import json \
  --hidden-import os \
  --hidden-import re \
  --hidden-import tempfile \
  --hidden-import time \
  --hidden-import urllib.error \
  --hidden-import urllib.parse \
  --hidden-import urllib.request "$fuzzer"

cat > "$OUT/$fuzzer_basename" <<EOF
#!/bin/sh
this_dir=\$(dirname "\$0")
ASAN_OPTIONS=\${ASAN_OPTIONS:-}:symbolize=1:external_symbolizer_path=\$this_dir/llvm-symbolizer:detect_leaks=0 \\
  "\$this_dir/$fuzzer_package" "\$@"
EOF
chmod +x "$OUT/$fuzzer_basename"

(
  cd "$SRC/piclaw/fuzz/corpus/$fuzzer_basename"
  python3 -m zipfile -c "$OUT/${fuzzer_basename}_seed_corpus.zip" ./*.json
)
