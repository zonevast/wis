#!/bin/bash
# Source user environment
if [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc"
fi

# Set working directory
cd /home/yousef/wis

# Launch speech indicator in background
python3 speech_indicator.py > /tmp/wis_debug.log 2>&1 &
