import datetime
from time import sleep
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import ipaddress, sys
from components.status_panel import StatusPanel
from utils.api_utils import *
from components.ip_range_selector import IPRangeSelector
from utils.ip_utils import *
from utils.switch_utils import *
from settings import *

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

def send_payload_all(request_type, payload):
    print()
    print("Send payload to all initiating")

    # turn off all ports except management
    print("Turning off all ports")
    update_all_ports(switch_ip, 2)
    print(get_all_port_status(switch_ip))

    # send payload for each port
    ports = get_port_list(switch_ip)
    ports = [10, 11, 12, 13, 14, 15, 16, 17, 18]
    for port in ports:
        print()
        print(f"Turning port {port} on")
        set_port(switch_ip, port, 1)      # Turn port on

        sleep(6)                  # wait for meg to be reachable
        
        # if not is_port_operational(switch_ip, port):
        #     print("Port not operational")
        #     continue
        # else:
        #     print("PORT OPERATIONAL")

        if is_ip_reachable(base_meg_ip):
            print("Meg is reachable. Continuing with payload")
        else:
            print("Meg is not reachable. Skipping this port")
            continue

        # Get auth for this meg
        print("Getting authorization to meg")
        post_auth(base_meg_ip)

        # make post request to meg
        process_service_for_ip(request_type, base_meg_ip, payload)
        
        # Turn port off
        set_port(switch_ip, port, 2)      
    update_all_ports(switch_ip, 1)
    # print(get_all_port_status(switch_ip))

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

    # ip_range_selector = IPRangeSelector(config_frame)

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

            # Define path based on selected service type
            service_type = selected_service_type.get()
            service_dir = Path("./payloads/" + service_type + "/" + selected_file.get())

            send_payload_all(service_type, service_dir)


        elif mode_notebook.index("current") == 1:  # Inventory mode
            if not inventory_file_loaded.get().startswith("Loaded file"):
                messagebox.showwarning("Input Error", "Please upload an inventory file.")
                return
            messagebox.showinfo("Starting Config", f"Configuring based on {inventory_file_loaded.get()}.")

    # Button to start the configuration process
    begin_button = tk.Button(tool_tab, text="Begin Config", command=begin_config, bg="green", fg="black")
    begin_button.pack(side=tk.BOTTOM, expand=True, pady=10, padx=10, anchor="e")

    # Create and pack the Status Panel on the right side
    # status_panel = StatusPanel(config_frame, port_count=20)
    # status_panel.pack(side="right", fill="y", padx=10, pady=10)

    # # Example update: Set some ports to show different statuses
    # status_panel.update_port_status(1, "off")
    # status_panel.update_port_status(2, "failed")
    # status_panel.update_port_status(3, "complete")

    # Console output display
    console_output = tk.Text(tool_tab, height=40, wrap="word", state="disabled")
    console_output.pack(fill="x", padx=10, pady=5)

    # Redirect stdout and sderr to the Text widget
    sys.stdout = RedirectedOutput(console_output)
    sys.stderr = RedirectedOutput(console_output)

    return tool_tab
