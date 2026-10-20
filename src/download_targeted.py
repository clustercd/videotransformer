"Targeted Wikimedia Commons searches. No API key is required."
import requests
from pathlib import Path
try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

import time
from urllib.parse import quote
import json

DOWNLOAD_DIR = DATA_DIR / "downloaded"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Targeted keywords for selected categories
PRIORITY_CATEGORIES = {
    'science': {
        'target': 35,
        'keywords': [
            'chemistry experiment', 'laboratory', 'microscope view',
            'physics demonstration', 'biology', 'DNA', 'molecule',
            'chemical reaction', 'science experiment', 'test tube',
            'petri dish', 'scientific research', 'atom', 'cell division'
        ]
    },
    'geographie': {
        'target': 27,
        'keywords': [
            'Eiffel Tower', 'Big Ben', 'Statue Liberty', 'Taj Mahal',
            'Great Wall China', 'Colosseum', 'landmarks', 'famous building',
            'city skyline', 'capital city', 'parliament', 'cathedral',
            'bridge', 'harbor', 'downtown', 'urban landscape'
        ]
    },
    'espace': {
        'target': 19,
        'keywords': [
            'rocket launch', 'Saturn', 'Jupiter', 'Mars rover',
            'lunar landing', 'space shuttle', 'ISS', 'nebula',
            'galaxy', 'solar eclipse', 'comet', 'telescope view',
            'astronaut spacewalk', 'satellite orbit', 'planetary'
        ]
    },
    'nature': {
        'target': 18,
        'keywords': [
            'rainforest', 'coral reef', 'aurora borealis', 'tornado',
            'lightning storm', 'waterfall', 'volcano eruption', 'glacier',
            'desert landscape', 'canyon', 'river delta', 'mountain range',
            'tropical storm', 'rainbow', 'sunrise', 'sunset'
        ]
    },
    'transport': {
        'target': 14,
        'keywords': [
            'steam locomotive', 'bullet train', 'cargo ship', 'aircraft takeoff',
            'helicopter flight', 'submarine', 'hot air balloon', 'ferry',
            'monorail', 'tram', 'freight train', 'cruise ship',
            'jet fighter', 'propeller plane'
        ]
    },
    'sports': {
        'target': 17,
        'keywords': [
            'basketball game', 'tennis match', 'volleyball', 'baseball',
            'ice hockey', 'gymnastics', 'swimming competition', 'track field',
            'cycling race', 'marathon', 'boxing match', 'wrestling',
            'skateboarding', 'rock climbing', 'diving', 'fencing'
        ]
    }
}

def search_wikimedia_videos(query: str, limit: int = 5):
    "Run the search wikimedia videos workflow."
    url = "https://commons.wikimedia.org/w/api.php"

    params = {
        'action': 'query',
        'format': 'json',
        'list': 'search',
        'srsearch': f'{query} filetype:video',
        'srnamespace': 6,
        'srlimit': limit,
        'srprop': 'size|timestamp'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get('query', {}).get('search', []):
            title = item['title'].replace('File:', '')
            if any(ext in title.lower() for ext in ['.webm', '.ogv', '.mp4', '.mov']):
                results.append(title)

        return results
    except Exception as e:
        print(f"  Search error: {e}")
        return []

def get_video_url(filename: str):
    "Resolve the direct media URL."
    url = "https://commons.wikimedia.org/w/api.php"

    params = {
        'action': 'query',
        'format': 'json',
        'titles': f'File:{filename}',
        'prop': 'imageinfo',
        'iiprop': 'url'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            imageinfo = page.get('imageinfo', [])
            if imageinfo:
                return imageinfo[0].get('url')

        return None
    except Exception as e:
        print(f"  Error URL: {e}")
        return None

def download_video(url: str, filename: str, category: str) -> bool:
    "Download one video."
    try:
        category_dir = DOWNLOAD_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize the filename
        clean_name = filename.replace(' ', '_')[:100]
        filepath = category_dir / clean_name

        if filepath.exists():
            return False

        print(f"  Downloading...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        # Maximum file size: 50 MB
        total_size = int(response.headers.get('content-length', 0))
        if total_size > 50 * 1024 * 1024:
            print(f"  Too large ({total_size / 1024 / 1024:.1f}MB), passe")
            return False

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"  OK: {clean_name}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print("=" * 60)
    print("TARGETED DOWNLOADS - SELECTED CATEGORYS")
    print("=" * 60)
    print()

    print("TARGETS:")
    for cat, config in PRIORITY_CATEGORIES.items():
        print(f"  {cat:15s}: +{config['target']} videos")
    print()

    input("Press ENTER to start...")
    print()

    total_downloaded = 0
    stats = {cat: 0 for cat in PRIORITY_CATEGORIES.keys()}

    for category, config in PRIORITY_CATEGORIES.items():
        target = config['target']
        keywords = config['keywords']

        print(f"\n{'=' * 60}")
        print(f"CATEGORY: {category.upper()} (target: +{target})")
        print(f"{'=' * 60}\n")

        downloaded = 0

        for keyword in keywords:
            if downloaded >= target:
                break

            print(f"Search: {keyword}")

            # Search
            videos = search_wikimedia_videos(keyword, limit=3)

            if not videos:
                print("  No results")
                continue

            print(f"  Found: {len(videos)} videos")

            # Download
            for video_title in videos:
                if downloaded >= target:
                    break

                print(f"\n  [{video_title[:50]}...]")

                # Resolve the media URL
                video_url = get_video_url(video_title)
                if not video_url:
                    print("  URL not found")
                    continue

                # Download
                if download_video(video_url, video_title, category):
                    downloaded += 1
                    total_downloaded += 1
                    stats[category] += 1
                    print(f"  Progress: {downloaded}/{target}")

                time.sleep(1.5)  # Rate limiting

            time.sleep(1)

        print(f"\n{category}: {downloaded} videos downloaded")

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for cat, count in stats.items():
        print(f"{cat:15s}: +{count} videos")
    print(f"\nTOTAL: {total_downloaded} videos downloaded")
    print(f"Folder: {DOWNLOAD_DIR}")
    print("=" * 60)

    # Save statistics
    stats_file = DOWNLOAD_DIR / "download_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    main()
