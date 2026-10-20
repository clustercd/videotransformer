"Short educational YouTube searches with a Creative Commons filter."
import subprocess
import json
from pathlib import Path

try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

DOWNLOAD_DIR = DATA_DIR / "downloaded"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# YouTube category searches for short videos with the CC filter
YOUTUBE_SEARCHES = {
    'science': {
        'target': 20,
        'queries': [
            'science experiment kids',
            'chemistry reaction',
            'microscope view',
            'physics demonstration',
            'DNA animation'
        ]
    },
    'geographie': {
        'target': 15,
        'queries': [
            'world landmarks',
            'famous buildings',
            'city skyline',
            'monuments tour'
        ]
    },
    'espace': {
        'target': 15,
        'queries': [
            'space footage',
            'rocket launch',
            'planets solar system',
            'NASA footage'
        ]
    },
    'nature': {
        'target': 10,
        'queries': [
            'waterfall nature',
            'lightning storm',
            'volcano eruption',
            'aurora borealis'
        ]
    },
    'transport': {
        'target': 10,
        'queries': [
            'trains documentary',
            'airplane takeoff',
            'ships boats'
        ]
    },
    'sports': {
        'target': 10,
        'queries': [
            'sports highlights',
            'olympic games',
            'athletics track'
        ]
    }
}

def check_ytdlp():
    "Check whether yt-dlp is installed."
    try:
        result = subprocess.run(['yt-dlp', '--version'],
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def download_youtube_videos(query: str, category: str, max_results: int = 3):
    "Run the download youtube videos workflow."
    category_dir = DOWNLOAD_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)

    # yt-dlp options
    cmd = [
        'yt-dlp',
        f'ytsearch{max_results}:{query} français documentaire',
        '--max-filesize', '20M',  # Max 20MB
        '--max-downloads', str(max_results),
        '--match-filter', 'duration < 180',  # Max 3 minutes
        '-o', str(category_dir / f'{category}_%(title).50s_%(id)s.%(ext)s'),
        '--format', 'best[height<=480]',  # Max 480p
        '--no-playlist',
        '--quiet',
        '--no-warnings'
    ]

    try:
        print(f"  Search YouTube (French): {query}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            # Count downloaded files
            files = list(category_dir.glob(f'{category}_*'))
            return len([f for f in files if f.stat().st_mtime > 0])
        else:
            print(f"  Error: {result.stderr[:100]}")
            return 0
    except Exception as e:
        print(f"  Error: {e}")
        return 0

def main():
    print("=" * 60)
    print("YOUTUBE CREATIVE COMMONS SEARCHES")
    print("=" * 60)
    print()

    # Check yt-dlp availability
    if not check_ytdlp():
        print("ERROR: yt-dlp not installed !")
        print()
        print("Installation:")
        print("  pip install yt-dlp")
        print()
        print("Or with Chocolatey:")
        print("  choco install yt-dlp")
        print()
        input("Press ENTER...")
        return

    print("TARGETS:")
    for cat, config in YOUTUBE_SEARCHES.items():
        print(f"  {cat:15s}: +{config['target']} videos")
    print()
    print("Source: YouTube (Creative Commons search filter)")
    print("Limit: up to 20 MB and 3 minutes per video")
    print()

    response = input("Continue? (yes/no): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        return

    print()
    total_downloaded = 0
    stats = {cat: 0 for cat in YOUTUBE_SEARCHES.keys()}

    for category, config in YOUTUBE_SEARCHES.items():
        target = config['target']
        queries = config['queries']

        print(f"\n{'=' * 60}")
        print(f"CATEGORY: {category.upper()} (target: +{target})")
        print(f"{'=' * 60}\n")

        downloaded = 0
        per_query = max(3, target // len(queries))

        for query in queries:
            if downloaded >= target:
                break

            count = download_youtube_videos(query, category, per_query)

            if count > 0:
                print(f"  Downloaded: {count} videos")
                downloaded += count
                total_downloaded += count
                stats[category] = downloaded

            print(f"  Progress: {downloaded}/{target}\n")

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for cat, count in stats.items():
        print(f"{cat:15s}: +{count} videos")
    print(f"\nTOTAL: {total_downloaded} videos")
    print(f"Folder: {DOWNLOAD_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
