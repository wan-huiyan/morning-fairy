"""Tests for the two drawn mascots added in 1.21.0: Nib (a wax crayon, drawn in crayon) and Pip (a little laptop whose face
glows on its screen). Each must survive every place a look passes through (read_look, build, the helper's POST /look) and
fill every mood and reaction symbol with its own drawing, so the scene's faces, hops and idle moments work for it.

Run from the repo root:  python3 -I -B -m unittest discover -s plugins/morning-fairy/skills/morning-fairy/digest/tests -v
"""
import json
import re
import sys
import unittest
from pathlib import Path

DIGEST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIGEST))

from test_fairy_look import FIXTURE  # noqa: E402
import build_digest as bd  # noqa: E402
import serve  # noqa: E402

NEW = {"nib": "nib-cr1", "pip": "pip-scr"}  # a def only that mascot's drawing uses


def page(mascot):
    return bd.build(json.loads(FIXTURE.read_text(encoding="utf-8")), look={"mascot": mascot})


def symbol(html, sid):
    m = re.search(rf'<symbol id="{sid}" [^>]*>(.*?)</symbol>', html, re.S)
    return m.group(1) if m else None


class DrawnMascots(unittest.TestCase):
    def test_every_mood_and_face_is_drawn_by_that_mascot(self):
        for kind, mark in NEW.items():
            html = page(kind)
            for m in bd.MOODS + bd.REACTIONS:
                body = symbol(html, bd._mood_id(m))
                self.assertIsNotNone(body, (kind, m))
                self.assertNotIn(bd.BODY_PATH, body, (kind, m))  # not the ticket
            self.assertIn(f'id="{mark}"', html, kind)  # its own defs travel with it

    def test_a_new_mascot_is_not_turned_back_into_the_ticket(self):
        for kind in NEW:
            self.assertEqual(bd.mascot_kind({"mascot": kind}, None), kind)
            self.assertEqual(bd.LOOK_CHOICES["mascot"].count(kind), 1)
            self.assertIn(kind, serve.LOOK_ONE["mascot"])  # or the helper refuses the switch

    def test_no_clawd_script_on_a_drawn_mascot_page(self):
        for kind in NEW:
            html = page(kind)
            self.assertNotIn("window.briefClawd = {", html, kind)
            self.assertNotIn(bd.CLAWD_BASE + "hello", html, kind)

    def test_only_nib_carries_the_line_boil(self):
        self.assertIn("@keyframes nibboil", page("nib"))
        for kind in ("ticket", "pip"):
            self.assertNotIn("@keyframes nibboil", page(kind))

    def test_the_look_switch_pictures_carry_their_own_defs(self):
        import base64
        for kind, mark in NEW.items():
            svg = base64.b64decode(bd.kind_icon_href(kind).split(",", 1)[1]).decode()
            self.assertIn(f'id="{mark}"', svg)
            self.assertNotIn("var(--", svg)  # a standalone picture has no page to read variables from


if __name__ == "__main__":
    unittest.main()
