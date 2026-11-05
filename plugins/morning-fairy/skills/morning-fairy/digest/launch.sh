#!/bin/bash
# Open the newest morning brief. Starts the local helper (serve.py, 127.0.0.1:8765) so Done taps are saved to
# ~/.morning-fairy/runs/done.jsonl; if the helper cannot start, the file opens directly and taps stay in that browser.
# BRIEF_DESKTOP_DIR overrides where the briefs are (default ~/Desktop), as it does for serve.py.
here="$(cd "$(dirname "$0")" && pwd)"
dir="${BRIEF_DESKTOP_DIR:-$HOME/Desktop}"
opener=open; command -v open >/dev/null 2>&1 || opener=xdg-open
# newest by the date the name starts with, not by file time, so re-saving an old brief never opens it instead of today
f=$(ls "$dir"/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]" Morning brief and Jira digest.html" 2>/dev/null | sort | tail -1)
if [ -z "$f" ]; then echo "No brief in $dir yet."; exit 0; fi
H=http://127.0.0.1:8765
up() { curl -fs -m 1 "$H/health" >/dev/null 2>&1; }
if ! up; then
  BRIEF_DESKTOP_DIR="$dir" nohup python3 -I "$here/serve.py" >/dev/null 2>&1 &
  for i in 1 2 3 4 5 6 7 8 9 10; do sleep 0.2; up && break; done
fi
if up; then "$opener" "$H/"; else "$opener" "$f"; fi
