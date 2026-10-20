"""Preview disposable caches; apply only when explicitly requested."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def clean(apply=False, root=ROOT):
    root = root.resolve()
    targets = [root / name for name in
               ("cache", ".pytest_cache", "src/__pycache__", "web/__pycache__", "tests/__pycache__")]
    for target in targets:
        if not target.exists():
            continue
        if target.is_symlink() or not target.resolve().is_relative_to(root):
            raise ValueError("Refusing to clean a path outside the project.")
        print(f'{"Removing" if apply else "Would remove"}: {target.relative_to(root)}')
        if apply:
            shutil.rmtree(target)
    if not apply:
        print("Preview only. Pass --apply to remove these caches. Media and logs are preserved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    clean(parser.parse_args().apply)
