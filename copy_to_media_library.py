"Copy organized MP4 videos into MediaLibrary/Encarta."
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from src.settings import DATA_DIR

# Paths
PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = DATA_DIR / "organized"
MEDIA_LIBRARY_HOME = Path(os.environ.get("MEDIA_LIBRARY_HOME", Path.home() / "MediaLibrary"))
ENCARTA_DIR = MEDIA_LIBRARY_HOME / "data" / "encarta"
DEST_DIR = ENCARTA_DIR / "videos_mp4"
INDEX_FILE = ENCARTA_DIR / "encarta_index.json"

def main():
    if not SOURCE_DIR.is_dir():
        raise FileNotFoundError("Organized source directory not found; run ORGANIZE.bat first.")
    # Create the destination directory
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # Statistics
    stats = {
        "total_copied": 0,
        "by_category": {},
        "timestamp": datetime.now().isoformat()
    }

    # API index
    videos_index = []

    print("🎬 COPY VIDEOS TO MEDIA_LIBRARY/ENCARTA")
    print("=" * 60)

    # Visit each category
    for category_dir in SOURCE_DIR.iterdir():
        if not category_dir.is_dir():
            continue

        category = category_dir.name
        stats["by_category"][category] = 0

        print(f"\n📂 Category: {category}")

        # Copy MP4 files only
        mp4_files = list(category_dir.glob("*.mp4"))

        for video_file in mp4_files:
            # Prefix the filename with its category
            new_name = f"{category}_{video_file.name}"
            dest_path = DEST_DIR / new_name

            # Copy the file
            shutil.copy2(video_file, dest_path)

            # Add the file to the index
            file_size = dest_path.stat().st_size
            videos_index.append({
                "id": dest_path.stem,
                "filename": new_name,
                "category": category,
                "size": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "path": str(dest_path.relative_to(ENCARTA_DIR))
            })

            stats["total_copied"] += 1
            stats["by_category"][category] += 1

        print(f"  ✅ {len(mp4_files)} videos MP4 copied")

    # Write the JSON index
    index_data = {
        "version": "1.0",
        "created_at": stats["timestamp"],
        "source": "VideoTransformer AI Analysis",
        "statistics": {
            "total_videos": stats["total_copied"],
            "by_category": stats["by_category"]
        },
        "content": {
            "videos": videos_index
        }
    }

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    print(f"✅ Total videos copied: {stats['total_copied']}")
    print(f"📁 Destination: {DEST_DIR}")
    print(f"📄 Index created: {INDEX_FILE}")
    print("\n📈 By category:")
    for cat, count in sorted(stats["by_category"].items(), key=lambda x: x[1], reverse=True):
        print(f"  • {cat}: {count} videos")

    print("\n✨ Completed. Videos are now available in MediaLibrary/Encarta")


if __name__ == "__main__":
    main()
