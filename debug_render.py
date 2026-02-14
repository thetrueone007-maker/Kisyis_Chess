#!/usr/bin/env python3
"""Debug script to test rendering features"""

import chess
import chess.pgn
from pathlib import Path
from PySide6.QtWidgets import QApplication
from enhanced_renderer import EnhancedRenderer, MoveHighlight
from stockfish_analyzer import MoveAnalysis

# Initialize Qt
app = QApplication([])

# Create renderer with all features enabled
renderer = EnhancedRenderer(
    assets_dir="assets",
    width=1080,
    height=1920,
    fps=60,
    out_dir="temp",
    move_seconds=1.0,
    show_eval_bar=True,
    show_highlights=True,
    show_comments=True
)

# Load a game
pgn_file = Path("ouvertures/Kasparov_Topalov_1999_Wijk_aan_Zee.pgn")
with open(pgn_file) as f:
    game = chess.pgn.read_game(f)

# Render a test frame with the 3rd position
board = chess.Board()
for move in list(game.mainline_moves())[:3]:
    board.push(move)

print(f"Position after 3 moves: {board.fen()}")

positions = renderer.compose_piece_positions(board)

# Create test annotation
test_annotation = MoveAnalysis(
    move_number=3,
    move=list(game.mainline_moves())[2],
    fen_before=chess.Board().fen(),
    fen_after=board.fen(),
    eval_before=50,
    eval_after=120,
    eval_change=70,
    is_brilliant=True,
    is_blunder=False,
    is_critical=False,
    best_move=list(game.mainline_moves())[2],
    pv_line=[]
)

print("\nRendering test frame...")
print(f"  show_eval_bar: {renderer.show_eval_bar}")
print(f"  show_highlights: {renderer.show_highlights}")
print(f"  show_comments: {renderer.show_comments}")

qimg = renderer.render_enhanced_frame(
    board,
    positions,
    "TEST FRAME",
    'small',
    1.0,
    eval_cp=120,  # White is ahead
    highlights=[MoveHighlight(from_square=11, to_square=27, color=(255, 215, 0, 180))],
    comment="This is a test comment to verify rendering works",
    move_annotation=test_annotation
)

# Save test frame
test_file = Path("temp/debug_frame.png")
qimg.save(str(test_file))

print(f"\n[OK] Test frame saved: {test_file}")
print("\nCheck this image for:")
print("  1. Evaluation bar on the LEFT (should show +1.2)")
print("  2. BRILLIANT!! badge in top-right")
print("  3. Yellow arrow/highlight")
print("  4. Comment box at bottom")
