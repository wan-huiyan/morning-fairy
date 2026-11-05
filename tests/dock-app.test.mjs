/**
 * make_dock_app.sh builds a working "Morning Brief.app" on macOS, and the app's launcher opens the right thing:
 * today's brief through the installed skill, the briefs folder when nothing is built yet, and the newest file
 * directly when no skill is installed. `open`, `curl` and `python3` are stand-ins, so nothing really opens.
 */
import { describe, it, before } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, symlinkSync, chmodSync, rmSync } from "node:fs";
import { tmpdir, platform } from "node:os";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SKILL = resolve(ROOT, "plugins/morning-fairy/skills/morning-fairy");
const MAKER = resolve(SKILL, "digest/make_dock_app.sh");
const mac = platform() === "darwin";
const NAME = " Morning brief and Jira digest.html";

describe("make_dock_app.sh", { skip: !mac && "builds a macOS app; runs on macOS only" }, () => {
  let t, app, briefs, stubs, log;
  before(() => {
    t = mkdtempSync(join(tmpdir(), "mf-dock-"));
    briefs = join(t, "My Briefs");
    mkdirSync(briefs);
    execFileSync("bash", [MAKER, join(t, "Apps")], { env: { ...process.env, BRIEF_DESKTOP_DIR: briefs, MORNING_FAIRY_NO_REVEAL: "1" }, stdio: "pipe" });
    app = join(t, "Apps", "Morning Brief.app", "Contents");
    stubs = join(t, "bin");
    mkdirSync(stubs);
    log = join(t, "opened.log");
    const stub = (name, body) => { writeFileSync(join(stubs, name), `#!/bin/bash\n${body}\n`); chmodSync(join(stubs, name), 0o755); };
    stub("open", `echo "$*" >> "${log}"`);
    stub("curl", "exit 1");     // the helper is never up
    stub("python3", "exit 0");  // and never really starts
  });
  const click = (home) => {
    rmSync(log, { force: true });
    execFileSync("/bin/bash", [join(app, "MacOS", "launch")], { env: { HOME: home, PATH: `${stubs}:/usr/bin:/bin` }, stdio: "pipe" });
    return existsSync(log) ? readFileSync(log, "utf-8").trim() : "";
  };
  const homeWithPlugin = () => {
    const home = mkdtempSync(join(tmpdir(), "mf-home-"));
    const v = join(home, ".claude/plugins/cache/wan-huiyan-morning-fairy/morning-fairy/1.1.0/skills");
    mkdirSync(v, { recursive: true });
    symlinkSync(SKILL, join(v, "morning-fairy"));
    return home;
  };

  it("makes a valid app with an icon and an executable launcher", () => {
    execFileSync("plutil", ["-lint", join(app, "Info.plist")]);
    assert.ok(existsSync(join(app, "Resources", "icon.icns")));
    execFileSync("bash", ["-n", join(app, "MacOS", "launch")]);
  });
  it("with nothing built yet, opens the briefs folder", () => {
    assert.equal(click(homeWithPlugin()), briefs);
  });
  it("finds a plugin install and opens the newest brief by its date", () => {
    writeFileSync(join(briefs, "2026-03-11" + NAME), "old");
    writeFileSync(join(briefs, "2026-03-12" + NAME), "new");
    assert.equal(click(homeWithPlugin()), join(briefs, "2026-03-12" + NAME));
  });
  it("with no skill installed, still opens the newest brief", () => {
    assert.equal(click(mkdtempSync(join(tmpdir(), "mf-empty-"))), join(briefs, "2026-03-12" + NAME));
  });
  it("moves a different app of the same name aside instead of overwriting it, and rebuilds its own in place", () => {
    const apps = join(t, "Apps2");
    const theirs = join(apps, "Morning Brief.app", "Contents");
    mkdirSync(theirs, { recursive: true });
    writeFileSync(join(theirs, "Info.plist"), '<?xml version="1.0"?><plist version="1.0"><dict><key>CFBundleIdentifier</key><string>com.example.mine</string></dict></plist>');
    const env = { ...process.env, BRIEF_DESKTOP_DIR: briefs, MORNING_FAIRY_NO_REVEAL: "1" };
    execFileSync("bash", [MAKER, apps], { env, stdio: "pipe" });
    assert.match(readFileSync(join(apps, "Morning Brief (old).app", "Contents", "Info.plist"), "utf-8"), /com\.example\.mine/);
    execFileSync("bash", [MAKER, apps], { env, stdio: "pipe" });  // a rebuild of our own app moves nothing
    assert.ok(!existsSync(join(apps, "Morning Brief (old 2).app")));
  });
});
