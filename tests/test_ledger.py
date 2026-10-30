"""Offline evidence-ledger tests. No network, npm or third-party test runner."""
import json
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_ledger import (  # noqa: E402
    collection, curated_categories, receipt_hash, summarize_tree,
)


def repository(name, branch="main", archived=False):
    return {
        "name": name, "owner": {"login": "QSOLKCB"}, "private": False,
        "visibility": "public", "default_branch": branch,
        "archived": archived, "fork": False,
    }


def tree(paths, truncated=False, sha="a" * 40):
    return {
        "sha": sha, "truncated": truncated,
        "tree": [{"path": p, "type": "blob"} for p in paths],
    }


class FixtureClient:
    def __init__(self, repos, trees, catalogue="", context=None):
        self.repos = repos
        self.trees = trees
        self.catalogue = catalogue
        self.context = context or {"snapshot_date": "2026-10-30"}

    def get(self, path):
        if path.startswith("/orgs/QSOLKCB/repos?"):
            if path.endswith("page=1"):
                return self.repos
            return []
        for name, result in self.trees.items():
            if path.startswith("/repos/QSOLKCB/" + name + "/git/trees/"):
                if isinstance(result, Exception):
                    raise result
                return result
        raise AssertionError("Unexpected API request: " + path)

    def get_text(self, owner, repo, filename):
        if repo == "QSOL-IMC":
            return self.catalogue
        if repo == "QSOL-CONTEXT":
            return json.dumps(self.context)
        raise AssertionError("Unexpected metadata source")


class EvidenceLedgerTests(unittest.TestCase):
    def test_manifest_and_container_detection_are_signals(self):
        result = summarize_tree(tree([
            "README.md", "package.json", "docs/samples/requirements.txt",
            "Dockerfile", ".github/workflows/tests.yml", "node_modules/lib/a.js",
        ]))
        self.assertEqual(result["state"], "scanned")
        self.assertEqual(result["manifest_count"], 2)
        self.assertEqual(result["manifest_paths"], ["docs/samples/requirements.txt", "package.json"])
        self.assertEqual(result["container_marker_count"], 1)
        self.assertEqual(result["vendored_file_count"], 1)
        self.assertEqual(result["workflow_count"], 1)

    def test_nested_paths_and_case_fold(self):
        result = summarize_tree(tree(["src/Package.JSON", "tools/Dockerfile", "charts/demo/Chart.yaml"]))
        self.assertEqual(result["manifest_count"], 1)
        self.assertEqual(result["container_marker_count"], 2)

    def test_truncated_tree_is_not_certified_clean(self):
        result = summarize_tree(tree(["README.md"], truncated=True))
        self.assertEqual(result["state"], "truncated")
        self.assertEqual(result["manifest_count"], 0)

    def test_bad_tree_is_rejected(self):
        for value in ({"sha": "a" * 40}, tree([], sha="invalid")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    summarize_tree(value)

    def test_curated_catalogue_duplicate_rejected(self):
        source = 'const REPOS = [{ name: "QEC", category: "Research", description: "A" }, ' \
                 '{ name: "QEC", category: "Physics", description: "B" }];'
        with self.assertRaises(ValueError):
            curated_categories(source)

    def test_offline_collection_counts_and_determinism(self):
        client = FixtureClient(
            [repository("Beta"), repository("Alpha")],
            {"Alpha": tree(["package.json"], sha="a" * 40), "Beta": tree(["README.md"], sha="b" * 40)},
            'const REPOS = [{ name: "Alpha", category: "Research", description: "A" }];'
        )
        a = collection(client, "2026-10-30")
        b = collection(client, "2026-10-30")
        self.assertEqual(a, b)
        self.assertEqual([x["name"] for x in a["repositories"]], ["Alpha", "Beta"])
        self.assertEqual(a["coverage"], {
            "total": 2, "scanned": 2, "unknown": 0,
            "with_manifest_signals": 1, "without_manifest_signals": 1, "catalogued": 1,
        })
        self.assertEqual(a["receipt_sha256"], receipt_hash(a))

    def test_tree_unavailable_is_unknown(self):
        client = FixtureClient(
            [repository("Alpha")],
            {"Alpha": HTTPError("https://api.github.com", 409, "empty", {}, None)},
            'const REPOS = [{ name: "Alpha", category: "Research", description: "A" }];'
        )
        result = collection(client, "2026-10-30")
        self.assertEqual(result["coverage"]["unknown"], 1)
        self.assertEqual(result["coverage"]["without_manifest_signals"], 0)
        self.assertEqual(result["repositories"][0]["scan"]["reason"], "http_409")

    def test_truncation_excluded_from_negative_counts(self):
        client = FixtureClient([repository("A")], {"A": tree([], truncated=True)})
        result = collection(client, "2026-10-30")
        self.assertEqual(result["coverage"]["unknown"], 1)
        self.assertEqual(result["coverage"]["without_manifest_signals"], 0)

    def test_missing_branch_is_unknown(self):
        result = collection(FixtureClient([repository("A", branch=None)], {}), "2026-10-30")
        self.assertEqual(result["repositories"][0]["scan"]["reason"], "no_default_branch")

    def test_duplicate_page_entries_fail_closed(self):
        client = FixtureClient([repository("Alpha"), repository("Alpha")], {"Alpha": tree([])})
        with self.assertRaisesRegex(ValueError, "duplicate repository"):
            collection(client, "2026-10-30")

    def test_no_repositories_fail_closed(self):
        with self.assertRaises(RuntimeError):
            collection(FixtureClient([], {}), "2026-10-30")

    def test_invalid_date_rejected(self):
        with self.assertRaises(ValueError):
            collection(FixtureClient([], {}), "2026-02-30")

    def test_receipt_invariant(self):
        report = {"schema_version": 1, "coverage": {"total": 1}}
        token = receipt_hash(report)
        self.assertEqual(token, receipt_hash({**report, "receipt_sha256": "excluded"}))
        report["coverage"]["total"] = 2
        self.assertNotEqual(token, receipt_hash(report))

    def test_api_restriction_stops_additional_tree_requests(self):
        client = FixtureClient(
            [repository("Alpha"), repository("Beta")],
            {
                "Alpha": HTTPError("https://api.github.com", 403, "limited", {}, None),
                "Beta": tree(["package.json"]),
            }
        )
        original = client.get
        calls = []

        def tracked_get(path):
            calls.append(path)
            return original(path)

        client.get = tracked_get
        report = collection(client, "2026-10-30")
        self.assertEqual(report["coverage"]["scanned"], 0)
        self.assertEqual(report["coverage"]["unknown"], 2)
        self.assertEqual(report["repositories"][1]["scan"]["reason"],
                         "api_restriction_stopped_collection")
        self.assertEqual(sum("/git/trees/" in path for path in calls), 1)
        self.assertTrue(report["references"]["collection_stopped_due_to_api_restriction"])

    def test_collector_does_not_read_private_context(self):
        client = FixtureClient(
            [repository("Alpha")], {"Alpha": tree([])},
            'const REPOS = [{ name: "Alpha", category: "Research", description: "A" }];'
        )
        original = client.get_text
        calls = []

        def guarded_get_text(owner, repo, filename):
            calls.append((repo, filename))
            if repo != "QSOL-IMC":
                raise AssertionError("private repository read forbidden")
            return original(owner, repo, filename)

        client.get_text = guarded_get_text
        result = collection(client, "2026-10-30")
        self.assertEqual(result["coverage"]["scanned"], 1)
        self.assertEqual(calls, [("QSOL-IMC", "app.js")])
        self.assertNotIn("context", result["sources"])

    def test_public_only_inventory(self):
        private = repository("PrivateSample")
        private["private"] = True
        private["visibility"] = "private"
        client = FixtureClient(
            [repository("PublicSample"), private],
            {"PublicSample": tree([])}
        )
        report = collection(client, "2026-10-30")
        self.assertEqual([row["name"] for row in report["repositories"]], ["PublicSample"])

    def test_static_browser_deployment_includes_ledger(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        browser = (ROOT / "ledger/ledger.js").read_text(encoding="utf-8")
        self.assertIn('id="ledger"', html)
        self.assertIn("mountLedger();", app)
        self.assertIn("build_ledger.py", workflow)
        self.assertIn("ledger/data.json", workflow)
        self.assertNotIn("api.github.com", browser)
        self.assertNotIn("GITHUB_TOKEN", browser)
        self.assertIn("validReceiptSha(report.receipt_sha256)", browser)
        self.assertIn("validTreeSha(scan.tree_sha)", browser)

    def test_optional_catalogue_network_failure_does_not_block_collection(self):
        for error in (TimeoutError("read timed out"), ConnectionResetError("reset by peer")):
            with self.subTest(error=type(error).__name__):
                client = FixtureClient([repository("Alpha")], {"Alpha": tree(["README.md"])})

                def failed_catalogue(owner, repo, filename):
                    raise error

                client.get_text = failed_catalogue
                report = collection(client, "2026-10-30")
                self.assertEqual(report["coverage"]["scanned"], 1)
                self.assertEqual(report["coverage"]["unknown"], 0)
                self.assertEqual(report["coverage"]["catalogued"], 0)
                self.assertIsNone(report["repositories"][0]["category"])
                self.assertEqual(report["references"]["catalogue_status"],
                                 "unavailable:" + type(error).__name__)
                self.assertEqual(report["receipt_sha256"], receipt_hash(report))

    def test_receipt_hash_is_64_lowercase_hex_digits(self):
        digest = receipt_hash({"schema_version": 1})
        self.assertEqual(len(digest), 64)
        self.assertTrue(all(letter in "0123456789abcdef" for letter in digest))

    def test_seed_snapshot_not_mistaken_for_verified(self):
        data = json.loads((ROOT / "ledger/data.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["coverage"]["total"], len(data["repositories"]))
        self.assertEqual(
            data["coverage"]["unknown"],
            sum(r["scan"]["state"] != "scanned" for r in data["repositories"])
        )
        self.assertEqual(
            len({r["name"] for r in data["repositories"]}), len(data["repositories"])
        )
        for row in data["repositories"]:
            self.assertTrue(row["url"].startswith("https://github.com/QSOLKCB/"))
            self.assertIn(row["scan"]["state"], {"scanned", "truncated", "unavailable", "not_scanned"})


if __name__ == "__main__":
    unittest.main()
