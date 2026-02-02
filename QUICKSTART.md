# 🚀 Guide de Démarrage Rapide - 5 Minutes

## ⚡ Installation Express

```bash
# 1. Exécuter le script de setup
chmod +x setup.sh
./setup.sh

# 2. Activer l'environnement virtuel
source venv_chess/bin/activate
```

## 🎬 Première Vidéo (Test)

```bash
# Générer une vidéo de test
python main_pipeline.py --count 1
```

**Résultat** : Vidéo dans `./tiktok_ready/`

## 📤 Upload TikTok

```bash
# Voir les instructions d'upload
python -c "from tiktok_manager import TikTokVideoPrep; TikTokVideoPrep().show_upload_instructions()"
```

1. Copier la caption générée
2. Ouvrir TikTok : https://www.tiktok.com/upload
3. Uploader la vidéo du dossier `tiktok_ready/`
4. Coller la caption
5. Publier ! 🎉

## 🔄 Production Automatique

```bash
# Lancer la production automatique (10 vidéos/jour)
python scheduler.py --videos-per-day 10
```

Le système génère automatiquement les vidéos. Vous n'avez qu'à les uploader !

## ⚙️ Configuration Optionnelle (Recommandée)

### 1. API Claude pour Commentaires IA

```bash
# Obtenir une clé : https://console.anthropic.com/
export ANTHROPIC_API_KEY="votre_clé_api"

# Rendre permanent
echo 'export ANTHROPIC_API_KEY="votre_clé_api"' >> ~/.bashrc
```

### 2. Installer Stockfish (Barre d'Évaluation)

```bash
# Manjaro/Arch
sudo pacman -S stockfish

# Ubuntu/Debian
sudo apt install stockfish

# macOS
brew install stockfish
```

### 3. Ajouter de la Musique

```bash
# Télécharger musique libre de droits
# YouTube Audio Library, Pixabay Music, etc.

# Placer les MP3 dans :
mkdir -p audio/music
# Copier vos fichiers MP3 ici
```

## 📊 Commandes Utiles

```bash
# Générer 5 vidéos immédiatement
python main_pipeline.py --count 5

# Générer 10 vidéos (70% Lichess, 30% classiques)
python main_pipeline.py --count 10 --mix-ratio 0.7

# Production intensive : 20 vidéos/jour
python scheduler.py --videos-per-day 20

# Test scheduler (1 batch maintenant, puis arrêt)
python scheduler.py --once

# Voir les logs
tail -f logs/scheduler_*.log
```

## 🎯 Workflow Quotidien

### Première fois
1. ✅ Lancer `./setup.sh`
2. ✅ Tester avec `python main_pipeline.py --count 1`
3. ✅ Uploader la vidéo test sur TikTok
4. ✅ Configurer ANTHROPIC_API_KEY (optionnel)
5. ✅ Ajouter 5-10 musiques de fond

### Ensuite
1. 🚀 Lancer `python scheduler.py --videos-per-day 10`
2. ⏰ Laisser tourner (génère automatiquement)
3. 📤 Uploader les vidéos sur TikTok quotidiennement
4. 📊 Analyser les performances
5. 🔄 Répéter !

## 🔧 Dépannage Express

### Pas de Musique
```bash
# Le système fonctionne sans, mais recommandé pour TikTok
# Télécharger des MP3 et les mettre dans audio/music/
```

### Stockfish Non Trouvé
```bash
# Installer Stockfish (voir ci-dessus)
# Ou désactiver temporairement :
python main_pipeline.py --count 1 --no-eval
```

### Erreur Python
```bash
# Réactiver l'environnement
source venv_chess/bin/activate

# Réinstaller dépendances
pip install -r requirements.txt
```

## 📈 Performance Attendue

- **Génération** : ~30-60 sec par vidéo
- **Qualité** : Professionnelle (comme Chess.com)
- **Format** : Parfait pour TikTok (9:16, 1080x1920)
- **Automatisation** : 95% automatique

## 🎯 Objectif Production

### Recommandé : 10 vidéos/jour
- ✅ Qualité constante
- ✅ Charge serveur raisonnable
- ✅ Facile à uploader manuellement
- ✅ Bon pour croissance organique

### Intensif : 20+ vidéos/jour
- ✅ Croissance rapide
- ✅ Saturation algorithme TikTok
- ⚠️ Nécessite automation upload
- ⚠️ Plus de stockage/bande passante

## 🆘 Besoin d'Aide ?

1. **README.md** - Documentation complète
2. **GitHub Issues** - Problèmes techniques
3. **Logs** - `logs/scheduler_*.log`

## ✨ Exemple de Résultat

Chaque vidéo inclut :

✅ Titre animé pro
✅ Barre d'évaluation Stockfish
✅ Highlights coups brillants
✅ Commentaires IA engageants
✅ Musique de fond
✅ Hashtags optimisés
✅ Format TikTok parfait

**Prêt pour la viralité ! 🚀**

---

**Temps total : 5 minutes de setup → Production illimitée automatique ! ♟️**
