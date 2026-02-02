# ♟️ Kisyis Chess - Générateur Automatique de Vidéos d'Échecs pour TikTok

Système complet et automatisé pour créer des vidéos d'échecs de qualité professionnelle optimisées pour TikTok.

## 🎯 Caractéristiques

### 🎬 Rendu Professionnel
- **Format vertical 9:16** optimisé pour TikTok (1080x1920)
- **60-120 FPS** pour une fluidité maximale
- **Animations fluides** des pièces avec effets de capture
- **Qualité 4K** avec encodage H.264 optimisé

### 📊 Analyse Intelligente
- **Intégration Stockfish** pour analyse en temps réel
- **Barre d'évaluation** animée comme sur Chess.com
- **Détection automatique** des coups brillants, blunders et moments critiques
- **Highlights visuels** avec flèches et surbrillance des cases

### 🤖 Commentaires IA
- **Génération automatique** de commentaires engageants via Claude AI
- **Style TikTok** optimisé pour maximiser l'engagement
- **Hashtags intelligents** basés sur les joueurs et le type de partie
- **Timing parfait** des commentaires sur les moments clés

### 🎵 Audio Professionnel
- **Musique de fond** avec fade in/out automatique
- **Support multi-format** (MP3, WAV, M4A)
- **Optimisation TikTok** (AAC, 192kbps, 48kHz)

### 📥 Sources de Parties Multiples
- **API Lichess** pour parties récentes des Grands Maîtres
- **Base de parties classiques** (Immortal Game, Opera Game, Kasparov, etc.)
- **Mix intelligent** 50/50 pour contenu varié

### ⏰ Automatisation Complète
- **Scheduler intégré** pour génération automatique
- **10+ vidéos par jour** en production
- **Queue de téléchargement** organisée
- **Logs détaillés** pour monitoring

## 🚀 Installation

### Prérequis Système

```bash
# Manjaro/Arch Linux
sudo pacman -S python python-pip ffmpeg stockfish

# Ubuntu/Debian
sudo apt install python3 python3-pip ffmpeg stockfish

# macOS
brew install python ffmpeg stockfish
```

### Installation Python

```bash
# Activer l'environnement virtuel
source venv_chess/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### Configuration API

```bash
# Pour les commentaires IA (optionnel mais recommandé)
export ANTHROPIC_API_KEY="votre_clé_api"

# Ajouter à ~/.bashrc ou ~/.zshrc pour persistance
echo 'export ANTHROPIC_API_KEY="votre_clé_api"' >> ~/.bashrc
```

Obtenir une clé API : https://console.anthropic.com/

### Configuration Audio

1. Télécharger de la musique libre de droits :
   - YouTube Audio Library : https://www.youtube.com/audiolibrary
   - Pixabay Music : https://pixabay.com/music/
   - Free Music Archive : https://freemusicarchive.org/

2. Placer les fichiers dans `./audio/music/`

```bash
mkdir -p audio/music
# Copier vos fichiers MP3 ici
```

## 💻 Utilisation

### Génération Simple

```bash
# Générer 1 vidéo
python main_pipeline.py --count 1

# Générer 5 vidéos
python main_pipeline.py --count 5

# 70% parties Lichess / 30% parties classiques
python main_pipeline.py --count 10 --mix-ratio 0.7
```

### Mode Automatique (Scheduler)

```bash
# 10 vidéos par jour (recommandé)
python scheduler.py --videos-per-day 10

# 20 vidéos par jour (production intensive)
python scheduler.py --videos-per-day 20

# Test : générer 1 batch immédiatement
python scheduler.py --once

# Daemon en arrière-plan
python scheduler.py --videos-per-day 10 --daemon
```

### Options Avancées

```bash
# Sans barre d'évaluation
python main_pipeline.py --count 5 --no-eval

# Sans musique
python main_pipeline.py --count 5 --no-audio

# Configuration personnalisée
python main_pipeline.py --config config.json --count 10
```

## 📁 Structure du Projet

```
Kisyis_Chess/
├── assets/                      # Images des pièces (PNG)
├── ouvertures/                  # Fichiers PGN source
├── renders/                     # Vidéos brutes rendues
├── tiktok_ready/               # Vidéos optimisées pour TikTok
├── audio/
│   ├── music/                  # Musique de fond
│   └── sfx/                    # Effets sonores
├── logs/                        # Logs du scheduler
├── temp/                        # Fichiers temporaires
│
├── game_fetcher.py             # Récupération de parties
├── stockfish_analyzer.py       # Analyse Stockfish
├── enhanced_renderer.py        # Rendu avec améliorations
├── comment_generator.py        # Génération de commentaires IA
├── audio_manager.py            # Gestion audio
├── tiktok_manager.py           # Préparation TikTok
├── main_pipeline.py            # Pipeline principal
├── scheduler.py                # Automatisation
└── README.md                   # Ce fichier
```

## 📤 Upload TikTok

### Méthode 1 : Manuel (Recommandé)

Le système génère automatiquement les métadonnées. Suivez les instructions :

```bash
# Voir la prochaine vidéo à uploader
python -c "from tiktok_manager import TikTokVideoPrep; TikTokVideoPrep().show_upload_instructions()"
```

1. Ouvrir TikTok (app ou web : https://www.tiktok.com/upload)
2. Sélectionner la vidéo indiquée
3. Copier-coller la caption générée
4. Publier !
5. Marquer comme uploadé dans le système

### Méthode 2 : Semi-Automatique

```bash
# Exporter pour outils d'automatisation
python -c "from tiktok_manager import TikTokVideoPrep; TikTokVideoPrep().export_for_automation()"
```

Utiliser avec des outils comme :
- TikTok Creator Tools API (officiel, nécessite approbation)
- Scripts d'automatisation navigateur (Selenium/Playwright)

## 🎨 Personnalisation

### Créer un Fichier de Configuration

```json
{
  "width": 1080,
  "height": 1920,
  "fps": 60,
  "move_seconds": 0.35,
  "enable_eval_bar": true,
  "enable_highlights": true,
  "enable_comments": true,
  "enable_audio": true,
  "stockfish_depth": 15,
  "anthropic_api_key": "votre_clé"
}
```

```bash
python main_pipeline.py --config my_config.json --count 5
```

### Modifier le Style Visuel

Éditer `enhanced_renderer.py` :

```python
# Couleurs des highlights
self.highlight_colors = {
    'brilliant': (255, 215, 0, 180),   # Or
    'blunder': (255, 50, 50, 150),     # Rouge
    'critical': (138, 43, 226, 150),   # Violet
}
```

### Ajouter des Parties Classiques

Éditer `game_fetcher.py`, section `_get_classic_games_database()` :

```python
{
    "name": "Ma_Partie_Iconique",
    "pgn": """[Event "Tournoi"]
[White "Joueur 1"]
[Black "Joueur 2"]
...
"""
}
```

## 📊 Monitoring & Analytics

### Logs du Scheduler

```bash
# Voir les logs en temps réel
tail -f logs/scheduler_*.log

# Rechercher les erreurs
grep "ERROR" logs/scheduler_*.log
```

### Statistiques TikTok

```python
from tiktok_manager import TikTokAnalytics

analytics = TikTokAnalytics()
analytics.log_video_stats("video.mp4", views=15000, likes=850, comments=42, shares=67)
analytics.show_summary()
```

## 🔧 Dépannage

### Stockfish Non Trouvé

```bash
# Installer Stockfish
sudo pacman -S stockfish  # Arch/Manjaro
sudo apt install stockfish  # Ubuntu/Debian
brew install stockfish      # macOS

# Ou spécifier le chemin manuellement
python main_pipeline.py --config '{"stockfish_path": "/chemin/vers/stockfish"}'
```

### Pas de Musique

```bash
# Vérifier les fichiers
ls -lh audio/music/

# Télécharger de la musique libre
# Voir section "Configuration Audio" ci-dessus
```

### Erreurs API Anthropic

```bash
# Vérifier la clé API
echo $ANTHROPIC_API_KEY

# Le système fonctionne sans, mais avec commentaires basiques
# Pour activer les commentaires IA, configurez la clé
```

### Problèmes FFmpeg

```bash
# Tester FFmpeg
ffmpeg -version

# Tester FFprobe
ffprobe -version

# Réinstaller si nécessaire
sudo pacman -S ffmpeg
```

## 🎯 Workflow de Production Recommandé

### Configuration Initiale (Une fois)

1. ✅ Installer toutes les dépendances
2. ✅ Configurer ANTHROPIC_API_KEY
3. ✅ Télécharger 5-10 musiques de fond
4. ✅ Tester avec 1 vidéo : `python main_pipeline.py --count 1`

### Production Quotidienne

1. 🚀 Lancer le scheduler : `python scheduler.py --videos-per-day 10`
2. ⏰ Le système génère automatiquement les vidéos
3. 📤 Uploader sur TikTok selon les instructions
4. 📊 Logger les statistiques pour optimisation

### Optimisation Continue

1. 📈 Analyser les vidéos performantes
2. 🎨 Ajuster les styles/couleurs si besoin
3. 🎵 Varier la musique de fond
4. 💬 Affiner les commentaires IA

## 📈 Performance Attendue

### Spécifications Techniques

- **Temps de rendu** : ~30-60 secondes par vidéo (selon durée)
- **Qualité** : Équivalente à Chess.com/Lichess
- **Taille fichier** : 5-20 MB par vidéo
- **Durée vidéo** : 15-90 secondes (optimal TikTok)

### Production

- **Capacité** : 50+ vidéos/jour possible
- **Recommandé** : 10-20 vidéos/jour pour qualité constante
- **Automatisation** : 95% automatique, 5% upload manuel

## 🤝 Contribution

Ce projet est open source. Améliorations bienvenues :

- Nouveaux styles visuels
- Parties classiques additionnelles
- Optimisations performance
- Intégrations API supplémentaires

## 📝 Licence

MIT License - Utilisation libre pour usage personnel et commercial.

## 🆘 Support

- GitHub Issues : [Créer un issue]
- Documentation Stockfish : https://stockfishchess.org/
- API Lichess : https://lichess.org/api
- Claude AI : https://www.anthropic.com/

## 🎬 Exemples de Résultats

Les vidéos générées incluent :

✅ Titre animé professionnel
✅ Barre d'évaluation en temps réel
✅ Highlights sur coups brillants/blunders
✅ Commentaires IA engageants
✅ Musique de fond
✅ Hashtags optimisés
✅ Format TikTok parfait

**Prêt pour l'upload et la viralité ! 🚀**

---

*Généré avec ♟️ par Kisyis Chess - Le meilleur générateur de contenu échecs pour TikTok*
