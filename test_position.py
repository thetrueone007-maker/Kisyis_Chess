#!/usr/bin/env python3
"""Test rapide de la position de la barre"""

import chess.pgn
from pathlib import Path
from main_pipeline import ChessTikTokPipeline

pgn_file = Path("ouvertures/Immortal_Game_Anderssen_Kieseritzky_1851.pgn")
with open(pgn_file) as f:
    game = chess.pgn.read_game(f)

print(" Test position barre d'évaluation")
print("  Position: margin_x - bar_width - 15px")
print("  Sécurité: min 10px du bord")
print()

pipeline = ChessTikTokPipeline()
pipeline.config['enable_audio'] = False

video = pipeline.generate_video(game, "test_bar_position")
print(f"\n[OK] Video: {video}")
