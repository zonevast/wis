# WIS: Whisper Input System for Linux

This guide provides step-by-step instructions to install and use WIS on a Linux system.

## Quick Start: How to Use

Follow these steps to get started.

### Step 1: Run the Installer (First Time Only)

First, you must run the installer script. This will automatically check for dependencies, install required software, and create an application shortcut.

Open your terminal, navigate to the project folder, and run:

```bash
bash install.sh
```

**Note:** You only need to do this once.

### Step 2: Launch the Application

After installation, you can start the application in two ways:

*   **(Recommended) Use the Applications Menu:**
    1.  Open your system's application menu.
    2.  Search for "**WIS**" and click to launch it.

*   **(Alternative) Use the Terminal:**
    If you prefer the command line, run the following command:
    ```bash
    python3 /wis/speech_indicator.py
    ```

This will start the WIS tray icon and begin speech recognition automatically.

### Step 3: Control Transcription

A microphone icon will appear in your system tray (usually at the top or bottom of your screen). This icon shows the status of the application.

*   **Right-click the icon** to open the control menu.
*   From the menu, you can **Start**, **Stop**, or **Quit** the application.

---

## Advanced Configuration

### Changing the Model Size

For a different balance of speed and accuracy, you can change the Whisper model.

1.  Open the file `live_speech_to_text.py`.
2.  Find the line `model = WhisperModel('small', ...)`
3.  Change `'small'` to one of the following:
    *   `'tiny'` or `'base'`: Faster, less accurate.
    *   `'medium'` or `'large'`: Slower, more accurate.

### Grammar Correction

-   Grammar correction requires Java 17+ and is enabled by default if Java is found.
-   If you wish to run the application without grammar correction, you can modify the `speech_indicator.py` file to add the `false` argument to the command that launches `live_speech_to_text.py`.

## Troubleshooting

-   **Delays or Lag:** Try to minimize background noise or switch to a smaller model (like `'base'` or `'tiny'`) for faster performance.
-   **Too Sensitive:** If the app picks up too much background noise, the `SILENCE_THRESHOLD` in the `live_speech_to_text.py` file can be adjusted.