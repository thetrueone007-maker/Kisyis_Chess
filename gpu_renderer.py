#!/usr/bin/env python3
"""
GPU-accelerated chess renderer using CuPy (CUDA) for RTX GPUs.
Falls back to NumPy if CUDA is not available.

This renderer pre-computes static elements and uses GPU for:
- Image compositing
- Alpha blending
- Interpolation
- Color operations
"""

import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
import chess
import chess.pgn
from PIL import Image
import subprocess
import sys

# Try to import CuPy for GPU acceleration
try:
    import cupy as cp
    from cupyx.scipy import ndimage as cp_ndimage
    GPU_AVAILABLE = True
    xp = cp  # Use CuPy as array module
    print("[GPU] CuPy CUDA acceleration enabled")
except ImportError:
    GPU_AVAILABLE = False
    xp = np  # Fallback to NumPy
    print("[CPU] CuPy not found, using NumPy (install with: pip install cupy-cuda12x)")

# Theme colors
THEME = {
    'light': (238, 238, 210),
    'dark': (118, 150, 86),
    'background': (22, 21, 18),
}

PIECE_SCALE = 0.88


@dataclass
class GPUMoveHighlight:
    from_square: int
    to_square: int
    color: Tuple[int, int, int, int]


class GPURenderer:
    """High-performance GPU-accelerated chess renderer"""

    def __init__(self, assets_dir, width=1080, height=1920, fps=60,
                 move_seconds=0.7, flip_board=False):
        self.assets_dir = Path(assets_dir)
        self.width = width
        self.height = height
        self.fps = fps
        self.move_seconds = move_seconds
        self.flip_board = flip_board

        # Calculate board dimensions (9:16 vertical format)
        self.board_size = int(min(width, height * 0.6))
        self.square_size = self.board_size // 8
        self.board_size = self.square_size * 8  # Align to grid

        # Center board
        self.margin_x = (width - self.board_size) // 2
        self.margin_y = (height - self.board_size) // 2

        # Pre-render static elements
        self._init_board_texture()
        self._load_pieces()

        # Frame buffer on GPU
        self.frame_buffer = xp.zeros((height, width, 4), dtype=xp.uint8)

        # Pre-compute easing lookup table
        self._init_easing_table()

    def _init_easing_table(self, steps=1000):
        """Pre-compute cubic easing values"""
        t = np.linspace(0, 1, steps)
        self.easing_table = 1 - np.power(1 - t, 3)
        if GPU_AVAILABLE:
            self.easing_table = cp.asarray(self.easing_table)

    def _get_eased_progress(self, progress: float) -> float:
        """Get eased progress value from lookup table"""
        idx = int(progress * (len(self.easing_table) - 1))
        idx = max(0, min(idx, len(self.easing_table) - 1))
        if GPU_AVAILABLE:
            return float(self.easing_table[idx].get())
        return float(self.easing_table[idx])

    def _init_board_texture(self):
        """Pre-render the chess board texture on GPU"""
        board = np.zeros((self.board_size, self.board_size, 4), dtype=np.uint8)

        light = THEME['light']
        dark = THEME['dark']

        for row in range(8):
            for col in range(8):
                is_light = (row + col) % 2 == 0
                color = light if is_light else dark

                y1 = row * self.square_size
                y2 = y1 + self.square_size
                x1 = col * self.square_size
                x2 = x1 + self.square_size

                board[y1:y2, x1:x2, 0] = color[0]
                board[y1:y2, x1:x2, 1] = color[1]
                board[y1:y2, x1:x2, 2] = color[2]
                board[y1:y2, x1:x2, 3] = 255

        # Transfer to GPU
        self.board_texture = xp.asarray(board) if GPU_AVAILABLE else board

        # Pre-render background
        bg = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        bg[:, :, 0] = THEME['background'][0]
        bg[:, :, 1] = THEME['background'][1]
        bg[:, :, 2] = THEME['background'][2]
        bg[:, :, 3] = 255
        self.background = xp.asarray(bg) if GPU_AVAILABLE else bg

    def _load_pieces(self):
        """Load piece images and transfer to GPU"""
        self.pieces = {}
        self.piece_size = int(self.square_size * PIECE_SCALE)

        piece_map = {
            ('w', 'K'): 'wK.png', ('w', 'Q'): 'wQ.png', ('w', 'R'): 'wR.png',
            ('w', 'B'): 'wB.png', ('w', 'N'): 'wN.png', ('w', 'P'): 'wP.png',
            ('b', 'K'): 'bK.png', ('b', 'Q'): 'bQ.png', ('b', 'R'): 'bR.png',
            ('b', 'B'): 'bB.png', ('b', 'N'): 'bN.png', ('b', 'P'): 'bP.png',
        }

        for key, filename in piece_map.items():
            path = self.assets_dir / filename
            if path.exists():
                img = Image.open(path).convert('RGBA')
                img = img.resize((self.piece_size, self.piece_size), Image.LANCZOS)
                arr = np.array(img, dtype=np.uint8)
                self.pieces[key] = xp.asarray(arr) if GPU_AVAILABLE else arr

    def _square_to_pixel(self, square: int) -> Tuple[int, int]:
        """Convert chess square to pixel coordinates"""
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)

        if self.flip_board:
            col = 7 - file_idx
            row = rank_idx
        else:
            col = file_idx
            row = 7 - rank_idx

        x = self.margin_x + col * self.square_size + (self.square_size - self.piece_size) // 2
        y = self.margin_y + row * self.square_size + (self.square_size - self.piece_size) // 2

        return x, y

    def _alpha_composite_gpu(self, background, overlay, x, y):
        """GPU-accelerated alpha compositing"""
        h, w = overlay.shape[:2]

        # Bounds checking
        if x < 0 or y < 0 or x + w > background.shape[1] or y + h > background.shape[0]:
            # Clip to valid region
            src_x1, src_y1 = max(0, -x), max(0, -y)
            src_x2 = min(w, background.shape[1] - x)
            src_y2 = min(h, background.shape[0] - y)
            dst_x1, dst_y1 = max(0, x), max(0, y)
            dst_x2 = dst_x1 + (src_x2 - src_x1)
            dst_y2 = dst_y1 + (src_y2 - src_y1)

            if src_x2 <= src_x1 or src_y2 <= src_y1:
                return

            overlay = overlay[src_y1:src_y2, src_x1:src_x2]
            x, y = dst_x1, dst_y1
            h, w = overlay.shape[:2]

        # Extract alpha channel and normalize
        alpha = overlay[:, :, 3:4].astype(xp.float32) / 255.0

        # Blend: out = overlay * alpha + background * (1 - alpha)
        bg_region = background[y:y+h, x:x+w].astype(xp.float32)
        fg = overlay[:, :, :3].astype(xp.float32)

        blended = fg * alpha + bg_region[:, :, :3] * (1 - alpha)
        background[y:y+h, x:x+w, :3] = blended.astype(xp.uint8)
        background[y:y+h, x:x+w, 3] = 255

    def render_frame(self, board: chess.Board,
                     moving_piece=None, from_sq=None, to_sq=None,
                     progress=0.0, highlights=None) -> np.ndarray:
        """Render a single frame - GPU accelerated"""

        # Start with background
        frame = self.background.copy()

        # Composite board
        frame[self.margin_y:self.margin_y + self.board_size,
              self.margin_x:self.margin_x + self.board_size] = self.board_texture

        # Draw highlights if any
        if highlights:
            for hl in highlights:
                self._draw_highlight(frame, hl.from_square, hl.color)
                self._draw_highlight(frame, hl.to_square, hl.color)

        # Draw static pieces
        for sq in chess.SQUARES:
            if from_sq is not None and sq == from_sq:
                continue  # Skip moving piece's origin

            piece = board.piece_at(sq)
            if piece is None:
                continue

            key = ('w' if piece.color == chess.WHITE else 'b', piece.symbol().upper())
            if key not in self.pieces:
                continue

            x, y = self._square_to_pixel(sq)
            self._alpha_composite_gpu(frame, self.pieces[key], x, y)

        # Draw moving piece with interpolation
        if moving_piece is not None and from_sq is not None and to_sq is not None:
            key = ('w' if moving_piece.color == chess.WHITE else 'b',
                   moving_piece.symbol().upper())

            if key in self.pieces:
                x1, y1 = self._square_to_pixel(from_sq)
                x2, y2 = self._square_to_pixel(to_sq)

                # Apply easing
                t = self._get_eased_progress(progress)
                x = int(x1 * (1 - t) + x2 * t)
                y = int(y1 * (1 - t) + y2 * t)

                self._alpha_composite_gpu(frame, self.pieces[key], x, y)

        # Transfer back to CPU for ffmpeg
        if GPU_AVAILABLE:
            return cp.asnumpy(frame)
        return frame

    def _draw_highlight(self, frame, square: int, color: Tuple[int, int, int, int]):
        """Draw square highlight"""
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)

        if self.flip_board:
            col = 7 - file_idx
            row = rank_idx
        else:
            col = file_idx
            row = 7 - rank_idx

        x1 = self.margin_x + col * self.square_size
        y1 = self.margin_y + row * self.square_size
        x2 = x1 + self.square_size
        y2 = y1 + self.square_size

        # Semi-transparent overlay
        alpha = color[3] / 255.0
        region = frame[y1:y2, x1:x2]

        for c in range(3):
            region[:, :, c] = (region[:, :, c] * (1 - alpha) +
                              color[c] * alpha).astype(xp.uint8)


class FastPipeline:
    """Optimized video generation pipeline"""

    def __init__(self, assets_dir='./assets', width=1080, height=1920, fps=60):
        self.renderer = GPURenderer(
            assets_dir=assets_dir,
            width=width,
            height=height,
            fps=fps
        )
        self.width = width
        self.height = height
        self.fps = fps

    def render_game(self, game: chess.pgn.Game, output_path: str):
        """Render entire game to video file"""
        moves = list(game.mainline_moves())

        # Find ffmpeg
        ffmpeg_path = 'ffmpeg'

        # NVENC H.264 encoding
        cmd = [
            ffmpeg_path, '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'rgba',
            '-s', f'{self.width}x{self.height}',
            '-r', str(self.fps),
            '-i', '-',
            '-c:v', 'h264_nvenc',
            '-preset', 'p4',
            '-rc', 'vbr',
            '-cq', '23',
            '-b:v', '10M',
            '-maxrate', '15M',
            '-pix_fmt', 'yuv420p',
            output_path
        ]

        print(f"Rendering {len(moves)} moves at {self.fps} FPS...")
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        board = game.board()
        frames_per_move = int(self.renderer.move_seconds * self.fps)

        # Initial pause
        frame = self.renderer.render_frame(board)
        for _ in range(self.fps):  # 1 second
            proc.stdin.write(frame.tobytes())

        # Render moves
        for move_idx, move in enumerate(moves):
            from_sq = move.from_square
            to_sq = move.to_square
            moving_piece = board.piece_at(from_sq)

            # Animate move
            for f in range(frames_per_move):
                progress = f / max(1, frames_per_move - 1)
                frame = self.renderer.render_frame(
                    board,
                    moving_piece=moving_piece,
                    from_sq=from_sq,
                    to_sq=to_sq,
                    progress=progress
                )
                proc.stdin.write(frame.tobytes())

            board.push(move)

            if (move_idx + 1) % 10 == 0:
                print(f"  Move {move_idx + 1}/{len(moves)}")

        # Final pause
        frame = self.renderer.render_frame(board)
        for _ in range(self.fps * 2):  # 2 seconds
            proc.stdin.write(frame.tobytes())

        proc.stdin.close()
        proc.wait()
        print(f"Done: {output_path}")


if __name__ == "__main__":
    # Test
    import chess.pgn
    from io import StringIO

    pgn = """[Event "Test"]
1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 1/2-1/2"""

    game = chess.pgn.read_game(StringIO(pgn))

    pipeline = FastPipeline(
        assets_dir='./assets',
        width=1080,
        height=1920,
        fps=60
    )

    pipeline.render_game(game, 'test_gpu.mp4')
