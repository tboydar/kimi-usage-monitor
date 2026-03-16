#!/bin/bash
# Kimi Usage Monitor Installation Script

set -e

echo "🌙 Installing Kimi Usage Monitor..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "❌ Error: Python 3.9+ is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python version check passed"

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is not installed"
    exit 1
fi

echo "✅ pip3 found"

# Install package
echo "📦 Installing kimi-monitor..."
pip3 install -e .

# Create config directory
mkdir -p ~/.kimi-monitor

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Get your API key from https://platform.moonshot.cn"
echo "2. Set environment variable: export KIMI_API_KEY='sk-...'"
echo "3. Run: kimi-monitor"
echo ""
echo "For more options, run: kimi-monitor --help"
