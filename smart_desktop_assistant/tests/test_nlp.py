"""Unit tests for NLP intent classification and entity extraction."""

import unittest
from smart_desktop_assistant.nlp.intent_types import IntentType, RiskLevel
from smart_desktop_assistant.nlp.intent_classifier import IntentClassifier
from smart_desktop_assistant.nlp.entity_extractor import EntityExtractor

class TestNLP(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.classifier = IntentClassifier()

    def test_file_intents(self):
        r1 = self.classifier.classify("organize my downloads folder")
        self.assertEqual(r1.intent, IntentType.ORGANIZE_FILES)

        r2 = self.classifier.classify("search for files with pdf extension")
        self.assertEqual(r2.intent, IntentType.SEARCH_FILES)

        r3 = self.classifier.classify("clean temporary files")
        self.assertEqual(r3.intent, IntentType.CLEANUP_TEMP)
        self.assertEqual(r3.risk_level, RiskLevel.DESTRUCTIVE)

    def test_system_intents(self):
        r1 = self.classifier.classify("check system performance")
        self.assertEqual(r1.intent, IntentType.SYSTEM_STATS)

        r2 = self.classifier.classify("list running processes")
        self.assertEqual(r2.intent, IntentType.LIST_PROCESSES)

        r3 = self.classifier.classify("take a screenshot")
        self.assertEqual(r3.intent, IntentType.TAKE_SCREENSHOT)

        r4 = self.classifier.classify("lock workstation")
        self.assertEqual(r4.intent, IntentType.LOCK_WORKSTATION)

    def test_api_intents(self):
        r1 = self.classifier.classify("what is the weather in Mumbai")
        self.assertEqual(r1.intent, IntentType.WEATHER_QUERY)
        self.assertEqual(r1.entities.get("location"), "Mumbai")

        r2 = self.classifier.classify("summarize Quantum Computing on wikipedia")
        self.assertEqual(r2.intent, IntentType.WIKI_SUMMARY)
        self.assertIn("quantum computing", r2.entities.get("wiki_topic", "").lower())

        r3 = self.classifier.classify("convert 100 USD to INR")
        self.assertEqual(r3.intent, IntentType.CURRENCY_CONVERT)
        self.assertEqual(r3.entities.get("amount"), 100.0)
        self.assertEqual(r3.entities.get("from_currency"), "USD")
        self.assertEqual(r3.entities.get("to_currency"), "INR")

    def test_routine_intents(self):
        r1 = self.classifier.classify("run morning routine")
        self.assertEqual(r1.intent, IntentType.RUN_ROUTINE)
        self.assertEqual(r1.entities.get("routine_name"), "morning_setup")

        r2 = self.classifier.classify("list all routines")
        self.assertEqual(r2.intent, IntentType.LIST_ROUTINES)

    def test_entity_extraction(self):
        entities = EntityExtractor.extract("remind me to drink water in 10 minutes")
        self.assertEqual(entities.get("duration_seconds"), 600)
        self.assertIn("drink water", entities.get("reminder_message", ""))

        app = EntityExtractor.extract_app_name("please open notepad now")
        self.assertEqual(app, "notepad")

        url = EntityExtractor.extract_url("browse to https://github.com/explore")
        self.assertEqual(url, "https://github.com/explore")

    def test_meta_intents(self):
        r1 = self.classifier.classify("exit")
        self.assertEqual(r1.intent, IntentType.EXIT)

        r2 = self.classifier.classify("help")
        self.assertEqual(r2.intent, IntentType.HELP)

if __name__ == "__main__":
    unittest.main()
