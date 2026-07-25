"""
╔══════════════════════════════════════════════════════════════╗
║           🖥️  DISK SPACE ANALYZER v2.0                       ║
║                                                              ║
║  Created by: Atul Bharti                                     ║
║  YouTube:    https://www.youtube.com/@atulbharti1            ║
║  Instagram:  https://www.instagram.com/trailsofatul/.        ║
║                                                              ║
║  HOW TO RUN:                                                 ║
║    python disk_analyzer.py                                   ║
║                                                              ║
║  WHAT IT DOES:                                               ║
║    1. Shows your top space-hungry folders                    ║
║    2. Finds large video files                                ║
║    3. Detects duplicate files wasting space                  ║
║    4. Checks video editor cache folders                      ║
║    5. Saves a full report to your Desktop                    ║
║                                                              ║
║  ✅ SAFE TO RUN — only reads files, never deletes anything   ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import hashlib
import platform
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ─── PYTHON VERSION CHECK ─────────────────────────────────────────────────────

if sys.version_info < (3, 7):
    print("❌ This script requires Python 3.7 or higher.")
    print(f"   Your version: {sys.version}")
    print("   Download latest Python from: https://www.python.org/downloads/")
    sys.exit(1)

# ─── CONFIG ──────────────────────────────────────────────────────────────────

SCAN_ROOT = Path.home()

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv",
    ".flv", ".m4v", ".3gp", ".hevc", ".ts",
    ".mts", ".m2ts", ".webm", ".vob", ".mpg", ".mpeg"
}

# Folders to skip (system/dev folders)
SKIP_DIRS = {
    "Windows", "System32", "$Recycle.Bin",
    "node_modules", ".git", "AppData/Local/Temp",
    "proc", "sys", "dev"
}

LARGE_FILE_MB = 100

# Video editor keywords to detect
VIDEO_EDITOR_KEYWORDS = [
    # VN Editor
    "frontrow.vlog", "FRVideoEditor", "vnvideo", "vn_editor", "VNEditor",
    # CapCut
    "CapCut", "capcut", "com.lemon.lvoMac",
    # Final Cut Pro
    "Final Cut", "finalcutpro", "com.apple.FinalCut",
    # DaVinci Resolve
    "DaVinci", "Resolve", "com.blackmagicdesign",
    # iMovie
    "iMovie", "com.apple.iMovieApp",
    # Adobe Premiere
    "Premiere", "Adobe/Common",
    # General VN
    "com.vn", "vn.video"
]

# ─── DETECT OS ───────────────────────────────────────────────────────────────

OS = platform.system()  # 'Darwin' = Mac, 'Windows', 'Linux'
DESKTOP = Path.home() / "Desktop"
REPORT_PATH = DESKTOP / f"disk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def format_size(size_bytes):
    """Convert bytes to human readable format (KB, MB, GB, TB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def file_hash(path, chunk_size=8192):
    """
    Fast partial hash — reads only first + last 8KB of file.
    This avoids reading full multi-GB files which would be very slow.
    Two files with same size AND same hash are almost certainly identical.
    """
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            h.update(f.read(chunk_size))   # read start of file
            f.seek(-chunk_size, 2)          # jump to near end of file
            h.update(f.read(chunk_size))    # read end of file
    except Exception:
        return None
    return h.hexdigest()

def should_skip(path):
    """Check if a folder should be skipped during scanning."""
    path_str = str(path)
    for skip in SKIP_DIRS:
        if skip in path_str:
            return True
    return False

def print_and_log(text, file):
    """Print to terminal AND write to report file simultaneously."""
    print(text)
    file.write(text + "\n")

# ─── START SCANNING ──────────────────────────────────────────────────────────

print("\n" + "=" * 62)
print("  🖥️  DISK SPACE ANALYZER v2.0 — by Atul Bharti")
print("=" * 62)
print(f"\n  OS detected:  {OS}")
print(f"  Scanning:     {SCAN_ROOT}")
print(f"  Report will be saved to: {REPORT_PATH}")
print("\n  (This may take 1-3 minutes depending on disk size...)\n")

folder_sizes = defaultdict(int)
video_files = []
all_files_by_size = defaultdict(list)

scanned = 0
errors = 0

for dirpath, dirnames, filenames in os.walk(SCAN_ROOT):
    dirpath = Path(dirpath)

    if should_skip(dirpath):
        dirnames.clear()
        continue

    dirnames[:] = [d for d in dirnames if not should_skip(dirpath / d)]

    for fname in filenames:
        fpath = dirpath / fname
        try:
            size = fpath.stat().st_size
        except (PermissionError, OSError):
            errors += 1
            continue

        scanned += 1

        # Show progress every 10,000 files
        if scanned % 10000 == 0:
            print(f"  ⏳ Scanned {scanned:,} files so far...")

        # Attribute size to parent folders (up to 3 levels deep)
        try:
            relative = fpath.relative_to(SCAN_ROOT)
            parts = relative.parts
            for depth in range(1, min(len(parts), 4)):
                parent = SCAN_ROOT / Path(*parts[:depth])
                folder_sizes[str(parent)] += size
        except ValueError:
            pass

        # Track video files
        if fpath.suffix.lower() in VIDEO_EXTENSIONS:
            video_files.append((fpath, size))

        # Track all files by size for duplicate detection
        all_files_by_size[size].append(fpath)

# ─── WRITE REPORT ────────────────────────────────────────────────────────────

with open(REPORT_PATH, "w", encoding="utf-8") as report:

    header = f"""
╔══════════════════════════════════════════════════════════════╗
║           🖥️  DISK SPACE ANALYZER v2.0                      ║
║           Report: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                   ║
║           Created by Atul Bharti | YouTube: @atulbharti      ║
╚══════════════════════════════════════════════════════════════╝

  OS:       {OS}
  Scanned:  {SCAN_ROOT}
"""
    print_and_log(header, report)
    print_and_log(f"✅ Scanned {scanned:,} files ({errors} skipped due to permissions)\n", report)

    # ── REPORT 1: TOP FOLDERS ──────────────────────────────────────────────

    print_and_log("=" * 62, report)
    print_and_log("📁 TOP 20 FOLDERS BY SIZE", report)
    print_and_log("=" * 62, report)

    sorted_folders = sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)[:20]
    for folder, size in sorted_folders:
        bar = "█" * min(int(size / (sorted_folders[0][1] / 30)), 30)
        print_and_log(f"  {format_size(size):>10}  {bar}  {folder}", report)

    # ── REPORT 2: LARGE VIDEO FILES ────────────────────────────────────────

    print_and_log("\n" + "=" * 62, report)
    print_and_log(f"🎬 LARGE VIDEO FILES (>{LARGE_FILE_MB} MB)", report)
    print_and_log("=" * 62, report)

    large_videos = [(p, s) for p, s in video_files if s > LARGE_FILE_MB * 1024 * 1024]
    large_videos.sort(key=lambda x: x[1], reverse=True)

    if large_videos:
        total_video_size = sum(s for _, s in large_videos)
        print_and_log(f"  Found {len(large_videos)} large video files totalling {format_size(total_video_size)}\n", report)
        for path, size in large_videos[:30]:
            print_and_log(f"  {format_size(size):>10}  {path}", report)
        if len(large_videos) > 30:
            print_and_log(f"\n  ... and {len(large_videos) - 30} more (see full report)", report)
    else:
        print_and_log("  ✅ No large video files found above threshold.", report)

    # ── REPORT 3: DUPLICATE FILES ──────────────────────────────────────────

    print_and_log("\n" + "=" * 62, report)
    print_and_log("♻️  DUPLICATE FILES (same size + hash)", report)
    print_and_log("=" * 62, report)
    print_and_log("  Hashing candidates... (files with matching sizes only)\n", report)

    duplicates = []
    total_wasted = 0

    candidate_groups = {
        size: paths for size, paths in all_files_by_size.items()
        if len(paths) > 1 and size > 1024 * 1024
    }

    hash_groups = defaultdict(list)
    for size, paths in candidate_groups.items():
        for path in paths:
            h = file_hash(path)
            if h:
                hash_groups[(size, h)].append(path)

    for (size, h), paths in hash_groups.items():
        if len(paths) > 1:
            wasted = size * (len(paths) - 1)
            total_wasted += wasted
            duplicates.append((size, wasted, paths))

    duplicates.sort(key=lambda x: x[1], reverse=True)

    if duplicates:
        print_and_log(f"  ⚠️  Found {len(duplicates)} duplicate groups — {format_size(total_wasted)} wasted!\n", report)
        for size, wasted, paths in duplicates[:20]:
            print_and_log(f"  {format_size(size)} each × {len(paths)} copies = {format_size(wasted)} wasted", report)
            for p in paths:
                print_and_log(f"      → {p}", report)
            print_and_log("", report)
        if len(duplicates) > 20:
            print_and_log(f"  ... and {len(duplicates) - 20} more duplicate groups (see full report file)", report)
            report.write("\n\n─── FULL DUPLICATE LIST ───\n\n")
            for size, wasted, paths in duplicates:
                report.write(f"  {format_size(size)} each × {len(paths)} copies = {format_size(wasted)} wasted\n")
                for p in paths:
                    report.write(f"      → {p}\n")
                report.write("\n")
    else:
        print_and_log("  ✅ No large duplicate files found!", report)

    # ── REPORT 4: VIDEO EDITOR FOLDERS ────────────────────────────────────

    print_and_log("\n" + "=" * 62, report)
    print_and_log("🎞️  VIDEO EDITOR — PROJECT & CACHE FOLDERS", report)
    print_and_log("=" * 62, report)

    editor_found = []
    for folder, size in folder_sizes.items():
        if any(kw.lower() in folder.lower() for kw in VIDEO_EDITOR_KEYWORDS):
            editor_found.append((folder, size))

    editor_found.sort(key=lambda x: x[1], reverse=True)

    if editor_found:
        for folder, size in editor_found:
            print_and_log(f"  {format_size(size):>10}  {folder}", report)
    else:
        print_and_log("  No video editor folders detected.", report)

    # ── SUMMARY ───────────────────────────────────────────────────────────

    print_and_log("\n" + "=" * 62, report)
    print_and_log("📊 SUMMARY", report)
    print_and_log("=" * 62, report)
    print_and_log(f"  Files scanned:       {scanned:,}", report)
    print_and_log(f"  Errors (no access):  {errors:,}", report)
    print_and_log(f"  Large video files:   {len(large_videos)}", report)
    print_and_log(f"  Duplicate groups:    {len(duplicates)}", report)
    print_and_log(f"  Wasted on dupes:     {format_size(total_wasted)}", report)
    print_and_log("", report)
    print_and_log("  💡 WHAT TO DO NEXT:", report)
    print_and_log("  1. Check the duplicate list — delete copies you don't need", report)
    print_and_log("  2. Clear video editor cache from inside the app settings", report)
    print_and_log("  3. Delete old Python .venv folders from finished projects", report)
    print_and_log("  4. Clear WhatsApp/Telegram media if you deleted the app", report)
    print_and_log("  5. Empty your Downloads folder of old installers & datasets", report)
    print_and_log("=" * 62, report)
    print_and_log(f"\n  📄 Full report saved to:\n  {REPORT_PATH}\n", report)
    print_and_log("  ─────────────────────────────────────────────────────────", report)
    print_and_log("  Script by Atul Bharti | Subscribe for more Python tips!", report)
    print_and_log("  ─────────────────────────────────────────────────────────\n", report)

print(f"\n✅ Done! Full report saved to:\n   {REPORT_PATH}\n")
