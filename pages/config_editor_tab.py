# config_editor_tab.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import json

def create_config_editor_tab(notebook, services_dir):
    # Create Config Editor tab
    config_editor_tab = ttk.Frame(notebook)
    notebook.add(config_editor_tab, text="Config Editor")

    # Variable to store the selected file
    selected_file = tk.StringVar()

    # Function to load available config files
    def load_config_files():
        # List all JSON files in the given services directory
        files = [file.name for file in services_dir.iterdir() if file.is_file() and file.suffix == '.json']
        dropdown_menu['values'] = files
        if files:
            selected_file.set(files[0])  # Select the first file by default
            display_json_content()       # Display its content in the editor
        else:
            dropdown_menu['values'] = []
            json_text.delete("1.0", tk.END)

    # Display the JSON content of the selected file in the editor
    def display_json_content():
        file_name = selected_file.get()
        if not file_name:
            json_text.delete("1.0", tk.END)
            return

        file_path = services_dir / file_name
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            json_text.delete("1.0", tk.END)
            json_text.insert(tk.END, json.dumps(data, indent=4))
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Selected file is not a valid JSON file.")
            json_text.delete("1.0", tk.END)

    # Save the edited JSON content as a new file
    def save_as_new_file():
        new_file_content = json_text.get("1.0", tk.END).strip()
        if not new_file_content:
            messagebox.showwarning("Warning", "Cannot save an empty file.")
            return

        try:
            json_data = json.loads(new_file_content)  # Validate JSON content
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON content. Cannot save the file.")
            return

        # Open file dialog to choose save location and file name
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialdir=services_dir,
            title="Save As"
        )

        if file_path:  # If user did not cancel
            try:
                with open(file_path, 'w') as f:
                    json.dump(json_data, f, indent=4)
                messagebox.showinfo("File Saved", f"New file saved as: {file_path}")
                load_config_files()  # Reload the file list to include the new file
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    # Dropdown menu to select a config file
    dropdown_menu = ttk.Combobox(config_editor_tab, textvariable=selected_file, state="readonly", width=40)
    dropdown_menu.pack(pady=5, padx=10, anchor="nw")
    dropdown_menu.bind("<<ComboboxSelected>>", lambda e: display_json_content())

    # Text widget for displaying and editing JSON content
    json_text = tk.Text(config_editor_tab, wrap="word", width=50)
    json_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # Button to save the edited JSON content as a new file
    save_button = tk.Button(config_editor_tab, text="Save as New File", command=save_as_new_file, bg="green", fg="black")
    save_button.pack(pady=10, padx=10, anchor="se")

    # Load files when the tab is created
    load_config_files()

    return config_editor_tab
