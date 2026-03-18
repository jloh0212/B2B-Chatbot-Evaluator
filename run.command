#!/bin/bash
# Run the B2B Chatbot Evaluator
# Double-click this file in Finder to launch the app.

# Change to the directory where this script lives
cd "$(dirname "$0")"

# Load API key from .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Prompt for key if still not set
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ANTHROPIC_API_KEY is not set."
  read -p "Paste your Anthropic API key: " ANTHROPIC_API_KEY
  export ANTHROPIC_API_KEY
fi

# Open VS Code
if command -v code &>/dev/null; then
  code .
elif [ -f "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" ]; then
  "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" .
else
  echo "VS Code not found — skipping. Install it or add 'code' to your PATH."
fi

echo ""
echo "Starting B2B Chatbot Evaluator..."
echo "Open http://127.0.0.1:7860 in your browser."
echo "Press Ctrl+C to stop."
echo ""

python3 app.py
