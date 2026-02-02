# 🚀 Upload Automatique TikTok

## 📋 Vue d'ensemble

Le système d'upload automatique TikTok utilise Playwright pour automatiser la publication de vidéos sur TikTok directement depuis le pipeline de génération.

**Fonctionnalités :**
- ✅ Connexion automatique avec Google
- ✅ Upload de vidéos
- ✅ Ajout automatique de titre et hashtags
- ✅ Sélection de musique recommandée par TikTok
- ✅ Publication automatique

## 🔧 Installation

### Prérequis

Playwright et Chromium doivent être installés :

```bash
# Activer l'environnement virtuel
source venv_chess/bin/activate

# Installer Playwright (déjà fait)
pip install playwright

# Installer le navigateur Chromium (déjà fait)
playwright install chromium
```

## 🎯 Utilisation

### Option 1 : Via le Pipeline Principal

Pour activer l'upload automatique lors de la génération de vidéos :

```bash
# Générer 1 vidéo et l'uploader automatiquement
python main_pipeline.py --count 1 --auto-upload

# Générer 5 vidéos et les uploader automatiquement
python main_pipeline.py --count 5 --auto-upload

# Production avec upload automatique (10 vidéos)
python main_pipeline.py --count 10 --auto-upload
```

**Au premier lancement :**
1. Une fenêtre de navigateur s'ouvrira automatiquement
2. Vous devrez vous connecter à TikTok avec votre compte Google
3. Après connexion, la session sera sauvegardée dans `tiktok_session.json`
4. Les uploads suivants utiliseront cette session (pas besoin de se reconnecter)

### Option 2 : Upload Manuel d'une Vidéo Existante

Pour uploader une vidéo déjà générée :

```bash
# Activer l'environnement virtuel
source venv_chess/bin/activate

# Lancer le script Python interactif
python
```

```python
from tiktok_auto_uploader import TikTokAutoUploader
from pathlib import Path

# Initialiser l'uploader
uploader = TikTokAutoUploader(headless=False)

# Se connecter (première fois seulement)
uploader.login_with_google()

# Uploader une vidéo
uploader.upload_video(
    video_path=Path("tiktok_ready/Kasparov_Topalov_1999_Wijk_aan_Zee.mp4"),
    title="♟️ Kasparov vs Topalov - Immortal Game",
    hashtags=["chess", "chessgame", "chessmaster", "chesstok"],
    description="Wijk aan Zee 1999 - One of the greatest games ever played",
    use_recommended_music=True,
    publish=True  # False = sauvegarder comme brouillon
)

# Fermer
uploader.close()
```

## 📝 Paramètres d'Upload

Lors de l'upload d'une vidéo, vous pouvez configurer :

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `video_path` | Chemin vers la vidéo | `Path("tiktok_ready/video.mp4")` |
| `title` | Titre de la vidéo | `"♟️ Magnus Carlsen vs Hikaru Nakamura"` |
| `hashtags` | Liste de hashtags (sans #) | `["chess", "chessgame", "chesstok"]` |
| `description` | Description additionnelle | `"World Championship 2023"` |
| `use_recommended_music` | Utiliser musique TikTok | `True` ou `False` |
| `publish` | Publier immédiatement | `True` (publier) ou `False` (brouillon) |

## 🔐 Gestion de Session

### Session Sauvegardée

Après la première connexion, vos identifiants de session sont sauvegardés dans :
```
tiktok_session.json
```

**Important :**
- ⚠️ Ne partagez jamais ce fichier (contient vos cookies de session)
- ✅ Ajouté automatiquement à `.gitignore`
- 🔄 Session valide pendant plusieurs semaines
- 🔑 Supprimez le fichier pour forcer une nouvelle connexion

### Réinitialiser la Session

Si vous avez des problèmes de connexion :

```bash
rm tiktok_session.json
```

La prochaine utilisation demandera une nouvelle connexion.

## 🎬 Workflow Complet

### Production Quotidienne Automatisée

```bash
# 1. Générer 10 vidéos et les uploader automatiquement
source venv_chess/bin/activate
python main_pipeline.py --count 10 --auto-upload

# 2. Le système va :
#    - Générer les 10 vidéos
#    - Pour chaque vidéo :
#      a) Ouvrir TikTok (ou réutiliser la session)
#      b) Uploader la vidéo
#      c) Ajouter titre + hashtags
#      d) Sélectionner musique recommandée
#      e) Publier
#    - Fermer le navigateur
```

### Mode Brouillon (Pour Révision)

Si vous préférez réviser avant publication, modifiez `main_pipeline.py` :

```python
# Ligne 283 dans main_pipeline.py
success = uploader.upload_video(
    video_path=tiktok_video,
    title=title,
    hashtags=hashtags,
    description=description,
    use_recommended_music=True,
    publish=False  # Changez True à False pour sauver comme brouillon
)
```

## ⚙️ Configuration Avancée

### Mode Headless (Sans Interface)

Pour exécuter sans afficher le navigateur (après première connexion) :

```python
uploader = TikTokAutoUploader(headless=True)
```

**Note :** Le mode headless ne fonctionne que si vous avez déjà une session sauvegardée.

### Fichier de Session Personnalisé

```python
uploader = TikTokAutoUploader(
    session_file="./custom_session.json"
)
```

## 🔍 Débogage

### Problème : Le navigateur ne s'ouvre pas

```bash
# Vérifier l'installation de Chromium
playwright install chromium

# Tester Playwright
python -m playwright codegen tiktok.com
```

### Problème : "Login failed" ou timeout

1. Vérifiez votre connexion internet
2. Supprimez `tiktok_session.json` et reconnectez-vous
3. Assurez-vous que votre compte Google peut accéder à TikTok
4. Essayez de vous connecter manuellement à TikTok d'abord

### Problème : Upload échoue silencieusement

Le script affichera un message vous permettant de compléter manuellement :

```
⏸️  Appuyez sur Entrée une fois que vous avez vérifié/publié manuellement...
```

Vous pouvez alors :
1. Vérifier les détails de la vidéo dans le navigateur
2. Cliquer sur "Publier" manuellement si nécessaire
3. Appuyer sur Entrée pour continuer

## 📊 Exemples de Production

### Exemple 1 : Upload Simple

```bash
python main_pipeline.py --count 1 --auto-upload
```

**Résultat :** 1 vidéo générée et uploadée sur TikTok

### Exemple 2 : Production en Masse

```bash
python main_pipeline.py --count 20 --auto-upload
```

**Résultat :** 20 vidéos générées et uploadées automatiquement
**Durée estimée :** ~30-60 min (selon votre machine)

### Exemple 3 : Sans Upload (Test)

```bash
python main_pipeline.py --count 5
```

**Résultat :** 5 vidéos générées, sauvegardées localement dans `tiktok_ready/`
**Usage :** Pour tester les vidéos avant upload

## 🎯 Recommandations

### Pour Débutants
1. ✅ Commencez sans `--auto-upload` pour tester
2. ✅ Uploadez 1-2 vidéos manuellement pour comprendre
3. ✅ Activez `--auto-upload` une fois à l'aise

### Pour Production
1. ✅ Utilisez `--auto-upload` pour gagner du temps
2. ✅ Générez 10-20 vidéos par jour maximum
3. ✅ Vérifiez les premiers uploads pour assurer la qualité
4. ✅ Gardez `tiktok_session.json` en sécurité

### Limitations TikTok
- 📊 Maximum recommandé : 20 vidéos/jour
- ⏱️ Laissez ~1-2 minutes entre chaque upload
- 🔄 Ne uploadez pas trop vite (risque de spam detection)

## 🚨 Sécurité

### Données Sensibles

**Ne commitez JAMAIS :**
- `tiktok_session.json` (cookies de session)
- Tout fichier contenant vos identifiants

**Déjà protégé dans `.gitignore` :**
```
tiktok_session.json
*.session
```

### Bonnes Pratiques

1. ✅ Changez votre mot de passe TikTok régulièrement
2. ✅ Utilisez l'authentification 2FA sur TikTok
3. ✅ Ne partagez pas vos fichiers de session
4. ✅ Exécutez sur une machine de confiance

## 📚 Ressources

- [Playwright Documentation](https://playwright.dev/python/)
- [TikTok Upload Guidelines](https://www.tiktok.com/community-guidelines)
- [TikTok API Limits](https://developers.tiktok.com/doc/overview)

## ✨ Résumé

```bash
# Installation (une fois)
source venv_chess/bin/activate
pip install playwright
playwright install chromium

# Utilisation quotidienne
python main_pipeline.py --count 10 --auto-upload

# Premier lancement : connexion Google dans le navigateur
# Suivants : upload automatique sans intervention
```

**C'est tout ! Vos vidéos sont maintenant uploadées automatiquement sur TikTok ! 🎉**
