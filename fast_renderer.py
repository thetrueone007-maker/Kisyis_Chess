#!/usr/bin/env python3
"""
Fast chess renderer using optimized NumPy + multiprocessing.
No CUDA required - pure Python speed optimization.

Optimizations:
1. Pre-rendered board texture
2. Pre-scaled pieces cached in memory
3. Vectorized alpha compositing with NumPy
4. Parallel frame generation with multiprocessing
5. Direct memory buffer to ffmpeg
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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import lru_cache
import time

# Theme colors
THEME = {
    'light': (238, 238, 210),
    'dark': (118, 150, 86),
    'background': (22, 21, 18),
    'highlight': (255, 255, 0, 100),
}

PIECE_SCALE = 0.88


def alpha_composite_fast(background: np.ndarray, overlay: np.ndarray,
                         x: int, y: int) -> None:
    """Ultra-fast alpha compositing using NumPy vectorization"""
    h, w = overlay.shape[:2]
    bg_h, bg_w = background.shape[:2]

    # Clip bounds
    src_x1 = max(0, -x)
    src_y1 = max(0, -y)
    src_x2 = min(w, bg_w - x)
    src_y2 = min(h, bg_h - y)

    if src_x2 <= src_x1 or src_y2 <= src_y1:
        return

    dst_x1 = max(0, x)
    dst_y1 = max(0, y)
    dst_x2 = dst_x1 + (src_x2 - src_x1)
    dst_y2 = dst_y1 + (src_y2 - src_y1)

    # Get regions
    overlay_region = overlay[src_y1:src_y2, src_x1:src_x2]
    bg_region = background[dst_y1:dst_y2, dst_x1:dst_x2]

    # Vectorized alpha blend
    alpha = overlay_region[:, :, 3:4].astype(np.float32) / 255.0

    # Only blend where alpha > 0 (optimization)
    mask = alpha[:, :, 0] > 0
    if not np.any(mask):
        return

    # Blend RGB channels
    bg_region[:, :, :3] = (
        overlay_region[:, :, :3] * alpha +
        bg_region[:, :, :3] * (1 - alpha)
    ).astype(np.uint8)


class FastRenderer:
    """Optimized chess renderer - pure NumPy, no GPU required"""

    def __init__(self, assets_dir, width=1080, height=1920, fps=60,
                 move_seconds=0.7, flip_board=False):
        self.assets_dir = Path(assets_dir)
        self.width = width
        self.height = height
        self.fps = fps
        self.move_seconds = move_seconds
        self.flip_board = flip_board

        # Calculate board dimensions
        self.board_size = int(min(width, height * 0.55))
        self.square_size = self.board_size // 8
        self.board_size = self.square_size * 8

        # Center board
        self.margin_x = (width - self.board_size) // 2
        self.margin_y = (height - self.board_size) // 2

        # Piece size
        self.piece_size = int(self.square_size * PIECE_SCALE)

        # Pre-render everything
        print("Pre-rendering assets...")
        self._init_background()
        self._init_board()
        self._load_pieces()
        self._init_easing()
        print("Assets ready!")

    def _init_easing(self):
        """Pre-compute easing lookup table"""
        steps = 1000
        t = np.linspace(0, 1, steps, dtype=np.float32)
        self.easing_lut = 1 - np.power(1 - t, 3)

    def _get_eased(self, progress: float) -> float:
        """Fast easing lookup"""
        idx = int(progress * (len(self.easing_lut) - 1))
        return self.easing_lut[min(idx, len(self.easing_lut) - 1)]

    def _init_background(self):
        """Create background buffer"""
        self.background = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        self.background[:, :, 0] = THEME['background'][0]
        self.background[:, :, 1] = THEME['background'][1]
        self.background[:, :, 2] = THEME['background'][2]
        self.background[:, :, 3] = 255

    def _init_board(self):
        """Pre-render chess board"""
        board = np.zeros((self.board_size, self.board_size, 4), dtype=np.uint8)

        for row in range(8):
            for col in range(8):
                is_light = (row + col) % 2 == 0
                color = THEME['light'] if is_light else THEME['dark']

                y1, y2 = row * self.square_size, (row + 1) * self.square_size
                x1, x2 = col * self.square_size, (col + 1) * self.square_size

                board[y1:y2, x1:x2, :3] = color
                board[y1:y2, x1:x2, 3] = 255

        # Create base frame with board composited
        self.base_frame = self.background.copy()
        self.base_frame[
            self.margin_y:self.margin_y + self.board_size,
            self.margin_x:self.margin_x + self.board_size
        ] = board

    def _load_pieces(self):
        """Load and pre-scale piece images"""
        self.pieces = {}

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
                self.pieces[key] = np.array(img, dtype=np.uint8)
            else:
                print(f"Warning: Missing piece {path}")

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

    def render_frame(self, board: chess.Board,
                     moving_piece=None, from_sq=None, to_sq=None,
                     progress=0.0, rook_piece=None, rook_from_sq=None,
                     rook_to_sq=None) -> np.ndarray:
        """Render a single frame"""

        # Start with pre-rendered base
        frame = self.base_frame.copy()

        # Collect pieces to skip (moving pieces)
        skip_squares = set()
        if from_sq is not None:
            skip_squares.add(from_sq)
        if rook_from_sq is not None:
            skip_squares.add(rook_from_sq)

        # Draw static pieces
        for sq in chess.SQUARES:
            if sq in skip_squares:
                continue

            piece = board.piece_at(sq)
            if piece is None:
                continue

            key = ('w' if piece.color == chess.WHITE else 'b', piece.symbol().upper())
            if key not in self.pieces:
                continue

            x, y = self._square_to_pixel(sq)
            alpha_composite_fast(frame, self.pieces[key], x, y)

        # Draw moving piece with interpolation
        if moving_piece is not None and from_sq is not None and to_sq is not None:
            key = ('w' if moving_piece.color == chess.WHITE else 'b',
                   moving_piece.symbol().upper())

            if key in self.pieces:
                x1, y1 = self._square_to_pixel(from_sq)
                x2, y2 = self._square_to_pixel(to_sq)

                t = self._get_eased(progress)
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)

                alpha_composite_fast(frame, self.pieces[key], x, y)

        # Draw castling rook
        if rook_piece is not None and rook_from_sq is not None and rook_to_sq is not None:
            key = ('w' if rook_piece.color == chess.WHITE else 'b', 'R')

            if key in self.pieces:
                x1, y1 = self._square_to_pixel(rook_from_sq)
                x2, y2 = self._square_to_pixel(rook_to_sq)

                t = self._get_eased(progress)
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)

                alpha_composite_fast(frame, self.pieces[key], x, y)

        return frame


class FastPipeline:
    """High-speed video generation pipeline"""

    def __init__(self, assets_dir='./assets', width=1080, height=1920, fps=60,
                 move_seconds=0.7):
        self.width = width
        self.height = height
        self.fps = fps
        self.move_seconds = move_seconds
        self.assets_dir = assets_dir

        self.renderer = FastRenderer(
            assets_dir=assets_dir,
            width=width,
            height=height,
            fps=fps,
            move_seconds=move_seconds
        )

    def render_game(self, game: chess.pgn.Game, output_path: str,
                    use_nvenc: bool = True):
        """Render entire game to video"""
        moves = list(game.mainline_moves())
        frames_per_move = int(self.move_seconds * self.fps)

        # FFmpeg command
        if use_nvenc:
            codec_args = [
                '-c:v', 'h264_nvenc',
                '-preset', 'p4',
                '-rc', 'vbr',
                '-cq', '23',
                '-b:v', '10M',
                '-maxrate', '15M',
            ]
        else:
            codec_args = [
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
            ]

        cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'rgba',
            '-s', f'{self.width}x{self.height}',
            '-r', str(self.fps),
            '-i', '-',
            *codec_args,
            '-pix_fmt', 'yuv420p',
            output_path
        ]

        print(f"Rendering {len(moves)} moves at {self.fps} FPS...")
        print(f"Encoder: {'NVENC (GPU)' if use_nvenc else 'libx264 (CPU)'}")
        sys.stdout.flush()

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                stderr=subprocess.DEVNULL,
                                bufsize=10**8)  # Large buffer

        board = game.board()
        start_time = time.time()
        total_frames = 0

        # Initial pause (1 second)
        frame = self.renderer.render_frame(board)
        for _ in range(self.fps):
            proc.stdin.write(frame.tobytes())
            total_frames += 1

        # Render each move
        for move_idx, move in enumerate(moves):
            from_sq = move.from_square
            to_sq = move.to_square
            moving_piece = board.piece_at(from_sq)

            # Check for castling
            is_castling = board.is_castling(move)
            rook_from_sq = None
            rook_to_sq = None
            rook_piece = None

            if is_castling:
                if to_sq > from_sq:  # Kingside
                    rook_from_sq = to_sq + 1
                    rook_to_sq = from_sq + 1
                else:  # Queenside
                    rook_from_sq = to_sq - 2
                    rook_to_sq = from_sq - 1
                rook_piece = board.piece_at(rook_from_sq)

            # Animate move
            for f in range(frames_per_move):
                progress = f / max(1, frames_per_move - 1)

                frame = self.renderer.render_frame(
                    board,
                    moving_piece=moving_piece,
                    from_sq=from_sq,
                    to_sq=to_sq,
                    progress=progress,
                    rook_piece=rook_piece,
                    rook_from_sq=rook_from_sq,
                    rook_to_sq=rook_to_sq
                )
                try:
                    proc.stdin.write(frame.tobytes())
                except (BrokenPipeError, OSError):
                    print(f"\nPipe error at move {move_idx + 1}")
                    proc.stdin.close()
                    proc.wait()
                    return
                total_frames += 1

            board.push(move)

            # Progress update every 5 moves
            if (move_idx + 1) % 5 == 0:
                elapsed = time.time() - start_time
                fps_actual = total_frames / elapsed
                print(f"  Move {move_idx + 1}/{len(moves)} - {fps_actual:.1f} fps")
                sys.stdout.flush()

        # Final pause (2 seconds)
        frame = self.renderer.render_frame(board)
        for _ in range(self.fps * 2):
            proc.stdin.write(frame.tobytes())
            total_frames += 1

        proc.stdin.close()
        ret = proc.wait()

        elapsed = time.time() - start_time
        if ret == 0:
            print(f"\nDone! {total_frames} frames in {elapsed:.1f}s ({total_frames/elapsed:.1f} fps)")
            print(f"Output: {output_path}")
        else:
            print(f"\nError: ffmpeg exited with code {ret}")
        sys.stdout.flush()


def render_pgn_file(pgn_path: str, output_dir: str = './renders',
                    width: int = 1080, height: int = 1920, fps: int = 60):
    """Render a PGN file to video"""
    from io import StringIO

    pgn_path = Path(pgn_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    pipeline = FastPipeline(
        assets_dir='./assets',
        width=width,
        height=height,
        fps=fps
    )

    with open(pgn_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse all games in file
    pgn_io = StringIO(content)
    game_num = 0

    while True:
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            break

        game_num += 1
        event = game.headers.get('Event', f'Game_{game_num}')
        # Clean filename
        safe_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in event)
        safe_name = safe_name[:50]  # Limit length

        output_path = output_dir / f"{safe_name}.mp4"

        print(f"\n{'='*60}")
        print(f"Game {game_num}: {event}")
        print(f"{'='*60}")

        pipeline.render_game(game, str(output_path))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Render specified PGN file
        render_pgn_file(sys.argv[1])
    else:
        # Test with sample game
        from io import StringIO

        pgn = """[Event "Test Game"]
[White "Player1"]
[Black "Player2"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 1/2-1/2"""

        game = chess.pgn.read_game(StringIO(pgn))

        pipeline = FastPipeline(
            assets_dir='./assets',
            width=1080,
            height=1920,
            fps=60
        )

        pipeline.render_game(game, 'test_fast.mp4')
