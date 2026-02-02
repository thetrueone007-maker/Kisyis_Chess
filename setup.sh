#!/bin/bash
# Setup script for Kisyis Chess TikTok Video Generator

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "♟️  KISYIS CHESS - Setup Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo "⚠️  Unsupported OS: $OSTYPE"
    exit 1
fi

echo ""
echo "[1/6] Checking system dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found"
    if [[ "$OS" == "linux" ]]; then
        echo "Install with: sudo pacman -S ffmpeg  (Arch/Manjaro)"
        echo "          or: sudo apt install ffmpeg  (Ubuntu/Debian)"
    else
        echo "Install with: brew install ffmpeg"
    fi
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ FFmpeg: $(ffmpeg -version | head -n1)"
fi

# Check Stockfish
if ! command -v stockfish &> /dev/null; then
    echo "⚠️  Stockfish not found (optional but recommended)"
    if [[ "$OS" == "linux" ]]; then
        echo "Install with: sudo pacman -S stockfish  (Arch/Manjaro)"
        echo "          or: sudo apt install stockfish  (Ubuntu/Debian)"
    else
        echo "Install with: brew install stockfish"
    fi
    read -p "Continue without Stockfish? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Stockfish: $(stockfish --version | head -n1)"
fi

echo ""
echo "[2/6] Setting up Python virtual environment..."

if [ ! -d "venv_chess" ]; then
    python3 -m venv venv_chess
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

source venv_chess/bin/activate

echo ""
echo "[3/6] Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

echo ""
echo "[4/6] Creating directory structure..."
mkdir -p ouvertures renders tiktok_ready temp audio/music audio/sfx logs
echo "✅ Directories created"

echo ""
echo "[5/6] Verifying assets..."
if [ -d "assets" ] && [ "$(ls -A assets/*.png 2>/dev/null)" ]; then
    echo "✅ Chess piece assets found ($(ls assets/*.png | wc -l) files)"
else
    echo "⚠️  Chess piece assets missing in ./assets/"
    echo "   Make sure you have: wK.png, wQ.png, wR.png, wB.png, wN.png, wP.png"
    echo "                       bK.png, bQ.png, bR.png, bB.png, bN.png, bP.png"
fi

echo ""
echo "[6/6] Configuration..."

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY not set"
    echo ""
    read -p "Do you have an Anthropic API key? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your API key: " api_key
        echo ""
        echo "export ANTHROPIC_API_KEY=\"$api_key\"" >> ~/.bashrc
        export ANTHROPIC_API_KEY="$api_key"
        echo "✅ API key saved to ~/.bashrc"
    else
        echo "💡 Get a key at: https://console.anthropic.com/"
        echo "   The system will work without it, but with basic comments only"
    fi
else
    echo "✅ ANTHROPIC_API_KEY is set"
fi

# Check for music
if [ "$(ls -A audio/music/*.mp3 2>/dev/null)" ]; then
    echo "✅ Background music found ($(ls audio/music/*.mp3 | wc -l) files)"
else
    echo "⚠️  No background music found"
    echo ""
    echo "💡 Download free music from:"
    echo "   - YouTube Audio Library: https://www.youtube.com/audiolibrary"
    echo "   - Pixabay Music: https://pixabay.com/music/"
    echo "   - Free Music Archive: https://freemusicarchive.org/"
    echo ""
    echo "   Then place MP3 files in: ./audio/music/"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SETUP COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Quick Start:"
echo ""
echo "   # Activate virtual environment"
echo "   source venv_chess/bin/activate"
echo ""
echo "   # Generate 1 test video"
echo "   python main_pipeline.py --count 1"
echo ""
echo "   # Start automatic production (10 videos/day)"
echo "   python scheduler.py --videos-per-day 10"
echo ""
echo "📖 Full documentation: README.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
