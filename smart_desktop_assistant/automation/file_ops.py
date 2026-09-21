"""File and directory automation operations."""

import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..config import FILE_CATEGORIES, DOWNLOADS_DIR, SYSTEM_TEMP

class FileOperations:
    """Automates repetitive file management workflows."""

    @staticmethod
    def organize_directory(target_dir: Optional[Path] = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        Organizes files in the target directory into categorized subdirectories
        (e.g., Documents, Images, Videos, Audio, Code, Archives, Installers).
        """
        target = Path(target_dir) if target_dir else DOWNLOADS_DIR

        if not target.exists() or not target.is_dir():
            return {
                "success": False,
                "message": f"Target directory does not exist: {target}",
                "moved_files": []
            }

        moved_files = []
        category_counts: Dict[str, int] = {}

        # Reverse map for fast extension lookup
        ext_to_category = {}
        for category, extensions in FILE_CATEGORIES.items():
            for ext in extensions:
                ext_to_category[ext.lower()] = category

        # Scan only top-level files (avoiding re-organizing existing category subfolders)
        for entry in os.scandir(target):
            if entry.is_file():
                file_path = Path(entry.path)
                ext = file_path.suffix.lower()
                category = ext_to_category.get(ext, "Misc")

                dest_folder = target / category
                dest_file = dest_folder / file_path.name

                # Avoid name collision
                if dest_file.exists():
                    base = file_path.stem
                    counter = 1
                    while dest_file.exists():
                        dest_file = dest_folder / f"{base}_{counter}{file_path.suffix}"
                        counter += 1

                moved_files.append({
                    "from": str(file_path.name),
                    "to": f"{category}/{dest_file.name}",
                    "category": category
                })
                category_counts[category] = category_counts.get(category, 0) + 1

                if not dry_run:
                    dest_folder.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(dest_file))

        return {
            "success": True,
            "directory": str(target),
            "dry_run": dry_run,
            "total_files": len(moved_files),
            "category_counts": category_counts,
            "moved_files": moved_files[:20]  # preview first 20
        }

    @staticmethod
    def search_files(
        directory: Optional[Path] = None,
        query: str = "",
        extension: Optional[str] = None,
        min_size_mb: Optional[float] = None,
        max_results: int = 30
    ) -> Dict[str, Any]:
        """Searches for files matching name pattern, extension, or minimum size."""
        target = Path(directory) if directory else DOWNLOADS_DIR
        if not target.exists():
            return {"success": False, "message": f"Directory not found: {target}", "results": []}

        matches = []
        q_lower = query.lower().strip() if query else ""
        ext_lower = extension.lower().strip() if extension else None
        min_bytes = int(min_size_mb * 1024 * 1024) if min_size_mb else None

        try:
            for root, _, files in os.walk(target):
                for f in files:
                    if len(matches) >= max_results:
                        break

                    f_path = Path(root) / f
                    if ext_lower and not f.lower().endswith(ext_lower):
                        continue
                    if q_lower and q_lower not in f.lower():
                        continue

                    try:
                        stat = f_path.stat()
                        size = stat.st_size
                        if min_bytes and size < min_bytes:
                            continue

                        matches.append({
                            "name": f,
                            "path": str(f_path),
                            "size_kb": round(size / 1024, 1),
                            "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime))
                        })
                    except (PermissionError, FileNotFoundError):
                        continue
                if len(matches) >= max_results:
                    break
        except Exception as e:
            return {"success": False, "error": str(e), "results": matches}

        return {
            "success": True,
            "directory": str(target),
            "total_matches": len(matches),
            "results": matches
        }

    @staticmethod
    def batch_rename(
        directory: Optional[Path] = None,
        find_text: str = "",
        replace_text: str = "",
        prefix: str = "",
        suffix: str = "",
        extension: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Safely renames multiple files in a directory."""
        target = Path(directory) if directory else DOWNLOADS_DIR
        if not target.exists():
            return {"success": False, "message": f"Directory not found: {target}", "renamed": []}

        renamed = []
        for entry in os.scandir(target):
            if entry.is_file():
                f_path = Path(entry.path)
                if extension and f_path.suffix.lower() != extension.lower():
                    continue

                stem = f_path.stem
                new_stem = stem
                if find_text:
                    new_stem = new_stem.replace(find_text, replace_text)
                if prefix:
                    new_stem = f"{prefix}{new_stem}"
                if suffix:
                    new_stem = f"{new_stem}{suffix}"

                new_name = f"{new_stem}{f_path.suffix}"
                if new_name != f_path.name:
                    dest_file = target / new_name
                    renamed.append({
                        "original": f_path.name,
                        "new": new_name
                    })
                    if not dry_run and not dest_file.exists():
                        f_path.rename(dest_file)

        return {
            "success": True,
            "dry_run": dry_run,
            "directory": str(target),
            "total_renamed": len(renamed),
            "renamed": renamed
        }

    @staticmethod
    def clean_temp_files(dry_run: bool = False) -> Dict[str, Any]:
        """Safely scans and removes temporary scratch files."""
        if not SYSTEM_TEMP.exists():
            return {"success": False, "message": "Temp directory not found", "freed_bytes": 0}

        deleted_count = 0
        freed_bytes = 0
        now = time.time()
        one_day_ago = now - (24 * 3600)  # delete files older than 24 hours to prevent locking active app files

        for entry in os.scandir(SYSTEM_TEMP):
            try:
                if entry.is_file():
                    stat = entry.stat()
                    if stat.st_mtime < one_day_ago:
                        freed_bytes += stat.st_size
                        deleted_count += 1
                        if not dry_run:
                            os.remove(entry.path)
            except (PermissionError, FileNotFoundError):
                continue

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        return {
            "success": True,
            "dry_run": dry_run,
            "deleted_files": deleted_count,
            "freed_mb": freed_mb,
            "message": f"{'Would remove' if dry_run else 'Removed'} {deleted_count} temp files, reclaiming {freed_mb} MB."
        }
