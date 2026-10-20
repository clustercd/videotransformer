"Copy videos into topic folders and generate a JSON index."
from pathlib import Path
try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

import json
import shutil


ORGANIZED_DIR = DATA_DIR / "organized"

# Keyword categories
CATEGORIES = {
    'animaux': ['chat', 'chien', 'oiseau', 'cheval', 'lion', 'bear', 'elephant',
                'fish', 'bird', 'cat', 'dog', 'horse', 'deer', 'rabbit', 'butterfly',
                'whale', 'shark', 'seal', 'turtle', 'eagle', 'turkey', 'geese'],

    'nature': ['tree', 'forest', 'mountain', 'ocean', 'waterfall', 'wave',
               'flower', 'plant', 'geyser', 'volcano', 'iceberg', 'beach',
               'cliffs', 'field'],

    'espace': ['space', 'moon', 'planet', 'satellite', 'apollo', 'rocket',
               'astronaut', 'mars', 'asteroid'],

    'science': ['microscope', 'experiment', 'laboratory', 'submarine',
                'telescope', 'chemistry', 'physics'],

    'transport': ['car', 'train', 'plane', 'airplane', 'helicopter', 'boat',
                  'ship', 'motorcycle', 'bicycle', 'scooter', 'flying'],

    'sports': ['soccer', 'football', 'skiing', 'surfboard', 'snowboard',
               'climbing', 'running', 'playing'],

    'histoire': ['pyramid', 'monument', 'ancient', 'museum', 'beatles',
                 'pope', 'soldier', 'tanks', 'war', 'black_white'],

    'vie_quotidienne': ['cooking', 'reading', 'family', 'people', 'crowd',
                        'wedding', 'dance', 'singing', 'sitting', 'walking',
                        'standing', 'working', 'painting'],

    'geographie': ['city', 'building', 'street', 'tower', 'factory',
                   'windmill', 'parade', 'theatre', 'stage']
}

def categorize_video(filename: str):
    "Determine a video category from its filename."
    name_lower = filename.lower()

    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in name_lower:
                return category

    return 'autre'

def organize_videos():
    "Copy videos into category folders."
    print("=" * 60)
    print("VIDEO ORGANIZATION")
    print("=" * 60)
    print()

    # Create the organized directory
    ORGANIZED_DIR.mkdir(parents=True, exist_ok=True)

    # Create category subdirectories
    for category in list(CATEGORIES.keys()) + ['autre']:
        (ORGANIZED_DIR / category).mkdir(parents=True, exist_ok=True)

    # Find all videos
    videos = []
    for ext in ['.mp4', '.avi', '.wmv', '.mpg', '.AVI', '.WMV', '.MPG']:
        videos.extend(DATA_DIR.glob(f"*{ext}"))

    # Exclude organized copies and desktop metadata
    videos = [v for v in videos if 'organized' not in str(v) and v.name != 'desktop.ini']

    print(f"Found: {len(videos)} videos")
    print()

    # Organize videos
    catalog = {}
    stats = {cat: 0 for cat in list(CATEGORIES.keys()) + ['autre']}

    for video in videos:
        category = categorize_video(video.stem)

        # Copy files while preserving the originals
        dest = ORGANIZED_DIR / category / video.name
        if not dest.exists():
            shutil.copy2(video, dest)
            print(f"📁 {category:20s} ← {video.name}")

        # Add the video to the catalog
        if category not in catalog:
            catalog[category] = []

        catalog[category].append({
            'filename': video.name,
            'path': str(dest.relative_to(DATA_DIR)),
            'description': video.stem.replace('_', ' ').title()
        })

        stats[category] += 1

    # Save the JSON catalog
    catalog_file = ORGANIZED_DIR / "catalog.json"
    with open(catalog_file, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print("STATISTICS")
    print("=" * 60)
    for category, count in sorted(stats.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"{category:20s}: {count:4d} videos")

    print()
    print("=" * 60)
    print(f"Catalog saved: {catalog_file}")
    print(f"Organized folder: {ORGANIZED_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    organize_videos()
