#!/usr/bin/env python3
"""
Download high-quality chess pieces from various sources.
Converts SVG to high-resolution PNG for optimal video rendering.
"""

import os
import sys
import requests
from pathlib import Path
from io import BytesIO

# Try to import cairosvg for SVG->PNG conversion
try:
    import cairosvg
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False
    print("Warning: cairosvg not installed. Install with: pip install cairosvg")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Output directory for high-quality pieces
OUTPUT_DIR = Path(__file__).parent / "assets_ultra"

# Lichess piece sets - SVG URLs
LICHESS_BASE = "https://raw.githubusercontent.com/lichess-org/lila/master/public/piece"

# Available piece sets from Lichess
PIECE_SETS = {
    'cburnett': 'cburnett',      # Default Lichess set - clean and professional
    'merida': 'merida',          # Classic tournament style
    'staunty': 'staunty',        # Modern 3D-ish
    'pirouetti': 'pirouetti',    # Elegant
    'chessnut': 'chessnut',      # Bold
    'letter': 'letter',          # Minimalist
    'alpha': 'alpha',            # Simple
    'california': 'california',  # Clean
}

# Piece file mapping
PIECES = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP', 'bK', 'bQ', 'bR', 'bB', 'bN', 'bP']

# Wikimedia Commons URLs (very high quality SVGs by Colin Burnett)
WIKIMEDIA_BASE = "https://upload.wikimedia.org/wikipedia/commons"
WIKIMEDIA_PIECES = {
    'wK': '/4/42/Chess_klt45.svg',
    'wQ': '/1/15/Chess_qlt45.svg',
    'wR': '/7/72/Chess_rlt45.svg',
    'wB': '/b/b1/Chess_blt45.svg',
    'wN': '/7/70/Chess_nlt45.svg',
    'wP': '/4/45/Chess_plt45.svg',
    'bK': '/f/f0/Chess_kdt45.svg',
    'bQ': '/4/47/Chess_qdt45.svg',
    'bR': '/f/ff/Chess_rdt45.svg',
    'bB': '/9/98/Chess_bdt45.svg',
    'bN': '/e/ef/Chess_ndt45.svg',
    'bP': '/c/c7/Chess_pdt45.svg',
}


def download_file(url: str) -> bytes:
    """Download file from URL and return bytes."""
    print(f"  Downloading: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def svg_to_png(svg_data: bytes, output_size: int = 1024) -> bytes:
    """Convert SVG data to PNG at specified size."""
    if HAS_CAIROSVG:
        return cairosvg.svg2png(
            bytestring=svg_data,
            output_width=output_size,
            output_height=output_size
        )
    else:
        raise ImportError("cairosvg is required for SVG conversion")


def download_lichess_set(set_name: str, output_dir: Path, size: int = 1024):
    """Download a complete piece set from Lichess."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nDownloading Lichess '{set_name}' piece set...")

    for piece in PIECES:
        url = f"{LICHESS_BASE}/{set_name}/{piece}.svg"
        try:
            svg_data = download_file(url)

            if HAS_CAIROSVG:
                png_data = svg_to_png(svg_data, size)
                output_path = output_dir / f"{piece}.png"
                with open(output_path, 'wb') as f:
                    f.write(png_data)
                print(f"    Saved: {output_path.name} ({size}x{size})")
            else:
                # Save SVG directly
                output_path = output_dir / f"{piece}.svg"
                with open(output_path, 'wb') as f:
                    f.write(svg_data)
                print(f"    Saved: {output_path.name} (SVG)")

        except Exception as e:
            print(f"    Error downloading {piece}: {e}")


def download_wikimedia_set(output_dir: Path, size: int = 1024):
    """Download high-quality pieces from Wikimedia Commons."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nDownloading Wikimedia Commons piece set...")

    for piece, path in WIKIMEDIA_PIECES.items():
        url = WIKIMEDIA_BASE + path
        try:
            svg_data = download_file(url)

            if HAS_CAIROSVG:
                png_data = svg_to_png(svg_data, size)
                output_path = output_dir / f"{piece}.png"
                with open(output_path, 'wb') as f:
                    f.write(png_data)
                print(f"    Saved: {output_path.name} ({size}x{size})")
            else:
                output_path = output_dir / f"{piece}.svg"
                with open(output_path, 'wb') as f:
                    f.write(svg_data)
                print(f"    Saved: {output_path.name} (SVG)")

        except Exception as e:
            print(f"    Error downloading {piece}: {e}")


def enhance_png_quality(input_dir: Path, output_dir: Path, target_size: int = 512):
    """Enhance existing PNG pieces by upscaling with high-quality resampling."""
    if not HAS_PIL:
        print("Pillow required for PNG enhancement")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nEnhancing pieces from {input_dir}...")

    for piece in PIECES:
        input_path = input_dir / f"{piece}.png"
        if not input_path.exists():
            print(f"    Missing: {piece}.png")
            continue

        try:
            img = Image.open(input_path).convert("RGBA")

            # Upscale with LANCZOS for best quality
            if img.size[0] < target_size:
                img = img.resize((target_size, target_size), Image.LANCZOS)

            output_path = output_dir / f"{piece}.png"
            img.save(output_path, "PNG", optimize=True)
            print(f"    Enhanced: {piece}.png -> {target_size}x{target_size}")

        except Exception as e:
            print(f"    Error enhancing {piece}: {e}")


def main():
    print("=" * 60)
    print("Chess Piece Downloader - High Quality Assets")
    print("=" * 60)

    # Target size for rendering (higher = better quality)
    TARGET_SIZE = 1024  # 1024x1024 pixels per piece

    # Download Wikimedia Commons set (best quality, public domain)
    wikimedia_dir = OUTPUT_DIR / "wikimedia"
    download_wikimedia_set(wikimedia_dir, TARGET_SIZE)

    # Download Lichess cburnett set (default, very clean)
    cburnett_dir = OUTPUT_DIR / "cburnett"
    download_lichess_set('cburnett', cburnett_dir, TARGET_SIZE)

    # Download Lichess staunty set (nice 3D look)
    staunty_dir = OUTPUT_DIR / "staunty"
    download_lichess_set('staunty', staunty_dir, TARGET_SIZE)

    # Download Lichess merida set (classic tournament)
    merida_dir = OUTPUT_DIR / "merida"
    download_lichess_set('merida', merida_dir, TARGET_SIZE)

    # Copy best set to main assets directory
    best_dir = OUTPUT_DIR / "wikimedia"  # Wikimedia has best quality
    main_assets = Path(__file__).parent / "assets"

    if best_dir.exists() and HAS_PIL:
        print(f"\nCopying best pieces to {main_assets}...")
        main_assets.mkdir(parents=True, exist_ok=True)

        for piece in PIECES:
            src = best_dir / f"{piece}.png"
            if src.exists():
                img = Image.open(src).convert("RGBA")
                dst = main_assets / f"{piece}.png"
                img.save(dst, "PNG", optimize=True)
                print(f"    Copied: {piece}.png")

    print("\n" + "=" * 60)
    print("Download complete!")
    print(f"High-quality pieces saved to: {OUTPUT_DIR}")
    print("=" * 60)

    if not HAS_CAIROSVG:
        print("\nNote: Install cairosvg for automatic SVG->PNG conversion:")
        print("  pip install cairosvg")


if __name__ == "__main__":
    main()
