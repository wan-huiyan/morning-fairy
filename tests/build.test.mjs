/**
 * The builder works end to end on the demo, the time machine links the earlier morning, the page keeps
 * the pieces the README promises, and the shipped demo data stays made up.
 */
import { describe, it, before } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync, readdirSync, mkdtempSync, existsSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DIGEST = resolve(ROOT, "plugins/morning-fairy/skills/morning-fairy/digest");

describe("the demo builds", () => {
  let out, today, past;
  before(() => {
    out = mkdtempSync(join(tmpdir(), "morning-fairy-"));
    execFileSync("bash", [resolve(DIGEST, "build_demo.sh"), out], { stdio: "pipe" });
    today = readFileSync(join(out, "2026-03-12 Morning brief and Jira digest.html"), "utf-8");
    past = readFileSync(join(out, "2026-03-11 Morning brief and Jira digest.html"), "utf-8");
  });
  it("writes both mornings", () => {
    assert.ok(today.length > 100000 && past.length > 100000);
  });
  it("today's time machine links the earlier morning by a relative link", () => {
    assert.ok(today.includes('class="streak tm'), "no time machine panel");
    assert.ok(today.includes('href="2026-03-11%20Morning%20brief%20and%20Jira%20digest.html"'), "no link to 11 Mar");
  });
  it("keeps the copy button, Done pills, the quest board and the day scene", () => {
    for (const s of ["data-copy-btn", 'class="dn"', 'id="sec-quests"', 'id="scene"', 'id="stage-data"']) {
      assert.ok(today.includes(s), `missing ${s}`);
    }
  });
  it("escapes plain-text fields (no raw <script from content)", () => {
    const scripts = (today.match(/<script/g) || []).length;
    assert.ok(scripts <= 6, `unexpected number of script tags: ${scripts}`);
  });
  it("the demo never writes inside the repo", () => {
    assert.ok(!existsSync(resolve(DIGEST, "runs")), "build_demo.sh must not create digest/runs/");
  });
});

describe("the helper keeps its data outside the skill folder", () => {
  // a plugin update installs a new versioned folder; data kept inside the old one would vanish from the time machine
  const digestDir = (env) => execFileSync("python3", ["-I", "-B", "-c",
    "import importlib.util,sys;s=importlib.util.spec_from_file_location('s',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(m.DIGEST)",
    resolve(DIGEST, "serve.py")], { env: { PATH: process.env.PATH, HOME: "/home/someone", ...env } }).toString().trim();
  it("defaults to ~/.morning-fairy", () => {
    assert.equal(digestDir({}), "/home/someone/.morning-fairy");
  });
  it("MORNING_FAIRY_HOME overrides it", () => {
    assert.equal(digestDir({ MORNING_FAIRY_HOME: "/data/mf" }), "/data/mf");
  });
});

describe("the shipped demo data is made up", () => {
  const files = [resolve(DIGEST, "example_content.json"), ...readdirSync(resolve(DIGEST, "demo")).map((f) => resolve(DIGEST, "demo", f))];
  it("every link points at example.com", () => {
    for (const f of files) {
      for (const [url] of readFileSync(f, "utf-8").matchAll(/https?:\/\/[^\s"'<>)]+/g)) {
        const host = new URL(url).hostname;
        assert.ok(host === "example.com" || host.endsWith(".example.com"), `${f}: ${url}`);
      }
    }
  });
  it("no email addresses", () => {
    for (const f of files) assert.ok(!/[\w.+-]+@[\w-]+\.[\w.]+/.test(readFileSync(f, "utf-8")), f);
  });
});

describe("no secrets or real addresses anywhere in the repo", () => {
  const walk = (d) => readdirSync(d).flatMap((n) => {
    const p = join(d, n);
    if ([".git", "node_modules"].includes(n)) return [];
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
  const text = walk(ROOT).filter((p) => /\.(md|py|json|jsonl|sh|mjs|yml|svg|html)$/.test(p));
  it("no API keys or tokens", () => {
    for (const p of text) {
      const s = readFileSync(p, "utf-8");
      assert.ok(!/\b(sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[abp]-[A-Za-z0-9-]{10,})/.test(s), p);
    }
  });
  it("no email addresses other than example or noreply ones", () => {
    for (const p of text) {
      if (p.endsWith("build.test.mjs")) continue;
      for (const [m] of readFileSync(p, "utf-8").matchAll(/[\w.+-]+@[\w-]+(\.[\w-]+)+/g)) {
        assert.ok(/example\.|noreply/.test(m) || /@(media|keyframes|supports|container|import|font-face)/.test(m) || /\.(png|svg|js|css)$/.test(m), `${p}: ${m}`);
      }
    }
  });
});
