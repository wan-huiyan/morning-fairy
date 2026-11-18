#!/usr/bin/env python3
"""BigQuery query spend, this month, for every GCP project you are working in -- data for the brief's Spend chapter.

"Working in" is measured each run, never listed by hand: a project counts when your own gcloud login ran a BigQuery job
there in the last 30 days (`bq ls -j`, which lists only the caller's jobs). Its regions are the locations of the
project's last 300 jobs by anyone. Spend is the whole project's, read from INFORMATION_SCHEMA.JOBS_BY_PROJECT.

Reads are billed to --bill-to (or $MORNING_FAIRY_GCP_BILL_TO) when given -- set it to a project of your own so that
watching a client's project never lands on the client's bill -- and otherwise to each project being read. Every read
refuses to scan more than CAP_BYTES. Dollar figures are ESTIMATES: bytes billed x the on-demand list price. They cover BigQuery queries
only -- not storage, Cloud Run, Dataform runtime or anything else, and not the free tier or credits.

Display ideas (month-to-date headline, same-days-last-month comparison, month-end pace) are borrowed from
agy-gcp-companion by ericsk, https://github.com/ericsk/agy-gcp-companion (Apache-2.0 per its package.json).
No code was copied.

Each account's spend is split into "your patch" (your own login, plus any account named in <home>/spend_accounts.json
or --mine, such as your own pipelines' service accounts) and "the neighbours" (everyone else in the same projects).

Usage: python3 measure_gcp_spend.py --json                     (prints the "spend" object for the content JSON)
       python3 measure_gcp_spend.py --projects a,b             (skip discovery)
       python3 measure_gcp_spend.py --bill-to my-own-project   (who pays for the reads; a few cents a day)
Needs the gcloud and bq command-line tools, signed in.
"""
import argparse, calendar, collections, concurrent.futures as cf, csv, datetime as dt, fnmatch, io, json, os, pathlib, re, statistics, subprocess, sys

PRICE_PER_TIB = 6.25
CAP_BYTES = 5_000_000_000      # per query; a project that needs more is reported as skipped, never silently dropped
BILL_TO = None                 # set by --bill-to / $MORNING_FAIRY_GCP_BILL_TO; None bills each project its own reads
ME = ""                        # the signed-in gcloud account, read at start
ACTIVE_DAYS = 30
PACE_DAYS = 7
MINOR_SHARE = 0.03
MINE = []                      # account patterns that count as "your patch", besides your own login


def is_mine(u):
    return u == ME or any(fnmatch.fnmatch(u, pat) for pat in MINE)


def read_mine(path):
    """<home>/spend_accounts.json: {"mine": ["my-pipeline@example.iam.gserviceaccount.com", "etl-*@example.*"]}"""
    try:
        return list(json.loads(pathlib.Path(path).read_text()).get("mine", []))
    except (OSError, ValueError):
        return []

SQL = """
SELECT DATE(creation_time) d, user_email,
       COUNT(*) jobs, IFNULL(SUM(total_bytes_billed),0) bytes,
       COUNTIF(job_type = 'QUERY' AND IFNULL(reservation_id, 'default-pipeline') != 'default-pipeline' AND total_slot_ms > 0) reserved_jobs
FROM `{p}`.`{region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time >= TIMESTAMP(DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH), MONTH))
GROUP BY 1,2"""


def sh(args, timeout=120):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def jobs(project, all_users, n):
    o = sh(["bq", "ls", "-j", "-n", str(n), "--format=json", f"--project_id={project}"] + (["-a"] if all_users else []))
    if o.returncode:
        return None
    try:
        return json.loads(o.stdout or "[]")
    except json.JSONDecodeError:
        return None


def discover(now):
    """Projects where you ran a BigQuery job in the last ACTIVE_DAYS days."""
    o = sh(["gcloud", "projects", "list", "--format=value(projectId)"])
    cutoff = (now - dt.timedelta(days=ACTIVE_DAYS)).timestamp() * 1000

    def mine(p):
        j = jobs(p, False, 50) or []
        return p if any(int(x["statistics"]["creationTime"]) >= cutoff for x in j) else None
    with cf.ThreadPoolExecutor(12) as ex:
        return sorted(p for p in ex.map(mine, o.stdout.split()) if p)


def regions(project):
    j = jobs(project, True, 300) or []
    locs = collections.Counter(x["jobReference"].get("location") for x in j if x.get("jobReference", {}).get("location"))
    total = sum(locs.values()) or 1
    # a region holding under MINOR_SHARE of recent jobs is left unread (its whole job log can cost more to read than it spent)
    return sorted(l for l, n in locs.items() if n / total >= MINOR_SHARE), sorted(l for l, n in locs.items() if n / total < MINOR_SHARE)


def short(u):
    if u.endswith("@developer.gserviceaccount.com"):
        return "Compute Engine default (service account)"
    if u.endswith(".iam.gserviceaccount.com"):
        return u.split("@")[0] + " (service account)"
    return "you" if u == ME else u


def usd(b):
    return int(b or 0) / 2**40 * PRICE_PER_TIB


def measure(project, now):
    rows, problems = [], []
    read, minor = regions(project)
    for loc in read:
        q = SQL.format(p=project, region="region-" + loc.lower())
        o = sh(["bq", "query", f"--project_id={BILL_TO or project}", f"--location={loc}", "--use_legacy_sql=false",
                f"--maximum_bytes_billed={CAP_BYTES}", "--format=csv", "--max_rows=1000000", q], timeout=300)
        if o.returncode:
            msg = " ".join((o.stderr + o.stdout).split())
            need = re.search(r"(\d+) or higher required", msg)
            problems.append(f"{loc} region not read: its job log needs {int(need.group(1)) / 1e9:.1f} GB, over the "
                            f"{CAP_BYTES / 1e9:.0f} GB limit" if need else f"{loc} region not read: {msg[-160:]}")
            continue
        rows += list(csv.DictReader(io.StringIO(o.stdout)))
    today = now.date()
    m0 = today.replace(day=1)
    pm0 = (m0 - dt.timedelta(days=1)).replace(day=1)
    days_in_m = calendar.monthrange(today.year, today.month)[1]
    daily, who, day_who = collections.defaultdict(float), collections.defaultdict(float), collections.defaultdict(collections.Counter)
    day_mine, mine_who = collections.defaultdict(float), set()
    prev_same = prev_total = 0.0
    reserved = 0
    for r in rows:
        d = dt.date.fromisoformat(r["d"]); c = usd(r["bytes"]); reserved += int(r["reserved_jobs"] or 0)
        if d >= m0:
            daily[d] += c; who[short(r["user_email"])] += c; day_who[d][short(r["user_email"])] += c
            if is_mine(r["user_email"]):
                day_mine[d] += c; mine_who.add(short(r["user_email"]))
        elif d >= pm0:
            prev_total += c
            if d.day <= today.day:
                prev_same += c
    mtd = sum(daily.values())
    window = min(PACE_DAYS, today.day - 1)
    pace = sum(daily.get(today - dt.timedelta(days=k), 0.0) for k in range(1, window + 1)) / window if window else None
    done = sum(v for d, v in daily.items() if d < today)
    projected = done + pace * (days_in_m - today.day + 1) if pace is not None else None
    series = []
    for i in range(days_in_m):
        d = m0 + dt.timedelta(days=i)
        top = day_who[d].most_common(1)
        series.append({"date": d.isoformat(), "usd": round(daily.get(d, 0.0), 4), "mine": round(day_mine.get(d, 0.0), 4), "future": d > today,
                       "partial": d == today, "top": top[0][0] if top else ""})
    complete = [daily.get(m0 + dt.timedelta(days=i), 0.0) for i in range(today.day - 1)]
    med = statistics.median(complete) if complete else 0
    spikes = [{"date": s["date"], "usd": round(s["usd"], 2), "top": s["top"],
               "share": round(s["usd"] / mtd, 3) if mtd else 0}
              for s in series if not s["future"] and s["usd"] >= max(5.0, 3 * med)]
    ranked = sorted(who.items(), key=lambda kv: -kv[1])
    top = [{"who": k, "usd": round(v, 2), "mine": k in mine_who} for k, v in ranked[:5]]
    if len(ranked) > 5:
        top.append({"who": f"{len(ranked) - 5} others", "usd": round(sum(v for _, v in ranked[5:]), 2)})
    return {"project": project,
            "mtd": round(mtd, 2), "mine": round(sum(day_mine.values()), 2), "prev_same": round(prev_same, 2), "prev_total": round(prev_total, 2),
            "pace": None if pace is None else round(pace, 2), "projected": None if projected is None else round(projected, 2),
            "pace_days": window, "days": series, "top": top, "spikes": spikes,
            "reserved_jobs": reserved, "problems": problems, "unread_minor_regions": minor}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--projects", help="comma-separated; default: discovered from your own BigQuery jobs")
    a.add_argument("--bill-to", default=os.environ.get("MORNING_FAIRY_GCP_BILL_TO"),
                   help="project that pays for the reads (default: each project pays for its own)")
    a.add_argument("--mine", help="comma-separated account patterns that count as yours (default: <home>/spend_accounts.json)")
    a.add_argument("--json", action="store_true")
    o = a.parse_args()
    global BILL_TO, ME, MINE
    BILL_TO = o.bill_to or None
    home = os.environ.get("MORNING_FAIRY_HOME") or os.path.expanduser("~/.morning-fairy")
    MINE = o.mine.split(",") if o.mine else read_mine(os.path.join(home, "spend_accounts.json"))
    ME = sh(["gcloud", "config", "get-value", "account"]).stdout.strip()
    now = dt.datetime.now().astimezone()
    projects = o.projects.split(",") if o.projects else discover(now)
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda p: measure(p, now), projects))
    res.sort(key=lambda r: -r["mtd"])
    m0 = now.date().replace(day=1)
    out = {"as_of": now.isoformat(timespec="minutes"), "month": f"{m0:%B %Y}",
           "prev_month": f"{(m0 - dt.timedelta(days=1)):%B}", "price_per_tib": PRICE_PER_TIB, "billed_to": BILL_TO or "each project itself",
           "active_days": ACTIVE_DAYS, "projects": res, "mine_accounts": ["your own login"] + MINE,
           "credit": {"name": "agy-gcp-companion", "by": "ericsk", "url": "https://github.com/ericsk/agy-gcp-companion"}}
    if o.json:
        json.dump(out, sys.stdout, indent=1)
    else:
        for r in res:
            print(f'{r["project"]:32} ${r["mtd"]:9.2f} this month  (same days last month ${r["prev_same"]:.2f}; '
                  f'month-end ~${r["projected"] or 0:.2f}){"  PROBLEMS: " + "; ".join(r["problems"]) if r["problems"] else ""}')


if __name__ == "__main__":
    main()
