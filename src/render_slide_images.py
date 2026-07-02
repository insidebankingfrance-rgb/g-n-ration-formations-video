"""Convertit chaque slide d'un .pptx en image PNG (fond visuel de la vidéo),
via LibreOffice (pptx -> pdf) puis Poppler (pdf -> png), une page par slide.
"""

import argparse
import re
import subprocess
from pathlib import Path


def _page_number(path):
    return int(re.search(r"-(\d+)\.png$", path.name).group(1))


def convert_pptx_to_pdf(pptx_path, workdir):
    subprocess.run(
        [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(workdir),
            str(pptx_path),
        ],
        check=True,
        capture_output=True,
    )
    pdf_path = workdir / (Path(pptx_path).stem + ".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"Échec de conversion LibreOffice : {pdf_path} introuvable")
    return pdf_path


def convert_pdf_to_pngs(pdf_path, out_dir, width=1920):
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "slide"
    subprocess.run(
        ["pdftoppm", "-png", "-scale-to-x", str(width), "-scale-to-y", "-1", str(pdf_path), str(prefix)],
        check=True,
        capture_output=True,
    )

    # pdftoppm ne remplit pas systématiquement les numéros de zéros (slide-1.png,
    # slide-2.png, ..., slide-10.png), ce qui casse le tri alphabétique au-delà
    # de 9 slides. On renomme en 0-indexé et zero-paddé pour matcher les index
    # de data/slides.json et data/avatar_clips/scene_XX.mp4.
    pages = sorted(out_dir.glob("slide-*.png"), key=_page_number)
    renamed = []
    for page_index, page_path in enumerate(pages):
        new_path = out_dir / f"slide-{page_index:02d}.png"
        page_path.rename(new_path)
        renamed.append(new_path)
    return renamed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", help="Chemin vers le fichier .pptx source")
    parser.add_argument(
        "-o", "--output-dir", default="data/slide_images", help="Dossier de sortie des images"
    )
    args = parser.parse_args()

    pptx_path = Path(args.pptx)
    out_dir = Path(args.output_dir)

    pdf_path = convert_pptx_to_pdf(pptx_path, out_dir)
    images = convert_pdf_to_pngs(pdf_path, out_dir)

    print(f"{len(images)} images de slides générées dans {out_dir}")


if __name__ == "__main__":
    main()
