#!/bin/bash
# AI Daily News - local run script

set -e

cd "$(dirname "$0")"

echo "========================================"
echo "🤖 AI Daily News - local run"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo

# Create the virtual environment on first run
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo
echo "1. Fetching news..."
python fetch_news.py

echo
echo "2. Translating headlines..."
python translate.py

echo
echo "3. Generating HTML..."
python generate.py

echo
echo "========================================"
echo "✓ Done!"
echo "========================================"
