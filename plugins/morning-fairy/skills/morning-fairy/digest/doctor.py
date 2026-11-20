#!/usr/bin/env python3
"""doctor.py: is this machine ready for morning-fairy? Read-only; it changes nothing.

    python3 -I <skill>/digest/doctor.py          # a checklist, each line with its fix
    python3 -I <skill>/digest/doctor.py --json   # the same, for Claude to read during setup

It checks what a script can see: the command-line tools and their sign-ins, the folders the brief writes to,
your optional settings files, the local helper and the Dock app. It cannot see your connectors (calendar, email,
chat, Jira): only a Claude session can, so the setup in SKILL.md section 0 checks those by making one small read
through each. Exit code 1 when a core check fails, else 0.
"""
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent
OK, WARN, MISSING, OFF = "ok", "warn", "missing", "off"  # off: an optional part you have not turned on


def home_dir():
    return Path(os.environ.get("MORNING_FAIRY_HOME") or Path.home() / ".morning-fairy")


def desktop_dir():
    return Path(os.environ.get("BRIEF_DESKTOP_DIR") or Path.home() / "Desktop")


def run(cmd, timeout=15):
    """(exit code, output) of a command, or (None, reason) when it cannot run. Never raises."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return None, "not installed"
    except subprocess.TimeoutExpired:
        return None, f"no answer in {timeout} s"
    except OSError as e:
        return None, str(e)


def item(group, name, status, detail, fix=""):
    return {"group": group, "name": name, "status": status, "detail": detail, "fix": fix}


def check_python():
    v = sys.version_info
    if v >= (3, 9):
        return item("core", "Python", OK, f"{v.major}.{v.minor}.{v.micro}")
    return item("core", "Python", MISSING, f"{v.major}.{v.minor} is too old; the builder needs 3.9 or newer",
                "Install a current Python 3 (macOS: `xcode-select --install`, or python.org).")


def check_folder(name, path, group="core"):
    """A folder the brief writes to: it must exist (or its parent must) and be writable."""
    p = Path(path)
    probe = p if p.exists() else p.parent
    if not probe.exists():
        return item(group, name, MISSING, f"{p} does not exist", f"mkdir -p '{p}'")
    if not os.access(probe, os.W_OK):
        return item(group, name, MISSING, f"{probe} is not writable", f"Check the permissions on {probe}.")
    if not p.exists():
        return item(group, name, OK, f"{p} (created on the first run)")
    return item(group, name, OK, str(p))


def check_gh():
    if not shutil.which("gh"):
        return item("recommended", "GitHub CLI (gh)", MISSING,
                    "not installed: merged pull requests are not used as Jira evidence, and Scout cannot search GitHub",
                    "macOS: `brew install gh`, then `gh auth login`. Others: https://cli.github.com")
    code, out = run(["gh", "auth", "status"])
    if code == 0:
        return item("recommended", "GitHub CLI (gh)", OK, "installed and signed in")
    return item("recommended", "GitHub CLI (gh)", WARN, "installed but not signed in", "gh auth login")


def check_gcloud():
    have = [t for t in ("gcloud", "bq") if shutil.which(t)]
    if not have:
        return item("optional", "Cloud spend (gcloud, bq)", OFF, "not installed; the Spend tab stays off",
                    "Only if you want the Spend tab: install the Google Cloud CLI, then `gcloud auth login`.")
    if len(have) < 2:
        return item("optional", "Cloud spend (gcloud, bq)", WARN, f"only {have[0]} is installed; the Spend tab needs both",
                    "gcloud components install bq")
    code, out = run(["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"], timeout=20)
    if code == 0 and out:
        return item("optional", "Cloud spend (gcloud, bq)", OK, "installed and signed in")
    return item("optional", "Cloud spend (gcloud, bq)", WARN, "installed but not signed in", "gcloud auth login")


def check_settings(name, purpose, needed_key, home, code_dir):
    """An optional settings file. Its home is the data folder; one beside the code (before 1.17.0) still works but is
    lost on the next plugin update, so it is flagged."""
    at_home, beside = home / name, code_dir / name
    path = at_home if at_home.exists() else beside if beside.exists() else None
    example = code_dir / name.replace(".json", ".example.json")
    if path is None:
        return item("optional", name, OFF, f"not set up, so {purpose} stays off",
                    f"cp '{example}' '{at_home}'  # then edit it")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return item("optional", name, MISSING, f"{path} is not valid JSON ({e})", f"Fix or re-copy it from {example.name}.")
    if needed_key not in data:
        return item("optional", name, WARN, f"{path} has no \"{needed_key}\"", f"Compare it with {example.name}.")
    if path == beside:
        return item("optional", name, WARN, f"{path} sits inside the skill folder, which a plugin update replaces",
                    f"mkdir -p '{home}' && mv '{beside}' '{at_home}'")
    return item("optional", name, OK, str(path))


def check_tempo(home, code_dir):
    """Tempo needs a "fill_tempo" block in clients.json and Chrome (with the Claude in Chrome extension)."""
    for p in (home / "clients.json", code_dir / "clients.json"):
        if p.exists():
            try:
                block = json.loads(p.read_text(encoding="utf-8")).get("fill_tempo")
            except (OSError, ValueError, AttributeError):
                block = None
            break
    else:
        return item("optional", "Tempo buttons", OFF, "off (no clients.json)")
    if not isinstance(block, dict) or not str(block.get("tempo_url", "")).strip():
        return item("optional", "Tempo buttons", OFF, "off: clients.json has no \"fill_tempo\" block with a tempo_url",
                    "Add the fill_tempo block from clients.example.json.")
    chrome = Path("/Applications/Google Chrome.app").exists() or bool(shutil.which("google-chrome"))
    if not chrome:
        return item("optional", "Tempo buttons", WARN, "set up, but Google Chrome was not found",
                    "Install Chrome and the Claude in Chrome extension (https://claude.com/claude-in-chrome), then sign in to Tempo there.")
    return item("optional", "Tempo buttons", OK,
                "set up; make sure the Claude in Chrome extension is installed and signed in to Tempo (a script cannot see it)")


def check_transcripts():
    p = Path.home() / ".claude" / "projects"
    if p.is_dir():
        return item("optional", "Claude Code session logs", OK, f"{p} (read by the Hours tab)")
    return item("optional", "Claude Code session logs", WARN, f"{p} not found; the Hours tab would have nothing to measure",
                "Use Claude Code on this computer for a day, then check again.")


def check_helper(port=8765):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return item("optional", "Local helper", OK, f"answering on 127.0.0.1:{port}")
    except OSError:
        return item("optional", "Local helper", OFF, "not running (Done taps then stay in one browser)",
                    "Click Morning Brief in the Dock, or run: bash '" + str(CODE / "launch.sh") + "'")


def check_dock_app():
    if platform.system() != "Darwin":
        return item("optional", "Dock app", OFF, "macOS only; open the brief's HTML file instead")
    app = Path.home() / "Applications" / "Morning Brief.app"
    if app.exists():
        return item("optional", "Dock app", OK, str(app))
    return item("optional", "Dock app", OFF, "not made yet", "bash '" + str(CODE / "make_dock_app.sh") + "'")


def checks():
    home, code_dir = home_dir(), CODE
    return [
        check_python(),
        check_folder("Data folder", home),
        check_folder("Desktop (where briefs go)", desktop_dir()),
        check_gh(),
        check_transcripts(),
        check_settings("clients.json", "the Hours tab", "clients", home, code_dir),
        check_tempo(home, code_dir),
        check_settings("start.json", "Start in Claude", "root", home, code_dir),
        check_gcloud(),
        check_helper(),
        check_dock_app(),
    ]


MARK = {OK: "ok  ", WARN: "warn", MISSING: "FIX ", OFF: "off "}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    res = checks()
    bad = any(r["status"] == MISSING and r["group"] == "core" for r in res)
    if "--json" in argv:
        print(json.dumps({"ready": not bad, "checks": res}, indent=1))
        return 1 if bad else 0
    for group, title in (("core", "Core"), ("recommended", "Recommended"), ("optional", "Optional")):
        rows = [r for r in res if r["group"] == group]
        print(f"\n{title}")
        for r in rows:
            print(f"  [{MARK[r['status']]}] {r['name']}: {r['detail']}")
            if r["fix"] and r["status"] != OK:
                print(f"         fix: {r['fix']}")
    print("\nConnectors (calendar, email, chat, Jira, Drive) are checked by Claude, not by this script:")
    print('say "set up morning fairy" in Claude Code.')
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
