import os
import shutil
import tkinter as tk
from tkinter import filedialog

class FileUploader(tk.Frame):
    def __init__(self, parent, main_folder="./payloads"):
        super().__init__(parent)
        self.main_folder = os.path.abspath(main_folder)

        # Ensure the main folder exists
        os.makedirs(self.main_folder, exist_ok=True)

        # UI Elements
        self.label = tk.Label(self, text="Upload a File or Folder:", font=("Arial", 12))
        self.label.pack(pady=5)

        self.upload_btn = tk.Button(self, text="Select File", command=self.upload_file)
        self.upload_btn.pack(pady=5)

        self.upload_btn = tk.Button(self, text="Select Folder", command=self.upload_folder)
        self.upload_btn.pack(pady=5)

        self.status_label = tk.Label(self, text="", fg="green")
        self.status_label.pack(pady=5)

    def upload_file(self):
        """Let the user pick either a file or a folder and upload it."""
        path = filedialog.askopenfilename(initialdir=self.main_folder)  # Allow file selection

        if not path:  # User canceled both dialogs
            return  

        dest_path = os.path.join(self.main_folder, os.path.basename(path))

        try:
            shutil.copy(path, dest_path)
            self.status_label.config(text=f"Uploaded File: {os.path.basename(path)}")
        except Exception as e:
            self.status_label.config(text=f"Upload failed: {e}")

    def upload_folder(self):
        """Let the user pick either a file or a folder and upload it."""
        path = filedialog.askdirectory(initialdir=self.main_folder)

        if not path:  # User canceled both dialogs
            return  

        dest_path = os.path.join(self.main_folder, os.path.basename(path))

        try:
            shutil.copytree(path, dest_path, dirs_exist_ok=True)
            self.status_label.config(text=f"Uploaded Folder: {os.path.basename(path)}")
        except Exception as e:
            self.status_label.config(text=f"Upload failed: {e}")


# Example usage in a Tkinter app
if __name__ == "__main__":
    root = tk.Tk()
    root.title("File Uploader")

    uploader = FileUploader(root)
    uploader.pack(padx=20, pady=20)

    root.mainloop()
