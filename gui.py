# main_gui.py
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from pages.tool_tab import create_tool_tab
from pages.config_editor_tab import create_config_editor_tab
from pages.inventory_tab import create_inventory_tab

# Initialize the main window
root = tk.Tk()
root.title("Configuration Tool")
root.geometry("900x500")

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
