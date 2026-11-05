"""Tests for "Build your own fairy", the look picker inside the brief (build_digest.fairy_picker and OFFER_CLAWD).

Run from the repo root:  python3 -I -B -m unittest discover -s plugins/morning-fairy/skills/morning-fairy/digest/tests -v
Pages are built in memory from the made-up demo morning; nothing is written anywhere. The browser side (opening once,
the parachute waiting, Save through the helper) is not checked here.
"""
import json
import re
import sys
import unittest
from pathlib import Path

DIGEST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIGEST))  # -I leaves the script's folder off the path

from test_fairy_look import FIXTURE, FULL_LOOK, without_picker  # noqa: E402  (also points the helper at a temp folder)
import build_digest as bd  # noqa: E402


def cfg_of(html):
    """The settings the picker's script was built with."""
    m = re.search(r"var C = (\{.*?\}), NS = ", html)
    return json.loads(m.group(1).replace("<\\/", "</"))


def template(html):
    m = re.search(r'<template id="fairy-tpl">(.*?</dialog>)</template>', html, re.S)  # it holds templates of its own
    return m.group(1)


class Picker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def page(self, look):
        return bd.build(json.loads(json.dumps(self.content)), look=look)

    def test_one_template_one_script_one_row(self):
        for look in (None, FULL_LOOK):
            html = self.page(look)
            self.assertEqual(html.count('<template id="fairy-tpl">'), 1)
            self.assertEqual(html.count("window.briefFairy = "), 1)
            self.assertEqual(html.count('id="fairy-open"'), 1)
            self.assertLess(html.index('id="fairy-open"'), html.index('<main class="main">'))  # inside the Look panel

    def test_its_boxes_are_never_page_boxes(self):
        # every check box and radio of the picker sits in the template (the copy check counts the page's own boxes)
        html = self.page(None)
        outside = html.replace(template(html), "")
        self.assertEqual(len(re.findall(r'type="checkbox"', template(html))), len(bd.FAIRY_MOVES))  # moves only: places are no longer chosen
        self.assertNotIn('name="places"', template(html))
        self.assertNotRegex(outside, r'<input[^>]*name="(places|moves|mascot|animal|line|eyes)"')

    def test_the_sheet_says_what_it_should(self):
        t = template(self.page(None))
        for text in ("Build your own fairy", "Save my fairy", "Not now", "The ticket", "Clawd", "Little animal icons",
                     "They draw the little icons across the page: tabs, quests, the Done box and the browser tab.",
                     "Moves", "Saving goes through the Morning Brief app. If the page doesn't open, click Morning Brief in your Dock (or run launch.sh) first.",
                     "Its own trick", "Lop bunny"):
            self.assertIn(text, t)
        self.assertEqual(re.findall(r'name="mascot" value="(\w+)"', t), ["ticket", "clawd"])  # the animal is no mascot any more
        for gone in ("A little animal", "The animal you pick below", "Pick the animal as your mascot", "Where little animals go",
                     "The browser-tab icon", "Top-bar buttons", "Open the brief from the Morning Brief app"):  # places are not a choice any more
            self.assertNotIn(gone, t)
        self.assertIn('aria-labelledby="fairy-title"', t)
        self.assertIn('<h2 id="fairy-title">', t)
        self.assertNotRegex(t, r"\son[a-z]+=")  # no inline handlers
        self.assertNotIn("<script", t)

    def test_starts_from_the_defaults_or_the_current_look(self):
        c = cfg_of(self.page(None))
        self.assertIsNone(c["look"])
        self.assertEqual(c["def"], bd.LOOK_DEFAULT)
        self.assertEqual(c["def"]["places"], list(bd.FF_PLACES))  # all six, never chosen in the picker
        self.assertIsNone(c["emb"])
        c = cfg_of(self.page(FULL_LOOK))
        self.assertEqual(c["look"], FULL_LOOK)
        self.assertEqual(c["emb"], ["thick-highlight", "cat"])  # the preview reuses the drawings the page carries
        self.assertEqual(c["date"], self.content["date"])

    def test_carries_each_animals_face_for_when_there_is_no_helper(self):
        t = template(self.page(None))
        faces = re.findall(r'<template class="face" data-a="([a-z]+)">(<svg.*?</svg>)</template>', t, re.S)
        self.assertEqual([a for a, _ in faces], [a for a, _ in bd.FAIRY_ANIMALS])
        for a, svg in faces:
            self.assertEqual(svg, bd._ff_read(bd.FF_DIR / bd.FAIRY_FACE_STYLE / f"{a}-face-whole.svg"))
        self.assertLess(sum(len(s) for _, s in faces), 12000)  # four small drawings, not a style set
        self.assertEqual(cfg_of(self.page(None))["faceStyle"], bd.FAIRY_FACE_STYLE)

    def test_preview_check_is_the_builders(self):
        safe = cfg_of(self.page(None))["safe"]
        self.assertEqual((safe["tags"], safe["attrs"], safe["d"], safe["v"]),
                         (list(bd.FF_TAGS), list(bd.FF_ATTRS), bd.FF_D_RE, bd.FF_VALUE_RE))

    def test_preview_names_match_the_helpers_whitelist(self):
        import serve
        c = cfg_of(self.page(None))
        self.assertEqual(set(c["styles"]), set(serve.FF_STYLES))
        self.assertEqual(set(c["animals"]), set(serve.FF_ANIMALS))
        self.assertTrue(set(c["nouns"]) <= set(serve.FF_NOUNS))

    def test_saves_only_where_the_done_button_does(self):
        html = self.page(None)
        rule = r"/^http:\/\/(127\.0\.0\.1|localhost):8765$/.test(location.origin)"
        self.assertEqual(html.count(rule), 2)  # the Done button's and the picker's
        self.assertIn("fetch('/look'", html)

    def test_parachute_waits_for_it(self):
        html = self.page(None)
        i = html.index(bd.HELLO_WAIT)
        self.assertTrue(html[i + len(bd.HELLO_WAIT):].startswith("set('brief-hello-' + today, '1');"))

    def test_the_animal_reaches_the_row_but_not_the_top_bar(self):
        html = self.page(FULL_LOOK)
        self.assertRegex(html, r'id="fairy-open"[^>]*><span><svg data-ff="face-whole" aria-hidden="true"></svg>Build your fairy…</span>')
        # the top bar's Look and sound buttons keep their own drawings (palette, speaker), look or no look
        self.assertRegex(html, r'id="look"[^>]*>' + re.escape(bd.ICONS["palette"]) + "</button>")
        self.assertIn(json.dumps(bd.ICONS["sound"]), html)
        self.assertIn(json.dumps(bd.ICONS["mute"]), html)
        for noun in ("palette", "music"):
            self.assertNotIn(f'data-ff="{noun}"', html)


class FromAFile(unittest.TestCase):
    """The sheet on a file page: Save opens the live brief with the choices in the address (#fairy=...)."""

    @classmethod
    def setUpClass(cls):
        cls.content = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.html = bd.build(json.loads(json.dumps(cls.content)))

    def run_js(self, hash_value):
        """parseHash from the page's own script, run in node against the page's own allowed lists."""
        import shutil
        import subprocess
        if not shutil.which("node"):
            self.skipTest("needs node")
        m = re.search(r"/\*hash:start\*/(.*?)/\*hash:end\*/", self.html, re.S)
        code = ("var C = " + json.dumps({"allowed": cfg_of(self.html)["allowed"]}) + ";" + m.group(1)
                + "console.log(JSON.stringify(parseHash(" + json.dumps(hash_value) + ")));")
        out = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=20)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_the_allowed_lists_are_the_builders(self):
        a = cfg_of(self.html)["allowed"]
        self.assertEqual(a["mascot"], ["ticket", "clawd"])
        self.assertEqual(a["animal"], ["cat", "dog", "lop", "bunny"])
        self.assertEqual((a["line"], a["eyes"], a["moves"]), (["thin", "thick"], ["dots", "shiny"], list(bd.FF_MOVES)))

    def test_a_good_hash_is_read_whole(self):
        self.assertEqual(self.run_js("#fairy=clawd.dog.thick.shiny.wake-sleep-trick"),
                         {"mascot": "clawd", "animal": "dog", "line": "thick", "eyes": "shiny", "moves": ["wake", "sleep", "trick"]})
        self.assertEqual(self.run_js("#fairy=ticket.cat.thin.dots.")["moves"], [])  # no moves picked: none

    def test_bad_values_are_ignored_one_by_one(self):
        self.assertEqual(self.run_js("#fairy=fanfan.fox.thick.dots.wake-fly-wake"),
                         {"line": "thick", "eyes": "dots", "moves": ["wake"]})  # no fanfan mascot, no fox, no fly, no repeat
        self.assertEqual(self.run_js("#fairy=clawd.cat"), {"mascot": "clawd", "animal": "cat"})  # missing parts stay as they are

    def test_anything_else_in_the_hash_is_refused(self):
        for h in ("", "#", "#other=1", "#fairy=ticket.cat.thin.dots.wake&x=1", "#fairy=<b>", "#fairy=ticket.cat.thin.dots.wake/../x", "#fairy=a b"):
            self.assertIsNone(self.run_js(h), h)

    def test_the_file_page_save_goes_to_the_helper_and_the_helper_is_not_loosened(self):
        self.assertIn("location.assign('http://127.0.0.1:8765/brief/' + name + '#' + hashOf(choice()))", self.html)
        self.assertIn("Open the live brief to save", self.html)
        self.assertIn("history.replaceState(null, ''", self.html)  # the address is cleared once the choices are read
        self.assertIn("var sent = SERVED &&", self.html)  # only a page the helper serves acts on the hash


class OfferClawd(unittest.TestCase):
    """OFFER_CLAWD: this package offers Clawd (loaded from the artist's repo, with credit); False removes every trace."""

    @classmethod
    def setUpClass(cls):
        cls.content = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def page(self, look):
        return bd.build(json.loads(json.dumps(self.content)), look=look)

    def test_this_package_offers_clawd(self):
        self.assertIs(bd.OFFER_CLAWD, True)

    def test_on_offers_the_card_and_credit(self):
        t = template(self.page(None))
        self.assertIn('value="clawd"', t)
        self.assertIn(bd.CLAWD_BASE + bd.CLAWD_IDLE, t)
        self.assertIn("fan art, non-commercial use, loads from the artist's own page", t.replace("\\'", "'").lower())
        self.assertIn("Clawd stickers: fan art by alwinecor (CC BY-NC-SA 4.0). Clawd belongs to Anthropic; unofficial.", t)

    def test_off_has_no_card_no_clawd_and_no_cdn(self):
        saved = bd.OFFER_CLAWD
        bd.OFFER_CLAWD = False
        try:
            for look in (None, FULL_LOOK, dict(FULL_LOOK, places=[])):
                html = self.page(look)
                self.assertNotIn("jsdelivr", html)
                self.assertNotIn("clawd-stickers", html)
                self.assertNotIn('value="clawd"', html)
                self.assertNotIn("alwinecor", html)
            html = self.page(FULL_LOOK)  # a look.json that asks for Clawd gets the ticket, and the picker starts from it
            self.assertEqual(cfg_of(html)["look"]["mascot"], "ticket")
            self.assertEqual(bd.mascot_kind(FULL_LOOK, None), "ticket")
            self.assertEqual(html, self.page(dict(FULL_LOOK, mascot="ticket")))
        finally:
            bd.OFFER_CLAWD = saved
        self.assertEqual(bd.mascot_kind(FULL_LOOK, None), "clawd")


if __name__ == "__main__":
    unittest.main()
