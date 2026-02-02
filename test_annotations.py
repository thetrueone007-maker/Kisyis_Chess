#!/usr/bin/env python3
"""Quick test to generate one video with annotations"""

import chess.pgn
from pathlib import Path
from main_pipeline import ChessTikTokPipeline

# Use an existing game
pgn_file = Path("ouvertures/Kasparov_Topalov_1999_Wijk_aan_Zee.pgn")

with open(pgn_file) as f:
    game = chess.pgn.read_game(f)

# Create pipeline
pipeline = ChessTikTokPipeline()
pipeline.config['enable_audio'] = False  # Skip audio for speed

# Generate video
video = pipeline.generate_video(game, "test_with_annotations")

print(f"\n✅ Video generated: {video}")
print("Check the video to see:")
print("  - Evaluation bar on the LEFT side")
print("  - Move annotation badges (Brilliant, Blunder, etc.)")
