"Analyze up to five local videos with BLIP."
import cv2
import torch
from pathlib import Path
try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

VIDEOS_DIR = DATA_DIR
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv', '.mpg']

def extract_frame(video_path):
    "Extract a frame from the middle of a video."
    cap = cv2.VideoCapture(str(video_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total == 0:
        cap.release()
        return None

    cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)
    pil_image.thumbnail((384, 384), Image.Resampling.LANCZOS)
    return pil_image

def main():
    print("🔧 Loading BLIP...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"   Device: {device}")

    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    model.to(device)
    print("✅ Model loaded\n")

    # Find up to five videos
    videos = []
    for ext in VIDEO_EXTENSIONS:
        videos.extend(VIDEOS_DIR.glob(f"*{ext}"))
        if len(videos) >= 5:
            break

    videos = videos[:5]

    print(f"🎬 Testing {len(videos)} videos:\n")

    for i, video in enumerate(videos, 1):
        print(f"[{i}/5] {video.name}")

        frame = extract_frame(video)
        if not frame:
            print("  ❌ Frame extraction failed\n")
            continue

        inputs = processor(frame, return_tensors="pt").to(device)
        out = model.generate(**inputs, max_length=20)
        caption = processor.decode(out[0], skip_special_tokens=True)

        print(f"  📝 Description: {caption}")
        print(f"  💡 Suggested name: {caption.lower().replace(' ', '_')[:30]}\n")

    print("=" * 60)
    print("✅ Test completed !")
    print(f"📊 Total available videos: {len(list(VIDEOS_DIR.glob('*.mp4')))} MP4, ", end='')
    print(f"{len(list(VIDEOS_DIR.glob('*.wmv')))} WMV, ", end='')
    print(f"{len(list(VIDEOS_DIR.glob('*.mpg')))} MPG")

if __name__ == "__main__":
    main()
