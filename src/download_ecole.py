"French educational video searches grouped by school level."
import subprocess
from pathlib import Path

try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

DOWNLOAD_DIR = DATA_DIR / "downloaded"

# Search presets by French school level
PROGRAMMES_SCOLAIRES = {
    'maternelle': {
        'niveau': 'Maternelle (3-5 ans)',
        'themes': [
            'alphabet letters ABC', 'numbers counting 1 to 10', 'colors learning',
            'shapes circle square triangle', 'animals farm zoo', 'fruits vegetables',
            'seasons weather', 'family members', 'body parts kids',
            'nursery rhymes songs', 'days of week', 'emotions feelings kids'
        ]
    },

    'cp_ce1': {
        'niveau': 'CP-CE1 (6-8 ans)',
        'themes': [
            'reading phonics kids', 'addition subtraction simple', 'telling time clock',
            'money coins counting', 'plants growth seeds', 'water cycle kids',
            'solar system planets kids', 'animals habitats', 'food groups nutrition',
            'recycling environment kids', 'maps compass direction', 'community helpers jobs'
        ]
    },

    'ce2_cm1': {
        'niveau': 'CE2-CM1 (8-10 ans)',
        'themes': [
            'multiplication division', 'fractions decimals', 'grammar verbs',
            'france geography regions', 'europe countries map', 'roman empire history',
            'photosynthesis plants', 'states of matter solid liquid', 'electricity circuit',
            'food chain ecosystem', 'human skeleton bones', 'magnets magnetism'
        ]
    },

    'cm2_6eme': {
        'niveau': 'CM2-6ème (10-12 ans)',
        'themes': [
            'french revolution history', 'world war documentary', 'ancient egypt civilization',
            'cell biology microscope', 'digestive system', 'solar system astronomy',
            'water cycle ecosystem', 'renewable energy', 'france rivers mountains',
            'medieval period castle', 'renaissance art', 'exploration columbus magellan'
        ]
    },

    'college': {
        'niveau': 'Collège (12-15 ans)',
        'themes': [
            'photosynthesis cellular', 'genetics DNA heredity', 'periodic table elements',
            'chemical reactions', 'newton laws physics', 'electricity magnetism',
            'industrial revolution', 'world geography continents', 'plate tectonics',
            'respiratory circulatory system', 'algebra equations', 'geometry theorems'
        ]
    }
}

# General topics for all school levels
SUJETS_UNIVERSELS = {
    'comment_ca_marche': [
        'how airplane flies', 'how car engine works', 'how computer works',
        'how internet works', 'how phone works', 'how camera works',
        'how refrigerator works', 'how bicycle works', 'how clock works'
    ],

    'animaux_incroyables': [
        'cheetah fastest animal', 'blue whale largest', 'hummingbird smallest',
        'giraffe tallest animal', 'chameleon changing color', 'octopus intelligence',
        'ants strength teamwork', 'dolphin communication', 'elephant memory'
    ],

    'inventions_qui_changent': [
        'wheel invention history', 'printing press gutenberg', 'electricity tesla edison',
        'airplane wright brothers', 'telephone bell invention', 'internet creation',
        'computer evolution', 'vaccine pasteur', 'penicillin fleming'
    ],

    'pays_du_monde': [
        'japan culture traditions', 'egypt pyramids history', 'brazil amazon rainforest',
        'australia great barrier reef', 'china great wall', 'india taj mahal',
        'russia kremlin moscow', 'kenya safari wildlife', 'peru machu picchu'
    ],

    'sports_olympiques': [
        'swimming olympic', 'gymnastics olympic', 'track and field athletics',
        'basketball game', 'soccer football world cup', 'tennis match',
        'cycling race tour', 'skiing olympic winter', 'ice skating figure'
    ],

    'instruments_musique': [
        'piano how it works', 'guitar strings vibration', 'violin bow technique',
        'drums percussion', 'trumpet brass instrument', 'flute woodwind',
        'saxophone jazz', 'organ pipes', 'harp strings'
    ]
}

def download_school_level(level_name: str, level_data: dict, videos_per: int = 2):
    "Run the download school level workflow."
    category_dir = DOWNLOAD_DIR / f"ecole_{level_name}"
    category_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"LEVEL: {level_data['niveau']}")
    print(f"{'=' * 60}\n")

    downloaded = 0

    for i, theme in enumerate(level_data['themes'], 1):
        print(f"[{i}/{len(level_data['themes'])}] {theme}")

        cmd = [
            'yt-dlp',
            f'ytsearch{videos_per}:{theme} français pour enfants éducatif',
            '--max-filesize', '25M',
            '--max-downloads', str(videos_per),
            '--match-filter', 'duration < 360',
            '-o', str(category_dir / f'{level_name}_{theme.replace(" ", "_")[:35]}_%(id)s.%(ext)s'),
            '--format', 'best[height<=720]',
            '--no-playlist',
            '--quiet',
            '--no-warnings',
            '--ignore-errors'
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=90)
            new_files = list(category_dir.glob(f'{level_name}_*'))
            count = len([f for f in new_files if theme.split()[0] in f.name])
            if count > 0:
                print(f"  ✅ {count}")
                downloaded += count
            else:
                print(f"  ⏭️")
        except:
            print(f"  ❌")

    print(f"\n{level_name}: {downloaded} videos")
    return downloaded

def main():
    print("=" * 60)
    print("SCHOOL CURRICULUM - VIDEO SEARCHES")
    print("=" * 60)
    print()
    print("Content grouped by French school level:")
    print()

    for level, data in PROGRAMMES_SCOLAIRES.items():
        print(f"  📚 {data['niveau']}")
        print(f"     └─ {len(data['themes'])} topics")

    print()
    print("  + General topics for all levels")
    for cat, themes in SUJETS_UNIVERSELS.items():
        print(f"    • {cat}: {len(themes)} topics")

    print()

    # Check yt-dlp availability
    try:
        subprocess.run(['yt-dlp', '--version'],
                      capture_output=True, timeout=5, check=True)
    except:
        print("❌ yt-dlp not installed !")
        input("\nPress ENTER...")
        return

    print("\nCHOICES:")
    print("  1. By school level")
    print("  2. General topics")
    print("  3. Both")

    choice = input("\nOption (1-3) : ").strip()

    videos_per = int(input("Videos per topic (1-3, default 2) : ").strip() or "2")

    print("\n🚀 Download...")

    total = 0

    if choice in ['1', '3']:
        for level_name, level_data in PROGRAMMES_SCOLAIRES.items():
            total += download_school_level(level_name, level_data, videos_per)

    if choice in ['2', '3']:
        for cat_name, themes in SUJETS_UNIVERSELS.items():
            cat_dir = DOWNLOAD_DIR / f"universel_{cat_name}"
            cat_dir.mkdir(parents=True, exist_ok=True)
            print(f"\n{'=' * 60}")
            print(f"CATEGORY: {cat_name}")
            print(f"{'=' * 60}\n")

            for theme in themes:
                print(f"{theme}... ", end='', flush=True)
                cmd = [
                    'yt-dlp',
                    f'ytsearch{videos_per}:{theme} français documentaire',
                    '--max-filesize', '25M',
                    '-o', str(cat_dir / f'{cat_name}_{theme.replace(" ", "_")[:30]}_%(id)s.%(ext)s'),
                    '--format', 'best[height<=720]',
                    '--quiet', '--no-warnings', '--ignore-errors'
                ]
                try:
                    subprocess.run(cmd, capture_output=True, timeout=90)
                    print("✅")
                    total += videos_per
                except:
                    print("❌")

    print()
    print("=" * 60)
    print(f"TOTAL: ~{total} videos downloaded")
    print(f"Folder: {DOWNLOAD_DIR}")

if __name__ == "__main__":
    main()
