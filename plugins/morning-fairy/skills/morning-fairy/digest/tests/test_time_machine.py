"""Tests for the time machine's place on the page (a top-row button and a dialog, no tab) and for the way back to the
newest brief that serve.py adds to an earlier one.

Run from anywhere:  python3 -I -B -m unittest discover -s ~/.claude/skills/jira-fairy/digest/tests -v
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

DIGEST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIGEST))  # -I leaves the script's folder off the path

import build_digest as bd  # noqa: E402
import serve  # noqa: E402

from test_fairy_look import FIXTURE  # noqa: E402  (the made-up demo morning)


def build(with_log):
    d = json.loads(FIXTURE.read_text())
    if not with_log:
        return bd.build(d)
    with tempfile.TemporaryDirectory() as tmp:
        return bd.build(d, log=str(Path(tmp) / "streak.jsonl"))


class Placement(unittest.TestCase):
    def test_button_and_dialog_not_a_tab(self):
        html = build(True)
        self.assertIn('id="tm-open"', html)
        top = html[html.index('class="nav-tools"'):html.index('id="look"')]
        self.assertIn('id="tm-open"', top, "the clock sits in the top row, before the look button")
        dlg = re.search(r'<dialog class="tm-dlg" id="tm-dlg".*?</dialog>', html, re.S)
        self.assertTrue(dlg and 'class="streak tm' in dlg.group(0), "the time machine lives in the dialog")
        self.assertNotIn('id="tab-calendar"', html)
        self.assertNotIn('id="sec-calendar"', html)
        secs = json.loads(re.search(r'<script type="application/json" id="stage-data">(.*?)</script>', html, re.S).group(1))["secs"]
        self.assertNotIn("calendar", [s[0] for s in secs], "the deck, signposts and swipes skip it")

    def test_no_time_machine_no_button(self):
        html = build(False)
        self.assertNotIn('id="tm-open"', html)
        self.assertNotIn('<dialog class="tm-dlg"', html)

    def test_page_script_has_the_past_function(self):
        html = build(True)
        self.assertNotIn("{tm_past}", html)
        self.assertIn("'http://127.0.0.1:8765/', false", html)  # a file cannot know today's brief exists


class WayBack(unittest.TestCase):
    def test_pill_carries_the_script_to_the_newest(self):
        out = serve.back_pill("2026-03-11 Morning brief and Jira digest.html", "2026-03-12 Morning brief and Jira digest.html")
        self.assertIn('id="tm-back"', out)
        self.assertIn('"/brief/2026-03-12%20Morning%20brief%20and%20Jira%20digest.html"', out)
        self.assertIn(bd.TM_PAST_JS, out)

    def test_old_call_still_works(self):
        out = serve.back_pill("2026-03-11 Morning brief and Jira digest.html")
        self.assertIn('id="tm-back"', out)
        self.assertNotIn("<script>", out)


if __name__ == "__main__":
    unittest.main()
