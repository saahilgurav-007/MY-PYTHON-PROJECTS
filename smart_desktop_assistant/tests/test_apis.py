"""Unit tests for public Web APIs integrations."""

import unittest
from smart_desktop_assistant.apis.weather_api import WeatherAPI
from smart_desktop_assistant.apis.wiki_api import WikipediaAPI
from smart_desktop_assistant.apis.network_api import NetworkAPI
from smart_desktop_assistant.apis.currency_api import CurrencyAPI

class TestAPIs(unittest.TestCase):

    def test_weather_structure(self):
        res = WeatherAPI.get_weather("Delhi")
        # Response should be a dictionary with success boolean and message
        self.assertIn("success", res)
        self.assertIn("message", res)
        if res["success"]:
            self.assertIn("temperature_c", res)
            self.assertIn("condition", res)

    def test_wiki_summary_structure(self):
        res = WikipediaAPI.get_summary("Python (programming language)")
        self.assertIn("success", res)
        self.assertIn("message", res)
        if res["success"]:
            self.assertIn("Python", res.get("title", ""))

    def test_network_diagnostics_structure(self):
        res = NetworkAPI.full_diagnostics()
        self.assertIn("local_ip", res)
        self.assertIn("public_ip", res)
        self.assertIn("message", res)

    def test_currency_conversion_structure(self):
        res = CurrencyAPI.convert(100.0, "USD", "EUR")
        self.assertIn("success", res)
        self.assertIn("message", res)
        if res["success"]:
            self.assertEqual(res["from_currency"], "USD")
            self.assertEqual(res["to_currency"], "EUR")
            self.assertGreater(res["converted_amount"], 0)

if __name__ == "__main__":
    unittest.main()
