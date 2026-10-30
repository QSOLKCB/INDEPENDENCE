#!/usr/bin/env python3
"""v1.0 actual Chromium browser journeys against the exact staged Pages artifact.

Uses the installed browser binary and standard-library local HTTP server.
No Node, npm, pip, Playwright, remote tests, fake DOM or browser download.
Missing browser => NOT_RUN and nonzero when --require-browser is supplied.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.parse import urlsplit

from site_bundle import verify

ROOT = Path(__file__).resolve().parent.parent
HARNESS_JS = ROOT / "scripts/browser_harness.js"
PROTOCOL = "REAL-BROWSER-JOURNEYS/1"
MODES = ("normal", "http503", "malformed")


class BrowserError(ValueError):
    pass


class ResultParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.capturing = False
        self.complete = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        args = dict(attrs)
        if tag == "pre" and args.get("id") == "verification-result":
            self.capturing = True
            self.complete = args.get("data-complete") == "yes"

    def handle_data(self, text):
        if self.capturing:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if tag == "pre" and self.capturing:
            self.capturing = False


def harness_html() -> bytes:
    return b"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; frame-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'">
<title>Actual browser verification</title></head><body style="margin:0">
<iframe id="site-frame" title="INDEPENDENCE under verification" width="100%" height="900"></iframe>
<pre id="verification-result">NOT_RUN</pre>
<script type="module" src="/__verification__/harness.js"></script></body></html>"""


def serve(site: Path, mode: str):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kwargs):
            super().__init__(*a, directory=str(site), **kwargs)

        def log_message(self, format, *args):
            return

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/__verification__/harness.html":
                content = harness_html()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            if path == "/__verification__/harness.js":
                content = HARNESS_JS.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/javascript; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            if path == "/ledger/data.json" and mode != "normal":
                body = b"unavailable" if mode == "http503" else b'{"schema_version":1,"repositories":['
                self.send_response(503 if mode == "http503" else 200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    return server


def parse_html(html: str, expected_mode: str) -> dict:
    parser = ResultParser()
    parser.feed(html)
    parser.close()
    if not parser.complete:
        raise BrowserError("browser did not complete the actual JavaScript harness")
    try:
        record = json.loads("".join(parser.parts))
    except (ValueError, RecursionError) as exc:
        raise BrowserError("malformed browser result") from exc
    if (type(record) is not dict or record.get("mode") != expected_mode or
            record.get("status") not in ("PASS", "FAIL") or
            type(record.get("checks")) is not list or not record["checks"]):
        raise BrowserError("incomplete browser result schema")
    if any(type(c) is not dict or c.get("status") not in ("PASS", "FAIL")
           for c in record["checks"]):
        raise BrowserError("malformed browser assertion list")
    return record


def run(site: Path, browser: str, *, require_browser: bool = True, modes=MODES) -> dict:
    staged = verify(site)
    executable = (shutil.which(browser) if browser else
                  next((shutil.which(name) for name in ("chromium", "google-chrome", "chromium-browser")
                        if shutil.which(name)), None))
    report = {
        "protocol": PROTOCOL, "site_tree_sha256": staged["tree_sha256"],
        "source_revision": staged["revision"], "actual_browser": "NOT_RUN",
        "browser_version": None, "runs": [],
        "limitations": [
            "A real headless Chromium executable is used; this is not Firefox, WebKit or a real-device accessibility audit.",
            "Local loopback HTTP is not the remote GitHub Pages CDN or deployment attestation.",
            "CSP and accessibility assertions cover explicit local cases, not all security or WCAG criteria."
        ]
    }
    if not executable:
        report["reason"] = "no installed Chromium/Chrome executable"
        return report
    try:
        version = subprocess.run([executable, "--version"], capture_output=True,
                                 text=True, timeout=15, check=False)
        if version.returncode or not version.stdout.strip():
            raise BrowserError("browser version query failed")
        report["browser_version"] = version.stdout.strip()[:200]
        for mode in modes:
            server = serve(site.resolve(), mode)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with tempfile.TemporaryDirectory(prefix="independence-browser-") as profile:
                    url = ("http://127.0.0.1:" + str(server.server_address[1]) +
                           "/__verification__/harness.html?mode=" + mode)
                    command = [executable, "--headless=new", "--no-sandbox",
                               "--disable-gpu", "--disable-dev-shm-usage",
                               "--disable-background-networking", "--no-first-run",
                               "--no-default-browser-check", "--disable-extensions",
                               "--user-data-dir=" + profile, "--window-size=1280,900",
                               "--virtual-time-budget=25000", "--dump-dom", url]
                    process = subprocess.run(command, capture_output=True, text=True,
                                             timeout=75, check=False)
                    if process.returncode or len(process.stdout) > 6_000_000:
                        raise BrowserError("actual browser failed: exit=" +
                                           str(process.returncode) + " " + process.stderr[-300:])
                    checked = parse_html(process.stdout, mode)
                    report["runs"].append({
                        "mode": mode, "status": checked["status"],
                        "checks": checked["checks"],
                        "user_agent": checked.get("user_agent", ""),
                        "viewport": checked.get("viewport", {}),
                        "resource_count": checked.get("resource_count", 0),
                        "stdout_sha256": hashlib.sha256(process.stdout.encode()).hexdigest()
                    })
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=5)
        report["actual_browser"] = ("CHROMIUM_LOCAL_EXECUTED_PASS"
                                    if all(r["status"] == "PASS" for r in report["runs"])
                                    else "CHROMIUM_LOCAL_EXECUTED_FAIL")
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        report["actual_browser"] = "CHROMIUM_LOCAL_EXECUTED_FAIL"
        report["reason"] = str(exc)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site", type=Path, required=True)
    ap.add_argument("--browser", default="")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--require-browser", action="store_true")
    args = ap.parse_args(argv)
    try:
        report = run(args.site, args.browser, require_browser=args.require_browser)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                   encoding="utf-8")
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0 if (report["actual_browser"] == "CHROMIUM_LOCAL_EXECUTED_PASS" or
                     (not args.require_browser and report["actual_browser"] == "NOT_RUN")) else 1
    except (OSError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
