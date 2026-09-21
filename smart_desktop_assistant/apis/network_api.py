"""Network diagnostic tools: public IP, ping, and DNS resolution."""

import json
import socket
import subprocess
import time
import urllib.request
from typing import Dict, Any

class NetworkAPI:
    """Provides network status, public IP discovery, and ping latency metrics."""

    @staticmethod
    def get_public_ip() -> Dict[str, Any]:
        """Queries public IP via ipify service."""
        try:
            req = urllib.request.Request(
                "https://api64.ipify.org?format=json",
                headers={"User-Agent": "SmartDesktopAssistant/1.0"}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode("utf-8"))
                ip = data.get("ip")
                return {
                    "success": True,
                    "ip": ip,
                    "message": f"Your public IP address is: {ip}"
                }
        except Exception as e:
            return {"success": False, "message": f"Could not determine public IP: {str(e)}"}

    @staticmethod
    def test_latency(host: str = "8.8.8.8") -> Dict[str, Any]:
        """Pings a target host to test connectivity and round-trip latency."""
        try:
            start_t = time.time()
            res = subprocess.run(
                ["ping", "-n", "2", host],
                capture_output=True,
                text=True,
                timeout=5
            )
            elapsed_ms = round((time.time() - start_t) * 1000 / 2, 1)
            is_online = res.returncode == 0

            return {
                "success": is_online,
                "host": host,
                "latency_ms": elapsed_ms if is_online else None,
                "message": (
                    f"Network is ONLINE (Ping to {host}: ~{elapsed_ms} ms)"
                    if is_online else f"Network appears OFFLINE or unreachable ({host})"
                )
            }
        except Exception as e:
            return {"success": False, "message": f"Ping failed: {str(e)}"}

    @staticmethod
    def full_diagnostics() -> Dict[str, Any]:
        """Combines local IP, public IP, and ping status."""
        # Local IP
        local_ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            pass

        ping_result = NetworkAPI.test_latency("8.8.8.8")
        pub_result = NetworkAPI.get_public_ip()

        return {
            "success": ping_result.get("success", False),
            "local_ip": local_ip,
            "public_ip": pub_result.get("ip", "Unavailable"),
            "ping": ping_result.get("latency_ms"),
            "message": (
                f"Network Status: {'Online' if ping_result.get('success') else 'Offline'} | "
                f"Local IP: {local_ip} | Public IP: {pub_result.get('ip', 'N/A')} | "
                f"Latency: ~{ping_result.get('latency_ms', 'N/A')} ms"
            )
        }
