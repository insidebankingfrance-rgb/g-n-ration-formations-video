"""Concatène des clips scene_*.mp4 en une vidéo finale unique via ffmpeg.

Suppose que tous les clips ont le même format (1920x1080, 25 fps, AAC).
"""

import argparse
import subprocess
from pathlib import Path


def concat(scene_paths, final_path):
    filelist = final_path.parent / "concat_list.txt"
    filelist.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in scene_paths), encoding="utf-8"
    )
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(filelist),
            "-c", "copy",
            str(final_path),
        ],
        check=True,
        capture_output=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clips-dir", default="data/scene_clips")
    parser.add_argument("-o", "--output", default="output/formation.mp4")
    args = parser.parse_args()

    scenes = sorted(Path(args.clips_dir).glob("scene_*.mp4"))
    if not scenes:
        raise SystemExit(f"Aucun clip trouvé dans {args.clips_dir}")

    final_path = Path(args.output)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Concaténation de {len(scenes)} scènes -> {final_path}", flush=True)
    concat(scenes, final_path)
    print(f"Vidéo finale : {final_path}", flush=True)


if __name__ == "__main__":
    main()
