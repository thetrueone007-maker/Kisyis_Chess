#!/usr/bin/env python3
"""
AI-powered commentary generation for chess games
Generates engaging, educational comments for TikTok videos
"""

import os
import chess
import chess.pgn
from typing import List, Dict, Optional
from anthropic import Anthropic
from stockfish_analyzer import MoveAnalysis


class CommentGenerator:
    """Generate AI commentary for chess moves"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize comment generator

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("[!] Warning: No Anthropic API key provided.")
            print("    Set ANTHROPIC_API_KEY environment variable to enable AI comments")
            print("    Falling back to template-based comments")
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)

    def generate_opening_comment(self, game: chess.pgn.Game) -> str:
        """Generate introductory comment about the game"""
        white = game.headers.get("White", "White")
        black = game.headers.get("Black", "Black")
        event = game.headers.get("Event", "Game")
        opening = game.headers.get("Opening", "")

        # Template-based fallback
        templates = [
            f" {white} vs {black} - {event}",
            f"[FIRE] Epic battle: {white} vs {black}",
            f"[CHESS] Legendary game from {event}",
        ]

        if opening:
            templates.append(f"[BOOK] {opening} - Watch this masterpiece!")

        if not self.client:
            import random
            return random.choice(templates)

        # AI-generated
        prompt = f"""Generate an engaging 10-15 word TikTok-style intro for this chess game:
White: {white}
Black: {black}
Event: {event}
Opening: {opening}

Make it exciting and hook the viewer. Use emojis. Be concise."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"AI comment failed: {e}")
            import random
            return random.choice(templates)

    def generate_move_comment(self, analysis: MoveAnalysis, board_before: chess.Board,
                              game_context: Dict) -> Optional[str]:
        """
        Generate comment for a specific move

        Args:
            analysis: Move analysis data
            board_before: Board position before the move
            game_context: Game metadata and context
        """
        # Only comment on interesting moves
        if not (analysis.is_brilliant or analysis.is_blunder or analysis.is_critical):
            return None

        move_san = board_before.san(analysis.move)

        # Template fallback
        if analysis.is_brilliant:
            template = f"[STAR] BRILLIANT! {move_san} - Incredible move!"
        elif analysis.is_blunder:
            template = f"[WARN] BLUNDER! {move_san} loses the advantage"
        elif abs(analysis.eval_change) > 300:
            template = f"[FIRE] CRITICAL! {move_san} changes everything"
        else:
            template = f"[IDEA] Key move: {move_san}"

        if not self.client:
            return template

        # AI-generated
        eval_before = analysis.eval_before / 100
        eval_after = analysis.eval_after / 100
        piece_type = board_before.piece_at(analysis.move.from_square).piece_type

        piece_names = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king"
        }

        prompt = f"""Generate a 12-15 word exciting TikTok comment for this chess move:

Move: {move_san} ({piece_names[piece_type]})
Evaluation before: {eval_before:+.1f}
Evaluation after: {eval_after:+.1f}
Change: {analysis.eval_change/100:+.1f}
Type: {"BRILLIANT" if analysis.is_brilliant else "BLUNDER" if analysis.is_blunder else "CRITICAL"}

Make it punchy, use 1-2 emojis, explain WHY it's significant in simple terms. TikTok audience."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"AI comment failed: {e}")
            return template

    def generate_endgame_comment(self, game: chess.pgn.Game, analyses: List[MoveAnalysis]) -> str:
        """Generate concluding comment"""
        result = game.headers.get("Result", "*")
        white = game.headers.get("White", "White")
        black = game.headers.get("Black", "Black")

        # Count brilliant moves and blunders
        brilliants = sum(1 for a in analyses if a.is_brilliant)
        blunders = sum(1 for a in analyses if a.is_blunder)

        template = ""
        if result == "1-0":
            template = f"[OK] {white} wins! {brilliants} brilliant moves"
        elif result == "0-1":
            template = f"[OK] {black} wins! {brilliants} brilliant moves"
        else:
            template = f" Draw - {brilliants} brilliant moves from both sides"

        if not self.client:
            return template

        # AI-generated
        prompt = f"""Generate a 12-15 word TikTok-style outro for this chess game:

Winner: {result}
White: {white}
Black: {black}
Brilliant moves: {brilliants}
Blunders: {blunders}

Make it exciting, congratulate the winner (or both for a draw). Use emojis. End on a high note."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"AI comment failed: {e}")
            return template

    def generate_hashtags(self, game: chess.pgn.Game) -> List[str]:
        """Generate relevant hashtags for TikTok"""
        white = game.headers.get("White", "").replace(" ", "")
        black = game.headers.get("Black", "").replace(" ", "")

        hashtags = [
            "#chess",
            "#chessgame",
            "#chessplayer",
            "#chesstok",
            "#chessmaster",
            "#chessmoves",
            "#chesstactic",
            "#chessstrategy"
        ]

        # Add player-specific tags if they're famous
        famous_players = {
            "MagnusCarlsen": "#magnuscarlsen",
            "Hikaru": "#hikaru",
            "DrNykterstein": "#magnuscarlsen",
            "FabianoCaruana": "#fabianocaruana",
        }

        for player, tag in famous_players.items():
            if player.lower() in white.lower() or player.lower() in black.lower():
                hashtags.append(tag)

        return hashtags


class CommentScheduler:
    """Schedule when comments should appear in the video"""

    def __init__(self, analyses: List[MoveAnalysis], fps: int = 120,
                 move_duration_seconds: float = 0.35):
        self.analyses = analyses
        self.fps = fps
        self.move_duration_seconds = move_duration_seconds
        self.frames_per_move = int(fps * move_duration_seconds)

    def get_comments_timeline(self, generator: CommentGenerator,
                              game: chess.pgn.Game) -> Dict[int, str]:
        """
        Generate timeline of when comments should appear

        Returns:
            Dict mapping frame number to comment text
        """
        timeline = {}
        board = game.board()

        # Opening comment at frame 0
        opening_comment = generator.generate_opening_comment(game)
        timeline[0] = opening_comment

        # Track frame numbers
        title_frames = int((1.0 + 0.6) * self.fps)  # Title display duration
        current_frame = title_frames

        # Move-by-move comments
        for i, analysis in enumerate(self.analyses):
            comment = generator.generate_move_comment(
                analysis,
                board,
                {"game": game}
            )

            if comment:
                # Show comment at the start of this move
                timeline[current_frame] = comment

            board.push(analysis.move)
            current_frame += self.frames_per_move

        # Endgame comment
        endgame_comment = generator.generate_endgame_comment(game, self.analyses)
        timeline[current_frame] = endgame_comment

        return timeline


if __name__ == "__main__":
    # Test the comment generator
    print("Comment Generator Test")
    print("=" * 50)

    generator = CommentGenerator()

    # Create sample game
    game = chess.pgn.Game()
    game.headers["White"] = "Magnus Carlsen"
    game.headers["Black"] = "Hikaru Nakamura"
    game.headers["Event"] = "Speed Chess Championship"
    game.headers["Result"] = "1-0"

    print("\nOpening comment:")
    print(generator.generate_opening_comment(game))

    print("\nHashtags:")
    print(" ".join(generator.generate_hashtags(game)))

    # Sample move analysis
    from stockfish_analyzer import MoveAnalysis
    sample_analysis = MoveAnalysis(
        move_number=15,
        move=chess.Move.from_uci("e2e4"),
        fen_before="",
        fen_after="",
        eval_before=50,
        eval_after=250,
        eval_change=200,
        is_brilliant=True,
        is_blunder=False,
        is_critical=True,
        best_move=None,
        pv_line=[]
    )

    print("\nBrilliant move comment:")
    board = chess.Board()
    print(generator.generate_move_comment(sample_analysis, board, {"game": game}))

    print("\nEndgame comment:")
    print(generator.generate_endgame_comment(game, [sample_analysis]))
