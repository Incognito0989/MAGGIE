import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from components.file_dropper import FileDropper

class ServiceConfigSelector(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Variable initialization
        self.selected_service_type = tk.StringVar()
        self.selected_file = tk.StringVar()
        self.file_path = None  # Initialize file_path as an instance variable

        # Service type dropdown
        ttk.Label(self, text="Select Service Type:").pack(anchor="w", padx=10, pady=5)
        self.service_type_menu = ttk.Combobox(self, textvariable=self.selected_service_type, state="readonly", width=40)
        self.service_type_menu['values'] = ['decode', 'transcode', 'descramble']
        self.service_type_menu.pack(padx=10, pady=5)

        # Config file dropdown
        ttk.Label(self, text="Select Config File:").pack(anchor="w", padx=10, pady=5)
        self.dropdown_menu = ttk.Combobox(self, textvariable=self.selected_file, state="readonly", width=40)
        self.dropdown_menu.pack(padx=10, pady=5)

        # Text widget for displaying and editing JSON content
        self.json_text = tk.Text(parent, wrap="word", width=50)
        self.json_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Buttons for Save and Save As New
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        self.save_button = ttk.Button(button_frame, text="Save", command=self.save_file)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.save_as_button = ttk.Button(button_frame, text="Save As New", command=self.save_file_as_new)
        self.save_as_button.pack(side=tk.LEFT, padx=5)

            #file dropper
        dropper = FileDropper(self)
        dropper.pack(padx=50)

        # Bind events
        self.service_type_menu.bind("<<ComboboxSelected>>", lambda e: self.load_config_files())
        self.dropdown_menu.bind("<<ComboboxSelected>>", lambda e: self.display_json_content())

    def load_config_files(self):
        # Check if a service type is selected
        if not self.selected_service_type.get():
            messagebox.showwarning("Selection Error", "Please select a service type.")
            return

        # Define path based on selected service type
        service_type = self.selected_service_type.get()
        self.service_dir = Path(f"./payloads/{service_type}")
        if not self.service_dir.exists():
            messagebox.showwarning("Directory Error", f"No directory found for {service_type}.")
            self.dropdown_menu['values'] = []
            return

        # Get JSON files from the selected service directory
        files = [file.name for file in self.service_dir.iterdir() if file.is_file() and file.suffix == '.json']
        self.dropdown_menu['values'] = files
        if files:
            self.selected_file.set(files[0])  # Set default selection
            self.file_path = self.service_dir / files[0]  # Set initial file_path
        else:
            self.dropdown_menu['values'] = []
            self.file_path = None  # Clear file_path if no files are found

    def display_json_content(self):
        file_name = self.selected_file.get()
        if not file_name:
            self.json_text.delete("1.0", tk.END)
            self.file_path = None  # Clear file_path if no file is selected
            return

        # Update file_path based on selected file
        self.file_path = self.service_dir / file_name
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            self.json_text.delete("1.0", tk.END)
            self.json_text.insert(tk.END, json.dumps(data, indent=4))
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Selected file is not a valid JSON file.")
            self.json_text.delete("1.0", tk.END)

    def save_file(self):
        # Save content in the JSON text widget to the current file
        if self.file_path is None:
            messagebox.showwarning("Save Error", "No file selected. Use 'Save As New' to create a new file.")
            return

        try:
            content = json.loads(self.json_text.get("1.0", tk.END))
            with open(self.file_path, 'w') as f:
                json.dump(content, f, indent=4)
            messagebox.showinfo("Success", f"File saved: {self.file_path}")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON format. Cannot save.")

    def save_file_as_new(self):
        # Open file dialog to select location and name for saving
        new_file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=self.service_dir
        )

        if new_file_path:
            try:
                content = json.loads(self.json_text.get("1.0", tk.END))
                with open(new_file_path, 'w') as f:
                    json.dump(content, f, indent=4)
                messagebox.showinfo("Success", f"File saved as: {new_file_path}")
                self.file_path = Path(new_file_path)  # Update file_path to new file
                self.selected_file.set(self.file_path.name)  # Update dropdown selection
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Invalid JSON format. Cannot save.")
