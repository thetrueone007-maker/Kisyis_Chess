#!/usr/bin/env python3
"""Test avec barre d'évaluation fluide et bien positionnée"""

import chess.pgn
from pathlib import Path
from main_pipeline import ChessTikTokPipeline

# Use Immortal Game
pgn_file = Path("ouvertures/Immortal_Game_Anderssen_Kieseritzky_1851.pgn")

with open(pgn_file) as f:
    game = chess.pgn.read_game(f)

print("🎬 Test avec barre d'évaluation CORRIGÉE:")
print("  ✓ Position: Dans la marge de gauche (pas superposée)")
print("  ✓ Animation: Interpolation fluide entre les valeurs")
print("  ✓ CHECKMATE détecté")
print()

pipeline = ChessTikTokPipeline()
pipeline.config['enable_audio'] = False

video = pipeline.generate_video(game, "test_smooth_eval")

print(f"\n✅ Video: {video}")
print("\n🔍 À vérifier:")
print("  1. Barre à GAUCHE (dans l'espace libre, pas sur l'échiquier)")
print("  2. Transitions FLUIDES (pas de sauts brusques)")
print("  3. CHECKMATE au dernier coup")
