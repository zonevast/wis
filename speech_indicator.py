#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import AppIndicator3, Gtk, GLib
import os
import subprocess
import signal
import time

class SpeechIndicator:
    def __init__(self):
        self.speech_process = None
        self.is_running = False
        self.control_file = "/tmp/speech_control.txt"
        self.status_file = "/tmp/speech_status.txt"

        # Create indicator
        self.indicator = AppIndicator3.Indicator.new(
            "speech-to-text",
            "microphone-sensitivity-medium",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        # Create menu
        self.menu = Gtk.Menu()

        # Status label
        self.status_item = Gtk.MenuItem(label="Status: Stopped")
        self.status_item.set_sensitive(False)
        self.menu.append(self.status_item)

        # Separator
        separator = Gtk.SeparatorMenuItem()
        self.menu.append(separator)

        # Start button
        self.start_item = Gtk.MenuItem(label="Start Speech Recognition")
        self.start_item.connect("activate", self.on_start)
        self.menu.append(self.start_item)

        # Stop button
        self.stop_item = Gtk.MenuItem(label="Stop Speech Recognition")
        self.stop_item.connect("activate", self.on_stop)
        self.stop_item.set_sensitive(False)
        self.menu.append(self.stop_item)

        # Separator
        separator2 = Gtk.SeparatorMenuItem()
        self.menu.append(separator2)

        # Quit button
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.on_quit)
        self.menu.append(quit_item)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)

        # Initialize control file
        self.write_control("stopped")

        # Auto-start speech recognition
        GLib.timeout_add(500, self.auto_start)

    def write_control(self, command):
        """Write control command to file"""
        try:
            with open(self.control_file, 'w') as f:
                f.write(command)
        except Exception as e:
            print(f"Error writing control file: {e}")

    def read_status(self):
        """Read status from file"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Error reading status file: {e}")
        return "unknown"

    def auto_start(self):
        """Auto-start speech recognition on launch"""
        self.on_start(None)
        return False  # Don't repeat the timeout

    def on_start(self, widget):
        """Start the speech recognition service"""
        if not self.is_running:
            try:
                # Start the speech service in background
                speech_script = "/home/yousef/wis/live_speech_to_text.py"

                # Open log file for subprocess output
                log_file = open("/tmp/live_speech_to_text.log", "w")

                self.speech_process = subprocess.Popen(
                    ["python3", speech_script, "false", self.control_file],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )

                self.is_running = True
                self.write_control("running")

                # Update UI
                self.status_item.set_label("Status: Running")
                self.start_item.set_sensitive(False)
                self.stop_item.set_sensitive(True)
                self.indicator.set_icon("microphone-sensitivity-high")

                print("Speech recognition started")
            except Exception as e:
                print(f"Error starting speech recognition: {e}")
                self.is_running = False

    def on_stop(self, widget):
        """Stop the speech recognition service"""
        if self.is_running and self.speech_process:
            try:
                # Send termination signal
                self.write_control("stopped")

                # Kill the process group
                os.killpg(os.getpgid(self.speech_process.pid), signal.SIGTERM)

                # Wait for process to terminate
                time.sleep(0.5)

                if self.speech_process.poll() is None:
                    # Force kill if still running
                    os.killpg(os.getpgid(self.speech_process.pid), signal.SIGKILL)

                self.speech_process = None
                self.is_running = False

                # Update UI
                self.status_item.set_label("Status: Stopped")
                self.start_item.set_sensitive(True)
                self.stop_item.set_sensitive(False)
                self.indicator.set_icon("microphone-sensitivity-medium")

                print("Speech recognition stopped")
            except Exception as e:
                print(f"Error stopping speech recognition: {e}")

    def on_quit(self, widget):
        """Quit the application"""
        # Stop speech recognition if running
        if self.is_running:
            self.on_stop(None)

        # Clean up control files
        try:
            if os.path.exists(self.control_file):
                os.remove(self.control_file)
            if os.path.exists(self.status_file):
                os.remove(self.status_file)
        except:
            pass

        Gtk.main_quit()

def main():
    indicator = SpeechIndicator()
    Gtk.main()

if __name__ == "__main__":
    main()
