"""Orchestrateur du pipeline de génération de vidéo de formation.

Étapes :
  1. extract   : .pptx -> data/slides.json (texte de chaque slide)
  2. images    : .pptx -> data/slide_images/slide-XX.png (fond visuel)
  3. narration : (manuel/IA) data/slides.json -> data/narration.json
                 -> écrit par Claude à partir du contenu extrait, PAS un script automatique
  4. avatars   : data/narration.json -> data/avatar_clips/scene_XX.mp4 (API D-ID)
  5. compose   : slides + clips avatar -> output/formation.mp4

Usage typique :
    python src/pipeline.py prepare support.pptx
    # -> Claude lit data/slides.json et écrit data/narration.json
    python src/pipeline.py generate
"""

import argparse
import subprocess
import sys
from pathlib import Path

SRC_DIR = Path(__file__).parent


def run(cmd):
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def prepare(pptx_path):
    run([sys.executable, str(SRC_DIR / "extract_content.py"), pptx_path])
    run([sys.executable, str(SRC_DIR / "render_slide_images.py"), pptx_path])
    print(
        "\nÉtape suivante (manuelle) : demande à Claude d'écrire data/narration.json "
        "à partir de data/slides.json, puis lance `python src/pipeline.py generate`."
    )


def generate():
    narration_path = Path("data/narration.json")
    if not narration_path.exists():
        raise SystemExit(
            "data/narration.json introuvable. Écris d'abord le script de narration "
            "(voir README) avant de lancer cette étape."
        )
    run([sys.executable, str(SRC_DIR / "generate_avatar_clip.py")])
    run([sys.executable, str(SRC_DIR / "compose_video.py")])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_prepare = subparsers.add_parser("prepare", help="Extrait le contenu et les images du support")
    p_prepare.add_argument("pptx", help="Chemin vers le fichier .pptx source")

    subparsers.add_parser("generate", help="Génère les clips avatar puis la vidéo finale")

    args = parser.parse_args()

    if args.command == "prepare":
        prepare(args.pptx)
    elif args.command == "generate":
        generate()


if __name__ == "__main__":
    main()
