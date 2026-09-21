"""System operations: hardware monitoring, process management, screenshot, and clipboard."""

import ctypes
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..config import SCREENSHOTS_DIR

class SystemOperations:
    """Manages system diagnostics and OS control."""

    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """Collects CPU, RAM, Disk, Uptime, and Battery statistics."""
        # 1. Disk usage via standard library shutil
        total_disk, used_disk, free_disk = shutil.disk_usage(Path.home().anchor)
        disk_stats = {
            "total_gb": round(total_disk / (1024**3), 1),
            "free_gb": round(free_disk / (1024**3), 1),
            "used_gb": round(used_disk / (1024**3), 1),
            "percent_used": round((used_disk / total_disk) * 100, 1)
        }

        # 2. RAM and CPU usage via Windows PowerShell
        ps_cmd = (
            "$os = Get-CimInstance Win32_OperatingSystem; "
            "$tot = $os.TotalVisibleMemorySize; "
            "$free = $os.FreePhysicalMemory; "
            "$used = $tot - $free; "
            "$cpu = (Get-CimInstance Win32_Processor).LoadPercentage; "
            "Write-Output \"$tot,$free,$used,$cpu\""
        )

        ram_stats = {"total_gb": 0, "free_gb": 0, "used_gb": 0, "percent_used": 0}
        cpu_usage_pct = 0.0

        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = res.stdout.strip().split(",")
                if len(parts) >= 4:
                    tot_kb = float(parts[0])
                    free_kb = float(parts[1])
                    used_kb = float(parts[2])
                    cpu_usage_pct = float(parts[3]) if parts[3] else 0.0

                    ram_stats = {
                        "total_gb": round(tot_kb / (1024 * 1024), 1),
                        "free_gb": round(free_kb / (1024 * 1024), 1),
                        "used_gb": round(used_kb / (1024 * 1024), 1),
                        "percent_used": round((used_kb / tot_kb) * 100, 1)
                    }
        except Exception:
            pass

        # 3. Battery status via Windows Kernel32
        battery_stats = SystemOperations._get_battery_status()

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_percent": cpu_usage_pct,
            "ram": ram_stats,
            "disk": disk_stats,
            "battery": battery_stats
        }

    @staticmethod
    def _get_battery_status() -> Dict[str, Any]:
        """Queries battery status using ctypes on Windows."""
        class SYSTEM_POWER_STATUS(ctypes.Structure):
            _fields_ = [
                ("ACLineStatus", ctypes.c_byte),
                ("BatteryFlag", ctypes.c_byte),
                ("BatteryLifePercent", ctypes.c_byte),
                ("Reserved1", ctypes.c_byte),
                ("BatteryLifeTime", ctypes.c_ulong),
                ("BatteryFullLifeTime", ctypes.c_ulong),
            ]

        try:
            status = SYSTEM_POWER_STATUS()
            if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
                percent = status.BatteryLifePercent
                is_charging = status.ACLineStatus == 1
                return {
                    "has_battery": percent != 255,
                    "percent": percent if percent != 255 else None,
                    "is_plugged_in": is_charging
                }
        except Exception:
            pass
        return {"has_battery": False, "percent": None, "is_plugged_in": None}

    @staticmethod
    def get_top_processes(count: int = 8, sort_by: str = "memory") -> List[Dict[str, Any]]:
        """Lists active top processes sorted by memory."""
        ps_cmd = (
            f"Get-Process | Sort-Object WorkingSet64 -Descending | "
            f"Select-Object -First {count} Id, ProcessName, @{{Name='MemoryMB';Expression={{[math]::Round($_.WorkingSet64 / 1MB, 1)}}}} | "
            f"ConvertTo-Csv -NoTypeInformation"
        )
        processes = []
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=6
            )
            if res.returncode == 0:
                lines = [line.strip('"\r\n') for line in res.stdout.strip().splitlines()]
                if len(lines) > 1:
                    headers = [h.strip('"') for h in lines[0].split('","')]
                    for line in lines[1:]:
                        parts = [p.strip('"') for p in line.split('","')]
                        if len(parts) >= 3:
                            processes.append({
                                "pid": parts[0],
                                "name": parts[1],
                                "memory_mb": float(parts[2]) if parts[2] else 0.0
                            })
        except Exception:
            pass
        return processes

    @staticmethod
    def kill_process(identifier: str, dry_run: bool = False) -> Dict[str, Any]:
        """Safely terminates a process by PID or application name."""
        target = identifier.strip()
        is_pid = target.isdigit()

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": f"[DRY RUN] Would terminate {'PID ' + target if is_pid else target + '.exe'}"
            }

        cmd = ["taskkill", "/F"]
        if is_pid:
            cmd.extend(["/PID", target])
        else:
            exe_name = target if target.lower().endswith(".exe") else f"{target}.exe"
            cmd.extend(["/IM", exe_name])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return {
                    "success": True,
                    "message": f"Successfully terminated process: {target}",
                    "details": res.stdout.strip()
                }
            else:
                return {
                    "success": False,
                    "message": f"Could not terminate process: {res.stderr.strip() or res.stdout.strip()}"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def capture_screenshot(custom_path: Optional[Path] = None) -> Dict[str, Any]:
        """Captures desktop screen natively without external dependencies."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if custom_path:
            save_path = Path(custom_path)
        else:
            save_path = SCREENSHOTS_DIR / f"screenshot_{timestamp}.png"

        save_path.parent.mkdir(parents=True, exist_ok=True)
        ps_path = str(save_path).replace("\\", "/")

        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
            "$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
            "$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height; "
            "$g = [System.Drawing.Graphics]::FromImage($bmp); "
            "$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size); "
            f"$bmp.Save('{ps_path}'); "
            "$g.Dispose(); $bmp.Dispose();"
        )

        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=8
            )
            if res.returncode == 0 and save_path.exists():
                return {
                    "success": True,
                    "path": str(save_path),
                    "size_kb": round(save_path.stat().st_size / 1024, 1),
                    "message": f"Screenshot saved successfully to {save_path.name}"
                }
            return {"success": False, "error": res.stderr.strip() or "Screenshot capture failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def lock_workstation() -> Dict[str, Any]:
        """Locks the Windows workstation desktop."""
        try:
            result = ctypes.windll.user32.LockWorkStation()
            if result:
                return {"success": True, "message": "Workstation locked successfully."}
            return {"success": False, "message": "Failed to lock workstation."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_clipboard() -> str:
        """Retrieves text from Windows clipboard."""
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                timeout=4
            )
            return res.stdout.strip()
        except Exception:
            return ""

    @staticmethod
    def set_clipboard(text: str) -> bool:
        """Stores text into Windows clipboard."""
        try:
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
                stdin=subprocess.PIPE,
                text=True
            )
            proc.communicate(input=text, timeout=4)
            return proc.returncode == 0
        except Exception:
            return False
