#!/usr/bin/env python3
"""Actual headless Firefox browser journeys via W3C WebDriver, stdlib only.

Requires locally installed Firefox and Geckodriver (developer tools).
Reuses the SAME local, independently scripted site and fault journeys as Chromium.
No Selenium/PyPI/npm and no simulated browser successes.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from run_browser_journeys import MODES, PROTOCOL, BrowserError, parse_html, serve
from site_bundle import verify


def post(url: str, body: dict | None = None, method: str = "POST", timeout: int = 45) -> dict:
    data = json.dumps(body or {}).encode("utf-8") if method == "POST" else None
    req = Request(url, data=data, method=method,
                  headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as response:
            packet = response.read(1_000_000)
        result = json.loads(packet)
        if type(result) is not dict or "value" not in result:
            raise BrowserError("invalid WebDriver JSON envelope")
        if isinstance(result["value"], dict) and "error" in result["value"]:
            raise BrowserError("WebDriver error: " + str(result["value"].get("message", ""))[:300])
        return result
    except (HTTPError, URLError, ValueError) as exc:
        raise BrowserError("WebDriver transport failed: " + str(exc)[:300]) from exc


def available() -> tuple[str | None, str | None]:
    firefox = shutil.which("firefox")
    driver = shutil.which("geckodriver")
    if not driver:
        base = Path(__import__("os").environ.get("GECKOWEBDRIVER", "/"))
        guess = base / "geckodriver"
        if guess.is_file():
            driver = str(guess)
    return firefox, driver


def run(site: Path, *, require_browser: bool = True, modes=MODES) -> dict:
    staged = verify(site)
    firefox, driver = available()
    report = {
        "protocol": PROTOCOL, "site_tree_sha256": staged["tree_sha256"],
        "source_revision": staged["revision"], "actual_browser": "NOT_RUN",
        "browser_version": None, "runs": [],
        "limitations": [
            "Real Firefox and Geckodriver are optional developer tools, not a shipped website dependency.",
            "Local loopback HTTP does not attest deployment to the public GitHub Pages CDN.",
            "These finite journeys are not comprehensive WCAG or browser-security certification."
        ]
    }
    if not firefox or not driver:
        report["reason"] = "Firefox or Geckodriver unavailable"
        return report
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    endpoint = "http://127.0.0.1:" + str(port)
    process = None
    session = None
    phase = "START"
    log_file = None
    try:
        ver = subprocess.run([driver, "--version"], text=True, capture_output=True,
                             check=False, timeout=15)
        if ver.returncode:
            raise BrowserError("geckodriver version query failed")
        log_file = tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
        process = subprocess.Popen([driver, "--port", str(port), "--log", "info"],
                                   stdout=log_file, stderr=subprocess.STDOUT)
        phase = "WAIT_DRIVER_READY"
        for _ in range(100):
            if process.poll() is not None:
                raise BrowserError("geckodriver stopped before readiness")
            try:
                if post(endpoint + "/status", method="GET", timeout=3)["value"].get("ready"):
                    break
            except BrowserError:
                pass
            time.sleep(0.15)
        else:
            raise BrowserError("geckodriver did not become ready")
        phase = "START_FIREFOX_SESSION"
        started = post(endpoint + "/session", {
            "capabilities": {"alwaysMatch": {
                "browserName": "firefox",
                "moz:firefoxOptions": {"args": ["-headless"]}
            }}
        })
        session = started["value"]["sessionId"]
        phase = "SESSION_READY"
        caps = started["value"].get("capabilities", {})
        report["browser_version"] = ("Firefox " + str(caps.get("browserVersion", "unknown")) +
                                     "; " + ver.stdout.strip().split("\n")[0])
        post(endpoint + "/session/" + session + "/window/rect",
             {"width": 1280, "height": 900})
        for mode in modes:
            phase = "RUN_" + mode
            server = serve(site.resolve(), mode)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                target = "http://127.0.0.1:" + str(server.server_address[1]) + (
                    "/__verification__/harness.html?mode=" + mode)
                post(endpoint + "/session/" + session + "/url", {"url": target})
                result = None
                for _ in range(240):
                    output = post(endpoint + "/session/" + session + "/execute/sync", {
                        "script": "const n=document.getElementById('verification-result'); return n && n.dataset.complete==='yes' ? n.textContent : null;",
                        "args": []
                    })["value"]
                    if output is not None:
                        result = parse_html('<pre id="verification-result" data-complete="yes">' +
                                            html.escape(output) + "</pre>", mode)
                        break
                    time.sleep(0.15)
                if result is None:
                    raise BrowserError("Firefox browser harness timed out: " + mode)
                report["runs"].append({
                    "mode": mode, "status": result["status"], "checks": result["checks"],
                    "user_agent": result.get("user_agent", ""),
                    "viewport": result.get("viewport", {}),
                    "resource_count": result.get("resource_count", 0),
                    "stdout_sha256": hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
                })
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
        report["actual_browser"] = ("FIREFOX_LOCAL_EXECUTED_PASS"
                                    if all(r["status"] == "PASS" for r in report["runs"])
                                    else "FIREFOX_LOCAL_EXECUTED_FAIL")
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        report["actual_browser"] = "FIREFOX_LOCAL_EXECUTED_FAIL"
        report["reason"] = phase + ": " + str(exc)
        if log_file:
            try:
                log_file.flush()
                log_file.seek(0)
                report["driver_log_tail"] = log_file.read()[-2500:]
            except (OSError, UnicodeError):
                pass
    finally:
        if session:
            try:
                post(endpoint + "/session/" + session, method="DELETE")
            except (ValueError, OSError):
                pass
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if log_file:
            log_file.close()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-browser", action="store_true")
    args = parser.parse_args(argv)
    try:
        record = run(args.site, require_browser=args.require_browser)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, sort_keys=True, indent=2))
        return 0 if (record["actual_browser"] == "FIREFOX_LOCAL_EXECUTED_PASS" or
                     (not args.require_browser and record["actual_browser"] == "NOT_RUN")) else 1
    except (OSError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
