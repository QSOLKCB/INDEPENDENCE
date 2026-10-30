#!/usr/bin/env python3
"""v1.0.1: verify or restore ORIGINAL PR-run browser evidence (Python stdlib).

Pinnned digest establishes byte identity only; it cannot attest that a browser
actually ran or convert PR-checkout evidence into release/deployment evidence.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = Path('formal/evidence/browser/v1.0.1')
ZIP_SHA256 = '76514017982d86c95003bd4f86ccdcf4404502ede4609ba8f7767b89ee6c396a'
SOURCE_REVISION = '9f5616aa76d1dd18448b8e0d1300f7c6eb43d3b3'
PR_HEAD = '63553a4118dea389547fdf5b821f9e04a50b9dd5'
TREE_SHA256 = 'd0350fe0b9123a3f4a21766e84122e9299de2872a3baa7a4a123226a6e473d62'
MAX_ZIP = 100000
MAX_MEMBER = 20000
PART_HASHES = (
    '496811803e1c4631bd0a3f7784f2b145cce13729',
    '16c8dc4ce7c718ea48d5d3d7da9e6373ea0c3188',
    '60dfedb5acfa3bd75028c78385189647572ec678',
    '5f8d2f6c67b394af5752177af9a4d771811214fd',
    'faa85a03c33537ca6da2d38b0f0b1ea420f95b92',
    'f55008a5bc4599547619e9f51ca78e65ac9f47d9',
    'dbc938b48f04c18ba1b71aa91f81834e2d948e29',
    '677f74208e9cb4e6f2ce684ca17acfc7411e3c39',
    '19068d4a36a69af0cf108e8d0ee1bf5d61e9a74e',
)
MEMBER_HASHES = {
    'real-browser-evidence.json': '00382bb58b3e3ac94853bbcb8ed4e5a0f43d9a5ea76e65b43ce1080a0dedb3b8',
    'chromium-narrow.json': '06a2269ccd7ecd3050fabbc58e89c01200dc8053175069434d6d338182cb6c19',
    'firefox-browser-evidence.json': 'a07be87d6fefe4915e0d387874b2d91b4a0f226d94d8a9dc53ea1a136f036087',
    'firefox-narrow.json': 'e9f3a076a1e53e74d91f7ed0f91650d35d16a55d55476bede29ae22d5162f29f',
}
MODES = {
    'real-browser-evidence.json': ('CHROMIUM_LOCAL_EXECUTED_PASS', ('normal', 'http503', 'malformed'), 1280, 1249),
    'chromium-narrow.json': ('CHROMIUM_LOCAL_EXECUTED_PASS', ('normal',), 390, 469),
    'firefox-browser-evidence.json': ('FIREFOX_LOCAL_EXECUTED_PASS', ('normal', 'http503', 'malformed'), 1280, 1252),
    'firefox-narrow.json': ('FIREFOX_LOCAL_EXECUTED_PASS', ('normal',), 390, 472),
}
SHARED = frozenset({
    'real document loaded with application script',
    'ledger fetch completed rather than hanging',
    'accessible headings/landmarks and unique IDs',
    'form labels and button accessible names',
    'viewport is not catastrophically horizontally clipped',
    'real CSP blocks inline code',
    'real page has no cross-origin runtime resource requests',
})
NORMAL = SHARED | {
    'real packaged ledger rendered',
    'ledger search changes and restores actual rendered results',
    'automaton deterministic replay',
    'real first-party browser self tests',
    'real 4096-vector formal browser lab and WebCrypto receipt',
    'real property laboratory executed',
    'real workflow handoff built locally',
}


class ArchiveError(ValueError):
    pass


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def reconstruct(root: Path = ROOT) -> bytes:
    encoded = []
    for i, expected in enumerate(PART_HASHES, start=1):
        path = root / ARCHIVE_DIR / 'base64' / f'part-{i:02d}.b64'
        if path.is_symlink() or not path.is_file():
            raise ArchiveError('missing/symlink archive fragment: ' + str(path))
        raw = path.read_bytes()
        if len(raw) != (52 if i == len(PART_HASHES) else 1024):
            raise ArchiveError('fragment byte length changed: ' + path.name)
        if git_blob_sha(raw) != expected or re.fullmatch(rb'[A-Za-z0-9+/]+={0,2}', raw) is None:
            raise ArchiveError('fragment content changed: ' + path.name)
        encoded.append(raw)
    try:
        archive = base64.b64decode(b''.join(encoded), validate=True)
    except (ValueError, binascii.Error) as error:
        raise ArchiveError('invalid lossless base64 encoding') from error
    if len(archive) != 6182 or sha256(archive) != ZIP_SHA256:
        raise ArchiveError('reconstructed original ZIP hash mismatch')
    return archive


def reject_pairs(pairs):
    out = {}
    for name, value in pairs:
        if name in out:
            raise ArchiveError('duplicate JSON key: ' + name)
        out[name] = value
    return out


def reject_float(_):
    raise ArchiveError('floating/non-finite JSON number prohibited')


def strict_json(payload: bytes):
    try:
        return json.loads(payload.decode('utf-8'), object_pairs_hook=reject_pairs,
                          parse_float=reject_float, parse_constant=reject_float)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ArchiveError('invalid browser JSON: ' + str(exc)) from exc


def verify_records(members: dict[str, bytes]) -> dict:
    if set(members) != set(MEMBER_HASHES):
        raise ArchiveError('missing, extra or renamed browser report')
    count = 0
    for name, expected_hash in MEMBER_HASHES.items():
        raw = members[name]
        if len(raw) > MAX_MEMBER or sha256(raw) != expected_hash:
            raise ArchiveError('original member bytes differ: ' + name)
        report = strict_json(raw)
        status, modes, requested_width, actual_width = MODES[name]
        if (type(report) is not dict or set(report) != {
                'actual_browser', 'browser_version', 'limitations', 'protocol',
                'requested_viewport', 'runs', 'site_tree_sha256', 'source_revision'}):
            raise ArchiveError('browser report schema mismatch: ' + name)
        if (report['protocol'] != 'REAL-BROWSER-JOURNEYS/1' or
                report['source_revision'] != SOURCE_REVISION or
                report['site_tree_sha256'] != TREE_SHA256 or
                report['actual_browser'] != status or
                type(report['browser_version']) is not str or not report['browser_version'] or
                type(report['limitations']) is not list or not report['limitations']):
            raise ArchiveError('incorrect browser revision, status or provenance: ' + name)
        expected_viewport = {'width': requested_width, 'height': 844 if requested_width == 390 else 900}
        if report['requested_viewport'] != expected_viewport or type(report['runs']) is not list or (
                len(report['runs']) != len(modes)):
            raise ArchiveError('incorrect requested viewport or run inventory: ' + name)
        for run, mode in zip(report['runs'], modes):
            if type(run) is not dict or set(run) != {
                    'checks', 'mode', 'resource_count', 'status', 'stdout_sha256', 'user_agent', 'viewport'}:
                raise ArchiveError('unexpected browser run schema')
            if (run['mode'] != mode or run['status'] != 'PASS' or
                    type(run['resource_count']) is not int or run['resource_count'] < 0 or
                    type(run['user_agent']) is not str or not run['user_agent'] or
                    type(run['stdout_sha256']) is not str or
                    re.fullmatch(r'[a-f0-9]{64}', run['stdout_sha256']) is None or
                    type(run['viewport']) is not dict or
                    type(run['viewport'].get('width')) is not int or
                    run['viewport']['width'] != actual_width):
                raise ArchiveError('browser run status/provenance differs: ' + name + '/' + mode)
            expected_names = NORMAL if mode == 'normal' else SHARED | {
                'controlled ' + mode + ' failure is fail-closed',
                'failed ledger cannot disable other first-party controls',
            }
            checks = run['checks']
            if type(checks) is not list or len(checks) != len(expected_names):
                raise ArchiveError('browser assertion count changed: ' + name)
            seen = []
            for check in checks:
                if type(check) is not dict or set(check) != {'detail', 'name', 'status'} or (
                        check['status'] != 'PASS' or type(check['name']) is not str or
                        type(check['detail']) is not str):
                    raise ArchiveError('browser assertion failed or malformed: ' + name)
                seen.append(check['name'])
            if set(seen) != expected_names or len(seen) != len(set(seen)):
                raise ArchiveError('browser assertions missing, duplicated or substituted: ' + name)
            count += len(checks)
    if count != 92:
        raise ArchiveError('expected exactly 92 recorded assertions')
    return {'protocol': 'BROWSER-ARCHIVE-VERIFICATION/1',
            'archive_sha256': ZIP_SHA256, 'member_count': 4,
            'recorded_checks': count, 'recorded_pass': count,
            'recorded_source_revision': SOURCE_REVISION,
            'staged_tree_sha256': TREE_SHA256,
            'status': 'ORIGINAL_BYTES_AND_INTERNAL_EVIDENCE_VERIFIED_UNATTESTED',
            'execution_attestation': 'NOT_INDEPENDENTLY_ESTABLISHED'}


def verify_archive(data: bytes) -> dict:
    if len(data) != 6182 or len(data) > MAX_ZIP or sha256(data) != ZIP_SHA256:
        raise ArchiveError('original ZIP SHA-256/length differs')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            names = [part.filename for part in entries]
            if len(names) != 4 or set(names) != set(MEMBER_HASHES) or len(set(names)) != 4:
                raise ArchiveError('ZIP member allowlist or uniqueness differs')
            if any(entry.is_dir() or entry.file_size > MAX_MEMBER or
                   entry.compress_size > MAX_ZIP for entry in entries):
                raise ArchiveError('ZIP member size/type invalid')
            members = {part.filename: archive.read(part) for part in entries}
    except (OSError, EOFError, zipfile.BadZipFile, RuntimeError) as error:
        raise ArchiveError('malformed or damaged ZIP') from error
    return verify_records(members)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path,
                        help='check an externally supplied original ZIP instead of built-in fragments')
    parser.add_argument('--restore', type=Path,
                        help='write the byte-identical original ZIP (refuses to overwrite)')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        data = args.archive.read_bytes() if args.archive is not None else reconstruct(args.root)
        result = verify_archive(data)
        if args.restore:
            args.restore.parent.mkdir(parents=True, exist_ok=True)
            with args.restore.open('xb') as out:
                out.write(data)
            if sha256(args.restore.read_bytes()) != ZIP_SHA256:
                raise ArchiveError('restored output failed checksum')
            result['restored_to'] = str(args.restore)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
