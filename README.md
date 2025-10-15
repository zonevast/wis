# Live Speech to Text

A real-time, offline-capable speech-to-text application that transcribes audio from your microphone and types it out for you.

## Key Features

-   **Real-time Transcription:** Captures microphone audio and converts it to text instantly.
-   **Offline First:** Works entirely offline after the initial model download.
-   **Grammar Correction:** Automatically corrects grammar and spelling (requires Java 17+).
-   **Keyboard Simulation:** Types the transcribed text into any active window.
-   **Pause/Resume:** Use `Ctrl+Shift+Space` to toggle transcription on and off.
-   **Noise Filtering:** Ignores short audio fragments and background noise.
-   **Multi-Language:** Supports various languages based on the chosen Whisper model.

## Setup

1.  **Prerequisites:**
    *   Python 3.7+
    *   Linux, Windows, or macOS
    *   A connected microphone
    *   Java 17+ (Optional, for grammar correction)

2.  **Installation:**
    Open your terminal and run:
    ```bash
    pip install faster-whisper language-tool-python sounddevice numpy pynput
    ```

## How to Use

1.  **Run the application:**
    ```bash
    python live_speech_to_text.py
    ```
    The first time you run it, the required speech model will be downloaded.

2.  **Start Speaking:** Once running, the application will listen for your voice and start typing what it hears.

3.  **Controls:**
    *   `Ctrl+Shift+Space`: Pause or resume the transcription.
    *   `Ctrl+C`: Stop the application.

## Configuration

### Model Size

For a different balance of speed and accuracy, you can change the model. Edit `live_speech_to_text.py` and change `'small'` to one of the following:

-   `'tiny'` or `'base'`: Faster, less accurate.
-   `'medium'` or `'large'`: Slower, more accurate.

### Grammar Correction

-   **Disable:** To run without grammar correction, use the following command:
    ```bash
    python live_speech_to_text.py false
    ```
-   **Note:** Grammar correction is automatically disabled if Java 17+ is not found.

## Troubleshooting

-   **Delays or Lag:** Try to minimize background noise or switch to a smaller model for faster performance.
-   **Too Sensitive:** If the app picks up too much background noise, the `SILENCE_THRESHOLD` in the code can be adjusted.
-   **Repetitions:** The system is designed to filter out short, repetitive fragments.
