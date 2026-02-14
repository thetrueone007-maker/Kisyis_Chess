#!/usr/bin/env python3
"""
Audio management for chess videos
Adds background music and sound effects
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict
import random

# Import ffmpeg path finder
try:
    from ffmpeg_path import FFMPEG_PATH
except ImportError:
    FFMPEG_PATH = FFMPEG_PATH


class AudioManager:
    """Manage background music and sound effects for chess videos"""

    def __init__(self, music_dir: Optional[Path] = None, sfx_dir: Optional[Path] = None):
        """
        Initialize audio manager

        Args:
            music_dir: Directory containing background music files
            sfx_dir: Directory containing sound effect files
        """
        self.music_dir = Path(music_dir) if music_dir else Path("./audio/music")
        self.sfx_dir = Path(sfx_dir) if sfx_dir else Path("./audio/sfx")

        # Create directories if they don't exist
        self.music_dir.mkdir(parents=True, exist_ok=True)
        self.sfx_dir.mkdir(parents=True, exist_ok=True)

        # Music recommendations for chess videos
        self.music_recommendations = """
        Recommended royalty-free music sources for chess videos:

        1. YouTube Audio Library (free, no attribution)
           - Search for "cinematic", "epic", "tension", "strategic"

        2. Pixabay Music (free, no attribution)
           - https://pixabay.com/music/

        3. Free Music Archive
           - https://freemusicarchive.org/

        4. Incompetech (free with attribution)
           - Search for Kevin MacLeod chess-appropriate tracks

        Recommended styles:
        - Cinematic/Epic for classical games
        - Electronic/Upbeat for blitz/rapid
        - Tension/Suspense for critical moments
        """

    def get_random_music(self) -> Optional[Path]:
        """Get a random background music file"""
        music_files = list(self.music_dir.glob("*.mp3")) + \
                     list(self.music_dir.glob("*.wav")) + \
                     list(self.music_dir.glob("*.m4a"))

        if not music_files:
            print("[WARN]  No music files found in", self.music_dir)
            print(self.music_recommendations)
            return None

        return random.choice(music_files)

    def add_audio_to_video(self, video_path: Path, output_path: Path,
                          music_path: Optional[Path] = None,
                          music_volume: float = 0.3,
                          fade_in: float = 2.0,
                          fade_out: float = 2.0) -> bool:
        """
        Add background music to a video file

        Args:
            video_path: Input video file
            output_path: Output video file with audio
            music_path: Background music file (random if None)
            music_volume: Volume level (0.0 to 1.0)
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds

        Returns:
            True if successful
        """
        if music_path is None:
            music_path = self.get_random_music()

        if music_path is None or not music_path.exists():
            print(f"[WARN]  Music file not found: {music_path}")
            print("   Skipping audio integration")
            # Just copy the video
            import shutil
            shutil.copy(video_path, output_path)
            return False

        # Get video duration
        duration = self._get_video_duration(video_path)
        if duration is None:
            return False

        # Build ffmpeg command with audio
        # - Loop music if needed
        # - Adjust volume
        # - Add fade in/out
        # - Mix with video (which has no audio originally)

        cmd = [
            FFMPEG_PATH, '-y',
            '-i', str(video_path),
            '-stream_loop', '-1',  # Loop audio
            '-i', str(music_path),
            '-filter_complex',
            f'[1:a]volume={music_volume},afade=t=in:st=0:d={fade_in},afade=t=out:st={duration-fade_out}:d={fade_out}[audio]',
            '-map', '0:v:0',
            '-map', '[audio]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',  # Stop when video ends
            str(output_path)
        ]

        try:
            print(f"Adding audio: {music_path.name}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[ERROR] FFmpeg error: {result.stderr}")
                return False

            print(f"[OK] Audio added successfully: {output_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Error adding audio: {e}")
            return False

    def _get_video_duration(self, video_path: Path) -> Optional[float]:
        """Get video duration in seconds using ffprobe"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception as e:
            print(f"Error getting video duration: {e}")

        return None

    def create_sfx_markers(self, analyses: List, fps: int = 120) -> Dict[int, str]:
        """
        Create sound effect markers for key moments

        Args:
            analyses: List of move analyses
            fps: Video frame rate

        Returns:
            Dict mapping frame numbers to SFX file names
        """
        sfx_timeline = {}

        # Define sound effects for different move types
        sfx_map = {
            'brilliant': 'brilliant.mp3',
            'blunder': 'blunder.mp3',
            'capture': 'capture.mp3',
            'check': 'check.mp3',
            'checkmate': 'checkmate.mp3'
        }

        current_frame = 0
        for analysis in analyses:
            # Add SFX for brilliant moves
            if analysis.is_brilliant:
                sfx_timeline[current_frame] = sfx_map['brilliant']
            # Add SFX for blunders
            elif analysis.is_blunder:
                sfx_timeline[current_frame] = sfx_map['blunder']

            current_frame += int(fps * 0.35)  # Move duration

        return sfx_timeline

    def download_sample_music(self):
        """Helper to guide user in downloading music"""
        print("\n" + "="*60)
        print("AUDIO SETUP GUIDE")
        print("="*60)
        print(self.music_recommendations)
        print("\nOnce downloaded, place music files in:")
        print(f"  {self.music_dir.absolute()}")
        print("\nSupported formats: MP3, WAV, M4A")
        print("="*60)


class TikTokAudioOptimizer:
    """Optimize audio specifically for TikTok"""

    @staticmethod
    def optimize_for_tiktok(input_video: Path, output_video: Path) -> bool:
        """
        Optimize audio for TikTok specifications

        TikTok recommendations:
        - AAC audio codec
        - 192 kbps bitrate
        - 44.1 kHz or 48 kHz sample rate
        - Stereo
        """
        cmd = [
            FFMPEG_PATH, '-y',
            '-i', str(input_video),
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000',
            '-ac', '2',
            str(output_video)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error optimizing audio: {e}")
            return False


if __name__ == "__main__":
    print("Audio Manager for Chess Videos")
    print("=" * 60)

    manager = AudioManager()

    # Check for music files
    music_files = list(manager.music_dir.glob("*.mp3"))
    if music_files:
        print(f"\n[OK] Found {len(music_files)} music file(s)")
        for f in music_files[:5]:
            print(f"   - {f.name}")
    else:
        print("\n[WARN]  No music files found!")
        manager.download_sample_music()

    print("\nTo add music to a video, use:")
    print("  manager.add_audio_to_video(video_path, output_path)")
