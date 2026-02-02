# Assets pour Mode Opening

Ce dossier contient les pièces d'échecs personnalisées pour le mode opening (théorie d'ouvertures).

## 📐 Format requis pour les PNG

### Spécifications techniques :
- **Résolution** : 512 x 512 pixels
- **Format** : PNG (RGBA)
- **Profondeur de couleur** : 8-bit/canal
- **Transparence** : Oui (canal alpha)
- **Fond** : Transparent
- **Taille fichier** : ~20-50 KB par pièce

### Noms de fichiers requis :

#### Pièces blanches :
- `wK.png` - Roi blanc (White King)
- `wQ.png` - Dame blanche (White Queen)
- `wR.png` - Tour blanche (White Rook)
- `wB.png` - Fou blanc (White Bishop)
- `wN.png` - Cavalier blanc (White Knight)
- `wP.png` - Pion blanc (White Pawn)

#### Pièces noires :
- `bK.png` - Roi noir (Black King)
- `bQ.png` - Dame noire (Black Queen)
- `bR.png` - Tour noire (Black Rook)
- `bB.png` - Fou noir (Black Bishop)
- `bN.png` - Cavalier noir (Black Knight)
- `bP.png` - Pion noir (Black Pawn)

## 🎨 Style recommandé pour le mode Opening

Pour le mode opening (apprentissage des ouvertures), un style **moderne et éducatif** est recommandé :

- Style **minimaliste** ou **flat design**
- Couleurs **vives et distinguables**
- Formes **claires et lisibles**
- Optionnel : Style **diagramme de livre** ou **style Lichess**

---

## 🤖 Prompt pour ChatGPT / DALL-E

Copie-colle ce prompt à ChatGPT pour générer les pièces :

```
Génère 12 icônes de pièces d'échecs modernes en style flat design pour une application éducative d'ouvertures d'échecs.

SPÉCIFICATIONS TECHNIQUES :
- Format : PNG avec fond transparent (RGBA)
- Résolution : 512 x 512 pixels
- Style : Flat design moderne, minimaliste, épuré
- Chaque pièce doit être centrée dans son carré

PIÈCES À CRÉER :

Pièces BLANCHES (couleur #FFFFFF ou blanc cassé) :
1. Roi blanc (wK.png) - couronne simple avec croix
2. Dame blanche (wQ.png) - couronne élégante avec pointes
3. Tour blanche (wR.png) - tour de château crénelée
4. Fou blanc (wB.png) - mitre d'évêque pointue
5. Cavalier blanc (wN.png) - tête de cheval stylisée
6. Pion blanc (wP.png) - forme simple ronde sur base

Pièces NOIRES (couleur #2C2C2C ou gris très foncé) :
7. Roi noir (bK.png) - identique au roi blanc mais couleur foncée
8. Dame noire (bQ.png) - identique à la dame blanche mais couleur foncée
9. Tour noire (bR.png) - identique à la tour blanche mais couleur foncée
10. Fou noir (bB.png) - identique au fou blanc mais couleur foncé
11. Cavalier noir (bN.png) - identique au cavalier blanc mais couleur foncée
12. Pion noir (bP.png) - identique au pion blanc mais couleur foncée

STYLE VISUEL :
- Design flat/2D (pas d'ombres portées complexes)
- Contours nets et lisibles
- Silhouettes reconnaissables instantanément
- Légère bordure ou outline pour meilleure visibilité (optionnel)
- Palette de couleurs : blanc pur pour les blancs, gris très foncé/noir pour les noirs

USAGE : Vidéos TikTok éducatives sur les ouvertures d'échecs
FORMAT DE SORTIE : 12 fichiers PNG séparés nommés exactement comme indiqué ci-dessus
```

---

## 📥 Installation

Après avoir généré les PNG avec ChatGPT :

1. Télécharge les 12 fichiers PNG
2. Renomme-les exactement selon la convention :
   - `wK.png`, `wQ.png`, `wR.png`, `wB.png`, `wN.png`, `wP.png`
   - `bK.png`, `bQ.png`, `bR.png`, `bB.png`, `bN.png`, `bP.png`
3. Place-les dans ce dossier `assets_opening/`

## ✅ Vérification

Pour vérifier que tout fonctionne :

```bash
python main_pipeline.py --count 1 --opening-mode "Sicilian" --no-audio
```

Si les assets existent, tu verras : `🎨 Using opening mode assets`

---

## 🎥 Résultat

Les vidéos générées en mode opening seront sauvegardées dans :
- **Dossier** : `./tiktok_opening/`
- **Comportement** : Pas d'annotations "BRILLIANT", "BLUNDER", etc.
- **Assets** : Utilise automatiquement les pièces de ce dossier
