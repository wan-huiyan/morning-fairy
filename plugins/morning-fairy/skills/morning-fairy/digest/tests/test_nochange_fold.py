"""No change folds into the Jira tab on every morning, quiet ones included."""
import importlib.util, json, pathlib, re, unittest

D = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bd", D / "build_digest.py")
bd = importlib.util.module_from_spec(spec); spec.loader.exec_module(bd)


def build(quiet):
    c = json.loads((D / "demo" / "content-2026-03-12.json").read_text(encoding="utf-8"))
    if quiet:
        for ch in c["chapters"]:
            ch["groups"] = [dict(g, cards=[]) for g in ch.get("groups", [])]
    return bd.build(c)


def tabs(html):
    return set(re.findall(r'role="tab" class="tab" id="tab-([a-z]+)"', html))



class NoChangeFold(unittest.TestCase):
    def test_quiet_morning_has_no_nochange_tab_and_folds_into_jira(self):
        html = build(quiet=True)
        self.assertTrue("nochange" not in tabs(html) and "todo" in tabs(html))
        jira = html.split('id="sec-todo"', 1)[1].split('id="sec-', 1)[0]
        self.assertTrue('<details class="nc-fold" id="nochange">' in jira and "Already up to date in Jira (2)" in jira)

    def test_busy_morning_still_folds_and_stays_closed(self):
        html = build(quiet=False)
        self.assertTrue("nochange" not in tabs(html))
        self.assertTrue('<details class="nc-fold" id="nochange">' in html and '<details class="nc-fold" id="nochange" open' not in html)


if __name__ == "__main__":
    unittest.main()
