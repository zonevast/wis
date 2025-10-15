# Live Speech to Text System

A real-time speech recognition system that captures audio from your microphone, transcribes speech to text, performs grammar correction, and simulates typing the output.

## Features

- Real-time speech recognition from microphone input
- Grammar and spell-check correction (when Java 17+ is available)
- Keyboard typing simulation
- Pause/Resume functionality with Ctrl+Shift+Space
- Noise filtering to avoid short fragments
- Completely offline operation (after initial model download)
- Support for multiple languages (depending on the selected Whisper model)

## Requirements

- Python 3.7+
- Linux, Windows, or macOS
- Microphone access
- Java 17+ (optional, for grammar correction)

## Installation

1. Install required packages:
```bash
pip install faster-whisper language-tool-python sounddevice numpy pynput
```

2. Run the application:
```bash
python live_speech_to_text.py
```

## Usage

- Speak normally into your microphone after starting the application
- The transcribed text will be automatically typed
- Press `Ctrl+Shift+Space` to pause/resume the speech recognition
- Press `Ctrl+C` to exit the application

## Notes

- The first time you run the application, it will download the Whisper model files to your local machine
- After the initial download, the system works completely offline
- For non-English languages, the grammar correction may be limited
- If you don't have Java 17+, grammar correction will be disabled automatically

## Customization

- To disable grammar correction: `python live_speech_to_text.py false`
- To change the model size, edit the model initialization in the code to use 'tiny', 'base', 'medium', or 'large' instead of 'small'

## Performance

- The 'small' model provides a good balance between speed and accuracy
- For better accuracy, use 'medium' or 'large' models (but they are slower)
- For faster performance on older computers, use 'tiny' or 'base' models

## Troubleshooting

- If you experience delays, try reducing background noise
- The system now uses a 2-second processing window for more responsiveness
- Short fragments and repetitions are automatically filtered out
- If the system is too sensitive to background noise, the silence threshold can be adjusted in the code