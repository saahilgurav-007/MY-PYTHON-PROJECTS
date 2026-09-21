"""Application launching and web browser automation."""

import os
import subprocess
import webbrowser
from typing import Dict, Any, Optional
from ..config import APP_REGISTRY

class AppOperations:
    """Manages application launching and web browsing."""

    @staticmethod
    def launch_app(app_name: str) -> Dict[str, Any]:
        """Launches a desktop application by registered name or system executable."""
        clean_name = app_name.lower().strip()
        executables = APP_REGISTRY.get(clean_name, [clean_name])

        for exe in executables:
            try:
                # Try os.startfile on Windows first (handles path resolution via PATH)
                os.startfile(exe)
                return {
                    "success": True,
                    "app": app_name,
                    "message": f"Successfully launched {app_name} ({exe})"
                }
            except Exception:
                try:
                    subprocess.Popen(
                        [exe],
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return {
                        "success": True,
                        "app": app_name,
                        "message": f"Launched {app_name} via background process"
                    }
                except Exception:
                    continue

        return {
            "success": False,
            "app": app_name,
            "message": f"Could not launch application '{app_name}'. Is it installed or in PATH?"
        }

    @staticmethod
    def open_url(url: str) -> Dict[str, Any]:
        """Opens a web URL in the system default web browser."""
        target_url = url.strip()
        if not target_url.startswith(("http://", "https://")):
            target_url = f"https://{target_url}"

        try:
            opened = webbrowser.open(target_url, new=2)
            if opened:
                return {
                    "success": True,
                    "url": target_url,
                    "message": f"Opened {target_url} in your default browser."
                }
            return {
                "success": False,
                "url": target_url,
                "message": "Browser failed to launch URL."
            }
        except Exception as e:
            return {"success": False, "url": target_url, "error": str(e)}
