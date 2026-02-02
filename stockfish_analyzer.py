#!/usr/bin/env python3
"""
Stockfish analysis module for chess games
Provides evaluation scores and identifies key moments
"""

import chess
import chess.pgn
import chess.engine
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class MoveAnalysis:
    """Analysis data for a single move"""
    move_number: int
    move: chess.Move
    fen_before: str
    fen_after: str
    eval_before: float  # In centipawns, from white's perspective
    eval_after: float
    eval_change: float  # Positive = improvement for side to move
    is_brilliant: bool
    is_blunder: bool
    is_critical: bool
    best_move: Optional[chess.Move]
    pv_line: List[chess.Move]  # Principal variation


class StockfishAnalyzer:
    def __init__(self, stockfish_path=None, depth=20, time_limit=0.1):
        """
        Initialize Stockfish analyzer

        Args:
            stockfish_path: Path to stockfish binary (auto-detect if None)
            depth: Analysis depth
            time_limit: Time limit per position in seconds
        """
        self.depth = depth
        self.time_limit = time_limit

        # Try to find Stockfish
        if stockfish_path is None:
            stockfish_path = self._find_stockfish()

        self.engine_path = Path(stockfish_path)
        if not self.engine_path.exists():
            raise FileNotFoundError(
                f"Stockfish not found at {stockfish_path}. "
                "Please install: sudo apt install stockfish (Linux) or brew install stockfish (Mac)"
            )

        self.engine = None

    def _find_stockfish(self):
        """Try to auto-detect Stockfish installation"""
        common_paths = [
            "./stockfish",  # Project directory (current working directory)
            str(Path(__file__).parent / "stockfish"),  # Relative to this file
            "/usr/bin/stockfish",
            "/usr/local/bin/stockfish",
            "/opt/homebrew/bin/stockfish",
            "stockfish",  # In PATH
        ]

        for path in common_paths:
            if Path(path).exists() or path == "stockfish":
                return path

        raise FileNotFoundError(
            "Could not find Stockfish. Please install it:\n"
            "  Linux: sudo apt install stockfish\n"
            "  Mac: brew install stockfish\n"
            "  Or download from: https://stockfishchess.org/download/"
        )

    def __enter__(self):
        """Context manager entry"""
        self.engine = chess.engine.SimpleEngine.popen_uci(str(self.engine_path))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.engine:
            self.engine.quit()

    def _eval_to_cp(self, score, turn):
        """Convert score to centipawns from white's perspective"""
        if score.is_mate():
            # Mate score: very high value
            mate_in = score.mate()
            if mate_in > 0:
                cp = 10000 - mate_in * 100
            else:
                cp = -10000 - mate_in * 100
        else:
            cp = score.score()

        # ALWAYS from white's perspective - no adjustment for turn
        # (positive = white winning, negative = black winning)

        return cp

    def analyze_position(self, board: chess.Board) -> Dict:
        """Analyze a single position"""
        if self.engine is None:
            raise RuntimeError("Analyzer not initialized. Use 'with' statement.")

        info = self.engine.analyse(
            board,
            chess.engine.Limit(depth=self.depth, time=self.time_limit)
        )

        score = info.get("score")
        pv = info.get("pv", [])

        cp_score = self._eval_to_cp(score.white(), board.turn)

        return {
            "score": cp_score,
            "best_move": pv[0] if pv else None,
            "pv": pv
        }

    def analyze_game(self, game: chess.pgn.Game) -> List[MoveAnalysis]:
        """Analyze entire game and identify key moments"""
        if self.engine is None:
            raise RuntimeError("Analyzer not initialized. Use 'with' statement.")

        board = game.board()
        moves = list(game.mainline_moves())
        analyses = []

        prev_eval = 0.0

        for i, move in enumerate(moves):
            fen_before = board.fen()
            moving_side = board.turn  # Remember who is moving

            # Analyze position before move
            analysis_before = self.analyze_position(board)
            eval_before = analysis_before["score"]
            best_move = analysis_before["best_move"]
            pv = analysis_before["pv"]

            # Make the move
            board.push(move)
            fen_after = board.fen()

            # Analyze after move
            analysis_after = self.analyze_position(board)
            eval_after = analysis_after["score"]  # Keep white's perspective (no flip)

            # Calculate eval change (from moving side's perspective)
            # Positive = improvement for the side that moved
            eval_change = eval_after - eval_before
            if moving_side == chess.BLACK:  # If black moved, flip the change
                eval_change = -eval_change

            # Detect key moments
            is_brilliant = eval_change > 200 and move == best_move
            is_blunder = eval_change < -300
            is_critical = abs(eval_change) > 200

            move_analysis = MoveAnalysis(
                move_number=i + 1,
                move=move,
                fen_before=fen_before,
                fen_after=fen_after,
                eval_before=eval_before,
                eval_after=eval_after,
                eval_change=eval_change,
                is_brilliant=is_brilliant,
                is_blunder=is_blunder,
                is_critical=is_critical,
                best_move=best_move,
                pv_line=pv
            )

            analyses.append(move_analysis)
            prev_eval = eval_after

        return analyses

    def get_critical_positions(self, analyses: List[MoveAnalysis], top_n=5) -> List[MoveAnalysis]:
        """Get the most critical positions in the game"""
        sorted_analyses = sorted(
            analyses,
            key=lambda x: abs(x.eval_change),
            reverse=True
        )
        return sorted_analyses[:top_n]

    def format_eval_for_display(self, cp_score: float) -> str:
        """Format evaluation score for display"""
        if abs(cp_score) > 5000:
            # Mate score
            mate_in = (10000 - abs(cp_score)) // 100
            return f"M{mate_in}" if cp_score > 0 else f"-M{mate_in}"
        else:
            # Regular score
            pawns = cp_score / 100.0
            return f"{pawns:+.1f}"


def analyze_pgn_file(pgn_path: Path, stockfish_path=None):
    """Analyze a PGN file and print results"""
    with open(pgn_path) as f:
        game = chess.pgn.read_game(f)

    if not game:
        print(f"Could not read game from {pgn_path}")
        return

    print(f"Analyzing: {game.headers.get('White')} vs {game.headers.get('Black')}")
    print(f"Event: {game.headers.get('Event', 'Unknown')}")

    with StockfishAnalyzer(stockfish_path=stockfish_path, depth=15) as analyzer:
        analyses = analyzer.analyze_game(game)

        print(f"\nAnalyzed {len(analyses)} moves")

        # Find brilliant moves
        brilliant = [a for a in analyses if a.is_brilliant]
        if brilliant:
            print(f"\n🌟 Brilliant moves: {len(brilliant)}")
            for a in brilliant[:3]:
                print(f"  Move {a.move_number}: {a.move.uci()} (eval change: {a.eval_change:+.0f})")

        # Find blunders
        blunders = [a for a in analyses if a.is_blunder]
        if blunders:
            print(f"\n⚠️  Blunders: {len(blunders)}")
            for a in blunders[:3]:
                print(f"  Move {a.move_number}: {a.move.uci()} (eval change: {a.eval_change:+.0f})")

        # Critical positions
        critical = analyzer.get_critical_positions(analyses, top_n=5)
        print(f"\n🔥 Critical moments:")
        for a in critical:
            print(f"  Move {a.move_number}: {a.move.uci()} "
                  f"({analyzer.format_eval_for_display(a.eval_before)} → "
                  f"{analyzer.format_eval_for_display(a.eval_after)})")

    return analyses


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        pgn_file = Path(sys.argv[1])
        analyze_pgn_file(pgn_file)
    else:
        print("Usage: python stockfish_analyzer.py <pgn_file>")
        print("\nTesting with sample game...")

        # Create a sample game
        game = chess.pgn.Game()
        game.headers["Event"] = "Test"
        game.headers["White"] = "Player1"
        game.headers["Black"] = "Player2"

        node = game
        for move in ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"]:
            node = node.add_variation(chess.Move.from_uci(move))

        with StockfishAnalyzer(depth=10) as analyzer:
            analyses = analyzer.analyze_game(game)
            print(f"Analyzed {len(analyses)} moves")
            for a in analyses:
                print(f"Move {a.move_number}: {a.move.uci()} - "
                      f"{analyzer.format_eval_for_display(a.eval_after)}")
