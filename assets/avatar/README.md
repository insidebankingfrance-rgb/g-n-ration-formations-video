# Photo du présentateur virtuel

Deux fichiers cohabitent ici :

- `presentateur.jpg` : la photo maître (haute résolution, telle que déposée par l'utilisateur).
- `presentateur_optimized.jpg` : version redimensionnée servie à D-ID (**c'est celle-ci que le pipeline utilise**).

## Pourquoi une version optimisée ?

D-ID applique une limite de **10 MB sur l'image décodée en mémoire** (pas sur le fichier
compressé). Un JPG de 2 MB peut donc décoder à 70+ MB si la résolution est très haute,
et D-ID renvoie alors `InvalidFileSizeError`. On sert donc une version bornée à ~1080 px
sur le plus grand côté, ce qui reste largement suffisant pour un talking-head.

## Régénérer la version optimisée

Après avoir remplacé `presentateur.jpg` par une nouvelle photo :

```bash
python -c "
from PIL import Image, ImageOps
im = ImageOps.exif_transpose(Image.open('assets/avatar/presentateur.jpg'))
im.thumbnail((1080, 1080), Image.Resampling.LANCZOS)
im.save('assets/avatar/presentateur_optimized.jpg', 'JPEG', quality=88, optimize=True)
"
```

Puis commit + push : le workflow prendra automatiquement la nouvelle version.

## Recommandations D-ID pour la photo maître

- Visage de face, bien centré, yeux ouverts, bouche fermée au repos
- Bon éclairage, fond neutre
- Une seule personne visible sur la photo
- Format JPG ou PNG
