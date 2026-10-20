"French-language educational search presets."
import subprocess
from pathlib import Path

try:
    from .settings import DATA_DIR, get_pexels_key
except ImportError:
    from settings import DATA_DIR, get_pexels_key

DOWNLOAD_DIR = DATA_DIR / "downloaded"

# French search phrases for French-language content
THEMES_FRANCAIS = {
    'sciences': {
        'nom': 'Sciences',
        'mots_cles': [
            'expérience scientifique', 'réaction chimique', 'électricité',
            'magnétisme aimant', 'photosynthèse plante', 'digestion aliment',
            'respiration poumon', 'circulation sanguine', 'système solaire planète',
            'ADN génétique', 'cellule biologie', 'microscope observation',
            'physique newton', 'gravité force', 'atome molécule'
        ]
    },

    'histoire': {
        'nom': 'Histoire',
        'mots_cles': [
            'préhistoire homme de cro-magnon', 'égypte pharaon pyramide',
            'rome antique gladiateur', 'moyen âge chevalier château',
            'renaissance léonard de vinci', 'révolution française',
            'napoléon bonaparte empire', 'première guerre mondiale',
            'seconde guerre mondiale', 'roi soleil versailles',
            'charlemagne empire', 'jeanne d\'arc', 'clovis baptême',
            'jules césar conquête gaule', 'louis XIV versailles'
        ]
    },

    'geographie': {
        'nom': 'Géographie',
        'mots_cles': [
            'tour eiffel paris', 'mont saint-michel', 'château de versailles',
            'alpes mont blanc', 'pyrénées montagne', 'loire fleuve france',
            'méditerranée mer', 'océan atlantique', 'régions de france',
            'paris capitale monuments', 'massif central volcan', 'bretagne',
            'normandie débarquement', 'provence lavande', 'alsace strasbourg'
        ]
    },

    'animaux': {
        'nom': 'Animaux',
        'mots_cles': [
            'lion savane', 'éléphant trompe', 'dauphin intelligence',
            'baleine océan', 'requin dents', 'aigle royal vol',
            'papillon métamorphose', 'abeille ruche miel', 'fourmi colonie',
            'loup meute', 'ours brun', 'renard rusé', 'cerf bois',
            'sanglier forêt', 'hérisson piquants', 'chouette hibou'
        ]
    },

    'nature': {
        'nom': 'Nature',
        'mots_cles': [
            'volcan éruption lave', 'séisme tremblement de terre',
            'tsunami vague géante', 'tornade cyclone', 'orage éclair foudre',
            'arc-en-ciel couleurs', 'chute d\'eau cascade', 'glacier glace',
            'désert sahara', 'forêt amazonienne', 'récif corallien',
            'aurore boréale', 'geyser source chaude', 'canyon érosion'
        ]
    },

    'corps_humain': {
        'nom': 'Corps Humain',
        'mots_cles': [
            'œil vision rétine', 'oreille audition son', 'cerveau neurone',
            'cœur battement circulation', 'poumon respiration oxygène',
            'muscle contraction', 'squelette os', 'peau épiderme',
            'estomac digestion', 'sang globule', 'dent dentition',
            'système immunitaire défense', 'croissance développement'
        ]
    },

    'inventions': {
        'nom': 'Inventions',
        'mots_cles': [
            'imprimerie gutenberg', 'machine à vapeur watt',
            'train locomotive', 'automobile voiture moteur',
            'avion frères wright', 'téléphone bell', 'radio marconi',
            'télévision invention', 'ordinateur informatique',
            'internet web', 'électricité edison', 'roue invention',
            'microscope leeuwenhoek', 'télescope galilée'
        ]
    },

    'espace': {
        'nom': 'Espace',
        'mots_cles': [
            'système solaire', 'soleil étoile', 'lune satellite terre',
            'mars planète rouge', 'jupiter géante gazeuse', 'saturne anneaux',
            'comète queue', 'astéroïde', 'galaxie voie lactée',
            'trou noir', 'nébuleuse', 'constellation étoiles',
            'station spatiale internationale', 'fusée décollage',
            'astronaute cosmonaute', 'télescope hubble'
        ]
    },

    'art_culture': {
        'nom': 'Art et Culture',
        'mots_cles': [
            'musée du louvre', 'joconde mona lisa', 'tour eiffel construction',
            'notre-dame de paris', 'monet nymphéas', 'van gogh tournesols',
            'picasso cubisme', 'rodin penseur', 'arc de triomphe',
            'versailles galerie des glaces', 'impressionnisme peinture',
            'musique classique mozart', 'opéra garnier', 'cinéma frères lumière'
        ]
    },

    'vie_quotidienne': {
        'nom': 'Vie Quotidienne',
        'mots_cles': [
            'fabrication du pain boulangerie', 'fromage production laitière',
            'chocolat cacao', 'miel abeille apiculture', 'vin vigne raisin',
            'huile d\'olive pressage', 'café torréfaction', 'thé plantation',
            'recyclage tri déchets', 'eau potable traitement',
            'électricité centrale production', 'agriculture fermier tracteur'
        ]
    }
}

def telecharger_francais(categorie: str, config: dict, videos_par: int = 2):
    "Run the telecharger francais workflow."
    dossier = DOWNLOAD_DIR / f"fr_{categorie}"
    dossier.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"CATEGORY: {config['nom']}")
    print(f"{'=' * 60}\n")

    telecharges = 0

    for i, mot_cle in enumerate(config['mots_cles'], 1):
        print(f"[{i}/{len(config['mots_cles'])}] {mot_cle}")

        cmd = [
            'yt-dlp',
            f'ytsearch{videos_par}:{mot_cle} français',
            '--max-filesize', '25M',
            '--max-downloads', str(videos_par),
            '--match-filter', 'duration < 360',
            '-o', str(dossier / f'fr_{categorie}_{mot_cle.replace(" ", "_")[:35]}_%(id)s.%(ext)s'),
            '--format', 'best[height<=720]',
            '--no-playlist',
            '--quiet',
            '--no-warnings',
            '--ignore-errors'
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=90)
            fichiers = [f for f in dossier.glob(f'fr_{categorie}_*')
                       if mot_cle.split()[0] in f.name]
            nb = min(videos_par, len(fichiers))
            if nb > 0:
                print(f"  ✅ {nb} video(s)")
                telecharges += nb
            else:
                print(f"  ⏭️ None")
        except:
            print(f"  ❌ Error")

    print(f"\n{categorie}: {telecharges} videos")
    return telecharges

def main():
    print("=" * 60)
    print("FRENCH EDUCATIONAL VIDEO SEARCHES")
    print("=" * 60)
    print()
    print("French search terms for French-language content:")
    print()

    for cat, config in THEMES_FRANCAIS.items():
        print(f"  🇫🇷 {config['nom']}")
        print(f"     └─ {len(config['mots_cles'])} keywords")

    print()
    print(f"Total : {sum(len(c['mots_cles']) for c in THEMES_FRANCAIS.values())} searches")
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
    categories = list(THEMES_FRANCAIS.keys())
    print("Available categories :")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {THEMES_FRANCAIS[cat]['nom']}")
    print(f"  0. ALL")
    print()

    choix = input("Choose (0 for all) : ").strip()

    if choix == '0':
        selection = THEMES_FRANCAIS.items()
    elif choix.isdigit() and 1 <= int(choix) <= len(categories):
        cat = categories[int(choix) - 1]
        selection = [(cat, THEMES_FRANCAIS[cat])]
    else:
        print("Invalid choice")
        return

    videos_par = input("Videos per keyword (1-3, default 2) : ").strip() or "2"
    videos_par = int(videos_par)

    print("\n🚀 Download in French...")

    total = 0
    stats = {}

    for categorie, config in selection:
        nb = telecharger_francais(categorie, config, videos_par)
        stats[categorie] = nb
        total += nb

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for cat, nb in stats.items():
        print(f"{THEMES_FRANCAIS[cat]['nom']:25s}: {nb:3d} videos")
    print(f"\nTOTAL: {total} videos in French")
    print(f"Folder: {DOWNLOAD_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
