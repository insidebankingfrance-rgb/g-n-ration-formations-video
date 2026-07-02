"""Assemble la vidéo finale : incruste chaque clip avatar (voix + lip-sync)
en petit format (coin bas-droit) sur l'image de la slide correspondante,
puis concatène toutes les scènes en une vidéo MP4 unique.
"""

import argparse
import subprocess
from pathlib import Path


def compose_scene(slide_image, avatar_clip, out_path, pip_width=480):
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(slide_image),
            "-i", str(avatar_clip),
            "-filter_complex",
            f"[1:v]scale={pip_width}:-1[pip];"
            f"[0:v][pip]overlay=W-w-40:H-h-40:shortest=1,scale=1920:1080[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
            "-shortest",
            str(out_path),
        ],
        check=True,
        capture_output=True,
    )


def concat_scenes(scene_paths, final_path):
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
    parser.add_argument("--slide-images-dir", default="data/slide_images")
    parser.add_argument("--avatar-clips-dir", default="data/avatar_clips")
    parser.add_argument("--scenes-dir", default="data/scenes")
    parser.add_argument("-o", "--output", default="output/formation.mp4")
    args = parser.parse_args()

    slide_images = sorted(Path(args.slide_images_dir).glob("slide-*.png"))
    avatar_clips = sorted(Path(args.avatar_clips_dir).glob("scene_*.mp4"))

    if len(slide_images) != len(avatar_clips):
        raise RuntimeError(
            f"{len(slide_images)} images de slides vs {len(avatar_clips)} clips avatar : "
            "vérifie que les deux étapes précédentes ont bien tourné sur le même support."
        )

    scenes_dir = Path(args.scenes_dir)
    scenes_dir.mkdir(parents=True, exist_ok=True)

    scene_outputs = []
    for slide_image, avatar_clip in zip(slide_images, avatar_clips):
        out_path = scenes_dir / f"{avatar_clip.stem}.mp4"
        print(f"Composition {out_path.name} ({slide_image.name} + {avatar_clip.name})...")
        compose_scene(slide_image, avatar_clip, out_path)
        scene_outputs.append(out_path)

    final_path = Path(args.output)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Concaténation de {len(scene_outputs)} scènes -> {final_path}")
    concat_scenes(scene_outputs, final_path)

    print(f"Vidéo finale : {final_path}")


if __name__ == "__main__":
    main()
