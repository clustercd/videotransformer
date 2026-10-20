"""Convert WMV files in the private data root without replacing existing outputs."""
from pathlib import Path
import shutil
import subprocess
import sys

from .settings import DATA_DIR


def main():
    if not shutil.which("ffmpeg"):
        print("FFmpeg is required on PATH.")
        return 1
    failed = 0
    for source in sorted(DATA_DIR.glob("*.wmv")):
        output = source.with_name(source.stem + "_converted.mp4")
        if output.exists():
            print(f"Skipping existing output: {output.name}")
            continue
        print(f"Converting: {source.name}")
        result = subprocess.run(["ffmpeg", "-n", "-i", str(source), "-c:v", "libx264",
                                 "-crf", "23", "-c:a", "aac", "-loglevel", "error", str(output)])
        failed += result.returncode != 0
    return int(bool(failed))


if __name__ == "__main__":
    sys.exit(main())
