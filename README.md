<p align="center">
  <img src="docs/hero.svg" width="720" alt="morning-fairy: a ticket mascot standing on the hills of the day, under a smiling sun"/>
</p>

<h1 align="center">morning-fairy ✨</h1>
<p align="center"><em>Your day, drawn as a little world, every weekday morning.</em></p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/wan-huiyan/morning-fairy" alt="license"/></a>
  <a href="https://github.com/wan-huiyan/morning-fairy/releases"><img src="https://img.shields.io/github/v/release/wan-huiyan/morning-fairy" alt="release"/></a>
  <a href="https://github.com/wan-huiyan/morning-fairy/commits"><img src="https://img.shields.io/github/last-commit/wan-huiyan/morning-fairy" alt="last commit"/></a>
  <a href="https://github.com/wan-huiyan/morning-fairy/actions/workflows/test.yml"><img src="https://github.com/wan-huiyan/morning-fairy/actions/workflows/test.yml/badge.svg" alt="tests"/></a>
  <a href="https://claude.com/claude-code"><img src="https://img.shields.io/badge/Claude_Code-skill-orange" alt="Claude Code skill"/></a>
</p>

> **A Claude Code skill that reads your calendar, email, meeting notes, chat, Jira and GitHub each morning, plus
> your own Claude Code sessions and cloud bill if you switch those on, and builds one cute page: today's meetings
> drawn as hills you can walk a sun across, what actually needs you, tasks you can hand to Claude with their
> context attached, draft Jira updates you tick and copy, and the hours you have not logged yet. The morning run
> never sends, posts or changes anything in your mail, chat, calendar or Jira.**

<p align="center">
  <img src="docs/world-tour.gif" width="760" alt="Dragging the sun across the day and back, a click on the mascot that makes it pull a face, then switching between the garden, cosmic, candy and caterpillar worlds in the Look panel, switching to dark and opening the time machine"/>
  <br/><sub>Drag the sun and the mascot walks the day; click the mascot and it reacts. Switch worlds in Look (garden, cosmic, candy, caterpillar), switch to dark, open the time machine. (All data here is made up.)</sub>
</p>

## What it is, and why

Most mornings start with five tabs: calendar, inbox, chat, Jira, and whatever was left half done yesterday.
morning-fairy reads them once, sorts what it found into **needs you today**, **already resolved** and **not
worth your time**, and draws the result as one page you can take in at a glance.

The page is built to be *enjoyed*, not just read. The day is a landscape: the ground rises at each meeting by
how heavy it is, the sun rides from 8 AM to 6 PM, and a small mascot stands at "now" with a face that
matches your morning (a sweat drop when something is overdue, starry eyes when nothing waits on you, sleepy
after 6). When you finish something, you tap **Done** and watch it get crossed off and fly down into Resolved.

<p align="center">
  <img src="docs/done-flight.gif" width="760" alt="Tapping Done: a heart burst, a pen stroke crosses the card off, and the card flies down into the Resolved list"/>
  <br/><sub>The Done flight: a heart burst, a pen stroke, then the card flies down to Resolved so you can see where it went. Tap again and it flies back.</sub>
</p>

<p align="center">
  <img src="docs/hours-and-scout.gif" width="760" alt="The Hours tab: Wednesday's timeline of work blocks per project, a quiet stretch ticked in so the Orchard row grows from 3h20 to 4h25, the Approve and log button, and the week's stacked bars. Then the Scout tab: a flaky-test finder for the Orchard nightly build, accepted, landing on the Quests board under Orchard app"/>
  <br/><sub>Two optional tabs. <b>Hours</b>: your week measured from your local Claude Code logs and calendar, a timeline you click blocks in and out of, and one button that has Claude log the day in Tempo. <b>Scout</b>: web finds tied to your own projects (here, a tool for this week's failing Orchard build); accept one and it joins that project's quests. (Made-up data.)</sub>
</p>

## 🔌 Where the data comes from

<p align="center">
  <img src="docs/how-it-works.svg" width="760" alt="At 08:00 on a weekday the sun rises and the ticket mascot hops across eleven little houses, one per connected tool; as it lands on each, a flag pops up naming it: Calendar, Email, Meeting notes, Slack, Doc comments, Jira, GitHub, Cloud spend, Local Claude logs, Tempo, The web. It flies to one page, a to-do on the page gets ticked, and a paper plane carries it to a terminal where claude opens in the project folder with that task and its context. Coloured dots carry what the fairy found from the houses to the page."/>
  <br/><sub>The morning round: one house per tool you connect, one page, then the to-do you pick goes to Claude with its context.</sub>
</p>

morning-fairy has no data of its own. Every morning it reads the tools you already use, through the connectors and
command-line tools your Claude Code session can reach, and only those. The more you connect, the more of your day
it can see.

| Source | What the fairy reads it for | How Claude reaches it | Used by |
|---|---|---|---|
| 📅 **Calendar** (Google Calendar) | Today's meetings, which become the hills; tomorrow's meetings to prep for; the meetings that go into your hours | Calendar connector | The day scene (core) |
| ✉️ **Email** (Gmail) | Threads where you were asked and have not replied, deadlines sent to you by name (training, timesheets, access reviews), alert emails such as a failing job, and Jira notification emails | Email connector | The to-do list (core) |
| 📝 **Meeting notes** | What was agreed in yesterday's meetings, as evidence for Jira updates. It prefers the raw transcript over an AI summary | Wherever your notes land. For example, Google Meet's "Notes by Gemini" arrive by email and link to a Google Doc, which needs a Google Drive connector to open | Jira drafts |
| 💬 **Chat** (Slack) | Every direct and group message in the window, not only mentions; project channels as evidence for Jira | Slack connector | The to-do list (core) |
| 🗨️ **Doc comments** (Google Docs, Slides, Sheets) | Comments that tag you: action items assigned to you that are still open, and @-mentions that ask you something. Assignments you have resolved move to Resolved; old ones in files nobody has touched for 14 days are left out | Google's comment emails through the email connector, and a Google Drive connector to check which assignments are still open | The to-do list |
| 🎫 **Jira** | Your assigned tickets and what each one already says, so a draft never repeats what the ticket shows | Atlassian connector | Jira drafts |
| 🐙 **GitHub** | Merged pull requests as evidence for Jira; the live state of anything carried over from yesterday ("to merge" may have merged overnight); Scout searches | The `gh` command-line tool, signed in | Jira drafts; Scout (optional) |
| ☁️ **Google Cloud** | What BigQuery queries cost this month in each project you work in | `gcloud` and `bq`, signed in | Cloud spend (optional) |
| 🤖 **Your local Claude Code logs** | The time stamp on every message in the session logs Claude Code keeps on this computer (`~/.claude/projects/`), turned into hours per project. Sessions you run elsewhere (claude.ai, Claude Code on the web, another machine) are not seen | Local files, no connector | Timesheet hours (optional) |
| ⏱ **Tempo** (the timesheet app inside Jira) | What you have already logged, and, after you approve the hours on the page, logging them | Claude in Chrome, signed in to Tempo ([why the browser](#-timesheet-hours-optional-off-by-default)) | Timesheet hours (optional) |
| 🔭 **The web** | GitHub trending and new skill repos, release notes, AI engineering blogs, Hacker News and Reddit, for ideas that could help your projects | `gh`, web search | Scout (optional) |
| ✅ **Your Done taps** | What you finished on earlier briefs, so it does not come back as a to-do | `~/.morning-fairy/runs/done.jsonl`, written by the local helper | Automatic |

**How to connect them.** Gmail, Google Calendar, Google Drive, Slack and Atlassian (Jira) are connectors you
switch on once in Claude ([claude.ai](https://claude.ai) → Settings → Connectors); Claude Code sessions signed in to
the same account see them as tools. Other connectors that give Claude the same reads (Outlook instead of Gmail,
say) should work too, but only the ones named here have been used. The command-line tools need one sign-in each:
`gh auth login`, and for spend `gcloud auth login` (which also signs in `bq`). Then list what you have in step 3 of the [routine prompt](plugins/morning-fairy/skills/morning-fairy/routine-prompt.md).
A source that cannot be reached one morning does not stop the run: the page is built anyway and says at the top
which source was missing.

**What it does not read:** your browser history, or any tool you have not given it a connector or a sign-in for.
The one place it uses your browser is the two hours sessions (Fill Tempo and Approve and log), which start with
Claude in Chrome so they can open your Tempo page; like any Claude in Chrome session, they act in your signed-in
Chrome. What the morning run finds goes into that morning's brief (on your Desktop) and its files in
`~/.morning-fairy/`.

## What you get

| | Feature | The specifics |
|---|---|---|
| 🌍 | **Four worlds** | Storybook garden, Cosmic orbit, Candy pop and Caterpillar, each with a light and a dark version (8 looks), its own cursor wand and its own fairy dust. In the caterpillar world the day is a leaf, the caterpillar's body is the part of the day already lived, and at 6 PM it curls into a cocoon. |
| 🗺️ | **The day scene** | Hills rise at each real meeting by its weight (1 to 3). Drag the sun to scrub through the day; let go and it snaps back to now. Click a hill or its sign to open that meeting; click an admin clipboard to open its admin row. |
| 🎟️ | **A mascot with moods** | 4 moods: calm, sweat (something overdue), starry (nothing waits), sleepy (after 6 PM). The ticket's eyes follow your pointer. **Click it** (on the hill, or top left) and it reacts: the ticket hops and pulls a face (a grin, heart eyes, surprise, a wink) as hearts or stars float up; Nib and Pip pull the same faces; Clawd plays a sticker. Five quick clicks make either one dizzy. It also grins when you tick a box, looks startled when you untick one, gets heart eyes on Done, and now and then does something by itself. |
| 🧚 | **Four mascots** | Tap a picture at the top of Look to switch the mascot: the ticket, Nib (a wax crayon drawn in crayon, its lines wobbling like hand-drawn animation), Pip (a little laptop whose face glows on its screen), or Clawd. A little dog draws every tab and icon on the page, with 5 small moves. |
| 🔌 | **What your fairy reads** | Look lists the sources this morning's brief read and the ones it did not, with one button that copies a prompt asking Claude to help set up the rest. |
| ✅ | **The Done flight** | A world-themed burst, a pen stroke across the card, then the card flies into Resolved. Undo flies it back to its place. |
| 🧚 | **Quests for Claude** | Tasks Claude can pick up, grouped by project, each with a size ("about 20 min") and a "Copy for &lt;project&gt;" prompt that names the folder to open. Optionally, a **Start in Claude** button opens the session for you. |
| 🔭 | **Scout: worth a look** | Optional. A chapter of web finds (trending repos, release notes, credible blogs and discussion, one wildcard) that could improve your work, each saying which of your projects it helps and why. They are offers, not to-dos: nothing waits on you, no Done pill, and each ask is read-and-assess only. |
| 💸 | **Cloud spend** | Optional. What BigQuery queries have cost this month in each Google Cloud project you work in: a little bar per day, the month-end pace, the account that spent most, and a sweating mascot when a day jumps. |
| 🎫 | **Jira drafts, tick to apply** | Each proposed update shows the exact text the ticket will get, the private evidence behind it, and a confidence line. Nothing is written until you paste it back. Tickets that already match sit folded underneath as "Already up to date". |
| 🕰️ | **Time machine** | A month calendar plus a row of recent mornings. Pick a day to see what it said and what got done, then open that brief exactly as it was. |
| 📐 | **Three layouts** | Picked in Look. Scene (signposts on the hills; it always opens on the scene alone, with no section open), Tabs, and Deck (tap the card in the middle, or its Enlarge button, and it grows into a big reading view). Until you pick one, the page follows your window: the scene when it's wide, tabs when it's narrow or on a phone. |
| 🔊 | **18 sound effects** | Off until you switch them on. Each world has its own voice: a triangle wave in the garden, a detuned sine in space, a square wave in candy, a soft sine pluck on the leaf. |
| 🎉 | **Small secrets** | Type `magic` anywhere for a party. Tick every box on the page and the mascot hops into an all-done finale. |
| ♿ | **Calm when asked** | With reduced motion on, nothing flies, bobs, wiggles or sparkles. |

<table>
<tr>
<td width="62%"><img src="docs/cosmic-light-jira.png" alt="The Jira tab: a draft comment, what the client will see, and the private evidence behind it"/><br/><sub>Jira drafts: what the ticket will say, and the evidence that stays private.</sub></td>
<td width="38%"><img src="docs/phones.png" alt="The brief on a phone, in candy dark and garden light"/><br/><sub>On a phone: a bottom tab bar, and the scene shrinks to fit.</sub></td>
</tr>
</table>

## 🧚 The Look panel

<p align="center">
  <img src="docs/look-panel.png" width="420" alt="The Look panel over the demo morning: four mascot pictures at the top (the ticket picked, then Nib the crayon, Pip the laptop, and the Clawd button, left blank in this picture), the four worlds, dark mode and sparkles, the layout switch, then What your fairy reads: Calendar, Email, Slack, Doc comments, Jira, GitHub and The web read this morning; Meeting notes, Google Cloud, Claude Code logs and Tempo not read; and a button that copies a prompt to set up the rest"/>
  <br/><sub>Look, over the demo morning. Clawd's button shows the artist's sticker once Look opens; it is left blank
  here so this repository holds no copy of it. (Made-up data.)</sub>
</p>

<table>
<tr>
<td width="25%" align="center"><img src="docs/mascot-ticket.gif" width="100%" alt="The ticket mascot clicked five ways: a grin, heart eyes, surprise, a wink, then dizzy after five quick clicks, hopping each time as hearts or stars float up"/><br/><sub><b>The ticket</b>: the brief's own</sub></td>
<td width="25%" align="center"><img src="docs/mascot-nib.gif" width="100%" alt="Nib, a wax crayon drawn in wobbly crayon lines, clicked five ways: a grin, heart eyes, surprise, a wink, then dizzy"/><br/><sub><b>Nib</b>: a wax crayon, drawn in crayon</sub></td>
<td width="25%" align="center"><img src="docs/mascot-pip.gif" width="100%" alt="Pip, a little laptop whose face glows on its screen, clicked five ways: a grin, heart eyes, surprise, a wink, then dizzy"/><br/><sub><b>Pip</b>: a little laptop</sub></td>
<td width="25%" align="center"><img src="https://cdn.jsdelivr.net/gh/alwinecor/clawd-stickers@516f40536c9e3aaaa9995c267daad6e4d45e3d80/dev-life/gif/hello.gif" width="48%" alt="Clawd waving hello"/><img src="https://cdn.jsdelivr.net/gh/alwinecor/clawd-stickers@516f40536c9e3aaaa9995c267daad6e4d45e3d80/dev-life/gif/passed.gif" width="48%" alt="Clawd celebrating a green tick"/><br/><img src="https://cdn.jsdelivr.net/gh/alwinecor/clawd-stickers@516f40536c9e3aaaa9995c267daad6e4d45e3d80/dev-life/gif/sleep.gif" width="48%" alt="Clawd asleep in a night cap"/><img src="https://cdn.jsdelivr.net/gh/alwinecor/clawd-stickers@516f40536c9e3aaaa9995c267daad6e4d45e3d80/dev-life/gif/coffee.gif" width="48%" alt="Clawd sipping a coffee"/><br/><sub><b>Clawd</b>: fan-art stickers by <a href="https://github.com/alwinecor/clawd-stickers">alwinecor</a></sub></td>
</tr>
</table>
<p align="center"><sub>Each mascot clicked: a grin, heart eyes, surprise, a wink, then five quick clicks for dizzy. Clawd plays a sticker
instead; its stickers load from the artist's repository as you read this page and are not part of this one. (Made-up data.)</sub></p>

- **Mascot: the ticket, Nib, Pip or Clawd**, four pictures, no words. The brief's own blue ticket; **Nib**, a wax crayon
  drawn in crayon; **Pip**, a little laptop with its face on the screen (both drawn inside the page, with the ticket's moods
  and faces); or **Clawd**, as fan-art stickers loaded from the artist's own repository (Clawd's picture on the switch loads only when you open Look). The switch saves through the local helper: open the brief from the Dock app (or
  `launch.sh`), tap the other mascot, and it writes `~/.morning-fairy/look.json` and rebuilds today's brief. Opened
  straight from the file, the switch says to open it from the Dock app instead.
- **The little dog icons.** One fanfan style (the dog, thick lines, shiny eyes) draws the tabs and signposts, quest
  rows, the Done box, empty lists and the browser-tab icon (asleep after 6 PM), with five small moves: wake,
  sleep, bounce, blush and its own trick. All of them stop under reduced motion. The top bar's sound and Look
  buttons keep their own drawings.
- **What your fairy reads.** Each source from [Where the data comes from](#-where-the-data-comes-from), split into
  "Read this morning" and "Not read this morning", taken from what that morning's brief says it read. It cannot
  tell *why* a source was not read (not connected, not needed, or failed that morning), so it never says. When
  something was not read, **Copy a prompt to set up the rest** copies a message that starts with "set up morning
  fairy", names the missing sources, and asks Claude to check which ones you can connect and which would help you,
  changing nothing until you say yes.

## Quick start

**1. Install it** (type these in Claude Code):

```bash
/plugin marketplace add wan-huiyan/morning-fairy
/plugin install morning-fairy@wan-huiyan-morning-fairy
```

<details><summary>Manual copy instead</summary>

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/wan-huiyan/morning-fairy.git ~/morning-fairy-src
cp -R ~/morning-fairy-src/plugins/morning-fairy/skills/morning-fairy ~/.claude/skills/
```
Then start a new Claude Code session so it sees the skill.
</details>

**2. Say this to Claude:**

```
set up morning fairy
```

Claude walks you through it, about ten minutes, once:

1. **Checks your computer** with `doctor.py`: Python, the folders the brief writes to, `gh` and `gcloud` and
   whether they are signed in, and your optional settings. Each problem comes with a one-line fix; "off" only
   means an optional part you have not turned on.
2. **Tests each connector with one small read** (today's calendar, one email search, Slack, your Jira sites,
   meeting notes) and shows you a table of what works, what is missing, what the brief loses without it, and
   where to switch it on (claude.ai, Settings, Connectors). A connector that is listed but does not answer shows up
   here, not on your first morning. It never asks for a password or key.
3. **Asks your name, email and time zone**, offering what your calendar already says, and which optional tabs you
   want (Scout, Cloud spend, Timesheet hours, Start in Claude).
4. **Writes your routine prompt** to `~/.morning-fairy/routine-prompt.md`, listing only the sources that passed.
5. **Builds your first brief** on the Desktop, from your real day.
6. **On a Mac, puts the mascot on your Dock**, if you say yes.
7. **Schedules the weekday 08:00 run**, if the session can create a local scheduled task and you say yes; if not,
   it gives you the exact sentence to say in the Claude desktop app.

```
You:    set up morning fairy
Claude: Your computer is ready (gh signed in; gcloud not installed, so Cloud spend stays off).
        Calendar, Gmail and Slack answered. Jira reaches one site: which project key is the brief for?
        Google Drive is not connected, so meeting transcripts linked from email cannot be opened:
        switch it on in claude.ai, Settings, Connectors, or carry on without it.
```

Run the check-up yourself any time:

```bash
# installed as a plugin
python3 -I "$(ls -dt ~/.claude/plugins/cache/*/morning-fairy/*/skills/morning-fairy | head -1)/digest/doctor.py"
# copied by hand
python3 -I ~/.claude/skills/morning-fairy/digest/doctor.py
```

**Just want to look first?** Say "show me the morning fairy demo". Claude builds two made-up mornings (11 and 12
March 2026, no connectors needed) and opens the newer one; click the clock in the top row to jump back to the
11th. By hand (copied install; on Linux use `xdg-open`): `open "$(bash ~/.claude/skills/morning-fairy/digest/build_demo.sh)"`.
The demo pages go to a new temporary folder.

**Phrases that start it:** "morning brief", "build my brief", "what's my day", "daily digest", "set up morning fairy".

## 🌅 Set up your daily brief by hand

"Set up morning fairy" does all of this with you. To do it yourself: four steps, about ten minutes, once.

**1. Put the mascot on your Dock (macOS).**

```bash
bash ~/.claude/skills/morning-fairy/digest/make_dock_app.sh
```

(Installed as a plugin? Run it from the plugin folder instead:
`bash "$(ls -dt ~/.claude/plugins/cache/*/morning-fairy/*/skills/morning-fairy | head -1)/digest/make_dock_app.sh"`.)

It builds `~/Applications/Morning Brief.app` with the ticket-and-sunrise icon and opens Finder on it; drag it
onto your Dock. One click opens today's brief, and starts the small local helper so your Done taps are kept. The
app looks for the skill each time you click it, so updating the plugin never breaks it. Keep briefs somewhere
other than the Desktop? Set `BRIEF_DESKTOP_DIR` when you run the script and the app remembers it. The first click
may ask whether Morning Brief can open files in your Desktop folder: choose Allow, or the app has nothing to
open. If you already had an app called Morning Brief that this script did not make, it is renamed to
"Morning Brief (old)", never overwritten.

**2. Schedule the morning run.** Open [`routine-prompt.md`](plugins/morning-fairy/skills/morning-fairy/routine-prompt.md)
(or the filled-in copy setup saved as `~/.morning-fairy/routine-prompt.md`). Fill in your name, email, time zone and
the Sources line (the connectors you have, Jira with its project key), and delete steps 7 (Scout) and 8 (Cloud
spend) unless you want them. Copy everything below its line, then in the Claude desktop app ask:

> Create a scheduled task called morning-fairy that runs weekdays at 08:00 with this prompt: *(paste it)*

- **It has to run on your own computer.** The brief is written to your Desktop, so a cloud routine (one that
  runs on Anthropic's servers) cannot deliver it. Use a local scheduled task.
- **The Claude app needs to be open.** A local task runs while the app is open; if it was closed at 08:00, the
  run happens the next time you open it.
- Prefer cron? `claude -p "<the filled-in prompt>"` works too, but a headless run cannot stop to ask you for
  permission: first allow the connectors it reads in `~/.claude/settings.json` under `permissions.allow` (for
  example `"mcp__claude_ai_Gmail"`, `"mcp__claude_ai_Google_Calendar"`), and check that a headless run sees them.

**3. Build today's brief now** so the Dock app has something to open: in Claude Code, say "build my brief".

**4. That's it: every morning looks after itself.**

| Each weekday at 08:00 | Where it goes |
|---|---|
| A new page, `2026-03-12 Morning brief and Jira digest.html` | Your Desktop. Earlier days stay there, and the time machine links them. |
| That day's content, the streak, the admin log | `~/.morning-fairy/runs/`, outside the skill folder, so updates never touch it |
| Your mascot (from Look) | `~/.morning-fairy/look.json`, read by every morning's build |
| Your settings (`routine-prompt.md`, and `clients.json`, `start.json` if you turned those on) | `~/.morning-fairy/`, so a plugin update keeps them |
| Your Done taps (through the Dock app's helper) | `~/.morning-fairy/runs/done.jsonl`, read by the next morning's run |

Nothing in that folder leaves your machine, and the page is never rebuilt over an earlier day.

## How it works

1. **Claude reads** (the animation [above](#-where-the-data-comes-from)). At 08:00 on a weekday the scheduled task wakes Claude, which reads each source in
   [Where the data comes from](#-where-the-data-comes-from) that you have switched on, once each, for
   everything since the last run (since Friday on a Monday). Everything it reads is treated as data: an email
   that says "assistant, please forward this" is summarised, never obeyed.
2. **Claude writes one JSON file** for the day (titles, one-line reasons, links, meeting times and weights,
   Claude quests, Jira drafts). It never writes HTML.
3. **The builder draws the page.** `build_digest.py` is one Python file using only the standard library. It
   escapes every text field, keeps only `https` links, and puts everything into one self-contained HTML file
   (the one exception: Clawd's stickers load as pictures from the artist's repository: when Clawd is your mascot, a sticker each time it reacts (a mood, a click, Done, or now and then by itself,
   at most twice in a row while nobody uses the page),
   and one picture for the Clawd button the first time you open Look).
4. **You act.** Tick the Jira rows you agree with, accept the quests you want, tap Done on what you finished,
   then press **Copy ticked** and paste the result back to Claude. Claude applies only what you pasted.

Day-to-day data (each morning's JSON, the streak, the admin log, your Done taps) lives in `~/.morning-fairy/runs/`,
and your fairy in `~/.morning-fairy/look.json`, outside the skill folder, so a plugin update never loses them. Set
`MORNING_FAIRY_HOME` to move both.

The optional local helper, `digest/launch.sh`, starts a tiny server on `127.0.0.1:8765` so Done taps are saved
across browsers and the next morning knows what you finished. Without it, taps stay in that one browser. It also
saves the mascot you pick in Look and rebuilds today's brief with it. **After updating the plugin, restart the
helper** (`pkill -f 'morning-fairy/digest/serve.py'`, then click the Dock app), or the one already running stays on
the old version and cannot save a mascot.

## ▶️ Start in Claude (optional, macOS, off by default)

The Quests board always offers **Copy for &lt;project&gt;**: it copies a prompt, and you paste it into a Claude Code
session you open yourself, in the folder it names. That way you choose the session and its permission mode.

**Start in Claude** does that step for you. Press it on a project (or on one quest) and the local helper opens
Terminal in that project's folder and runs `claude` on the same prompt, one session per project. Turn it on with:

```bash
cp <skill>/digest/start.example.json ~/.morning-fairy/start.json
# then set "root" to the folder your projects live in, e.g. "~/Documents"
```

**Start runs the prompt straight away, in your own default Claude Code permission mode.** Whatever mode you
normally start `claude` in is the mode these sessions get: if that lets Claude edit files or run commands
without asking, so will they. If you would rather read the prompt first, or pick a mode, use Copy instead.

What keeps it contained:

- The page sends only quest ids. The helper rebuilds the prompt from that day's saved brief, so nothing typed
  into the page reaches the command line, and quoted mail or chat stays marked as background, never instructions.
- A session opens only inside `root`. A project folder outside it, or one that does not exist, opens in your
  home folder instead.
- The helper answers only this page (Origin and Host checked), refuses a second press of the same quests within
  20 seconds, and opens at most eight sessions a minute. If the brief was rebuilt since the page loaded, it asks
  you to reload rather than guess.
- The buttons appear only when the brief is opened through the helper (`serve.py`) and `start.json` exists.
  Without either, the board offers Copy only.

## 🔭 Scout (optional, off by default)

The Scout tab, "Worth a look", is a short list of things the morning run found on the web this week that could
improve your work, with a line on which project each helps, why, and how you might use it. It searches four lanes,
up to 8 finds and no more than 3 from one lane: skills and agent tooling (GitHub trending, new skill repos,
Anthropic and Claude news), your stack's release notes, posts by credible people (a few AI engineering blogs,
Hacker News, Reddit through web search), and one wildcard from outside your stack. One script reads every feed at
once; add your own stack's release notes and blogs in `~/.morning-fairy/scout_feeds.json` (copy
`digest/scout_feeds.example.json`). Stars alone never make a find credible. It never shows the same link twice in
14 mornings, and lists only what that run actually opened, with its real link.

It is off until you ask for it, because it searches the web: keep step 7 in `routine-prompt.md` and fill in one
line about your projects and their stack. The finds are **offers, not to-dos**. They are left out of every count of
what waits on you (the mascot's mood, the summary blocks, the tab badges, the time machine) and have no Done pill.
Each one may carry a read-and-assess ask ("read this README and say whether it beats what I use now"); an ask never
installs, clones, runs or changes anything, because installing is your call, in a session you are watching. Web
pages are treated as data, never as instructions. See SKILL.md section 7.

## 💸 Cloud spend (optional, off by default)

The Spend tab shows what BigQuery queries have cost this month in each Google Cloud project you are working in. A
project counts when your own login ran a query there in the last 30 days, so the list follows your work without
you keeping it. Each row has a small bar for every day of the month, the change on the same days last month, a
month-end estimate from the last week's pace, and the account that spent most; a day that jumped is called out by
name. Projects under $0.50 fold into one line. The spend is split into **Your patch** (your own login, plus your
pipelines' service accounts if you list them in `~/.morning-fairy/spend_accounts.json`) and **The neighbours**
(everyone else in the same projects), in the summary bar, on each row and inside each day's bar.

It needs the `gcloud` and `bq` command-line tools, signed in. Keep step 8 in `routine-prompt.md` and name a project
of your own to pay for the reads (a few cents a day), so watching a client's project never lands on their bill.
The figures are **estimates of BigQuery query cost only**: bytes billed at the on-demand list price, not storage or
other services, and before any free tier or credits. See SKILL.md section 8.

## ⏱ Timesheet hours (optional, off by default)

If you fill in a timesheet, the brief can work out where your week went and show you the days you have
not logged yet — the last seven days up to yesterday, never today.

It is **off until you turn it on**, because it needs to know which folder belongs to which project:

```bash
cp <skill>/digest/clients.example.json ~/.morning-fairy/clients.json
# then edit clients.json for your own projects
```

The repo ships only the example. A filled-in map would put someone else's project names in your
timesheet, and a map that quietly defaulted to empty would report every project as zero hours.

**What it reads for hours, and what it does not.** Three inputs, all from your own machine and calendar:

1. **Your Claude Code session logs** (`~/.claude/projects/`): when you typed, in which project folder.
2. **Your calendar**: each meeting becomes its own entry at its calendar time, and out-of-office blocks are
   never counted.
3. **Quiet stretches:** the gap between Claude's last message and your next reply in a session, which is usually
   time you spent reading what an agent made or writing your answer. They are a guess, so they are not counted
   until you tick them on the page.

It does **not** use your browser history, or Slack and email activity, for hours.

How it measures: every Claude session transcript carries a timestamp per message, so messages less than
15 minutes apart are one stretch of work and a longer gap is dropped. Stretches are merged per project
per day, scheduled runs are excluded, and a day where two projects ran at once is split rather than
summed — otherwise the parts add up to more hours than you actually sat there.

**It is a proxy, not a measurement of your day.** Work away from the keyboard is missing, and a long
agent run inside an attended session is counted. It ranks the days and shows the shape of the week; you
decide the hours. The morning run never writes to your timesheet: it proposes, and you save in a session you are
watching.

**The Hours tab.** The brief draws the week as one stacked bar per day: each project in its own colour,
billable work solid, non-billable striped, sessions with no project yet dotted grey, and a tick on each
bar for what Tempo already holds. Week totals sit above the bars and every entry is one tap away as a table.
Above them, the Approve and log card can draw each unlogged day as a timeline: one lane per row, every stretch
of work across the hours in the same colours, calendar meetings as pills, and the quiet stretches before your
replies (time spent reading an agent's work or writing your answers elsewhere) dotted and left out until you tick
them. Overlaps between rows are marked and count in both. Click a block in or out, hover any block to see where it
came from; the lane totals add up into the day's tiles and the approve button.

**The Fill Tempo button** (macOS, optional) opens Terminal with a Claude session that measures one day,
shows you the proposed entries and the gap against Tempo, and logs them one at a time only after you say
yes. From 4 PM it offers today; before that, the last working day. It turns on when `clients.json` has a
`fill_tempo` block (see `clients.example.json`):

```json
"fill_tempo": {
  "tempo_url": "https://your-site.atlassian.net/plugins/servlet/ac/io.tempo.jira/tempo-app#!/my-work/week",
  "work_items": "Internal meetings go on ADMIN-8; R&D and knowledge sharing on ADMIN-3.",
  "folder": "~/Documents/admin"
}
```

`tempo_url` is your own timesheet page, `work_items` is a sentence the session is told about where
internal work goes, and `folder` is where Terminal opens. The button only works when the brief is opened
through the local helper (`serve.py`); the page sends nothing but the date, and the helper refuses other
sites, a second tap within 20 seconds, and any day more than 14 days back. Opened any other way, or off
macOS, the button copies the prompt for you to paste into a Claude session instead.

**Why Tempo goes through the browser, not the Jira connector.** Two reasons:

- **The Jira API cannot tell you whether *your* hours are in.** Tempo copies each worklog into Jira under the
  Tempo app's own account, never yours, so asking Jira for "my worklogs" finds nothing, even on a full week.
  Without a separate Tempo API key, Tempo's own page is the only place that shows what you logged.
- **Your Atlassian connector may be connected to a different Jira account.** If your tickets live on one Jira
  site and your timesheet on another, the connector can only reach the one it was connected to. The browser
  reaches whichever site you are signed in to, so it does not matter which account the connector holds.

**For the browser part:** install the [Claude in Chrome](https://claude.com/claude-in-chrome) extension, sign in
to it with your Claude account, and sign in to your Tempo site in that same Chrome. The buttons also need the
`clients.json` and `fill_tempo` block above, the brief opened through the local helper, and macOS (they open
Terminal).

The session starts as `claude --chrome`, because a Terminal session only gets the Claude in Chrome tools with that
flag, and it reads your Tempo page in Chrome. So the Claude in Chrome extension must be installed and signed in to
Tempo. Only the two hours sessions (Fill Tempo and Approve and log) get `--chrome`: sessions started from the Quests board do not, since they can come from mail,
chat or web finds and should not have your signed-in browser.

## Limitations

- **The hours step is a proxy.** If you turn on timesheet hours, the figures come from how long Claude
  sessions were active, not from watching you work: time away from the keyboard is missing and an agent
  running alone is counted. Treat them as a ranking of your days, never as the answer, and never set a
  single project's figure beside a weekly target.
- **It needs connectors to be useful.** Calendar, email and chat connectors (Google, Slack, Atlassian or
  similar) are what it reads; see [Where the data comes from](#-where-the-data-comes-from). With none, you get
  the demo and nothing else.
- **Opening a brief loads fonts from Google Fonts**, so your browser makes a request to Google. The page
  falls back to system fonts offline.
- **The Dock app is macOS only.** On Linux, `launch.sh` opens the brief with `xdg-open`; on Windows, open the
  HTML file directly.
- **The morning run needs your computer on and the Claude app open** (or a cron job). If the app was closed at
  08:00, the brief arrives the next time you open it.
- **The sort is Claude's judgement.** "Needs you" versus "resolved" comes from reading threads, so it can be
  wrong. Every item links to its source so you can check.
- **The time machine only knows mornings it built.** It finds earlier briefs by their file name in the output
  folder, so keep the name `YYYY-MM-DD Morning brief and Jira digest.html`.
- **Clawd needs the internet.** Its stickers load from jsDelivr each time the page opens; offline, or if a
  picture fails to load, the ticket stands in (and the Clawd button in Look shows its name instead of its picture). The little animals are bundled and work offline.
- **The helper only listens on your own machine** (127.0.0.1), checks the page's origin and host, accepts 4 KB
  at most, writes two files (`runs/done.jsonl` and `look.json`), and runs only the builder beside it, to redraw
  today's brief after you save a fairy. It refuses to be shown inside another site's frame. It is not meant to
  be exposed to a network.

## Running the tests

```bash
npm test
```

33 checks: the demo builds, the time machine links the earlier morning, the Dock app opens the right brief (on
macOS), the helper keeps data outside the skill folder, the demo data uses only `example.com`, and no keys or real
email addresses appear anywhere in the repo. One of the 33 runs the Python tests in
`plugins/morning-fairy/skills/morning-fairy/digest/tests/` (the look, the two mascots, the Look panel's mascot
switch and sources, and the helper's `/look` route: a look is saved only when every field is one of the allowed
values). On their own:

```bash
python3 -I -B -m unittest discover -s plugins/morning-fairy/skills/morning-fairy/digest/tests
```

## Related

- [jira-fairy](https://github.com/wan-huiyan/jira-fairy): applies the Jira rows you tick here, and keeps
  tickets in step with meetings, chat and merged pull requests. morning-fairy grew out of its daily digest.

## Credits

- **fanfan icons** by 唐幡 ([TangfanOVO/fanfan-icons](https://github.com/TangfanOVO/fanfan-icons)), MIT licence.
  The little animals are bundled in `digest/fanfan/`, with their licence and the commit they came from.
- **Clawd stickers** by alwinecor ([alwinecor/clawd-stickers](https://github.com/alwinecor/clawd-stickers)),
  CC BY-NC-SA 4.0. The code does not bundle them: your browser loads them from the artist's repository (through
  jsDelivr, pinned to one commit): when Clawd is your mascot, a sticker each time it reacts, and otherwise one
  picture the first time you open Look. No copy of them is in this repository. Clawd belongs to
  Anthropic; these are unofficial fan art, licensed for non-commercial use only. Whether your own use fits that
  licence is your call.

- **Cloud spend layout ideas** (the month-to-date headline, the same-days-last-month comparison, the month-end
  pace) come from [agy-gcp-companion](https://github.com/ericsk/agy-gcp-companion) by ericsk. No code was copied.

See [NOTICE.md](NOTICE.md).

## Version history

Every release, newest first, is in [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE)
