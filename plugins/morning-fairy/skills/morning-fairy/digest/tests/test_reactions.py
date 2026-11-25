"""Tests for the mascot's reactions (1.20.0): five faces the ticket pulls for a moment, the logo as a button, a button over
the scene's mascot, Clawd's reaction stickers, and the idle moments' limits.

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

from test_fairy_look import FIXTURE  # noqa: E402  (also points the helper at a temp folder)
import build_digest as bd  # noqa: E402


def page(mascot="ticket"):
    return bd.build(json.loads(FIXTURE.read_text(encoding="utf-8")), look={"mascot": mascot})


class Faces(unittest.TestCase):
    def test_a_ticket_page_carries_every_reaction_face(self):
        html = page()
        for r in bd.REACTIONS:
            self.assertEqual(html.count(f'<symbol id="mascot-{r}" '), 1, r)

    def test_the_faces_are_never_moods(self):
        self.assertFalse(set(bd.REACTIONS) & set(bd.MOODS))
        self.assertFalse(set(bd.REACTIONS) & set(bd.MOOD_LABELS))

    def test_each_face_is_its_own_drawing(self):
        drawn = {r: bd.mascot_parts(r) for r in bd.REACTIONS}
        self.assertEqual(len(set(drawn.values())), len(bd.REACTIONS))
        self.assertNotIn(bd.mascot_parts("calm"), drawn.values())

    def test_a_clawd_page_has_no_faces_it_would_not_use(self):
        html = page("clawd")
        for r in bd.REACTIONS:
            self.assertNotIn(f'id="mascot-{r}"', html)


class WhereYouPokeIt(unittest.TestCase):
    def test_the_logo_is_a_labelled_button(self):
        self.assertRegex(page(), r'<button type="button" class="pet-logo" id="pet-logo" aria-label="Say hi to the mascot"><svg class="mascot logo"')

    def test_the_scene_button_is_pointer_only(self):
        # the keyboard way in is the logo; the scene's button is redrawn over a moving mascot
        self.assertIn('<button type="button" class="petme" id="petme" tabindex="-1" aria-hidden="true"></button>', page())

    def test_the_scene_button_follows_the_mascot(self):
        html = page()
        self.assertIn("    placePet();\n  }\n  function placePet(){", html)


class Reacting(unittest.TestCase):
    def test_a_reaction_beats_the_mood_while_it_lasts(self):
        self.assertIn("var m = st.react || (st.night ? 'sleepy'", page())

    def test_reduced_motion_keeps_the_face_and_drops_the_motion(self):
        html = page()
        self.assertIn("if (!el || rm() || playing(el)) return;  // never restart a hop in mid-air", html)
        self.assertIn("function burst(el, r){\n    if (!el || rm()) return;", html)
        self.assertIn("@media (prefers-reduced-motion:reduce){.pet-logo .mascot{transition:none}}", html)

    def test_idle_moments_are_limited(self):
        html = page()
        m = re.search(r"\(function idle\(\)\{(.*?)\}\)\(\);", html, re.S)
        self.assertIsNotNone(m)
        body = m.group(1)
        for need in ("document.visibilityState === 'visible'", "!rm()", "!st.night", "idleN < 2", "Date.now() - lastAct > 15000"):
            self.assertIn(need, body)

    def test_clawd_stickers_for_reactions_have_lengths(self):
        for k in ("hello", "right", "duck", "coffee", "clear", "dizzy"):
            file, ms = bd.CLAWD_STICKERS[k]
            self.assertTrue(file.endswith(".apng"), k)
            self.assertGreater(ms, 3000, k)
        html = page("clawd")
        self.assertIn("window.briefClawd = {on:", html)

    def test_the_caterpillar_world_is_still_built(self):
        self.assertTrue(bd.CATERPILLAR)
        html = page()
        self.assertIn('value="caterpillar"', html)


if __name__ == "__main__":
    unittest.main()
