"Wikimedia Commons video searches. No API key is required."
import requests
from pathlib import Path
try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

import time
from urllib.parse import unquote

DOWNLOAD_DIR = DATA_DIR / "wikimedia"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# French and English educational keywords
KEYWORDS = {
    'animaux': ['cat', 'dog', 'bird', 'elephant', 'lion', 'fish', 'rabbit'],
    'nature': ['waterfall', 'mountain', 'forest', 'ocean', 'flower'],
    'espace': ['space', 'planet', 'solar system', 'moon', 'astronomy'],
    'science': ['experiment', 'microscope', 'chemistry', 'physics'],
    'histoire': ['ancient', 'monument', 'museum', 'archaeology'],
}

def search_wikimedia_videos(query: str, limit: int = 10):
    """Search des videos sur Wikimedia Commons"""
    url = "https://commons.wikimedia.org/w/api.php"

    params = {
        'action': 'query',
        'format': 'json',
        'list': 'search',
        'srsearch': f'{query} filetype:video',
        'srnamespace': 6,  # File namespace
        'srlimit': limit,
        'srprop': 'size|wordcount|timestamp'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get('query', {}).get('search', []):
            title = item['title'].replace('File:', '')
            # Keep video files only
            if any(ext in title.lower() for ext in ['.webm', '.ogv', '.mp4']):
                results.append(title)

        return results
    except Exception as e:
        print(f"❌ Search error: {e}")
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
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            imageinfo = page.get('imageinfo', [])
            if imageinfo:
                return imageinfo[0].get('url')

        return None
    except Exception as e:
        print(f"❌ Error URL: {e}")
        return None

def download_video(url: str, filename: str, category: str) -> bool:
    "Download one video."
    try:
        category_dir = DOWNLOAD_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize the filename
        clean_name = filename.replace(' ', '_')
        filepath = category_dir / clean_name

        if filepath.exists():
            print(f"  ⏭️ Already downloaded")
            return True

        print(f"  📥 Download...")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"  ✅ Saved: {clean_name}")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("📥 WIKIMEDIA COMMONS DOWNLOADER")
    print("🆓 No API key required !")
    print("=" * 60)
    print()

    print("📚 Available categories:")
    for i, cat in enumerate(KEYWORDS.keys(), 1):
        print(f"  {i}. {cat}")
    print()

    choice = input("Download all categories? (yes/no): ")
    if choice.lower() not in ['oui', 'o', 'yes', 'y']:
        print("❌ Cancelled")
        return

    videos_per_keyword = int(input("Videos per keyword (1-5): ") or "2")

    print()
    print("🚀 Download in progress...")
    print("⚠️ Wikimedia may respond slowly; please wait...")
    print("=" * 60)
    print()

    total_downloaded = 0

    for category, keywords in KEYWORDS.items():
        print(f"\n📂 Category: {category.upper()}")
        print("-" * 60)

        for keyword in keywords:
            print(f"\n🔍 Search: {keyword}")

            # Search
            videos = search_wikimedia_videos(keyword, videos_per_keyword * 2)

            if not videos:
                print("  ❌ No videos found")
                continue

            print(f"  📹 Found: {len(videos)} videos")

            # Download
            downloaded = 0
            for video_title in videos[:videos_per_keyword]:
                print(f"\n  📝 {video_title}")

                # Resolve the media URL
                video_url = get_video_url(video_title)
                if not video_url:
                    print("  ❌ URL not found")
                    continue

                # Download
                if download_video(video_url, video_title, category):
                    downloaded += 1
                    total_downloaded += 1

                if downloaded >= videos_per_keyword:
                    break

                time.sleep(2)  # Rate-limit requests to the source

    print()
    print("=" * 60)
    print(f"✅ Download completed : {total_downloaded} videos")
    print(f"📁 Folder: {DOWNLOAD_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
