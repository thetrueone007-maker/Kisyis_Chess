#!/usr/bin/env python3
"""
Download high-quality chess pieces as PNG directly.
No SVG conversion needed - uses pre-rendered PNG from various sources.
"""

import os
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO

OUTPUT_DIR = Path(__file__).parent / "assets_ultra"

# Lichess PNG pieces (pre-rendered at 256px, we'll upscale with LANCZOS)
LICHESS_PNG_BASE = "https://raw.githubusercontent.com/lichess-org/lila/master/public/piece"

# JohnPablok's Cburnett pieces on GitHub (high quality)
CBURNETT_BASE = "https://raw.githubusercontent.com/ornicar/lila/master/public/piece/cburnett"

# Alternative: Chess.com style from a mirror (if available)
# We'll use multiple sources for redundancy

PIECES = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP', 'bK', 'bQ', 'bR', 'bB', 'bN', 'bP']

# Piece sets available as SVG on Lichess (we download and render)
AVAILABLE_SETS = ['cburnett', 'merida', 'staunty', 'pirouetti', 'alpha', 'california', 'chessnut']


def download_image(url: str) -> Image.Image:
    """Download image from URL and return PIL Image."""
    print(f"  GET {url}")
    response = requests.get(url, timeout=30, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGBA")


def download_lichess_svg_rendered(set_name: str, output_dir: Path, size: int = 512):
    """
    Download Lichess pieces as SVG and use browser/pillow to render.
    Lichess also provides them in piece-css as base64 PNG.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nDownloading Lichess '{set_name}' set...")

    for piece in PIECES:
        # Lichess stores SVG files
        url = f"{LICHESS_PNG_BASE}/{set_name}/{piece}.svg"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Save SVG for later conversion
            svg_path = output_dir / f"{piece}.svg"
            with open(svg_path, 'wb') as f:
                f.write(response.content)
            print(f"    Saved SVG: {piece}.svg")

        except Exception as e:
            print(f"    Error: {piece} - {e}")


def download_from_wikimedia_png(output_dir: Path, size: int = 1024):
    """
    Download from Wikimedia - they have PNG renders available.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nDownloading from Wikimedia Commons (PNG)...")

    # Wikimedia has thumb URLs for PNG rendering of SVGs
    # Format: /wikipedia/commons/thumb/{path}/1024px-{filename}
    WIKIMEDIA_THUMBS = {
        'wK': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Chess_klt45.svg/1024px-Chess_klt45.svg.png',
        'wQ': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Chess_qlt45.svg/1024px-Chess_qlt45.svg.png',
        'wR': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Chess_rlt45.svg/1024px-Chess_rlt45.svg.png',
        'wB': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Chess_blt45.svg/1024px-Chess_blt45.svg.png',
        'wN': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Chess_nlt45.svg/1024px-Chess_nlt45.svg.png',
        'wP': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Chess_plt45.svg/1024px-Chess_plt45.svg.png',
        'bK': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Chess_kdt45.svg/1024px-Chess_kdt45.svg.png',
        'bQ': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Chess_qdt45.svg/1024px-Chess_qdt45.svg.png',
        'bR': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/Chess_rdt45.svg/1024px-Chess_rdt45.svg.png',
        'bB': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Chess_bdt45.svg/1024px-Chess_bdt45.svg.png',
        'bN': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/Chess_ndt45.svg/1024px-Chess_ndt45.svg.png',
        'bP': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Chess_pdt45.svg/1024px-Chess_pdt45.svg.png',
    }

    for piece, url in WIKIMEDIA_THUMBS.items():
        try:
            img = download_image(url)

            # Resize if needed
            if img.size[0] != size:
                img = img.resize((size, size), Image.LANCZOS)

            output_path = output_dir / f"{piece}.png"
            img.save(output_path, "PNG", optimize=True)
            print(f"    Saved: {piece}.png ({size}x{size})")

        except Exception as e:
            print(f"    Error: {piece} - {e}")


def download_greenchess_set(output_dir: Path, size: int = 512):
    """
    Download from Green Chess (has multiple piece sets as PNG).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nDownloading Green Chess style pieces...")

    # This is a fallback source
    base = "https://greenchess.net/info/img/pieces"

    piece_map = {
        'wK': 'w_king', 'wQ': 'w_queen', 'wR': 'w_rook',
        'wB': 'w_bishop', 'wN': 'w_knight', 'wP': 'w_pawn',
        'bK': 'b_king', 'bQ': 'b_queen', 'bR': 'b_rook',
        'bB': 'b_bishop', 'bN': 'b_knight', 'bP': 'b_pawn',
    }

    for our_name, their_name in piece_map.items():
        url = f"{base}/merida/{their_name}.png"
        try:
            img = download_image(url)
            if img.size[0] != size:
                img = img.resize((size, size), Image.LANCZOS)

            output_path = output_dir / f"{our_name}.png"
            img.save(output_path, "PNG", optimize=True)
            print(f"    Saved: {our_name}.png")
        except Exception as e:
            print(f"    Error: {our_name} - {e}")


def create_enhanced_pieces(input_dir: Path, output_dir: Path, size: int = 512):
    """
    Take existing pieces and enhance them with better rendering.
    - Add subtle drop shadow
    - Optimize colors
    - Ensure clean transparency
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nEnhancing pieces from {input_dir}...")

    from PIL import ImageFilter, ImageEnhance

    for piece in PIECES:
        input_path = input_dir / f"{piece}.png"
        if not input_path.exists():
            continue

        try:
            img = Image.open(input_path).convert("RGBA")

            # Upscale if needed
            if img.size[0] < size:
                img = img.resize((size, size), Image.LANCZOS)
            elif img.size[0] > size:
                img = img.resize((size, size), Image.LANCZOS)

            # Enhance contrast slightly for better visibility
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.05)

            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)

            output_path = output_dir / f"{piece}.png"
            img.save(output_path, "PNG", optimize=True)
            print(f"    Enhanced: {piece}.png")

        except Exception as e:
            print(f"    Error: {piece} - {e}")


def main():
    print("=" * 70)
    print("  CHESS PIECE DOWNLOADER - Ultra High Quality")
    print("=" * 70)

    TARGET_SIZE = 1024  # 1024x1024 for ultra-sharp rendering

    # 1. Download from Wikimedia (best quality, public domain)
    wikimedia_dir = OUTPUT_DIR / "wikimedia"
    download_from_wikimedia_png(wikimedia_dir, TARGET_SIZE)

    # 2. Download Lichess SVGs for later use
    for set_name in ['cburnett', 'staunty', 'merida']:
        svg_dir = OUTPUT_DIR / f"{set_name}_svg"
        download_lichess_svg_rendered(set_name, svg_dir)

    # 3. Copy best set to main assets
    main_assets = Path(__file__).parent / "assets"
    best_source = wikimedia_dir

    if best_source.exists():
        print(f"\n{'='*70}")
        print(f"  Copying best pieces to main assets: {main_assets}")
        print(f"{'='*70}")

        main_assets.mkdir(parents=True, exist_ok=True)

        for piece in PIECES:
            src = best_source / f"{piece}.png"
            if src.exists():
                img = Image.open(src)
                dst = main_assets / f"{piece}.png"
                img.save(dst, "PNG", optimize=True)
                print(f"  -> {piece}.png copied")

    print(f"\n{'='*70}")
    print("  DOWNLOAD COMPLETE!")
    print(f"  High-quality assets: {OUTPUT_DIR}")
    print(f"  Main assets updated: {main_assets}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
