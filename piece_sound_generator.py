#!/usr/bin/env python3
"""
Manage piece movement sounds for chess videos using Chess.com sounds
"""

import subprocess
import shutil
from pathlib import Path
from typing import List, Dict
import chess
import chess.pgn

# Import ffmpeg path finder
try:
    from ffmpeg_path import FFMPEG_PATH
except ImportError:
    FFMPEG_PATH = FFMPEG_PATH


class PieceSoundGenerator:
    """Manage sound effects for piece movements using Chess.com sounds"""

    def __init__(self, sfx_dir: Path = None):
        """
        Initialize sound generator

        Args:
            sfx_dir: Directory to store sound effects
        """
        self.sfx_dir = Path(sfx_dir) if sfx_dir else Path("./audio/sfx")
        self.sfx_dir.mkdir(parents=True, exist_ok=True)

        # Chess.com sounds directory
        self.chesscom_dir = self.sfx_dir / "chesscom"

        # Ensure Chess.com sounds are available
        self._ensure_sounds_exist()

    def _ensure_sounds_exist(self):
        """Copy Chess.com sound effects if they don't exist"""

        sounds = ['move', 'capture', 'check', 'castle']

        for sound_name in sounds:
            sound_file = self.sfx_dir / f"{sound_name}.mp3"
            chesscom_sound = self.chesscom_dir / f"{sound_name}.mp3"

            if chesscom_sound.exists() and not sound_file.exists():
                shutil.copy(chesscom_sound, sound_file)
                print(f"[OK] Using Chess.com {sound_name} sound: {sound_file}")
            elif sound_file.exists():
                print(f"[OK] Chess.com {sound_name} sound ready: {sound_file}")
            else:
                print(f"[WARN]  Chess.com {sound_name} sound not found (optional)")

    def add_piece_sounds_to_video(self, video_path: Path, output_path: Path,
                                  game: chess.pgn.Game,
                                  fps: int = 60,
                                  move_seconds: float = 0.7,
                                  title_big_seconds: float = 1.0,
                                  title_shrink_seconds: float = 0.6) -> bool:
        """
        Add piece movement sounds to a chess video

        Args:
            video_path: Input video file
            output_path: Output video file with sounds
            game: Chess game to get move information
            fps: Video frame rate
            move_seconds: Duration of each move animation
            title_big_seconds: Duration of big title
            title_shrink_seconds: Duration of title shrinking

        Returns:
            True if successful
        """
        # Load all sound files
        move_sound = self.sfx_dir / "move.mp3"
        capture_sound = self.sfx_dir / "capture.mp3"
        check_sound = self.sfx_dir / "check.mp3"
        castle_sound = self.sfx_dir / "castle.mp3"

        if not move_sound.exists() or not capture_sound.exists():
            print("[WARN]  Sound files not found, skipping sound integration")
            import shutil
            shutil.copy(video_path, output_path)
            return False

        # Build timeline of sound events
        sound_timeline = []
        current_time = title_big_seconds + title_shrink_seconds

        board = game.board()
        for move in game.mainline_moves():
            # Determine move type
            is_capture = board.is_capture(move)
            is_castling = board.is_castling(move)

            # Make the move to check if it results in check
            board.push(move)
            is_check = board.is_check()

            # Select appropriate sound (priority: check > castle > capture > move)
            if is_check and check_sound.exists():
                sound_file = check_sound
                volume = 3.0  # Slightly louder for check
            elif is_castling and castle_sound.exists():
                sound_file = castle_sound
                volume = 2.5
            elif is_capture:
                sound_file = capture_sound
                volume = 2.8
            else:
                sound_file = move_sound
                volume = 2.2

            # Add sound at the moment the piece reaches its destination
            # (approximately 70% through the move animation for smooth feel)
            sound_time = current_time + (move_seconds * 0.7)

            sound_timeline.append({
                'time': sound_time,
                'file': sound_file,
                'volume': volume
            })

            current_time += move_seconds

        # Build ffmpeg filter complex for mixing sounds
        if not sound_timeline:
            # No moves, just copy
            import shutil
            shutil.copy(video_path, output_path)
            return True

        # Create ffmpeg command with multiple sound overlays
        filter_parts = []
        input_files = ['-i', str(video_path)]

        for i, sound_event in enumerate(sound_timeline):
            input_files.extend(['-i', str(sound_event['file'])])
            delay_ms = int(sound_event['time'] * 1000)
            volume = sound_event['volume']
            filter_parts.append(
                f"[{i+1}:a]adelay={delay_ms}|{delay_ms},volume={volume}[s{i}]"
            )

        # Mix all sounds together
        if len(sound_timeline) == 1:
            mix_filter = "[s0]"
        else:
            sound_inputs = "".join(f"[s{i}]" for i in range(len(sound_timeline)))
            mix_filter = f"{sound_inputs}amix=inputs={len(sound_timeline)}:duration=longest[audio]"
            filter_parts.append(mix_filter)
            mix_filter = "[audio]"

        filter_complex = ";".join(filter_parts)

        cmd = [
            FFMPEG_PATH, '-y',
            *input_files,
            '-filter_complex', filter_complex,
            '-map', '0:v:0',
            '-map', mix_filter,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            str(output_path)
        ]

        try:
            print(f"Adding {len(sound_timeline)} piece sounds to video...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"[WARN]  FFmpeg warning: {result.stderr[:200]}")
                # Try simpler approach - just copy if mixing fails
                import shutil
                shutil.copy(video_path, output_path)
                return False

            print(f"[OK] Added piece sounds successfully")
            return True

        except Exception as e:
            print(f"[WARN]  Error adding piece sounds: {e}")
            import shutil
            shutil.copy(video_path, output_path)
            return False


if __name__ == "__main__":
    print("Piece Sound Generator for Chess Videos")
    print("=" * 60)

    generator = PieceSoundGenerator()
    print("\n[OK] Sound effects ready:")
    print(f"   - Move sound: {generator.sfx_dir / 'move.mp3'}")
    print(f"   - Capture sound: {generator.sfx_dir / 'capture.mp3'}")
