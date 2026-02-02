#!/usr/bin/env python3
"""
Module to fetch chess games from multiple sources:
- Lichess API (recent games from top GMs)
- Lichess Masters Database (historical master games)
- Chess.com API (player games)
- Online PGN databases
"""

import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
import berserk
import requests
import chess.pgn
from io import StringIO
import time


class GameFetcher:
    def __init__(self, output_dir="./ouvertures", cache_file="./game_cache.json"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()

        # Initialize Lichess client (no token needed for public data)
        self.lichess = berserk.Client()

        # Top GMs to track on Lichess
        self.lichess_players = [
            "DrNykterstein",  # Magnus Carlsen
            "Hikaru",         # Hikaru Nakamura
            "FabianoCaruana", # Fabiano Caruana
            "DanielNaroditsky",
            "Firouzja2003",   # Alireza Firouzja
            "Polish_fighter3000",  # Jan-Krzysztof Duda
            "RebeccaHarris",  # Levy Rozman
            "GMHikaruOnTwitch",
            "penguingim1",    # Andrew Tang
            "chessbrahs",
            "veloce",         # Maxime Vachier-Lagrave
            "nihalsarin",     # Nihal Sarin
            "viditchess",     # Vidit Gujrathi
            "FairChess_on_YouTube", # Levon Aronian
        ]

        # Top Chess.com players
        self.chesscom_players = [
            "magnuscarlsen",
            "hikaru",
            "fabianocaruana",
            "gothamchess",
            "danielnaroditsky",
            "gmbenjaminfinegold",
            "viditchess",
            "nihal_sarin",
            "lachesisq",
            "chessbrahs",
        ]

        # PGN database sources
        self.pgn_sources = [
            {
                "name": "Lichess Elite Database",
                "url": "https://database.lichess.org/",
                "type": "lichess_elite"
            }
        ]

    def _load_cache(self):
        """Load cache of already processed games"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {"processed_games": []}

    def _save_cache(self):
        """Save cache to disk"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def fetch_lichess_masters_games(self, count=10, min_rating=2400):
        """
        Fetch games from Lichess Masters Database
        This contains millions of high-quality master games
        """
        try:
            print(f"🏆 Fetching {count} master games from Lichess...")

            # Use Lichess API to get games from masters database
            # We'll use the TV games endpoint and explore recent master games
            games = []

            # Method 1: Get recent games from top players
            for player in random.sample(self.lichess_players, min(5, len(self.lichess_players))):
                try:
                    player_games = self.fetch_lichess_game(player, max_games=2)
                    games.extend(player_games)
                    if len(games) >= count:
                        break
                except Exception as e:
                    print(f"   ⚠️  Error fetching from {player}: {e}")
                    continue

            print(f"   ✅ Fetched {len(games)} games from Lichess")
            return games[:count]

        except Exception as e:
            print(f"   ❌ Error fetching Lichess masters games: {e}")
            return []

    def fetch_chesscom_games(self, count=5):
        """
        Fetch recent games from Chess.com API
        """
        try:
            print(f"♟️  Fetching {count} games from Chess.com...")
            games = []

            for player in random.sample(self.chesscom_players, min(3, len(self.chesscom_players))):
                try:
                    # Get player's archives
                    archives_url = f"https://api.chess.com/pub/player/{player}/games/archives"
                    response = requests.get(archives_url, timeout=10)

                    if response.status_code != 200:
                        continue

                    archives = response.json().get('archives', [])
                    if not archives:
                        continue

                    # Get games from most recent month
                    recent_archive = archives[-1]
                    games_response = requests.get(recent_archive, timeout=10)

                    if games_response.status_code != 200:
                        continue

                    month_games = games_response.json().get('games', [])

                    # Convert Chess.com games to PGN
                    for game_data in month_games[:5]:
                        if 'pgn' in game_data:
                            try:
                                game = chess.pgn.read_game(StringIO(game_data['pgn']))
                                if game and self._is_interesting_game(game):
                                    games.append(game)
                                    if len(games) >= count:
                                        break
                            except:
                                continue

                    if len(games) >= count:
                        break

                    time.sleep(0.5)  # Rate limiting

                except Exception as e:
                    print(f"   ⚠️  Error fetching from Chess.com player {player}: {e}")
                    continue

            print(f"   ✅ Fetched {len(games)} games from Chess.com")
            return games[:count]

        except Exception as e:
            print(f"   ❌ Error fetching Chess.com games: {e}")
            return []

    def fetch_random_master_game(self):
        """
        Fetch a random high-quality master game from various sources
        """
        sources = [
            ('lichess', lambda: self.fetch_lichess_masters_games(count=1)),
            ('chesscom', lambda: self.fetch_chesscom_games(count=1)),
        ]

        # Randomly select a source
        source_name, fetch_func = random.choice(sources)

        try:
            games = fetch_func()
            if games:
                return games[0]
        except Exception as e:
            print(f"   ⚠️  Error fetching from {source_name}: {e}")

        return None

    def fetch_lichess_game(self, username, max_games=5, opening_filter=None):
        """Fetch recent games from a specific player, optionally filtered by opening"""
        try:
            if opening_filter:
                print(f"Fetching {opening_filter} games for {username}...")
            else:
                print(f"Fetching games for {username}...")
            # Use requests to get PGN directly from Lichess API
            url = f"https://lichess.org/api/games/user/{username}"
            params = {
                'max': max_games * 3 if opening_filter else max_games,  # Get more if filtering
                'rated': 'true',
                'perfType': 'blitz,rapid,classical',
                'moves': 'true',
                'tags': 'true',
                'opening': 'true',
                'pgnInJson': 'false'  # Get PGN format
            }
            headers = {'Accept': 'application/x-chess-pgn'}

            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"   ⚠️  HTTP {response.status_code} for {username}")
                return []

            # Split PGN string into individual games
            pgn_text = response.text
            fetched_games = []

            # Read games from PGN text
            pgn_io = StringIO(pgn_text)
            while True:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break

                # Apply opening filter if specified
                if opening_filter:
                    opening = game.headers.get('Opening', '')
                    eco = game.headers.get('ECO', '')
                    # Check if opening name or ECO code matches
                    if not (opening_filter.lower() in opening.lower() or
                            opening_filter.upper() in eco):
                        continue

                if self._is_interesting_game(game):
                    fetched_games.append(game)
                    if len(fetched_games) >= max_games:
                        break

            if opening_filter:
                print(f"   ✅ Found {len(fetched_games)} {opening_filter} games from {username}")
            else:
                print(f"   ✅ Found {len(fetched_games)} interesting games from {username}")
            return fetched_games

        except Exception as e:
            print(f"   ⚠️  Error fetching games for {username}: {e}")
            return []

    def _is_interesting_game(self, game):
        """Determine if a game is interesting enough for content"""
        # Skip if already processed
        game_id = game.headers.get("Site", "").split("/")[-1]
        if game_id in self.cache["processed_games"]:
            return False

        # Must have minimum moves (more permissive)
        moves = list(game.mainline_moves())
        if len(moves) < 15 or len(moves) > 100:
            return False

        # Accept most games, including draws
        result = game.headers.get("Result", "*")
        if result == "1/2-1/2":
            return random.random() < 0.7  # 70% chance for draws

        return True


    def save_game_to_pgn(self, game, filename=None):
        """Save game to PGN file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_{timestamp}.pgn"

        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            exporter = chess.pgn.FileExporter(f)
            game.accept(exporter)

        # Mark as processed
        game_id = game.headers.get("Site", filename).split("/")[-1]
        if game_id not in self.cache["processed_games"]:
            self.cache["processed_games"].append(game_id)
            self._save_cache()

        print(f"Saved game to {filepath}")
        return filepath

    def fetch_batch_games(self, count=10, mix_ratio=None, opening_filter=None):
        """
        Fetch a batch of games from multiple sources

        Args:
            count: Number of games to fetch
            mix_ratio: Can be either:
                - float (0.0-1.0): proportion of Lichess vs other sources (backward compatible)
                - dict: source weights {'lichess': 0.4, 'chesscom': 0.4, 'masters': 0.2}
                - None: uses default distribution
            opening_filter: Filter games by opening name or ECO code (e.g., "Sicilian", "B20")
        """
        source_distribution = None

        # Handle both old (float) and new (dict) formats
        if mix_ratio is not None:
            if isinstance(mix_ratio, dict):
                # New format: direct source distribution
                source_distribution = mix_ratio
            elif isinstance(mix_ratio, (int, float)):
                # Old format: backward compatibility
                source_distribution = {
                    'lichess': mix_ratio,
                    'chesscom': (1 - mix_ratio) * 0.6,
                    'masters': (1 - mix_ratio) * 0.4,
                }

        if source_distribution is None:
            source_distribution = {
                'lichess': 0.5,      # 50% from Lichess player games
                'chesscom': 0.3,     # 30% from Chess.com
                'masters': 0.2,      # 20% from masters database
            }

        games = []

        # Calculate counts per source
        lichess_count = int(count * source_distribution.get('lichess', 0))
        chesscom_count = int(count * source_distribution.get('chesscom', 0))
        masters_count = count - lichess_count - chesscom_count

        if opening_filter:
            print(f"\n📊 Fetching {count} games with opening: {opening_filter}")
        else:
            print(f"\n📊 Fetching {count} games:")
        print(f"   • {lichess_count} from Lichess players")
        print(f"   • {chesscom_count} from Chess.com")
        print(f"   • {masters_count} from Masters database\n")

        # Fetch from Lichess
        if lichess_count > 0:
            players_to_check = random.sample(
                self.lichess_players,
                min(max(3, lichess_count // 2), len(self.lichess_players))
            )
            for player in players_to_check:
                try:
                    player_games = self.fetch_lichess_game(
                        player,
                        max_games=3,
                        opening_filter=opening_filter
                    )
                    for i, g in enumerate(player_games):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        opening_name = g.headers.get('Opening', 'Unknown').replace(' ', '_')[:30]
                        name = f"lichess_{player}_{opening_name}_{timestamp}_{i}"
                        games.append((g, name))
                    if len(games) >= lichess_count:
                        break
                except Exception as e:
                    print(f"   ⚠️  Error with {player}: {e}")
                    continue

        # Fetch from Chess.com
        if chesscom_count > 0:
            try:
                chesscom_games = self.fetch_chesscom_games(count=chesscom_count)
                for i, game in enumerate(chesscom_games):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    white = game.headers.get('White', 'Unknown').replace(' ', '_')
                    black = game.headers.get('Black', 'Unknown').replace(' ', '_')
                    name = f"chesscom_{white}_vs_{black}_{timestamp}"
                    games.append((game, name))
            except Exception as e:
                print(f"   ⚠️  Error fetching Chess.com: {e}")

        # Fetch from Masters database
        if masters_count > 0:
            try:
                master_games = self.fetch_lichess_masters_games(count=masters_count)
                for i, game in enumerate(master_games):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    white = game.headers.get('White', 'Master').replace(' ', '_')
                    black = game.headers.get('Black', 'Master').replace(' ', '_')
                    name = f"masters_{white}_vs_{black}_{timestamp}"
                    games.append((game, name))
            except Exception as e:
                print(f"   ⚠️  Error fetching Masters: {e}")

        # Save all games
        print(f"\n💾 Saving {len(games)} games to disk...")
        saved_files = []
        for game, name in games[:count]:
            try:
                filepath = self.save_game_to_pgn(game, f"{name}.pgn")
                saved_files.append(filepath)
            except Exception as e:
                print(f"   ⚠️  Error saving {name}: {e}")
                continue

        print(f"✅ Successfully saved {len(saved_files)} games\n")
        return saved_files


if __name__ == "__main__":
    fetcher = GameFetcher()
    print("=" * 70)
    print("CHESS GAME FETCHER - Multi-Source Edition")
    print("=" * 70)

    # Test fetching from multiple sources
    files = fetcher.fetch_batch_games(
        count=10,
        source_distribution={
            'lichess': 0.5,
            'chesscom': 0.3,
            'masters': 0.2
        }
    )

    print(f"\n{'=' * 70}")
    print(f"✅ COMPLETE: Fetched {len(files)} games from multiple sources")
    print(f"{'=' * 70}")
    print("\nSaved games:")
    for f in files:
        print(f"  📄 {f.name}")
