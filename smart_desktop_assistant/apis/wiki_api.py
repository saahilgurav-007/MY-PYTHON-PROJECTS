"""Wikipedia summary API integration."""

import json
import urllib.parse
import urllib.request
from typing import Dict, Any

class WikipediaAPI:
    """Queries official Wikipedia REST API for instant summaries."""

    @staticmethod
    def get_summary(query: str) -> Dict[str, Any]:
        """Fetches a concise Wikipedia summary for the search topic."""
        topic = query.strip()
        if not topic:
            return {"success": False, "message": "Search query is empty."}

        encoded_title = urllib.parse.quote(topic.replace(" ", "_"))
        api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"

        try:
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "SmartDesktopAssistant/1.0 (educational-assistant)"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))

            title = data.get("title", topic)
            extract = data.get("extract", "No extract available.")
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{encoded_title}")

            return {
                "success": True,
                "title": title,
                "extract": extract,
                "url": page_url,
                "message": f"{title}: {extract}\nRead more: {page_url}"
            }
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"success": False, "message": f"No Wikipedia article found for '{topic}'."}
            return {"success": False, "message": f"Wikipedia query error: HTTP {e.code}"}
        except Exception as e:
            return {"success": False, "message": f"Wikipedia query failed: {str(e)}"}
