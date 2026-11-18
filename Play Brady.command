#!/bin/bash
# Double-click this file on a Mac to install what Brady needs (first time only) and start the game.
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed."
  echo "Install it from https://www.python.org/downloads then double-click this file again."
  open "https://www.python.org/downloads/"
  read -r -p "Press Enter to close..."
  exit 1
fi

if ! python3 -c "import pygame" >/dev/null 2>&1; then
  echo "First run: installing the game library (pygame)..."
  python3 -m pip install --user --only-binary :all: -r requirements.txt || {
    echo "Install failed. Send the message above to Claude."
    read -r -p "Press Enter to close..."
    exit 1
  }
fi

echo "Starting Brady..."
python3 main.py
