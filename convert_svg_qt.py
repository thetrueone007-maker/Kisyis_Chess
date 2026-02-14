#!/usr/bin/env python3
"""
Convert SVG to PNG using PySide6/Qt (already installed).
"""

import sys
from pathlib import Path
from PIL import Image
import io

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray, Qt

# Directories
BASE_DIR = Path(__file__).parent
SVG_SETS = ['cburnett_svg', 'staunty_svg', 'merida_svg']
OUTPUT_SIZE = 1024

PIECES = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP', 'bK', 'bQ', 'bR', 'bB', 'bN', 'bP']


def svg_to_png_qt(svg_path: Path, output_path: Path, size: int = 1024):
    """Convert SVG to PNG using Qt's SVG renderer."""
    # Read SVG data
    with open(svg_path, 'rb') as f:
        svg_data = f.read()

    # Create SVG renderer
    renderer = QSvgRenderer(QByteArray(svg_data))
    if not renderer.isValid():
        raise ValueError(f"Invalid SVG: {svg_path}")

    # Create image with transparency
    img = QImage(size, size, QImage.Format.Format_RGBA8888)
    img.fill(Qt.GlobalColor.transparent)

    # Render SVG to image
    painter = QPainter(img)
    painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()

    # Save PNG
    img.save(str(output_path), "PNG")

    return (size, size)


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
            size = svg_to_png_qt(svg_path, png_path, OUTPUT_SIZE)
            print(f"  OK {piece}.png ({size[0]}x{size[1]})")
        except Exception as e:
            print(f"  ERROR {piece}: {e}")


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
            print(f"  OK {piece}.png")


def main():
    print("=" * 70)
    print("  SVG TO PNG CONVERTER (Qt/PySide6)")
    print("=" * 70)

    # Need QApplication for Qt
    app = QApplication.instance() or QApplication(sys.argv)

    # Convert all SVG sets
    for svg_set in SVG_SETS:
        output_name = svg_set.replace('_svg', '_hq')
        process_set(svg_set, output_name)

    # Copy best to main assets (cburnett is clean and professional)
    best_set = BASE_DIR / "assets_ultra" / "cburnett_hq"
    if best_set.exists():
        copy_to_assets(best_set, BASE_DIR / "assets")

    # Also copy staunty as alternative
    staunty_set = BASE_DIR / "assets_ultra" / "staunty_hq"
    if staunty_set.exists():
        copy_to_assets(staunty_set, BASE_DIR / "assets_staunty_new")

    # Also copy merida as alternative
    merida_set = BASE_DIR / "assets_ultra" / "merida_hq"
    if merida_set.exists():
        copy_to_assets(merida_set, BASE_DIR / "assets_merida_new")

    print("\n" + "=" * 70)
    print("  CONVERSION COMPLETE!")
    print("  Main assets: ./assets (cburnett)")
    print("  Alternative: ./assets_staunty_new (staunty)")
    print("  Alternative: ./assets_merida_new (merida)")
    print("=" * 70)


if __name__ == "__main__":
    main()
