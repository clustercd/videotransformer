"Describe and optionally rename videos with local BLIP inference. Initial model download requires network access."

import cv2
import torch
from pathlib import Path
try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

from typing import List
import json
import re
from PIL import Image

try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    BLIP_AVAILABLE = True
except ImportError:
    print("⚠️ Transformers is unavailable")
    print("Install: pip install transformers pillow torch opencv-python")
    BLIP_AVAILABLE = False

# Settings
VIDEOS_DIR = DATA_DIR
FRAMES_TO_EXTRACT = 2
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv', '.mpg']

processor = None
model = None

def load_vision_model():
    "Load the BLIP base model."
    global processor, model

    if not BLIP_AVAILABLE:
        return False

    try:
        print("📥 Loading BLIP base (approximately 1 GB)...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"   Device: {device}")

        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        model.to(device)

        print("✅ Model loaded")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def extract_frames(video_path: Path, num_frames: int = 2) -> List[Image.Image]:
    "Extract representative video frames."
    frames = []

    try:
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames == 0:
            return []

        positions = [
            int(total_frames * 0.5),
            int(total_frames * 0.8)
        ][:num_frames]

        for pos in positions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()

            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                pil_image.thumbnail((384, 384), Image.Resampling.LANCZOS)
                frames.append(pil_image)

        cap.release()
    except Exception as e:
        print(f"❌ Frame extraction error: {e}")

    return frames

def analyze_video(frames: List[Image.Image]) -> str:
    "Run the analyze video workflow."
    if not model or not frames:
        return None

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        descriptions = []

        for i, frame in enumerate(frames):
            inputs = processor(frame, return_tensors="pt").to(device)
            out = model.generate(**inputs, max_length=20)
            caption = processor.decode(out[0], skip_special_tokens=True)
            descriptions.append(caption)
            print(f"    Frame {i+1}: {caption}")

        # Simple word substitutions
        keywords = {
            'cat': 'chat', 'dog': 'chien', 'bird': 'oiseau',
            'rabbit': 'lapin', 'horse': 'cheval', 'cow': 'vache'
        }

        all_text = " ".join(descriptions).lower()
        found = [fr for en, fr in keywords.items() if en in all_text]

        if found:
            return "_".join(found[:2])

        words = [w for w in all_text.split() if len(w) > 3][:2]
        return "_".join(words) if words else "video"

    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return None

def rename_video(video_path: Path, new_name: str, dry_run: bool) -> bool:
    "Rename a video, or preview the proposed name."
    try:
        new_path = video_path.parent / f"{new_name}{video_path.suffix}"

        if new_path.exists() and new_path != video_path:
            counter = 1
            while new_path.exists():
                new_path = video_path.parent / f"{new_name}_{counter}{video_path.suffix}"
                counter += 1

        if dry_run:
            print(f"🔄 PREVIEW: {video_path.name} → {new_path.name}")
        else:
            video_path.rename(new_path)
            print(f"✅ RENAMED: {video_path.name} → {new_path.name}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    "Run the command-line workflow."
    print("=" * 60)
    print("🎬 VIDEOTRANSFORMER - LIGHTWEIGHT ANALYSIS")
    print("=" * 60)
    print()

    if not BLIP_AVAILABLE or not load_vision_model():
        print("❌ Could not load the model")
        return

    print(f"📁 Folder: {VIDEOS_DIR}")
    print("💻 100% LOCAL")
    print("=" * 60)
    print()

    # Find videos with lowercase and uppercase extensions
    videos = []
    for ext in VIDEO_EXTENSIONS:
        videos.extend(VIDEOS_DIR.glob(f"*{ext}"))
        videos.extend(VIDEOS_DIR.glob(f"*{ext.upper()}"))

    if not videos:
        print("❌ No videos found in the data folder")
        return

    print(f"📹 {len(videos)} videos found")
    print()

    # Ask for confirmation
    response = input("Start analysis? (yes/no): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("❌ Cancelled")
        return

    dry_run = input("\nRename the files? (yes/no): ").lower() not in ['oui', 'o', 'yes', 'y']

    if not dry_run:
        confirm = input("Confirm actual file renaming? (yes/no): ")
        if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
            dry_run = True
            print("→ Switching to preview mode")

    print()
    print("🚀 Processing...")
    print("=" * 60)
    print()

    # Process each video
    results = {'success': [], 'failed': [], 'skipped': []}

    for i, video_path in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] {video_path.name}")

        # Skip filenames that are already descriptive
        if len(video_path.stem) > 5 and '_' in video_path.stem:
            print("  ⏭️ Already descriptive")
            results['skipped'].append(video_path.name)
            continue

        # Extract frames
        print("  📸 Extracting frames...")
        frames = extract_frames(video_path)

        if not frames:
            print("  ❌ Frame extraction failed")
            results['failed'].append(video_path.name)
            continue

        # Analyze
        print("  🤖 Analysis...")
        suggested_name = analyze_video(frames)

        if not suggested_name:
            print("  ❌ Analysis failed")
            results['failed'].append(video_path.name)
            continue

        print(f"  💡 Suggestion: {suggested_name}")

        # Rename
        if rename_video(video_path, suggested_name, dry_run):
            results['success'].append((video_path.name, suggested_name))
        else:
            results['failed'].append(video_path.name)

        print()

    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Succeeded: {len(results['success'])}")
    print(f"⏭️ Skipped: {len(results['skipped'])}")
    print(f"❌ Failed: {len(results['failed'])}")

    # Save results
    results_file = VIDEOS_DIR / "results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results: {results_file}")

if __name__ == "__main__":
    main()
