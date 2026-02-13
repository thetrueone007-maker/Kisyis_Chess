#!/usr/bin/env python3
"""
Kisyis Chess - Full Automation Script
Generates chess videos (GM games + puzzles) and posts them to TikTok 5x/day.

Usage:
    python run_automation.py              # Run full automation (5/day schedule)
    python run_automation.py --setup      # First-time interactive setup
    python run_automation.py --once       # Generate and upload 1 video now
    python run_automation.py --once --type puzzle  # Generate 1 puzzle video
    python run_automation.py --dry-run    # Generate but don't upload
"""

import os
import sys
import json
import shutil
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime


def setup_logging():
    """Configure logging for the automation"""
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"automation_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('ChessAutomation')


def preflight_check(logger):
    """
    Verify all dependencies and prerequisites are available.
    Returns True if critical deps are met, False otherwise.
    """
    logger.info("=" * 70)
    logger.info("[CHECK] PREFLIGHT CHECKS")
    logger.info("=" * 70)

    all_ok = True
    warnings = []

    # 1. Check FFmpeg
    try:
        from ffmpeg_path import FFMPEG_PATH
        if FFMPEG_PATH:
            logger.info(f"  [OK] FFmpeg: {FFMPEG_PATH}")
        else:
            logger.error("  [FAIL] FFmpeg not found")
            all_ok = False
    except Exception:
        logger.error("  [FAIL] FFmpeg not found - install with: brew install ffmpeg")
        all_ok = False

    # 2. Check Stockfish
    stockfish_path = Path("./stockfish")
    if stockfish_path.exists():
        logger.info(f"  [OK] Stockfish: {stockfish_path}")
        # Make sure it's executable
        if not os.access(stockfish_path, os.X_OK):
            os.chmod(stockfish_path, 0o755)
            logger.info("       Made stockfish executable")
    else:
        warnings.append("Stockfish binary not found - evaluation bar disabled")

    # 3. Check chess piece assets
    assets_dir = Path("./assets")
    required_pieces = ['wK.png', 'wQ.png', 'wR.png', 'wB.png', 'wN.png', 'wP.png',
                       'bK.png', 'bQ.png', 'bR.png', 'bB.png', 'bN.png', 'bP.png']
    missing_pieces = [p for p in required_pieces if not (assets_dir / p).exists()]
    if not missing_pieces:
        logger.info(f"  [OK] Chess assets: {assets_dir} (12 pieces)")
    else:
        logger.error(f"  [FAIL] Missing chess pieces: {missing_pieces}")
        all_ok = False

    # 4. Check Playwright
    try:
        from playwright.sync_api import sync_playwright
        logger.info("  [OK] Playwright installed")
    except ImportError:
        logger.error("  [FAIL] Playwright not installed - run: pip install playwright && playwright install chromium")
        all_ok = False

    # 5. Check TikTok session
    session_file = Path("./tiktok_session.json")
    if session_file.exists():
        logger.info(f"  [OK] TikTok session: {session_file}")
    else:
        warnings.append("TikTok session not found - run with --setup for first login")

    # 6. Check audio SFX
    sfx_dir = Path("./audio/sfx")
    if sfx_dir.exists() and any(sfx_dir.iterdir()):
        logger.info(f"  [OK] Audio SFX: {sfx_dir}")
    else:
        warnings.append("No audio SFX files found in ./audio/sfx/")

    # 7. Check required directories
    for d in ['./ouvertures', './renders', './tiktok_ready', './temp', './logs']:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("  [OK] Output directories created")

    # 8. Check Python modules
    try:
        import chess
        import chess.pgn
        import requests
        import berserk
        import schedule
        from PySide6.QtWidgets import QApplication
        logger.info("  [OK] Python dependencies OK")
    except ImportError as e:
        logger.error(f"  [FAIL] Missing Python module: {e}")
        all_ok = False

    # Show warnings
    for w in warnings:
        logger.warning(f"  [WARN] {w}")

    logger.info("=" * 70)
    if all_ok:
        logger.info("[OK] Preflight checks PASSED")
    else:
        logger.error("[FAIL] Preflight checks FAILED - fix errors above")
    logger.info("=" * 70 + "\n")

    return all_ok


def first_time_setup(logger):
    """Interactive first-time setup: TikTok login + test video"""
    logger.info("\n" + "=" * 70)
    logger.info("[SETUP] FIRST TIME SETUP")
    logger.info("=" * 70)

    if not preflight_check(logger):
        logger.error("Fix preflight errors before running setup")
        return False

    # Check if TikTok session exists
    session_file = Path("./tiktok_session.json")
    if session_file.exists():
        logger.info("[OK] TikTok session already exists")
        response = input("Re-do TikTok login? (y/N): ").strip().lower()
        if response != 'y':
            logger.info("Keeping existing session")
            return True

    # TikTok login
    logger.info("\n[KEY] Opening browser for TikTok login...")
    logger.info("    A browser window will open.")
    logger.info("    Please log in with your Google account.")
    logger.info("    The session will be saved for future use.\n")

    try:
        from tiktok_auto_uploader import TikTokAutoUploader
        uploader = TikTokAutoUploader(headless=False, debug=True)

        if uploader.login_with_google():
            logger.info("[OK] TikTok login successful!")
            uploader.close()
        else:
            logger.error("[FAIL] TikTok login failed")
            uploader.close()
            return False

    except Exception as e:
        logger.error(f"[FAIL] TikTok login error: {e}")
        return False

    # Create config.json if it doesn't exist
    config_file = Path("./config.json")
    if not config_file.exists():
        example_config = Path("./config.example.json")
        if example_config.exists():
            shutil.copy(example_config, config_file)
            logger.info("[OK] Created config.json from example")
        else:
            # Create minimal config
            config = {
                "enable_auto_upload": True,
                "enable_comments": False,
                "use_nvenc": False,
                "videos_per_day": 5,
                "enable_puzzles": True,
            }
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("[OK] Created minimal config.json")

    logger.info("\n[OK] Setup complete! You can now run: python run_automation.py")
    return True


def load_config():
    """Load config from file or return defaults"""
    config_file = Path("./config.json")
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)
    return None


def run_automation(args, logger):
    """Main automation loop"""
    if not preflight_check(logger):
        logger.error("Fix errors before running. Use --setup for first time setup.")
        sys.exit(1)

    config = load_config()

    # Apply CLI overrides
    if config is None:
        config = {}
    config['enable_auto_upload'] = not args.dry_run
    config['enable_comments'] = False  # Fixed hashtags only

    if args.dry_run:
        logger.info("[DRY-RUN] Videos will be generated but NOT uploaded to TikTok")

    if args.once:
        # Single video mode
        logger.info(f"\n[ONCE] Generating a single {args.type} video...")

        from main_pipeline import ChessTikTokPipeline
        pipeline = ChessTikTokPipeline(config)
        video = pipeline.generate_single_content(content_type=args.type)

        if video:
            logger.info(f"\n[OK] Video generated: {video}")
        else:
            logger.error("\n[FAIL] Video generation failed")
            sys.exit(1)

    else:
        # Full schedule mode
        logger.info(f"\n[SCHEDULE] Starting 5/day automation...")
        logger.info("Schedule:")
        logger.info("  07:00 - Puzzle")
        logger.info("  10:30 - GM Game")
        logger.info("  13:00 - Auto (puzzle/game)")
        logger.info("  17:00 - GM Game")
        logger.info("  20:30 - Puzzle")
        logger.info(f"  Jitter: +/- {args.jitter} minutes")
        logger.info("\nPress Ctrl+C to stop\n")

        from scheduler import VideoScheduler
        scheduler = VideoScheduler(
            videos_per_day=args.videos_per_day,
            config=config,
            jitter_minutes=args.jitter
        )
        scheduler.run_forever()


def main():
    parser = argparse.ArgumentParser(
        description="Kisyis Chess - Full TikTok Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_automation.py --setup        # First-time setup (TikTok login)
  python run_automation.py --once         # Generate + upload 1 video now
  python run_automation.py --once --type puzzle  # 1 puzzle video
  python run_automation.py --dry-run --once      # Generate without uploading
  python run_automation.py                # Start 5/day schedule
        """
    )

    parser.add_argument(
        '--setup',
        action='store_true',
        help='First-time interactive setup (TikTok login + test)'
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='Generate and upload 1 video, then exit'
    )

    parser.add_argument(
        '--type',
        type=str,
        choices=['game', 'puzzle', 'auto'],
        default='auto',
        help='Content type: game, puzzle, or auto (default: auto)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate video but do not upload to TikTok'
    )

    parser.add_argument(
        '--videos-per-day',
        type=int,
        default=5,
        help='Number of videos per day (default: 5)'
    )

    parser.add_argument(
        '--jitter',
        type=int,
        default=15,
        help='Random jitter in minutes for scheduling (default: 15)'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to custom config JSON file'
    )

    args = parser.parse_args()

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    logger = setup_logging()

    logger.info("\n" + "=" * 70)
    logger.info("  KISYIS CHESS - TikTok Automation")
    logger.info("  5 videos/day (GM games + puzzles)")
    logger.info("=" * 70)

    if args.config:
        # Override config file path
        os.environ['CHESS_CONFIG'] = args.config

    if args.setup:
        success = first_time_setup(logger)
        sys.exit(0 if success else 1)
    else:
        run_automation(args, logger)


if __name__ == "__main__":
    main()
