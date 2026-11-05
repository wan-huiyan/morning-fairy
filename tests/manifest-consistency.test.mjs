/**
 * Manifest Consistency Tests — Pattern B (multi-skill plugin) layout.
 *
 * Assertive checks (no graceful-degradation guards): a missing manifest at the
 * canonical path is a FAILURE, not a skip — that is exactly the layout bug that
 * makes `claude plugin marketplace add` silently mis-register.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const PLUGIN = "morning-fairy";

const marketplaceJsonPath = resolve(ROOT, ".claude-plugin/marketplace.json");
const pluginJsonPath = resolve(ROOT, `plugins/${PLUGIN}/.claude-plugin/plugin.json`);
const skillMdPath = resolve(ROOT, `plugins/${PLUGIN}/skills/${PLUGIN}/SKILL.md`);

function extractFrontmatter(md) {
  const match = md.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  const fields = {};
  for (const line of match[1].split("\n")) {
    const kv = line.match(/^(\w[\w-]*):\s*(.+)/);
    if (kv) fields[kv[1]] = kv[2].trim();
  }
  return fields;
}

describe("layout", () => {
  it("marketplace.json exists at .claude-plugin/marketplace.json", () => {
    assert.ok(existsSync(marketplaceJsonPath), `missing: ${marketplaceJsonPath}`);
  });
  it("plugin.json exists inside plugins/<name>/.claude-plugin/", () => {
    assert.ok(existsSync(pluginJsonPath), `missing: ${pluginJsonPath}`);
  });
  it("SKILL.md exists at plugins/<plugin>/skills/<skill>/SKILL.md", () => {
    assert.ok(existsSync(skillMdPath), `missing: ${skillMdPath}`);
  });
  it("no stale root-level SKILL.md duplicate", () => {
    assert.ok(!existsSync(resolve(ROOT, "SKILL.md")), "root SKILL.md would go stale — only the nested copy is loaded");
  });
});

const marketplace = JSON.parse(readFileSync(marketplaceJsonPath, "utf-8"));
const plugin = JSON.parse(readFileSync(pluginJsonPath, "utf-8"));
const fm = extractFrontmatter(readFileSync(skillMdPath, "utf-8"));

describe("marketplace.json", () => {
  it("has exactly one plugin entry", () => {
    assert.equal(marketplace.plugins.length, 1);
  });
  it("plugins[0].name matches plugin.json name (what users type before the @)", () => {
    assert.equal(marketplace.plugins[0].name, plugin.name);
  });
  it("plugins[0].source points at ./plugins/<name> (never '.' or './')", () => {
    assert.equal(marketplace.plugins[0].source, `./plugins/${plugin.name}`);
    assert.ok(existsSync(resolve(ROOT, marketplace.plugins[0].source)));
  });
  it("marketplace name is owner-prefixed and differs from the plugin name", () => {
    assert.notEqual(marketplace.name, plugin.name);
    assert.ok(marketplace.name.endsWith(plugin.name));
  });
  it("versions agree between marketplace entry and plugin.json", () => {
    assert.equal(marketplace.plugins[0].version, plugin.version);
  });
});

describe("SKILL.md frontmatter", () => {
  it("name matches the plugin name", () => {
    assert.equal(fm.name, plugin.name);
  });
  it("version matches plugin.json", () => {
    assert.equal(fm.version, plugin.version);
  });
  it("has a multi-line trigger-bearing description", () => {
    const md = readFileSync(skillMdPath, "utf-8");
    assert.ok(/description:\s*\|/.test(md), "description should be a YAML block scalar with trigger conditions");
  });
});

describe("the version is bumped everywhere it is recorded", () => {
  it("package.json matches plugin.json", () => {
    const pkg = JSON.parse(readFileSync(resolve(ROOT, "package.json"), "utf-8"));
    assert.equal(pkg.version, plugin.version);
  });
  it("README's Version History has an entry for the current version", () => {
    const readme = readFileSync(resolve(ROOT, "README.md"), "utf-8");
    assert.ok(
      readme.includes(`- **${plugin.version}** (`),
      `README.md has no '- **${plugin.version}** (…)' line — bump the changelog too`
    );
  });
});

describe("README", () => {
  it("never mentions the fake install command", () => {
    const readme = readFileSync(resolve(ROOT, "README.md"), "utf-8");
    assert.ok(!/claude\s+install[- ]skill|claude\s+skill\s+install/.test(readme));
  });
  it("every repo path the README's install block names actually exists", () => {
    const readme = readFileSync(resolve(ROOT, "README.md"), "utf-8");
    const paths = [...readme.matchAll(/\/tmp\/morning-fairy\/(\S+)/g)].map((m) => m[1]);
    assert.ok(paths.length, "the install block should name the skill directory to copy");
    for (const p of paths) {
      assert.ok(existsSync(resolve(ROOT, p)), `README install block names a path that does not exist: ${p}`);
    }
    assert.ok(
      !/git clone \S+ ~\/\.claude\/skills\//.test(readme),
      "cloning the repo root into ~/.claude/skills/ leaves no SKILL.md there"
    );
  });
});
