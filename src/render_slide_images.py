"""Convertit chaque slide du support source (.pptx ou .pdf) en image PNG.

Pour un .pptx : passe par LibreOffice (pptx -> pdf) avant l'export.
Pour un .pdf  : convertit directement page par page via `pdftoppm`.

L'option --pages permet de ne garder que certaines pages (1-indexées),
équivalente à celle de extract_content.py.
"""

import argparse
import re
import subprocess
from pathlib import Path


def _page_number(path):
    return int(re.search(r"-(\d+)\.png$", path.name).group(1))


def parse_pages_spec(spec):
    if not spec:
        return None
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(part))
    return sorted(pages)


def convert_pptx_to_pdf(pptx_path, workdir):
    workdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(workdir), str(pptx_path)],
        check=True, capture_output=True,
    )
    pdf_path = workdir / (Path(pptx_path).stem + ".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"Échec de conversion LibreOffice : {pdf_path} introuvable")
    return pdf_path


def convert_pdf_to_pngs(pdf_path, out_dir, filter_pages=None, width=1920):
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "raw"
    subprocess.run(
        ["pdftoppm", "-png", "-scale-to-x", str(width), "-scale-to-y", "-1", str(pdf_path), str(prefix)],
        check=True, capture_output=True,
    )

    pages = sorted(out_dir.glob("raw-*.png"), key=_page_number)
    if filter_pages is not None:
        wanted = set(filter_pages)
        pages = [p for p in pages if _page_number(p) in wanted]

    for page in out_dir.glob("slide-*.png"):
        page.unlink()

    renamed = []
    for new_index, page_path in enumerate(pages):
        new_path = out_dir / f"slide-{new_index:02d}.png"
        page_path.rename(new_path)
        renamed.append(new_path)

    for leftover in out_dir.glob("raw-*.png"):
        leftover.unlink()

    return renamed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="Chemin vers le fichier .pptx ou .pdf")
    parser.add_argument("-o", "--output-dir", default="data/slide_images", help="Dossier de sortie des images")
    parser.add_argument("--pages", help="Filtre 1-indexé, ex '1,2,9-11' (par défaut : tout le support)")
    args = parser.parse_args()

    src = Path(args.source)
    out_dir = Path(args.output_dir)
    filter_pages = parse_pages_spec(args.pages)

    if src.suffix.lower() == ".pptx":
        pdf_path = convert_pptx_to_pdf(src, out_dir)
    elif src.suffix.lower() == ".pdf":
        pdf_path = src
    else:
        raise SystemExit(f"Format non pris en charge : {src.suffix}. Attendu : .pptx ou .pdf")

    images = convert_pdf_to_pngs(pdf_path, out_dir, filter_pages=filter_pages)
    print(f"{len(images)} images de slides générées dans {out_dir}")


if __name__ == "__main__":
    main()
