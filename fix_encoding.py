#!/usr/bin/env python3
"""Fix emoji encoding issues in Python files for Windows console compatibility."""

import os
import re
from pathlib import Path

def remove_all_emojis(text):
    """Remove all emoji characters from text."""
    # Pattern to match most emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"
        "\u2705\u2714\u2716\u2728\u2764\u2B50\u26A1\u2600-\u26FF"  # misc symbols
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

# Specific replacements - emoji to text
REPLACEMENTS = {
    '\U0001f4ca': '[STATS]',      # chart
    '\U0001f4c8': '[CHART]',      # chart increasing
    '\U0001f4c9': '[CHART]',      # chart decreasing
    '\U0001f4e5': '[INBOX]',      # inbox
    '\U0001f4e6': '[PACKAGE]',    # package
    '\U0001f4e4': '[OUTBOX]',     # outbox
    '\U0001f4dd': '[NOTE]',       # memo
    '\U0001f4d1': '[DOC]',        # bookmark
    '\U0001f4d6': '[BOOK]',       # book
    '\U0001f4a1': '[IDEA]',       # lightbulb
    '\U0001f525': '[FIRE]',       # fire
    '\U0001f3af': '[TARGET]',     # target
    '\U0001f3c6': '[TROPHY]',     # trophy
    '\U0001f389': '[PARTY]',      # party
    '\U0001f38a': '[CONFETTI]',   # confetti
    '\U0001f4aa': '[STRONG]',     # bicep
    '\U0001f9e0': '[BRAIN]',      # brain
    '\U0001f916': '[ROBOT]',      # robot
    '\U0001f680': '[ROCKET]',     # rocket
    '\U0001f440': '[EYES]',       # eyes
    '\U0001f47e': '[ALIEN]',      # alien
    '\U0001f31f': '[GLOW]',       # glowing star
    '\U0001f4ab': '[DIZZY]',      # dizzy
    '\U0001f550': '[CLOCK]',      # clock
    '\U0001f4f1': '[PHONE]',      # phone
    '\U0001f4bb': '[LAPTOP]',     # laptop
    '\U0001f4c2': '[FOLDER]',     # folder
    '\U0001f4ce': '[PIN]',        # pin
    '\U0001f517': '[LINK]',       # link
    '\U0001f510': '[LOCK]',       # lock
    '\U0001f511': '[KEY]',        # key
    '\U0001f512': '[LOCK]',       # lock2
    '\U0001f513': '[UNLOCK]',     # unlock
    '\U0001f527': '[TOOL]',       # wrench
    '\U0001f528': '[HAMMER]',     # hammer
    '\U0001f529': '[NUT]',        # nut
    '\U0001f52e': '[CRYSTAL]',    # crystal ball
    '\U0001f534': '[RED]',        # red circle
    '\U0001f535': '[BLUE]',       # blue circle
    '\U0001f7e2': '[GREEN]',      # green circle
    '\U0001f7e1': '[YELLOW]',     # yellow circle
    '\U0001f7e0': '[ORANGE]',     # orange circle
    '\u2705': '[OK]',             # check mark
    '\u2714': '[OK]',             # check mark
    '\u2716': '[X]',              # cross mark
    '\u274c': '[X]',              # cross mark
    '\u26a0': '[WARN]',           # warning
    '\u2728': '[SPARK]',          # sparkles
    '\u2B50': '[STAR]',           # star
    '\u26a1': '[BOLT]',           # lightning
    '\u2764': '[HEART]',          # heart
    '\u23f0': '[ALARM]',          # alarm
    '\u23f3': '[TIMER]',          # timer
    '\u231b': '[HOURGLASS]',      # hourglass
    '\u267b': '[RECYCLE]',        # recycle
    '\u2699': '[GEAR]',           # gear
    '\u25b6': '[PLAY]',           # play
    '\u23f8': '[PAUSE]',          # pause
    '\u23f9': '[STOP]',           # stop
    '\u23ea': '[REWIND]',         # rewind
    '\u23e9': '[FAST]',           # fast forward
    '\u2139': '[INFO]',           # info
    '\u2753': '[?]',              # question
    '\u2757': '[!]',              # exclamation
    '\u265f': '[PAWN]',           # chess pawn
    '\u265e': '[KNIGHT]',         # chess knight
    '\u2654': '[KING]',           # chess king
    '\u2655': '[QUEEN]',          # chess queen
}

def fix_file(filepath: Path):
    """Fix emoji encoding in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Apply specific replacements first
        for emoji, replacement in REPLACEMENTS.items():
            content = content.replace(emoji, replacement)

        # Remove any remaining emojis
        content = remove_all_emojis(content)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath.name}")
            return True
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
    return False

def main():
    base_dir = Path(__file__).parent
    py_files = list(base_dir.glob('*.py'))

    print(f"Checking {len(py_files)} Python files...")
    fixed = 0
    for f in py_files:
        if fix_file(f):
            fixed += 1

    print(f"\nFixed {fixed} files")

if __name__ == "__main__":
    main()
