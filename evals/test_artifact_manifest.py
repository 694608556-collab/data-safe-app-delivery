"""Observable file-integrity and CLI behavior, no real application side effects."""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "artifact_manifest.py"
SPEC = importlib.util.spec_from_file_location("artifact_manifest", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ArtifactManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def make(self, name, content):
        path = self.root / name
        path.write_bytes(content)
        return path

    def test_empty_file(self):
        path = self.make("empty.apk", b"")
        actual = MODULE.fingerprint(path)
        self.assertEqual(actual["bytes"], 0)
        self.assertEqual(actual["sha256"], hashlib.sha256(b"").hexdigest())

    def test_binary_larger_than_buffer_is_complete(self):
        content = bytes(range(256)) * (MODULE.READ_BYTES // 256 * 2 + 7)
        path = self.make("large.ipa", content)
        actual = MODULE.fingerprint(path)
        self.assertEqual(actual["bytes"], len(content))
        self.assertEqual(actual["sha256"], hashlib.sha256(content).hexdigest())

    def test_unicode_and_space_cli_without_source_change(self):
        path = self.make("最终 安装包.apk", b"complete-package\x00\xff")
        before = path.read_bytes()
        mtime = path.stat().st_mtime_ns
        result = subprocess.run([sys.executable, str(SCRIPT), "--", str(path)],
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)["artifacts"][0]
        self.assertEqual(record["path"], str(path.absolute()))
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.stat().st_mtime_ns, mtime)

    def test_all_files_emitted_in_requested_order(self):
        first = self.make("one.apk", b"one")
        second = self.make("two.ipa", b"two")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = MODULE.main([str(first), str(second)])
        self.assertEqual(status, 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data["evidenceType"], "file-identity-only")
        self.assertEqual([x["sha256"] for x in data["artifacts"]],
                         [hashlib.sha256(b"one").hexdigest(),
                          hashlib.sha256(b"two").hexdigest()])

    def test_missing_file_emits_no_partial_success(self):
        first = self.make("valid.apk", b"valid")
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = MODULE.main([str(first), str(self.root / "missing.ipa")])
        self.assertEqual(status, 2)
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(error.getvalue())

    def test_directory_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.fingerprint(self.root)

    def test_symbolic_link_rejected_before_open(self):
        path = self.make("regular.apk", b"keep")
        original = path.lstat()
        class LinkStat:
            st_mode = stat.S_IFLNK | 0o777
        with patch.object(Path, "lstat", return_value=LinkStat()):
            with self.assertRaises(ValueError):
                MODULE.fingerprint(path)
        self.assertEqual(path.read_bytes(), b"keep")
        self.assertEqual(path.lstat().st_mtime_ns, original.st_mtime_ns)

    def test_changed_file_metadata_rejected(self):
        path = self.make("changing.apk", b"content")
        signatures = [(1,), (1,), (1,), (2,)]
        with patch.object(MODULE, "_signature", side_effect=signatures):
            with self.assertRaisesRegex(ValueError, "changed while reading"):
                MODULE.fingerprint(path)

    def test_cli_requires_explicit_files(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")


if __name__ == "__main__":
    unittest.main(verbosity=2)
