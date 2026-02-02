#!/usr/bin/env python3
"""
Enhanced chess renderer with professional features:
- Evaluation bar (Stockfish-powered)
- Move highlights and arrows
- Text commentary
- Support for audio integration
"""

import sys
import math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PySide6.QtGui import QImage, QPainter, QPixmap, QColor, QFont, QPen, QPainterPath
from PySide6.QtCore import QPointF, Qt, QRectF
import chess
import chess.pgn

# Import base renderer
from chess_com_like_pyside_6 import Renderer, BACKGROUND_COLOR, LIGHT_COLOR, DARK_COLOR


@dataclass
class MoveHighlight:
    """Visual highlight for a move"""
    from_square: int
    to_square: int
    color: Tuple[int, int, int, int]  # RGBA
    width: int = 8
    draw_arrow: bool = True


@dataclass
class TextComment:
    """Text commentary to display"""
    text: str
    move_number: int
    duration_frames: int = 60  # How long to show


class EnhancedRenderer(Renderer):
    """Extended renderer with professional features"""

    def __init__(self, *args, show_eval_bar=True, show_highlights=True,
                 show_comments=True, opening_mode=False, flip_board=False, **kwargs):
        super().__init__(*args, flip_board=flip_board, **kwargs)

        self.show_eval_bar = show_eval_bar
        self.show_highlights = show_highlights
        self.show_comments = show_comments
        self.opening_mode = opening_mode  # Disable move annotations in opening mode

        # Previous eval for smooth interpolation
        self.prev_eval = 0.0

        # Colors for highlights
        self.highlight_colors = {
            'brilliant': (255, 215, 0, 180),      # Gold
            'great': (100, 255, 100, 150),        # Green
            'blunder': (255, 50, 50, 150),        # Red
            'miss': (255, 165, 0, 150),           # Orange
            'critical': (138, 43, 226, 150),      # Purple
            'default': (255, 255, 100, 120)       # Yellow
        }

    def draw_evaluation_bar(self, painter, eval_cp: float, interpolation: float = 0.3):
        """Draw the evaluation bar - ALWAYS from white's perspective"""
        if not self.show_eval_bar:
            return

        # Smooth interpolation for fluid transitions
        eval_cp = self.prev_eval * (1 - interpolation) + eval_cp * interpolation
        self.prev_eval = eval_cp

        # Position bar in the LEFT margin (before the board starts)
        bar_width = int(self.width * 0.035)  # Fixed width
        bar_x = max(10, self.margin_x - bar_width - 40)  # 10px more to the left
        bar_y = self.margin_y
        bar_height = self.board_size

        # Clamp evaluation
        max_eval = 500  # Centipawns
        eval_clamped = max(-max_eval, min(max_eval, eval_cp))

        # Calculate white's advantage percentage (0 to 1)
        # ALWAYS from white's perspective: positive = white winning
        white_ratio = (eval_clamped + max_eval) / (2 * max_eval)

        # Draw background
        painter.fillRect(
            int(bar_x),
            int(bar_y),
            bar_width,
            int(bar_height),
            QColor(50, 50, 50)
        )

        # Calculate portion heights
        black_height = int(bar_height * (1 - white_ratio))
        white_height = int(bar_height * white_ratio)

        if self.flip_board:
            # Black's perspective: white at top, black at bottom
            # Draw white's portion (top)
            painter.fillRect(
                int(bar_x),
                int(bar_y),
                bar_width,
                white_height,
                QColor(250, 250, 250)
            )
            # Draw black's portion (bottom)
            painter.fillRect(
                int(bar_x),
                int(bar_y + white_height),
                bar_width,
                black_height,
                QColor(30, 30, 30)
            )
        else:
            # White's perspective: black at top, white at bottom
            # Draw black's portion (top)
            painter.fillRect(
                int(bar_x),
                int(bar_y),
                bar_width,
                black_height,
                QColor(30, 30, 30)
            )
            # Draw white's portion (bottom)
            painter.fillRect(
                int(bar_x),
                int(bar_y + black_height),
                bar_width,
                white_height,
                QColor(250, 250, 250)
            )

        # Draw center line
        center_y = bar_y + bar_height / 2
        painter.setPen(QPen(QColor(120, 120, 120), 2))
        painter.drawLine(
            int(bar_x),
            int(center_y),
            int(bar_x + bar_width),
            int(center_y)
        )

        # Draw evaluation text
        eval_text = self._format_eval(eval_cp)
        font = QFont("Arial", max(16, int(self.width * 0.020)), QFont.Bold)
        painter.setFont(font)

        # Position text based on advantage
        text_y = bar_y + black_height
        if white_ratio > 0.5:
            painter.setPen(QColor(10, 10, 10))
            text_y = min(text_y + 30, bar_y + bar_height - 15)
        else:
            painter.setPen(QColor(250, 250, 250))
            text_y = max(text_y - 15, bar_y + 25)

        # Center the text
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(eval_text)
        painter.drawText(
            int(bar_x + (bar_width - text_width) / 2),
            int(text_y),
            eval_text
        )

    def _format_eval(self, cp: float) -> str:
        """Format centipawn evaluation"""
        if abs(cp) > 5000:
            mate_in = int((10000 - abs(cp)) / 100)
            return f"M{mate_in}" if cp > 0 else f"-M{mate_in}"
        else:
            return f"{cp/100:+.1f}"

    def draw_move_annotation(self, painter, move_analysis, board_turn):
        """Draw Chess.com-style move annotation badge"""
        if not move_analysis or self.opening_mode:
            return  # Skip annotations in opening mode (theory moves)

        # Check if this is checkmate (eval is extreme)
        is_checkmate = abs(move_analysis.eval_after) > 9000

        # Determine annotation type and style
        if is_checkmate:
            text = "CHECKMATE!"
            bg_color = QColor(218, 165, 32)  # Gold
            icon = "#"
        elif move_analysis.is_brilliant:
            text = "BRILLIANT!!"
            bg_color = QColor(26, 188, 156)  # Turquoise
            icon = "!!"
        elif move_analysis.is_blunder:
            text = "BLUNDER"
            bg_color = QColor(231, 76, 60)   # Red
            icon = "??"
        elif abs(move_analysis.eval_change) > 100 and move_analysis.eval_change > 0:
            text = "GREAT MOVE"
            bg_color = QColor(46, 204, 113)  # Green
            icon = "!"
        elif abs(move_analysis.eval_change) > 50 and move_analysis.eval_change < -50:
            text = "MISTAKE"  # Shorter than "INACCURACY"
            bg_color = QColor(241, 196, 15)  # Yellow/Orange
            icon = "?!"
        elif move_analysis.move == move_analysis.best_move:
            text = "BEST"
            bg_color = QColor(52, 152, 219)  # Blue
            icon = "✓"
        else:
            return  # No annotation for normal moves

        # Position badge in top-right corner of board
        badge_width = int(self.width * 0.25)
        badge_height = int(self.height * 0.045)
        badge_x = self.margin_x + self.board_size - badge_width - 20
        badge_y = self.margin_y + 20

        # Draw badge background with rounded corners
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(
            int(badge_x), int(badge_y),
            badge_width, badge_height,
            10, 10
        )

        # Draw badge text
        font = QFont("Arial", max(18, int(self.width * 0.022)), QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))

        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(text)
        text_x = badge_x + (badge_width - text_width) / 2
        text_y = badge_y + badge_height / 2 + fm.height() / 3

        painter.drawText(
            int(text_x),
            int(text_y),
            text
        )

        # Draw icon on left side of badge
        icon_font = QFont("Arial", max(22, int(self.width * 0.028)), QFont.Bold)
        painter.setFont(icon_font)
        painter.drawText(
            int(badge_x + 10),
            int(text_y),
            icon
        )

    def draw_move_arrow(self, painter, from_sq: int, to_sq: int,
                       color: Tuple[int, int, int, int], width: int = 8):
        """Draw an arrow from one square to another"""
        if not self.show_highlights:
            return

        # Get center points
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

        # Calculate arrow
        dx = to_center.x() - from_center.x()
        dy = to_center.y() - from_center.y()
        length = math.sqrt(dx*dx + dy*dy)

        if length < 1:
            return

        # Shorten arrow to not overlap pieces
        shorten = self.square_size * 0.3
        ratio = (length - shorten) / length
        to_center = QPointF(
            from_center.x() + dx * ratio,
            from_center.y() + dy * ratio
        )

        # Draw arrow shaft
        painter.setPen(QPen(QColor(*color), width, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(from_center, to_center)

        # Draw arrowhead
        angle = math.atan2(dy, dx)
        arrow_size = width * 2.5

        p1 = to_center
        p2 = QPointF(
            to_center.x() - arrow_size * math.cos(angle - math.pi/6),
            to_center.y() - arrow_size * math.sin(angle - math.pi/6)
        )
        p3 = QPointF(
            to_center.x() - arrow_size * math.cos(angle + math.pi/6),
            to_center.y() - arrow_size * math.sin(angle + math.pi/6)
        )

        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        path.lineTo(p3)
        path.closeSubpath()

        painter.fillPath(path, QColor(*color))

    def draw_square_highlight(self, painter, square: int,
                              color: Tuple[int, int, int, int]):
        """Highlight a specific square"""
        if not self.show_highlights:
            return

        tl = self.square_top_left(square)
        painter.fillRect(
            int(tl.x()),
            int(tl.y()),
            int(self.square_size),
            int(self.square_size),
            QColor(*color)
        )

    def draw_text_comment(self, painter, comment: str, opacity: float = 1.0):
        """Draw commentary text at the bottom"""
        if not self.show_comments or not comment:
            return

        # Comment box dimensions
        box_height = int(self.height * 0.12)
        box_y = self.height - box_height - 20
        box_x = 20
        box_width = self.width - 40

        # Semi-transparent background
        painter.setOpacity(opacity * 0.85)
        painter.fillRect(box_x, box_y, box_width, box_height, QColor(20, 20, 30))

        # Draw border
        painter.setPen(QPen(QColor(100, 100, 255), 2))
        painter.drawRect(box_x, box_y, box_width, box_height)

        # Draw text
        painter.setOpacity(opacity)
        font_size = max(16, int(self.width * 0.030))
        font = QFont("Helvetica", font_size, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))

        # Word wrap text
        text_rect = QRectF(box_x + 20, box_y + 10, box_width - 40, box_height - 20)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.TextWordWrap, comment)

        painter.setOpacity(1.0)

    def render_enhanced_frame(self, board, piece_positions, title_text, title_phase,
                             title_t, eval_cp=0, highlights: List[MoveHighlight] = None,
                             comment: str = None, comment_opacity: float = 1.0,
                             move_annotation=None):
        """Render a complete frame with all enhancements"""

        qimg = QImage(self.width, self.height, QImage.Format.Format_RGBA8888)
        qimg.fill(QColor(*BACKGROUND_COLOR))
        painter = QPainter(qimg)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        # Draw board
        self.draw_board_background(painter)

        # Draw highlights and arrows BEFORE pieces
        if highlights:
            for hl in highlights:
                # First highlight the squares
                self.draw_square_highlight(painter, hl.from_square,
                                          (hl.color[0], hl.color[1], hl.color[2], 80))
                self.draw_square_highlight(painter, hl.to_square,
                                          (hl.color[0], hl.color[1], hl.color[2], 80))

                # Then draw arrow
                if hl.draw_arrow:
                    self.draw_move_arrow(painter, hl.from_square, hl.to_square,
                                       hl.color, hl.width)

        # Draw pieces
        for sq, data in piece_positions.items():
            pix, px, py, op = data
            if pix is None:
                continue
            painter.setOpacity(op)
            painter.drawPixmap(int(px), int(py), pix)
            painter.setOpacity(1.0)

        # Draw evaluation bar (always from white's perspective)
        self.draw_evaluation_bar(painter, eval_cp)

        # Draw move annotation badge (Brilliant, Blunder, etc.)
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
    print("Enhanced Renderer Module")
    print("This module extends the base renderer with:")
    print("  - Evaluation bar")
    print("  - Move highlights and arrows")
    print("  - Text commentary")
    print("\nUse this with the main pipeline for full automation.")
