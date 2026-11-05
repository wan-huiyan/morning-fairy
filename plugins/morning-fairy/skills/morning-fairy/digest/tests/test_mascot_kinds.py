"""Tests for who the mascot is (look.json "mascot": ticket or clawd; an older "fanfan" reads as the ticket) in build_digest.py.

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
        self.assertEqual(bd.mascot_defs("fanfan"), bd.mascot_defs())  # not a mascot any more: the ticket

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

    def test_clawd_page_has_the_animal_on_the_tab_icon(self):
        # all six places are on with any look, the browser-tab icon included, so Clawd's page carries the animal's face there
        self.assertNotIn(f'href="{bd.favicon_href(bd.page_mood(self.content))}" id="tab-icon"', self.page(FULL_LOOK))

    # ---- an older look.json that still says "fanfan" ----
    def test_an_old_fanfan_mascot_is_the_ticket_with_the_animal_icons(self):
        old = self.page(dict(FULL_LOOK, mascot="fanfan"))
        new = self.page(dict(FULL_LOOK, mascot="ticket"))
        self.assertEqual(old, new)
        self.assertNotIn('"kind"', old)  # no mascot script
        self.assertEqual(old.count('<template id="ff-sun">'), 1)  # the icons are still the animal's
        self.assertIn(bd.FF_CREDIT, old)

    def test_the_fanfan_mascot_code_is_gone(self):
        html = self.page(dict(FULL_LOOK, mascot="clawd"))
        for gone in ("fanMood", "fanRest", "fanTo", "ff-who", "fbox"):
            self.assertNotIn(gone, html)

    # ---- the list headings ----
    def test_needs_and_resolved_headings_get_icons_with_a_look(self):
        html = self.page(dict(FULL_LOOK, mascot="ticket"))
        self.assertIn('<h3 class="group gh" id="needs"><span class="gi"><svg data-ff="bell" aria-hidden="true"></svg></span>Needs attention</h3>', html)
        self.assertIn('<h3 class="group gh" id="resolved"><span class="gi"><svg data-ff="trophy" aria-hidden="true"></svg></span>Resolved</h3>', html)
        plain = self.page(None)  # no look: the headings keep their plain text
        self.assertIn('<h3 class="group" id="needs">Needs attention</h3>', plain)

    def test_no_credit_without_borrowed_art(self):
        html = self.page(None)  # no look: no animal, no sticker
        self.assertNotIn('class="foot credit"', html)
        self.assertNotIn(".who-pic", html)


if __name__ == "__main__":
    unittest.main()
