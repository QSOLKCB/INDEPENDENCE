#!/usr/bin/env python3
"""INDEPENDENCE-RESEARCH-EVIDENCE/1: strict offline archive+receipt verifier.

Original byte matching and receipt consistency ONLY. Neither SHA-256 nor
tool output independently attests execution, authorship, live CDN correctness
or mathematical refinement of first-party JavaScript. Python stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tarfile

ROOT = Path(__file__).resolve().parent.parent
DIR = Path("formal/research/v1.1.0")
PROTOCOL = "INDEPENDENCE-RESEARCH-EVIDENCE/1"
PINNED = {
    "automata4-proof-archive.tar.gz":
        (3473, "05990c6b614d463e973bdee55b20159b59a37844fe03d81f75927f729de99457",
         "automata4-proof-archive"),
    "INDEPENDENCE-rocq-proof-evidence.tar.gz":
        (3658, "c7a28f450c0cb50df51f16cec6190cbcfef850dcf88042e88911bb6167796d6f",
         "INDEPENDENCE-rocq-proof-evidence"),
}
VECTOR_SHA = "f1ecce4798a35f6642a065a0ffbf87e6bdfcbb30ba0afffb5fb0da69c7c40635"
SPEC_SHA = "8b20b315d0b4c6d967a198fc909c65ce1d22a37261e8f64efb63734dcc6d0522"
LEAN_SRC_SHA = "74cb8349ba99feae805a31b74931cbb8da0d98e2020bb738da95d42198f16b98"
ROCQ_SRC_SHA = "6f814063141fbed564db239c3e5abaf4bdd833e2819889d7a6be005ee937ada1"
BROWSER_SHA = "76514017982d86c95003bd4f86ccdcf4404502ede4609ba8f7767b89ee6c396a"
MAX_BYTES = 100_000
HEX = re.compile(r"^[0-9a-f]{64}$")
LEAN = ("pattern_bounded", "rule_zero_cell", "rule_all_cell",
        "rule_zero_row", "rule_all_row", "rule90_known_row")
ROCQ = ("neighborhood_bounded", "arithmetic_table_cell",
        "arbitrary_width_length", "arbitrary_width_table_length",
        "independent_models_equivalent", "rule_zero_cell", "rule_255_cell",
        "rule_zero_all_widths", "rule_255_all_widths", "rule90_cell_xor",
        "rule90_all_widths", "automata4_model_bridge", "zero_boundary_empty",
        "zero_boundary_singleton", "rule90_known_four")


class EvidenceError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def json_strict(data: bytes):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise EvidenceError("duplicate JSON key: " + key)
            obj[key] = value
        return obj

    def reject_number(_):
        raise EvidenceError("noninteger/nonfinite JSON number")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=reject_number, parse_float=reject_number)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise EvidenceError("invalid evidence JSON: " + str(exc)) from exc


def original_members(data: bytes, expected: dict, name: str):
    length, fixed_sha, rootname = PINNED[name]
    require(len(data) == length and sha(data) == fixed_sha,
            "original archive digest differs: " + name)
    require(type(expected) is dict and set(expected) == {"bytes", "sha256", "members"}
            and expected["bytes"] == length and expected["sha256"] == fixed_sha,
            "manifest attempts to repin original archive")
    expected_members = expected["members"]
    require(type(expected_members) is dict and expected_members,
            "missing tar member inventory")
    members = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for item in tar:
                require(item.isfile() or item.isdir(), "untrusted tar entry type")
                require(item.name == rootname or item.name.startswith(rootname + "/"),
                        "tar entry outside expected root")
                remainder = item.name[len(rootname):].lstrip("/")
                require(".." not in remainder.split("/") and "\\" not in remainder,
                        "unsafe tar path")
                if item.isdir():
                    continue
                require(item.name not in members and 0 <= item.size <= MAX_BYTES,
                        "duplicate or oversized tar member")
                stream = tar.extractfile(item)
                require(stream is not None, "tar member cannot be read")
                body = stream.read(MAX_BYTES + 1)
                require(len(body) == item.size, "truncated tar member")
                members[item.name] = body
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise EvidenceError("unreadable original tar archive") from exc
    require(set(members) == set(expected_members), "tar member allowlist differs")
    for member, body in members.items():
        pin = expected_members[member]
        require(type(pin) is dict and set(pin) == {"bytes", "sha256"}
                and type(pin["bytes"]) is int and pin["bytes"] == len(body)
                and type(pin["sha256"]) is str
                and HEX.fullmatch(pin["sha256"]) is not None
                and sha(body) == pin["sha256"],
                "original tar member digest differs: " + member)
    return members


def verify_sums(members, prefix):
    filename = prefix + "/SHA256SUMS.txt"
    require(filename in members, "missing SHA256SUMS")
    names = set()
    for line in members[filename].decode("utf-8").splitlines():
        pair = line.split("  ", 1)
        require(len(pair) == 2 and HEX.fullmatch(pair[0]) is not None,
                "invalid checksum line")
        checksum, shortname = pair
        require(shortname not in names and "/" not in shortname
                and shortname not in ("", ".", ".."), "duplicate/unsafe checksum name")
        names.add(shortname)
        target = prefix + "/" + shortname
        require(target in members and sha(members[target]) == checksum,
                "internal SHA256SUMS mismatch: " + shortname)
    require(names == {name[len(prefix)+1:] for name in members if name != filename},
            "internal SHA256SUMS omits one or more files")
    return len(names)


def verify_receipts(lean_members, rocq_members):
    lroot = "automata4-proof-archive/"
    rroot = "INDEPENDENCE-rocq-proof-evidence/"
    require(lean_members[lroot + "SOURCE_COMMIT.txt"] ==
            b"764aec4bda8381de2aed620037d5ff992dba25ea\n",
            "AUTOMATA4 source commit provenance changed")
    require(rocq_members[rroot + "SOURCE_COMMIT.txt"] ==
            b"00c093ce56071813b815805c86559b8b4b303cab\n",
            "Rocq proof execution commit provenance changed")
    partial = json_strict(lean_members[lroot + "automata4-lean-spark-evidence.json"])
    full = json_strict(lean_members[lroot + "automata4-complete-evidence.json"])
    rocq = json_strict(rocq_members[rroot + "rocq-executed-evidence.json"])
    for obj in (partial, full):
        require(type(obj) is dict and obj.get("protocol") == "AUTOMATA4-FORMAL-LAB/1"
                and obj.get("finite_cases") == 4096
                and obj.get("reference_status") == "FINITE_ENUMERATION_CHECKED"
                and obj.get("vectors_sha256") == VECTOR_SHA
                and obj.get("spec_sha256") == SPEC_SHA
                and obj.get("lean_source_sha256") == LEAN_SRC_SHA
                and obj.get("independent_execution_attestation") is False,
                "AUTOMATA4 reference/corpus/attestation changed")
        lean = obj.get("lean", {})
        spark = obj.get("spark", {})
        require(type(lean) is dict and lean.get("status") == "KERNEL_CHECKED"
                and lean.get("exit_code") == 0
                and lean.get("command") ==
                    ["lean", "--trust=0", "formal/lean/AutomataReference.lean"]
                and lean.get("axiom_audit") == {name: [] for name in LEAN}
                and sha(lean.get("raw_output", "").encode()) ==
                    lean.get("raw_output_sha256"),
                "Lean kernel/axiom/original-output receipt differs")
        require(type(spark) is dict
                and spark.get("status") == "GNATPROVE_REPORTED_DISCHARGED"
                and spark.get("exit_code") == 0 and spark.get("checks") == 10
                and "Success: all checks proved (10 checks)." in spark.get("raw_output", "")
                and sha(spark.get("raw_output", "").encode()) ==
                    spark.get("raw_output_sha256"),
                "GNATprove contract/output receipt differs")
    require(partial.get("ada") == {"status": "NOT_RUN"}
            and partial.get("javascript") == {"status": "NOT_RUN"},
            "partial receipt falsely promotes executable checks")
    a, j = full.get("ada", {}), full.get("javascript", {})
    require(a.get("status") == "LOCAL_ADA_FINITE_EXECUTED_UNATTESTED"
            and a.get("cases") == 4096 and a.get("invalid_cases") == 10
            and a.get("vectors_sha256") == VECTOR_SHA
            and j.get("status") == "LOCAL_JS_FINITE_EXECUTED"
            and j.get("cases") == 4096 and j.get("vectors_sha256") == VECTOR_SHA,
            "Ada/JS bounded execution receipt differs")
    require(type(rocq) is dict and rocq.get("protocol") == "AUTOMATA-ROCQ/1"
            and rocq.get("source_sha256") == ROCQ_SRC_SHA
            and rocq.get("source_git_blob_sha1") ==
                "15dfdf5925492c5647477d8f2970664bdd827d93"
            and rocq.get("rocq_version_pin") == "9.2.0"
            and rocq.get("independent_execution_attestation") is False
            and sha(rocq_members[rroot+"Automata.v"]) == ROCQ_SRC_SHA,
            "Rocq source/attestation identity differs")
    r = rocq.get("rocq", {})
    audits = r.get("assumption_audit", {})
    require(r.get("status") == "KERNEL_CHECKED" and r.get("exit_code") == 0
            and type(audits) is dict and audits.get("closed_theorems") == 15
            and audits.get("expected_theorems") == 15
            and audits.get("no_extra_axioms_reported") is True
            and rocq.get("theorems") == list(ROCQ)
            and r.get("raw_output", "").count("Closed under the global context") == 15
            and sha(r.get("raw_output", "").encode()) == r.get("raw_output_sha256")
            and type(r.get("compiled_vo_sha256")) is str
            and HEX.fullmatch(r["compiled_vo_sha256"]) is not None,
            "Rocq proof/assumption/compiled digest receipt differs")
    bridge = rocq.get("finite_bridge", {})
    require(bridge.get("status") == "FINITE_BRIDGE_CHECKED"
            and bridge.get("automata4_cases") == 4096
            and bridge.get("canonical_vectors_sha256") == VECTOR_SHA,
            "Rocq finite model bridge differs")
    return {"lean_model_theorems_recorded": 6, "spark_checks_recorded": 10,
            "ada_valid_vectors_recorded": 4096, "ada_invalid_inputs_recorded": 10,
            "javascript_vectors_recorded": 4096, "rocq_model_obligations_recorded": 15,
            "rocq_compiled_vo_sha256_recorded": r["compiled_vo_sha256"]}


def verify(root=ROOT):
    manifest_path = root / DIR / "evidence-manifest.json"
    require(manifest_path.is_file() and not manifest_path.is_symlink(),
            "missing/symlinked evidence manifest")
    manifest = json_strict(manifest_path.read_bytes())
    require(type(manifest) is dict and set(manifest) == {
        "protocol", "report_version", "source_baseline", "zenodo",
        "evidence_archives", "historical_browser_evidence", "scope_policy"},
        "manifest schema differs")
    require(manifest["protocol"] == PROTOCOL and manifest["report_version"] == "1.1.0",
            "wrong report/protocol")
    require(manifest["zenodo"]["doi"] == "10.5281/zenodo.23816739"
            and manifest["zenodo"]["do_not_claim_report_published"] is True,
            "Zenodo publication incorrectly promoted")
    policy = manifest["scope_policy"]
    require(policy.get("independent_execution_attestation") is False
            and policy.get("js_formal_refinement") == "NOT_ESTABLISHED",
            "unsupported independent attestation or refinement claim")
    browser = manifest["historical_browser_evidence"]
    require(browser["zip_sha256"] == BROWSER_SHA
            and browser["original_actions_run_id"] == 41112613136
            and browser["reported_checks"] == 92
            and browser["execution_attestation"] == "NOT_INDEPENDENTLY_ESTABLISHED",
            "historical browser PR-run provenance changed")
    require(set(manifest["evidence_archives"]) == set(PINNED), "archive inventory differs")
    originals = {}
    total = 0
    for name, (_, _, prefix) in PINNED.items():
        path = root / DIR / name
        require(path.is_file() and not path.is_symlink(), "missing/symlink archive: " + name)
        originals[name] = original_members(
            path.read_bytes(), manifest["evidence_archives"][name], name)
        total += verify_sums(originals[name], prefix)
    outcomes = verify_receipts(originals["automata4-proof-archive.tar.gz"],
                               originals["INDEPENDENCE-rocq-proof-evidence.tar.gz"])
    return {
        "protocol": PROTOCOL,
        "status": "ORIGINAL_ARCHIVES_AND_RECEIPTS_INTERNALLY_VERIFIED_UNATTESTED",
        "archives": 2,
        "original_internal_sha256_entries_checked": total,
        "browser_zip_sha256_pinned_not_reexecuted": BROWSER_SHA,
        "independent_execution_attestation": False,
        "zenodo_publication": "NOT_VERIFIED",
        **outcomes
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify(args.root)
        output = json.dumps(result, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        print(output, end="")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print("NOT_VERIFIED: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
