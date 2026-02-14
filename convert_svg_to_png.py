#!/usr/bin/env python3
"""
Convert downloaded SVG chess pieces to high-resolution PNG.
"""

import cairosvg
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import io

# Directories
BASE_DIR = Path(__file__).parent
SVG_SETS = ['cburnett_svg', 'staunty_svg', 'merida_svg']
OUTPUT_SIZE = 1024  # Ultra-high resolution

PIECES = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP', 'bK', 'bQ', 'bR', 'bB', 'bN', 'bP']


def svg_to_png_enhanced(svg_path: Path, output_path: Path, size: int = 1024):
    """Convert SVG to PNG with enhancement."""
    # Read SVG
    with open(svg_path, 'rb') as f:
        svg_data = f.read()

    # Convert to PNG at target size
    png_data = cairosvg.svg2png(
        bytestring=svg_data,
        output_width=size,
        output_height=size
    )

    # Load into PIL for enhancement
    img = Image.open(io.BytesIO(png_data)).convert("RGBA")

    # Slight sharpening for crispness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.1)

    # Slight contrast boost
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.02)

    # Save
    img.save(output_path, "PNG", optimize=True)
    return img.size


def process_set(set_name: str, output_name: str):
    """Process a complete SVG set."""
    svg_dir = BASE_DIR / "assets_ultra" / set_name
    output_dir = BASE_DIR / "assets_ultra" / output_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nProcessing {set_name} -> {output_name} ({OUTPUT_SIZE}x{OUTPUT_SIZE})...")

    for piece in PIECES:
        svg_path = svg_dir / f"{piece}.svg"
        png_path = output_dir / f"{piece}.png"

        if not svg_path.exists():
            print(f"  Missing: {svg_path}")
            continue

        try:
            size = svg_to_png_enhanced(svg_path, png_path, OUTPUT_SIZE)
            print(f"  [OK] {piece}.png ({size[0]}x{size[1]})")
        except Exception as e:
            print(f"  [X] {piece}: {e}")


def copy_best_to_assets(source_dir: Path, assets_dir: Path):
    """Copy best pieces to main assets directory."""
    print(f"\nCopying to main assets: {assets_dir}")
    assets_dir.mkdir(parents=True, exist_ok=True)

    for piece in PIECES:
        src = source_dir / f"{piece}.png"
        if src.exists():
            img = Image.open(src)
            dst = assets_dir / f"{piece}.png"
            img.save(dst, "PNG", optimize=True)
            print(f"  [OK] {piece}.png -> assets/")


def main():
    print("=" * 70)
    print("  SVG TO PNG CONVERTER - Ultra High Quality")
    print("=" * 70)

    # Convert all SVG sets
    for svg_set in SVG_SETS:
        output_name = svg_set.replace('_svg', '_hq')
        process_set(svg_set, output_name)

    # Choose the best set and copy to main assets
    # cburnett is clean and professional - best for video
    best_set = BASE_DIR / "assets_ultra" / "cburnett_hq"
    main_assets = BASE_DIR / "assets"

    if best_set.exists():
        copy_best_to_assets(best_set, main_assets)

    # Also save staunty as an alternative (nice 3D look)
    staunty_set = BASE_DIR / "assets_ultra" / "staunty_hq"
    staunty_assets = BASE_DIR / "assets_staunty_new"

    if staunty_set.exists():
        copy_best_to_assets(staunty_set, staunty_assets)

    print("\n" + "=" * 70)
    print("  CONVERSION COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
