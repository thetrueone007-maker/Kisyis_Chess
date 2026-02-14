"""FFmpeg path finder for Windows/Linux/Mac"""
import os
import shutil
import platform
from pathlib import Path

def find_ffmpeg():
    """Find ffmpeg executable path"""
    # Check if ffmpeg is in PATH
    ffmpeg_in_path = shutil.which('ffmpeg')
    if ffmpeg_in_path:
        return ffmpeg_in_path

    # Windows-specific locations
    if platform.system() == 'Windows':
        possible_paths = [
            # WinGet installation
            Path.home() / 'AppData/Local/Microsoft/WinGet/Packages',
            # Common installation locations
            Path('C:/ffmpeg/bin'),
            Path('C:/Program Files/ffmpeg/bin'),
            Path('C:/Program Files (x86)/ffmpeg/bin'),
        ]

        for base_path in possible_paths:
            if base_path.exists():
                # Search for ffmpeg.exe
                for ffmpeg_exe in base_path.rglob('ffmpeg.exe'):
                    return str(ffmpeg_exe)

    # Linux/Mac paths
    else:
        possible_paths = [
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path

    raise FileNotFoundError("FFmpeg not found. Please install FFmpeg and add it to PATH.")

# Cache the path
FFMPEG_PATH = find_ffmpeg()
print(f"Using FFmpeg: {FFMPEG_PATH}")
