import sys
import tkinter as tk
from tkinter import scrolledtext

LOG_FILE = "maggie_debug.log"
MAX_LINES = 1000  # Maximum lines to keep in the log file

class LogViewer(tk.Frame):
    def __init__(self, parent, lines=20):
        super().__init__(parent)
        self.lines_to_show = lines

        # Text widget for displaying logs
        self.text_widget = scrolledtext.ScrolledText(self, height=lines, wrap="word", state="disabled")
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        # Start updating logs in the background
        self.update_log()

    def update_log(self):
        """ Reads last few lines from the log file and updates the UI. """
        try:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()

            # Trim file to max allowed lines
            if len(lines) > MAX_LINES:
                with open(LOG_FILE, "w") as f:
                    f.writelines(lines[-MAX_LINES:])  # Keep only the last MAX_LINES

            self.display_log(lines[-self.lines_to_show:])  # Show only last few lines
        except Exception:
            pass  # Ignore errors if file is empty or unreadable

        self.after(1000, self.update_log)  # Schedule next update

    def display_log(self, lines):
        """ Update the text widget with the latest log lines. """
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, "".join(lines))
        self.text_widget.config(state="disabled")
        self.text_widget.yview(tk.END)  # Auto-scroll to the bottom

class RedirectOutput:
    """ Redirects stdout and stderr to a log file and the console. """
    def __init__(self, log_file):
        self.log_file_path = log_file
        self.terminal = sys.stdout

    def write(self, message):
        self.terminal.write(message)  # Print to console
        self.terminal.flush()

        with open(self.log_file_path, "a") as log_file:
            log_file.write(message)

        # Trim file after every write
        self.trim_log_file()

    def flush(self):
        self.terminal.flush()

    def trim_log_file(self):
        """ Trims the log file to keep only the last MAX_LINES. """
        try:
            with open(self.log_file_path, "r") as f:
                lines = f.readlines()
            if len(lines) > MAX_LINES:
                with open(self.log_file_path, "w") as f:
                    f.writelines(lines[-MAX_LINES:])  # Keep last MAX_LINES
        except Exception:
            pass  # Ignore file errors

# Redirect stdout and stderr
sys.stdout = RedirectOutput(LOG_FILE)
sys.stderr = sys.stdout
