# main_gui.py
import tkinter as tk
from tkinter import Image, ttk
from pathlib import Path
from pages.tool_tab import create_tool_tab
from pages.config_editor_tab import create_config_editor_tab
from pages.inventory_tab import create_inventory_tab
from utils.logo import ResizableImageApp

# Initialize the main window
root = tk.Tk()
root.title("Meg Service Tool")
root.geometry("1000x800")

ResizableImageApp(root, "assets/synamedia-logo-black-rgb.png")

# Define the services directory path
services_dir = Path(__file__).parent / "payloads"

# Create the Notebook (tabs container)
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)


# Add each tab by calling the create functions
create_tool_tab(notebook, services_dir)
create_config_editor_tab(notebook, services_dir)
create_inventory_tab(notebook)

# Run the Tkinter event loop
root.mainloop()
