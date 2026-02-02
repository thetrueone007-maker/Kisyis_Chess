#!/usr/bin/env python3
"""
Render chess games to MP4 (direct ffmpeg pipe) — 9:16 vertical, 4K-ish, 120FPS default.

Requirements:
  pip install PySide6 python-chess Pillow
  ffmpeg must be installed and in PATH.

Usage:
  python chess_com_like_pyside_6.py --input_dir ./ouvertures --assets ./assets --output_dir ./renders
"""

import sys
import os
import math
import argparse
import subprocess
from pathlib import Path
from time import time

from PySide6.QtGui import QImage, QPainter, QPixmap, QColor, QFont
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

import chess
import chess.pgn
from PIL import Image

# ----------------- Defaults / Config -----------------
DEFAULT_FPS = 120
DEFAULT_WIDTH = 2160   # 9:16 vertical width
DEFAULT_HEIGHT = 3840
BOARD_SQUARES = 8
TITLE_BIG_SECONDS = 1.0
TITLE_SHRINK_SECONDS = 0.6
MOVE_SECONDS = 0.7    # slower moves (50% slower)
BACKGROUND_COLOR = (0, 0, 0, 0)  # transparent background
LIGHT_COLOR = (235, 245, 255)   # white-ish square
DARK_COLOR = (30, 100, 170)     # blue square
PIECE_SCALE = 0.92
COORD_FONT_RATIO = 0.035
TITLE_BIG_RATIO = 0.12
TITLE_SMALL_RATIO = 0.045

PIECE_FILENAME_MAP = {
    ('w','K'): 'wK.png', ('w','Q'): 'wQ.png', ('w','R'): 'wR.png', ('w','B'): 'wB.png', ('w','N'): 'wN.png', ('w','P'): 'wP.png',
    ('b','K'): 'bK.png', ('b','Q'): 'bQ.png', ('b','R'): 'bR.png', ('b','B'): 'bB.png', ('b','N'): 'bN.png', ('b','P'): 'bP.png',
}
# -----------------------------------------------------

class Renderer:
    def __init__(self, assets_dir, width, height, fps, out_dir, move_seconds=MOVE_SECONDS, flip_board=False):
        self.assets_dir = Path(assets_dir)
        self.width = width
        self.height = height
        self.fps = fps
        self.out_dir = Path(out_dir)
        self.move_seconds = move_seconds
        self.flip_board = flip_board  # Flip board for black's perspective

        self.board_size = min(self.width, int(self.height * 0.82))
        self.margin_x = (self.width - self.board_size) // 2
        self.margin_y = int((self.height - self.board_size) * 0.55)
        self.square_size = self.board_size / BOARD_SQUARES

        self._load_piece_images()

    def _load_piece_images(self):
        self.pil_pieces = {}
        for (color, piece), filename in PIECE_FILENAME_MAP.items():
            path = self.assets_dir / filename
            if not path.exists():
                raise FileNotFoundError(f"Missing piece asset: {path}")
            img = Image.open(path).convert("RGBA")
            self.pil_pieces[(color, piece)] = img

    def _pil_to_qpixmap_scaled(self, pil_img, target_px):
        pil2 = pil_img.resize((int(target_px), int(target_px)), Image.LANCZOS)
        data = pil2.tobytes("raw", "RGBA")
        qim = QImage(data, pil2.width, pil2.height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qim)

    def square_top_left(self, square):
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)

        if self.flip_board:
            # Black's perspective: flip both axes
            x = self.margin_x + (7 - file_idx) * self.square_size
            y = self.margin_y + rank_idx * self.square_size
        else:
            # White's perspective: normal
            x = self.margin_x + file_idx * self.square_size
            y = self.margin_y + (7 - rank_idx) * self.square_size

        return QPointF(x, y)

    def draw_board_background(self, painter):
        painter.fillRect(0, 0, self.width, self.height, QColor(*BACKGROUND_COLOR))
        for r in range(8):
            for f in range(8):
                x = int(self.margin_x + f * self.square_size)
                y = int(self.margin_y + r * self.square_size)
                color = LIGHT_COLOR if ((f + r) % 2 == 0) else DARK_COLOR
                painter.fillRect(x, y, int(self.square_size)+1, int(self.square_size)+1, QColor(*color))
        coord_font_size = max(12, int(self.square_size * COORD_FONT_RATIO))
        font = QFont("Helvetica", coord_font_size)
        painter.setFont(font)
        painter.setPen(QColor(40,40,40))
        for i in range(8):
            fx = int(self.margin_x + i*self.square_size + 6)
            fy = int(self.margin_y + self.board_size - 6)
            # Files: a-h for white, h-a for black
            file_label = chr(ord('a') + (7 - i) if self.flip_board else ord('a') + i)
            painter.drawText(fx, fy, file_label)
            rx = int(self.margin_x + 3)
            ry = int(self.margin_y + i*self.square_size + coord_font_size)
            # Ranks: 8-1 for white, 1-8 for black
            rank_label = str(i + 1) if self.flip_board else str(8 - i)
            painter.drawText(rx, ry, rank_label)

    def draw_title(self, painter, text, phase, t):
        if phase == 'big':
            size = max(18, int(self.width * TITLE_BIG_RATIO))
            font = QFont("Helvetica", size)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))  # White title
            fm = painter.fontMetrics()
            w = fm.horizontalAdvance(text)
            h = fm.height()
            x = (self.width - w) / 2
            y = (self.margin_y / 2) + h/2
            painter.drawText(int(x), int(y), text)
        elif phase == 'shrinking':
            t = max(0.0, min(1.0, t))
            big_size = int(self.width * TITLE_BIG_RATIO)
            small_size = int(self.width * TITLE_SMALL_RATIO)
            size = int(big_size*(1-t) + small_size*t)
            font = QFont("Helvetica", size)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))  # White title
            fm = painter.fontMetrics()
            w = fm.horizontalAdvance(text)
            h = fm.height()
            start_x = (self.width - w) / 2
            start_y = (self.margin_y / 2) + h/2
            end_x = self.margin_x + 8
            end_y = self.margin_y - h - 15  # Above the board, not overlapping
            x = start_x*(1-t) + end_x*t
            y = start_y*(1-t) + end_y*t
            painter.drawText(int(x), int(y), text)
        else:
            size = int(self.width * TITLE_SMALL_RATIO)
            font = QFont("Helvetica", size)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))  # White title
            fm = painter.fontMetrics()
            h = fm.height()
            # Position above the board, not overlapping
            painter.drawText(int(self.margin_x + 8), int(self.margin_y - 15), text)

    def compose_piece_positions(self, board, moving_piece=None, from_sq=None, to_sq=None, progress=0.0, capture_sq=None, capture_fade=1.0, rook_piece=None, rook_from_sq=None, rook_to_sq=None):
        positions = {}
        piece_px = int(self.square_size * PIECE_SCALE)
        qpix_cache = {}
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p is None:
                continue
            if from_sq is not None and sq == from_sq:
                continue
            # Skip rook square if it's moving during castling
            if rook_from_sq is not None and sq == rook_from_sq:
                continue
            key = ('w' if p.color == chess.WHITE else 'b', p.symbol().upper())
            if key not in qpix_cache:
                pil = self.pil_pieces.get(key)
                if pil is None:
                    continue
                qpix_cache[key] = self._pil_to_qpixmap_scaled(pil, piece_px)
            pix = qpix_cache[key]
            tl = self.square_top_left(sq)
            posx = tl.x() + (self.square_size - pix.width())/2
            posy = tl.y() + (self.square_size - pix.height())/2
            opacity = 1.0
            if capture_sq is not None and sq == capture_sq:
                opacity = capture_fade
            positions[sq] = (pix, posx, posy, opacity)

        # Animate the main moving piece
        if moving_piece is not None and from_sq is not None and to_sq is not None:
            tl_from = self.square_top_left(from_sq)
            tl_to = self.square_top_left(to_sq)
            startx = tl_from.x() + (self.square_size - piece_px)/2
            starty = tl_from.y() + (self.square_size - piece_px)/2
            endx = tl_to.x() + (self.square_size - piece_px)/2
            endy = tl_to.y() + (self.square_size - piece_px)/2
            t = 1 - pow(1 - progress, 3)
            curx = startx*(1-t) + endx*t
            cury = starty*(1-t) + endy*t
            key = ('w' if moving_piece.color == chess.WHITE else 'b', moving_piece.symbol().upper())
            if key not in qpix_cache:
                pil = self.pil_pieces.get(key)
                qpix_cache[key] = self._pil_to_qpixmap_scaled(pil, piece_px)
            pix = qpix_cache[key]
            positions[to_sq] = (pix, curx, cury, 1.0)

        # Animate the rook during castling
        if rook_piece is not None and rook_from_sq is not None and rook_to_sq is not None:
            tl_from = self.square_top_left(rook_from_sq)
            tl_to = self.square_top_left(rook_to_sq)
            startx = tl_from.x() + (self.square_size - piece_px)/2
            starty = tl_from.y() + (self.square_size - piece_px)/2
            endx = tl_to.x() + (self.square_size - piece_px)/2
            endy = tl_to.y() + (self.square_size - piece_px)/2
            t = 1 - pow(1 - progress, 3)
            curx = startx*(1-t) + endx*t
            cury = starty*(1-t) + endy*t
            key = ('w' if rook_piece.color == chess.WHITE else 'b', rook_piece.symbol().upper())
            if key not in qpix_cache:
                pil = self.pil_pieces.get(key)
                qpix_cache[key] = self._pil_to_qpixmap_scaled(pil, piece_px)
            pix = qpix_cache[key]
            positions[rook_to_sq] = (pix, curx, cury, 1.0)

        return positions

    def render_board_qimage(self, board, piece_positions, title_text, title_phase, title_t):
        qimg = QImage(self.width, self.height, QImage.Format.Format_RGBA8888)
        qimg.fill(QColor(*BACKGROUND_COLOR))
        painter = QPainter(qimg)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.draw_board_background(painter)
        for sq, data in piece_positions.items():
            pix, px, py, op = data
            if pix is None:
                continue
            painter.setOpacity(op)
            painter.drawPixmap(int(px), int(py), pix)
            painter.setOpacity(1.0)
        self.draw_title(painter, title_text, title_phase, title_t)
        painter.end()
        return qimg

    def render_game_to_pipe(self, game, out_mp4_path):
        header_title = game.headers.get('Event') or game.headers.get('Title') or Path(out_mp4_path).stem
        moves = [m for m in game.mainline_moves()]
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgba',
            '-s', f'{self.width}x{self.height}',
            '-r', str(self.fps),
            '-i', '-',
            '-an',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '18',
            '-preset', 'slow',
            str(out_mp4_path)
        ]
        print("Launching ffmpeg:", " ".join(ffmpeg_cmd))
        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        frames_big = max(1, int(TITLE_BIG_SECONDS * self.fps))
        for i in range(frames_big):
            t = i / max(1, frames_big - 1)
            title_phase = 'big'; title_t = t
            positions = self.compose_piece_positions(chess.Board())
            qimg = self.render_board_qimage(chess.Board(), positions, header_title, title_phase, title_t)
            proc.stdin.write(qimg.bits().tobytes())

        frames_shrink = max(1, int(TITLE_SHRINK_SECONDS * self.fps))
        for i in range(frames_shrink):
            t = i / max(1, frames_shrink - 1)
            title_phase = 'shrinking'; title_t = t
            positions = self.compose_piece_positions(chess.Board())
            qimg = self.render_board_qimage(chess.Board(), positions, header_title, title_phase, title_t)
            proc.stdin.write(qimg.bits().tobytes())

        board = game.board()
        frames_per_move = max(1, int(self.move_seconds * self.fps))
        for move in moves:
            from_sq = move.from_square
            to_sq = move.to_square
            moving_piece = board.piece_at(from_sq)
            is_capture = board.is_capture(move)
            is_castling = board.is_castling(move)
            capture_sq = None

            # Handle castling - need to move both king and rook
            rook_from_sq = None
            rook_to_sq = None
            rook_piece = None
            if is_castling:
                # Determine rook squares for castling
                if to_sq > from_sq:  # Kingside castling
                    rook_from_sq = to_sq + 1  # Rook is one square to the right
                    rook_to_sq = from_sq + 1   # Rook ends up between king's start and end
                else:  # Queenside castling
                    rook_from_sq = to_sq - 2  # Rook is two squares to the left
                    rook_to_sq = from_sq - 1   # Rook ends up between king's start and end
                rook_piece = board.piece_at(rook_from_sq)

            if is_capture:
                capture_sq = to_sq
                if board.is_en_passant(move):
                    capture_sq = to_sq - 8 if moving_piece.color == chess.WHITE else to_sq + 8
            for f in range(frames_per_move):
                p = f / max(1, frames_per_move - 1)
                cap_op = 1.0
                if is_capture and p > 0.4:
                    cap_op = max(0.0, 1.0 - (p - 0.4) / 0.6)
                positions = self.compose_piece_positions(board, moving_piece=moving_piece, from_sq=from_sq, to_sq=to_sq, progress=p, capture_sq=capture_sq, capture_fade=cap_op, rook_piece=rook_piece, rook_from_sq=rook_from_sq, rook_to_sq=rook_to_sq)
                qimg = self.render_board_qimage(board, positions, header_title, 'small', 1.0)
                proc.stdin.write(qimg.bits().tobytes())
            board.push(move)

        pause_frames = max(1, int(1.0 * self.fps))
        for _ in range(pause_frames):
            positions = self.compose_piece_positions(board)
            qimg = self.render_board_qimage(board, positions, header_title, 'small', 1.0)
            proc.stdin.write(qimg.bits().tobytes())

        proc.stdin.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"ffmpeg exited with code {ret}")
        print("Wrote", out_mp4_path)

# ----------------- Utilities -----------------

def load_pgn_game(path):
    with open(path, 'r', encoding='utf-8') as f:
        game = chess.pgn.read_game(f)
    return game

# ----------------- Main CLI -----------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', required=True)
    parser.add_argument('--assets', required=True)
    parser.add_argument('--output_dir', required=True)
    parser.add_argument('--fps', type=int, default=DEFAULT_FPS)
    parser.add_argument('--width', type=int, default=DEFAULT_WIDTH)
    parser.add_argument('--height', type=int, default=DEFAULT_HEIGHT)
    parser.add_argument('--move_seconds', type=float, default=MOVE_SECONDS)
    args = parser.parse_args()

    app = QApplication([])

    input_dir = Path(args.input_dir)
    assets = Path(args.assets)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    renderer = Renderer(assets_dir=assets, width=args.width, height=args.height, fps=args.fps, out_dir=out_dir, move_seconds=args.move_seconds)

    pgn_files = sorted([p for p in input_dir.glob("*.pgn")])
    if not pgn_files:
        print("No .pgn files found in", input_dir)
        return

    for p in pgn_files:
        print("Processing:", p.name)
        game = load_pgn_game(p)
        if game is None:
            print("  Could not read game from", p)
            continue
        out_mp4 = out_dir / (p.stem + ".mp4")
        start = time()
        renderer.render_game_to_pipe(game, out_mp4)
        elapsed = time() - start
        print(f"  Done in {elapsed:.1f}s")

if __name__ == "__main__":
    main()
