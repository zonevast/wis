#!/bin/bash

# install.sh - WIS (Whisper Input System) Installer
# Auto-checks and installs missing dependencies

set -e

echo "=== WIS Installation Script ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if Python 3 is installed
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3 first: sudo apt install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓${NC} Found: $PYTHON_VERSION"

# Check if pip3 is installed
echo "Checking pip3 installation..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}Warning: pip3 is not installed${NC}"
    echo "Installing pip3..."
    sudo apt install python3-pip -y
fi
echo -e "${GREEN}✓${NC} pip3 is installed"

# Check Java for grammar correction (optional)
echo ""
echo "Checking Java installation (optional, for grammar correction)..."
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1)
    echo -e "${GREEN}✓${NC} Found: $JAVA_VERSION"
else
    echo -e "${YELLOW}⚠${NC} Java not found - grammar correction will be disabled"
    echo "  To enable grammar correction, install Java 17+: sudo apt install default-jdk"
fi

# Check NVIDIA GPU and CUDA
echo ""
echo "Checking GPU and CUDA support..."
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓${NC} NVIDIA GPU detected"
    CUDA_AVAILABLE=true
else
    echo -e "${YELLOW}⚠${NC} No NVIDIA GPU detected - will use CPU mode"
    CUDA_AVAILABLE=false
fi

# Check Python dependencies
echo ""
echo "Checking Python dependencies..."

check_python_package() {
    local package=$1
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $package is already installed"
        return 0
    else
        echo -e "${YELLOW}✗${NC} $package is not installed"
        return 1
    fi
}

# List of packages to check
PACKAGES_MISSING=0

echo "Checking faster_whisper..."
if ! check_python_package "faster_whisper"; then
    PACKAGES_MISSING=1
fi

echo "Checking sounddevice..."
if ! check_python_package "sounddevice"; then
    PACKAGES_MISSING=1
fi

echo "Checking numpy..."
if ! check_python_package "numpy"; then
    PACKAGES_MISSING=1
fi

echo "Checking pynput..."
if ! check_python_package "pynput"; then
    PACKAGES_MISSING=1
fi

echo "Checking torch..."
if ! check_python_package "torch"; then
    PACKAGES_MISSING=1
fi

echo "Checking language_tool_python..."
if ! check_python_package "language_tool_python"; then
    echo -e "${YELLOW}⚠${NC} language_tool_python not installed (optional)"
fi

# Install missing packages
if [ $PACKAGES_MISSING -eq 1 ]; then
    echo ""
    echo "Installing missing Python packages..."

    if [ "$CUDA_AVAILABLE" = true ]; then
        echo "Installing with CUDA support..."
        pip3 install -r "$SCRIPT_DIR/requirements.txt" --index-url https://download.pytorch.org/whl/cu124
    else
        echo "Installing CPU-only version..."
        pip3 install faster-whisper language-tool-python sounddevice numpy pynput
        pip3 install torch --index-url https://download.pytorch.org/whl/cpu
    fi

    echo -e "${GREEN}✓${NC} Python packages installed successfully"
else
    echo -e "${GREEN}✓${NC} All required Python packages are already installed"
fi

# Update live_speech_to_text.py to use CPU if no CUDA
if [ "$CUDA_AVAILABLE" = false ]; then
    echo ""
    echo "Configuring for CPU mode..."
    if grep -q 'device="cuda"' "$SCRIPT_DIR/live_speech_to_text.py"; then
        sed -i 's/device="cuda"/device="cpu"/g' "$SCRIPT_DIR/live_speech_to_text.py"
        sed -i 's/compute_type="float16"/compute_type="int8"/g' "$SCRIPT_DIR/live_speech_to_text.py"
        sed -i 's/WhisperModel("large"/WhisperModel("small"/g' "$SCRIPT_DIR/live_speech_to_text.py"
        echo -e "${GREEN}✓${NC} Configured for CPU with 'small' model"
    fi
fi

# Create desktop entry
echo ""
echo "Creating desktop application entry..."
DESKTOP_FILE="$HOME/.local/share/applications/wis.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=WIS
Comment=Whisper Input System - Live Speech to Text
Exec=python3 $SCRIPT_DIR/speech_indicator.py
Icon=audio-input-microphone
Terminal=false
Categories=Audio;Utility;Accessibility;
Keywords=speech;transcription;whisper;voice;dictation;
StartupNotify=false
X-GNOME-Autostart-enabled=false
EOF

chmod +x "$DESKTOP_FILE"
echo -e "${GREEN}✓${NC} Desktop entry created at: $DESKTOP_FILE"

# Make main script executable
chmod +x "$SCRIPT_DIR/live_speech_to_text.py" 2>/dev/null || true

echo ""
echo -e "${GREEN}=== Installation Complete ===${NC}"
echo ""
echo "You can now run WIS in the following ways:"
echo "  1. From terminal: python3 $SCRIPT_DIR/live_speech_to_text.py"
echo "  2. From applications menu: Search for 'WIS'"
echo ""
echo "Controls:"
echo "  - Ctrl+Shift+Space: Pause/Resume"
echo "  - Ctrl+C: Exit"
echo ""

if [ "$CUDA_AVAILABLE" = false ]; then
    echo -e "${YELLOW}Note: Running in CPU mode. For faster performance with GPU:${NC}"
    echo "  1. Install NVIDIA drivers and CUDA"
    echo "  2. Reinstall PyTorch: pip3 install torch --index-url https://download.pytorch.org/whl/cu124"
    echo "  3. Edit line 25 in live_speech_to_text.py to use device='cuda'"
    echo ""
fi
