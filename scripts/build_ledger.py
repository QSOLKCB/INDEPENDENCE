#!/usr/bin/env python3
"""Build a scoped, source-pinned GitHub repository filename evidence ledger.

Python standard library only. An authenticated GitHub token is recommended.
Never infers 'dependency free' from absent manifest filenames.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

OWNER = "QSOLKCB"
SCHEMA_VERSION = 1
API = "https://api.github.com"
MANIFESTS = frozenset({
    "package.json", "package-lock.json", "npm-shrinkwrap.json", "yarn.lock",
    "pnpm-lock.yaml", "bun.lock", "bun.lockb", "requirements.txt",
    "requirements-dev.txt", "pipfile", "pipfile.lock", "poetry.lock", "uv.lock",
    "pyproject.toml", "setup.py", "composer.json", "composer.lock",
    "gemfile", "gemfile.lock", "cargo.toml", "cargo.lock", "go.mod", "go.sum",
    "pom.xml", "build.gradle", "build.gradle.kts", "gradle.lockfile",
    "packages.lock.json", "pubspec.yaml", "pubspec.lock", "deno.json",
    "deno.jsonc", "deno.lock", "mix.exs", "mix.lock",
})
CONTAINERS = frozenset({
    "dockerfile", "compose.yml", "compose.yaml", "docker-compose.yml",
    "docker-compose.yaml", "chart.yaml", "kustomization.yaml",
})
VENDORED_DIRS = frozenset({"node_modules", ".venv", "vendor"})
MAX_PATH_SAMPLES = 30
CATALOG_PATTERN = re.compile(
    r'\{\s*name:\s*"([^"]+)",\s*category:\s*"([^"]+)",\s*description:\s*"[^"]*"\s*\}'
)


class GitHubClient:
    def __init__(self, token: str = ""):
        self.token = token

    def get(self, path: str):
        if not path.startswith("/") or "://" in path:
            raise ValueError("GitHub API path must be absolute and relative to host")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "QSOL-IMC-Independence-Evidence-Ledger",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(API + path, headers=headers)
        with urlopen(request, timeout=25) as response:
            return json.load(response)

    def get_text(self, owner: str, repo: str, filename: str) -> str:
        payload = self.get(
            "/repos/" + quote(owner, safe="") + "/" + quote(repo, safe="") +
            "/contents/" + quote(filename, safe="/")
        )
        if payload.get("encoding") != "base64":
            raise ValueError("unsupported content encoding")
        return base64.b64decode(payload["content"], validate=False).decode("utf-8")


def summarize_tree(tree: dict) -> dict:
    if not isinstance(tree, dict) or not isinstance(tree.get("tree"), list):
        raise ValueError("missing recursive tree response")
    manifests, containers, workflows = [], [], []
    vendored = 0
    files = 0
    for item in tree["tree"]:
        if item.get("type") != "blob":
            continue
        path = item.get("path", "")
        if not isinstance(path, str):
            raise ValueError("non-string path")
        files += 1
        parts = path.lower().split("/")
        base = parts[-1]
        if base in MANIFESTS:
            manifests.append(path)
        if base in CONTAINERS or (parts and parts[0] == "charts"):
            containers.append(path)
        if any(p in VENDORED_DIRS for p in parts[:-1]):
            vendored += 1
        if len(parts) == 3 and parts[0:2] == [".github", "workflows"] and base.endswith((".yml", ".yaml")):
            workflows.append(path)
    manifests.sort()
    containers.sort()
    workflows.sort()
    truncated = bool(tree.get("truncated"))
    sha = tree.get("sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("invalid Git tree SHA")
    return {
        "state": "truncated" if truncated else "scanned",
        "tree_sha": sha,
        "files_seen": files,
        "manifest_count": len(manifests),
        "manifest_paths": manifests[:MAX_PATH_SAMPLES],
        "manifest_paths_omitted": max(0, len(manifests) - MAX_PATH_SAMPLES),
        "container_marker_count": len(containers),
        "container_marker_paths": containers[:MAX_PATH_SAMPLES],
        "vendored_file_count": vendored,
        "workflow_count": len(workflows),
    }


def curated_categories(source: str) -> dict[str, str]:
    pairs = CATALOG_PATTERN.findall(source)
    mapping = {}
    for name, category in pairs:
        if name in mapping:
            raise ValueError("duplicate curated catalogue entry: " + name)
        mapping[name] = category
    if not mapping:
        raise ValueError("curated catalogue is empty or unparseable")
    return mapping


def receipt_hash(document: dict) -> str:
    payload = {k: v for k, v in document.items() if k != "receipt_sha256"}
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def collection(client, as_of: str, owner: str = OWNER) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", as_of):
        raise ValueError("as-of must be YYYY-MM-DD")
    datetime.strptime(as_of, "%Y-%m-%d")
    discovered = {}
    page = 1
    while True:
        if page > 100:
            raise RuntimeError("repository pagination exceeded safety limit")
        result = client.get(
            "/orgs/" + quote(owner, safe="") +
            "/repos?type=public&sort=full_name&direction=asc&per_page=100&page=" + str(page)
        )
        if not isinstance(result, list):
            raise ValueError("GitHub repository list is not an array")
        for repo in result:
            if repo.get("private") or repo.get("visibility") not in (None, "public"):
                continue
            name = repo.get("name", "")
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or repo.get("owner", {}).get("login", "").lower() != owner.lower():
                raise ValueError("invalid repository owner/name")
            if name in discovered:
                raise ValueError("duplicate repository in stable pagination: " + name)
            discovered[name] = repo
        if len(result) < 100:
            break
        page += 1
    if not discovered:
        raise RuntimeError("GitHub returned zero public repositories; refusing empty success")

    category_state = "available"
    try:
        catalog = curated_categories(client.get_text(owner, "QSOL-IMC", "app.js"))
    except (HTTPError, URLError, ValueError, KeyError, UnicodeError) as error:
        catalog = {}
        category_state = "unavailable:" + type(error).__name__
    context_date = None
    try:
        context_doc = json.loads(client.get_text(owner, "QSOL-CONTEXT", "manifest.json"))
        if isinstance(context_doc, dict):
            value = context_doc.get("snapshot_date")
            if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                context_date = value
    except (HTTPError, URLError, ValueError, KeyError, UnicodeError):
        pass  # Optional metadata. Do not ingest private personal/project records.

    rows = []
    for name in sorted(discovered, key=lambda value: (value.casefold(), value)):
        repo = discovered[name]
        branch = repo.get("default_branch")
        if not isinstance(branch, str) or not branch:
            scan = {"state": "unavailable", "reason": "no_default_branch"}
        else:
            try:
                path = "/repos/" + quote(owner, safe="") + "/" + quote(name, safe="") + \
                    "/git/trees/" + quote(branch, safe="") + "?recursive=1"
                scan = summarize_tree(client.get(path))
            except HTTPError as error:
                scan = {"state": "unavailable", "reason": "http_" + str(error.code)}
            except (URLError, ValueError, KeyError, TimeoutError, OSError) as error:
                scan = {"state": "unavailable", "reason": type(error).__name__}
        rows.append({
            "name": name,
            "url": "https://github.com/" + owner + "/" + name,
            "branch": branch,
            "archived": bool(repo.get("archived")),
            "fork": bool(repo.get("fork")),
            "category": catalog.get(name),
            "scan": scan,
        })

    scanned = [r for r in rows if r["scan"]["state"] == "scanned"]
    document = {
        "schema_version": SCHEMA_VERSION,
        "as_of": as_of,
        "scope": "GitHub public repositories belonging to " + owner,
        "method": "GitHub REST org listing with explicit pagination and recursive default-branch git trees",
        "sources": {
            "repositories": "https://github.com/orgs/" + owner + "/repositories",
            "catalog": "https://github.com/" + owner + "/QSOL-IMC/blob/main/app.js",
            "context": "https://github.com/" + owner + "/QSOL-CONTEXT/blob/main/manifest.json",
        },
        "references": {
            "catalogue_status": category_state,
            "context_manifest_snapshot_date": context_date,
            "context_policy": "Only manifest snapshot date is used; no personal context is published.",
        },
        "coverage": {
            "total": len(rows),
            "scanned": len(scanned),
            "unknown": len(rows) - len(scanned),
            "with_manifest_signals": sum(r["scan"]["manifest_count"] > 0 for r in scanned),
            "without_manifest_signals": sum(r["scan"]["manifest_count"] == 0 for r in scanned),
            "catalogued": sum(r["category"] is not None for r in rows),
        },
        "limitations": [
            "No manifest filename observed does not establish zero dependencies.",
            "Manifest files may describe tooling, optional or standard-library-only packages.",
            "Recursive tree truncation, access errors and missing branches count as unknown.",
            "Import graphs, binary provenance, tests, runtime downloads and vulnerabilities are not assessed.",
            "Git tree SHA identifies the inspected tree; this is not a signed attestation.",
            "This point-in-time public listing may change after collection.",
        ],
        "repositories": rows,
    }
    document["receipt_sha256"] = receipt_hash(document)
    return document


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "ledger" / "data.json")
    args = parser.parse_args(argv)
    try:
        document = collection(GitHubClient(os.environ.get("GITHUB_TOKEN", "")), args.as_of)
        data = json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data, encoding="utf-8")
    except (ValueError, HTTPError, URLError, OSError, RuntimeError) as error:
        print("Ledger collection failed: " + str(error), file=sys.stderr)
        return 1
    print("Ledger:", document["coverage"], "SHA-256:", document["receipt_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
