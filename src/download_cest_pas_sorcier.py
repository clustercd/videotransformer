"Topic searches inspired by the French educational show C'est pas sorcier."
import subprocess
from pathlib import Path

try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

DOWNLOAD_DIR = DATA_DIR / "downloaded"

# Topics inspired by C'est pas sorcier
THEMES_CPS = {
    'sciences_terre': {
        'serie': 'Sciences de la Terre',
        'episodes': [
            'volcano eruption lava', 'earthquake seismic', 'tsunami wave formation',
            'tornado formation', 'hurricane cyclone', 'cave stalactite',
            'glacier ice movement', 'river erosion', 'desert sand dune',
            'mountain formation tectonic', 'ocean current', 'coral reef formation',
            'geothermal geyser', 'fossil dinosaur', 'mineral crystal formation'
        ]
    },

    'animaux_comportement': {
        'serie': 'Animaux et Comportement',
        'episodes': [
            'bee hive honey', 'ant colony organization', 'spider web construction',
            'bird nest building', 'beaver dam construction', 'dolphin echolocation',
            'bat ultrasound', 'chameleon camouflage', 'octopus intelligence',
            'wolf pack hunting', 'elephant memory', 'penguin march',
            'salmon migration spawning', 'butterfly metamorphosis lifecycle',
            'shark teeth hunting', 'owl hunting night'
        ]
    },

    'corps_sante': {
        'serie': 'Corps et Santé',
        'episodes': [
            'eye vision mechanism', 'ear hearing sound', 'brain memory learning',
            'heart circulation blood', 'lung breathing oxygen', 'muscle contraction',
            'bone skeleton structure', 'immune system defense', 'DNA genetics',
            'digestion stomach intestine', 'kidney filtration', 'skin protection',
            'nerve impulse', 'hormone gland', 'pregnancy birth development'
        ]
    },

    'comment_ca_marche': {
        'serie': 'Comment ça marche ?',
        'episodes': [
            'airplane flight aerodynamic', 'train locomotive steam', 'car engine combustion',
            'bicycle gear mechanism', 'elevator lift mechanism', 'lock key mechanism',
            'clock watch mechanism', 'camera lens photography', 'microwave cooking',
            'refrigerator cooling', 'windmill wind turbine', 'solar panel energy',
            'battery electricity storage', 'telescope mirror lens', 'microscope magnification'
        ]
    },

    'histoire_patrimoine': {
        'serie': 'Histoire et Patrimoine',
        'episodes': [
            'pyramid construction egypt', 'roman aqueduct engineering', 'medieval castle defense',
            'eiffel tower construction', 'notre dame cathedral', 'versailles palace',
            'stonehenge mystery', 'great wall china', 'colosseum rome',
            'taj mahal india', 'machu picchu peru', 'petra jordan',
            'angkor wat cambodia', 'sagrada familia barcelona'
        ]
    },

    'alimentation_agriculture': {
        'serie': 'Alimentation et Agriculture',
        'episodes': [
            'wheat bread making', 'milk cheese production', 'chocolate cocoa processing',
            'honey bee production', 'wine grape fermentation', 'olive oil pressing',
            'coffee bean roasting', 'tea leaf processing', 'rice cultivation paddy',
            'corn maize farming', 'tomato greenhouse', 'apple orchard harvest',
            'fish aquaculture farming', 'chicken egg production'
        ]
    },

    'environnement': {
        'serie': 'Environnement et Écologie',
        'episodes': [
            'recycling waste management', 'solar energy panel', 'wind turbine farm',
            'water treatment purification', 'composting organic waste', 'rainforest deforestation',
            'ocean plastic pollution', 'greenhouse effect climate', 'ozone layer protection',
            'endangered species conservation', 'sustainable agriculture', 'electric car battery',
            'carbon footprint emission', 'biodiversity ecosystem'
        ]
    },

    'transport_voyage': {
        'serie': 'Transports et Voyages',
        'episodes': [
            'tgv high speed train', 'airplane cockpit flight', 'ship cruise navigation',
            'submarine underwater', 'hot air balloon flight', 'helicopter rotor',
            'metro subway tunnel', 'cable car mountain', 'ferry boat crossing',
            'space shuttle launch', 'rocket propulsion', 'airport control tower',
            'port container shipping', 'bridge construction engineering'
        ]
    },

    'metiers': {
        'serie': 'Métiers et Professions',
        'episodes': [
            'firefighter rescue operation', 'doctor surgery hospital', 'veterinarian animal care',
            'farmer agriculture tractor', 'baker bread baking', 'chef cooking kitchen',
            'architect building design', 'engineer construction site', 'pilot airplane cockpit',
            'astronaut space station', 'scientist laboratory research', 'artist painter studio',
            'musician orchestra instrument', 'journalist news reporting'
        ]
    },

    'espace_astronomie': {
        'serie': 'Espace et Astronomie',
        'episodes': [
            'moon phases lunar', 'solar eclipse sun', 'mars exploration rover',
            'jupiter storm great spot', 'saturn rings planet', 'comet tail formation',
            'asteroid belt orbit', 'black hole gravity', 'supernova explosion',
            'galaxy formation milky way', 'constellation stars night', 'telescope observation',
            'ISS space station orbit', 'rocket launch countdown', 'satellite communication'
        ]
    }
}

def download_cps_videos(theme_name: str, theme_data: dict, videos_per: int = 2):
    "Run the download cps videos workflow."
    category_dir = DOWNLOAD_DIR / f"cps_{theme_name}"
    category_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"THEME CPS: {theme_data['serie']}")
    print(f"{'=' * 60}\n")

    downloaded = 0

    for i, episode_theme in enumerate(theme_data['episodes'], 1):
        print(f"[{i}/{len(theme_data['episodes'])}] {episode_theme}")

        cmd = [
            'yt-dlp',
            f'ytsearch{videos_per}:{episode_theme} français documentaire éducatif',
            '--max-filesize', '30M',
            '--max-downloads', str(videos_per),
            '--match-filter', 'duration < 420',  # Max 7 min
            '-o', str(category_dir / f'cps_{theme_name}_{episode_theme.replace(" ", "_")[:35]}_%(id)s.%(ext)s'),
            '--format', 'best[height<=720]',
            '--no-playlist',
            '--quiet',
            '--no-warnings',
            '--ignore-errors'
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=90)
            new_files = [f for f in category_dir.glob(f'cps_{theme_name}_*')
                        if episode_theme.split()[0] in f.name]
            count = min(videos_per, len(new_files))
            if count > 0:
                print(f"  ✅ {count} video(s)")
                downloaded += count
            else:
                print(f"  ⏭️ None")
        except:
            print(f"  ❌ Error")

    print(f"\n{theme_name}: {downloaded} videos")
    return downloaded

def main():
    print("=" * 60)
    print("C'EST PAS SORCIER - EDUCATIONAL SEARCHES")
    print("=" * 60)
    print()
    print("Topics inspired by the French science show:")
    print()

    for theme, data in THEMES_CPS.items():
        print(f"  🔬 {data['serie']}")
        print(f"     └─ {len(data['episodes'])} topics")

    print()
    print(f"Total : {sum(len(d['episodes']) for d in THEMES_CPS.values())} topics")
    print()

    # Check yt-dlp availability
    try:
        subprocess.run(['yt-dlp', '--version'],
                      capture_output=True, timeout=5, check=True)
    except:
        print("❌ yt-dlp not installed !")
        print("   pip install yt-dlp")
        input("\nPress ENTER...")
        return

    # Choose a preset
    themes_list = list(THEMES_CPS.keys())
    print("Available categories :")
    for i, theme in enumerate(themes_list, 1):
        print(f"  {i}. {THEMES_CPS[theme]['serie']}")
    print(f"  0. ALL")
    print()

    choice = input("Choose (0 for all) : ").strip()

    if choice == '0':
        selected = THEMES_CPS.items()
    elif choice.isdigit() and 1 <= int(choice) <= len(themes_list):
        theme_name = themes_list[int(choice) - 1]
        selected = [(theme_name, THEMES_CPS[theme_name])]
    else:
        print("Invalid choice")
        return

    videos_per = input("Videos per topic (1-3, default 2) : ").strip() or "2"
    videos_per = int(videos_per)

    print("\n🚀 Download...")

    total = 0
    stats = {}

    for theme_name, theme_data in selected:
        count = download_cps_videos(theme_name, theme_data, videos_per)
        stats[theme_name] = count
        total += count

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for theme, count in stats.items():
        print(f"{THEMES_CPS[theme]['serie']:30s}: {count:3d} videos")
    print(f"\nTOTAL: {total} videos")
    print(f"Folder: {DOWNLOAD_DIR}")

if __name__ == "__main__":
    main()
