import sounddevice as sd
import numpy as np
import queue
import threading
import tempfile
import os
from faster_whisper import WhisperModel
from pynput.keyboard import Key, Controller
from pynput import keyboard
import time
import wave
import logging

# Attempt to import language_tool_python, but make it optional
try:
    import language_tool_python
    LANGUAGE_TOOL_AVAILABLE = True
except ImportError:
    LANGUAGE_TOOL_AVAILABLE = False
    print("language_tool_python not available. Grammar correction will be disabled.")

class LiveSpeechToText:
    def __init__(self, use_grammar_correction=True, control_file=None):
        # Initialize components
        self.model = WhisperModel("large", device="cuda", compute_type="float16")
        self.keyboard = Controller()

        # Initialize grammar correction if available and requested
        self.use_grammar_correction = use_grammar_correction and LANGUAGE_TOOL_AVAILABLE
        if self.use_grammar_correction:
            try:
                self.grammar_tool = language_tool_python.LanguageTool('en')
            except Exception as e:
                print(f"Error initializing grammar tool: {e}")
                print("Grammar correction will be disabled.")
                self.use_grammar_correction = False

        # Audio recording parameters
        self.sample_rate = 16000
        self.chunk_duration = 2  # seconds (further reduced for more responsive transcription)
        self.chunk_size = self.sample_rate * self.chunk_duration

        # Threading components
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.terminate = False
        self.paused = False  # Add pause state
        self.ctrl_pressed = False
        self.shift_pressed = False

        # Control file for external control (GUI)
        self.control_file = control_file
        self.status_file = control_file.replace('_control.txt', '_status.txt') if control_file else None
        
        # Voice activity detection parameters
        self.audio_buffer = np.array([])
        self.silence_threshold = 0.01  # Adjust this value based on your environment
        self.min_audio_length = self.sample_rate * 0.5  # Minimum 0.5 seconds of audio
        
        # Temporary file for audio chunks
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize the keyboard listener for hotkeys
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
    
    def on_press(self, key):
        """Handle keyboard hotkeys"""
        try:
            if key == Key.ctrl or key == Key.ctrl_r:
                self.ctrl_pressed = True
            elif key == Key.shift or key == Key.shift_r:
                self.shift_pressed = True
            elif key == Key.space and self.ctrl_pressed and self.shift_pressed:
                self.toggle_pause()
        except AttributeError:
            # Handle special keys that don't have simple comparisons
            pass
    
    def on_release(self, key):
        """Handle key releases to reset modifiers"""
        try:
            if key == Key.ctrl or key == Key.ctrl_r:
                self.ctrl_pressed = False
            elif key == Key.shift or key == Key.shift_r:
                self.shift_pressed = False
            elif key == Key.esc:
                # Stop the listener if Escape is pressed
                return False
        except AttributeError:
            pass
    
    def toggle_pause(self):
        """Toggle the pause state"""
        self.paused = not self.paused
        if self.paused:
            print("Speech recognition PAUSED (Ctrl+Shift+Space)")
        else:
            print("Speech recognition RESUMED (Ctrl+Shift+Space)")
    
    def is_repetition(self, text):
        """Check if the text is likely a repetition/noise"""
        # Split into words and check if there are many repetitions
        words = text.split()
        if len(words) <= 1:
            return False  # Single words are OK to pass through
            
        # Count unique words
        unique_words = set(words)
        if len(unique_words) == 1 and len(words) > 1:
            # All words are the same - likely noise
            return True
            
        # Check if the same character is repeated many times
        chars = list(text)
        unique_chars = set(chars)
        if len(unique_chars) == 1 and len(chars) > 3:
            # Same character repeated many times
            return True
            
        return False
    
    def audio_callback(self, indata, frames, time, status):
        """Callback function to capture audio data"""
        if status:
            print(f"Audio status: {status}")
        # Add audio data to queue (we'll do voice activity detection during processing)
        audio_data = indata.copy()
        self.audio_queue.put(audio_data)
    
    def record_audio(self):
        """Record audio in a separate thread"""
        print("Starting audio recording... Speak now!")
        with sd.InputStream(callback=self.audio_callback, 
                           channels=1, 
                           samplerate=self.sample_rate,
                           dtype='float32'):
            while not self.terminate:
                time.sleep(0.1)
    
    def save_audio_chunk(self, audio_data, filename):
        """Save audio chunk to a WAV file"""
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes for int16
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio file using faster-whisper"""
        # segments, info = self.model.transcribe(audio_file)
        segments, info = self.model.transcribe(
        audio_file,
        language="en",       # <--- Force English transcription
        beam_size=5,         # Optional: improves accuracy a bit
        vad_filter=True      # Optional: filters silence better
        )
        raw_text = " ".join([seg.text for seg in segments])
        return raw_text.strip()
    
    def correct_grammar(self, text):
        """Correct grammar in the transcribed text"""
        if not text or not self.use_grammar_correction:
            return text
        try:
            # Only attempt grammar correction for English text
            # LanguageTool may not properly support Arabic grammar correction
            import re
            # Check if text contains mainly English characters
            english_chars = re.findall(r'[a-zA-Z]', text)
            if len(english_chars) / len(text.replace(' ', '')) < 0.3:  # If less than 30% English chars
                return text  # Skip grammar correction for non-English text
            
            matches = self.grammar_tool.check(text)
            corrected = language_tool_python.utils.correct(text, matches)
            return corrected
        except Exception as e:
            print(f"Grammar correction error: {e}")
            return text  # Return original text if correction fails
    
    def type_text(self, text):
        """Simulate typing the text"""
        if text:
            try:
                # Add a space at the beginning to ensure proper spacing
                if text and text[0] != ' ':
                    text = ' ' + text
                
                # Handle typing with proper Unicode support
                # Split the text into individual characters to handle Unicode better
                for char in text:
                    try:
                        self.keyboard.press(char)
                        self.keyboard.release(char)
                    except (self.keyboard.InvalidCharacterException, self.keyboard.InvalidKeyException):
                        # If character cannot be typed, skip it
                        continue
            except Exception as e:
                print(f"Error typing text: {e}")
                # Fallback: write to a file instead
                try:
                    with open("typed_output.txt", "a", encoding="utf-8") as f:
                        f.write(text + " ")
                except:
                    pass
    
    def check_control_file(self):
        """Check control file for external commands"""
        if self.control_file and os.path.exists(self.control_file):
            try:
                with open(self.control_file, 'r') as f:
                    command = f.read().strip()
                    if command == "stopped":
                        self.terminate = True
                    elif command == "pause":
                        self.paused = True
                    elif command == "resume" or command == "running":
                        self.paused = False
            except Exception as e:
                print(f"Error reading control file: {e}")

    def write_status(self, status):
        """Write current status to status file"""
        if self.status_file:
            try:
                with open(self.status_file, 'w') as f:
                    f.write(status)
            except Exception as e:
                print(f"Error writing status file: {e}")

    def process_audio_chunks(self):
        """Process audio chunks as they become available"""
        accumulated_audio = np.array([])

        while not self.terminate:
            try:
                # Check for external control commands
                self.check_control_file()

                # Get audio data from queue
                audio_chunk = self.audio_queue.get(timeout=0.1)

                # Skip processing if paused
                if self.paused:
                    self.write_status("paused")
                    continue

                self.write_status("running")
                
                # Accumulate audio data
                accumulated_audio = np.concatenate([accumulated_audio, audio_chunk.flatten()])
                
                # Process when we have enough audio data
                if len(accumulated_audio) >= self.chunk_size:
                    # Calculate volume (RMS) to check if there's enough speech content
                    rms = np.sqrt(np.mean(accumulated_audio**2))
                    
                    # Only process if the audio level is above the threshold
                    if rms > self.silence_threshold:
                        # Save the accumulated audio as a temporary file
                        temp_filename = os.path.join(self.temp_dir, f"chunk_{int(time.time())}.wav")
                        self.save_audio_chunk(accumulated_audio, temp_filename)
                        
                        try:
                            # Transcribe the audio
                            raw_text = self.transcribe_audio(temp_filename)
                            
                            if raw_text:
                                # Filter out short fragments and noise
                                # More intelligent filtering:
                                # 1. At least 2 words OR contains meaningful punctuation
                                # 2. Length of at least 5 characters
                                words = raw_text.split()
                                has_meaningful_punct = any(p in raw_text for p in '.!?')
                                is_meaningful = (len(words) >= 2 or len(raw_text.strip()) >= 5 or has_meaningful_punct)
                                
                                # Additional check: don't type if it's just repetitions
                                stripped_text = raw_text.strip()
                                if is_meaningful and not self.is_repetition(stripped_text):
                                    print(f"Raw: {raw_text}")
                                    
                                    # Correct grammar
                                    corrected_text = self.correct_grammar(raw_text)
                                    if corrected_text != raw_text:
                                        print(f"Corrected: {corrected_text}")
                                    
                                    # Type the text (prefer corrected, fallback to raw)
                                    text_to_type = corrected_text if corrected_text else raw_text
                                    
                                    # Add a small delay to allow for processing
                                    time.sleep(0.05)
                                    
                                    # Type the text
                                    self.type_text(text_to_type)
                                else:
                                    # Skip short fragments, repetitions, or likely noise
                                    print(f"Skipped: '{raw_text}'")
                                    
                        except Exception as e:
                            print(f"Error processing audio chunk: {e}")
                        
                        # Remove temporary file
                        try:
                            os.remove(temp_filename)
                        except:
                            pass  # File might not exist or be in use
                    else:
                        print("Skipped low-volume chunk")  # Debug info
                    
                    # Reset accumulated audio to only keep the overflow
                    overflow_size = len(accumulated_audio) - self.chunk_size
                    if overflow_size > 0:
                        accumulated_audio = accumulated_audio[-overflow_size:]
                    else:
                        accumulated_audio = np.array([])
                
            except queue.Empty:
                continue
    
    def start(self):
        """Start the live speech to text system"""
        print("Starting Live Speech to Text System...")
        print("Press Ctrl+C to stop the system")
        
        # Start recording thread
        recording_thread = threading.Thread(target=self.record_audio)
        recording_thread.start()
        
        # Start processing thread
        processing_thread = threading.Thread(target=self.process_audio_chunks)
        processing_thread.start()
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping the system...")
            self.terminate = True
            
            # Wait for threads to finish
            recording_thread.join()
            processing_thread.join()
            
            # Stop the keyboard listener
            self.listener.stop()
            
            # Clean up temporary directory
            import shutil
            shutil.rmtree(self.temp_dir)
            
            print("System stopped.")

if __name__ == "__main__":
    import sys

    # Check if grammar correction should be enabled (default to True if not specified)
    use_grammar = True
    control_file = None

    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ['false', '0', 'no', 'off']:
            use_grammar = False

    # Check if control file path is provided (for GUI control)
    if len(sys.argv) > 2:
        control_file = sys.argv[2]

    # Create and start the live speech to text system
    print("=== Live Speech to Text System ===")
    print("Commands:")
    print("  - Speak normally for automatic transcription")
    print("  - Press Ctrl+Shift+Space to pause/resume")
    print("  - Press Ctrl+C to exit")
    if control_file:
        print(f"  - Control file: {control_file}")
    print("")

    print("Initializing system...")
    if use_grammar and LANGUAGE_TOOL_AVAILABLE:
        print("Grammar correction: ENABLED")
    elif use_grammar and not LANGUAGE_TOOL_AVAILABLE:
        print("Grammar correction: NOT AVAILABLE (requires Java 17+)")
    else:
        print("Grammar correction: DISABLED")

    print(f"Audio chunk duration: 2 seconds (for responsiveness)")
    print("")
    print("Starting Live Speech to Text System...")
    print("Speak now! (System is active)")

    speech_system = LiveSpeechToText(use_grammar_correction=use_grammar, control_file=control_file)
    speech_system.start()