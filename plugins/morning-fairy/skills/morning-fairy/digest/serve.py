#!/usr/bin/env python3
"""A tiny local helper for the morning brief: serves the newest brief from the Desktop and saves Done taps to
~/.morning-fairy/runs/done.jsonl (MORNING_FAIRY_HOME overrides the folder).

127.0.0.1 only, port 8765. Writes that done.jsonl, and look.json in the same folder (beside runs/) when the brief saves
a new look, after which it rebuilds today's brief with the builder beside this file. Also serves the bundled fanfan
icons (fanfan/ beside this file) for the look picker's previews. Python standard library only.
Start it with: python3 -I serve.py   (the launcher script does this when it is not already running)
Tests may point it elsewhere with BRIEF_DIGEST_DIR and BRIEF_DESKTOP_DIR.
"""
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

HOST, PORT = "127.0.0.1", 8765
# Data lives outside the skill folder, so a plugin update (a new versioned folder) does not leave the history behind.
DIGEST = Path(os.environ.get("BRIEF_DIGEST_DIR") or os.environ.get("MORNING_FAIRY_HOME") or Path.home() / ".morning-fairy")
DESKTOP = Path(os.environ.get("BRIEF_DESKTOP_DIR") or Path.home() / "Desktop")
PATTERN = "* Morning brief and Jira digest.html"
ORIGINS = {f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"}
HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
MAX_BODY = 4096
CODE = Path(__file__).resolve().parent  # the builder and the bundled fanfan icons always come from beside this file
# /fanfan/<style>/<animal>-<noun>.svg: only these names, built from the match, never from the request
FF_STYLES = ("thin", "thick", "thin-highlight", "thick-highlight")
FF_ANIMALS = ("cat", "dog", "lop", "bunny")
FF_NOUNS = ("sun", "bell", "ticket", "robot", "trophy", "clock", "news", "mail", "search", "file", "sparkles",
            "palette", "moon", "music", "wand", "sleep", "star", "face-whole", "alarm", "heart")
FF_PATH = re.compile(r"/fanfan/(" + "|".join(FF_STYLES) + r")/(" + "|".join(FF_ANIMALS) + r")-("
                     + "|".join(re.escape(n) for n in FF_NOUNS) + r")\.svg")
# look.json: every key required, nothing else allowed (the builder is more forgiving; this is the one place that writes it)
LOOK_ONE = {"mascot": ("ticket", "clawd", "fanfan"), "animal": FF_ANIMALS, "line": ("thin", "thick"), "eyes": ("dots", "shiny")}
LOOK_MANY = {"places": ("tabs", "quests", "toolbar", "done", "empty", "favicon"), "moves": ("wake", "sleep", "bounce", "blush", "trick")}
LOOK_LOCK = threading.Lock()  # one save-and-rebuild at a time


def briefs():
    """Saved briefs, newest first by the date their name starts with (then file time), so re-saving an old one never
    makes it the page that / opens."""
    try:
        found = [p for p in DESKTOP.iterdir() if p.is_file() and fnmatch.fnmatchcase(p.name, PATTERN)]
    except OSError:
        return []
    def key(p):
        m = re.match(r"(\d{4}-\d{2}-\d{2}) ", p.name)
        try:
            t = p.stat().st_mtime
        except OSError:
            t = 0
        return (m.group(1) if m else "", t)
    return sorted(found, key=key, reverse=True)


def back_pill(name):
    """A small fixed link on a past brief opened from the time machine: which morning this is, and the way back."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2}) ", name)
    try:
        when = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).strftime("%A %-d %b") if m else "an earlier morning"
    except ValueError:
        when = "an earlier morning"
    return ('<a href="/" id="tm-back" style="position:fixed;z-index:2147483000;left:50%;bottom:calc(86px + env(safe-area-inset-bottom,0px));'
            'transform:translateX(-50%);display:inline-flex;align-items:center;gap:10px;padding:10px 16px;border-radius:999px;'
            'background:#15161a;color:#fff;font:600 14px/1.2 system-ui,-apple-system,sans-serif;text-decoration:none;'
            'box-shadow:0 10px 30px rgba(0,0,0,.35);white-space:nowrap">'
            '<span style="opacity:.75;font-weight:500">Time machine: ' + when + '</span>'
            '<span style="padding:5px 11px;border-radius:999px;background:#fff;color:#15161a">Back to today</span></a>')


def _text(v, limit):
    return isinstance(v, str) and len(v) <= limit


def clean_look(r):
    """The look as look.json stores it, or None when anything is missing, unknown or the wrong type."""
    if not isinstance(r, dict) or set(r) != set(LOOK_ONE) | set(LOOK_MANY):
        return None
    for k, allowed in LOOK_ONE.items():
        if not isinstance(r[k], str) or r[k] not in allowed:
            return None
    for k, allowed in LOOK_MANY.items():
        v = r[k]
        if not isinstance(v, list) or len(v) != len(set(v)) or not all(isinstance(x, str) and x in allowed for x in v):
            return None
    return {**{k: r[k] for k in LOOK_ONE}, **{k: [x for x in allowed if x in r[k]] for k, allowed in LOOK_MANY.items()}}


def write_look(look):
    """Write look.json beside runs/ (a temp file of its own swapped in, so a crash never leaves half a file). Returns its
    path. The data folder may not exist yet: a look can be saved before the first morning run."""
    DIGEST.mkdir(parents=True, exist_ok=True)
    path = DIGEST / "look.json"
    fd, tmp = tempfile.mkstemp(prefix=".look.json.", suffix=".tmp", dir=DIGEST)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(look, indent=1) + "\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return path


def rebuild_today(path):
    """Rebuild TODAY's brief from runs/content-<today>.json with the same logs as the morning run and the look at path.
    Returns whether a brief was rebuilt (False: no content for today yet, so the look arrives with tomorrow's brief)."""
    today = datetime.now().strftime("%Y-%m-%d")
    runs = DIGEST / "runs"
    content = runs / f"content-{today}.json"
    if not content.is_file():
        return False
    out = DESKTOP / f"{today} Morning brief and Jira digest.html"
    cmd = [sys.executable, "-I", str(CODE / "build_digest.py"), str(content), str(out),
           "--log", str(runs / "streak.jsonl"), "--admin-log", str(runs / "admin.jsonl"), "--look", str(path)]
    done = subprocess.run(cmd, capture_output=True, timeout=120)
    if done.returncode != 0:
        raise RuntimeError("the builder failed: " + done.stderr.decode("utf-8", "replace")[-400:])
    return True


class Handler(BaseHTTPRequestHandler):
    server_version = "BriefHelper"
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # nothing is logged to disk or anywhere else
        pass

    def _send(self, code, body=b"", ctype="text/plain; charset=utf-8", extra=()):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _host_ok(self):
        return self.headers.get("Host", "") in HOSTS

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, "forbidden")
        path = urlsplit(self.path).path
        if path == "/health":
            return self._send(200, "ok")
        if path.startswith("/fanfan/"):
            m = FF_PATH.fullmatch(self.path)  # the raw path: no query, no escapes, nothing but a listed name
            if not m:
                return self._send(404, "not found")
            f = CODE / "fanfan" / m.group(1) / f"{m.group(2)}-{m.group(3)}.svg"
            if not f.is_file():
                return self._send(404, "not found")
            return self._send(200, f.read_bytes(), "image/svg+xml",
                              extra=[("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'")])
        if path == "/":
            found = briefs()
            if not found:
                return self._send(404, "no brief on the Desktop yet")
            return self._send(302, "", extra=[("Location", "/brief/" + quote(found[0].name))])
        if path.startswith("/brief/"):
            name = unquote(path[len("/brief/"):])
            if not name or "/" in name or "\\" in name or ".." in name or "\0" in name:
                return self._send(400, "bad name")
            if not fnmatch.fnmatchcase(name, PATTERN):
                return self._send(404, "not found")
            f = DESKTOP / name
            if not f.is_file():
                return self._send(404, "not found")
            body = f.read_bytes()
            newest = briefs()
            if newest and newest[0].name != name:  # an earlier morning: add the way back to today
                pill = back_pill(name).encode("utf-8")
                i = body.rfind(b"</body>")
                body = body[:i] + pill + body[i:] if i >= 0 else body + pill
            # never inside another site's frame: a page there could steer a click onto Done or "Save my fairy"
            return self._send(200, body, "text/html; charset=utf-8",
                              extra=[("X-Frame-Options", "DENY"), ("Content-Security-Policy", "frame-ancestors 'none'")])
        return self._send(404, "not found")

    do_HEAD = do_GET

    def do_POST(self):
        self.close_connection = True  # a refused body is never read, so the connection is not reused
        route = urlsplit(self.path).path
        if route not in ("/done", "/look"):
            return self._send(404, "not found")
        if self.headers.get("Origin", "") not in ORIGINS or not self._host_ok():
            return self._send(403, "forbidden")
        try:
            n = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self._send(411, "length required")
        if n < 0 or n > MAX_BODY:
            return self._send(413, "too large")
        try:
            r = json.loads(self.rfile.read(n).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._send(400, "bad json")
        if route == "/look":
            look = clean_look(r)
            if look is None:
                return self._send(400, "bad fields")
            # "saved" says whether look.json was written, so the page can tell a failed rebuild after a good save
            # (the look still arrives with tomorrow's brief) from a save that never happened
            with LOOK_LOCK:
                try:
                    path = write_look(look)
                except OSError:
                    return self._send(500, '{"ok":false,"saved":false,"rebuilt":false}', "application/json")
                try:
                    rebuilt = rebuild_today(path)
                except (OSError, RuntimeError, subprocess.SubprocessError):
                    return self._send(500, '{"ok":false,"saved":true,"rebuilt":false}', "application/json")
            return self._send(200, json.dumps({"ok": True, "saved": True, "rebuilt": rebuilt}), "application/json")
        ok = (isinstance(r, dict) and all(k in r for k in ("date", "id", "title", "project", "done"))
              and isinstance(r["date"], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"])
              and _text(r["id"], 200) and r["id"] and _text(r["title"], 500) and _text(r["project"], 200)
              and isinstance(r["done"], bool))
        if not ok:
            return self._send(400, "bad fields")
        rec = {"at": datetime.now().astimezone().isoformat(timespec="seconds"), "date": r["date"], "id": r["id"],
               "title": r["title"], "project": r["project"], "done": r["done"]}
        runs = DIGEST / "runs"
        runs.mkdir(parents=True, exist_ok=True)
        with open(runs / "done.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return self._send(200, '{"ok":true}', "application/json")

    def do_PUT(self):
        self._send(405, "method not allowed")

    do_DELETE = do_PATCH = do_PUT


if __name__ == "__main__":
    try:
        srv = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as e:
        sys.exit(f"cannot bind {HOST}:{PORT}: {e}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
