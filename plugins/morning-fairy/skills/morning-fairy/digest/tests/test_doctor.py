"""doctor.py: the setup check-up. Read-only, so these tests only look at what it reports, in temp folders of their own."""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import doctor  # noqa: E402


class Settings(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.home, self.code = Path(t.name) / "home", Path(t.name) / "code"
        self.home.mkdir()
        self.code.mkdir()

    def check(self):
        return doctor.check_settings("clients.json", "the Hours tab", "clients", self.home, self.code)

    def test_absent_is_off_and_says_how_to_copy_it_into_the_data_folder(self):
        r = self.check()
        self.assertEqual(r["status"], doctor.OFF)
        self.assertIn(str(self.home / "clients.json"), r["fix"])
        self.assertIn("clients.example.json", r["fix"])

    def test_in_the_data_folder_is_ok(self):
        (self.home / "clients.json").write_text(json.dumps({"clients": []}))
        self.assertEqual(self.check()["status"], doctor.OK)

    def test_beside_the_code_is_flagged_with_the_move(self):
        (self.code / "clients.json").write_text(json.dumps({"clients": []}))
        r = self.check()
        self.assertEqual(r["status"], doctor.WARN)
        self.assertIn("mv", r["fix"])
        self.assertIn(str(self.home / "clients.json"), r["fix"])

    def test_broken_json_needs_fixing(self):
        (self.home / "clients.json").write_text("{nope")
        self.assertEqual(self.check()["status"], doctor.MISSING)

    def test_missing_key_is_a_warning(self):
        (self.home / "clients.json").write_text("{}")
        self.assertEqual(self.check()["status"], doctor.WARN)

    def test_tempo_is_off_without_a_fill_tempo_block(self):
        (self.home / "clients.json").write_text(json.dumps({"clients": []}))
        self.assertEqual(doctor.check_tempo(self.home, self.code)["status"], doctor.OFF)


class Tools(unittest.TestCase):
    def test_gh_missing(self):
        with mock.patch.object(doctor.shutil, "which", return_value=None):
            r = doctor.check_gh()
        self.assertEqual(r["status"], doctor.MISSING)
        self.assertIn("gh auth login", r["fix"])

    def test_gh_signed_in(self):
        with mock.patch.object(doctor.shutil, "which", return_value="/x/gh"), \
             mock.patch.object(doctor, "run", return_value=(0, "Logged in")):
            self.assertEqual(doctor.check_gh()["status"], doctor.OK)

    def test_gh_not_signed_in(self):
        with mock.patch.object(doctor.shutil, "which", return_value="/x/gh"), \
             mock.patch.object(doctor, "run", return_value=(1, "not logged in")):
            self.assertEqual(doctor.check_gh()["status"], doctor.WARN)

    def test_spend_is_off_without_gcloud(self):
        with mock.patch.object(doctor.shutil, "which", return_value=None):
            self.assertEqual(doctor.check_gcloud()["status"], doctor.OFF)

    def test_run_never_raises(self):
        self.assertEqual(doctor.run(["/no/such/tool-xyz"])[0], None)


class Report(unittest.TestCase):
    def test_json_lists_every_check_and_says_whether_ready(self):
        buf = io.StringIO()
        with redirect_stdout(buf), mock.patch.object(doctor, "check_helper",
                                                     return_value=doctor.item("optional", "Local helper", doctor.OFF, "x")):
            code = doctor.main(["--json"])
        out = json.loads(buf.getvalue())
        self.assertIn("ready", out)
        self.assertEqual(code, 0 if out["ready"] else 1)
        names = {c["name"] for c in out["checks"]}
        for n in ("Python", "Data folder", "GitHub CLI (gh)", "clients.json", "start.json", "Tempo buttons"):
            self.assertIn(n, names)

    def test_a_failed_core_check_exits_1(self):
        bad = [doctor.item("core", "Python", doctor.MISSING, "old")]
        with mock.patch.object(doctor, "checks", return_value=bad), redirect_stdout(io.StringIO()):
            self.assertEqual(doctor.main([]), 1)


if __name__ == "__main__":
    unittest.main()
