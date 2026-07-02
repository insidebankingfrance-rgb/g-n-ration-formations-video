"""Génère un clip vidéo d'avatar parlant (voix + lip-sync) par scène, via l'API D-ID.

Prérequis : un compte D-ID (palier gratuit / crédits d'essai) et une clé API
dans la variable d'environnement D_ID_API_KEY (voir .env.example).

Entrée : data/narration.json -> [{"index": 0, "text": "..."}, ...]
Sortie : data/avatar_clips/scene_XX.mp4

NB : le format exact des en-têtes d'authentification et des endpoints peut
évoluer côté D-ID. À ajuster si l'API renvoie une erreur 401/404 lors du
premier vrai test (voir docs.d-id.com).
"""

import argparse
import base64
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.d-id.com"
POLL_INTERVAL_SECONDS = 4
POLL_TIMEOUT_SECONDS = 300


def _auth_header():
    api_key = os.environ.get("D_ID_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("D_ID_API_KEY manquante : configure ton .env (voir .env.example)")
    # La clé copiée depuis le dashboard D-ID s'utilise généralement telle quelle.
    # Si D-ID te fournit une clé "email:secret", on l'encode nous-même en base64.
    if ":" in api_key and not api_key.count(" "):
        api_key = base64.b64encode(api_key.encode()).decode()
    return {"Authorization": f"Basic {api_key}"}


def upload_avatar_image(image_path):
    with open(image_path, "rb") as f:
        response = requests.post(
            f"{API_BASE}/images",
            headers=_auth_header(),
            files={"image": f},
            timeout=60,
        )
    response.raise_for_status()
    return response.json()["url"]


def create_talk(text, source_url, voice_id):
    payload = {
        "source_url": source_url,
        "script": {
            "type": "text",
            "input": text,
            "provider": {"type": "microsoft", "voice_id": voice_id},
        },
        "config": {"fluent": True, "pad_audio": 0.3},
    }
    response = requests.post(
        f"{API_BASE}/talks",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["id"]


def wait_for_talk(talk_id):
    deadline = time.time() + POLL_TIMEOUT_SECONDS
    while time.time() < deadline:
        response = requests.get(
            f"{API_BASE}/talks/{talk_id}", headers=_auth_header(), timeout=30
        )
        response.raise_for_status()
        data = response.json()
        status = data.get("status")
        if status == "done":
            return data["result_url"]
        if status == "error":
            raise RuntimeError(f"D-ID a échoué sur le talk {talk_id} : {data}")
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(f"Le talk {talk_id} n'a pas abouti dans le temps imparti")


def download(url, dest_path):
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    dest_path.write_bytes(response.content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n", "--narration", default="data/narration.json", help="Fichier JSON de narration"
    )
    parser.add_argument(
        "-o", "--output-dir", default="data/avatar_clips", help="Dossier de sortie des clips"
    )
    parser.add_argument(
        "--avatar-image", default=os.environ.get("AVATAR_IMAGE_PATH", "assets/avatar/presentateur.jpg")
    )
    parser.add_argument("--voice-id", default=os.environ.get("D_ID_VOICE_ID", "fr-FR-DeniseNeural"))
    args = parser.parse_args()

    scenes = json.loads(Path(args.narration).read_text(encoding="utf-8"))
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Upload de l'avatar {args.avatar_image}...")
    source_url = upload_avatar_image(args.avatar_image)

    for scene in scenes:
        dest = out_dir / f"scene_{scene['index']:02d}.mp4"
        if dest.exists():
            print(f"[{scene['index']}] déjà généré, on saute")
            continue
        print(f"[{scene['index']}] génération du clip avatar ({len(scene['text'])} caractères)...")
        talk_id = create_talk(scene["text"], source_url, args.voice_id)
        result_url = wait_for_talk(talk_id)
        download(result_url, dest)
        print(f"[{scene['index']}] -> {dest}")

    print("Terminé.")


if __name__ == "__main__":
    main()
