"""Currency conversion and exchange rates API."""

import json
import urllib.request
from typing import Dict, Any

class CurrencyAPI:
    """Queries live foreign exchange rates."""

    @staticmethod
    def convert(amount: float, from_curr: str, to_curr: str) -> Dict[str, Any]:
        """Converts an amount from one currency to another."""
        base = from_curr.upper().strip()
        target = to_curr.upper().strip()

        try:
            url = f"https://open.er-api.com/v6/latest/{base}"
            req = urllib.request.Request(url, headers={"User-Agent": "SmartDesktopAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))

            if data.get("result") != "success":
                return {"success": False, "message": f"Currency data unavailable for {base}."}

            rates = data.get("rates", {})
            rate = rates.get(target)

            if rate is None:
                return {"success": False, "message": f"Target currency '{target}' not supported."}

            converted = round(amount * rate, 2)
            return {
                "success": True,
                "amount": amount,
                "from_currency": base,
                "to_currency": target,
                "rate": rate,
                "converted_amount": converted,
                "message": f"{amount} {base} = {converted:,.2f} {target} (Rate: 1 {base} = {rate:.4f} {target})"
            }
        except Exception as e:
            return {"success": False, "message": f"Currency conversion error: {str(e)}"}
