"""Tests for who the mascot is (look.json "mascot": ticket, clawd or fanfan) in build_digest.py.

Run from the repo root:  python3 -I -B -m unittest discover -s plugins/morning-fairy/skills/morning-fairy/digest/tests -v
Pages are built in memory from the made-up demo morning; nothing is written anywhere.
"""
import json
import re
import sys
import unittest
from pathlib import Path

DIGEST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIGEST))  # -I leaves the script's folder off the path

from test_fairy_look import FIXTURE, FULL_LOOK  # noqa: E402  (also points the helper at a temp folder)
import build_digest as bd  # noqa: E402

MOOD_IDS = ("mascot", "mascot-sweat", "mascot-sleepy", "mascot-starry")


class MascotKinds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def page(self, look):
        return bd.build(json.loads(json.dumps(self.content)), look=look)

    def symbol(self, html, sid):
        m = re.search(rf'<symbol id="{sid}" [^>]*>(.*?)</symbol>', html)
        self.assertIsNotNone(m, sid)
        return m.group(1)

    # ---- the ticket ----
    def test_ticket_defs_are_unchanged(self):
        self.assertEqual(bd.mascot_defs(), bd.mascot_defs("ticket"))
        self.assertEqual(bd.mascot_defs("fanfan", None), bd.mascot_defs())  # no animal to draw: the ticket

    def test_ticket_look_has_no_mascot_script_and_no_clawd(self):
        from test_fairy_look import without_picker
        look = dict(FULL_LOOK, mascot="ticket")
        html = self.page(look)
        # the picker's Clawd card names the address too, inside a template that only loads when the picker opens
        self.assertNotIn(bd.CLAWD_BASE, without_picker(html, self.content["date"], look, [bd.ff_style(look), look["animal"]]))
        self.assertNotIn("clawd-credit", html)
        self.assertNotIn("tk-mascot", html)
        self.assertNotIn('"kind":', html)
        self.assertEqual(self.symbol(html, "mascot"), self.symbol(bd.mascot_defs(), "mascot"))

    def test_kind_falls_back_to_the_ticket(self):
        self.assertEqual(bd.mascot_kind(None, None), "ticket")
        self.assertEqual(bd.mascot_kind({"mascot": "fanfan"}, None), "ticket")
        self.assertEqual(bd.mascot_kind({"mascot": "dragon"}, None), "ticket")
        self.assertEqual(bd.mascot_kind({"mascot": "clawd"}, None), "clawd")

    # ---- Clawd ----
    def test_clawd_symbols_are_a_picture_with_the_ticket_kept_beside(self):
        html = self.page(FULL_LOOK)
        for sid in MOOD_IDS:
            s = self.symbol(html, sid)
            self.assertIn(f'href="{bd.CLAWD_BASE}idle.svg"', s)
            self.assertIn('image-rendering="pixelated"', s)
            self.assertIn("mbody", self.symbol(html, "tk-" + sid))  # the ticket, for when the picture cannot load
        self.assertIn('"kind": "clawd"', html)
        self.assertIn(bd.CLAWD_CREDIT, html)
        self.assertIn(bd.FF_CREDIT, html)  # the look's icons are fanfan too

    def test_clawd_is_only_ever_linked_never_copied(self):
        html = self.page(FULL_LOOK)
        self.assertNotRegex(html, r"<script[^>]*\ssrc=")  # no remote script at all
        for url in re.findall(r"https://cdn\.jsdelivr\.net/[^\s\"'<>]*", html):
            self.assertTrue(url.startswith(bd.CLAWD_BASE), url)  # pinned to the one commit
        self.assertNotIn("data:image/png", html)
        self.assertNotIn("data:image/apng", html)
        self.assertIn("deadline.apng", html)  # the stickers are named in the script's settings, as addresses

    def test_no_clawd_file_in_the_package(self):
        # Clawd is fan art under a non-commercial licence: it is loaded from the artist's repo, never shipped here
        names = [p for p in DIGEST.rglob("*") if p.is_file() and re.search(r"clawd|\.apng$", p.name, re.I)]
        self.assertEqual(names, [])
        self.assertTrue(bd.CLAWD_BASE.startswith("https://cdn.jsdelivr.net/gh/alwinecor/clawd-stickers@"))
        self.assertRegex(bd.CLAWD_BASE, r"@[0-9a-f]{40}/")  # pinned to one commit

    def test_clawd_keeps_the_ticket_tab_icon(self):
        look = dict(FULL_LOOK, places=["tabs"])
        self.assertIn(f'href="{bd.favicon_href(bd.page_mood(self.content))}" id="tab-icon"', self.page(look))

    def test_clawd_without_fanfan_places_credits_clawd_only(self):
        html = self.page(dict(FULL_LOOK, places=[]))
        self.assertIn(bd.CLAWD_CREDIT, html)
        self.assertNotIn(bd.FF_CREDIT, html)
        self.assertNotIn("root.FanfanMotion", html)  # the motion helper itself (the mascot script only names it)

    # ---- the fanfan animal ----
    def test_fanfan_symbols_draw_the_animal_in_the_page_ink(self):
        html = self.page(dict(FULL_LOOK, mascot="fanfan"))
        for sid, mark in zip(MOOD_IDS, ("bb-i-face-whole", "bb-i-alarm", None, "bb-i-trophy")):
            s = self.symbol(html, sid)
            self.assertIn('style="color:var(--w-ink)"', s)
            self.assertNotIn("<image", s)
            if mark:
                self.assertIn(mark, s)
        self.assertNotIn("bb-eye-a", self.symbol(html, "mascot-sleepy"))  # the still face with its eyes shut
        self.assertNotIn("tk-mascot", html)
        self.assertNotIn(bd.CLAWD_CREDIT, html)
        self.assertIn('"kind": "fanfan"', html)

    def test_fanfan_mascot_brings_its_drawings_and_moves_even_with_no_places(self):
        html = self.page(dict(FULL_LOOK, mascot="fanfan", places=[]))
        for noun in ("face-whole", "alarm", "trophy"):
            self.assertEqual(html.count(f'<template id="ff-{noun}">'), 1, noun)
        self.assertIn("root.FanfanMotion", html)
        self.assertIn(bd.FF_CREDIT, html)
        self.assertIn(".rider svg{transform:scale(.78)", html)
        self.assertNotIn("<template id=\"ff-sun\">", html)  # the places are still off

    def test_mascot_script_runs_before_the_scene(self):
        html = self.page(dict(FULL_LOOK, mascot="fanfan"))
        self.assertLess(html.index('"kind": "fanfan"'), html.index("var D = JSON.parse(document.getElementById('stage-data')"))

    # ---- the list headings ----
    def test_needs_and_resolved_headings_get_icons_with_tabs(self):
        html = self.page(dict(FULL_LOOK, mascot="ticket", places=["tabs"]))
        self.assertIn('<h3 class="group gh" id="needs"><span class="gi"><svg data-ff="bell" aria-hidden="true"></svg></span>Needs attention</h3>', html)
        self.assertIn('<h3 class="group gh" id="resolved"><span class="gi"><svg data-ff="trophy" aria-hidden="true"></svg></span>Resolved</h3>', html)
        plain = self.page(dict(FULL_LOOK, mascot="ticket", places=["quests"]))
        self.assertIn('<h3 class="group" id="needs">Needs attention</h3>', plain)

    def test_a_fanfan_tab_icon_alone_is_credited(self):
        html = self.page(dict(FULL_LOOK, mascot="ticket", places=["favicon"]))
        self.assertIn(bd.FF_CREDIT, html)
        self.assertNotIn("root.FanfanMotion", html)  # nothing moves in the page itself

    def test_no_credit_without_borrowed_art(self):
        html = self.page(dict(FULL_LOOK, mascot="ticket", places=[]))
        self.assertNotIn('class="foot credit"', html)
        self.assertNotIn(".who-pic", html)


if __name__ == "__main__":
    unittest.main()
