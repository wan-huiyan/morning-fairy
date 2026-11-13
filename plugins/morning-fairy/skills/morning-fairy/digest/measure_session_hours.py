#!/usr/bin/env python3
"""How many hours did each project get, measured from Claude session logs.

This is a PROXY for a timesheet, not a measurement of the working day. Read the
"What this number is and is not" section of the morning-fairy SKILL.md section "Timesheet hours (optional)"
before putting a figure from here in front of anyone.

The method, in one paragraph: every session transcript under ~/.claude/projects
carries a timestamp on each message. Consecutive messages less than --gap minutes
apart are treated as one continuous stretch of work; a longer gap ends the stretch
and the idle time is not counted. Each session is attributed to a client by its
working directory (clients.json). Stretches are then UNIONED per client per day,
so two sessions running side by side on the same client count once, not twice.
Sessions started by a scheduled task are excluded: nobody was at the keyboard.

Usage:
  python3 -I measure_session_hours.py --start 2026-11-09 --end 2026-11-13
  python3 -I measure_session_hours.py --start 2026-11-12 --client acme --json
  python3 -I measure_session_hours.py --start 2026-11-09 --meetings meetings.json

--meetings takes [{"client": "acme", "start": "2026-11-12T16:00", "end": "...Z or local"}]
and unions those intervals in too, so a meeting attended with no session open still
counts. The brief already fetches the calendar; pass what it found.
"""

import argparse
import datetime as dt
import glob
import json
import os
import sys

DEFAULT_PROJECTS = os.path.expanduser("~/.claude/projects")
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MAP = os.path.join(HERE, "clients.json")
EXAMPLE_MAP = os.path.join(HERE, "clients.example.json")


def load_clients(path):
    """Read the project map. Absent is a clear error, never a silent empty map.

    Shipping a filled-in clients.json would put someone else's project names in
    your timesheet, so the repo carries clients.example.json and you copy it.
    """
    try:
        with open(path) as fh:
            return json.load(fh)["clients"]
    except FileNotFoundError:
        raise SystemExit(
            "No project map at %s.\n"
            "This step is opt-in: copy the example and edit it for your own work --\n"
            "    cp %s %s\n"
            "Until then the hours step does not run." % (path, EXAMPLE_MAP, DEFAULT_MAP)
        )


def classify(cwd, clients, first_text=""):
    """Which client a session's hours belong to.

    The morning brief's own header is checked FIRST, because the folder lies: a
    brief headed "Monks admin (internal)" is routinely opened in whichever repo
    happens to be to hand, and the directory would then bill internal work to
    that client. Where no header says otherwise, fall back to the directory.
    First matching pattern wins in both passes; no match is 'unattributed'.
    """
    head = (first_text or "")[:400].lower()
    if "morning brief tasks for" in head:
        for c in clients:
            for label in c.get("labels", []):
                if label.lower() in head:
                    return c["name"]
    if not cwd:
        return "unattributed"
    low = cwd.lower()
    for c in clients:
        for pat in c["patterns"]:
            if pat.lower() in low:
                return c["name"]
    return "unattributed"


def first_user_text(obj):
    msg = obj.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return ""


def read_session(path):
    """-> (cwd, first user message text, sorted [(timestamp, typed_by_her)])."""
    cwd = None
    first = None
    stamps = []
    with open(path, errors="ignore") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except (ValueError, TypeError):
                continue
            if cwd is None:
                cwd = obj.get("cwd")
            if first is None and obj.get("type") == "user":
                text = first_user_text(obj)
                if text:
                    first = text
            ts = obj.get("timestamp")
            if ts:
                try:
                    when = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
                except ValueError:
                    continue
                stamps.append((when, is_typed_by_her(obj)))
    stamps.sort(key=lambda r: r[0])
    return cwd, (first or ""), stamps


NOTICE_PREFIXES = (
    "<system-reminder", "<task-notification", "<cross-session-message",
    "<side-sessions-event", "<local-command", "<command-name", "<command-message",
    "<scheduled-task", "<ci-monitor-event", "<pasted_content",
)


def is_typed_by_her(obj):
    """True when this user message carries text SHE wrote.

    A user-role message is often not a person: tool results, harness notices and
    automated events all arrive this way. Used by --require-typed to drop stretches
    where an agent ran on alone with nobody at the keyboard.
    """
    if obj.get("type") != "user":
        return False
    msg = obj.get("message") or {}
    content = msg.get("content")
    parts = ([content] if isinstance(content, str)
             else [p.get("text", "") for p in content
                   if isinstance(p, dict) and p.get("type") == "text"]
             if isinstance(content, list) else [])
    return any(t.strip() and not t.strip().startswith(NOTICE_PREFIXES) for t in parts)


def is_scheduled(first_text):
    """A run nobody was at the keyboard for.

    Match the tag ANYWHERE in the first user message, not just at the start:
    a system-reminder is routinely prepended, which defeats a startswith test.
    """
    return "<scheduled-task" in first_text


def split_at_midnight(start, end):
    """Yield (date, seconds) so a stretch crossing midnight lands on both days."""
    while start < end:
        midnight = dt.datetime.combine(
            start.date() + dt.timedelta(days=1), dt.time.min, tzinfo=start.tzinfo
        )
        stop = min(end, midnight)
        yield start.date(), (stop - start).total_seconds()
        start = stop


def union(intervals):
    """Merge overlapping or touching (start, end) pairs."""
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            if end > merged[-1][1]:
                merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    return merged


def collect(projects_dir, clients, gap_minutes, require_typed=False):
    """-> {client: [(start, end), ...]} of raw, unmerged active stretches."""
    by_client = {}
    gap = dt.timedelta(minutes=gap_minutes)
    for path in glob.glob(os.path.join(projects_dir, "*", "*.jsonl")):
        cwd, first, stamps = read_session(path)
        if len(stamps) < 2 or is_scheduled(first):
            continue
        name = classify(cwd, clients, first)
        bucket = by_client.setdefault(name, [])
        # Break the session into stretches first, so --require-typed can judge a
        # whole stretch rather than a single pair of messages inside it.
        stretch = [stamps[0]]
        for row in stamps[1:]:
            if row[0] - stretch[-1][0] <= gap:
                stretch.append(row)
            else:
                _emit(bucket, stretch, require_typed)
                stretch = [row]
        _emit(bucket, stretch, require_typed)
    return by_client


def _emit(bucket, stretch, require_typed):
    if len(stretch) < 2:
        return
    if require_typed and not any(typed for _, typed in stretch):
        return
    bucket.append((stretch[0][0], stretch[-1][0]))


def add_meetings(by_client, meetings_path):
    with open(meetings_path) as fh:
        for m in json.load(fh):
            start = dt.datetime.fromisoformat(m["start"]).astimezone()
            end = dt.datetime.fromisoformat(m["end"]).astimezone()
            by_client.setdefault(m.get("client", "unattributed"), []).append((start, end))


def daily_hours(intervals, lo, hi):
    """Union, then split across dates, clipped to [lo, hi] inclusive of both days."""
    out = {}
    for start, end in union(intervals):
        for date, seconds in split_at_midnight(start, end):
            if lo <= date <= hi:
                out[date] = out.get(date, 0.0) + seconds / 3600.0
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", required=True, help="first day, YYYY-MM-DD (local)")
    ap.add_argument("--end", help="last day, YYYY-MM-DD (local); defaults to --start")
    ap.add_argument("--gap", type=float, default=15.0,
                    help="minutes of silence that end a stretch (default 15)")
    ap.add_argument("--client", help="report only this client")
    ap.add_argument("--projects-dir", default=DEFAULT_PROJECTS)
    ap.add_argument("--clients", default=DEFAULT_MAP, help="path to clients.json")
    ap.add_argument("--meetings", help="JSON list of calendar meetings to union in")
    ap.add_argument("--require-typed", action="store_true",
                    help="count a stretch only if it holds a message she typed, "
                         "dropping agent runs nobody was present for. Off by "
                         "default; use it to check how much a day depends on them.")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    lo = dt.date.fromisoformat(args.start)
    hi = dt.date.fromisoformat(args.end) if args.end else lo
    if hi < lo:
        ap.error("--end is before --start")

    clients = load_clients(args.clients)
    by_client = collect(args.projects_dir, clients, args.gap, args.require_typed)
    if args.meetings:
        add_meetings(by_client, args.meetings)

    result = {}
    for name, intervals in by_client.items():
        if args.client and name != args.client:
            continue
        per_day = daily_hours(intervals, lo, hi)
        if per_day:
            result[name] = per_day

    # Wall clock: the union across ALL clients. Per-client figures summed can
    # exceed it, because two clients worked at once count once here and twice there.
    everything = [iv for name, ivs in by_client.items()
                  if not args.client or name == args.client
                  for iv in ivs]
    wall = daily_hours(everything, lo, hi)

    days = sorted({d for per_day in result.values() for d in per_day} | set(wall))

    if args.as_json:
        payload = {
            "window": {"start": str(lo), "end": str(hi), "gap_minutes": args.gap},
            "by_client": {n: {str(d): round(h, 2) for d, h in sorted(pd.items())}
                          for n, pd in sorted(result.items())},
            "wall_clock": {str(d): round(h, 2) for d, h in sorted(wall.items())},
            "caveat": "Proxy for a timesheet, not a measurement of the working day. "
                      "See 'Timesheet hours' in the morning-fairy skill.",
        }
        json.dump(payload, sys.stdout, indent=2)
        print()
        return 0

    names = sorted(result)
    width = max([len("day")] + [len(n) for n in names]) if names else 3
    header = "  ".join(["day       "] + [n.rjust(max(6, len(n))) for n in names] + ["  wall"])
    print(header)
    print("-" * len(header))
    for d in days:
        row = [d.strftime("%a %d %b")]
        for n in names:
            row.append(("%.1f" % result[n].get(d, 0.0)).rjust(max(6, len(n))))
        row.append(("%.1f" % wall.get(d, 0.0)).rjust(6))
        print("  ".join(row))
    print("-" * len(header))
    totals = ["total     "]
    for n in names:
        totals.append(("%.1f" % sum(result[n].values())).rjust(max(6, len(n))))
    totals.append(("%.1f" % sum(wall.values())).rjust(6))
    print("  ".join(totals))
    print()
    print("Hours any session for that client was active, overlaps merged, scheduled")
    print("runs excluded, gaps over %g min dropped. A proxy, not your working day:" % args.gap)
    print("off-keyboard work is missing, and a meeting with a session left open is in.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
