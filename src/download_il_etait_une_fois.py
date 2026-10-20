"Educational topic searches inspired by the French Once Upon a Time series."
import subprocess
from pathlib import Path

try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

DOWNLOAD_DIR = DATA_DIR / "downloaded"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Topics inspired by Once Upon a Time
THEMES_EDUCATIFS = {
    'vie_corps_humain': {
        'series': 'Il était une fois... la Vie',
        'episodes': [
            'blood circulation', 'heart beating', 'digestive system',
            'respiratory system', 'brain neurons', 'immune system',
            'DNA cell', 'skeleton bones', 'muscles movement',
            'eye vision', 'ear hearing', 'skin anatomy',
            'vaccination antibodies', 'birth pregnancy', 'growth development'
        ]
    },

    'histoire': {
        'series': 'Il était une fois... l\'Homme',
        'episodes': [
            'prehistoric caveman', 'ancient egypt pharaoh', 'ancient greece',
            'roman empire', 'viking ships', 'medieval castle',
            'renaissance art', 'french revolution', 'industrial revolution',
            'world war footage', 'ancient china', 'mesopotamia',
            'aztec maya civilization', 'knights armor'
        ]
    },

    'espace': {
        'series': 'Il était une fois... l\'Espace',
        'episodes': [
            'solar system planets', 'galaxy milky way', 'space station ISS',
            'rocket launch', 'moon landing', 'mars exploration',
            'satellites orbit', 'astronaut spacewalk', 'nebula stars',
            'black hole', 'comet asteroid', 'telescope observatory',
            'space shuttle', 'jupiter saturn', 'sun solar flare'
        ]
    },

    'decouvreurs': {
        'series': 'Il était une fois... les Découvreurs',
        'episodes': [
            'archimedes physics', 'galileo telescope', 'newton gravity',
            'einstein relativity', 'marie curie radioactivity', 'pasteur vaccine',
            'edison lightbulb', 'wright brothers airplane', 'bell telephone',
            'marconi radio', 'tesla electricity', 'darwin evolution',
            'lavoisier chemistry', 'mendeleev periodic table'
        ]
    },

    'explorateurs': {
        'series': 'Il était une fois... les Explorateurs',
        'episodes': [
            'columbus ships', 'magellan voyage', 'marco polo silk road',
            'vasco gama', 'james cook pacific', 'livingstone africa',
            'amundsen polar', 'hillary everest', 'cousteau ocean',
            'armstrong moon', 'viking exploration'
        ]
    },

    'nature_terre': {
        'series': 'Thèmes Nature & Terre',
        'episodes': [
            'volcano eruption', 'earthquake', 'tsunami wave', 'hurricane storm',
            'tornado', 'lightning thunder', 'rainbow formation', 'waterfall',
            'glacier ice', 'desert sand', 'rainforest jungle', 'coral reef',
            'ocean waves', 'mountain formation', 'river delta',
            'aurora borealis', 'geyser', 'canyon erosion'
        ]
    },

    'animaux': {
        'series': 'Animaux du Monde',
        'episodes': [
            'lion hunting', 'elephant herd', 'whale swimming', 'dolphin playing',
            'eagle flying', 'penguin colony', 'butterfly metamorphosis',
            'bee pollination', 'spider web', 'ant colony',
            'shark ocean', 'bear fishing', 'giraffe savanna',
            'monkey jungle', 'wolf pack', 'bird migration'
        ]
    },

    'inventions': {
        'series': 'Grandes Inventions',
        'episodes': [
            'printing press', 'steam engine', 'automobile car',
            'airplane flight', 'radio broadcast', 'television',
            'computer technology', 'internet network', 'telephone communication',
            'camera photography', 'microscope science', 'wheel invention'
        ]
    }
}

def download_theme_videos(theme_name: str, theme_data: dict, max_per_keyword: int = 2):
    "Run the download theme videos workflow."
    category_dir = DOWNLOAD_DIR / theme_name
    category_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"THEME: {theme_data['series']}")
    print(f"{'=' * 60}\n")

    downloaded = 0

    for i, episode_theme in enumerate(theme_data['episodes'], 1):
        print(f"[{i}/{len(theme_data['episodes'])}] {episode_theme}")

        # Build the yt-dlp command
        cmd = [
            'yt-dlp',
            f'ytsearch{max_per_keyword}:{episode_theme} français documentaire éducatif',
            '--max-filesize', '25M',
            '--max-downloads', str(max_per_keyword),
            '--match-filter', 'duration < 300',  # Max 5 min
            '-o', str(category_dir / f'{theme_name}_{episode_theme.replace(" ", "_")[:40]}_%(id)s.%(ext)s'),
            '--format', 'best[height<=720]',
            '--no-playlist',
            '--quiet',
            '--no-warnings',
            '--ignore-errors'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)

            if result.returncode == 0:
                # Count new files
                new_files = [f for f in category_dir.glob(f'{theme_name}_*')
                           if episode_theme.replace(" ", "_")[:20] in f.name]
                count = len(new_files)
                if count > 0:
                    print(f"  ✅ {count} video(s)")
                    downloaded += count
                else:
                    print(f"  ⏭️ None")
            else:
                print(f"  ⚠️ Error")
        except Exception as e:
            print(f"  ❌ {str(e)[:50]}")

    print(f"\n{theme_name}: {downloaded} videos downloaded")
    return downloaded

def main():
    print("=" * 60)
    print("ONCE UPON A TIME - EDUCATIONAL SEARCHES")
    print("=" * 60)
    print()
    print("Based on topics from the educational series:")
    print()

    for theme, data in THEMES_EDUCATIFS.items():
        print(f"  📺 {data['series']}")
        print(f"     └─ {len(data['episodes'])} topics")

    print()
    print(f"Total : {sum(len(d['episodes']) for d in THEMES_EDUCATIFS.values())} topics")
    print("Videos per topic : 1-2")
    print("Estimated total : ~150-250 videos")
    print()

    # Check yt-dlp availability
    try:
        subprocess.run(['yt-dlp', '--version'],
                      capture_output=True, timeout=5, check=True)
    except:
        print("❌ ERROR: yt-dlp not installed !")
        print("   pip install yt-dlp")
        input("\nPress ENTER...")
        return

    # Choose a preset
    print("Available categories :")
    themes_list = list(THEMES_EDUCATIFS.keys())
    for i, theme in enumerate(themes_list, 1):
        print(f"  {i}. {theme}")
    print(f"  0. ALL")
    print()

    choice = input("Choose (0 for all) : ").strip()

    if choice == '0':
        selected = THEMES_EDUCATIFS.items()
    elif choice.isdigit() and 1 <= int(choice) <= len(themes_list):
        theme_name = themes_list[int(choice) - 1]
        selected = [(theme_name, THEMES_EDUCATIFS[theme_name])]
    else:
        print("Invalid choice")
        return

    print()
    videos_per = input("Videos per topic (1-3, default 2) : ").strip() or "2"
    videos_per = int(videos_per)

    print()
    print("🚀 Download in progress...")

    total = 0
    stats = {}

    for theme_name, theme_data in selected:
        count = download_theme_videos(theme_name, theme_data, videos_per)
        stats[theme_name] = count
        total += count

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for theme, count in stats.items():
        print(f"{theme:25s}: {count:3d} videos")
    print(f"\nTOTAL: {total} videos downloaded")
    print(f"Folder: {DOWNLOAD_DIR}")
    print("=" * 60)
    print()
    print("NEXT STEPS:")
    print("  1. Copy videos into the data folder")
    print("  2. RUN_LIGHT.bat (analyze)")
    print("  3. ORGANIZE.bat (organize)")

if __name__ == "__main__":
    main()
