"""Regression checks for the clone documentation verifier."""
from pathlib import Path
import tempfile
import unittest
from scripts.verify_clean_clone import check_documents


class DocumentationLinks(unittest.TestCase):
    def check(self, link, target=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text(link, encoding="utf-8")
            if target is not None:
                (root / "guide.md").write_text(target, encoding="utf-8")
            return check_documents(root, ["README.md"])

    def test_valid_heading_and_external_link(self):
        result = self.check("[guide](guide.md#try-it) [source](https://example.invalid)", "# Try it\n")
        self.assertEqual(result, {"internal_links": 1, "errors": []})

    def test_missing_file_is_reported(self):
        self.assertIn("missing link target", self.check("[guide](guide.md)")["errors"][0])

    def test_missing_heading_is_reported(self):
        result = self.check("[guide](guide.md#missing)", "# Try it\n")
        self.assertIn("missing heading", result["errors"][0])

    def test_path_outside_repository_is_rejected(self):
        self.assertIn("leaves repository", self.check("[outside](../outside.md)")["errors"][0])


if __name__ == "__main__":
    unittest.main()
