"Educational stock video searches using Pexels and Pixabay."
import requests
import os
from pathlib import Path
try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

import time
from typing import List, Dict

# Obtain API keys from the providers
PEXELS_API_KEY = get_pexels_key()  # https://www.pexels.com/api/
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")  # https://pixabay.com/api/docs/

DOWNLOAD_DIR = DATA_DIR / "downloaded"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Educational categories for children
CATEGORIES = {
    'animaux': ['cat', 'dog', 'bird', 'rabbit', 'lion', 'elephant', 'fish', 'butterfly'],
    'nature': ['tree', 'flower', 'mountain', 'ocean', 'waterfall', 'sunset', 'forest'],
    'espace': ['space', 'planet', 'moon', 'stars', 'rocket', 'astronaut'],
    'science': ['laboratory', 'microscope', 'chemistry', 'physics', 'biology'],
    'transport': ['car', 'train', 'airplane', 'boat', 'bicycle'],
    'vie_quotidienne': ['cooking', 'reading', 'playing', 'learning', 'family']
}

def download_from_pexels(query: str, per_page: int = 5) -> List[Dict]:
    "Run the download from pexels workflow."
    if not PEXELS_API_KEY:
        print("⚠️ First configure PEXELS_API_KEY")
        return []

    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": per_page, "size": "medium"}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        videos = []
        for video in data.get('videos', []):
            video_files = video.get('video_files', [])
            if video_files:
                # Prefer medium quality
                video_url = video_files[0]['link']
                videos.append({
                    'url': video_url,
                    'id': video['id'],
                    'query': query
                })

        return videos
    except Exception as e:
        print(f"❌ Error Pexels: {e}")
        return []

def download_from_pixabay(query: str, per_page: int = 5) -> List[Dict]:
    "Run the download from pixabay workflow."
    if not PIXABAY_API_KEY:
        print("⚠️ First configure PIXABAY_API_KEY")
        return []

    url = "https://pixabay.com/api/videos/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "per_page": per_page,
        "video_type": "film"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        videos = []
        for hit in data.get('hits', []):
            video_files = hit.get('videos', {})
            if 'medium' in video_files:
                videos.append({
                    'url': video_files['medium']['url'],
                    'id': hit['id'],
                    'query': query
                })

        return videos
    except Exception as e:
        print(f"❌ Error Pixabay: {e}")
        return []

def download_video(video_info: Dict, category: str) -> bool:
    "Download one video."
    try:
        category_dir = DOWNLOAD_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Filename: category_query_id.mp4
        filename = f"{category}_{video_info['query']}_{video_info['id']}.mp4"
        filepath = category_dir / filename

        if filepath.exists():
            print(f"  ⏭️ Already downloaded: {filename}")
            return True

        print(f"  📥 Download: {filename}...")
        response = requests.get(video_info['url'], stream=True)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"  ✅ Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("📥 EDUCATIONAL VIDEO DOWNLOADER")
    print("=" * 60)
    print()

    # Check API keys
    if not PEXELS_API_KEY and not PIXABAY_API_KEY:
        print("❌ No API key configured !")
        print()
        print("🔑 Configuration required:")
        print("1. Pexels: https://www.pexels.com/api/")
        print("2. Pixabay: https://pixabay.com/api/docs/")
        print()
        print("Set the provider API keys in your environment.")
        return

    # Choose a source
    print("📡 Available sources:")
    sources = []
    if bool(PEXELS_API_KEY):
        sources.append('pexels')
        print("  ✅ Pexels")
    if bool(PIXABAY_API_KEY):
        sources.append('pixabay')
        print("  ✅ Pixabay")
    print()

    # Choose categories
    print("📚 Available categories:")
    for i, cat in enumerate(CATEGORIES.keys(), 1):
        print(f"  {i}. {cat}")
    print()

    choice = input("Download all categories? (yes/no): ")
    if choice.lower() not in ['oui', 'o', 'yes', 'y']:
        print("❌ Cancelled")
        return

    videos_per_query = int(input("Videos per keyword (1-10): ") or "3")

    print()
    print("🚀 Download in progress...")
    print("=" * 60)
    print()

    total_downloaded = 0

    for category, queries in CATEGORIES.items():
        print(f"\n📂 Category: {category.upper()}")
        print("-" * 60)

        for query in queries:
            print(f"\n🔍 Search: {query}")

            videos = []

            # Pexels
            if 'pexels' in sources:
                videos.extend(download_from_pexels(query, videos_per_query))
                time.sleep(1)  # Rate limiting

            # Pixabay
            if 'pixabay' in sources:
                videos.extend(download_from_pixabay(query, videos_per_query))
                time.sleep(1)  # Rate limiting

            # Download
            for video in videos[:videos_per_query]:
                if download_video(video, category):
                    total_downloaded += 1
                time.sleep(0.5)

    print()
    print("=" * 60)
    print(f"✅ Download completed : {total_downloaded} videos")
    print(f"📁 Folder: {DOWNLOAD_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
