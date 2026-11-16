"""Tests for the Hours for Tempo chapter (build_digest.render_hours), the Fill Tempo prompt both sides build from
clients.json's "fill_tempo" block, and the helper's /fill-hours route (serve.py).

Run from the repo root:  python3 -I -B -m unittest discover -s plugins/morning-fairy/skills/morning-fairy/digest/tests -v
Nothing is launched: launch_fill is replaced, so no Terminal window opens and no Claude session starts. The config is a
temp file of the test's own, so a clients.json you keep beside the builder is never read.
"""
import http.client
import json
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path

DIGEST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIGEST))  # -I leaves the script's folder off the path

from test_fairy_look import FIXTURE  # noqa: E402  (also points the helper at a temp folder)
import build_digest as bd  # noqa: E402
import serve  # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="mf-hours-"))
FILL = {"tempo_url": "https://example.atlassian.net/tempo#!/my-work/week",
        "work_items": "Meetings go on ADMIN-8.", "folder": str(_TMP)}


def entry(project, minutes, billable, what="", key=""):
    return {"project": project, "what": what, "key": key, "minutes": minutes, "billable": billable}


HOURS = {"days": [
    {"date": "2026-03-09", "label": "Mon 9", "entries": [entry("Lighthouse Co", 405, True, "Client work", "LH-10"),
                                                        entry("Lighthouse Co", 30, False, "Workshop", "LH-1"),
                                                        entry("Admin", 30, False, "Standup", "ADMIN-8")],
     "unattributed": 0, "logged": 300},
    {"date": "2026-03-10", "label": "Tue 10", "entries": [entry("Orchard app", 60, True)], "unattributed": 90, "logged": None},
    {"date": "2026-03-11", "label": "Wed 11", "entries": [], "unattributed": 0, "logged": None},
]}


def widths(html):
    return [float(w) for w in re.findall(r'class="hseg[^"]*" style="width:([\d.]+)%"', html)]


class Config:
    """Point the builder and the helper at one temp clients.json (or none) for the length of a test."""

    def use_config(self, block, name="clients.json"):
        path = _TMP / name
        if block is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(json.dumps({"clients": [], "fill_tempo": block}), encoding="utf-8")
        saved = bd.FILL_CONFIG_FILE, serve.FILL_CONFIG
        bd.FILL_CONFIG_FILE = serve.FILL_CONFIG = path
        self.addCleanup(lambda: (setattr(bd, "FILL_CONFIG_FILE", saved[0]), setattr(serve, "FILL_CONFIG", saved[1])))


class RenderHours(Config, unittest.TestCase):
    def test_totals_split_billable_non_billable_and_to_attribute(self):
        h = bd.render_hours(HOURS, ["Lighthouse Co", "Orchard app", "Admin"])
        stats = re.findall(r'<span class="hstat-v">([^<]+)</span><span class="hstat-l">([^<]+)</span>', h)
        self.assertEqual(stats, [("7h45", "Billable"), ("1h", "Non-billable"), ("1h30", "To attribute")])

    def test_week_bar_adds_up_to_the_whole(self):
        h = bd.render_hours(HOURS, [])
        week = re.search(r'<div class="hweek"[^>]*>(.*?)</div>', h).group(1)
        self.assertAlmostEqual(sum(widths(week)), 100.0, places=2)

    def test_day_bars_share_one_scale(self):
        h = bd.render_hours(HOURS, [])
        days = re.findall(r'<span class="htrack"[^>]*>(.*?)</span><span class="hday-t">', h)
        self.assertEqual(len(days), 3)
        self.assertAlmostEqual(sum(widths(days[0])), 100.0, places=2)  # the longest day fills the track
        self.assertAlmostEqual(sum(widths(days[1])), 150 / 465 * 100, places=2)
        self.assertEqual(widths(days[2]), [])

    def test_hues_follow_the_projects_list_not_the_minutes(self):
        h = bd.render_hours(HOURS, ["Orchard app", "Lighthouse Co", "Admin"])
        self.assertIn('data-tip="Orchard app: 1h"', h.replace(", billable", ""))
        self.assertRegex(h, r'class="hseg hs1" style="width:[\d.]+%" data-tip="Orchard app')
        self.assertRegex(h, r'class="hseg hs2" style="width:[\d.]+%" data-tip="Lighthouse Co, Client work')

    def test_a_fifth_project_falls_back_to_grey(self):
        many = {"days": [{"date": "2026-03-09", "label": "Mon", "entries": [entry(f"P{i}", 10, True) for i in range(6)]}]}
        h = bd.render_hours(many, [])
        self.assertEqual(h.count('class="hseg hs0"'), 4)  # P4 and P5, in the week bar and the day bar

    def test_tempo_states(self):
        h = bd.render_hours(HOURS, [])
        self.assertIn('<small class="hgap">gap 2h45</small>', h)  # 7h45 proposed, 5h in Tempo
        self.assertIn("<small>Tempo not read</small>", h)
        self.assertIn("<small>nothing measured</small>", h)
        self.assertEqual(h.count('class="hlog"'), 1)
        full = {"days": [dict(HOURS["days"][0], logged=600)]}
        self.assertIn("all in Tempo", bd.render_hours(full, []))

    def test_text_is_escaped(self):
        bad = {"days": [{"date": "x", "label": "<b>Mon</b>", "note": "<script>x</script>",
                         "entries": [entry('<img src=x onerror=1>', 30, True, 'a"b')]}], "logged_note": "<i>n</i>"}
        h = bd.render_hours(bad, [])
        for raw in ("<b>Mon", "<script>x", "<img src", "<i>n"):
            self.assertNotIn(raw, h)

    def test_bad_entries_never_stop_the_build(self):
        bad = {"days": [{"date": "x", "label": "Mon", "logged": "n/a", "unattributed": None, "entries": [
            {"project": "", "minutes": 30}, {"minutes": 15}, {"project": "A", "minutes": None, "billable": True},
            {"project": "A", "minutes": -30, "billable": True}, {"project": "A", "minutes": "60", "billable": True}, "junk"]}, "junk"]}
        h = bd.render_hours(bad, [])
        stats = re.findall(r'<span class="hstat-v">([^<]+)</span>', h)
        self.assertEqual(stats, ["1h", "0m", "45m"])  # 60 billable; the two entries with no project are to attribute
        self.assertTrue(all(w >= 0 for w in widths(h)))

    def test_table_view_lists_every_entry(self):
        h = bd.render_hours(HOURS, [])
        self.assertEqual(len(re.findall(r"<tr><td>", h)), 5)  # four entries and Tue's 1h30 to attribute

    def page_prompt(self):
        content = json.loads(FIXTURE.read_text())
        content["chapters"].append({"id": "hours", "nav": "Hours", "title": "Hours for Tempo", "hours": HOURS})
        page = bd.build(content)
        self.assertIn('class="hours"', page)
        m = re.search(r'<script type="application/json" id="fill-prompt">(.*?)</script>', page)
        return json.loads(m.group(1).replace("<\\/", "</"))

    def test_page_carries_the_configured_prompt_only_with_an_hours_chapter(self):
        self.use_config(FILL)
        self.assertNotIn('id="fill-prompt"', bd.build(json.loads(FIXTURE.read_text())))
        prompt = self.page_prompt()
        self.assertEqual(bd.render_hours(HOURS, []).count("data-fill-go"), 1)
        for want in ("{date}", "{day}", FILL["tempo_url"], FILL["work_items"], str(DIGEST / "measure_session_hours.py"),
                     str(DIGEST.parent / "SKILL.md")):
            self.assertIn(want, prompt)
        self.assertNotIn("\n", prompt)
        self.assertNotRegex(prompt, r"\{(skill_md|measure|tempo_url|work_items)\}")

    def test_no_fill_tempo_block_means_no_button(self):
        for block in (None, {}, {"tempo_url": "  "}, {"work_items": "x"}, "not a dict"):
            with self.subTest(block=block):
                self.use_config(block)
                self.assertEqual(bd.fill_prompt_template(), "")
                self.assertEqual(self.page_prompt(), "")
                self.assertNotIn("data-fill", bd.render_hours(HOURS, []))  # no panel at all, so never a dead button

    def test_config_text_is_not_searched_for_placeholders(self):
        self.use_config(dict(FILL, work_items="Put {tempo_url} and {measure} here."))
        self.assertIn("Put {tempo_url} and {measure} here.", bd.fill_prompt_template())

    def test_old_rows_still_render_and_get_the_button(self):
        self.use_config(FILL)
        ch = {"id": "hours", "title": "Hours", "rows": [{"title": "Mon 9", "html": "Measured: Lighthouse 7h15."}]}
        out = bd.render_chapter(ch)
        self.assertIn("Measured: Lighthouse 7h15.", out)
        self.assertEqual(out.count("data-fill-go"), 1)
        self.assertNotIn("data-fill-go", bd.render_chapter(dict(ch, id="nochange")))


class FillPrompt(Config, unittest.TestCase):
    def test_date_bounds(self):
        today = date(2026, 3, 16)
        self.assertEqual(serve.fill_date("2026-03-16", today), today)
        self.assertEqual(serve.fill_date("2026-03-02", today), date(2026, 3, 2))
        for bad in ("2026-03-17", "2026-03-01", "2026-02-30", "16/03/2026", "2026-03-16x", "", None, 20260316):
            self.assertIsNone(serve.fill_date(bad, today), bad)

    def test_prompt_names_the_day_and_has_no_placeholders(self):
        p = serve.fill_prompt(date(2026, 3, 13), FILL)
        self.assertIn("Friday 13 March 2026 (2026-03-13)", p)
        self.assertIn("--start 2026-03-13 --end 2026-03-13", p)
        self.assertIn(FILL["tempo_url"], p)
        self.assertNotIn("{", p)
        self.assertNotIn("\n", p)

    def test_builder_and_helper_build_the_same_prompt(self):
        self.use_config(FILL)
        self.assertEqual(bd.FILL_PROMPT_FILE, serve.FILL_PROMPT)
        self.assertEqual(bd.fill_prompt_template(), serve.fill_template(serve.fill_config()))

    def test_both_read_clients_json_beside_the_code(self):
        self.assertEqual(bd.FILL_CONFIG_FILE, DIGEST / "clients.json")
        self.assertEqual(serve.FILL_CONFIG, DIGEST / "clients.json")

    def test_folder_comes_from_the_config(self):
        self.assertEqual(serve.fill_folder(FILL), _TMP)
        self.assertEqual(serve.fill_folder(dict(FILL, folder=str(_TMP / "missing"))), Path.home())
        self.assertEqual(serve.fill_folder({"tempo_url": "x"}), Path.home())

    def test_the_example_config_turns_the_button_on(self):
        ex = json.loads((DIGEST / "clients.example.json").read_text())["fill_tempo"]
        self.assertTrue(ex["tempo_url"].startswith("https://"))
        self.assertIn("{date}", serve.fill_template(ex))


class FillRoute(Config, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = serve.launch_fill
        cls.launched = []
        serve.launch_fill = lambda prompt, folder: cls.launched.append((prompt, folder))
        cls.record = [serve.launch_fill]  # in a list, so self.record[0] is the plain function, not a bound method
        cls.srv = serve.ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        serve.launch_fill = cls.saved

    def setUp(self):
        self.launched.clear()
        serve._fill_last[0] = None
        self.use_config(FILL)

    def post(self, body, origin="http://127.0.0.1:8765", host="127.0.0.1:8765"):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        data = json.dumps(body).encode()
        h = {"Host": host, "Content-Type": "application/json", "Content-Length": str(len(data))}
        if origin:
            h["Origin"] = origin
        c.request("POST", "/fill-hours", body=data, headers=h)
        r = c.getresponse()
        out = (r.status, r.read())
        c.close()
        return out

    def test_opens_one_session_for_a_good_date_in_the_configured_folder(self):
        day = (date.today() - timedelta(days=1)).isoformat()
        st, body = self.post({"date": day})
        self.assertEqual(st, 200)
        self.assertEqual(json.loads(body), {"ok": True, "date": day})
        self.assertEqual(len(self.launched), 1)
        prompt, folder = self.launched[0]
        self.assertIn(f"--start {day} --end {day}", prompt)
        self.assertIn(FILL["tempo_url"], prompt)
        self.assertEqual(folder, _TMP)

    def test_a_double_tap_opens_one_session(self):
        day = date.today().isoformat()
        self.assertEqual(self.post({"date": day})[0], 200)
        self.assertEqual(self.post({"date": day})[0], 429)
        self.assertEqual(len(self.launched), 1)

    def test_refuses_bad_dates_foreign_origins_and_hosts(self):
        today = date.today().isoformat()
        self.assertEqual(self.post({"date": "2099-01-01"})[0], 400)
        self.assertEqual(self.post({"date": "rm -rf ~"})[0], 400)
        self.assertEqual(self.post({"prompt": "anything"})[0], 400)
        self.assertEqual(self.post({"date": today}, origin="https://example.com")[0], 403)
        self.assertEqual(self.post({"date": today}, origin=None)[0], 403)
        self.assertEqual(self.post({"date": today}, host="evil.example:8765")[0], 403)
        self.assertEqual(self.launched, [])

    def test_off_without_a_fill_tempo_block(self):
        self.use_config(None)
        self.assertEqual(self.post({"date": date.today().isoformat()})[0], 404)
        self.assertEqual(self.post({"date": date.today().isoformat()}, origin="https://example.com")[0], 403)
        self.assertEqual(self.launched, [])

    def test_a_launch_that_times_out_still_blocks_a_quick_retry(self):
        def slow(prompt, folder):
            raise subprocess.TimeoutExpired("osascript", 20)
        serve.launch_fill = slow
        try:
            self.assertEqual(self.post({"date": date.today().isoformat()})[0], 500)
        finally:
            serve.launch_fill = self.record[0]
        self.assertEqual(self.post({"date": date.today().isoformat()})[0], 429)
        self.assertEqual(self.launched, [])

    def test_a_failed_launch_says_so_and_does_not_block_a_retry(self):
        def boom(prompt, folder):
            raise OSError("no Terminal")
        serve.launch_fill = boom
        try:
            self.assertEqual(self.post({"date": date.today().isoformat()})[0], 500)
        finally:
            serve.launch_fill = self.record[0]
        self.assertEqual(self.post({"date": date.today().isoformat()})[0], 200)


if __name__ == "__main__":
    unittest.main()
