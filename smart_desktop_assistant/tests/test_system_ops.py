"""Unit tests for system diagnostics and hardware monitoring."""

import unittest
from smart_desktop_assistant.automation.system_ops import SystemOperations

class TestSystemOps(unittest.TestCase):

    def test_get_system_stats(self):
        stats = SystemOperations.get_system_stats()
        self.assertIn("cpu_percent", stats)
        self.assertIn("ram", stats)
        self.assertIn("disk", stats)
        self.assertIn("battery", stats)

        # Check disk stats
        disk = stats["disk"]
        self.assertGreater(disk["total_gb"], 0)
        self.assertGreaterEqual(disk["percent_used"], 0)

    def test_get_top_processes(self):
        procs = SystemOperations.get_top_processes(count=3)
        self.assertIsInstance(procs, list)
        if procs:
            self.assertIn("pid", procs[0])
            self.assertIn("name", procs[0])
            self.assertIn("memory_mb", procs[0])

    def test_kill_process_dry_run(self):
        res = SystemOperations.kill_process("nonexistent_test_proc", dry_run=True)
        self.assertTrue(res["success"])
        self.assertTrue(res["dry_run"])
        self.assertIn("DRY RUN", res["message"])

    def test_clipboard(self):
        test_msg = "smart_assistant_test_token"
        ok = SystemOperations.set_clipboard(test_msg)
        if ok:
            val = SystemOperations.get_clipboard()
            self.assertEqual(val, test_msg)

if __name__ == "__main__":
    unittest.main()
