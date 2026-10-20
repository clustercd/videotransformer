"Build an age, subject and topic hierarchy for Andrew/Encarta."
import json
import os
from pathlib import Path
try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

import shutil


ANDREW_HOME = Path(os.environ.get("ANDREW_HOME", Path.home() / "Andrew"))
ORGANIZED_DIR = ANDREW_HOME / "data" / "encyclopedie"

# AGE, SUBJECT AND TOPIC HIERARCHY
STRUCTURE_ANDREW = {
    'par_age': {
        'nom': '📚 By age',
        'description': 'Age-appropriate content',
        'categories': {
            '3-5_ans_maternelle': {
                'mots_cles': ['alphabet', 'colors', 'numbers', 'shapes', 'animals farm',
                             'nursery', 'counting', 'fruits', 'family', 'body parts'],
                'emoji': '👶'
            },
            '6-8_ans_cp_ce1': {
                'mots_cles': ['reading', 'addition', 'subtraction', 'clock', 'plants growth',
                             'water cycle kids', 'solar system kids', 'maps'],
                'emoji': '📖'
            },
            '8-10_ans_ce2_cm1': {
                'mots_cles': ['multiplication', 'fractions', 'france geography', 'roman empire',
                             'photosynthesis', 'electricity circuit', 'food chain'],
                'emoji': '🧮'
            },
            '10-12_ans_cm2_6eme': {
                'mots_cles': ['revolution', 'world war', 'egypt', 'cell biology',
                             'digestive system', 'medieval', 'exploration'],
                'emoji': '🌍'
            },
            '12-15_ans_college': {
                'mots_cles': ['genetics', 'dna', 'periodic table', 'chemical reaction',
                             'newton', 'industrial revolution', 'algebra'],
                'emoji': '🔬'
            }
        }
    },

    'par_matiere': {
        'nom': '📕 By school subject',
        'description': 'School subject categories',
        'categories': {
            'sciences_vie_terre': {
                'mots_cles': ['animal', 'plant', 'cell', 'biology', 'ecosystem', 'nature',
                             'volcano', 'earthquake', 'weather', 'climate', 'ocean'],
                'emoji': '🌱',
                'sous_categories': {
                    'biologie': ['cell', 'dna', 'genetics', 'evolution', 'organism'],
                    'geologie': ['volcano', 'earthquake', 'rock', 'fossil', 'mountain'],
                    'ecologie': ['ecosystem', 'environment', 'recycling', 'pollution']
                }
            },
            'histoire_geographie': {
                'mots_cles': ['history', 'ancient', 'medieval', 'war', 'revolution',
                             'france', 'geography', 'country', 'city', 'monument'],
                'emoji': '🏛️',
                'sous_categories': {
                    'prehistoire': ['prehistoric', 'caveman', 'stone age', 'neanderthal'],
                    'antiquite': ['egypt', 'greece', 'rome', 'mesopotamia'],
                    'moyen_age': ['medieval', 'castle', 'knight', 'viking'],
                    'temps_modernes': ['renaissance', 'revolution', 'industrial'],
                    'epoque_contemporaine': ['world war', 'modern']
                }
            },
            'physique_chimie': {
                'mots_cles': ['physics', 'chemistry', 'electricity', 'magnet', 'force',
                             'energy', 'atom', 'molecule', 'reaction', 'experiment'],
                'emoji': '⚡',
                'sous_categories': {
                    'physique': ['gravity', 'force', 'energy', 'electricity', 'magnet'],
                    'chimie': ['atom', 'molecule', 'reaction', 'element', 'periodic']
                }
            },
            'mathematiques': {
                'mots_cles': ['math', 'number', 'count', 'addition', 'multiplication',
                             'geometry', 'algebra', 'fraction', 'equation'],
                'emoji': '🔢'
            },
            'francais_langues': {
                'mots_cles': ['reading', 'writing', 'grammar', 'verb', 'alphabet',
                             'language', 'communication'],
                'emoji': '📝'
            }
        }
    },

    'par_theme': {
        'nom': '🎨 By topic',
        'description': 'Explore by topic',
        'categories': {
            'corps_humain': {
                'mots_cles': ['heart', 'brain', 'blood', 'muscle', 'bone', 'eye', 'ear',
                             'digestive', 'respiratory', 'immune', 'cœur', 'cerveau'],
                'emoji': '🫀',
                'sous_categories': {
                    'organes': ['heart', 'brain', 'lung', 'stomach', 'kidney'],
                    'systemes': ['circulatory', 'digestive', 'respiratory', 'nervous'],
                    'sante': ['vaccine', 'immune', 'hygiene', 'nutrition']
                }
            },
            'animaux': {
                'mots_cles': ['lion', 'elephant', 'whale', 'dolphin', 'bird', 'fish',
                             'insect', 'reptile', 'mammal', 'chat', 'chien', 'oiseau'],
                'emoji': '🦁',
                'sous_categories': {
                    'mammiferes': ['lion', 'elephant', 'whale', 'dolphin', 'bear'],
                    'oiseaux': ['eagle', 'owl', 'penguin', 'bird'],
                    'aquatiques': ['fish', 'whale', 'dolphin', 'shark', 'octopus'],
                    'insectes': ['bee', 'butterfly', 'ant', 'spider']
                }
            },
            'espace_astronomie': {
                'mots_cles': ['space', 'planet', 'moon', 'star', 'galaxy', 'rocket',
                             'astronaut', 'solar system', 'mars', 'saturn', 'lune'],
                'emoji': '🚀',
                'sous_categories': {
                    'systeme_solaire': ['sun', 'mercury', 'venus', 'earth', 'mars', 'jupiter'],
                    'exploration': ['rocket', 'astronaut', 'iss', 'apollo', 'shuttle'],
                    'phenomenes': ['black hole', 'nebula', 'comet', 'asteroid', 'eclipse']
                }
            },
            'inventions_technologie': {
                'mots_cles': ['invention', 'computer', 'robot', 'internet', 'airplane',
                             'car', 'train', 'telephone', 'electricity', 'machine'],
                'emoji': '⚙️',
                'sous_categories': {
                    'transport': ['airplane', 'car', 'train', 'ship', 'bicycle'],
                    'communication': ['telephone', 'radio', 'television', 'internet'],
                    'energie': ['electricity', 'steam engine', 'solar', 'wind']
                }
            },
            'nature_environnement': {
                'mots_cles': ['tree', 'forest', 'ocean', 'river', 'mountain', 'desert',
                             'waterfall', 'glacier', 'volcano', 'rainbow', 'arbre'],
                'emoji': '🌳',
                'sous_categories': {
                    'ecosystemes': ['forest', 'desert', 'ocean', 'savanna', 'jungle'],
                    'phenomenes': ['volcano', 'earthquake', 'tornado', 'tsunami'],
                    'climat': ['weather', 'climate', 'season', 'temperature']
                }
            },
            'art_culture': {
                'mots_cles': ['painting', 'sculpture', 'music', 'museum', 'monument',
                             'louvre', 'versailles', 'eiffel', 'art', 'culture'],
                'emoji': '🎨',
                'sous_categories': {
                    'peinture': ['monet', 'van gogh', 'picasso', 'painting'],
                    'monuments': ['eiffel tower', 'pyramid', 'colosseum', 'taj mahal'],
                    'musique': ['instrument', 'orchestra', 'composer', 'mozart']
                }
            },
            'vie_quotidienne': {
                'mots_cles': ['bread', 'cheese', 'cooking', 'agriculture', 'farmer',
                             'recycling', 'water', 'food', 'pain', 'fromage'],
                'emoji': '🍞'
            },
            'sports_jeux': {
                'mots_cles': ['soccer', 'basketball', 'swimming', 'running', 'olympic',
                             'sport', 'game', 'play'],
                'emoji': '⚽'
            }
        }
    },

    'series_cultes': {
        'nom': '📺 Educational series',
        'description': 'Collections inspired by educational shows',
        'categories': {
            'il_etait_une_fois': {
                'nom': 'Il était une fois...',
                'emoji': '📺',
                'series': ['la_vie', 'lhomme', 'lespace', 'les_decouvreurs',
                          'les_explorateurs', 'nature_terre', 'animaux', 'inventions']
            },
            'cest_pas_sorcier': {
                'nom': 'C\'est pas sorcier',
                'emoji': '🔬',
                'series': ['sciences_terre', 'animaux_comportement', 'corps_sante',
                          'comment_ca_marche', 'histoire_patrimoine']
            }
        }
    }
}

def categoriser_video(filename: str, stem: str):
    "Run the categoriser video workflow."
    categories = {
        'age': [],
        'matiere': [],
        'theme': [],
        'serie': []
    }

    stem_lower = stem.lower()

    # By age
    for age, config in STRUCTURE_ANDREW['par_age']['categories'].items():
        if any(mot in stem_lower for mot in config['mots_cles']):
            categories['age'].append(age)

    # By school subject
    for matiere, config in STRUCTURE_ANDREW['par_matiere']['categories'].items():
        if any(mot in stem_lower for mot in config['mots_cles']):
            categories['matiere'].append(matiere)

    # By topic
    for theme, config in STRUCTURE_ANDREW['par_theme']['categories'].items():
        if any(mot in stem_lower for mot in config['mots_cles']):
            categories['theme'].append(theme)

    return categories

def organiser_encyclopedie():
    "Run the organiser encyclopedie workflow."
    print("=" * 60)
    print("ANDREW ENCYCLOPEDIA ORGANIZATION")
    print("=" * 60)
    print()
    print(f"📍 DESTINATION: {ORGANIZED_DIR}")
    print(f"📁 SOURCE: {DATA_DIR}")
    print()

    # Check the destination parent directory
    parent_dir = ORGANIZED_DIR.parent
    if not parent_dir.exists():
        print(f"❌ ERROR: Directory {parent_dir} does not exist !")
        print("   Check the ANDREW_HOME environment variable:")
        input("\nPress ENTER...")
        return

    # Create the directory structure
    ORGANIZED_DIR.mkdir(parents=True, exist_ok=True)

    # Main directory structure
    for dimension, config in STRUCTURE_ANDREW.items():
        if dimension == 'series_cultes':
            continue

        dim_dir = ORGANIZED_DIR / dimension
        dim_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{config['nom']}")
        print(f"  {config['description']}")

        for cat_name, cat_config in config['categories'].items():
            cat_dir = dim_dir / cat_name
            cat_dir.mkdir(parents=True, exist_ok=True)

            emoji = cat_config.get('emoji', '📁')
            print(f"  {emoji} {cat_name}")

            # Create configured subcategories
            if 'sous_categories' in cat_config:
                for sous_cat in cat_config['sous_categories'].keys():
                    sous_dir = cat_dir / sous_cat
                    sous_dir.mkdir(parents=True, exist_ok=True)

    # Find all videos
    all_videos = []
    for ext in ['.mp4', '.avi', '.wmv', '.mpg', '.AVI', '.WMV', '.MPG', '.webm']:
        all_videos.extend(DATA_DIR.glob(f"**/*{ext}"))

    # Exclude organized copies and desktop metadata
    all_videos = [v for v in all_videos if 'encyclopedie_andrew' not in str(v)
                  and 'organized' not in str(v) and v.name != 'desktop.ini']

    print(f"\n\n📹 {len(all_videos)} videos to organize...")
    print()

    # Full catalog
    catalogue = {
        'par_age': {},
        'par_matiere': {},
        'par_theme': {},
        'index_global': []
    }

    stats = {
        'age': {},
        'matiere': {},
        'theme': {}
    }

    # Organize each video
    for i, video in enumerate(all_videos, 1):
        if i % 50 == 0:
            print(f"  Progresss: {i}/{len(all_videos)}")

        cats = categoriser_video(video.name, video.stem)

        video_info = {
            'nom': video.name,
            'stem': video.stem,
            'taille': video.stat().st_size,
            'categories': cats
        }

        # Copy into each matching category
        for age in cats['age']:
            dest = ORGANIZED_DIR / 'par_age' / age / video.name
            if not dest.exists():
                shutil.copy2(video, dest)
            stats['age'][age] = stats['age'].get(age, 0) + 1

        for matiere in cats['matiere']:
            dest = ORGANIZED_DIR / 'par_matiere' / matiere / video.name
            if not dest.exists():
                shutil.copy2(video, dest)
            stats['matiere'][matiere] = stats['matiere'].get(matiere, 0) + 1

        for theme in cats['theme']:
            dest = ORGANIZED_DIR / 'par_theme' / theme / video.name
            if not dest.exists():
                shutil.copy2(video, dest)
            stats['theme'][theme] = stats['theme'].get(theme, 0) + 1

        catalogue['index_global'].append(video_info)

    # Save the catalog
    catalogue_file = ORGANIZED_DIR / "catalogue_andrew.json"
    with open(catalogue_file, 'w', encoding='utf-8') as f:
        json.dump(catalogue, f, indent=2, ensure_ascii=False)

    # Write a Markdown index
    readme = ORGANIZED_DIR / "INDEX.md"
    with open(readme, 'w', encoding='utf-8') as f:
        f.write("# 📚 ANDREW ENCYCLOPEDIA\n\n")
        f.write(f"Total : {len(all_videos)} educational videos\n\n")

        f.write("## 📚 By age\n\n")
        for age, count in sorted(stats['age'].items()):
            emoji = STRUCTURE_ANDREW['par_age']['categories'][age]['emoji']
            f.write(f"- {emoji} **{age.replace('_', ' ').title()}** : {count} videos\n")

        f.write("\n## 📕 By subject\n\n")
        for mat, count in sorted(stats['matiere'].items()):
            emoji = STRUCTURE_ANDREW['par_matiere']['categories'][mat]['emoji']
            f.write(f"- {emoji} **{mat.replace('_', ' ').title()}** : {count} videos\n")

        f.write("\n## 🎨 By topic\n\n")
        for theme, count in sorted(stats['theme'].items()):
            emoji = STRUCTURE_ANDREW['par_theme']['categories'][theme]['emoji']
            f.write(f"- {emoji} **{theme.replace('_', ' ').title()}** : {count} videos\n")

    # Summary
    print()
    print("=" * 60)
    print("ORGANIZATION SUMMARY")
    print("=" * 60)
    print()
    print("📚 BY AGE:")
    for age, count in sorted(stats['age'].items()):
        print(f"  {age:30s}: {count:4d} videos")

    print("\n📕 BY SUBJECT:")
    for mat, count in sorted(stats['matiere'].items()):
        print(f"  {mat:30s}: {count:4d} videos")

    print("\n🎨 BY TOPIC:")
    for theme, count in sorted(stats['theme'].items()):
        print(f"  {theme:30s}: {count:4d} videos")

    print()
    print("=" * 60)
    print(f"📁 Folder: {ORGANIZED_DIR}")
    print(f"📋 Catalogue: {catalogue_file}")
    print(f"📖 Index: {readme}")
    print("=" * 60)

if __name__ == "__main__":
    organiser_encyclopedie()
