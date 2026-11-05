"""Tests for the look (look.json, fanfan icons) in build_digest.py and the helper's /fanfan and /look routes in serve.py.

Run from the repo root:  python3 -I -B -m unittest discover -s plugins/morning-fairy/skills/morning-fairy/digest/tests -v
(npm test runs it too.) Pages are built from the made-up demo morning. Everything is written under temp folders: before
serve.py is imported, its data and briefs folders are pointed at a temp folder, so your own ~/.morning-fairy and Desktop
are never read or written; the helper is started on a free port, and the Host and Origin headers name 8765 by hand.
"""
import atexit
import http.client
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import unittest
from datetime import datetime
from pathlib import Path

DIGEST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIGEST))  # -I leaves the script's folder off the path

# serve.py reads where its data lives when it is imported: never let that be the real home folder
_SANDBOX = Path(tempfile.mkdtemp(prefix="mf-test-"))
atexit.register(shutil.rmtree, _SANDBOX, True)
os.environ["BRIEF_DIGEST_DIR"] = str(_SANDBOX / "home")
os.environ["BRIEF_DESKTOP_DIR"] = str(_SANDBOX / "Desktop")

import build_digest as bd  # noqa: E402
import serve  # noqa: E402

FIXTURE = DIGEST / "demo" / "content-2026-03-12.json"  # made-up data, shipped with the package


def without_picker(html, date, look=None, emb=None):
    """The page with the "Build your own fairy" picker taken out again: its template, its script, its Look-panel row and
    the line that makes the good-morning parachute wait for it. Each must be there exactly once."""
    tpl, js = bd.fairy_picker(look, date, emb)
    for part in (tpl + "\n", js, bd.HELLO_WAIT):
        assert html.count(part) == 1, part[:80]
        html = html.replace(part, "")
    # the Look-panel row (with the top-bar icons on, its label carries a little face)
    html, n = re.subn(r'  <button type="button" class="look-switch fairy-open" id="fairy-open"[^\n]*?</button>\n', "", html)
    assert n == 1
    return html


# every choice switched on: Clawd, the cat in thick lines with shiny eyes, all six places, all five moves
FULL_LOOK = {"mascot": "clawd", "animal": "cat", "line": "thick", "eyes": "shiny",
             "places": ["tabs", "quests", "toolbar", "done", "empty", "favicon"], "moves": ["wake", "sleep", "bounce", "blush", "trick"]}


class SandboxIsInPlace(unittest.TestCase):
    def test_the_helper_never_points_at_the_real_home(self):
        self.assertTrue(str(serve.DIGEST).startswith(str(_SANDBOX)), serve.DIGEST)
        self.assertTrue(str(serve.DESKTOP).startswith(str(_SANDBOX)), serve.DESKTOP)


class ReadLook(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, text):
        p = self.tmp / "look.json"
        p.write_text(text, encoding="utf-8")
        return p

    def test_missing_file_is_no_look(self):
        self.assertIsNone(bd.read_look(self.tmp / "nope.json"))
        self.assertIsNone(bd.read_look(None))

    def test_not_json_or_not_an_object_is_no_look(self):
        self.assertIsNone(bd.read_look(self.write("{not json")))
        self.assertIsNone(bd.read_look(self.write("[1, 2]")))
        self.assertIsNone(bd.read_look(self.write('"cat"')))

    def test_good_look_is_kept(self):
        self.assertEqual(bd.read_look(self.write(json.dumps(FULL_LOOK))), FULL_LOOK)

    def test_bad_values_fall_back_one_by_one(self):
        look = bd.read_look(self.write(json.dumps({"mascot": "dragon", "animal": "dog", "line": 3, "eyes": "shiny",
                                                     "places": ["tabs", "../etc", 7, "favicon"], "moves": "all", "extra": 1})))
        self.assertEqual(look["mascot"], "ticket")
        self.assertEqual(look["animal"], "dog")
        self.assertEqual(look["line"], "thin")
        self.assertEqual(look["eyes"], "shiny")
        self.assertEqual(look["places"], list(bd.FF_PLACES))  # whatever an older file lists, all six
        self.assertEqual(look["moves"], list(bd.FF_MOVES))  # not a list: the default
        self.assertNotIn("extra", look)

    def test_older_look_files_with_fewer_places_read_as_all_six(self):
        for body in ({"mascot": "fanfan", "animal": "cat", "line": "thin", "eyes": "dots", "moves": ["wake"]},
                     {"mascot": "fanfan", "animal": "cat", "line": "thin", "eyes": "dots", "places": ["tabs"], "moves": ["wake"]},
                     {"mascot": "fanfan", "animal": "cat", "line": "thin", "eyes": "dots", "places": [], "moves": ["wake"]}):
            look = bd.read_look(self.write(json.dumps(body)))
            self.assertEqual(look["places"], list(bd.FF_PLACES))
            self.assertEqual(look["moves"], ["wake"])

    def test_empty_object_gives_defaults(self):
        self.assertEqual(bd.read_look(self.write("{}")), bd.LOOK_DEFAULT)

    def test_style_folder(self):
        self.assertEqual(bd.ff_style({"line": "thick", "eyes": "shiny"}), "thick-highlight")
        self.assertEqual(bd.ff_style({"line": "thin", "eyes": "dots"}), "thin")


class BuildWithLook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def page(self, look):
        return bd.build(json.loads(json.dumps(self.content)), look=look)

    def test_no_look_is_the_old_page_plus_a_flag(self):
        html = without_picker(self.page(None), self.content["date"])  # the picker is in every page; see test_fairy_picker
        self.assertIn('<body data-look-set="0">', html)
        self.assertNotIn("data-ff=", html.split("<script>")[0])
        self.assertNotIn("fanfan", html)

    def test_look_embeds_each_used_drawing_once(self):
        html = self.page(FULL_LOOK)
        self.assertIn('<body data-look-set="1">', html)
        self.assertIn("MIT · by @唐幡", html)  # fanfan's own header kept
        for noun in ("sun", "ticket", "bell", "trophy", "news", "moon", "wand", "robot"):
            self.assertEqual(html.count(f'<template id="ff-{noun}">'), 1, noun)
        # every placeholder in the page has its drawing, and every drawing carried is used
        used = set(re.findall(r'<svg[^>]* data-ff="([a-z-]+)" aria-hidden="true">', html))
        carried = set(re.findall(r'<template id="ff-([a-z-]+)"><svg', html))
        self.assertLessEqual(carried, set(bd.FF_NOUNS))
        self.assertTrue(used)
        self.assertLessEqual(used, carried)
        tpl = "".join(re.findall(r'<template id="ff-[a-z-]+">.*?</template>', html))
        self.assertTrue(tpl)
        self.assertNotRegex(tpl, r"bb-(dog|lop|bunny)\b")  # only the chosen animal (the motion css names them all)

    def test_all_six_places_are_on_whatever_the_look_lists(self):
        full = self.page(FULL_LOOK)
        for places in ([], ["tabs"], ["favicon"]):
            self.assertEqual(self.page(dict(FULL_LOOK, places=places)), full, places)
        no_key = {k: v for k, v in FULL_LOOK.items() if k != "places"}
        page = self.page(no_key)  # a missing "places" key is valid: same drawings, and the picker starts from all six
        self.assertEqual(re.findall(r'<template id="ff-[a-z-]+">', page), re.findall(r'<template id="ff-[a-z-]+">', full))
        self.assertIn('"places": ["tabs", "quests", "toolbar", "done", "empty", "favicon"]', page)
        self.assertEqual(sorted(bd.Fan(FULL_LOOK).places), sorted(bd.FF_PLACES))

    def test_icons_are_decoration(self):
        # every placeholder is hidden from screen readers (what the copy button copies is checked in a browser, not here)
        html = self.page(FULL_LOOK)
        tags = re.findall(r'<svg[^>]* data-ff="(?:' + "|".join(bd.FF_NOUNS) + r')"[^>]*>', html)
        self.assertTrue(tags)
        for tag in tags:
            self.assertIn('aria-hidden="true"', tag)

    def test_favicon_has_ink_written_in(self):
        f = bd.Fan(FULL_LOOK)
        import base64
        for asleep in (False, True):
            svg = base64.b64decode(f.favicon(asleep).split(",", 1)[1]).decode("utf-8")
            self.assertNotIn("currentColor", svg)
            self.assertIn(bd.INK, svg)
            self.assertIn("prefers-color-scheme: dark", svg)

    def test_every_bundled_style_and_animal_loads(self):
        for line in ("thin", "thick"):
            for eyes in ("dots", "shiny"):
                for animal in ("cat", "dog", "lop", "bunny"):
                    f = bd.Fan(dict(FULL_LOOK, line=line, eyes=eyes, animal=animal))
                    self.assertEqual(len(f.svgs), len(bd.FF_NOUNS))
                    f.favicon(), f.favicon(True)

    def test_drawing_check_refuses_anything_but_plain_line_art(self):
        # each of these either loaded something from elsewhere in Chrome or slipped past an earlier denylist
        ns = 'xmlns="http://www.w3.org/2000/svg"'
        bad = [f'<svg {ns}><image href="#a"><animate attributeName="href" to="https://evil.example/a.png"/></image></svg>',
               f'<svg {ns}><path d="M0 0" style="fill:u\\72l(https://evil.example/s.svg#x)"/></svg>',
               f'<svg {ns}><path d="M0 0" fill="u\\72l(https://evil.example/f.svg#x)"/></svg>',
               f'<svg {ns}><g><set attributeName="href" to="&#106;avascript:alert(1)"/></g></svg>',
               f'<svg {ns}><foreignObject><img xmlns="http://www.w3.org/1999/xhtml" src="x"/></foreignObject></svg>',
               f'<svg {ns}><img src="https://evil.example/i.png"/></svg>',
               f'<svg {ns} onload="alert(1)"/>', f'<!DOCTYPE svg><svg {ns}/>', '<svg><path d="M0 0"/></svg>',
               f'<svg {ns}><path d="M0 0" fill="url(#g)"/></svg>']
        tmp = Path(tempfile.mkdtemp())
        try:
            for i, t in enumerate(bad):
                f = tmp / f"{i}.svg"
                f.write_text(t, encoding="utf-8")
                with self.assertRaises(ValueError, msg=t):
                    bd._ff_read(f)
        finally:
            shutil.rmtree(tmp)

    def test_every_bundled_drawing_passes_the_check(self):
        n = 0
        for style in bd.FAIRY_STYLES:
            for p in sorted((bd.FF_DIR / style).glob("*.svg")):
                bd._ff_read(p)
                n += 1
        self.assertEqual(n, len(bd.FAIRY_STYLES) * len(bd.LOOK_CHOICES["animal"]) * len(bd.FF_NOUNS))

    def test_lists_match_the_helpers(self):
        # the helper and the builder each keep their own copy (neither imports the other): they must agree
        self.assertEqual(serve.FF_STYLES, bd.FAIRY_STYLES)
        self.assertEqual(serve.FF_ANIMALS, bd.LOOK_CHOICES["animal"])
        self.assertEqual(serve.FF_NOUNS, bd.FF_NOUNS)
        self.assertEqual({k: tuple(v) for k, v in serve.LOOK_ONE.items()}, bd.LOOK_CHOICES)
        self.assertEqual(serve.LOOK_MANY, {"places": bd.FF_PLACES, "moves": bd.FF_MOVES})

    def test_out_file_is_swapped_in_whole(self):
        import subprocess
        tmp = Path(tempfile.mkdtemp())
        try:
            out = tmp / "2026-03-12 Morning brief and Jira digest.html"
            out.write_text("old", encoding="utf-8")
            subprocess.run([sys.executable, "-I", "-B", str(DIGEST / "build_digest.py"), str(FIXTURE), str(out)],
                           check=True, capture_output=True)
            self.assertTrue(out.read_text(encoding="utf-8").startswith("<!doctype"))
            self.assertEqual(sorted(x.name for x in tmp.iterdir()), [out.name])  # no temp file left beside it
        finally:
            shutil.rmtree(tmp)

    def test_default_look_path_is_beside_runs(self):
        # with --log <home>/runs/streak.jsonl and no --look, the builder reads <home>/look.json: in the installed package
        # that is ~/.morning-fairy/look.json, the file the helper writes (run here on temp copies only)
        import subprocess
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "runs").mkdir()
            out = tmp / "out.html"
            cmd = [sys.executable, "-I", "-B", str(DIGEST / "build_digest.py"), str(FIXTURE), str(out),
                   "--log", str(tmp / "runs" / "streak.jsonl")]
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertIn('data-look-set="0"', out.read_text(encoding="utf-8"))  # no look.json yet
            (tmp / "look.json").write_text(json.dumps(FULL_LOOK), encoding="utf-8")
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertIn('data-look-set="1"', out.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(tmp)


class Helper(unittest.TestCase):
    """serve.py on a free port, with DIGEST and DESKTOP pointed at temp folders."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.digest, cls.desk = cls.tmp / "home", cls.tmp / "Desktop"
        (cls.digest / "runs").mkdir(parents=True)
        cls.desk.mkdir()
        cls.saved = (serve.DIGEST, serve.DESKTOP)
        serve.DIGEST, serve.DESKTOP = cls.digest, cls.desk
        cls.srv = serve.ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        serve.DIGEST, serve.DESKTOP = cls.saved
        shutil.rmtree(cls.tmp)

    def req(self, method, path, body=None, host="127.0.0.1:8765", origin="http://127.0.0.1:8765", length=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        h = {"Host": host}
        if origin:
            h["Origin"] = origin
        data = None
        if body is not None:
            data = (body if isinstance(body, str) else json.dumps(body)).encode("utf-8")
            h["Content-Type"] = "application/json"
            h["Content-Length"] = str(len(data) if length is None else length)
        c.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        for k, v in h.items():
            c.putheader(k, v)
        c.endheaders()
        if data:
            c.send(data)
        r = c.getresponse()
        out = (r.status, r.getheader("Content-Type"), r.read())
        c.close()
        return out

    def leftovers(self, folder):
        return sorted(p.name for p in folder.glob(".look.json.*"))

    # ---- GET /fanfan/... ----
    def test_fanfan_serves_a_listed_icon(self):
        st, ct, body = self.req("GET", "/fanfan/thick-highlight/cat-star.svg")
        self.assertEqual(st, 200)
        self.assertEqual(ct, "image/svg+xml")
        self.assertTrue(body.startswith(b"<svg"))
        self.assertEqual(self.req("GET", "/fanfan/thin/bunny-face-whole.svg")[0], 200)

    def test_fanfan_refuses_everything_else(self):
        for path in ("/fanfan/../serve.py", "/fanfan/thin/../../serve.py", "/fanfan/thin/cat-star.svg/..",
                     "/fanfan/%2e%2e/serve.py", "/fanfan/thin/cat-star%2Esvg", "/fanfan/thin/%2e%2e%2fLICENSE",
                     "/fanfan/LICENSE", "/fanfan/fanfan-motion.css", "/fanfan/favicon/thin/cat-face-whole.svg",
                     "/fanfan/thin/cat-home.svg", "/fanfan/thin/fox-star.svg", "/fanfan/fat/cat-star.svg",
                     "/fanfan/thin/cat-star.svg?x=1", "/fanfan/thin//cat-star.svg", "/fanfan/THIN/cat-star.svg",
                     "/fanfan/thin/cat-star.svg%00", "/fanfan/thin\\cat-star.svg", "/fanfan/thin/cat-star"):
            self.assertEqual(self.req("GET", path)[0], 404, path)

    def test_fanfan_needs_the_local_host(self):
        self.assertEqual(self.req("GET", "/fanfan/thin/cat-star.svg", host="evil.example:8765")[0], 403)

    def test_brief_refuses_to_be_framed(self):
        name = "2026-03-12 Morning brief and Jira digest.html"
        (self.desk / name).write_text("<!doctype html><body>x</body>", encoding="utf-8")
        try:
            c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
            c.putrequest("GET", "/brief/" + name.replace(" ", "%20"), skip_host=True)
            c.putheader("Host", "127.0.0.1:8765")
            c.endheaders()
            r = c.getresponse()
            r.read()
            self.assertEqual(r.status, 200)
            self.assertEqual(r.getheader("X-Frame-Options"), "DENY")
            self.assertIn("frame-ancestors 'none'", r.getheader("Content-Security-Policy"))
            c.close()
        finally:
            (self.desk / name).unlink()

    # ---- POST /look ----
    def test_look_refuses_wrong_origin_host_length(self):
        self.assertEqual(self.req("POST", "/look", FULL_LOOK, origin="http://evil.example")[0], 403)
        self.assertEqual(self.req("POST", "/look", FULL_LOOK, origin=None)[0], 403)
        self.assertEqual(self.req("POST", "/look", FULL_LOOK, host="evil.example")[0], 403)
        self.assertEqual(self.req("POST", "/look", "x" * 5000)[0], 413)
        self.assertFalse((self.digest / "look.json").exists())

    def test_look_refuses_bad_shapes(self):
        bad = [dict(FULL_LOOK, animal="fox"), dict(FULL_LOOK, line=["thick"]), dict(FULL_LOOK, places=["tabs", "tabs"]),
               dict(FULL_LOOK, places=["../x"]), dict(FULL_LOOK, moves="all"), dict(FULL_LOOK, extra=1),
               {k: v for k, v in FULL_LOOK.items() if k not in ("eyes",)}, {k: v for k, v in FULL_LOOK.items() if k != "moves"},
               [FULL_LOOK], "cat"]
        for b in bad:
            self.assertEqual(self.req("POST", "/look", b)[0], 400, b)
        self.assertEqual(self.req("POST", "/look", "{not json")[0], 400)
        self.assertFalse((self.digest / "look.json").exists())

    def test_look_without_places_is_saved_with_all_six(self):
        # the picker no longer sends places; what is written still lists them all
        body = {k: v for k, v in FULL_LOOK.items() if k != "places"}
        self.assertEqual(serve.clean_look(body), FULL_LOOK)
        self.assertEqual(serve.clean_look(dict(body, places=["tabs"])), FULL_LOOK)  # an older page's shorter list: checked, then all six
        self.assertIsNone(serve.clean_look(dict(body, places=["x"])))

    def test_look_saves_and_rebuilds_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        content = self.digest / "runs" / f"content-{today}.json"
        try:
            # no content for today: the look is saved, nothing is rebuilt
            st, ct, body = self.req("POST", "/look", FULL_LOOK)
            self.assertEqual((st, json.loads(body)), (200, {"ok": True, "saved": True, "rebuilt": False}))
            self.assertEqual(json.loads((self.digest / "look.json").read_text(encoding="utf-8")), FULL_LOOK)
            # with today's content: the brief in the (temp) briefs folder is rebuilt with the new look and the temp logs
            d = json.loads(FIXTURE.read_text(encoding="utf-8"))
            d["date"] = today
            content.write_text(json.dumps(d), encoding="utf-8")
            new = dict(FULL_LOOK, animal="dog")
            st, ct, body = self.req("POST", "/look", new)
            self.assertEqual((st, json.loads(body)), (200, {"ok": True, "saved": True, "rebuilt": True}))
            page = (self.desk / f"{today} Morning brief and Jira digest.html").read_text(encoding="utf-8")
            self.assertIn('data-look-set="1"', page)
            tpl = "".join(re.findall(r'<template id="ff-[a-z-]+">.*?</template>', page))
            self.assertIn("bb-dog", tpl)
            self.assertTrue((self.digest / "runs" / "streak.jsonl").is_file())
            self.assertEqual(self.leftovers(self.digest), [])
            self.assertEqual([p.name for p in self.desk.iterdir() if p.name.startswith(".")], [])  # the brief was swapped in whole
        finally:
            content.unlink(missing_ok=True)

    def test_look_saved_but_rebuild_failed_says_so(self):
        # a broken content file for today: look.json is still written, and the reply says saved but not rebuilt
        today = datetime.now().strftime("%Y-%m-%d")
        content = self.digest / "runs" / f"content-{today}.json"
        try:
            content.write_text("{not json", encoding="utf-8")
            st, ct, body = self.req("POST", "/look", dict(FULL_LOOK, animal="lop"))
            self.assertEqual((st, json.loads(body)), (500, {"ok": False, "saved": True, "rebuilt": False}))
            self.assertEqual(json.loads((self.digest / "look.json").read_text(encoding="utf-8"))["animal"], "lop")
        finally:
            content.unlink(missing_ok=True)

    def test_look_not_saved_says_so(self):
        # look.json cannot be written (a folder is in its way): nothing saved, nothing rebuilt, no temp file left behind
        path = self.digest / "look.json"
        keep = path.read_bytes() if path.is_file() else None
        path.unlink(missing_ok=True)
        path.mkdir()
        try:
            st, ct, body = self.req("POST", "/look", FULL_LOOK)
            self.assertEqual((st, json.loads(body)), (500, {"ok": False, "saved": False, "rebuilt": False}))
            self.assertEqual(self.leftovers(self.digest), [])
        finally:
            path.rmdir()
            if keep is not None:
                path.write_bytes(keep)

    def test_look_can_be_saved_before_the_first_morning_run(self):
        # a fresh install: the data folder (~/.morning-fairy) does not exist yet when the picker saves
        fresh = self.tmp / "fresh-home"
        self.assertFalse(fresh.exists())
        serve.DIGEST = fresh
        try:
            st, ct, body = self.req("POST", "/look", FULL_LOOK)
            self.assertEqual((st, json.loads(body)), (200, {"ok": True, "saved": True, "rebuilt": False}))
            self.assertEqual(json.loads((fresh / "look.json").read_text(encoding="utf-8")), FULL_LOOK)
            self.assertEqual(self.leftovers(fresh), [])
        finally:
            serve.DIGEST = self.digest

    def test_done_still_works(self):
        st, _, _ = self.req("POST", "/done", {"date": "2026-03-12", "id": "x", "title": "t", "project": "p", "done": True})
        self.assertEqual(st, 200)
        self.assertTrue((self.digest / "runs" / "done.jsonl").is_file())


if __name__ == "__main__":
    unittest.main()
