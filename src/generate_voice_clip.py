"""Génère un clip MP4 par scène : slide en plein écran + narration vocale.

Utilise Edge-TTS (Microsoft, gratuit, illimité) pour la synthèse vocale.
Aucune API key nécessaire, aucun quota. Voix française par défaut.

Entrée : data/narration.json + data/slide_images/slide-XX.png
Sortie : data/scene_clips/scene_XX.mp4 (slide 1920x1080 + piste audio)
"""

import argparse
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts


DEFAULT_VOICE = "fr-FR-HenriNeural"


async def synthesize(text, voice, mp3_path):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(mp3_path))


def render_scene(slide_image, mp3_path, out_mp4):
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(slide_image),
            "-i", str(mp3_path),
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
                   "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-r", "25",
            str(out_mp4),
        ],
        check=True,
        capture_output=True,
    )


async def main_async(args):
    scenes = json.loads(Path(args.narration).read_text(encoding="utf-8"))
    audio_dir = Path(args.audio_dir)
    clips_dir = Path(args.clips_dir)
    slides_dir = Path(args.slides_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)

    for scene in scenes:
        idx = scene["index"]
        slide = slides_dir / f"slide-{idx:02d}.png"
        if not slide.exists():
            raise FileNotFoundError(f"Slide manquante : {slide}")

        mp3 = audio_dir / f"scene_{idx:02d}.mp3"
        mp4 = clips_dir / f"scene_{idx:02d}.mp4"

        if mp4.exists():
            print(f"[{idx}] déjà généré ({mp4.name}), on saute", flush=True)
            continue

        print(f"[{idx}] TTS ({len(scene['text'])} caractères) -> {mp3.name}", flush=True)
        await synthesize(scene["text"], args.voice, mp3)

        print(f"[{idx}] rendu vidéo (slide + audio) -> {mp4.name}", flush=True)
        render_scene(slide, mp3, mp4)

    print(f"Terminé : {len(scenes)} scènes prêtes dans {clips_dir}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--narration", default="data/narration.json")
    parser.add_argument("--slides-dir", default="data/slide_images")
    parser.add_argument("--audio-dir", default="data/audio_clips")
    parser.add_argument("--clips-dir", default="data/scene_clips")
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=(
            "ID de voix Edge-TTS. Voix FR disponibles : "
            "fr-FR-HenriNeural (H, chaleureux), fr-FR-DeniseNeural (F), "
            "fr-FR-VivienneMultilingualNeural (F, très naturelle), "
            "fr-FR-RemyMultilingualNeural (H, très naturel)."
        ),
    )
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
