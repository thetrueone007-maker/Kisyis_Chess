#!/usr/bin/env python3
"""
Convert SVG to PNG using svglib + reportlab (pure Python, no Cairo needed).
"""

from pathlib import Path
from PIL import Image
import io

try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    HAS_SVGLIB = True
except ImportError:
    HAS_SVGLIB = False
    print("svglib not available")

# Directories
BASE_DIR = Path(__file__).parent
SVG_SETS = ['cburnett_svg', 'staunty_svg', 'merida_svg']
OUTPUT_SIZE = 1024

PIECES = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP', 'bK', 'bQ', 'bR', 'bB', 'bN', 'bP']


def svg_to_png_svglib(svg_path: Path, output_path: Path, size: int = 1024):
    """Convert SVG to PNG using svglib."""
    drawing = svg2rlg(str(svg_path))
    if drawing is None:
        raise ValueError(f"Could not parse SVG: {svg_path}")

    # Scale to target size
    scale_x = size / drawing.width if drawing.width else 1
    scale_y = size / drawing.height if drawing.height else 1
    scale = min(scale_x, scale_y)

    drawing.width = size
    drawing.height = size
    drawing.scale(scale, scale)

    # Render to PNG
    renderPM.drawToFile(drawing, str(output_path), fmt="PNG", dpi=300)

    # Resize to exact size with PIL
    img = Image.open(output_path).convert("RGBA")
    if img.size != (size, size):
        img = img.resize((size, size), Image.LANCZOS)
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
            size = svg_to_png_svglib(svg_path, png_path, OUTPUT_SIZE)
            print(f"  [OK] {piece}.png ({size[0]}x{size[1]})")
        except Exception as e:
            print(f"  [X] {piece}: {e}")


def copy_to_assets(source_dir: Path, assets_dir: Path):
    """Copy pieces to assets directory."""
    print(f"\nCopying to: {assets_dir}")
    assets_dir.mkdir(parents=True, exist_ok=True)

    for piece in PIECES:
        src = source_dir / f"{piece}.png"
        if src.exists():
            img = Image.open(src)
            dst = assets_dir / f"{piece}.png"
            img.save(dst, "PNG", optimize=True)
            print(f"  [OK] {piece}.png")


def main():
    print("=" * 70)
    print("  SVG TO PNG CONVERTER (svglib)")
    print("=" * 70)

    if not HAS_SVGLIB:
        print("ERROR: svglib not installed. Run: pip install svglib reportlab")
        return

    # Convert all SVG sets
    for svg_set in SVG_SETS:
        output_name = svg_set.replace('_svg', '_hq')
        process_set(svg_set, output_name)

    # Copy best to main assets
    best_set = BASE_DIR / "assets_ultra" / "cburnett_hq"
    if best_set.exists():
        copy_to_assets(best_set, BASE_DIR / "assets")

    print("\n" + "=" * 70)
    print("  DONE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
