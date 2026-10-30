"""v0.6 AI–human GitHub workflow: offline structure and safety contracts."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.duplicates = set()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.duplicates.add(a["id"])
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "app.js").read_text(encoding="utf-8")
        cls.core = (ROOT / "workflow/core.js").read_text(encoding="utf-8")
        cls.ui = (ROOT / "workflow/ui.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "workflow/workflow.css").read_text(encoding="utf-8")
        cls.doc = (ROOT / "docs/AI-HUMAN-WORKFLOW.md").read_text(encoding="utf-8")
        cls.parser = Tags()
        cls.parser.feed(cls.html)

    def test_workflow_navigation_and_section(self):
        self.assertIn('href="#workflow"', self.html)
        self.assertRegex(self.html, r'<section id="workflow"')
        self.assertIn('id="workflow-stage-nav"', self.html)
        self.assertIn('id="workflow-stage-detail"', self.html)

    def test_no_duplicate_html_ids(self):
        self.assertEqual(self.parser.duplicates, set())

    def test_old_release_sections_preserved(self):
        for section in ("lab", "evidence", "ledger", "tribunal", "museum", "breeding"):
            with self.subTest(section=section):
                self.assertIn('id="' + section + '"', self.html)

    def test_handoff_inputs_and_buttons_exist(self):
        for key in ("goal", "scope", "excluded", "invariants", "acceptance"):
            self.assertIn('id="workflow-' + key + '"', self.html)
        for action in ("load-example", "build", "copy", "prompt", "builder-status"):
            self.assertIn('id="workflow-' + action + '"', self.html)

    def test_copy_button_starts_disabled(self):
        self.assertRegex(self.html, r'<button id="workflow-copy"[^>]*\bdisabled\b')

    def test_composer_requires_goal_and_size_guard(self):
        self.assertIn('key==="goal" && !trimmed', self.core)
        self.assertIn('value.length>1200', self.core)
        self.assertIn("throw new RangeError", self.core)

    def test_no_model_calls_or_dynamic_code_execution(self):
        for path, source in (("core", self.core), ("ui", self.ui)):
            for forbidden in ("innerHTML", "eval(", "new Function(", "fetch(",
                              "XMLHttpRequest", "localStorage", "sessionStorage"):
                with self.subTest(path=path, forbidden=forbidden):
                    self.assertNotIn(forbidden, source)

    def test_prompt_uses_text_content_and_not_markup(self):
        self.assertIn('output.textContent=current', self.ui)
        self.assertIn('element.textContent=String(content)', self.ui)
        self.assertIn("await navigator.clipboard.writeText(current)", self.ui)

    def test_stale_prompt_invalidates_after_input_changes(self):
        self.assertIn('addEventListener("input",invalidate)', self.ui)
        self.assertIn("copy.disabled=true", self.ui)
        self.assertIn('current=""', self.ui)

    def test_self_acknowledgement_is_not_verification(self):
        self.assertIn("selfReportedOnly:true", self.core)
        self.assertIn("no repository checks were run", self.ui)
        self.assertIn("not literal", self.html)

    def test_exact_public_pr_examples(self):
        for number in range(1, 6):
            with self.subTest(number=number):
                self.assertIn('https://github.com/QSOLKCB/INDEPENDENCE/pull/' +
                              str(number), self.core)

    def test_prompt_preserves_human_authority(self):
        self.assertIn("Do not merge, publish, release, deploy", self.core)
        self.assertIn("exact PR HEAD", self.core)
        self.assertIn("unavailable tooling and skipped checks", self.core)

    def test_site_asset_audit_and_deployment(self):
        audit = (ROOT / "scripts/audit.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        for file in ("workflow/core.js", "workflow/ui.js", "workflow/workflow.css"):
            with self.subTest(file=file):
                self.assertTrue((ROOT / file).is_file())
                self.assertIn('"' + file + '"', audit)
        self.assertIn(
            'cp workflow/core.js workflow/ui.js workflow/workflow.css "$site/workflow/"',
            workflow)
        self.assertIn("mountWorkflow();", self.app)

    def test_no_external_runtime_css_or_script(self):
        self.assertNotIn("@import", self.css)
        self.assertNotRegex(self.css, r"url\s*\(")
        self.assertIn('script-src \'self\'', self.html)
        self.assertIn('connect-src \'self\'', self.html)

    def test_documentation_contains_limitations_and_method(self):
        for phrase in ("not a scientific finding", "Human control",
                       "Fresh HEAD", "Adversarial review", "exact full SHA",
                       "does not guarantee", "does not measure AI coding accuracy"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), self.doc.lower())

    def test_maintains_manual_pages_deployment(self):
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn('github.ref == \'refs/heads/main\'', workflow)
        self.assertIn("python3 -m unittest discover -s tests -v", workflow)
        self.assertIn("python3 scripts/audit.py --json", workflow)


if __name__ == "__main__":
    unittest.main()
