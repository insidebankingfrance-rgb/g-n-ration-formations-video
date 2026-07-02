"""Génère un clip MP4 par scène : slide en plein écran + narration vocale.

Utilise Piper (moteur TTS local, ONNX). Aucune API externe à l'exécution,
donc pas de risque de rate-limit ou de coupure de service.

Le modèle vocal (~60 MB) est attendu dans data/piper/<voice>.onnx et
data/piper/<voice>.onnx.json. Le workflow GitHub Actions le télécharge
depuis HuggingFace en amont ; en local voir README.

Entrée : data/narration.json + data/slide_images/slide-XX.png
Sortie : data/scene_clips/scene_XX.mp4 (slide 1920x1080 + piste audio)
"""

import argparse
import json
import os
import subprocess
from pathlib import Path


DEFAULT_MODEL_DIR = "data/piper"
DEFAULT_VOICE = "fr_FR-siwis-medium"


def synthesize(text, model_path, wav_path):
    """Appelle le binaire piper via stdin -> WAV."""
    subprocess.run(
        ["piper", "--model", str(model_path), "--output-file", str(wav_path)],
        input=text.encode("utf-8"),
        check=True,
        capture_output=True,
    )


def render_scene(slide_image, wav_path, out_mp4):
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(slide_image),
            "-i", str(wav_path),
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--narration", default="data/narration.json")
    parser.add_argument("--slides-dir", default="data/slide_images")
    parser.add_argument("--audio-dir", default="data/audio_clips")
    parser.add_argument("--clips-dir", default="data/scene_clips")
    parser.add_argument("--model-dir", default=os.environ.get("PIPER_MODEL_DIR", DEFAULT_MODEL_DIR))
    parser.add_argument("--voice", default=os.environ.get("PIPER_VOICE", DEFAULT_VOICE))
    args = parser.parse_args()

    model_path = Path(args.model_dir) / f"{args.voice}.onnx"
    if not model_path.exists():
        raise SystemExit(
            f"Modèle piper introuvable : {model_path}\n"
            f"Télécharge-le depuis HuggingFace, ex :\n"
            f"  curl -sSL -o {model_path} \\\n"
            f"    'https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/{args.voice}.onnx'\n"
            f"  curl -sSL -o {model_path}.json \\\n"
            f"    'https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/{args.voice}.onnx.json'\n"
        )

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

        wav = audio_dir / f"scene_{idx:02d}.wav"
        mp4 = clips_dir / f"scene_{idx:02d}.mp4"

        if mp4.exists():
            print(f"[{idx}] déjà généré ({mp4.name}), on saute", flush=True)
            continue

        print(f"[{idx}] TTS piper ({len(scene['text'])} caractères) -> {wav.name}", flush=True)
        synthesize(scene["text"], model_path, wav)

        print(f"[{idx}] rendu vidéo (slide + audio) -> {mp4.name}", flush=True)
        render_scene(slide, wav, mp4)

    print(f"Terminé : {len(scenes)} scènes prêtes dans {clips_dir}", flush=True)


if __name__ == "__main__":
    main()
