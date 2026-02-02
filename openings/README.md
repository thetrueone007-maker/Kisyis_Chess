# 📚 Fichiers de Définition d'Ouvertures

Ce dossier contient les définitions JSON des ouvertures d'échecs pour le mode opening.

## 📐 Format JSON Requis

Chaque ouverture doit être un fichier JSON avec la structure suivante :

```json
{
  "title": "Nom de l'Ouverture - Variation",
  "description": "Description courte de l'ouverture et de ses objectifs",
  "eco_code": "Code ECO (ex: B20, C50, E60)",
  "side": "white" ou "black",
  "moves": [
    "e4",
    "e5",
    "Nf3",
    "..."
  ],
  "hashtags": [
    "#Hashtag1",
    "#Hashtag2"
  ],
  "key_ideas": [
    "Idée clé 1",
    "Idée clé 2",
    "Idée clé 3"
  ]
}
```

### Champs obligatoires :

- **title** : Titre complet de l'ouverture (affiché dans la vidéo)
- **description** : Description de l'ouverture (1-2 phrases)
- **side** : `"white"` ou `"black"`
  - ⚠️ **Important** : Si `"black"`, l'échiquier sera inversé (perspective des noirs)
- **moves** : Liste des coups en notation algébrique (ex: "e4", "Nf3", "O-O")
- **hashtags** : Liste de hashtags pour TikTok (5-10 recommandés)
- **key_ideas** : Points clés de l'ouverture (3-5 idées)

### Champs optionnels :

- **eco_code** : Code ECO si tu le connais (ex: "B20", "C50") - Pas obligatoire !

### Format des coups :

Utilise la **notation algébrique standard** (SAN) :
- Pions : `e4`, `d5`, `c6`
- Pièces : `Nf3`, `Bc4`, `Qd2`
- Captures : `exd5`, `Nxe4`
- Roque : `O-O` (petit roque), `O-O-O` (grand roque)
- Échec : `Qh5+`
- Promotion : `e8=Q`

## 🎯 Exemples

### Exemple 1 : Ouverture pour les BLANCS
**Fichier** : `italian_game.json`
- Échiquier : Vue normale (blancs en bas)
- Coups : Commence par le premier coup des blancs

### Exemple 2 : Ouverture pour les NOIRS
**Fichier** : `sicilian_defense.json`
- Échiquier : **Inversé** (noirs en bas)
- Coups : Commence par le premier coup des blancs, mais perspective des noirs

---

## 🤖 Prompt pour ChatGPT

Copie-colle ce prompt à ChatGPT pour qu'il génère des fichiers d'ouvertures :

```
Tu es un expert en échecs. Je veux que tu génères des fichiers JSON de définition d'ouvertures d'échecs pour une application éducative TikTok.

FORMAT JSON REQUIS :
{
  "title": "Nom de l'Ouverture - Variation",
  "description": "Description de l'ouverture en 1-2 phrases (objectifs, style de jeu)",
  "side": "white" OU "black" (selon qui joue cette ouverture),
  "moves": [
    "Liste des coups en notation algébrique (SAN)",
    "Exemple: e4, Nf3, Bc4, O-O, etc.",
    "10 à 20 coups de la ligne principale"
  ],
  "hashtags": [
    "5 à 8 hashtags TikTok pertinents",
    "Mélange anglais/français",
    "Exemple: #ChessOpening, #EchecsTheorie"
  ],
  "key_ideas": [
    "3 à 5 idées clés de l'ouverture",
    "Concepts stratégiques importants",
    "Ce que le joueur doit comprendre"
  ]
}

NOTE : Le champ "eco_code" est OPTIONNEL. Ne l'ajoute que si tu le connais.

RÈGLES IMPORTANTES :
1. "side": "white" si c'est une ouverture jouée par les blancs
2. "side": "black" si c'est une ouverture/défense jouée par les noirs
3. Les coups doivent être en notation algébrique standard (SAN)
4. Inclure 10 à 20 coups de la ligne principale
5. Description courte et pédagogique (pour débutants/intermédiaires)
6. Hashtags mixtes français/anglais pour TikTok

EXEMPLES D'OUVERTURES À GÉNÉRER :

Pour les BLANCS :
- Italian Game (Giuoco Piano)
- Ruy Lopez (Spanish Opening)
- Queen's Gambit
- English Opening
- Scotch Game
- King's Indian Attack

Pour les NOIRS :
- Sicilian Defense (Dragon, Najdorf)
- French Defense
- Caro-Kann Defense
- Scandinavian Defense
- Pirc Defense
- King's Indian Defense

GÉNÈRE UN FICHIER JSON POUR CHAQUE OUVERTURE.
Nomme les fichiers en snake_case : italian_game.json, french_defense.json, etc.
```

---

## 📥 Utilisation

### 1. Génération avec ChatGPT
Demande à ChatGPT de générer les fichiers JSON pour les ouvertures que tu veux.

### 2. Sauvegarde
Place les fichiers `.json` dans ce dossier `openings/`

### 3. Génération de vidéo

```bash
# Utiliser un fichier d'ouverture
python main_pipeline.py --opening-mode italian_game.json

# Plusieurs vidéos de la même ouverture
python main_pipeline.py --count 3 --opening-mode sicilian_defense.json
```

### 4. Vérification

Le système va :
- ✅ Lire le fichier JSON
- ✅ Créer une partie avec les coups définis
- ✅ Inverser l'échiquier si `"side": "black"`
- ✅ Désactiver les annotations (BRILLIANT, BLUNDER, etc.)
- ✅ Utiliser les assets personnalisés de `assets_opening/`
- ✅ Sauvegarder dans `tiktok_opening/`

---

## 📂 Structure des fichiers

```
openings/
├── README.md                    ← Ce fichier
├── italian_game.json            ← Exemple pour les blancs
├── sicilian_defense.json        ← Exemple pour les noirs
├── french_defense.json
├── ruy_lopez.json
└── ... autres ouvertures
```

---

## ✅ Checklist de validation

Avant d'utiliser un fichier JSON, vérifie :

- [ ] Tous les champs obligatoires sont présents
- [ ] `side` est soit `"white"` soit `"black"`
- [ ] Les coups sont en notation algébrique valide
- [ ] Il y a entre 10 et 20 coups
- [ ] Le code ECO est correct
- [ ] Les hashtags commencent par `#`
- [ ] Il y a 3-5 idées clés

---

## 🎨 Personnalisation

- **Assets** : Place tes PNG personnalisés dans `assets_opening/`
- **Hashtags** : Adapte selon ta stratégie TikTok
- **Longueur** : Ajuste le nombre de coups (10-20 recommandé)
- **Description** : Garde-la concise pour l'affichage vidéo
