#!/bin/bash -eu

fuzzer="$SRC/piclaw/fuzz/hailo_proxy_fuzzer.py"
fuzzer_basename="$(basename -s .py "$fuzzer")"
compile_python_fuzzer "$fuzzer" \
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
  --hidden-import urllib.request

(
  cd "$SRC/piclaw/fuzz/corpus/$fuzzer_basename"
  python3 -m zipfile -c "$OUT/${fuzzer_basename}_seed_corpus.zip" ./*.json
)
