# main_gui.py
import tkinter as tk
from tkinter import Image, ttk
from pathlib import Path
from pages.tool_tab import ToolTab
from pages.config_editor_tab import create_config_editor_tab
from pages.inventory_tab import create_inventory_tab
from utils.logo import ResizableImageApp

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
# create_inventory_tab(notebook)

# Run the Tkinter event loop
root.mainloop()

