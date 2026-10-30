"""README release/publication badge contract; no network or new packages."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
DOI = "10.5281/zenodo.23816739"
WORKFLOWS = ("verify.yml", "deploy-pages.yml", "verify-public-pages.yml")


class ReadmePublicationTests(unittest.TestCase):
    def test_doi_and_status_badges_immediately_below_title(self):
        lines = README.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "# THE SOFTWARE DECLARATION OF INDEPENDENCE")
        badges = "\n".join(lines[1:13])
        self.assertIn("https://zenodo.org/badge/DOI/" + DOI + ".svg", badges)
        self.assertIn("https://doi.org/" + DOI, badges)
        self.assertIn("https://img.shields.io/github/v/release/QSOLKCB/INDEPENDENCE", badges)
        self.assertIn("Apache--2.0", badges)

    def test_badged_workflows_really_exist_and_are_marked_manual(self):
        readme = README.read_text(encoding="utf-8")
        for filename in WORKFLOWS:
            with self.subTest(filename=filename):
                path = ROOT / ".github" / "workflows" / filename
                self.assertTrue(path.is_file())
                url = "https://github.com/QSOLKCB/INDEPENDENCE/actions/workflows/" + filename
                self.assertIn("](" + url + ")", readme)
                if filename == "verify.yml":
                    self.assertIn(url + "/badge.svg?branch=main", readme)
                else:
                    self.assertNotIn(url + "/badge.svg?branch=main", readme)
        self.assertIn("Pages deploy (manual)", readme)
        self.assertIn("Published-byte audit (manual)", readme)
        self.assertIn("https://img.shields.io/badge/Pages_deploy-manual-lightgrey", readme)
        self.assertIn("https://img.shields.io/badge/Published_byte_audit-manual-lightgrey", readme)
        self.assertIn("separate HTTPS byte check received 404", readme)
        self.assertIn("That observation is NOT_VERIFIED", readme)

    def test_completed_v110_has_auditable_citation_and_limits(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("Project milestone: v1.1.0 formalisation complete", readme)
        self.assertIn("## Completed project — v1.1.0 research milestone", readme)
        self.assertIn("https://github.com/QSOLKCB/INDEPENDENCE/releases/tag/v1.1.0", readme)
        self.assertIn("doi:10.5281/zenodo.23816739", readme)
        self.assertIn("not a claim of universal software correctness", readme)
        self.assertIn("**Research boundary:**", readme)
        self.assertIn("records `NOT_RUN` unless a real compiler", readme)
        self.assertTrue(
            (ROOT / "formal" / "research" / "v1.1.0" / "FORMALISATION_REPORT.md").is_file()
        )


if __name__ == "__main__":
    unittest.main()
