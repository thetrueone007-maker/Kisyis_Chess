#!/usr/bin/env python3
"""
Main automation pipeline for chess video generation
Orchestrates all components for end-to-end video creation
"""

import sys
import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime
import subprocess
from typing import Optional, List
import chess
import chess.pgn
from io import StringIO
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import QPointF

# Import our modules
from game_fetcher import GameFetcher
from enhanced_renderer import EnhancedRenderer, MoveHighlight, TextComment
from comment_generator import CommentGenerator, CommentScheduler
from audio_manager import AudioManager
from tiktok_manager import TikTokVideoPrep
from piece_sound_generator import PieceSoundGenerator
from tiktok_auto_uploader import TikTokAutoUploader
try:
    from stockfish_analyzer import StockfishAnalyzer
    STOCKFISH_AVAILABLE = True
except:
    STOCKFISH_AVAILABLE = False
    print("⚠️  Stockfish not available - evaluation features disabled")


class ChessTikTokPipeline:
    """Complete pipeline for automated chess video generation"""

    def __init__(self, config: dict = None):
        """
        Initialize pipeline

        Args:
            config: Configuration dictionary
        """
        self.config = config or self._default_config()
        self._initialize_components()

    def load_opening_from_json(self, json_file: str) -> chess.pgn.Game:
        """Load an opening from a JSON definition file"""
        opening_path = Path('openings') / json_file

        if not opening_path.exists():
            raise FileNotFoundError(f"Opening file not found: {opening_path}")

        with open(opening_path, 'r', encoding='utf-8') as f:
            opening_data = json.load(f)

        # Create a new game
        game = chess.pgn.Game()

        # Set headers
        game.headers["Event"] = opening_data['title']
        game.headers["Site"] = "Chess Opening Database"
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        game.headers["White"] = "Theory" if opening_data['side'] == 'white' else "Opponent"
        game.headers["Black"] = "Theory" if opening_data['side'] == 'black' else "Opponent"
        game.headers["Result"] = "*"
        game.headers["ECO"] = opening_data.get('eco_code', '')
        game.headers["Opening"] = opening_data['title']

        # Add moves
        node = game
        board = chess.Board()

        for move_san in opening_data['moves']:
            try:
                move = board.parse_san(move_san)
                node = node.add_variation(move)
                board.push(move)
            except Exception as e:
                print(f"⚠️  Error parsing move '{move_san}': {e}")
                break

        # Store opening metadata for later use
        game.opening_data = opening_data

        return game

    def _initialize_components(self):
        """Initialize pipeline components"""
        # Initialize components
        self.game_fetcher = GameFetcher(
            output_dir=self.config['pgn_dir'],
            cache_file=self.config['game_cache']
        )

        self.comment_generator = CommentGenerator(
            api_key=self.config.get('anthropic_api_key')
        )

        self.audio_manager = AudioManager(
            music_dir=self.config['music_dir'],
            sfx_dir=self.config['sfx_dir']
        )

        self.piece_sound_gen = PieceSoundGenerator(
            sfx_dir=self.config['sfx_dir']
        )

        self.tiktok_prep = TikTokVideoPrep(
            output_dir=self.config['tiktok_dir']
        )

        # Create output directories
        for dir_key in ['pgn_dir', 'renders_dir', 'temp_dir', 'tiktok_dir',
                        'tiktok_opening_dir', 'assets_opening_dir']:
            Path(self.config[dir_key]).mkdir(parents=True, exist_ok=True)

    def _default_config(self) -> dict:
        """Default configuration"""
        return {
            'pgn_dir': './ouvertures',
            'assets_dir': './assets',
            'assets_opening_dir': './assets_opening',  # Assets for opening mode
            'renders_dir': './renders',
            'temp_dir': './temp',
            'tiktok_dir': './tiktok_ready',
            'tiktok_opening_dir': './tiktok_opening',  # Separate folder for opening videos
            'music_dir': './audio/music',
            'sfx_dir': './audio/sfx',
            'game_cache': './game_cache.json',
            'anthropic_api_key': None,  # Set via env var
            'stockfish_path': str(Path(__file__).parent / 'stockfish'),  # Use local Stockfish

            # Rendering settings
            'width': 1440,
            'height': 2560,
            'fps': 120,
            'move_seconds': 1,  # 30% slower than before (0.7 * 1.30)

            # Feature flags
            'enable_eval_bar': STOCKFISH_AVAILABLE,
            'enable_highlights': True,
            'enable_comments': True,
            'enable_audio': True,
            'enable_auto_upload': False,  # Auto-upload to TikTok
            'enable_opening_mode': False,  # Opening theory mode (no move annotations)

            # Analysis settings
            'stockfish_depth': 20,  # Increased for better analysis
            'stockfish_time': 0.15,  # Slightly more time per position
        }

    def generate_video(self, game: chess.pgn.Game, game_name: str) -> Optional[Path]:
        """
        Generate complete video for a single game

        Args:
            game: Chess game to render
            game_name: Identifier for the game

        Returns:
            Path to final TikTok-ready video
        """
        print(f"\n{'='*70}")
        print(f"Generating video: {game_name}")
        print(f"{'='*70}")

        # Step 1: Analyze game with Stockfish
        analyses = None
        if self.config['enable_eval_bar'] and STOCKFISH_AVAILABLE:
            print("\n[1/8] Analyzing game with Stockfish...")
            try:
                with StockfishAnalyzer(
                    stockfish_path=self.config['stockfish_path'],
                    depth=self.config['stockfish_depth'],
                    time_limit=self.config['stockfish_time']
                ) as analyzer:
                    analyses = analyzer.analyze_game(game)
                    print(f"   ✅ Analyzed {len(analyses)} moves")

                    # Show statistics
                    brilliant = sum(1 for a in analyses if a.is_brilliant)
                    blunders = sum(1 for a in analyses if a.is_blunder)
                    print(f"   🌟 {brilliant} brilliant moves")
                    print(f"   ⚠️  {blunders} blunders")
            except Exception as e:
                print(f"   ⚠️  Stockfish analysis failed: {e}")
                analyses = None

        # Step 2: Generate comments
        print("\n[2/8] Generating AI commentary...")
        comment_timeline = {}
        if self.config['enable_comments']:
            try:
                if analyses:
                    scheduler = CommentScheduler(
                        analyses,
                        fps=self.config['fps'],
                        move_duration_seconds=self.config['move_seconds']
                    )
                    comment_timeline = scheduler.get_comments_timeline(
                        self.comment_generator,
                        game
                    )
                    print(f"   ✅ Generated {len(comment_timeline)} comments")
                else:
                    # Basic comments without analysis
                    comment_timeline[0] = self.comment_generator.generate_opening_comment(game)
                    print(f"   ✅ Generated opening comment")
            except Exception as e:
                print(f"   ⚠️  Comment generation failed: {e}")

        # Step 3: Render video
        print("\n[3/8] Rendering video...")
        video_path = Path(self.config['temp_dir']) / f"{game_name}_raw.mp4"

        app = QApplication.instance() or QApplication([])

        # Use opening assets if in opening mode and they exist
        assets_dir = self.config['assets_dir']
        if self.config.get('enable_opening_mode', False):
            opening_assets = Path(self.config['assets_opening_dir'])
            # Check if opening assets exist (at least one piece)
            if (opening_assets / 'wK.png').exists():
                assets_dir = self.config['assets_opening_dir']
                print("   🎨 Using opening mode assets")

        # Check if board should be flipped for black's perspective
        flip_board = False
        if hasattr(game, 'opening_data') and game.opening_data.get('side') == 'black':
            flip_board = True
            print("   🔄 Flipping board for black's perspective")

        renderer = EnhancedRenderer(
            assets_dir=assets_dir,
            width=self.config['width'],
            height=self.config['height'],
            fps=self.config['fps'],
            out_dir=self.config['renders_dir'],
            move_seconds=self.config['move_seconds'],
            show_eval_bar=self.config['enable_eval_bar'] and analyses is not None,
            show_highlights=self.config['enable_highlights'],
            show_comments=self.config['enable_comments'],
            opening_mode=self.config['enable_opening_mode'],
            flip_board=flip_board
        )

        try:
            self._render_enhanced_game(
                renderer,
                game,
                analyses,
                comment_timeline,
                video_path
            )
            print(f"   ✅ Rendered: {video_path}")
        except Exception as e:
            print(f"   ❌ Rendering failed: {e}")
            return None

        # Step 4: Add piece sounds
        print("\n[4/8] Adding piece sounds...")
        piece_sound_path = Path(self.config['temp_dir']) / f"{game_name}_sounds.mp4"
        piece_sounds_added = self.piece_sound_gen.add_piece_sounds_to_video(
            video_path,
            piece_sound_path,
            game,
            fps=self.config['fps'],
            move_seconds=self.config['move_seconds']
        )

        if piece_sounds_added:
            final_video = piece_sound_path
            print(f"   ✅ Piece sounds added")
        else:
            final_video = video_path
            print(f"   ⚠️  Using video without piece sounds")

        # Step 5: Add background music
        if self.config['enable_audio']:
            print("\n[5/8] Adding background music...")
            audio_path = Path(self.config['temp_dir']) / f"{game_name}_audio.mp4"
            success = self.audio_manager.add_audio_to_video(
                final_video,
                audio_path,
                music_volume=0.25
            )
            if success:
                final_video = audio_path
                print(f"   ✅ Background music added")
            else:
                print(f"   ⚠️  Skipping background music (no music files found)")
        else:
            print("\n[5/8] Skipping background music (disabled)")

        # Step 6: Optimize for TikTok
        print("\n[6/8] Optimizing for TikTok...")

        # Use separate folder for opening mode videos
        original_output_dir = self.tiktok_prep.output_dir
        if self.config.get('enable_opening_mode', False):
            self.tiktok_prep.output_dir = Path(self.config['tiktok_opening_dir'])
            print("   📁 Saving to opening mode folder")

        tiktok_video = self.tiktok_prep.optimize_for_tiktok(
            final_video,
            f"{game_name}.mp4"
        )

        # Restore original output dir
        self.tiktok_prep.output_dir = original_output_dir

        if not tiktok_video:
            print(f"   ❌ Optimization failed")
            return None

        # Step 7: Prepare metadata
        print("\n[7/8] Preparing upload metadata...")
        white = game.headers.get('White', 'Player')
        black = game.headers.get('Black', 'Player')
        event = game.headers.get('Event', 'Chess Game')

        title = f"♟️ {white} vs {black}"
        hashtags = self.comment_generator.generate_hashtags(game)
        description = f"{event} - {game.headers.get('Result', '*')}"

        self.tiktok_prep.add_to_upload_queue(
            tiktok_video,
            title,
            hashtags,
            description
        )

        # Step 8: Auto-upload to TikTok (if enabled)
        if self.config['enable_auto_upload']:
            print("\n[8/8] Uploading to TikTok...")
            try:
                # Reuse uploader instance if already exists
                if not hasattr(self, '_tiktok_uploader'):
                    self._tiktok_uploader = TikTokAutoUploader(headless=False, debug=True)

                    # Check if already logged in, otherwise prompt for login
                    print("🔑 Première connexion à TikTok requise...")
                    if not self._tiktok_uploader.login_with_google():
                        print("⚠️  Échec de la connexion TikTok, vidéo sauvegardée localement")
                        self._tiktok_uploader.close()
                        delattr(self, '_tiktok_uploader')
                        return tiktok_video

                # Upload video (reusing existing browser session)
                success = self._tiktok_uploader.upload_video(
                    video_path=tiktok_video,
                    title=title,
                    hashtags=hashtags,
                    description=description,
                    use_recommended_music=True,
                    publish=True
                )

                if success:
                    print("✅ Vidéo uploadée sur TikTok avec succès!")
                else:
                    print("⚠️  Upload TikTok échoué, vidéo sauvegardée localement")

            except Exception as e:
                print(f"⚠️  Erreur lors de l'upload TikTok: {e}")
                print("   Vidéo sauvegardée localement")
                # Clean up uploader on error
                if hasattr(self, '_tiktok_uploader'):
                    try:
                        self._tiktok_uploader.close()
                    except:
                        pass
                    delattr(self, '_tiktok_uploader')
        else:
            print("\n[8/8] Auto-upload TikTok désactivé")

        print(f"\n{'='*70}")
        print(f"✅ VIDEO COMPLETE: {tiktok_video}")
        print(f"{'='*70}\n")

        return tiktok_video

    def _render_enhanced_game(self, renderer, game, analyses, comment_timeline, output_path):
        """Render game with all enhancements"""

        header_title = game.headers.get('Event') or game.headers.get('Title') or output_path.stem
        moves = list(game.mainline_moves())

        # Setup ffmpeg pipe
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgba',
            '-s', f'{renderer.width}x{renderer.height}',
            '-r', str(renderer.fps),
            '-i', '-',
            '-an',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '18',
            '-preset', 'slow',
            str(output_path)
        ]

        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        # Title sequence
        frames_big = max(1, int(1.0 * renderer.fps))
        frames_shrink = max(1, int(0.6 * renderer.fps))

        for i in range(frames_big + frames_shrink):
            if i < frames_big:
                t = i / max(1, frames_big - 1)
                phase, title_t = 'big', t
            else:
                t = (i - frames_big) / max(1, frames_shrink - 1)
                phase, title_t = 'shrinking', t

            positions = renderer.compose_piece_positions(chess.Board())
            comment = comment_timeline.get(i, "")
            qimg = renderer.render_enhanced_frame(
                chess.Board(),
                positions,
                header_title,
                phase,
                title_t,
                eval_cp=0,
                comment=comment
            )
            proc.stdin.write(qimg.bits().tobytes())

        # Moves
        board = game.board()
        frames_per_move = max(1, int(renderer.move_seconds * renderer.fps))
        current_frame = frames_big + frames_shrink

        for move_idx, move in enumerate(moves):
            analysis = analyses[move_idx] if analyses else None

            from_sq = move.from_square
            to_sq = move.to_square
            moving_piece = board.piece_at(from_sq)
            is_capture = board.is_capture(move)

            capture_sq = None
            if is_capture:
                capture_sq = to_sq
                if board.is_en_passant(move):
                    capture_sq = to_sq - 8 if moving_piece.color == chess.WHITE else to_sq + 8

            # Determine highlight color
            highlights = []
            if renderer.show_highlights and analysis:
                if analysis.is_brilliant:
                    color = renderer.highlight_colors['brilliant']
                elif analysis.is_blunder:
                    color = renderer.highlight_colors['blunder']
                elif analysis.is_critical:
                    color = renderer.highlight_colors['critical']
                else:
                    color = renderer.highlight_colors['default']

                highlights = [MoveHighlight(from_sq, to_sq, color)]

            # Render move frames
            for f in range(frames_per_move):
                p = f / max(1, frames_per_move - 1)
                cap_op = 1.0
                if is_capture and p > 0.4:
                    cap_op = max(0.0, 1.0 - (p - 0.4) / 0.6)

                positions = renderer.compose_piece_positions(
                    board,
                    moving_piece=moving_piece,
                    from_sq=from_sq,
                    to_sq=to_sq,
                    progress=p,
                    capture_sq=capture_sq,
                    capture_fade=cap_op
                )

                eval_cp = analysis.eval_after if analysis else 0
                comment = comment_timeline.get(current_frame + f, "")

                # Show annotation badge during the second half of the move animation
                show_annotation = f > frames_per_move // 2

                qimg = renderer.render_enhanced_frame(
                    board,
                    positions,
                    header_title,
                    'small',
                    1.0,
                    eval_cp=eval_cp,
                    highlights=highlights if f > frames_per_move // 3 else None,
                    comment=comment,
                    move_annotation=analysis if (show_annotation and analysis) else None
                )
                proc.stdin.write(qimg.bits().tobytes())

            board.push(move)
            current_frame += frames_per_move

        # End pause
        pause_frames = max(1, int(1.5 * renderer.fps))
        for i in range(pause_frames):
            positions = renderer.compose_piece_positions(board)
            eval_cp = analyses[-1].eval_after if analyses else 0
            comment = comment_timeline.get(current_frame + i, "")
            qimg = renderer.render_enhanced_frame(
                board,
                positions,
                header_title,
                'small',
                1.0,
                eval_cp=eval_cp,
                comment=comment
            )
            proc.stdin.write(qimg.bits().tobytes())

        proc.stdin.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"ffmpeg exited with code {ret}")

    def generate_batch(self, count: int = 10, mix_ratio: float = 0.5, opening_filter: str = None):
        """
        Generate a batch of videos

        Args:
            count: Number of videos to generate
            mix_ratio: Ratio of Lichess vs classic games
            opening_filter: Filter games by opening (e.g., "Sicilian", "French", "B20")
        """
        print(f"\n🚀 Starting batch generation: {count} videos")
        if opening_filter:
            print(f"   🎯 Opening filter: {opening_filter}")
        print(f"   Mix: {int(mix_ratio*100)}% Lichess / {int((1-mix_ratio)*100)}% Classic")

        # Calculate upload delay if auto-upload is enabled
        upload_delay_seconds = 0
        if self.config.get('enable_auto_upload', False) and count > 1:
            # Spread uploads over 24 hours
            upload_delay_seconds = (24 * 3600) / count
            hours = int(upload_delay_seconds // 3600)
            minutes = int((upload_delay_seconds % 3600) // 60)
            print(f"   📤 Auto-upload enabled: posts every {hours}h{minutes:02d}min")

        # Check if using JSON opening definition
        if opening_filter and opening_filter.endswith('.json'):
            # Generate from JSON opening definition (always 1 video per JSON)
            print(f"\n📚 Loading opening from JSON: {opening_filter}")
            games_to_process = []

            try:
                game = self.load_opening_from_json(opening_filter)
                game_name = Path(opening_filter).stem
                games_to_process.append((game, game_name, opening_filter))  # Add filename for archiving
            except Exception as e:
                print(f"   ❌ Error loading opening: {e}")
                return

            print(f"✅ Loaded opening theory: 1 video\n")
        else:
            # Fetch games online
            print("\n📥 Fetching games...")
            pgn_files = self.game_fetcher.fetch_batch_games(count, mix_ratio, opening_filter)
            print(f"✅ Fetched {len(pgn_files)} games\n")

            games_to_process = []
            for pgn_file in pgn_files:
                with open(pgn_file) as f:
                    game = chess.pgn.read_game(f)
                if game:
                    games_to_process.append((game, pgn_file.stem, None))  # None = no archiving needed

        # Generate videos
        success_count = 0
        for i, (game, game_name, json_file) in enumerate(games_to_process, 1):
            print(f"\n[{i}/{len(games_to_process)}] Processing: {game_name}")

            if not game:
                print(f"   ❌ Could not read game")
                continue

            video_path = self.generate_video(game, game_name)
            if video_path:
                success_count += 1

                # Archive JSON file if it's from opening mode
                if json_file:
                    try:
                        source = Path('openings') / json_file
                        dest = Path('openings/archive') / json_file
                        shutil.move(str(source), str(dest))
                        print(f"   📦 Archived: {json_file} → archive/")
                    except Exception as e:
                        print(f"   ⚠️  Could not archive {json_file}: {e}")

                # Wait between uploads if auto-upload is enabled and not the last video
                if self.config.get('enable_auto_upload', False) and i < len(games_to_process):
                    from datetime import datetime, timedelta
                    import time
                    import random

                    # Add random variation (±25%) to delay to avoid bot detection
                    variation = random.uniform(0.75, 1.25)
                    actual_delay = upload_delay_seconds * variation

                    next_upload_time = datetime.now() + timedelta(seconds=actual_delay)
                    print(f"\n⏰ Waiting until {next_upload_time.strftime('%H:%M:%S')} for next upload...")
                    print(f"   ({int(actual_delay//3600)}h {int((actual_delay%3600)//60)}min delay - randomized)")

                    # Sleep with progress updates
                    sleep_interval = 60  # Update every minute
                    elapsed = 0
                    while elapsed < actual_delay:
                        time.sleep(min(sleep_interval, actual_delay - elapsed))
                        elapsed += sleep_interval
                        remaining = actual_delay - elapsed
                        if remaining > 0:
                            print(f"   ⏳ {int(remaining//60)} minutes remaining until next upload...")

        # Clean up TikTok uploader if it was used
        if hasattr(self, '_tiktok_uploader'):
            print("\n🔒 Closing browser...")
            try:
                self._tiktok_uploader.close()
            except:
                pass
            delattr(self, '_tiktok_uploader')

        print(f"\n{'='*70}")
        print(f"🎉 BATCH COMPLETE: {success_count}/{len(games_to_process)} videos generated")
        print(f"{'='*70}\n")

        # Show upload instructions
        if not self.config.get('enable_auto_upload', False):
            self.tiktok_prep.show_upload_instructions()


def main():
    parser = argparse.ArgumentParser(description="Automated Chess TikTok Video Generator")
    parser.add_argument('--count', type=int, default=1, help='Number of videos to generate')
    parser.add_argument('--mix-ratio', type=float, default=0.5, help='Lichess vs Classic ratio (0-1)')
    parser.add_argument('--no-eval', action='store_true', help='Disable evaluation bar')
    parser.add_argument('--no-audio', action='store_true', help='Disable background music')
    parser.add_argument('--auto-upload', action='store_true', help='Enable automatic TikTok upload')
    parser.add_argument('--opening-mode', type=str, nargs='?', const=True, default=None,
                        help='Opening theory mode: specify JSON file (e.g., "sicilian_defense.json")')
    parser.add_argument('--all-openings', action='store_true', help='Generate one video for each JSON in openings/ folder')
    parser.add_argument('--config', type=str, help='Path to config JSON file')

    args = parser.parse_args()

    # Load configuration
    config = None
    if args.config:
        import json
        with open(args.config) as f:
            config = json.load(f)

    pipeline = ChessTikTokPipeline(config)

    # Apply command-line overrides
    if args.no_eval:
        pipeline.config['enable_eval_bar'] = False
    if args.no_audio:
        pipeline.config['enable_audio'] = False
    if args.auto_upload:
        pipeline.config['enable_auto_upload'] = True

    # Handle opening mode
    opening_filter = None
    if args.all_openings:
        # Generate one video for each JSON in openings/
        pipeline.config['enable_opening_mode'] = True
        openings_dir = Path('openings')
        json_files = sorted(openings_dir.glob('*.json'))

        if not json_files:
            print("❌ No JSON files found in openings/")
            return

        print(f"\n🎯 ALL-OPENINGS MODE: {len(json_files)} openings found")
        print("=" * 70)

        for json_file in json_files:
            pipeline.generate_batch(
                count=1,
                mix_ratio=args.mix_ratio,
                opening_filter=json_file.name
            )
    elif args.opening_mode is not None:
        pipeline.config['enable_opening_mode'] = True
        # If opening_mode is a string (not True), use it as filter
        if isinstance(args.opening_mode, str):
            opening_filter = args.opening_mode

        # Generate videos
        pipeline.generate_batch(
            count=args.count,
            mix_ratio=args.mix_ratio,
            opening_filter=opening_filter
        )
    else:
        # Normal mode (fetch games online)
        pipeline.generate_batch(
            count=args.count,
            mix_ratio=args.mix_ratio,
            opening_filter=None
        )


if __name__ == "__main__":
    main()
