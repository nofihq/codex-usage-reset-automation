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
    def test_auth_backups_are_ignored_and_forced_private_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            shutil.copyfile(ROOT / 'scripts/privacy_check.py', root / 'scripts/privacy_check.py')
            shutil.copyfile(ROOT / '.gitignore', root / '.gitignore')
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True, capture_output=True)
            names = ['auth-backup.json', 'nested/old-auth.json', 'plus.expected.json']
            ignored = subprocess.run(['git', 'check-ignore', '--stdin'], cwd=root,
                                     input='\n'.join(names)+'\n', text=True,
                                     capture_output=True, check=True)
            self.assertEqual(set(ignored.stdout.splitlines()), set(names))
            names.append('UPPER-AUTH.JSON')
            for name in names:
                path = root/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{"fixture":"synthetic"}')
            subprocess.run(['git', 'add', '-f', '.'], cwd=root, check=True, capture_output=True)
            result = subprocess.run([sys.executable, str(root/'scripts/privacy_check.py')],
                                    cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertEqual({row['file'] for row in json.loads(result.stdout)['problems']}, set(names))

    def test_jwt_and_opaque_refresh_values_are_rejected_without_disclosure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'scripts').mkdir()
            shutil.copyfile(ROOT/'scripts/privacy_check.py', root/'scripts/privacy_check.py')
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True, capture_output=True)
            token = '.'.join(('eyJ'+'h'*20, 'p'*24, 's'*24))
            for value in (token, json.dumps({'refresh_token': 'synthetic' * 5})):
                with self.subTest(kind='jwt' if value == token else 'opaque'):
                    (root/'example.txt').write_text(value)
                    subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)
                    result = subprocess.run([sys.executable, str(root/'scripts/privacy_check.py')],
                                            cwd=root, capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(json.loads(result.stdout)['problems'], [
                        {'file': 'example.txt', 'reason': 'possible access credential'}])
                    self.assertNotIn(value, result.stdout + result.stderr)

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
