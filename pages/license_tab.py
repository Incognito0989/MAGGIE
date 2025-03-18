from tkinter import ttk
from components.directory_selector import DirectorySelector
import datetime
import threading
from time import sleep
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import sys
from components.file_dropper import FileDropper
from components.configurator import ConfigPanel
from components.file_selector import FileSelector
from components.status_panel import StatusPanel
from components.ip_range_selector import IPRangeSelector
from utils.ip_utils import *
from utils.meg_utils import MegManager
from utils.switch_utils import *
from settings import *
from components.log_viewer import LogViewer


class LicenseTab:
    def __init__(self, notebook):
        """Initialize the LicenseTab and create the components."""
        self.notebook = notebook
        self.license_tab = ttk.Frame(self.notebook)
        notebook.add(self.license_tab, text="License")

        # Create and pack the ServiceConfigSelector component
        self.selector = DirectorySelector(self.license_tab)
        self.selector.pack(fill="both", expand=True, padx=10, pady=10)  # Make sure to pack it

        # Frame to contain buttons
        button_frame = tk.Frame(self.license_tab)
        button_frame.pack(side=tk.BOTTOM, pady=10)

        # Log Viewer Panel
        self.log_viewer = LogViewer(self.license_tab)
        self.log_viewer.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Begin Config Button
        self.begin_button = tk.Button(button_frame, text="Begin Config", command=self.upload_license, bg="green", fg="black")
        self.begin_button.grid(row=0, column=1, padx=55)

    def connected_ports(self):
        print()
        print("[INFO] Getting active ports")
        self.status_panel.update_all_circle_color(status='disconnected')

        #Get all operational ports to configure
        print("Getting operational ports")
        update_all_ports(switch_ip, 1)
        sleep(10)
        ports = get_active_ports(switch_ip)
        print("ACTIVE PORTS: ")
        print(ports)

        # turn off all ports except management and exceptions and non active
        print("Turning off all active ports")
        update_ports(ports, 2, self)

        return ports


    def upload_license(self):
        def background():
            print(f"[INFO] BEGGINING LICENSE PROCEDURE")
            ports = self.connected_ports()

            for port in ports:
                try:
                    print(f"===================MEG FACTORY RESET ON PORT {(int(port) - 1)}========================")
                    meg = MegManager(payload=None, processing_type=None, service_dir=None)

                    self.status_panel.update_circle_color(port, 'processing')
                    print()

                    meg.upload_license(pwExpire=True, license_dir=self.selector.selected_directory_path)

                    # set status to green    
                    print(f"[SUCCESS] Port {int(port) - 1} factory reset successfully.")
                    self.status_panel.update_circle_color(port, status='success')

                except Exception as e:
                    print(f"[ERROR] Failed on port {int(port) - 1}: {e}")
                    self.status_panel.update_circle_color(port, status='failed')

                finally:
                    print()
                    set_port(switch_ip, port, 2)  # Turn port off
            update_all_ports(switch_ip, 1)


        # Run the process in a separate thread
        self.config_thread = threading.Thread(target=background, daemon=True)
        self.config_thread.start()   