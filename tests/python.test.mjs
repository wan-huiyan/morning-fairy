/**
 * The Python tests beside the builder (digest/tests: the look, the three mascots, the "Build your own fairy" picker,
 * and the helper's /fanfan and /look routes), run through unittest so `npm test` and CI cover them.
 * HOME and every data folder point at a fresh temp folder, so nothing can reach your own ~/.morning-fairy or Desktop.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const TESTS = resolve(ROOT, "plugins/morning-fairy/skills/morning-fairy/digest/tests");

describe("python tests (digest/tests)", () => {
  it("all pass, with nothing written outside a temp folder", () => {
    const t = mkdtempSync(join(tmpdir(), "mf-py-"));
    try {
      mkdirSync(join(t, "Desktop"));
      const env = {
        PATH: process.env.PATH,
        HOME: t,
        TMPDIR: t,
        MORNING_FAIRY_HOME: join(t, "mf"),
        BRIEF_DIGEST_DIR: join(t, "mf"),
        BRIEF_DESKTOP_DIR: join(t, "Desktop"),
      };
      const r = spawnSync("python3", ["-I", "-B", "-m", "unittest", "discover", "-s", TESTS], {
        env, encoding: "utf-8", timeout: 300000,
      });
      const report = `${r.stdout || ""}${r.stderr || ""}`;
      assert.equal(r.status, 0, `python3 -m unittest failed:\n${report.slice(-6000)}`);
      const ran = report.match(/Ran (\d+) tests?/);
      assert.ok(ran && Number(ran[1]) >= 50, `expected the whole suite to run:\n${report.slice(-2000)}`);
    } finally {
      rmSync(t, { recursive: true, force: true });
    }
  });
});
