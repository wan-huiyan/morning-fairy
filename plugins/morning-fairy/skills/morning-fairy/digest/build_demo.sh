#!/bin/bash
# Build the demo: two mornings (Wed 11 and Thu 12 Mar 2026) of a made-up person, so the time machine has a day to visit.
# Usage: ./build_demo.sh [out-dir]   (default: a new temporary folder). It never writes inside this repo.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
out="${1:-$(mktemp -d)}"
runs="$(mktemp -d)"
cp "$here"/demo/*.jsonl "$here"/demo/content-*.json "$runs"/
for d in 2026-03-11 2026-03-12; do
  python3 -I "$here/build_digest.py" "$runs/content-$d.json" "$out/$d Morning brief and Jira digest.html" \
    --log "$runs/streak.jsonl" --admin-log "$runs/admin.jsonl" >/dev/null
done
echo "$out/2026-03-12 Morning brief and Jira digest.html"
