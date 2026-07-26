import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RepositoryIntegrityTests(unittest.TestCase):
    def test_root_contains_only_authority_orientation_and_build_files(self):
        expected_files = {
            ".gitignore",
            "CONSTITUTION.md",
            "LICENSE-STATUS.md",
            "README.md",
            "pyproject.toml",
        }
        actual_files = {
            path.name for path in ROOT.iterdir() if path.is_file()
        }
        self.assertEqual(actual_files, expected_files)
        self.assertFalse(list(ROOT.glob("README-FAS-*.md")))

    def test_repository_folders_have_declared_roles(self):
        expected_folders = {
            ".github",
            "docs",
            "examples",
            "schemas",
            "src",
            "tests",
        }
        generated_folders = {".ruff_cache", ".pytest_cache", "build", "dist"}
        actual_folders = {
            path.name
            for path in ROOT.iterdir()
            if path.is_dir()
            and path.name != ".git"
            and path.name not in generated_folders
        }
        self.assertEqual(actual_folders, expected_folders)
        for required in (
            ROOT / ".github/workflows/ci.yml",
            ROOT / "docs/README.md",
            ROOT / "docs/architecture",
            ROOT / "docs/compliance",
            ROOT / "docs/governance",
            ROOT / "docs/releases",
        ):
            self.assertTrue(required.exists(), required)

    def test_constitution_is_first_and_linked_from_orientation(self):
        constitution = (ROOT / "CONSTITUTION.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Highest governing document", constitution)
        self.assertIn("Users decide; FORGE follows", constitution)
        self.assertIn("CONSTITUTION.md", readme)
        self.assertLess(
            readme.index("CONSTITUTION.md"),
            readme.index("Approved slicer foundation"),
        )

    def test_architecture_set_matches_implemented_reference_baseline(self):
        implemented_ids = {
            *range(1, 11),
            *range(12, 16),
            *range(18, 37),
        }
        actual_ids = {
            int(path.name[4:7])
            for path in (ROOT / "docs/architecture").glob("FAS-*.md")
        }
        self.assertEqual(actual_ids, implemented_ids)

    def test_reconciliation_is_complete_and_fas_026_is_next(self):
        mapping = json.loads(
            (
                ROOT / "docs/governance/fas-reconciliation-map.json"
            ).read_text(encoding="utf-8")
        )
        historical = [row["historical_id"] for row in mapping["mappings"]]
        canonical = {
            value
            for row in mapping["mappings"]
            for value in row["canonical_ids"]
        }
        self.assertEqual(len(historical), 36)
        self.assertEqual(len(set(historical)), 36)
        self.assertEqual(
            canonical,
            {f"FAS-{number:03d}" for number in range(1, 38)},
        )
        self.assertEqual(mapping["rules"]["next_canonical_id"], "FAS-037")

        register = (
            ROOT / "docs/governance/FORGE-DECISION-REGISTER.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "The next canonical specification is FAS-037",
            register,
        )

    def test_all_json_documents_parse(self):
        json_files = sorted((ROOT / "schemas").rglob("*.json"))
        json_files += sorted((ROOT / "examples").rglob("*.json"))
        json_files.append(
            ROOT / "docs/governance/fas-reconciliation-map.json"
        )
        self.assertGreater(len(json_files), 40)
        for path in json_files:
            with self.subTest(path=path.relative_to(ROOT)):
                json.loads(path.read_text(encoding="utf-8"))

    def test_local_markdown_links_resolve(self):
        pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for path in ROOT.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for target in pattern.findall(text):
                if (
                    "://" in target
                    or target.startswith("#")
                    or target.startswith("mailto:")
                ):
                    continue
                target_path = target.split("#", 1)[0]
                resolved = (path.parent / target_path).resolve()
                with self.subTest(
                    source=path.relative_to(ROOT),
                    target=target,
                ):
                    self.assertTrue(resolved.exists(), resolved)

    def test_v1_audit_does_not_overstate_product_readiness(self):
        audit = (
            ROOT / "docs/governance/FORGE-V1-READINESS-AUDIT.md"
        ).read_text(encoding="utf-8")
        self.assertIn("not yet a complete v1.0 application", audit)
        self.assertIn("Licensing Gate 1", audit)
        self.assertIn("FAS-026", audit)
        self.assertIn("FAS-037", audit)
        self.assertIn("Yes, Print", audit)


if __name__ == "__main__":
    unittest.main()
