import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import ipaddress, sys
from utils.api_utils import *
from components.ip_range_selector import IPRangeSelector
from utils.ip_utils import *
class RedirectedOutput:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        # Add a timestamp before each message
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Format timestamp as you wish
        message_with_timestamp = f"[{timestamp}] {message}"

        # Temporarily enable the text widget to insert text
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message_with_timestamp)
        self.text_widget.see(tk.END)  # Auto-scroll to the latest output
        self.text_widget.config(state=tk.DISABLED)  # Disable it again to prevent editing

    def flush(self):  # To handle interactive environments
        pass

def create_tool_tab(notebook, services_dir):
    # Create Tool tab
    tool_tab = ttk.Frame(notebook)
    notebook.add(tool_tab, text="Tool")

    # Mode selection (Config or Inventory)
    mode_notebook = ttk.Notebook(tool_tab)
    mode_notebook.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

    # Variables for Config tab inputs
    selected_file = tk.StringVar()
    selected_service_type = tk.StringVar()  # New variable for service type selection
    inventory_file_loaded = tk.StringVar(value="No file loaded")

    send_to_all_connected = tk.BooleanVar()  # Variable for the checkbox


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

    # # IP Range input fields
    # ip_frame = tk.Frame(config_frame)
    # ip_frame.pack(pady=10, padx=10, anchor="w")

    # ttk.Label(ip_frame, text="IP Range Start:").grid(row=0, column=0, padx=5, pady=5)
    # ip_start_entry = ttk.Entry(ip_frame, textvariable=ip_range_start, width=20)
    # ip_start_entry.grid(row=0, column=1, padx=5, pady=5)

    # ttk.Label(ip_frame, text="IP Range End:").grid(row=1, column=0, padx=5, pady=5)
    # ip_end_entry = ttk.Entry(ip_frame, textvariable=ip_range_end, width=20)
    # ip_end_entry.grid(row=1, column=1, padx=5, pady=5)

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

    ip_range_selector = IPRangeSelector(config_frame)

    # Run config based on selected IP range or inventory file
    def begin_config():
        # Validate that both the service type and config file are selected
        if not selected_service_type.get():
            print("Please select a service type.")
            return
        if not selected_file.get():
            print("Please select a config file.")
            return
    
        if mode_notebook.index("current") == 0:  # Config mode
            start_ip = ip_range_selector.get_ip_start()
            end_ip = ip_range_selector.get_ip_end() if ip_range_selector.get_ip_end else ip_range_selector.get_ip_start()

            # Define path based on selected service type
            service_type = selected_service_type.get()
            service_dir = Path("./payloads/" + service_type + "/" + selected_file.get())

            if not start_ip:
                messagebox.showwarning("Input Error", "Please enter an IP range start.")
                return
            print(f"Starting config for {service_dir} from IP {start_ip} to {end_ip}.")
            for ip in ip_range(start_ip, end_ip):
                if is_ip_reachable(ip):
                    print(f"IP {ip} is reachable. Proceeding with configuration.")
                    post_auth(ip)
                    process_service_for_ip(selected_service_type.get(), ip, service_dir)
                else: continue


        elif mode_notebook.index("current") == 1:  # Inventory mode
            if not inventory_file_loaded.get().startswith("Loaded file"):
                messagebox.showwarning("Input Error", "Please upload an inventory file.")
                return
            messagebox.showinfo("Starting Config", f"Configuring based on {inventory_file_loaded.get()}.")

    # Button to start the configuration process
    begin_button = tk.Button(tool_tab, text="Begin Config", command=begin_config, bg="green", fg="black")
    begin_button.pack(side=tk.BOTTOM, expand=True, pady=10, padx=10, anchor="e")

    # Console output display
    console_output = tk.Text(tool_tab, height=40, wrap="word", state="disabled")
    console_output.pack(fill="x", padx=10, pady=5)

    # Redirect stdout and sderr to the Text widget
    sys.stdout = RedirectedOutput(console_output)
    sys.stderr = RedirectedOutput(console_output)

    return tool_tab
