#!/usr/bin/env python3
"""Simple test - just one move with all features visible"""

import chess.pgn
from pathlib import Path
from main_pipeline import ChessTikTokPipeline

# Use quick game
pgn_file = Path("ouvertures/Immortal_Game_Anderssen_Kieseritzky_1851.pgn")
with open(pgn_file) as f:
    game = chess.pgn.read_game(f)

# Create pipeline
print("Creating pipeline...")
pipeline = ChessTikTokPipeline()
pipeline.config['enable_audio'] = False
pipeline.config['stockfish_depth'] = 15
pipeline.config['stockfish_time'] = 0.1

print(f"Config:")
print(f"  enable_eval_bar: {pipeline.config['enable_eval_bar']}")
print(f"  enable_highlights: {pipeline.config['enable_highlights']}")
print(f"  enable_comments: {pipeline.config['enable_comments']}")

# Generate
print("\nGenerating video...")
video = pipeline.generate_video(game, "test_simple")

print(f"\n[OK] Video: {video}")
print("\nOpen this video and check for:")
print("  1. LEFT evaluation bar that moves")
print("  2. Annotation badges (BRILLIANT!!, BLUNDER, etc.)")
print("  3. Move arrows/highlights")
