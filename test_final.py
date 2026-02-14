#!/usr/bin/env python3
"""Test final avec toutes les corrections"""

import chess.pgn
from pathlib import Path
from main_pipeline import ChessTikTokPipeline

# Use Immortal Game (courte avec checkmate à la fin)
pgn_file = Path("ouvertures/Immortal_Game_Anderssen_Kieseritzky_1851.pgn")

with open(pgn_file) as f:
    game = chess.pgn.read_game(f)

# Create pipeline
print(" Génération vidéo avec TOUTES les corrections:")
print("  [OK] Barre d'évaluation VISIBLE à gauche (x=20)")
print("  [OK] CHECKMATE détecté au lieu de BLUNDER")
print("  [OK] Badges raccourcis (MISTAKE au lieu de INACCURACY)")
print("  [OK] Profondeur Stockfish augmentée à 20")
print()

pipeline = ChessTikTokPipeline()
pipeline.config['enable_audio'] = False

# Generate
video = pipeline.generate_video(game, "test_final_fixed")

print(f"\n[OK] Video: {video}")
print("\n Vérifiez:")
print("  1. Barre d'évaluation VISIBLE à gauche")
print("  2. Dernier coup = CHECKMATE (pas BLUNDER)")
print("  3. Badges plus courts")
