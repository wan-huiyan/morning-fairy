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
        self.assertEqual(len(re.findall(r'type="checkbox"', template(html))), len(bd.FAIRY_PLACES) + len(bd.FAIRY_MOVES))
        self.assertNotRegex(outside, r'<input[^>]*name="(places|moves|mascot|animal|line|eyes)"')

    def test_the_sheet_says_what_it_should(self):
        t = template(self.page(None))
        for text in ("Build your own fairy", "Save my fairy", "Not now", "A little animal", "The ticket", "Where little animals go",
                     "Moves", "Open the brief from the Morning Brief app in your Dock to save your fairy.", "The browser-tab icon",
                     "Its own trick", "Lop bunny"):
            self.assertIn(text, t)
        self.assertIn('aria-labelledby="fairy-title"', t)
        self.assertIn('<h2 id="fairy-title">', t)
        self.assertNotRegex(t, r"\son[a-z]+=")  # no inline handlers
        self.assertNotIn("<script", t)

    def test_starts_from_the_defaults_or_the_current_look(self):
        c = cfg_of(self.page(None))
        self.assertIsNone(c["look"])
        self.assertEqual(c["def"], bd.LOOK_DEFAULT)
        self.assertNotIn("favicon", c["def"]["places"])  # the browser-tab icon starts unticked
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

    def test_toolbar_icons_reach_the_row(self):
        html = self.page(FULL_LOOK)
        self.assertRegex(html, r'id="fairy-open"[^>]*><span><svg data-ff="face-whole" aria-hidden="true"></svg>Build your fairy…</span>')
        html = self.page(dict(FULL_LOOK, places=["tabs"]))
        self.assertIn("<span>Build your fairy…</span>", html)


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
