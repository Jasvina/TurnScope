#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
SERVER_PID=""
SERVER_PORT=""

cleanup() {
  local exit_code=$?
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP_DIR"
  return "$exit_code"
}

trap cleanup EXIT

cd "$ROOT_DIR"

start_http_server() {
  local web_dir="$1"
  local port_file="$TMP_DIR/http.port"
  local log_file="$TMP_DIR/http.log"

  python3 - "$web_dir" "$port_file" <<'PY' >/dev/null 2>"$log_file" &
import functools
import http.server
import pathlib
import sys

directory = sys.argv[1]
port_file = pathlib.Path(sys.argv[2])
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)
server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
port_file.write_text(str(server.server_address[1]), encoding="utf-8")
try:
    server.serve_forever()
finally:
    server.server_close()
PY
  SERVER_PID="$!"

  for _ in {1..50}; do
    if [[ -s "$port_file" ]]; then
      SERVER_PORT="$(<"$port_file")"
      return 0
    fi
    if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
      cat "$log_file" >&2 || true
      return 1
    fi
    sleep 0.1
  done

  echo "Timed out waiting for local HTTP server to start." >&2
  cat "$log_file" >&2 || true
  return 1
}

echo "[1/7] Run adapter precision checks"
python3 packages/adapters-codex/src/eval_samples.py
python3 packages/adapters-openclaw/src/eval_samples.py

echo "[2/7] Compile Python sources"
python3 -m py_compile \
  apps/collector/src/collector.py \
  apps/collector/tests/test_collector.py \
  packages/adapters-codex/src/map_app_server.py \
  packages/adapters-codex/src/eval_samples.py \
  packages/adapters-openclaw/src/map_session_store.py \
  packages/adapters-openclaw/src/eval_samples.py

echo "[3/7] Run collector unit tests"
python3 -m unittest apps.collector.tests.test_collector

echo "[4/7] Build a collector bundle from the Codex sample"
python3 packages/adapters-codex/src/map_app_server.py \
  --input packages/adapters-codex/fixtures/sample-app-server.jsonl \
  --output "$TMP_DIR/codex.ndjson"
python3 apps/collector/src/collector.py \
  --input "$TMP_DIR/codex.ndjson" \
  --outdir "$TMP_DIR/codex-collector"
test -f "$TMP_DIR/codex-collector/index.json"
test -f "$TMP_DIR/codex-collector/bundles/session-pack.json"

echo "[5/7] Build a collector bundle from the OpenClaw sample"
python3 packages/adapters-openclaw/src/map_session_store.py \
  --input packages/adapters-openclaw/fixtures/sample-sessions-store.json \
  --output "$TMP_DIR/openclaw.ndjson"
python3 apps/collector/src/collector.py \
  --input "$TMP_DIR/openclaw.ndjson" \
  --outdir "$TMP_DIR/openclaw-collector"
test -f "$TMP_DIR/openclaw-collector/index.json"

echo "[6/7] Check static web syntax"
node --check apps/web/app.js

echo "[7/7] Run a local HTTP smoke test"
start_http_server "apps/web"
curl -fsS "http://127.0.0.1:$SERVER_PORT/" | grep -q "TurnScope"

echo "Verification complete."
