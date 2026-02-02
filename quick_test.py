#!/usr/bin/env python3
"""Quick test with shorter game"""

import chess.pgn
from pathlib import Path
from main_pipeline import ChessTikTokPipeline

# Use shorter game (Immortal Game - only 23 moves)
pgn_file = Path("ouvertures/Immortal_Game_Anderssen_Kieseritzky_1851.pgn")

with open(pgn_file) as f:
    game = chess.pgn.read_game(f)

# Create pipeline with faster Stockfish
pipeline = ChessTikTokPipeline()
pipeline.config['enable_audio'] = False
pipeline.config['stockfish_depth'] = 12  # Faster analysis
pipeline.config['stockfish_time'] = 0.05  # Faster per position

print("🚀 Generating quick test video...")
video = pipeline.generate_video(game, "quick_test")

print(f"\n✅ VIDÉO PRÊTE: {video}")
print("\n🎬 Vérifiez:")
print("  ✓ Barre d'évaluation à GAUCHE")
print("  ✓ Badges d'annotation (BRILLIANT, BLUNDER, etc.)")
