"""No dependency/remote API: original archive preservation and adversarial fixtures."""
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import verify_browser_archive as archive


class BrowserArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = archive.reconstruct(ROOT)
        with zipfile.ZipFile(io.BytesIO(cls.original)) as z:
            cls.members = {name: z.read(name) for name in z.namelist()}

    def test_lossless_reconstruction_from_git_fragments(self):
        self.assertEqual(len(self.original), 6182)
        self.assertEqual(archive.sha256(self.original), archive.ZIP_SHA256)
        self.assertEqual(archive.verify_archive(self.original)['recorded_pass'], 92)

    def test_original_git_blob_chunks_are_pinned(self):
        for number, expected in enumerate(archive.PART_HASHES, 1):
            path = ROOT / archive.ARCHIVE_DIR / 'base64' / f'part-{number:02d}.b64'
            self.assertEqual(archive.git_blob_sha(path.read_bytes()), expected)

    def test_archive_owns_exact_four_original_member_bytes(self):
        self.assertEqual(set(self.members), set(archive.MEMBER_HASHES))
        for name, data in self.members.items():
            self.assertEqual(hashlib.sha256(data).hexdigest(), archive.MEMBER_HASHES[name])

    def test_cli_restore_recreates_byte_identical_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'source-browser-evidence.zip'
            self.assertEqual(archive.main(['--root', str(ROOT), '--restore', str(target)]), 0)
            self.assertEqual(target.read_bytes(), self.original)
            self.assertEqual(archive.main(['--root', str(ROOT), '--restore', str(target)]), 1)

    def test_altered_zip_bytes_fail_before_any_status_claim(self):
        wrong = bytearray(self.original)
        wrong[10] ^= 1
        with self.assertRaisesRegex(archive.ArchiveError, 'ZIP SHA-256'):
            archive.verify_archive(bytes(wrong))

    def test_wrong_or_missing_members_fail_closed(self):
        for change in ('missing', 'extra'):
            other = dict(self.members)
            if change == 'missing':
                other.pop('firefox-narrow.json')
            else:
                other['fake.json'] = b'{}'
            with self.subTest(change=change), self.assertRaisesRegex(archive.ArchiveError, 'browser report'):
                archive.verify_records(other)

    def test_member_substitution_and_forged_status_fail_closed(self):
        original = self.members['real-browser-evidence.json']
        for field, value in (('source_revision', 'a' * 40),
                             ('site_tree_sha256', 'b' * 64),
                             ('actual_browser', 'FIREFOX_LOCAL_EXECUTED_PASS')):
            doc = json.loads(original)
            doc[field] = value
            changed = dict(self.members)
            changed['real-browser-evidence.json'] = json.dumps(doc).encode()
            with self.subTest(field=field), self.assertRaises(archive.ArchiveError):
                archive.verify_records(changed)

    def test_duplicate_nonfinite_and_false_browser_pass_rejected(self):
        original = self.members['real-browser-evidence.json']
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}'):
            with self.assertRaises(archive.ArchiveError):
                archive.strict_json(raw)
        doc = json.loads(original)
        doc['runs'][0]['checks'][1]['status'] = 'FAIL'
        altered = json.dumps(doc).encode()
        changed = dict(self.members)
        changed['real-browser-evidence.json'] = altered
        with self.assertRaises(archive.ArchiveError):
            archive.verify_records(changed)

    def test_pr_checkout_is_not_later_release_commit(self):
        self.assertNotEqual(archive.SOURCE_REVISION, archive.PR_HEAD)
        self.assertNotEqual(archive.SOURCE_REVISION,
                            '764aec4bda8381de2aed620037d5ff992dba25ea')
        summary = archive.verify_archive(self.original)
        self.assertEqual(summary['execution_attestation'], 'NOT_INDEPENDENTLY_ESTABLISHED')

    def test_corrupt_fragment_rejected_before_zip_decode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / archive.ARCHIVE_DIR / 'base64'
            folder.mkdir(parents=True)
            for i in range(1, 10):
                name = f'part-{i:02d}.b64'
                (folder / name).write_bytes((ROOT / archive.ARCHIVE_DIR / 'base64' / name).read_bytes())
            part = folder / 'part-01.b64'
            part.write_bytes(b'A' + part.read_bytes()[1:])
            with self.assertRaisesRegex(archive.ArchiveError, 'fragment content changed'):
                archive.reconstruct(root)

if __name__ == '__main__':
    unittest.main()
