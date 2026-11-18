"""The Spend chapter: rows for real spend, tiny projects folded, honest notes, fails soft."""
import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location("bd", pathlib.Path(__file__).resolve().parents[1] / "build_digest.py")
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)


def proj(name, mtd, **kw):
    days = [{"date": f"2026-11-{i:02d}", "usd": 1.0, "future": i > 18, "partial": i == 18, "top": "x (service account)"}
            for i in range(1, 31)]
    base = {"project": name, "mtd": mtd, "prev_same": 10.0, "prev_total": 20.0, "pace": 1.0, "projected": mtd + 12,
            "days": days, "top": [{"who": "x (service account)", "usd": mtd}], "spikes": [], "reserved_jobs": 0, "problems": []}
    base.update(kw)
    return base


class Spend(unittest.TestCase):
    def test_rows_fold_and_totals(self):
        html = bd.render_spend({"prev_month": "October", "projects": [proj("big-one", 80.0), proj("tiny", 0.2)]})
        self.assertEqual(html.count('class="hday sday"'), 1)
        self.assertIn("Also watched", html)
        self.assertIn("tiny", html)
        self.assertIn("$80.20", html)  # the headline counts every project, folded ones included
        self.assertEqual(html.count('class="sbar sfut"'), 12)

    def test_spike_makes_the_mascot_sweat_and_says_so(self):
        sp = {"projects": [proj("p", 50.0, spikes=[{"date": "2026-11-02", "usd": 40.0, "top": "x", "share": 0.8}])]}
        self.assertEqual(bd.spend_mood(sp), "sweat")
        self.assertIn("2 Nov jumped to $40.00, 80% of the month", bd.render_spend(sp))

    def test_unread_region_is_called_out_as_too_low(self):
        html = bd.render_spend({"projects": [proj("p", 0.1, problems=["US region not read: its job log needs 6.1 GB, over the 5 GB limit"])]})
        self.assertIn("so this figure is too low", html)
        self.assertIn('class="hday sday"', html)

    def test_empty_is_safe(self):
        self.assertIn("No project", bd.render_spend({"projects": []}))

    def test_spend_chapter_gets_its_css_and_tooltip(self):
        c = __import__("json").loads((pathlib.Path(__file__).resolve().parents[1] / "demo" / "content-2026-03-12.json").read_text())
        c["chapters"].insert(1, {"id": "spend", "nav": "Spend", "title": "Cloud spend", "spend": {"projects": [proj("p", 9.0)]}})
        html = bd.build(c)
        self.assertIn(".sspark{", html)
        self.assertIn('id="tab-spend"', html)


if __name__ == "__main__":
    unittest.main()
