"""Tests for the Scout chapter: web finds that are offers, never to-dos.

Run from the repo root:  python3 -I -B -m unittest discover -s plugins/morning-fairy/skills/morning-fairy/digest/tests -v
Pages are built in memory from the made-up demo morning; nothing is written anywhere. start.json is a temp file of the
test's own, so one you keep beside the builder is never read.
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

DIGEST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIGEST))  # -I leaves the script's folder off the path

from test_fairy_look import FIXTURE  # noqa: E402  (also points the helper at a temp folder)
import build_digest as bd  # noqa: E402

FIND = {"title": "A palette checker", "url": "https://github.com/example/palette-check", "text": "Could help. {source}",
        "source": "GitHub", "project": "AI tools", "links": [{"label": "Post", "url": "https://example.com/post"}],
        "claude": {"ask": "read its README and say whether it beats the validator", "size": "about 15 min"}}


def scout_chapter(items=None):
    return {"id": "scout", "nav": "Scout", "title": "Worth a look",
            "lists": [{"id": "scout", "tone": "scout", "title": "Found this morning", "items": items if items is not None else [dict(FIND)],
                       "empty": "Looked; nothing new."}]}


def page(chapters):
    """A whole page from the reference content with only these chapters."""
    d = json.loads(FIXTURE.read_text())
    d["chapters"] = chapters
    d.setdefault("projects", []).append({"name": "AI tools", "kind": "internal"})
    return bd.build(d)


def scout_only():
    return {"date": "2026-11-16", "projects": [{"name": "AI tools", "kind": "internal"}], "chapters": [scout_chapter()]}


class NothingWaits(unittest.TestCase):
    def test_mood_is_starry(self):
        self.assertEqual(bd.page_mood(scout_only()), "starry")

    def test_chapter_badge_is_zero(self):
        self.assertEqual(bd._chapter_count(scout_chapter()), 0)

    def test_time_machine_counts_no_todos(self):
        self.assertEqual(bd.day_facts(scout_only())["todos"], 0)

    def test_glance_counts_no_needs(self):
        html = bd.auto_glance(scout_only()["chapters"])
        bigs = re.findall(r'<span class="slice-big">(\d+)</span>', html)
        self.assertTrue(bigs)
        self.assertEqual(set(bigs), {"0"}, html)

    def test_a_warn_list_still_counts(self):
        d = scout_only()
        d["chapters"].append({"id": "today", "lists": [{"tone": "warn", "items": [{"title": "Reply to Sam", "stamp": "overdue"}]}]})
        self.assertEqual(bd.page_mood(d), "sweat")


class Renders(unittest.TestCase):
    def test_page_shows_the_find_with_no_done_pill_and_a_quest(self):
        with tempfile.TemporaryDirectory() as tmp:
            conf = Path(tmp) / "start.json"
            conf.write_text(json.dumps({"root": tmp}))
            saved, bd.START_CONFIG_FILE = bd.START_CONFIG_FILE, conf  # Start is opt-in: switch it on for this page
            try:
                html = page([scout_chapter()])
            finally:
                bd.START_CONFIG_FILE = saved
        self.assertIn('class="items items-scout"', html)
        self.assertIn("A palette checker", html)
        self.assertIn(".items-scout .item", html)
        li = re.search(r'<li class="item" id="item-scout-1".*?</li>', html, re.S).group(0)
        self.assertNotIn("data-did", li)  # an offer, not a to-do
        self.assertIn('data-start-quest=', html)  # its ask is a quest, with a Start button when Start is set up
        self.assertIn("read its README", html)

    def test_no_scout_css_without_a_scout_list(self):
        self.assertNotIn(".items-scout", page([{"id": "today", "title": "Today", "lists": [{"tone": "ok", "items": [{"title": "x"}]}]}]))

    def test_empty_scout_says_it_looked(self):
        self.assertIn("Looked; nothing new.", page([scout_chapter([])]))

    def test_the_guard_says_the_tasks_may_come_from_the_web(self):
        self.assertIn("email, Slack, calendar and the web", bd.TASK_GUARD)


class ReadScouted(unittest.TestCase):
    def test_reads_the_last_fortnight_of_scout_links_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)

            def put(day, chapters):
                (t / f"content-{day}.json").write_text(json.dumps({"chapters": chapters}))
            put("2026-11-13", [scout_chapter(), {"id": "today", "lists": [{"tone": "warn", "items": [{"title": "x", "url": "https://warn.example"}]}]}])
            put("2026-11-01", [scout_chapter([{"title": "old", "url": "https://too-old.example"}])])  # 15 days back
            put("2026-11-16", [scout_chapter([{"title": "today", "url": "https://today.example"}])])  # today is not "already shown"
            (t / "content-2026-11-12.json").write_text("{not json")
            got = bd.read_scouted(t, "2026-11-16")
        self.assertEqual(got, {"https://github.com/example/palette-check", "https://example.com/post"})

    def test_bad_date_or_missing_folder_reads_nothing(self):
        self.assertEqual(bd.read_scouted("/nonexistent", "2026-11-16"), set())
        self.assertEqual(bd.read_scouted("/nonexistent", "16/11/2026"), set())


class Example(unittest.TestCase):
    def test_example_has_a_scout_chapter_and_builds(self):
        d = json.loads((DIGEST / "example_content.json").read_text())
        self.assertIn("scout", [c["id"] for c in d["chapters"]])
        self.assertIn("items-scout", bd.build(d))


if __name__ == "__main__":
    unittest.main()
