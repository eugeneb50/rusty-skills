"""Tests for rusty-audit and the skill's own structure. Run from this dir:
    python3 -m unittest test_rusty_audit
"""
import importlib.machinery
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
AUDIT = HERE / "rusty-audit"

loader = importlib.machinery.SourceFileLoader("rusty_audit", str(AUDIT))
spec = importlib.util.spec_from_loader("rusty_audit", loader)
ra = importlib.util.module_from_spec(spec)
loader.exec_module(ra)

PROD = """\
use std::fs;
pub fn load(p: &str) -> String {
    let s = fs::read_to_string(p).unwrap();
    let _ = fs::remove_file(p);
    // lean: global lock; upgrade when contention shows in a profile
    // lean: linear scan
    s.clone()
}

#[cfg(test)]
mod tests {
    #[test]
    fn t() { Some(1).unwrap(); }
}
"""


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(AUDIT), *args],
                          capture_output=True, text=True, cwd=cwd)


class Signals(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "src").mkdir()
        (root / "src/lib.rs").write_text(PROD)
        (root / "tests").mkdir()
        (root / "tests/it.rs").write_text("fn x() { None::<u8>.unwrap(); }\n")
        (root / "target").mkdir()
        (root / "target/gen.rs").write_text("fn y() { None::<u8>.unwrap(); }\n")
        self.root = root

    def tearDown(self):
        self.tmp.cleanup()

    def test_counts_production_code_only(self):
        s = ra.signals(self.root)
        self.assertEqual(s["unwrap"], 1)  # cfg(test), tests/, target/ skipped
        self.assertEqual(s["ignored_result"], 1)
        self.assertEqual(s["clone"], 1)
        self.assertEqual(s["files"], 1)

    def test_ledger_flags_markers_without_trigger(self):
        rows = ra.ledger(self.root)
        self.assertEqual(len(rows), 2)
        self.assertEqual([r["no_trigger"] for r in rows], [False, True])

    def test_ratchet_fails_on_increase_and_passes_on_equal(self):
        base = self.root / "baseline.json"
        self.assertEqual(run("ratchet", str(base), str(self.root), "--update").returncode, 0)
        self.assertEqual(run("ratchet", str(base), str(self.root)).returncode, 0)
        (self.root / "src/more.rs").write_text("fn z() { None::<u8>.unwrap(); }\n")
        r = run("ratchet", str(base), str(self.root))
        self.assertEqual(r.returncode, 1)
        self.assertIn("unwrap", r.stdout)

    def test_ratchet_update_lowers_but_never_raises(self):
        base = self.root / "baseline.json"
        run("ratchet", str(base), str(self.root), "--update")
        (self.root / "src/more.rs").write_text("fn z() { None::<u8>.unwrap(); }\n")
        self.assertEqual(run("ratchet", str(base), str(self.root), "--update").returncode, 1)
        self.assertEqual(json.loads(base.read_text())["unwrap"], 1)

    def test_record_appends_a_metrics_line(self):
        for _ in range(2):
            self.assertEqual(run("record", str(self.root)).returncode, 0)
        lines = (self.root / ".rusty/metrics.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["signals"]["unwrap"], 1)


class Clippy(unittest.TestCase):
    def test_counts_each_lint_site_once(self):
        msg = {"reason": "compiler-message", "message": {
            "code": {"code": "clippy::indexing_slicing"},
            "spans": [{"is_primary": True, "file_name": "src/a.rs", "line_start": 3}]}}
        lines = [json.dumps(msg), json.dumps(msg), "not json", json.dumps({"reason": "x"})]
        self.assertEqual(ra.clippy_counts(lines), {"clippy::indexing_slicing": 1})


class SkillStructure(unittest.TestCase):
    """The skill's own SOP: small entry point, no dead or missing guides,
    full coverage of the upstream rule set."""

    def test_entry_point_stays_small(self):
        text = (SKILL / "SKILL.md").read_text()
        self.assertLessEqual(len(text.splitlines()), 200)
        self.assertLessEqual(len(text.encode()), 14_000)

    def test_every_guide_is_routed_and_every_route_exists(self):
        text = (SKILL / "SKILL.md").read_text()
        linked = set(re.findall(r"references/([a-z0-9-]+\.md)", text))
        on_disk = {p.name for p in (SKILL / "references").glob("*.md")}
        self.assertEqual(linked, on_disk)

    def test_guides_stay_within_budget(self):
        for p in (SKILL / "references").glob("*.md"):
            self.assertLessEqual(len(p.read_text().encode()), 24_000, p.name)

    def test_config_templates_parse(self):
        import tomllib
        for p in (SKILL / "references").glob("*.md"):
            text = p.read_text()
            for block in re.findall(r"```toml\n(.*?)```", text, re.S):
                tomllib.loads(block)
            try:
                import yaml
            except ImportError:
                continue
            for block in re.findall(r"```yaml\n(.*?)```", text, re.S):
                yaml.safe_load(block)

    def test_every_upstream_rust_skills_rule_is_covered(self):
        refs = "".join(p.read_text() for p in (SKILL / "references").glob("*.md"))
        ids = (HERE / "upstream-ids.txt").read_text().split()
        missing = [i for i in ids if i not in refs]
        self.assertEqual(missing, [], f"{len(missing)} upstream rules uncovered")


if __name__ == "__main__":
    unittest.main()
