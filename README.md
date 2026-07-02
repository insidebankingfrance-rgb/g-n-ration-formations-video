# Générateur de vidéos de formation (avatar IA)

Pipeline qui transforme un support de formation (PowerPoint) en vidéo avec un
présentateur virtuel (avatar IA) qui commente les slides, incrusté en petit
format sur les visuels du support.

## Comment ça marche

```
support.pptx
   │
   ├─► extract_content.py     → data/slides.json        (texte de chaque slide)
   ├─► render_slide_images.py → data/slide_images/*.png (fond visuel de chaque scène)
   │
   ▼
Claude écrit le script de narration à partir de data/slides.json
   │
   ▼
data/narration.json  (texte que l'avatar va dire, scène par scène)
   │
   ├─► generate_avatar_clip.py → data/avatar_clips/*.mp4  (API D-ID : voix + lip-sync)
   ├─► compose_video.py        → output/formation.mp4     (incrustation + assemblage final)
```

La rédaction du script pédagogique (transformer des puces de slide en texte
parlé, naturel et pédagogique) est faite par Claude directement — pas besoin
de clé API ni de coût supplémentaire pour cette étape, c'est inclus dans ton
abonnement Claude.

Seule la génération de l'avatar parlant (voix + animation du visage) passe
par un service tiers, car ça nécessite un moteur de rendu vidéo dédié.

## Choix technique : D-ID

Aucune solution d'avatar IA n'est gratuite et illimitée. On utilise **D-ID**
pour le premier test car :
- Inscription gratuite avec des crédits d'essai utilisables directement via API
- Pas besoin d'installer quoi que ce soit en local (le rendu se fait sur leurs serveurs)
- Gère en un seul appel la voix (texte-à-parole) ET l'animation labiale de l'avatar

**Limites du palier gratuit** : nombre de crédits limité (quelques minutes de
vidéo au total), possible filigrane selon l'offre en cours. Suffisant pour
valider le pipeline sur un premier support ; si le résultat te convient et
que tu veux passer à l'échelle (plus de vidéos, sans filigrane), il faudra un
plan payant chez D-ID (ou Synthesia/HeyGen — le code est fait pour qu'on
puisse changer de fournisseur assez facilement).

## Installation

```bash
pip install -r requirements.txt
```

Dépendances système nécessaires (déjà installées dans cet environnement) :
`ffmpeg`, `libreoffice` (conversion pptx → pdf), `poppler-utils` (pdf → images).

## Configuration

```bash
cp .env.example .env
```

1. Crée un compte gratuit sur https://www.d-id.com, récupère ta clé API
   (Account Settings > API Keys) et mets-la dans `D_ID_API_KEY`.
2. Ajoute une photo du présentateur virtuel dans `assets/avatar/` (voir
   `assets/avatar/README.md` pour les critères), et renseigne son chemin
   dans `AVATAR_IMAGE_PATH`.

## Utilisation

```bash
# 1. Extraction du contenu + génération des images de fond
python src/pipeline.py prepare mon_support.pptx

# 2. Demander à Claude d'écrire data/narration.json à partir de data/slides.json
#    (se fait dans la conversation, pas une commande à lancer)

# 3. Génération des clips avatar + assemblage de la vidéo finale
python src/pipeline.py generate
```

La vidéo finale est produite dans `output/formation.mp4`.

### Format de `data/narration.json`

Une entrée par slide, dans l'ordre, avec le texte que l'avatar doit dire :

```json
[
  { "index": 0, "text": "Bonjour et bienvenue dans cette formation sur..." },
  { "index": 1, "text": "Voyons maintenant le premier point clé..." }
]
```

## Limitations connues

- Le palier gratuit D-ID est limité en durée totale de vidéo générée ; au-delà,
  il faudra passer sur un plan payant ou changer de fournisseur.
- La mise en page (avatar en incrustation bas-droite sur les slides) est fixe
  pour l'instant ; on pourra la rendre configurable si besoin (plein écran,
  taille/position de l'avatar, habillage/branding...).
- Pas de sous-titres générés automatiquement pour l'instant.

## Prochaine étape

Envoie ton premier support de formation (.pptx) pour lancer un premier test
de bout en bout.
