"""Exercise the tracked-source scanner on a real synthetic Git index."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Privacy(unittest.TestCase):
    def test_private_page_references_are_rejected_without_printing_values(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            shutil.copyfile(ROOT / 'scripts/privacy_check.py', root / 'scripts/privacy_check.py')
            reference = 'page_' + 'a' * 32
            source = root / 'example.txt'
            source.write_text(reference)
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True, capture_output=True)
            subprocess.run(['git', 'add', 'scripts/privacy_check.py', 'example.txt'],
                           cwd=root, check=True, capture_output=True)
            command = [sys.executable, str(root / 'scripts/privacy_check.py')]
            failed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(failed.returncode, 2)
            report = json.loads(failed.stdout)
            self.assertEqual(report['problems'], [
                {'file': 'example.txt', 'reason': 'private cloud Page reference'}])
            self.assertNotIn(reference, failed.stdout + failed.stderr)
            source.write_text('page_REPLACE_WITH_YOUR_PRIVATE_PAGE_ID')
            subprocess.run(['git', 'add', 'example.txt'], cwd=root, check=True, capture_output=True)
            passed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(passed.returncode, 0, passed.stdout)
            self.assertTrue(json.loads(passed.stdout)['ok'])


if __name__ == '__main__':
    unittest.main()
