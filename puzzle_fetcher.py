#!/usr/bin/env python3
"""
Module to fetch chess puzzles from Lichess API.
Converts puzzles into chess.pgn.Game objects compatible with the existing pipeline.
Tracks processed puzzles to avoid repeats.
"""

import json
import random
import time
import requests
import chess
import chess.pgn
from io import StringIO
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict


class PuzzleFetcher:
    """Fetch and manage chess puzzles from Lichess"""

    LICHESS_API = "https://lichess.org/api"

    def __init__(self, cache_file="./puzzle_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load cache of already processed puzzles"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"processed_puzzles": [], "known_ids": []}

    def _save_cache(self):
        """Save cache to disk"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def _is_new_puzzle(self, puzzle_id: str) -> bool:
        """Check if puzzle hasn't been used before"""
        return puzzle_id not in self.cache["processed_puzzles"]

    def _mark_processed(self, puzzle_id: str):
        """Add to processed list and save cache"""
        if puzzle_id not in self.cache["processed_puzzles"]:
            self.cache["processed_puzzles"].append(puzzle_id)
            self._save_cache()

    def fetch_daily_puzzle(self) -> Optional[dict]:
        """Fetch the daily puzzle from Lichess"""
        try:
            response = requests.get(
                f"{self.LICHESS_API}/puzzle/daily",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[WARN] Error fetching daily puzzle: {e}")
        return None

    def fetch_puzzle_by_id(self, puzzle_id: str) -> Optional[dict]:
        """Fetch a specific puzzle by ID"""
        try:
            response = requests.get(
                f"{self.LICHESS_API}/puzzle/{puzzle_id}",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[WARN] Error fetching puzzle {puzzle_id}: {e}")
        return None

    def fetch_random_puzzles(self, count: int = 5, max_retries: int = 50) -> List[dict]:
        """
        Fetch multiple unique puzzles.
        Strategy:
        1. Try the daily puzzle first
        2. Use Lichess puzzle activity/batch endpoints
        3. Explore puzzle IDs discovered from API responses
        """
        puzzles = []
        tried_ids = set(self.cache["processed_puzzles"])

        print(f"[PUZZLE] Fetching {count} unique puzzles from Lichess...")

        # 1. Try daily puzzle
        daily = self.fetch_daily_puzzle()
        if daily and daily.get('puzzle', {}).get('id'):
            pid = daily['puzzle']['id']
            if self._is_new_puzzle(pid):
                puzzles.append(daily)
                tried_ids.add(pid)
                print(f"   [OK] Daily puzzle #{pid} (rating: {daily['puzzle'].get('rating', '?')})")

        if len(puzzles) >= count:
            return puzzles[:count]

        # 2. Fetch puzzles from the Lichess puzzle storm/batch-like approach
        #    Use the puzzle/next endpoint style by trying known ID patterns
        #    Lichess puzzle IDs are 5-character alphanumeric strings
        attempts = 0
        while len(puzzles) < count and attempts < max_retries:
            attempts += 1
            # Generate a random 5-char puzzle ID (Lichess uses a-zA-Z0-9)
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            random_id = ''.join(random.choices(chars, k=5))

            if random_id in tried_ids:
                continue
            tried_ids.add(random_id)

            puzzle = self.fetch_puzzle_by_id(random_id)
            if puzzle and puzzle.get('puzzle', {}).get('id'):
                pid = puzzle['puzzle']['id']
                if self._is_new_puzzle(pid):
                    puzzles.append(puzzle)
                    # Store discovered ID for future reference
                    if pid not in self.cache["known_ids"]:
                        self.cache["known_ids"].append(pid)
                    print(f"   [OK] Puzzle #{pid} (rating: {puzzle['puzzle'].get('rating', '?')})")

            # Rate limit: ~1 request per second
            time.sleep(1.0)

        # 3. If we still don't have enough, try known IDs we haven't used
        if len(puzzles) < count:
            unused_known = [
                kid for kid in self.cache.get("known_ids", [])
                if kid not in self.cache["processed_puzzles"] and kid not in tried_ids
            ]
            random.shuffle(unused_known)

            for kid in unused_known[:count - len(puzzles)]:
                puzzle = self.fetch_puzzle_by_id(kid)
                if puzzle and puzzle.get('puzzle', {}).get('id'):
                    puzzles.append(puzzle)
                    print(f"   [OK] Known puzzle #{kid} (rating: {puzzle['puzzle'].get('rating', '?')})")
                time.sleep(1.0)

        print(f"   [RESULT] Fetched {len(puzzles)}/{count} puzzles")
        self._save_cache()
        return puzzles[:count]

    def puzzle_to_game(self, puzzle_data: dict) -> Optional[chess.pgn.Game]:
        """
        Convert a Lichess puzzle API response into a chess.pgn.Game object
        compatible with the existing video generation pipeline.

        The puzzle data contains:
        - game.pgn: full game PGN (space-separated moves like "d4 Nf6 c4 e6")
        - puzzle.initialPly: ply where the puzzle starts
        - puzzle.solution: list of UCI moves (the correct sequence)
        """
        try:
            game_data = puzzle_data.get('game', {})
            puzzle_info = puzzle_data.get('puzzle', {})

            pgn_moves = game_data.get('pgn', '')
            initial_ply = puzzle_info.get('initialPly', 0)
            solution = puzzle_info.get('solution', [])

            if not pgn_moves or not solution:
                return None

            # Parse the full game PGN to reach the puzzle position.
            # Lichess puzzle PGN is space-separated SAN moves.
            # Play ALL PGN moves — the PGN ends right at the puzzle start position.
            # The solution then starts with the opponent's trigger move.
            board = chess.Board()
            moves_list = pgn_moves.split()

            for san_move in moves_list:
                try:
                    move = board.parse_san(san_move)
                    board.push(move)
                except (chess.IllegalMoveError, chess.InvalidMoveError, chess.AmbiguousMoveError):
                    return None

            # Create a new game starting from the puzzle position
            puzzle_game = chess.pgn.Game()
            puzzle_game.setup(board)

            # Set headers
            players = game_data.get('players', [])
            white_name = 'White'
            black_name = 'Black'
            for p in players:
                if isinstance(p, dict):
                    if p.get('color') == 'white':
                        white_name = p.get('name', p.get('user', {}).get('name', 'White'))
                    elif p.get('color') == 'black':
                        black_name = p.get('name', p.get('user', {}).get('name', 'Black'))

            puzzle_game.headers["Event"] = f"Puzzle #{puzzle_info.get('id', 'unknown')}"
            puzzle_game.headers["Site"] = f"lichess.org/training/{puzzle_info.get('id', '')}"
            puzzle_game.headers["White"] = white_name
            puzzle_game.headers["Black"] = black_name
            puzzle_game.headers["Result"] = "*"
            puzzle_game.headers["PuzzleRating"] = str(puzzle_info.get('rating', 0))
            puzzle_game.headers["PuzzleThemes"] = " ".join(puzzle_info.get('themes', []))

            # Add the solution moves to the game
            node = puzzle_game
            temp_board = board.copy()
            for uci_str in solution:
                try:
                    move = chess.Move.from_uci(uci_str)
                    if move not in temp_board.legal_moves:
                        # Try with promotion
                        move = chess.Move.from_uci(uci_str + 'q')
                        if move not in temp_board.legal_moves:
                            break
                    node = node.add_variation(move)
                    temp_board.push(move)
                except (ValueError, chess.IllegalMoveError):
                    break

            # Attach puzzle metadata for pipeline detection
            puzzle_game.puzzle_data = {
                'id': puzzle_info.get('id', 'unknown'),
                'rating': puzzle_info.get('rating', 0),
                'themes': puzzle_info.get('themes', []),
                'solution': solution,
                'plays': puzzle_info.get('plays', 0),
                'initial_ply': initial_ply,
            }

            return puzzle_game

        except Exception as e:
            print(f"[WARN] Error converting puzzle to game: {e}")
            return None

    def fetch_and_convert(self, count: int = 1) -> List[chess.pgn.Game]:
        """
        Fetch puzzles and convert them to Game objects ready for the pipeline.
        Returns a list of chess.pgn.Game objects with puzzle_data attached.
        """
        puzzles = self.fetch_random_puzzles(count=count)
        games = []

        for puzzle_data in puzzles:
            game = self.puzzle_to_game(puzzle_data)
            if game:
                pid = puzzle_data['puzzle']['id']
                self._mark_processed(pid)
                games.append(game)

        print(f"[OK] Converted {len(games)}/{len(puzzles)} puzzles to game format")
        return games


if __name__ == "__main__":
    print("=" * 70)
    print("CHESS PUZZLE FETCHER - Lichess Edition")
    print("=" * 70)

    fetcher = PuzzleFetcher()

    # Test: fetch and convert 3 puzzles
    games = fetcher.fetch_and_convert(count=3)

    for game in games:
        pd = game.puzzle_data
        print(f"\nPuzzle #{pd['id']}:")
        print(f"  Rating: {pd['rating']}")
        print(f"  Themes: {', '.join(pd['themes'])}")
        print(f"  Solution: {' '.join(pd['solution'])}")
        print(f"  Moves in game: {len(list(game.mainline_moves()))}")

    print(f"\n{'=' * 70}")
    print(f"[OK] Done: {len(games)} puzzles ready for pipeline")
    print(f"{'=' * 70}")
