#!/usr/bin/env python3
"""
Ultra-quality chess renderer with professional visual effects:
- Piece shadows and depth effects
- Premium board textures
- Smooth gradients and anti-aliasing
- Enhanced evaluation bar
- Professional move highlights
"""

import sys
import math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PySide6.QtGui import (QImage, QPainter, QPixmap, QColor, QFont, QPen, QPainterPath,
                           QLinearGradient, QRadialGradient, QBrush, QConicalGradient)
from PySide6.QtCore import QPointF, Qt, QRectF
import chess
import chess.pgn
from PIL import Image, ImageFilter, ImageEnhance
import io

# Modern premium color schemes
PREMIUM_THEMES = {
    'chess_com': {
        'light': (238, 238, 210),
        'dark': (118, 150, 86),
        'background': (22, 21, 18),
        'accent': (255, 193, 7),
    },
    'lichess': {
        'light': (240, 217, 181),
        'dark': (181, 136, 99),
        'background': (32, 32, 32),
        'accent': (100, 200, 100),
    },
    'modern_blue': {
        'light': (222, 227, 230),
        'dark': (82, 120, 162),
        'background': (15, 23, 42),
        'accent': (56, 189, 248),
    },
    'purple_premium': {
        'light': (240, 232, 255),
        'dark': (126, 87, 194),
        'background': (18, 18, 28),
        'accent': (192, 132, 252),
    }
}

# Select theme
THEME = PREMIUM_THEMES['chess_com']
BACKGROUND_COLOR = THEME['background']
LIGHT_COLOR = THEME['light']
DARK_COLOR = THEME['dark']
ACCENT_COLOR = THEME['accent']

# Rendering settings
PIECE_SCALE = 0.88  # Slightly smaller for better shadow visibility
PIECE_SHADOW_OFFSET = 8
PIECE_SHADOW_BLUR = 12
PIECE_SHADOW_OPACITY = 100
ENABLE_PIECE_SHADOWS = True
ENABLE_BOARD_TEXTURE = True
ENABLE_SQUARE_HIGHLIGHTS = True

PIECE_FILENAME_MAP = {
    ('w','K'): 'wK.png', ('w','Q'): 'wQ.png', ('w','R'): 'wR.png', ('w','B'): 'wB.png', ('w','N'): 'wN.png', ('w','P'): 'wP.png',
    ('b','K'): 'bK.png', ('b','Q'): 'bQ.png', ('b','R'): 'bR.png', ('b','B'): 'bB.png', ('b','N'): 'bN.png', ('b','P'): 'bP.png',
}


@dataclass
class MoveHighlight:
    """Visual highlight for a move"""
    from_square: int
    to_square: int
    color: Tuple[int, int, int, int]
    width: int = 10
    draw_arrow: bool = True


class UltraRenderer:
    """Premium chess renderer with advanced visual effects"""

    def __init__(self, assets_dir, width, height, fps, out_dir, move_seconds=1.0,
                 show_eval_bar=True, show_highlights=True, show_comments=True,
                 opening_mode=False, flip_board=False, theme='chess_com'):
        self.assets_dir = Path(assets_dir)
        self.width = width
        self.height = height
        self.fps = fps
        self.out_dir = Path(out_dir)
        self.move_seconds = move_seconds
        self.flip_board = flip_board

        self.show_eval_bar = show_eval_bar
        self.show_highlights = show_highlights
        self.show_comments = show_comments
        self.opening_mode = opening_mode

        # Apply theme
        if theme in PREMIUM_THEMES:
            self.theme = PREMIUM_THEMES[theme]
        else:
            self.theme = PREMIUM_THEMES['chess_com']

        # Calculate board dimensions
        self.board_size = min(self.width, int(self.height * 0.78))
        self.margin_x = (self.width - self.board_size) // 2
        self.margin_y = int((self.height - self.board_size) * 0.52)
        self.square_size = self.board_size / 8

        # Previous eval for smooth interpolation
        self.prev_eval = 0.0

        # Colors for highlights
        self.highlight_colors = {
            'brilliant': (255, 215, 0, 200),      # Gold
            'great': (46, 204, 113, 180),         # Emerald
            'blunder': (231, 76, 60, 180),        # Red
            'miss': (241, 196, 15, 180),          # Yellow
            'critical': (155, 89, 182, 180),      # Purple
            'default': (52, 152, 219, 150),       # Blue
            'check': (231, 76, 60, 120),          # Red overlay for check
        }

        self._load_piece_images()
        self._create_piece_shadows()

    def _load_piece_images(self):
        """Load and prepare piece images"""
        self.pil_pieces = {}
        for (color, piece), filename in PIECE_FILENAME_MAP.items():
            path = self.assets_dir / filename
            if not path.exists():
                raise FileNotFoundError(f"Missing piece asset: {path}")
            img = Image.open(path).convert("RGBA")
            self.pil_pieces[(color, piece)] = img

    def _create_piece_shadows(self):
        """Pre-create shadow images for pieces"""
        self.pil_shadows = {}
        if not ENABLE_PIECE_SHADOWS:
            return

        for key, img in self.pil_pieces.items():
            # Create shadow from alpha channel
            shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))

            # Extract alpha and create shadow
            alpha = img.split()[3]
            shadow_alpha = alpha.filter(ImageFilter.GaussianBlur(PIECE_SHADOW_BLUR))

            # Apply shadow with reduced opacity
            shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, PIECE_SHADOW_OPACITY))
            shadow_layer.putalpha(shadow_alpha)

            self.pil_shadows[key] = shadow_layer

    def _pil_to_qpixmap_scaled(self, pil_img, target_px):
        """Convert PIL image to QPixmap with high-quality scaling"""
        pil2 = pil_img.resize((int(target_px), int(target_px)), Image.LANCZOS)
        data = pil2.tobytes("raw", "RGBA")
        qim = QImage(data, pil2.width, pil2.height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qim)

    def square_top_left(self, square):
        """Get top-left position of a square"""
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)

        if self.flip_board:
            x = self.margin_x + (7 - file_idx) * self.square_size
            y = self.margin_y + rank_idx * self.square_size
        else:
            x = self.margin_x + file_idx * self.square_size
            y = self.margin_y + (7 - rank_idx) * self.square_size

        return QPointF(x, y)

    def draw_premium_background(self, painter):
        """Draw premium gradient background"""
        # Multi-layer gradient background
        bg = self.theme['background']

        # Main gradient
        gradient = QRadialGradient(self.width / 2, self.height * 0.4, max(self.width, self.height) * 0.8)
        gradient.setColorAt(0, QColor(bg[0] + 25, bg[1] + 25, bg[2] + 25))
        gradient.setColorAt(0.5, QColor(bg[0] + 10, bg[1] + 10, bg[2] + 10))
        gradient.setColorAt(1, QColor(bg[0], bg[1], bg[2]))
        painter.fillRect(0, 0, self.width, self.height, QBrush(gradient))

        # Subtle vignette
        vignette = QRadialGradient(self.width / 2, self.height / 2, max(self.width, self.height) * 0.7)
        vignette.setColorAt(0, QColor(0, 0, 0, 0))
        vignette.setColorAt(1, QColor(0, 0, 0, 80))
        painter.fillRect(0, 0, self.width, self.height, QBrush(vignette))

    def draw_board_frame(self, painter):
        """Draw premium board frame with depth effect"""
        # Outer shadow
        shadow_offset = 15
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 60))
        painter.drawRoundedRect(
            int(self.margin_x - 15 + shadow_offset),
            int(self.margin_y - 15 + shadow_offset),
            int(self.board_size + 30),
            int(self.board_size + 30),
            12, 12
        )

        # Frame gradient
        frame_gradient = QLinearGradient(
            self.margin_x, self.margin_y,
            self.margin_x, self.margin_y + self.board_size
        )
        frame_gradient.setColorAt(0, QColor(80, 65, 50))
        frame_gradient.setColorAt(0.3, QColor(55, 45, 35))
        frame_gradient.setColorAt(0.7, QColor(45, 35, 25))
        frame_gradient.setColorAt(1, QColor(35, 28, 20))

        painter.setBrush(QBrush(frame_gradient))
        painter.drawRoundedRect(
            int(self.margin_x - 15),
            int(self.margin_y - 15),
            int(self.board_size + 30),
            int(self.board_size + 30),
            12, 12
        )

        # Inner border highlight
        painter.setPen(QPen(QColor(120, 100, 80, 100), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(
            int(self.margin_x - 14),
            int(self.margin_y - 14),
            int(self.board_size + 28),
            int(self.board_size + 28),
            11, 11
        )

    def draw_board_squares(self, painter):
        """Draw board squares with premium gradients"""
        light = self.theme['light']
        dark = self.theme['dark']

        for r in range(8):
            for f in range(8):
                x = int(self.margin_x + f * self.square_size)
                y = int(self.margin_y + r * self.square_size)
                size = int(self.square_size) + 1
                is_light = (f + r) % 2 == 0

                base = light if is_light else dark

                # Create subtle gradient for 3D effect
                sq_gradient = QLinearGradient(x, y, x + size, y + size)
                if is_light:
                    sq_gradient.setColorAt(0, QColor(base[0] + 12, base[1] + 12, base[2] + 8))
                    sq_gradient.setColorAt(0.5, QColor(base[0], base[1], base[2]))
                    sq_gradient.setColorAt(1, QColor(base[0] - 15, base[1] - 15, base[2] - 18))
                else:
                    sq_gradient.setColorAt(0, QColor(base[0] + 18, base[1] + 22, base[2] + 12))
                    sq_gradient.setColorAt(0.5, QColor(base[0], base[1], base[2]))
                    sq_gradient.setColorAt(1, QColor(base[0] - 12, base[1] - 15, base[2] - 8))

                painter.fillRect(x, y, size, size, QBrush(sq_gradient))

    def draw_coordinates(self, painter):
        """Draw coordinates with premium styling"""
        coord_font_size = max(16, int(self.square_size * 0.18))
        font = QFont("Segoe UI", coord_font_size, QFont.Bold)
        painter.setFont(font)

        light = self.theme['light']
        dark = self.theme['dark']

        for i in range(8):
            is_light_bottom = ((i + 7) % 2 == 0)
            is_light_side = ((0 + (7 - i)) % 2 == 0) if not self.flip_board else ((0 + i) % 2 == 0)

            # File labels
            file_label = chr(ord('a') + (7 - i) if self.flip_board else ord('a') + i)
            fx = int(self.margin_x + i * self.square_size + self.square_size - coord_font_size - 4)
            fy = int(self.margin_y + self.board_size - 6)

            color = dark if is_light_bottom else light
            # Shadow
            painter.setPen(QColor(0, 0, 0, 50))
            painter.drawText(fx + 1, fy + 1, file_label)
            # Text
            painter.setPen(QColor(color[0], color[1], color[2]))
            painter.drawText(fx, fy, file_label)

            # Rank labels
            rank_label = str(i + 1) if self.flip_board else str(8 - i)
            rx = int(self.margin_x + 5)
            ry = int(self.margin_y + i * self.square_size + coord_font_size + 4)

            color = dark if is_light_side else light
            painter.setPen(QColor(0, 0, 0, 50))
            painter.drawText(rx + 1, ry + 1, rank_label)
            painter.setPen(QColor(color[0], color[1], color[2]))
            painter.drawText(rx, ry, rank_label)

    def draw_evaluation_bar(self, painter, eval_cp: float, interpolation: float = 0.25):
        """Draw premium evaluation bar"""
        if not self.show_eval_bar:
            return

        # Smooth interpolation
        eval_cp = self.prev_eval * (1 - interpolation) + eval_cp * interpolation
        self.prev_eval = eval_cp

        # Bar dimensions
        bar_width = int(self.width * 0.045)
        bar_x = max(20, self.margin_x - bar_width - 45)
        bar_y = self.margin_y
        bar_height = self.board_size

        # Clamp evaluation
        max_eval = 600
        eval_clamped = max(-max_eval, min(max_eval, eval_cp))
        white_ratio = (eval_clamped + max_eval) / (2 * max_eval)

        # Shadow
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 50))
        painter.drawRoundedRect(int(bar_x + 4), int(bar_y + 4), bar_width, int(bar_height), 8, 8)

        # Background
        painter.setBrush(QColor(25, 25, 30))
        painter.drawRoundedRect(int(bar_x), int(bar_y), bar_width, int(bar_height), 8, 8)

        # Calculate portions
        black_height = int(bar_height * (1 - white_ratio))
        white_height = int(bar_height * white_ratio)

        # White portion with gradient
        white_gradient = QLinearGradient(bar_x, 0, bar_x + bar_width, 0)
        white_gradient.setColorAt(0, QColor(245, 245, 245))
        white_gradient.setColorAt(0.5, QColor(255, 255, 255))
        white_gradient.setColorAt(1, QColor(230, 230, 230))

        # Black portion with gradient
        black_gradient = QLinearGradient(bar_x, 0, bar_x + bar_width, 0)
        black_gradient.setColorAt(0, QColor(35, 35, 40))
        black_gradient.setColorAt(0.5, QColor(50, 50, 55))
        black_gradient.setColorAt(1, QColor(30, 30, 35))

        if self.flip_board:
            painter.setBrush(QBrush(white_gradient))
            painter.drawRoundedRect(int(bar_x), int(bar_y), bar_width, white_height, 8, 8)
            painter.setBrush(QBrush(black_gradient))
            painter.drawRoundedRect(int(bar_x), int(bar_y + white_height), bar_width, black_height, 8, 8)
        else:
            painter.setBrush(QBrush(black_gradient))
            painter.drawRoundedRect(int(bar_x), int(bar_y), bar_width, black_height, 8, 8)
            painter.setBrush(QBrush(white_gradient))
            painter.drawRoundedRect(int(bar_x), int(bar_y + black_height), bar_width, white_height, 8, 8)

        # Center line
        center_y = bar_y + bar_height / 2
        painter.setPen(QPen(QColor(80, 80, 90, 200), 3))
        painter.drawLine(int(bar_x), int(center_y), int(bar_x + bar_width), int(center_y))

        # Evaluation text
        eval_text = self._format_eval(eval_cp)
        font = QFont("Segoe UI", max(20, int(self.width * 0.024)), QFont.Bold)
        painter.setFont(font)
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(eval_text)

        text_y = bar_y + black_height
        if white_ratio > 0.5:
            text_y = min(text_y + 38, bar_y + bar_height - 25)
            painter.setPen(QColor(0, 0, 0, 40))
            painter.drawText(int(bar_x + (bar_width - text_width) / 2 + 1), int(text_y + 1), eval_text)
            painter.setPen(QColor(20, 20, 25))
        else:
            text_y = max(text_y - 20, bar_y + 35)
            painter.setPen(QColor(255, 255, 255, 40))
            painter.drawText(int(bar_x + (bar_width - text_width) / 2 + 1), int(text_y + 1), eval_text)
            painter.setPen(QColor(250, 250, 255))

        painter.drawText(int(bar_x + (bar_width - text_width) / 2), int(text_y), eval_text)

    def _format_eval(self, cp: float) -> str:
        """Format evaluation display"""
        if abs(cp) > 5000:
            mate_in = int((10000 - abs(cp)) / 100)
            return f"M{mate_in}" if cp > 0 else f"-M{mate_in}"
        else:
            return f"{cp/100:+.1f}"

    def draw_move_arrow(self, painter, from_sq: int, to_sq: int,
                       color: Tuple[int, int, int, int], width: int = 12):
        """Draw premium move arrow"""
        if not self.show_highlights:
            return

        from_tl = self.square_top_left(from_sq)
        to_tl = self.square_top_left(to_sq)

        from_center = QPointF(
            from_tl.x() + self.square_size / 2,
            from_tl.y() + self.square_size / 2
        )
        to_center = QPointF(
            to_tl.x() + self.square_size / 2,
            to_tl.y() + self.square_size / 2
        )

        dx = to_center.x() - from_center.x()
        dy = to_center.y() - from_center.y()
        length = math.sqrt(dx*dx + dy*dy)

        if length < 1:
            return

        # Shorten arrow
        shorten = self.square_size * 0.35
        ratio = (length - shorten) / length
        to_center = QPointF(
            from_center.x() + dx * ratio,
            from_center.y() + dy * ratio
        )

        # Draw shadow
        painter.setPen(QPen(QColor(0, 0, 0, 60), width + 4, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(
            QPointF(from_center.x() + 3, from_center.y() + 3),
            QPointF(to_center.x() + 3, to_center.y() + 3)
        )

        # Draw arrow shaft
        painter.setPen(QPen(QColor(*color), width, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(from_center, to_center)

        # Draw arrowhead
        angle = math.atan2(dy, dx)
        arrow_size = width * 2.2

        p1 = to_center
        p2 = QPointF(
            to_center.x() - arrow_size * math.cos(angle - math.pi/5),
            to_center.y() - arrow_size * math.sin(angle - math.pi/5)
        )
        p3 = QPointF(
            to_center.x() - arrow_size * math.cos(angle + math.pi/5),
            to_center.y() - arrow_size * math.sin(angle + math.pi/5)
        )

        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        path.lineTo(p3)
        path.closeSubpath()

        painter.fillPath(path, QColor(*color))

    def draw_square_highlight(self, painter, square: int, color: Tuple[int, int, int, int]):
        """Draw square highlight with glow effect"""
        if not self.show_highlights:
            return

        tl = self.square_top_left(square)

        # Draw highlight
        painter.fillRect(
            int(tl.x()),
            int(tl.y()),
            int(self.square_size),
            int(self.square_size),
            QColor(*color)
        )

    def draw_move_annotation(self, painter, move_analysis, board_turn):
        """Draw move annotation badge"""
        if not move_analysis or self.opening_mode:
            return

        is_checkmate = abs(move_analysis.eval_after) > 9000

        if is_checkmate:
            text, bg = "CHECKMATE!", QColor(255, 193, 7)
            accent = QColor(255, 220, 100)
        elif move_analysis.is_brilliant:
            text, bg = "BRILLIANT!!", QColor(26, 188, 156)
            accent = QColor(80, 220, 190)
        elif move_analysis.is_blunder:
            text, bg = "BLUNDER", QColor(220, 53, 69)
            accent = QColor(255, 100, 100)
        elif abs(move_analysis.eval_change) > 100 and move_analysis.eval_change > 0:
            text, bg = "GREAT MOVE", QColor(40, 167, 69)
            accent = QColor(100, 200, 120)
        elif abs(move_analysis.eval_change) > 50 and move_analysis.eval_change < -50:
            text, bg = "MISTAKE", QColor(255, 152, 0)
            accent = QColor(255, 190, 80)
        elif move_analysis.move == move_analysis.best_move:
            text, bg = "BEST", QColor(0, 123, 255)
            accent = QColor(80, 170, 255)
        else:
            return

        # Badge dimensions
        badge_width = int(self.width * 0.30)
        badge_height = int(self.height * 0.052)
        badge_x = self.margin_x + self.board_size - badge_width - 20
        badge_y = self.margin_y + 20
        radius = 14

        # Shadow
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 90))
        painter.drawRoundedRect(int(badge_x + 5), int(badge_y + 5), badge_width, badge_height, radius, radius)

        # Gradient background
        gradient = QLinearGradient(badge_x, badge_y, badge_x, badge_y + badge_height)
        gradient.setColorAt(0, accent)
        gradient.setColorAt(0.4, bg)
        gradient.setColorAt(1, bg.darker(120))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(int(badge_x), int(badge_y), badge_width, badge_height, radius, radius)

        # Border
        painter.setPen(QPen(QColor(255, 255, 255, 80), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(int(badge_x), int(badge_y), badge_width, badge_height, radius, radius)

        # Text
        font = QFont("Segoe UI", max(22, int(self.width * 0.026)), QFont.Bold)
        painter.setFont(font)
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(text)
        text_x = badge_x + (badge_width - text_width) / 2
        text_y = badge_y + badge_height / 2 + fm.height() / 3

        painter.setPen(QColor(0, 0, 0, 120))
        painter.drawText(int(text_x + 2), int(text_y + 2), text)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(int(text_x), int(text_y), text)

    def draw_text_comment(self, painter, comment: str, opacity: float = 1.0):
        """Draw commentary with premium styling"""
        if not self.show_comments or not comment:
            return

        box_height = int(self.height * 0.12)
        box_y = self.height - box_height - 40
        box_x = 40
        box_width = self.width - 80
        radius = 18

        painter.setOpacity(opacity)

        # Shadow
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, int(110 * opacity)))
        painter.drawRoundedRect(box_x + 6, box_y + 6, box_width, box_height, radius, radius)

        # Background gradient
        gradient = QLinearGradient(box_x, box_y, box_x, box_y + box_height)
        gradient.setColorAt(0, QColor(35, 35, 45, 245))
        gradient.setColorAt(1, QColor(22, 22, 28, 250))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(box_x, box_y, box_width, box_height, radius, radius)

        # Accent border
        accent = self.theme['dark']
        accent_gradient = QLinearGradient(box_x, box_y, box_x + box_width, box_y)
        accent_gradient.setColorAt(0, QColor(accent[0], accent[1], accent[2]))
        accent_gradient.setColorAt(0.5, QColor(accent[0] + 30, accent[1] + 30, accent[2] + 15))
        accent_gradient.setColorAt(1, QColor(accent[0], accent[1], accent[2]))
        painter.setPen(QPen(QBrush(accent_gradient), 4))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(box_x, box_y, box_width, box_height, radius, radius)

        # Text
        font_size = max(20, int(self.width * 0.034))
        font = QFont("Segoe UI", font_size, QFont.Bold)
        painter.setFont(font)

        text_rect = QRectF(box_x + 30, box_y + 18, box_width - 60, box_height - 36)

        painter.setPen(QColor(0, 0, 0, 100))
        shadow_rect = QRectF(text_rect.x() + 2, text_rect.y() + 2, text_rect.width(), text_rect.height())
        painter.drawText(shadow_rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, comment)

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, comment)

        painter.setOpacity(1.0)

    def draw_title(self, painter, text, phase, t):
        """Draw title with premium effects"""
        if phase == 'big':
            size = max(20, int(self.width * 0.11))
        elif phase == 'shrinking':
            t = max(0.0, min(1.0, t))
            big_size = int(self.width * 0.11)
            small_size = int(self.width * 0.05)
            size = int(big_size*(1-t) + small_size*t)
        else:
            size = int(self.width * 0.05)

        font = QFont("Segoe UI", size, QFont.Bold)
        painter.setFont(font)
        fm = painter.fontMetrics()
        w = fm.horizontalAdvance(text)
        h = fm.height()

        if phase == 'big':
            x = (self.width - w) / 2
            y = (self.margin_y / 2) + h/2
        elif phase == 'shrinking':
            start_x = (self.width - w) / 2
            start_y = (self.margin_y / 2) + h/2
            end_x = self.margin_x + 10
            end_y = self.margin_y - h - 25
            x = start_x*(1-t) + end_x*t
            y = start_y*(1-t) + end_y*t
        else:
            x = self.margin_x + 10
            y = self.margin_y - 25

        # Shadow
        painter.setPen(QColor(0, 0, 0, 130))
        painter.drawText(int(x + 4), int(y + 4), text)

        # Main text
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(int(x), int(y), text)

    def compose_piece_positions(self, board, moving_piece=None, from_sq=None, to_sq=None,
                                progress=0.0, capture_sq=None, capture_fade=1.0,
                                rook_piece=None, rook_from_sq=None, rook_to_sq=None):
        """Compose piece positions with shadows"""
        positions = {}
        piece_px = int(self.square_size * PIECE_SCALE)
        qpix_cache = {}
        shadow_cache = {}

        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p is None:
                continue
            if from_sq is not None and sq == from_sq:
                continue
            if rook_from_sq is not None and sq == rook_from_sq:
                continue

            key = ('w' if p.color == chess.WHITE else 'b', p.symbol().upper())

            if key not in qpix_cache:
                pil = self.pil_pieces.get(key)
                if pil is None:
                    continue
                qpix_cache[key] = self._pil_to_qpixmap_scaled(pil, piece_px)
                if key in self.pil_shadows:
                    shadow_cache[key] = self._pil_to_qpixmap_scaled(self.pil_shadows[key], piece_px)

            pix = qpix_cache[key]
            shadow = shadow_cache.get(key)
            tl = self.square_top_left(sq)
            posx = tl.x() + (self.square_size - pix.width())/2
            posy = tl.y() + (self.square_size - pix.height())/2
            opacity = 1.0
            if capture_sq is not None and sq == capture_sq:
                opacity = capture_fade
            positions[sq] = (pix, posx, posy, opacity, shadow)

        # Animate moving piece
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
                if key in self.pil_shadows:
                    shadow_cache[key] = self._pil_to_qpixmap_scaled(self.pil_shadows[key], piece_px)

            pix = qpix_cache[key]
            shadow = shadow_cache.get(key)
            positions[to_sq] = (pix, curx, cury, 1.0, shadow)

        # Animate rook for castling
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
                if key in self.pil_shadows:
                    shadow_cache[key] = self._pil_to_qpixmap_scaled(self.pil_shadows[key], piece_px)

            pix = qpix_cache[key]
            shadow = shadow_cache.get(key)
            positions[rook_to_sq] = (pix, curx, cury, 1.0, shadow)

        return positions

    def render_enhanced_frame(self, board, piece_positions, title_text, title_phase,
                             title_t, eval_cp=0, highlights: List[MoveHighlight] = None,
                             comment: str = None, comment_opacity: float = 1.0,
                             move_annotation=None):
        """Render complete frame with all premium effects"""

        qimg = QImage(self.width, self.height, QImage.Format.Format_RGBA8888)
        qimg.fill(QColor(*self.theme['background']))
        painter = QPainter(qimg)
        painter.setRenderHints(
            QPainter.Antialiasing |
            QPainter.SmoothPixmapTransform |
            QPainter.TextAntialiasing
        )

        # Draw premium background
        self.draw_premium_background(painter)

        # Draw board frame
        self.draw_board_frame(painter)

        # Draw board squares
        self.draw_board_squares(painter)

        # Draw coordinates
        self.draw_coordinates(painter)

        # Draw highlights
        if highlights:
            for hl in highlights:
                self.draw_square_highlight(painter, hl.from_square,
                                          (hl.color[0], hl.color[1], hl.color[2], 90))
                self.draw_square_highlight(painter, hl.to_square,
                                          (hl.color[0], hl.color[1], hl.color[2], 90))
                if hl.draw_arrow:
                    self.draw_move_arrow(painter, hl.from_square, hl.to_square,
                                        hl.color, hl.width)

        # Draw piece shadows first
        if ENABLE_PIECE_SHADOWS:
            for sq, data in piece_positions.items():
                if len(data) >= 5:
                    pix, px, py, op, shadow = data
                    if shadow is not None:
                        painter.setOpacity(op * 0.6)
                        painter.drawPixmap(int(px + PIECE_SHADOW_OFFSET),
                                          int(py + PIECE_SHADOW_OFFSET), shadow)
                        painter.setOpacity(1.0)

        # Draw pieces
        for sq, data in piece_positions.items():
            pix = data[0]
            px, py, op = data[1], data[2], data[3]
            if pix is None:
                continue
            painter.setOpacity(op)
            painter.drawPixmap(int(px), int(py), pix)
            painter.setOpacity(1.0)

        # Draw evaluation bar
        self.draw_evaluation_bar(painter, eval_cp)

        # Draw move annotation
        if move_annotation:
            self.draw_move_annotation(painter, move_annotation, board.turn)

        # Draw title
        self.draw_title(painter, title_text, title_phase, title_t)

        # Draw comment
        if comment:
            self.draw_text_comment(painter, comment, comment_opacity)

        painter.end()
        return qimg


if __name__ == "__main__":
    print("Ultra-Quality Chess Renderer")
    print("Features:")
    print("  - Premium gradient backgrounds")
    print("  - Piece shadows with blur")
    print("  - High-quality board textures")
    print("  - Smooth move animations")
    print("  - Professional evaluation bar")
