"""Tests for the Look panel since 1.18.0: one fixed fanfan style on every page, the Ticket | Clawd switch, and the list of
sources this morning's brief read, with a prompt to set up the rest. The "Build your fairy" picker is gone.

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


def content():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def with_new_tabs():
    """The demo morning plus the chapters added after the fanfan tabs were drawn: Hours, Cloud spend, Scout."""
    d = content()
    d["chapters"][1:1] = [
        {"id": "hours", "nav": "Hours", "title": "Hours", "lists": []},
        {"id": "spend", "nav": "Spend", "title": "Cloud spend", "lists": []},
        {"id": "scout", "nav": "Scout", "title": "Worth a look",
         "lists": [{"id": "scout", "tone": "scout", "title": "Worth a look", "items": []}]},
    ]
    return d


def look_panel(html):
    m = re.search(r'<div class="look-panel" id="look-panel".*?\n</div>', html, re.S)
    assert m, "no Look panel"
    return m.group(0)


class OneFanfanStyle(unittest.TestCase):
    def test_every_tab_draws_a_fanfan_icon_with_or_without_a_look(self):
        for look in (None, FULL_LOOK):
            html = bd.build(with_new_tabs(), look=look)
            tabs = re.findall(r'<button type="button" role="tab" class="tab" id="tab-([a-z]+)"[^>]*>(.*?)</button>', html)
            self.assertGreaterEqual(len(tabs), 6)
            for key, inner in tabs:
                self.assertIn("data-ff=", inner, key)

    def test_the_style_is_fixed_whatever_the_look_asks_for(self):
        a = bd.build(content(), look=dict(FULL_LOOK, animal="cat", line="thin", eyes="dots", mascot="ticket"))
        b = bd.build(content(), look=dict(FULL_LOOK, animal="bunny", line="thick", eyes="shiny", mascot="ticket"))
        self.assertEqual(a, b)
        self.assertEqual(a, bd.build(content(), look=None))

    def test_the_fanfan_credit_is_on_every_page(self):
        self.assertIn(bd.FF_CREDIT, bd.build(content(), look=None))


class NoPicker(unittest.TestCase):
    def test_build_your_fairy_is_gone(self):
        for look in (None, FULL_LOOK):
            html = bd.build(content(), look=look)
            self.assertNotIn("Build your fairy", html)
            self.assertNotIn("Build your own fairy", html)
            self.assertNotIn("fairy-tpl", html)
            self.assertNotIn("fairy-open", html)
            self.assertNotIn("briefFairy", html)


class MascotSwitch(unittest.TestCase):
    def test_ticket_and_clawd_sit_first_in_the_look_panel(self):
        panel = look_panel(bd.build(content(), look=None))
        self.assertLess(panel.index('class="look-mascot"'), panel.index('class="look-worlds"'))
        self.assertIn('data-mascot="ticket"', panel)
        self.assertIn('data-mascot="clawd"', panel)

    def test_the_current_mascot_is_pressed(self):
        for kind in ("ticket", "nib", "pip", "clawd"):
            panel = look_panel(bd.build(content(), look=dict(FULL_LOOK, mascot=kind)))
            self.assertRegex(panel, rf'data-mascot="{kind}" aria-pressed="true"')

    def test_saving_goes_through_the_helper_with_a_whole_look(self):
        html = bd.build(content(), look=None)
        self.assertIn("fetch('/look'", html)
        for k, v in bd.FF_LOOK.items():
            self.assertIn(f'"{k}": "{v}"', html)

    def test_no_clawd_button_when_clawd_is_not_offered(self):
        saved = bd.OFFER_CLAWD
        bd.OFFER_CLAWD = False
        try:
            html = bd.build(content(), look=FULL_LOOK)
            self.assertNotIn('data-mascot="clawd"', look_panel(html))
            self.assertIn('data-mascot="nib"', look_panel(html))  # the drawn mascots are always offered
            self.assertNotIn("jsdelivr", html)
        finally:
            bd.OFFER_CLAWD = saved

    def test_a_ticket_page_fetches_no_clawd_until_look_opens(self):
        html = bd.build(content(), look=dict(FULL_LOOK, mascot="ticket"))
        # the Look panel's Clawd button names the sticker as data-src only: nothing is fetched until Look opens
        self.assertEqual(html.count(bd.CLAWD_BASE), 1)
        self.assertIn(f'data-src="{bd.CLAWD_BASE}{bd.CLAWD_IDLE}"', html)
        self.assertNotIn(f'src="{bd.CLAWD_BASE}', html.replace(f'data-src="{bd.CLAWD_BASE}', ""))

    def test_the_mascots_are_pictures_not_words(self):
        panel = look_panel(bd.build(content(), look=None))
        picks = re.findall(r'<button type="button" class="mpick" data-mascot="([a-z]+)"[^>]*>(.*?)</button>', panel)
        self.assertEqual([k for k, _ in picks], ["ticket", "nib", "pip", "clawd"])
        for k, inner in picks:
            self.assertTrue(inner.startswith("<img "), k)
            self.assertEqual(re.sub(r"<[^>]+>", "", inner).strip(), "", k)  # no visible words
        self.assertRegex(panel, r'data-mascot="ticket"[^>]*aria-label="The ticket"')


class Layouts(unittest.TestCase):
    """1.19.0: Map is retired, the top bar's layout switch is gone (Look has it), and the scene opens on the scene alone."""

    def test_no_map_and_one_layout_switch(self):
        html = bd.build(content(), look=None)
        self.assertNotIn('data-layout="map"', html)
        self.assertNotIn("lvxp", html)
        self.assertNotIn('class="lvl', html)
        self.assertNotIn("mapLayout", html)
        self.assertEqual(html.count('aria-label="Layout"'), 1)  # only the Look panel's
        self.assertIn('<button type="button" data-layout="scene">Scene</button></div>', look_panel(html))

    def test_a_saved_map_opens_the_scene(self):
        html = bd.build(content(), look=None)
        self.assertIn("return v === 'map' ? 'scene' :", html)

    def test_switching_to_the_scene_opens_no_sheet(self):
        html = bd.build(content(), look=None)
        self.assertNotIn("openSheet(keep", html)


class Sources(unittest.TestCase):
    def test_the_demo_marquee_maps_onto_the_known_sources(self):
        got = bd.sources_read(content())
        self.assertEqual({k for k, on in got if on}, {"calendar", "email", "chat", "jira", "github"})
        self.assertEqual([k for k, _ in got], [k for k, *_ in bd.SOURCES])  # every known source, in the README's order

    def test_aliases_from_a_real_morning(self):
        d = content()
        d["sources_marquee"] = ["Jira", "Gmail", "Calendar", "Slack", "GitHub", "Tempo", "Session logs", "Google Cloud"]
        on = {k for k, v in bd.sources_read(d) if v}
        self.assertEqual(on, {"jira", "email", "calendar", "chat", "github", "tempo", "logs", "cloud"})

    def test_the_sources_chapter_rows_count_too(self):
        d = content()
        d["sources_marquee"] = []
        d["chapters"].append({"id": "sources", "title": "What was read", "rows": [{"title": "Meetings:", "html": "x"}]})
        self.assertIn(("notes", True), bd.sources_read(d))

    def test_scout_finds_mean_the_web_was_read(self):
        d = with_new_tabs()
        self.assertIn(("web", False), bd.sources_read(d))  # an empty Scout list: not read
        d["chapters"][3]["lists"][0]["items"] = [{"title": "x", "url": "https://example.com", "text": "y"}]
        self.assertIn(("web", True), bd.sources_read(d))

    def test_the_panel_lists_them_and_offers_the_setup_prompt(self):
        panel = look_panel(bd.build(content(), look=None))
        self.assertIn('class="look-sources"', panel)
        self.assertIn("Read this morning", panel)
        self.assertIn("Not read this morning", panel)
        self.assertRegex(panel, r'data-src="tempo"[^>]*data-on="0"')
        self.assertRegex(panel, r'data-src="jira"[^>]*data-on="1"')
        self.assertIn('id="sources-copy"', panel)
        self.assertNotIn("Not connected", panel)  # the page only knows what was read, never why not

    def test_the_prompt_starts_the_setup_and_asks_only_to_check(self):
        p = bd.sources_prompt(content())
        self.assertTrue(p.startswith("set up morning fairy"), p)
        for name in ("Tempo", "Google Cloud", "Meeting notes"):
            self.assertIn(name, p)
        self.assertNotIn("Calendar,", p)  # it was read
        self.assertIn("change nothing", p.lower())

    def test_nothing_left_to_set_up(self):
        d = content()
        d["sources_marquee"] = [label for _, label, *_ in bd.SOURCES]
        self.assertIsNone(bd.sources_prompt(d))
        self.assertNotIn('id="sources-copy"', look_panel(bd.build(d, look=None)))


if __name__ == "__main__":
    unittest.main()
