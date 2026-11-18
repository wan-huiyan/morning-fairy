"""Tests for measure_session_hours.py, on synthetic transcripts.

unittest rather than pytest, because the repo's CI runs `python3 -m unittest
discover` over this folder and a pytest-only file would fail to import there.

Nothing here reads a real transcript: every fixture is written into the test's
own temp folder.
"""

import contextlib
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import measure_session_hours as m  # noqa: E402

TZ = dt.datetime.now().astimezone().tzinfo

CLIENTS = [
    {"name": "acme", "patterns": ["acme-platform"], "labels": ["Acme Corp"]},
    {"name": "zephyr", "patterns": ["/zephyr"], "labels": ["Zephyr"]},
    {"name": "internal", "patterns": ["/admin"], "labels": ["Internal"]},
]


def at(day, hour, minute=0):
    return dt.datetime(2026, 11, day, hour, minute)


def span(day, start, end, every=5):
    """Stamps every `every` minutes from start to end, as a working session
    produces. Written as a helper because hand-listing stamps an hour apart
    creates a fixture the 15-minute gap rule correctly scores as zero."""
    h, mi = (int(x) for x in start.split(":"))
    eh, em = (int(x) for x in end.split(":"))
    cur, stop, out = at(day, h, mi), at(day, eh, em), []
    while cur <= stop:
        out.append(cur)
        cur += dt.timedelta(minutes=every)
    if out[-1] != stop:
        out.append(stop)
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def write_session(self, project, name, cwd, stamps, first_user=None):
        d = os.path.join(self.root, project)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, name + ".jsonl")
        with open(path, "w") as fh:
            if first_user is not None:
                fh.write(json.dumps({
                    "type": "user", "cwd": cwd,
                    "timestamp": stamps[0].replace(tzinfo=TZ).isoformat(),
                    "message": {"content": first_user},
                }) + "\n")
            for s in stamps:
                fh.write(json.dumps({
                    "type": "assistant", "cwd": cwd,
                    "timestamp": s.replace(tzinfo=TZ).isoformat(),
                }) + "\n")
        return path

    def hours(self, start, end=None, gap=15.0, meetings=None):
        by_client = m.collect(self.root, CLIENTS, gap)
        if meetings:
            m.add_meetings(by_client, meetings)
        lo = dt.date.fromisoformat(start)
        hi = dt.date.fromisoformat(end) if end else lo
        return {n: m.daily_hours(iv, lo, hi) for n, iv in by_client.items()}


class TestMerging(Base):
    def test_overlapping_sessions_on_one_project_count_once(self):
        self.write_session("p1", "a", "/u/acme-platform", span(9, "10:00", "11:00"))
        self.write_session("p2", "b", "/u/acme-platform/.worktrees/w",
                           span(9, "10:20", "10:40"))
        got = self.hours("2026-11-09")
        self.assertAlmostEqual(got["acme"][dt.date(2026, 11, 9)], 1.0, places=5)

    def test_a_gap_over_the_threshold_is_not_counted(self):
        self.write_session("p1", "a", "/u/acme-platform",
                           [at(9, 10), at(9, 10, 10), at(9, 11, 40), at(9, 11, 50)])
        got = self.hours("2026-11-09")
        self.assertAlmostEqual(got["acme"][dt.date(2026, 11, 9)], 20 / 60, places=5)

    def test_a_gap_exactly_at_the_threshold_still_counts(self):
        self.write_session("p1", "a", "/u/acme-platform", [at(9, 10), at(9, 10, 15)])
        got = self.hours("2026-11-09")
        self.assertAlmostEqual(got["acme"][dt.date(2026, 11, 9)], 0.25, places=5)

    def test_a_session_crossing_midnight_splits_across_both_days(self):
        self.write_session("p1", "a", "/u/acme-platform",
                           [at(9, 23, 50), at(10, 0, 0), at(10, 0, 10)])
        got = self.hours("2026-11-09", "2026-11-10")["acme"]
        self.assertAlmostEqual(got[dt.date(2026, 11, 9)], 10 / 60, places=5)
        self.assertAlmostEqual(got[dt.date(2026, 11, 10)], 10 / 60, places=5)

    def test_days_outside_the_window_are_clipped_out(self):
        self.write_session("p1", "a", "/u/acme-platform", span(8, "10:00", "11:00"))
        self.write_session("p2", "b", "/u/acme-platform", span(9, "10:00", "11:00"))
        self.assertEqual(set(self.hours("2026-11-09")["acme"]), {dt.date(2026, 11, 9)})


class TestWallClock(Base):
    def test_two_projects_at_once_are_separate_but_the_wall_clock_merges_them(self):
        """The reason a parallel day must be split, not summed: per-project
        unions add up to more time than anyone actually sat there."""
        self.write_session("p1", "a", "/u/acme-platform", span(9, "10:00", "11:00"))
        self.write_session("p2", "b", "/u/zephyr", span(9, "10:30", "11:30"))
        by_client = m.collect(self.root, CLIENTS, 15.0)
        day = dt.date(2026, 11, 9)
        self.assertAlmostEqual(m.daily_hours(by_client["acme"], day, day)[day], 1.0, places=5)
        self.assertAlmostEqual(m.daily_hours(by_client["zephyr"], day, day)[day], 1.0, places=5)
        everything = [iv for ivs in by_client.values() for iv in ivs]
        self.assertAlmostEqual(m.daily_hours(everything, day, day)[day], 1.5, places=5)


class TestAttribution(Base):
    def test_classify_is_first_match_wins_and_case_insensitive(self):
        cl = [{"name": "narrow", "patterns": ["acme-atlas"]},
              {"name": "wide", "patterns": ["acme"]}]
        self.assertEqual(m.classify("/u/Acme-Atlas-thing", cl), "narrow")
        self.assertEqual(m.classify("/u/acme-platform", cl), "wide")
        self.assertEqual(m.classify(None, cl), "unattributed")

    def test_the_brief_header_beats_the_folder_it_was_opened_in(self):
        """The real failure: an Internal brief opened in a client repo billed a
        whole morning of internal work to that client."""
        self.write_session(
            "p1", "a", "/u/acme-platform", span(13, "10:00", "11:00"),
            first_user="Morning brief tasks for Internal, Friday 13 Nov 2026\n"
                       "Open this in Claude Code in: ~/admin",
        )
        got = self.hours("2026-11-13")
        self.assertNotIn("acme", got)
        self.assertAlmostEqual(got["internal"][dt.date(2026, 11, 13)], 1.0, places=5)

    def test_a_client_brief_in_that_clients_repo_is_still_that_client(self):
        self.write_session("p1", "a", "/u/acme-platform", span(10, "10:00", "11:00"),
                           first_user="Morning brief tasks for Acme Corp (client work)")
        got = self.hours("2026-11-10")
        self.assertAlmostEqual(got["acme"][dt.date(2026, 11, 10)], 1.0, places=5)

    def test_ordinary_work_with_no_header_falls_back_to_the_folder(self):
        self.write_session("p1", "a", "/u/acme-platform", span(10, "10:00", "11:00"),
                           first_user="pick up the handoff and carry on?")
        got = self.hours("2026-11-10")
        self.assertAlmostEqual(got["acme"][dt.date(2026, 11, 10)], 1.0, places=5)

    def test_an_unmapped_cwd_is_reported_not_dropped(self):
        """A scratch workspace has no project. It is a pile to attribute by
        hand, never a zero."""
        self.write_session("p1", "a", "/u/Library/scratch-2026-11-13", span(9, "10:00", "10:30"))
        got = self.hours("2026-11-09")
        self.assertAlmostEqual(got["unattributed"][dt.date(2026, 11, 9)], 0.5, places=5)


class TestScheduledAndTyped(Base):
    def test_scheduled_run_is_excluded_even_behind_a_system_reminder(self):
        """The tag is rarely first in the message; match it anywhere."""
        self.write_session(
            "p1", "sched", "/u/acme-platform", [at(9, 8), at(9, 8, 10)],
            first_user="<system-reminder>ctx</system-reminder>\n"
                       '<scheduled-task name="daily-digest" file="...">',
        )
        self.assertEqual(self.hours("2026-11-09"), {})

    def test_a_session_merely_mentioning_the_phrase_is_kept(self):
        self.write_session("p1", "a", "/u/acme-platform", span(9, "10:00", "10:30"),
                           first_user="can you edit the scheduled task SKILL.md for me?")
        got = self.hours("2026-11-09")
        self.assertAlmostEqual(got["acme"][dt.date(2026, 11, 9)], 0.5, places=5)

    def test_require_typed_drops_a_stretch_nobody_was_present_for(self):
        stamps = span(10, "10:00", "11:00")
        path = self.write_session("p1", "a", "/u/acme-platform", stamps)
        with open(path, "a") as fh:
            for s in span(10, "14:00", "14:30"):
                fh.write(json.dumps({
                    "type": "user", "cwd": "/u/acme-platform",
                    "timestamp": s.replace(tzinfo=TZ).isoformat(),
                    "message": {"content": "now do the other half"},
                }) + "\n")
        day = dt.date(2026, 11, 10)
        loose = m.collect(self.root, CLIENTS, 15.0)
        strict = m.collect(self.root, CLIENTS, 15.0, require_typed=True)
        self.assertAlmostEqual(m.daily_hours(loose["acme"], day, day)[day], 1.5, places=5)
        self.assertAlmostEqual(m.daily_hours(strict["acme"], day, day)[day], 0.5, places=5)

    def test_a_harness_notice_is_not_a_typed_message(self):
        for text in ["<system-reminder>x</system-reminder>",
                     "<task-notification>done</task-notification>",
                     '<cross-session-message from="a">hi</cross-session-message>']:
            self.assertFalse(m.is_typed_by_her({"type": "user", "message": {"content": text}}))
        self.assertTrue(m.is_typed_by_her({"type": "user", "message": {"content": "please resume"}}))
        self.assertFalse(m.is_typed_by_her({"type": "assistant", "message": {"content": "ok"}}))

    def test_a_loaded_skill_a_loop_prompt_or_a_context_summary_is_not_typed(self):
        for extra in ({"isMeta": True},
                      {"isCompactSummary": True, "isVisibleInTranscriptOnly": True}):
            obj = dict({"type": "user",
                        "message": {"content": "Watch my access request until it is set up."}}, **extra)
            self.assertFalse(m.is_typed_by_her(obj))

    def test_the_cli_drops_unattended_stretches_unless_asked(self):
        # An agent running alone: no message anyone typed.
        self.write_session("p1", "a", "/u/acme-platform", span(10, "10:00", "11:00"))
        cmap = os.path.join(self.root, "clients.json")
        with open(cmap, "w") as fh:
            json.dump({"clients": CLIENTS}, fh)
        args = ["--start", "2026-11-10", "--projects-dir", self.root,
                "--clients", cmap, "--json"]

        def run(extra):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                m.main(args + extra)
            return json.loads(buf.getvalue())["by_client"]

        self.assertNotIn("acme", run([]))
        self.assertNotIn("acme", run(["--require-typed"]))  # old flag still accepted
        self.assertAlmostEqual(run(["--include-unattended"])["acme"]["2026-11-10"], 1.0, places=5)


class TestMeetingsAndOptIn(Base):
    def test_a_meeting_is_unioned_in_and_does_not_double_count(self):
        self.write_session("p1", "a", "/u/acme-platform", span(12, "15:00", "16:30"))
        meetings = os.path.join(self.root, "meetings.json")
        with open(meetings, "w") as fh:
            json.dump([
                {"client": "acme", "start": "2026-11-12T16:00", "end": "2026-11-12T16:30"},
                {"client": "acme", "start": "2026-11-12T11:30", "end": "2026-11-12T12:00"},
            ], fh)
        got = self.hours("2026-11-12", meetings=meetings)
        self.assertAlmostEqual(got["acme"][dt.date(2026, 11, 12)], 2.0, places=5)

    def test_a_missing_project_map_stops_with_a_readable_message(self):
        """Opt-in: no clients.json, no hours step. Never a silent empty map,
        which would report every project as zero."""
        with self.assertRaises(SystemExit) as caught:
            m.load_clients(os.path.join(self.root, "nope.json"))
        self.assertIn("opt-in", str(caught.exception))

    def test_the_shipped_example_map_parses_and_has_the_keys_classify_reads(self):
        """Shape only. It does NOT check that the example names are made up —
        that is a reading job before publishing, not an assertion."""
        clients = m.load_clients(m.EXAMPLE_MAP)
        self.assertTrue(clients)
        for c in clients:
            self.assertIn("name", c)
            self.assertIn("patterns", c)


class TestSpans(Base):
    def test_spans_list_every_stretch_typed_alone_and_meetings(self):
        self.write_session("p1", "a", "/u/acme-platform", span(10, "10:00", "10:30"), first_user="Check the <b>model</b> chart")
        self.write_session("p1", "b", "/u/acme-platform", span(10, "14:00", "14:20"))  # an agent running alone
        self.write_session("p2", "c", "/u/acme-platform", span(10, "23:40", "23:55") + [at(11, 0, 10)], first_user="late")
        cmap = os.path.join(self.root, "clients.json")
        with open(cmap, "w") as fh:
            json.dump({"clients": CLIENTS}, fh)
        meet = os.path.join(self.root, "meetings.json")
        with open(meet, "w") as fh:
            json.dump([{"client": "internal", "title": "Weekly sync", "start": at(10, 11).replace(tzinfo=TZ).isoformat(),
                        "end": at(10, 11, 30).replace(tzinfo=TZ).isoformat()}], fh)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.main(["--start", "2026-11-10", "--projects-dir", self.root, "--clients", cmap, "--meetings", meet, "--json", "--spans"])
        spans = json.loads(buf.getvalue())["spans"]
        self.assertEqual(list(spans), ["2026-11-10"], "the 00:00-00:10 tail on the 11th is outside the window")
        got = spans["2026-11-10"]
        self.assertEqual([(s["client"], s["kind"], s["start"], s["end"], s.get("counted"), s["title"]) for s in got], [
            ("acme", "session", "10:00", "10:30", True, "Check the model chart"),
            ("internal", "meeting", "11:00", "11:30", None, "Weekly sync"),
            ("acme", "session", "14:00", "14:20", False, ""),
            ("acme", "session", "23:40", "24:00", True, "late")])
        self.assertEqual((got[0]["typed"], got[2]["typed"]), (1, 0))


    def write_turns(self, project, name, cwd, turns):
        """A session from [(datetime, who, text)], who "me" (a message you typed) or "agent"."""
        d = os.path.join(self.root, project)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, name + ".jsonl"), "w") as fh:
            for when, who, text in turns:
                o = ({"type": "user", "message": {"content": text}} if who == "me" else
                     {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
                fh.write(json.dumps({**o, "cwd": cwd, "timestamp": when.replace(tzinfo=TZ).isoformat()}) + "\n")

    def test_quiet_stretches_before_a_reply_are_listed_and_cut(self):
        turns = [(t, "agent", "working") for t in span(10, "10:00", "10:30")]
        turns[0] = (turns[0][0], "me", "Start the analysis")
        turns += [(t, "agent", "a background job finished") for t in span(10, "11:00", "11:05")]  # the agent alone
        turns += [(at(10, 11, 40), "me", "here are my five words"), (at(10, 11, 45), "agent", "ok")]
        turns += [(at(10, 16, 0), "me", "after a long break"), (at(10, 16, 5), "agent", "ok")]  # 4h15 of silence: no quiet
        self.write_turns("p1", "a", "/u/acme-platform", turns)
        self.write_session("p2", "b", "/u/admin", span(10, "10:52", "10:58"), first_user="other work")
        cmap = os.path.join(self.root, "clients.json")
        with open(cmap, "w") as fh:
            json.dump({"clients": CLIENTS}, fh)
        iso = lambda h, mi: at(10, h, mi).replace(tzinfo=TZ).isoformat()
        meet = os.path.join(self.root, "meetings.json")
        with open(meet, "w") as fh:
            json.dump([{"client": "internal", "title": "Sync", "start": iso(10, 40), "end": iso(10, 50)},
                       {"client": "internal", "away": True, "start": iso(11, 20), "end": iso(11, 30)}], fh)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.main(["--start", "2026-11-10", "--projects-dir", self.root, "--clients", cmap, "--meetings", meet, "--json", "--spans"])
        out = json.loads(buf.getvalue())
        quiet = [(s["start"], s["end"], s["words"], s["counted"]) for s in out["spans"]["2026-11-10"] if s["kind"] == "quiet"]
        # 10:30-11:00 less the sync and the other session's typing (10:50-10:52 is under 5 minutes, so dropped);
        # then 11:05-11:40 less the away block. The chain runs back across the agent-alone stretch at 11:00.
        self.assertEqual(quiet, [("10:30", "10:40", 5, False), ("11:05", "11:20", 5, False), ("11:30", "11:40", 5, False)])
        self.assertAlmostEqual(out["by_client"]["internal"]["2026-11-10"], 16 / 60, delta=0.01)  # the sync counts, away does not


if __name__ == "__main__":
    unittest.main()
