#!/usr/bin/env python3
"""
System test script - Verify all components are working
"""

import sys
from pathlib import Path

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("♟️  KISYIS CHESS - System Test")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

errors = []
warnings = []

# Test 1: Python modules
print("\n[1/8] Testing Python imports...")
try:
    import chess
    import chess.pgn
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QImage
    import requests
    import berserk
    import schedule
    print("✅ All Python packages available")
except ImportError as e:
    errors.append(f"Python package missing: {e}")
    print(f"❌ {errors[-1]}")

# Test 2: System tools
print("\n[2/8] Testing system tools...")
import subprocess

def check_command(cmd):
    try:
        result = subprocess.run([cmd, '--version'], capture_output=True, timeout=2)
        return result.returncode == 0
    except:
        return False

if check_command('ffmpeg'):
    print("✅ FFmpeg available")
else:
    errors.append("FFmpeg not found")
    print(f"❌ {errors[-1]}")

if check_command('stockfish'):
    print("✅ Stockfish available")
else:
    warnings.append("Stockfish not found (optional)")
    print(f"⚠️  {warnings[-1]}")

# Test 3: Project modules
print("\n[3/8] Testing project modules...")
try:
    from game_fetcher import GameFetcher
    from enhanced_renderer import EnhancedRenderer
    from comment_generator import CommentGenerator
    from audio_manager import AudioManager
    from tiktok_manager import TikTokVideoPrep
    print("✅ All project modules loadable")
except ImportError as e:
    errors.append(f"Project module error: {e}")
    print(f"❌ {errors[-1]}")

# Test 4: Assets
print("\n[4/8] Testing chess piece assets...")
assets_dir = Path("./assets")
required_pieces = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP', 'bK', 'bQ', 'bR', 'bB', 'bN', 'bP']
missing_pieces = []

for piece in required_pieces:
    if not (assets_dir / f"{piece}.png").exists():
        missing_pieces.append(piece)

if missing_pieces:
    errors.append(f"Missing piece assets: {', '.join(missing_pieces)}")
    print(f"❌ {errors[-1]}")
else:
    print(f"✅ All 12 piece assets found")

# Test 5: Directories
print("\n[5/8] Testing directory structure...")
required_dirs = ['ouvertures', 'renders', 'assets', 'tiktok_ready', 'temp']
for dir_name in required_dirs:
    dir_path = Path(dir_name)
    if dir_path.exists():
        print(f"✅ {dir_name}/")
    else:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ {dir_name}/ (created)")

# Test 6: Configuration
print("\n[6/8] Testing configuration...")
import os

api_key = os.getenv('ANTHROPIC_API_KEY')
if api_key:
    print(f"✅ ANTHROPIC_API_KEY set ({api_key[:8]}...)")
else:
    warnings.append("ANTHROPIC_API_KEY not set (AI comments will be basic)")
    print(f"⚠️  {warnings[-1]}")

# Test 7: Music
print("\n[7/8] Testing audio files...")
music_dir = Path("./audio/music")
music_files = list(music_dir.glob("*.mp3")) if music_dir.exists() else []

if music_files:
    print(f"✅ {len(music_files)} music file(s) found")
else:
    warnings.append("No background music found (videos will have no audio)")
    print(f"⚠️  {warnings[-1]}")

# Test 8: Game fetcher
print("\n[8/8] Testing game fetching...")
try:
    from game_fetcher import GameFetcher
    fetcher = GameFetcher()
    game, name = fetcher.get_classic_game()
    if game:
        print(f"✅ Can fetch classic games ({name})")
    else:
        errors.append("Classic game fetching failed")
        print(f"❌ {errors[-1]}")
except Exception as e:
    errors.append(f"Game fetcher error: {e}")
    print(f"❌ {errors[-1]}")

# Summary
print("\n" + "━"*60)
print("SUMMARY")
print("━"*60)

if errors:
    print(f"\n❌ {len(errors)} ERROR(S):")
    for error in errors:
        print(f"   • {error}")

if warnings:
    print(f"\n⚠️  {len(warnings)} WARNING(S):")
    for warning in warnings:
        print(f"   • {warning}")

if not errors:
    print("\n✅ ALL CRITICAL TESTS PASSED!")
    print("\n🚀 System is ready for video generation!")
    print("\nQuick Start:")
    print("  python main_pipeline.py --count 1")
else:
    print("\n❌ SYSTEM NOT READY")
    print("\nPlease fix the errors above before proceeding.")
    print("See README.md for installation instructions.")
    sys.exit(1)

if warnings:
    print("\n💡 Tips:")
    for i, warning in enumerate(warnings, 1):
        if "ANTHROPIC_API_KEY" in warning:
            print(f"  {i}. Get API key: https://console.anthropic.com/")
        elif "Stockfish" in warning:
            print(f"  {i}. Install Stockfish: sudo pacman -S stockfish")
        elif "music" in warning:
            print(f"  {i}. Download music: https://www.youtube.com/audiolibrary")

print("\n" + "━"*60)
print("Test complete!")
print("━"*60 + "\n")
