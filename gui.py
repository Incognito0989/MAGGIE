import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from pathlib import Path
import json
import main
import ipaddress

# Initialize the main window
root = tk.Tk()
root.title("Configuration Tool")
root.geometry("800x400")

# Variable to store the selected config file
selected_file = tk.StringVar()

# Function to generate the IP range using ipaddress
def ip_range(start_ip, end_ip):
    # Create IP address objects
    start = ipaddress.ip_address(start_ip)
    end = ipaddress.ip_address(end_ip)

    # Iterate through the range of IP addresses
    for ip in range(int(start), int(end) + 1):
        yield ipaddress.ip_address(ip)

# Function to load available config files from the "Services" directory
def load_config_files():
    services_dir = Path(__file__).parent / "Services"
    if services_dir.exists() and services_dir.is_dir():
        files = [file.name for file in services_dir.iterdir() if file.is_file() and file.suffix == '.json']
        dropdown_menu['values'] = files
        selected_file.set('')  # Reset selected file
        root.services_dir = services_dir
    else:
        messagebox.showerror("Error", "The 'Services' directory does not exist.")
        dropdown_menu['values'] = []

# Function to display JSON content of the selected file in the side panel
def display_json_content():
    if not selected_file.get():
        json_text.delete("1.0", tk.END)
        return

    file_path = root.services_dir / selected_file.get()
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        json_text.delete("1.0", tk.END)
        json_text.insert(tk.END, json.dumps(data, indent=4))
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Selected file is not a valid JSON file.")
        json_text.delete("1.0", tk.END)

# Function to begin the configuration process
def begin_config():
    ip_range_start = ip_start_entry.get()
    ip_range_end = ip_end_entry.get()
    if not ip_range_start or not ip_range_end:
        messagebox.showwarning("Input Error", "Please enter both IP ranges.")
        return
    messagebox.showinfo("Configuration Started", f"Starting configuration for IP range {ip_range_start} to {ip_range_end}.")
    
    selected_file_path = root.services_dir / selected_file.get()
    
    for ip in ip_range(ip_range_start, ip_range_end):
        main.post_auth(ip)
        main.post_decode_service(ip, selected_file_path)

# Frame for the main configuration file management
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# Left Frame for the dropdown and IP inputs
left_frame = tk.Frame(main_frame)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

# Dropdown menu to select the config file
dropdown_menu = ttk.Combobox(left_frame, textvariable=selected_file, state="readonly", width=40)
dropdown_menu.pack(pady=5)
dropdown_menu.bind("<<ComboboxSelected>>", lambda e: display_json_content())

# Input boxes for IP range
ip_frame = tk.Frame(left_frame)
ip_frame.pack(pady=10)

ip_start_label = tk.Label(ip_frame, text="IP Range Start:")
ip_start_label.grid(row=0, column=0, padx=5, pady=5)

ip_start_entry = tk.Entry(ip_frame)
ip_start_entry.grid(row=0, column=1, padx=5, pady=5)

ip_end_label = tk.Label(ip_frame, text="IP Range End:")
ip_end_label.grid(row=1, column=0, padx=5, pady=5)

ip_end_entry = tk.Entry(ip_frame)
ip_end_entry.grid(row=1, column=1, padx=5, pady=5)

# Begin Config button
button_begin = tk.Button(left_frame, text="Begin Config", command=begin_config, bg="blue", fg="black")
button_begin.pack(pady=10)

# Right Frame for JSON content display
right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

json_text = tk.Text(right_frame, wrap="word", width=50, state='normal')
json_text.pack(fill=tk.BOTH, expand=True)

# Load config files on startup
load_config_files()

# Run the Tkinter event loop
root.mainloop()
