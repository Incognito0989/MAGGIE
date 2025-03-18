# main_gui.py
import tkinter as tk
from tkinter import Image, ttk
from pathlib import Path
from pages.tool_tab import ToolTab
from pages.config_editor_tab import create_config_editor_tab
from pages.inventory_tab import create_inventory_tab
from pages.license_tab import LicenseTab
from utils.logo import ResizableImageApp
from settings import *

import os
import subprocess

def get_ssh_public_key():
    """Ensures an SSH key exists, generates one if needed, and retrieves the public key."""
    pub_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    private_key_path = os.path.expanduser("~/.ssh/id_rsa")

    # Check if the SSH key exists
    if not os.path.exists(pub_key_path):
        print("SSH public key not found. Generating a new one...")
        subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", private_key_path], check=True)

    # Read and return the public key
    with open(pub_key_path, "r") as f:
        pub_key = f.read().strip()
    return pub_key

# Example usage
pub_key = get_ssh_public_key()

# Initialize the main window
root = tk.Tk()
root.title("MAGGIE")

# Get the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Set the window size to fill the entire screen
root.geometry(f"{screen_width}x{screen_height}")

ResizableImageApp(root, "assets/Maggie_Logo.png")
# Define the services directory path
services_dir = Path(__file__).parent / "payloads"

# Create the Notebook (tabs container)
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# Add each tab by calling the create functions
toolTab = ToolTab(notebook, services_dir)

create_config_editor_tab(notebook, services_dir)
license_tab = LicenseTab(notebook)
# create_inventory_tab(notebook)

# Run the Tkinter event loop
root.mainloop()

