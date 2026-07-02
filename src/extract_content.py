"""Extrait le texte du support source (.pptx ou .pdf) vers data/slides.json.

Pour un .pptx : lit chaque slide via python-pptx (titre / puces / notes).
Pour un .pdf  : extrait le texte de chaque page via `pdftotext -layout`.

L'option --pages permet de ne garder que certaines pages (1-indexées),
utile pour lancer un PoC sur un sous-ensemble du support :
    --pages 1,2,9,10,11
    --pages 9-14
"""

import argparse
import json
import subprocess
from pathlib import Path


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


def extract_pptx(pptx_path):
    from pptx import Presentation

    prs = Presentation(pptx_path)
    slides = []
    for i, slide in enumerate(prs.slides):
        title = None
        bullets = []
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            text = shape.text_frame.text.strip()
            if not text:
                continue
            if shape == slide.shapes.title and title is None:
                title = text
            else:
                bullets.extend([line.strip() for line in text.split("\n") if line.strip()])
        notes = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
        slides.append({"index": i, "page": i + 1, "title": title or f"Slide {i + 1}", "bullets": bullets, "notes": notes})
    return slides


def extract_pdf(pdf_path):
    result = subprocess.run(
        ["pdfinfo", str(pdf_path)], capture_output=True, text=True, check=True
    )
    page_count = int(next(line for line in result.stdout.splitlines() if line.startswith("Pages:")).split()[1])

    slides = []
    for page_num in range(1, page_count + 1):
        text = subprocess.run(
            ["pdftotext", "-layout", "-f", str(page_num), "-l", str(page_num), str(pdf_path), "-"],
            capture_output=True, text=True, check=True,
        ).stdout
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        # Retire les pieds de page de confidentialité présents sur chaque slide.
        lines = [
            line for line in lines
            if "strictement confidentielles" not in line and not line.isdigit()
        ]
        title = lines[0] if lines else f"Slide {page_num}"
        bullets = lines[1:] if len(lines) > 1 else []
        slides.append({
            "index": page_num - 1,
            "page": page_num,
            "title": title,
            "bullets": bullets,
            "notes": "",
        })
    return slides


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="Chemin vers le fichier .pptx ou .pdf")
    parser.add_argument("-o", "--output", default="data/slides.json", help="Fichier JSON de sortie")
    parser.add_argument("--pages", help="Filtre 1-indexé, ex '1,2,9-11' (par défaut : tout le support)")
    args = parser.parse_args()

    src = Path(args.source)
    if src.suffix.lower() == ".pptx":
        slides = extract_pptx(src)
    elif src.suffix.lower() == ".pdf":
        slides = extract_pdf(src)
    else:
        raise SystemExit(f"Format non pris en charge : {src.suffix}. Attendu : .pptx ou .pdf")

    filter_pages = parse_pages_spec(args.pages)
    if filter_pages is not None:
        wanted = set(filter_pages)
        slides = [s for s in slides if s["page"] in wanted]
        for new_index, slide in enumerate(slides):
            slide["index"] = new_index

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(slides, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(slides)} slides extraites -> {out_path}")


if __name__ == "__main__":
    main()
