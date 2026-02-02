#!/bin/bash
# Script pour télécharger les sons de Chess.com

echo "📥 Téléchargement des sons Chess.com..."

# Créer le dossier
mkdir -p audio/sfx/chesscom

# Télécharger les sons
curl -L -o audio/sfx/chesscom/move.mp3 \
  "https://images.chesscomfiles.com/chess-themes/sounds/_MP3_/default/move-self.mp3"

curl -L -o audio/sfx/chesscom/capture.mp3 \
  "https://images.chesscomfiles.com/chess-themes/sounds/_MP3_/default/capture.mp3"

# Sons additionnels optionnels
curl -L -o audio/sfx/chesscom/check.mp3 \
  "https://images.chesscomfiles.com/chess-themes/sounds/_MP3_/default/move-check.mp3" 2>/dev/null || true

curl -L -o audio/sfx/chesscom/castle.mp3 \
  "https://images.chesscomfiles.com/chess-themes/sounds/_MP3_/default/castle.mp3" 2>/dev/null || true

# Copier vers le dossier sfx
cp -f audio/sfx/chesscom/move.mp3 audio/sfx/
cp -f audio/sfx/chesscom/capture.mp3 audio/sfx/

echo "✅ Sons Chess.com téléchargés et installés!"
ls -lh audio/sfx/*.mp3
