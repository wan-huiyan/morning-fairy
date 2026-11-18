"""Tests for Approve and log: build_digest.render_approve / log_rows and serve.py's /log-hours route.

Run from the repo root:  python3 -I -B -m unittest discover -s plugins/morning-fairy/skills/morning-fairy/digest/tests -v
Nothing is launched: launch_fill is replaced, so no Terminal window opens and no Claude session starts. The brief's saved
content and the "fill_tempo" config are files of the test's own in a temp folder.
"""
import http.client
import json
import shutil
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path

DIGEST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIGEST))  # -I leaves the script's folder off the path

from test_hours import FILL, Config  # noqa: E402  (also points the helper at a temp folder)
import build_digest as bd  # noqa: E402
import serve  # noqa: E402

TODAY = date.today()
DAY = (TODAY - timedelta(days=1)).isoformat()


def hours(logged=0):
    return {"days": [
        {"date": DAY, "label": "Yesterday", "logged": logged, "unattributed": 30, "entries": [
            {"project": "Acme", "what": "Client work", "desc": "Model checks for the deck", "key": "ACME-1", "minutes": 135, "billable": True},
            {"project": "Admin", "what": "Meetings", "key": "ADM-8", "minutes": 90, "billable": False},
            {"project": "Admin", "what": "Nothing", "key": "ADM-9", "minutes": 0, "billable": False}]},
        {"date": (TODAY - timedelta(days=2)).isoformat(), "label": "Before", "logged": 300, "entries": [
            {"project": "Acme", "key": "ACME-1", "minutes": 240, "billable": True}]}]}


def content(logged=0):
    return {"date": TODAY.isoformat(), "chapters": [{"id": "hours", "title": "Hours", "hours": hours(logged)}]}


class Rows(unittest.TestCase):
    def test_work_item_and_billable_come_from_the_brief(self):
        got = bd.log_rows(content(), DAY, [{"i": 0, "minutes": 120, "desc": "  Edited\x07 text  "}, {"i": 1, "minutes": 90}])
        self.assertEqual([(e["key"], m, d) for e, m, d in got], [("ACME-1", 120, "Edited text"), ("ADM-8", 90, "Meetings")])

    def test_anything_the_brief_does_not_propose_is_refused(self):
        c = content()
        for day, rows in [("2020-01-01", [{"i": 0, "minutes": 60}]),             # not a day of this brief
                          ((TODAY - timedelta(days=2)).isoformat(), [{"i": 0, "minutes": 60}]),  # already all in Tempo
                          (DAY, [{"i": 5, "minutes": 60}]), (DAY, [{"i": True, "minutes": 60}]),
                          (DAY, [{"i": 2, "minutes": 60}]),                       # a zero-minute row is not offered
                          (DAY, [{"i": 0, "minutes": 60}, {"i": 0, "minutes": 60}])]:
            with self.assertRaises(KeyError, msg=(day, rows)):
                bd.log_rows(c, day, rows)
        for rows in ([{"i": 0, "minutes": 3}], [{"i": 0, "minutes": 7}], [{"i": 0, "minutes": 605}], [{"i": 0, "minutes": "60"}],
                     [{"i": 0, "minutes": 60, "desc": "x" * 161}], []):
            with self.assertRaises(ValueError, msg=rows):
                bd.log_rows(c, DAY, rows)


class Card(unittest.TestCase):
    def test_only_days_with_a_gap_and_rows_get_a_card(self):
        html = bd.render_approve(bd._clean_hours(hours()))
        self.assertEqual(html.count('class="happ-day"'), 1)
        self.assertIn(f'data-day="{DAY}"', html)
        self.assertEqual(html.count('class="happ-on"'), 2, "the zero-minute row is left out")
        self.assertIn('data-i="1"', html)
        self.assertIn('value="Model checks for the deck"', html)
        self.assertEqual(bd.render_approve(bd._clean_hours(hours(logged=225))), "")


class Route(Config, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        (cls.tmp / "runs").mkdir()
        (cls.tmp / "runs" / f"content-{TODAY.isoformat()}.json").write_text(json.dumps(content()))
        cls.saved = (serve.DIGEST, serve.launch_fill)
        cls.launched = []
        serve.DIGEST = cls.tmp
        serve.launch_fill = lambda prompt, folder: cls.launched.append((prompt, folder))
        cls.srv = serve.ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        serve.DIGEST, serve.launch_fill = cls.saved
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.launched.clear()
        serve._fill_last[0] = None
        self.use_config(FILL)

    def post(self, body, origin="http://127.0.0.1:8765"):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=30)
        data = json.dumps(body).encode()
        h = {"Host": "127.0.0.1:8765", "Content-Type": "application/json", "Content-Length": str(len(data)), "Origin": origin}
        c.request("POST", "/log-hours", body=data, headers=h)
        r = c.getresponse()
        out = r.status
        r.read()
        c.close()
        return out

    def body(self, rows):
        return {"brief": TODAY.isoformat(), "day": DAY, "rows": rows}

    def test_logs_exactly_the_approved_rows_once(self):
        self.assertEqual(self.post(self.body([{"i": 0, "minutes": 120, "desc": 'Deck "v2" checks'}])), 200)
        self.assertEqual(len(self.launched), 1)
        p, folder = self.launched[0]
        self.assertIn("work item ACME-1, 2h00, billable, description \"Deck 'v2' checks\"", p)
        self.assertNotIn("ADM-8", p)
        self.assertIn(f"({DAY})", p)
        self.assertIn(FILL["tempo_url"], p)
        self.assertNotIn("{", p, "every placeholder is filled")
        self.assertNotIn("\n", p)
        self.assertEqual(folder, serve.fill_folder(FILL))
        self.assertEqual(self.post(self.body([{"i": 0, "minutes": 120}])), 429, "a double tap starts one session")
        self.assertEqual(len(self.launched), 1)

    def test_refuses_forged_rows_other_sites_and_missing_briefs(self):
        self.assertEqual(self.post(self.body([{"i": 9, "minutes": 60}])), 400)
        self.assertEqual(self.post(self.body([{"i": 0, "minutes": 60, "key": "EVIL-1"}])), 400)
        self.assertEqual(self.post(self.body([{"i": 0, "minutes": 60}]), origin="https://example.com"), 403)
        self.assertEqual(self.post({"brief": (TODAY - timedelta(days=3)).isoformat(), "day": DAY, "rows": [{"i": 0, "minutes": 60}]}), 400)
        self.assertEqual(self.post({"brief": DAY, "day": DAY, "rows": [{"i": 0, "minutes": 60}]}), 404)
        self.assertEqual(self.launched, [])

    def test_off_without_a_fill_tempo_block(self):
        self.use_config(None)
        self.assertEqual(self.post(self.body([{"i": 0, "minutes": 120}])), 404)
        self.assertEqual(self.post(self.body([{"i": 0, "minutes": 120}]), origin="https://example.com"), 403)
        self.assertEqual(self.launched, [])

    def test_the_approve_card_shows_whether_or_not_fill_is_set_up(self):
        self.use_config(None)
        out = bd.render_hours(content()["chapters"][0]["hours"], [])
        self.assertIn("data-approve", out)
        self.assertNotIn("data-fill-go", out)


if __name__ == "__main__":
    unittest.main()
