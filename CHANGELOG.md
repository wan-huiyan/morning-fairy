# Changelog

- **1.23.0** (2026-11-25): a wider Scout. It now searches four lanes, so the list is never all one changelog: skills
  and agent tooling (GitHub trending, skill repos rising over the last 30 days, Anthropic and Claude news), your
  stack's release notes, posts by credible people (Simon Willison, Eugene Yan, Hamel Husain, Latent Space, Hacker
  News, Reddit through web search) and one wildcard from outside your stack. Up to 8 finds, no more than 3 from one
  lane, within 30 reads. A new script, `scout_feeds.py`, reads every feed in one call and says per source whether it
  was read, so "nothing new" is never confused with "could not read"; add your own stack's feeds in
  `~/.morning-fairy/scout_feeds.json` (example included: Google Cloud release notes, the Google Ads blog, two data
  visualisation blogs). A credibility rule: an official source, a named practitioner or real discussion; a star
  count alone is not enough.
- **1.22.0** (2026-11-25): a new source, **doc comments**. Comments in Google Docs, Slides and Sheets that tag you
  now reach the to-do list: action items assigned to you that are still open, and @-mentions that ask you
  something. Google's comment emails say what was asked; a Google Drive search says which assignments are still
  open, so one you resolved moves to Resolved. Look's "What your fairy reads" lists it.
- **1.21.0** (2026-11-25): two new mascots and a bigger Clawd. **Nib**, a wax crayon drawn in crayon (its lines redraw
  themselves a few times a second, like hand-drawn animation, in the scene and the top-left logo), and **Pip**, a little
  laptop whose face glows on its screen (dimmer at night). Both have the ticket's four moods and five click faces, hop,
  and do the same idle moments; both are drawn inside the page, so they work offline. Clawd now stands about 1.4 times
  bigger, filling the space the ticket fills. The mascot switch in Look is always shown, with four pictures (three if
  the builder does not offer Clawd).
- **1.20.0** (2026-11-25): a livelier mascot. Click it, on the hill or top left (the top-left one is a button, so
  the keyboard reaches it too), and it reacts. The ticket hops and pulls one of four new faces in turn (a grin,
  heart eyes, surprise, a wink) while hearts or stars float up; Clawd plays one of five stickers in turn. Five quick
  clicks make either one dizzy. The ticket also grins when you tick a box, looks startled when you untick one and
  gets heart eyes on Done, and both do something small by themselves now and then: only while the page is in view,
  never at night or with reduced motion, and at most twice in a row while nobody uses the page. With reduced motion
  the faces still change but nothing hops or floats.
- **1.19.0** (2026-11-25): tidier layouts. The mascot switch in Look is two pictures instead of the words Ticket and
  Clawd. The layout switch in the top bar is gone (Look has the same one). Map is retired: it looked busy, and a
  browser that had saved Map opens the scene instead. Switching to Scene no longer opens the section you were reading:
  the scene always opens on the scene alone.
- **1.18.0** (2026-11-25): a simpler Look panel. "Build your fairy…" and its picker are gone: the mascot is now a
  Ticket | Clawd switch at the top of Look, and every page draws the same little dog icons, including the tabs added
  since the picker (Hours, Cloud spend, Scout), which had kept plain line drawings. In the picker's place, Look lists
  which sources this morning's brief read and which it did not, with a button that copies a "set up morning fairy"
  prompt for the rest. An existing `look.json` still works: its mascot and moves count, its animal, line and eyes
  are ignored. The helper no longer serves `/fanfan` (only the picker used it).
- **1.17.2** (2026-11-24): the same login-page check now finds the right browser for you. When more than one Chrome is
  connected to Claude, the session opens the Tempo link in each one, just to look, and carries on in the one that is
  signed in. It asks you only if none, or more than one, is signed in. Before this it asked you which one to use.
- **1.17.1** (2026-11-24): Fill Tempo and Approve and log no longer get stuck on a login page. If the Tempo link lands
  on the Atlassian login page, the session now checks which Chrome browsers are connected to Claude and asks which
  one you are signed in on, instead of asking you to sign in again in a browser you are not using.
- **1.17.0** (2026-11-20): easy setup. Say "set up morning fairy" and Claude checks your computer with the new
  `digest/doctor.py` (Python, folders, `gh` and `gcloud` sign-ins, settings files, the helper, the Dock app; read-only,
  each problem with its fix), tests each connector with one small read, asks your name, email and time zone, writes
  your routine prompt to `~/.morning-fairy/routine-prompt.md`, builds your first brief, and schedules the run or tells
  you how. Your settings files `clients.json` and `start.json` now live in `~/.morning-fairy/`, so a plugin update
  (which installs a new folder) no longer loses them; a file still beside the code is read until you move it, and
  `doctor.py` tells you how.
- **1.16.0** (2026-11-19): the swipe deck is back, beside the map, so there are four layouts to pick from. Tap the card in
  the middle of the deck (or the Enlarge button in its header) and it grows into a big reading view, nearly the whole
  window on a laptop and the whole screen on a phone, with its own scroll. Close it with ×, Escape or a tap outside and it
  shrinks back into its place. Tapping a box, a link or a button inside the card still does just that, and a swipe still
  just moves the deck. Tapping a card at the side brings it to the middle. A pick of the deck saved in the browser opens
  as the deck again.
- **1.15.0** (2026-11-18): a quest map. The side-scrolling card layout is retired and a new Map layout takes its
  place: each section is a numbered level standing on the hills, joined by a dashed path (a snake across a laptop, a
  zig-zag down a phone). The mascot hops to the level you open and its card pops up over the scene, with Level i of n,
  Back and Next level (or the arrow keys). A level shows how many of its items are still to do and turns into a check
  when you have ticked them all; an XP bar under the headline counts today's ticks. A saved pick of the old layout opens
  as the map.
- **1.14.1** (2026-11-18): calendar meetings are logged as the calendar shows them. An hours entry can carry a
  `start` time; the page shows it ("from 10:00") and the logging session logs that row as its own worklog at that
  time and length. Both Tempo prompts now say each meeting is its own worklog, never merged with another.
- **1.14.0** (2026-11-18): quiet stretches. The session log only sees time while messages flow, so reading an
  agent's work or writing your answers in the brief went uncounted. `measure_session_hours.py --spans` now lists
  the silence before each reply you typed, cut around meetings, out-of-office blocks (`"away": true` in
  `--meetings`) and typing in other sessions, and the timeline draws them dotted and left out until you tick them.
  And overlaps between rows now count in both rows: the timeline marks them and takes nothing off either.
- **1.13.0** (2026-11-18): the Spend tab splits each project's cost into **Your patch** (your login plus the
  service accounts you list in `spend_accounts.json`) and **The neighbours** (everyone else), in the summary bar,
  each row and each day's bar.
- **1.12.1** (2026-11-18): the session that Approve and log starts now runs on Sonnet (`--model sonnet`): the hours
  are already decided on the page, so it only types them in. Fill Tempo, which measures and proposes, stays on your
  default model.
- **1.12.0** (2026-11-18): the Approve and log card draws each day as a timeline. One lane per row, each stretch
  of work across the hours in the project's colour, calendar meetings as pills, and stretches where an agent ran
  alone faded and left out until you click them in. Where two rows overlap, the overlap is hatched and counted
  once (in the meeting's row by default; a click moves it). Lane totals sum into the tiles and the button, and
  hovering a block says where it came from. `measure_session_hours.py --spans` lists the stretches the brief needs.
- **1.11.0** (2026-11-18): the Spend tab, optional. `measure_gcp_spend.py` finds the Google Cloud projects you ran
  a BigQuery query in over the last 30 days and estimates what their queries cost this month; the page draws a row
  per project with a bar per day, the month-end pace and any day that jumped. And the "No change" tickets now always
  sit folded at the foot of the Jira tab as "Already up to date in Jira (N)": on a morning with nothing to update
  they used to get a tab of their own.
- **1.10.0** (2026-11-18): the Hours tab gets an "Approve and log" card. For each day Tempo still lacks, it lists
  the morning's proposed rows, all ticked, with the minutes and the description Tempo will get, both editable.
  One click starts a Claude session that logs exactly those rows, reading the day in Tempo first and stopping if
  anything does not match. It needs the same Tempo setup as Fill Tempo; without it the card still shows and says logging is not set up.
  Hours entries can carry a short `desc` for that description. The hours measure now counts only stretches where you
  actually typed a message, so agents running on their own, a loaded skill, a `/loop` prompt or a
  context-refresh summary no longer add time; `--include-unattended` brings the old count back, and
  `--require-typed` still works but is now the default.
- **1.9.0** (2026-11-17): the time machine moves from the tabs to a clock button in the top row and opens as a
  dialog, so the remaining tabs fit; a narrow tab strip (a laptop window about 1000 px wide) shows them icon over
  label. An earlier brief served by the helper now has a way forward inside its time machine: its own day is
  labelled with its date instead of "Today", and a "Today" chip and a "Back to today's brief" button lead to the
  newest brief. A past brief opened straight from the folder links back through the helper. The calendar's
  Sunday column no longer overflows on a phone.
- **1.8.1** (2026-11-16): Fill Tempo opens its Terminal session as `claude --chrome`, so it can reach the Claude in
  Chrome extension to read your Tempo page (without the flag the session has no Chrome tools). Start in Claude
  sessions stay without it.
- **1.8.0** (2026-11-16): the Scout tab. An optional `scout` list (tone `scout`) shows web finds as offers: no Done
  pill, left out of every count of what waits on you, asks read-and-assess only, and `read_scouted` keeps a link from
  being shown twice in 14 mornings. The routine prompt gains an optional step for it. Quest prompts now say the
  tasks may come from "email, Slack, calendar and the web". On a phone, the seven tab labels wrap instead of
  overlapping.
- **1.7.0** (2026-11-16): Start in Claude. With `digest/start.json` in place and the brief opened through the
  local helper, each project and quest on the Quests board can open a Claude Code session in Terminal, in its
  project folder (`POST /start-quests`, quest ids only; folders limited to `root`). It runs in your own default
  permission mode; Copy stays for anyone who would rather paste the prompt themselves. Fill Tempo now hands its
  prompt to Terminal the same way, through a private file the new shell reads once and deletes.
- **1.6.2** (2026-11-16): the Hours tab lists the newest day first, in the bars and the table.
- **1.6.1** (2026-11-16): the Hours tab's bars take each world's own colours (garden, cosmic, candy,
  caterpillar; light and dark), and the greys follow each world's muted ink.
- **1.6.0** (2026-11-16): the Hours tab. An `hours` chapter draws one stacked bar per day (each project
  its own colour; billable solid, non-billable striped, unattributed dotted grey; a tick for what Tempo
  already holds), with week totals and a table view. A Fill Tempo button asks the local helper
  (`POST /fill-hours`, a date only) to open Terminal on an attended Claude session for one day, or copies
  the prompt without the helper. Its Tempo page, work-item note and folder come from a `fill_tempo` block
  in `clients.json`; without one the button does not show.
- **1.5.0** (2026-11-13): an optional timesheet-hours step. With a `digest/clients.json` in place, the
  run measures the last seven days from your session transcripts, proposes the per-day gap against what
  is already logged, and stops there — it reads and proposes, it never saves a timesheet entry. Off by
  default; the repo ships only `clients.example.json`.
- **1.4.1** (2026-11-06): the README's picker pictures show Clawd's real sticker on the Clawd card, instead of
  the ticket the card falls back to offline. Those two pictures carry the sticker's CC BY-NC-SA 4.0 licence.
- **1.4.0** (2026-11-06): calmer and roomier. The right-hand panel (count tiles, project cards, tabs and buttons)
  now takes its colours from its world, light and dark, a step quieter than the scene. Cards tilt less as they grow
  and not at all past 560 px, so big cards stay easy to read. A tall meeting hill no longer pushes signs into the sun:
  the sun rides above every board, getting smaller first, and on a phone the scene gets up to 35% more sky rather than
  shrinking the signs. In the swipe deck, where the scene's height is fixed by the screen, the sun can still touch the
  top sign on a very tall day. The "now" label no longer sits on a signpost.
- **1.3.0** (2026-11-05): a fourth world, Caterpillar: the day is a big leaf, the caterpillar's body is the
  part of the day already lived with its head munching at now, it climbs over each meeting's hill, curls into a cocoon
  after 6 PM, and the all-done finale is a butterfly. The meeting hills and the admin clipboards on the scene are now
  links: each opens its row in Your day. Ticking Done on an admin to-do now closes its overdue or due-today deadline
  in the admin log at the next build. Meeting titles are escaped before they reach the scene drawing (a `<` in a
  calendar title used to break it).
- **1.2.1** (2026-11-05): a simpler picker. The mascot is the ticket or Clawd; the little animal is now the style
  of the page's icons rather than a third mascot, and it goes everywhere it fits (no more choosing places). The top
  bar's sound and Look buttons keep their own drawings. On a brief opened as a file, the save button opens the live
  brief with your choices already filled in. An older `look.json` still works: a "fanfan" mascot reads as the
  ticket, and any list of places reads as all of them. 60 Python tests.
- **1.2.0** (2026-11-05): build your own fairy. A picker (once on the first brief, then from Look) chooses the
  mascot (the ticket, Clawd, or a little animal), one of four animals, line and eyes, six places for little animal
  icons, and five moves. Saved by the helper to `~/.morning-fairy/look.json`, which also redraws today's brief. The
  fanfan icons are bundled (MIT); Clawd loads from the artist's repository and falls back to the ticket offline.
  The helper now refuses to be framed by another site. 56 Python tests, run by `npm test`.
- **1.1.1** (2026-11-05): the Auto layout button is gone. On a wide window it looked exactly like Tap the scene;
  the page still follows your window until you pick a layout, and the button for what's showing is the pressed one.
- **1.1.0** (2026-11-05): a Dock app maker (`make_dock_app.sh`, macOS) with the mascot icon, a fill-in-the-blanks
  daily routine prompt (`routine-prompt.md`), and a "Set up your daily brief" guide. CI now also runs on macOS.
- **1.0.0** (2026-11-05): first release. Three worlds in light and dark, four layouts, the day scene with
  meeting hills and a draggable sun, the mood mascot, the Done flight, the Quests board, Jira drafts with
  tick-to-copy, the time machine, 17 sound effects, and a local helper that remembers Done taps.
