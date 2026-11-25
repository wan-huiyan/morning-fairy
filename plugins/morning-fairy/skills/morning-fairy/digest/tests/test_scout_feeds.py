"""Tests for scout_feeds.py, the Scout's one-call reader of news, release notes and GitHub trending.

Run from the repo root:  python3 -I -B -m unittest discover -s plugins/morning-fairy/skills/morning-fairy/digest/tests -v
Nothing is fetched: every test feeds the parsers made-up text, or swaps fetch() for a stub.
"""
import datetime as dt
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

DIGEST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIGEST))  # -I leaves the script's folder off the path

import scout_feeds as sf  # noqa: E402

RSS = """
<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>Blog</title>
<item><title>New &amp; shiny</title><link>https://example.com/new</link><pubDate>Mon, 24 Nov 2026 09:00:00 GMT</pubDate></item>
<item><title>Old one</title><link>https://example.com/old</link><pubDate>Mon, 10 Nov 2026 09:00:00 GMT</pubDate></item>
</channel></rss>"""

ATOM = """<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Weblog</title>
<entry><title>A post</title><link rel="alternate" href="https://example.org/post"/><published>2026-11-24T08:00:00Z</published></entry>
</feed>"""

TRENDING = """<article class="Box-row"><h2 class="h3"><a href="/acme/rocket" class="Link">acme / rocket</a></h2>
<p class="col-9 color-fg-muted my-1 pr-4">  Ships   things  </p><span>1,234 stars this week</span></article>"""

SITEMAP = """<urlset><url><loc>https://www.example.com/news/big-launch</loc><lastmod>2026-11-24T10:00:00Z</lastmod></url>
<url><loc>https://www.example.com/news/old-launch</loc><lastmod>2026-10-01T10:00:00Z</lastmod></url>
<url><loc>https://www.example.com/careers/jobs</loc><lastmod>2026-11-24T10:00:00Z</lastmod></url></urlset>"""

SINCE = dt.date(2026, 11, 20)


class Parsers(unittest.TestCase):
    def test_rss_with_a_leading_blank_line(self):
        items = sf.read_feed(RSS)
        self.assertEqual(items[0], (dt.date(2026, 11, 24), "New & shiny", "https://example.com/new"))
        self.assertEqual(len(items), 2)

    def test_only_https_links_reach_the_output(self):
        items = sf.read_feed(RSS.replace("https://example.com/new", "javascript:alert(1)"))
        self.assertEqual([i[2] for i in items], ["", "https://example.com/old"])

    def test_an_oldest_first_feed_prints_newest_first(self):
        head, new, old = RSS.split("<item>")
        oldest_first = head + "<item>" + old.replace("</channel></rss>", "") + "<item>" + new + "</channel></rss>"
        self.assertEqual([i[0].day for i in sf.read_feed(oldest_first)], [24, 10])

    def test_entity_declarations_are_refused(self):
        with self.assertRaises(ValueError):
            sf.read_feed('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "aaaa">]><rss>&a;</rss>')

    def test_atom_takes_the_alternate_link(self):
        self.assertEqual(sf.read_feed(ATOM), [(dt.date(2026, 11, 24), "A post", "https://example.org/post")])

    def test_trending_names_repo_description_and_stars(self):
        [(date, title, link)] = sf.read_trending(TRENDING)
        self.assertIsNone(date)
        self.assertEqual(title, "acme/rocket: Ships things (1,234 stars this week)")
        self.assertEqual(link, "https://github.com/acme/rocket")

    def test_sitemap_keeps_matching_paths_since_the_cutoff(self):
        items = sf.read_sitemap(SITEMAP, ["/news/"], SINCE)
        self.assertEqual(items, [(dt.date(2026, 11, 24), "big launch", "https://www.example.com/news/big-launch")])


class Sweep(unittest.TestCase):
    def run_sweep(self, pages):
        lines, real = [], sf.fetch

        def stub(url, timeout):
            if isinstance(pages[url], Exception):
                raise pages[url]
            return pages[url]
        sf.fetch = stub
        try:
            sf.sweep([("people", "Blog", "https://a/rss", "feed", ""),
                      ("skills", "Trending", "https://b/trending", "trending", ""),
                      ("stack", "Broken", "https://c/rss", "feed", "")], SINCE, out=lines.append)
        finally:
            sf.fetch = real
        return "\n".join(lines)

    def test_only_new_entries_and_an_honest_status_per_source(self):
        out = self.run_sweep({"https://a/rss": RSS, "https://b/trending": TRENDING, "https://c/rss": OSError("HTTP 403")})
        self.assertIn("[people] Blog: 1 new entries", out)
        self.assertIn("https://example.com/new", out)
        self.assertNotIn("https://example.com/old", out)
        self.assertIn("[skills] Trending: 1 entries", out)
        self.assertIn("[stack] Broken: UNREADABLE (OSError: HTTP 403)", out)

    def test_a_trending_page_with_no_repos_is_unreadable_not_quiet(self):
        out = self.run_sweep({"https://a/rss": RSS, "https://b/trending": "<html>new layout</html>",
                              "https://c/rss": RSS})
        self.assertIn("[skills] Trending: UNREADABLE", out)


class Config(unittest.TestCase):
    def test_last_brief_is_the_newest_content_file_before_today(self):
        with tempfile.TemporaryDirectory() as d:
            for day in ("2026-11-21", "2026-11-24", "2026-11-25"):
                Path(d, f"content-{day}.json").write_text("{}")
            self.assertEqual(sf.last_brief(d, "2026-11-25"), "2026-11-24")
            self.assertEqual(sf.last_brief(os.path.join(d, "none"), "2026-11-25"), "2026-11-18")

    def test_extra_feeds_need_https_and_a_known_kind(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "scout_feeds.json")
            p.write_text(json.dumps({"feeds": [
                {"lane": "stack", "name": "Release notes", "url": "https://example.com/feed.xml"},
                {"name": "Plain http", "url": "http://example.com/feed.xml"},
                {"name": "Odd kind", "url": "https://example.com/x", "kind": "scrape"}]}))
            self.assertEqual(sf.read_extra(str(p)), [("stack", "Release notes", "https://example.com/feed.xml", "feed", "")])
            self.assertEqual(sf.read_extra(str(Path(d, "missing.json"))), [])
            p.write_text('{"feeds": [{"url": "https://x",}]}')
            self.assertEqual(sf.read_extra(str(p)), [])  # bad JSON: skipped, never a crash
            p.write_text('{"feeds": ["https://x"]}')
            self.assertEqual(sf.read_extra(str(p)), [])

    def test_the_example_file_is_valid(self):
        feeds = sf.read_extra(str(DIGEST / "scout_feeds.example.json"))
        self.assertGreaterEqual(len(feeds), 5)


if __name__ == "__main__":
    unittest.main()
