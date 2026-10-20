"Pexels searches for selected categories. An API key is required."
import requests
from pathlib import Path
import time
import json

# Get your API key from https://www.pexels.com/api/
try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key
PEXELS_API_KEY = get_pexels_key()

DOWNLOAD_DIR = DATA_DIR / "downloaded"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Targeted keywords by category
PRIORITY_CATEGORIES = {
    'science': {
        'target': 35,
        'keywords': [
            'chemistry', 'laboratory', 'microscope', 'experiment',
            'DNA', 'molecule', 'research', 'scientist', 'beaker',
            'test tube', 'physics', 'biology'
        ]
    },
    'geographie': {
        'target': 27,
        'keywords': [
            'Eiffel Tower', 'Big Ben', 'Statue Liberty', 'Taj Mahal',
            'landmark', 'monument', 'cathedral', 'bridge', 'downtown',
            'skyline', 'parliament', 'harbor', 'city view'
        ]
    },
    'espace': {
        'target': 19,
        'keywords': [
            'rocket', 'planet', 'galaxy', 'space', 'astronaut',
            'moon', 'stars', 'satellite', 'nebula', 'cosmos',
            'telescope', 'Mars', 'solar system'
        ]
    },
    'nature': {
        'target': 18,
        'keywords': [
            'waterfall', 'volcano', 'lightning', 'rainbow',
            'glacier', 'desert', 'canyon', 'tornado', 'storm',
            'aurora', 'coral reef', 'rainforest'
        ]
    },
    'transport': {
        'target': 14,
        'keywords': [
            'train', 'ship', 'airplane', 'helicopter', 'boat',
            'ferry', 'submarine', 'balloon', 'jet', 'aircraft'
        ]
    },
    'sports': {
        'target': 17,
        'keywords': [
            'basketball', 'tennis', 'volleyball', 'swimming',
            'running', 'cycling', 'skateboard', 'climbing',
            'gymnastics', 'soccer', 'baseball'
        ]
    }
}

def search_pexels(query: str, per_page: int = 5):
    "Search Pexels videos."
    if not PEXELS_API_KEY:
        return []

    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "per_page": per_page,
        "size": "medium",
        "orientation": "landscape"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        videos = []
        for video in data.get('videos', []):
            video_files = video.get('video_files', [])
            if video_files:
                # Prefer medium quality to limit file size
                for vf in video_files:
                    if vf.get('quality') == 'hd' and vf.get('width', 0) <= 1280:
                        videos.append({
                            'url': vf['link'],
                            'id': video['id'],
                            'width': vf.get('width', 0),
                            'size': vf.get('file_size', 0)
                        })
                        break
                else:
                    # Otherwise use the first available format
                    if video_files:
                        videos.append({
                            'url': video_files[0]['link'],
                            'id': video['id'],
                            'width': video_files[0].get('width', 0),
                            'size': video_files[0].get('file_size', 0)
                        })

        return videos
    except Exception as e:
        print(f"  Error: {e}")
        return []

def download_video(video_info: dict, query: str, category: str) -> bool:
    "Download one video."
    try:
        category_dir = DOWNLOAD_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Filename: category_query_id.mp4
        clean_query = query.replace(' ', '_')[:30]
        filename = f"{category}_{clean_query}_{video_info['id']}.mp4"
        filepath = category_dir / filename

        if filepath.exists():
            return False

        # Maximum file size: 30 MB
        size_mb = video_info.get('size', 0) / (1024 * 1024)
        if size_mb > 30:
            print(f"  Too large ({size_mb:.1f}MB)")
            return False

        print(f"  Downloading ({size_mb:.1f}MB)...")
        response = requests.get(video_info['url'], stream=True, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"  OK: {filename}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print("=" * 60)
    print("PEXELS DOWNLOADS - SELECTED CATEGORYS")
    print("=" * 60)
    print()

    if not PEXELS_API_KEY:
        print("ERROR: API key not configured !")
        print()
        print("1. Visit: https://www.pexels.com/api/")
        print("2. Create a free account")
        print("3. Copy your API key")
        print("4. Set the PEXELS_API_KEY environment variable")
        print()
        input("Press ENTER...")
        return

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
            videos = search_pexels(keyword, per_page=3)

            if not videos:
                print("  No results")
                time.sleep(1)
                continue

            print(f"  Found: {len(videos)} videos")

            # Download
            for video_info in videos:
                if downloaded >= target:
                    break

                if download_video(video_info, keyword, category):
                    downloaded += 1
                    total_downloaded += 1
                    stats[category] += 1
                    print(f"  Progress: {downloaded}/{target}")

                time.sleep(1)

            time.sleep(2)  # Rate limiting Pexels

        print(f"\n{category}: {downloaded} videos")

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
