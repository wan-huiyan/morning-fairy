#!/bin/bash
# Make "Morning Brief.app", a one-click way to open today's brief from the Dock (macOS only).
#
#   bash make_dock_app.sh [folder]      default folder: ~/Applications
#
# The app holds no copy of the skill. Each time you click it, it looks for the installed skill (a manual copy in
# ~/.claude/skills/morning-fairy, else the newest plugin install) and runs its launch.sh, so a plugin update never
# leaves the app pointing at an old folder. If it cannot find the skill, it opens the newest brief file directly.
# Run it again any time to rebuild the app; it only ever writes inside "<folder>/Morning Brief.app".
set -euo pipefail

if [ "$(uname -s)" != "Darwin" ]; then
  echo "make_dock_app.sh builds a macOS app. On other systems, run launch.sh (next to this script) instead." >&2
  exit 1
fi

here="$(cd "$(dirname "$0")" && pwd)"
dest="${1:-$HOME/Applications}"
app="$dest/Morning Brief.app"
briefs="${BRIEF_DESKTOP_DIR:-$HOME/Desktop}"   # baked in: an app opened from the Dock does not see your shell's variables

# an app of the same name that this script did not make is moved aside, never overwritten
if [ -d "$app" ]; then
  old_id=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$app/Contents/Info.plist" 2>/dev/null || true)
  if [ "$old_id" != "io.github.wan-huiyan.morning-fairy" ]; then
    aside="$dest/Morning Brief (old).app"; n=2
    while [ -e "$aside" ]; do aside="$dest/Morning Brief (old $n).app"; n=$((n + 1)); done
    mv "$app" "$aside"
    echo "You already had a different Morning Brief.app; it is now: $aside"
  fi
fi

mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"

cat > "$app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Morning Brief</string>
  <key>CFBundleDisplayName</key><string>Morning Brief</string>
  <key>CFBundleIdentifier</key><string>io.github.wan-huiyan.morning-fairy</string>
  <key>CFBundleExecutable</key><string>launch</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>LSUIElement</key><true/>
</dict></plist>
PLIST

# the icon: the ticket mascot in front of a sunrise, turned into the .icns the Dock wants (sips and iconutil come with macOS)
set_dir="$(mktemp -d)/icon.iconset"
mkdir -p "$set_dir"
for s in 16 32 128 256 512; do
  sips -z "$s" "$s" "$here/app-icon.png" --out "$set_dir/icon_${s}x${s}.png" >/dev/null
  d=$((s * 2))
  if [ "$d" -le 512 ]; then sips -z "$d" "$d" "$here/app-icon.png" --out "$set_dir/icon_${s}x${s}@2x.png" >/dev/null; fi
done
iconutil -c icns "$set_dir" -o "$app/Contents/Resources/icon.icns"
rm -rf "$(dirname "$set_dir")"

# the launcher the Dock runs; the briefs folder is written in now, the skill is looked up at click time
{
  echo '#!/bin/bash'
  printf 'export BRIEF_DESKTOP_DIR=%q\n' "$briefs"
  cat <<'LAUNCH'
skill=""
for c in "$HOME/.claude/skills/morning-fairy" \
         "$(ls -dt "$HOME"/.claude/plugins/cache/*/morning-fairy/*/skills/morning-fairy 2>/dev/null | head -1)"; do
  if [ -n "$c" ] && [ -f "$c/digest/launch.sh" ]; then skill="$c"; break; fi
done
if [ -n "$skill" ]; then
  out=$(/bin/bash "$skill/digest/launch.sh") || true
  case "$out" in "No brief in"*) open "$BRIEF_DESKTOP_DIR" ;; esac   # nothing built yet: show the folder it will land in
  exit 0
fi
# no skill found: open the newest brief as a plain file (newest by the date in its name)
f=$(ls "$BRIEF_DESKTOP_DIR"/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]" Morning brief and Jira digest.html" 2>/dev/null | sort | tail -1)
if [ -n "$f" ]; then open "$f"; else open "$BRIEF_DESKTOP_DIR"; fi
LAUNCH
} > "$app/Contents/MacOS/launch"
chmod +x "$app/Contents/MacOS/launch"
touch "$app"   # so Finder and the Dock pick up the new icon

echo "Made: $app"
echo "Next: drag it from the Finder window that just opened onto your Dock."
[ -z "${MORNING_FAIRY_NO_REVEAL:-}" ] && open -R "$app" || true
