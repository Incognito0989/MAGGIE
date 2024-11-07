import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import main
import ipaddress

# Function to generate the IP range using ipaddress
def ip_range(start_ip, end_ip):
    print(start_ip)
    print(end_ip)
    # Create IP address objects
    start = ipaddress.ip_address(start_ip)
    end = ipaddress.ip_address(end_ip)

    # Iterate through the range of IP addresses
    for ip in range(int(start), int(end) + 1):
        yield ipaddress.ip_address(ip)

def create_tool_tab(notebook, services_dir):
    # Create Tool tab
    tool_tab = ttk.Frame(notebook)
    notebook.add(tool_tab, text="Tool")

    # Mode selection (Config or Inventory)
    mode_notebook = ttk.Notebook(tool_tab)
    mode_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Variables for Config tab inputs
    selected_file = tk.StringVar()
    selected_service_type = tk.StringVar()  # New variable for service type selection
    ip_range_start = tk.StringVar()
    ip_range_end = tk.StringVar()
    inventory_file_loaded = tk.StringVar(value="No file loaded")

    # --- Config Tab ---
    config_frame = ttk.Frame(mode_notebook)
    mode_notebook.add(config_frame, text="By Config")

    # Dropdown for selecting a service type
    ttk.Label(config_frame, text="Select Service Type:").pack(anchor="w", padx=10, pady=5)
    service_type_menu = ttk.Combobox(config_frame, textvariable=selected_service_type, state="readonly", width=40)
    service_type_menu['values'] = ['decode', 'transcode', 'descramble']
    service_type_menu.pack(padx=10, pady=5)

    # Function to filter files based on service type
    def load_config_files():
        if not selected_service_type.get():
            messagebox.showwarning("Selection Error", "Please select a service type.")
            return
        
        # Define path based on selected service type
        service_type = selected_service_type.get()
        service_dir = Path("./payloads/" + service_type)
        if not service_dir.exists():
            messagebox.showwarning("Directory Error", f"No directory found for {service_type}.")
            dropdown_menu['values'] = []
            return

        # Get JSON files from the selected service directory
        files = [file.name for file in service_dir.iterdir() if file.is_file() and file.suffix == '.json']
        dropdown_menu['values'] = files
        if files:
            selected_file.set(files[0])  # Set default selection
        else:
            dropdown_menu['values'] = []

    # Dropdown for selecting a config file
    ttk.Label(config_frame, text="Select Config File:").pack(anchor="w", padx=10, pady=5)
    dropdown_menu = ttk.Combobox(config_frame, textvariable=selected_file, state="readonly", width=40)
    dropdown_menu.pack(padx=10, pady=5)

    # Load files when service type changes
    service_type_menu.bind("<<ComboboxSelected>>", lambda e: load_config_files())

    # IP Range input fields
    ip_frame = tk.Frame(config_frame)
    ip_frame.pack(pady=10, padx=10, anchor="w")

    ttk.Label(ip_frame, text="IP Range Start:").grid(row=0, column=0, padx=5, pady=5)
    ip_start_entry = ttk.Entry(ip_frame, textvariable=ip_range_start, width=20)
    ip_start_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(ip_frame, text="IP Range End:").grid(row=1, column=0, padx=5, pady=5)
    ip_end_entry = ttk.Entry(ip_frame, textvariable=ip_range_end, width=20)
    ip_end_entry.grid(row=1, column=1, padx=5, pady=5)

    # --- Inventory Tab ---
    inventory_frame = ttk.Frame(mode_notebook)
    mode_notebook.add(inventory_frame, text="By Inventory")

    # Inventory file upload button and label to show the loaded file
    def upload_inventory_file():
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            inventory_file_loaded.set(f"Loaded file: {Path(file_path).name}")
            # Optionally, copy or move the file to a specific location for processing

    upload_button = tk.Button(inventory_frame, text="Upload Inventory File", command=upload_inventory_file, bg="blue", fg="black")
    upload_button.pack(pady=10, padx=10)

    # Display loaded inventory file name
    inventory_label = ttk.Label(inventory_frame, textvariable=inventory_file_loaded, foreground="green")
    inventory_label.pack(pady=5, padx=10)

    # Run config based on selected IP range or inventory file
    def begin_config():
        if mode_notebook.index("current") == 0:  # Config mode
            start_ip = ip_range_start.get()
            end_ip = ip_range_end.get() if ip_range_end.get() else ip_range_start.get()
            # Define path based on selected service type
            service_type = selected_service_type.get()
            service_dir = Path("./payloads/" + service_type + "/" + selected_file.get())

            if not start_ip:
                messagebox.showwarning("Input Error", "Please enter an IP range start.")
                return
            messagebox.showinfo("Starting Config", f"Starting config for {service_dir} from IP {start_ip} to {end_ip}.")
            for ip in ip_range(ip_range_start.get(), ip_range_end.get()):
                main.post_auth(ip)
                main.post_decode_service(ip, service_dir)

        elif mode_notebook.index("current") == 1:  # Inventory mode
            if not inventory_file_loaded.get().startswith("Loaded file"):
                messagebox.showwarning("Input Error", "Please upload an inventory file.")
                return
            messagebox.showinfo("Starting Config", f"Configuring based on {inventory_file_loaded.get()}.")

    # Button to start the configuration process
    begin_button = tk.Button(tool_tab, text="Begin Config", command=begin_config, bg="green", fg="black")
    begin_button.pack(side=tk.BOTTOM, pady=10, padx=10, anchor="e")

    return tool_tab
