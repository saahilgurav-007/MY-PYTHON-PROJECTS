"""Unit tests for file operations and automation."""

import shutil
import tempfile
import unittest
from pathlib import Path
from smart_desktop_assistant.automation.file_ops import FileOperations

class TestFileOps(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="assistant_test_"))

        # Create sample files
        (self.test_dir / "invoice.pdf").write_text("dummy invoice", encoding="utf-8")
        (self.test_dir / "photo.png").write_text("dummy image", encoding="utf-8")
        (self.test_dir / "script.py").write_text("print('hello')", encoding="utf-8")
        (self.test_dir / "notes.txt").write_text("meeting notes", encoding="utf-8")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_organize_directory_dry_run(self):
        res = FileOperations.organize_directory(self.test_dir, dry_run=True)
        self.assertTrue(res["success"])
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["total_files"], 4)

        # Files must still be in original root folder in dry run mode
        self.assertTrue((self.test_dir / "invoice.pdf").exists())
        self.assertFalse((self.test_dir / "Documents" / "invoice.pdf").exists())

    def test_organize_directory_execution(self):
        res = FileOperations.organize_directory(self.test_dir, dry_run=False)
        self.assertTrue(res["success"])
        self.assertFalse(res["dry_run"])
        self.assertEqual(res["total_files"], 4)

        # Verify categorization into subfolders
        self.assertTrue((self.test_dir / "Documents" / "invoice.pdf").exists())
        self.assertTrue((self.test_dir / "Documents" / "notes.txt").exists())
        self.assertTrue((self.test_dir / "Images" / "photo.png").exists())
        self.assertTrue((self.test_dir / "Code" / "script.py").exists())

    def test_search_files(self):
        res = FileOperations.search_files(self.test_dir, query="invoice")
        self.assertTrue(res["success"])
        self.assertEqual(res["total_matches"], 1)
        self.assertEqual(res["results"][0]["name"], "invoice.pdf")

        res_ext = FileOperations.search_files(self.test_dir, extension=".py")
        self.assertTrue(res_ext["success"])
        self.assertEqual(res_ext["total_matches"], 1)
        self.assertEqual(res_ext["results"][0]["name"], "script.py")

    def test_batch_rename(self):
        res = FileOperations.batch_rename(self.test_dir, prefix="test_", extension=".txt")
        self.assertTrue(res["success"])
        self.assertEqual(res["total_renamed"], 1)
        self.assertTrue((self.test_dir / "test_notes.txt").exists())
        self.assertFalse((self.test_dir / "notes.txt").exists())

if __name__ == "__main__":
    unittest.main()
