#!/bin/bash
# Example script to run NDI SDK setup with DirectML
# This demonstrates usage of the Python 3.14 compatible setup script

echo "Starting NDI SDK and DirectML setup..."
echo "This script fixes the Python 3.14 tar.extractall() deprecation warning"
echo

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

# Check if version is compatible
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
    echo "✓ Python version is compatible"
else
    echo "✗ Python 3.7+ required"
    exit 1
fi

echo
echo "Running NDI SDK setup with Python 3.14 compatibility..."

# Run the setup script
python3 src/setup_directml.py

# Check exit code
if [ $? -eq 0 ]; then
    echo
    echo "=================================================="
    echo "✓ NDI SDK setup completed successfully!"
    echo "✓ Python 3.14 tar.extractall() compatibility fixed"
    echo "✓ DirectML dependencies installed"
    echo "=================================================="
else
    echo
    echo "=================================================="
    echo "✗ Setup failed. Check the error messages above."
    echo "=================================================="
    exit 1
fi