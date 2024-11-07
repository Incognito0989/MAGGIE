# inventory_tab.py
import tkinter as tk
from tkinter import ttk

def create_inventory_tab(notebook):
    # Create Inventory tab
    inventory_tab = ttk.Frame(notebook)
    notebook.add(inventory_tab, text="Inventory")

    # Placeholder label for future inventory features
    label = tk.Label(inventory_tab, text="Inventory Management Features Coming Soon", font=("Arial", 12))
    label.pack(pady=20)

    return inventory_tab
