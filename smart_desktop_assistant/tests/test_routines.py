"""Unit tests for routine automation and multi-step macro execution."""

import unittest
from smart_desktop_assistant.automation.routines import RoutineManager
from smart_desktop_assistant.core.dispatcher import CommandDispatcher

class TestRoutines(unittest.TestCase):

    def setUp(self):
        self.rm = RoutineManager()
        self.dispatcher = CommandDispatcher()

    def test_default_routines(self):
        routines = self.rm.get_all_routines()
        self.assertIn("morning_setup", routines)
        self.assertIn("clean_workspace", routines)
        self.assertIn("dev_session", routines)

    def test_save_and_retrieve_routine(self):
        test_steps = ["check system performance", "what is on my clipboard"]
        self.rm.save_routine("test_unit_macro", test_steps, description="A unit test routine")

        r = self.rm.get_routine("test_unit_macro")
        self.assertIsNotNone(r)
        self.assertEqual(r["steps"], test_steps)

        # Cleanup
        self.rm.delete_routine("test_unit_macro")
        self.assertIsNone(self.rm.get_routine("test_unit_macro"))

    def test_routine_execution_dry_run(self):
        res = self.dispatcher.dispatch("run morning routine", dry_run=True)
        self.assertTrue(res.success)
        self.assertTrue(res.dry_run)
        self.assertIn("morning_setup", res.message)

if __name__ == "__main__":
    unittest.main()
