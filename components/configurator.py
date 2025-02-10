import json
import tkinter as tk
from tkinter import ttk

class ConfigPanel(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, padding=10, *args, **kwargs)
        
        self.settings = {
            "Satellite": "", "TP": "", "D/L Pol": "", "D/L Freq.": "", "DVB Standard": "", "MOD": "",
            "S.R": "", "FEC": "", "Target PGM ID": "", "Processing Type": "", "Signal Output Format": "",
            "TS Output Video Codec": "", "TS Output Video Resolution": "", "TS Output Video Bitrate": "",
            "TS Output Vid PID Value": "", "TS Output Audio Codec": "", "TS Output Audio Bitrate": "",
            "TS Output Aud PID Value": "", "Total TS Bitrate (incl. Null Packets)": ""
        }

        # Dictionary to specify which fields should have dropdowns and their options
        self.dropdown_fields = {
            "Processing Type": ["Transcode", "Decode"],
            "Signal Output Format": ["SD-SDI", "HD-SDI", "TS-ASI", "TSoIP"],
            "TS Output Video Resolution": ["SD", "HD", "FHD", "UHD", "UHD_8K"],
            "TS Output Video Codec": ["MPEG2", "H.264", "H.265"],
            "DVB Standard": ["ATSC-DCII", "Legacy-ATSC", "DVB"],

        }

        # Dictionary to specify the fields corresponding json param
        self.mapping_dict = {
            "Processing Type": "processing.ProcessingType",
            "Signal Output Format": "output.SignalFormat",
            "TS Output Video Codec": "output.Video.Codec",
            "TS Output Video Resolution": "output.Video.Resolution",
            "TS Output Video Bitrate": "output.Video.Bitrate",
            "TS Output Vid PID Value": "output.Video.PID",
            "TS Output Audio Codec": "output.Audio.Codec",
            "TS Output Audio Bitrate": "output.Audio.Bitrate",
            "TS Output Aud PID Value": "output.Audio.PID",
        }

        self.templates = {
            "Transcode" : "./Templates/DNT_GENERATOR/Transcode.json",
            "Decode" : "./Templates/DNT_GENERATOR/Decode.json",
        }
        
        self.entry_widgets = {}
        self._create_widgets()
    
    def _create_widgets(self):
        settings_keys = list(self.settings.keys())
        section_1, section_2, section_3 = (
            settings_keys[:9], settings_keys[9:15], settings_keys[15:]
        )

        ttk.Label(self, text="Satellite Input", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 5))
        ttk.Label(self, text="Video Output", font=("Arial", 12, "bold")).grid(row=0, column=2, columnspan=2, pady=(0, 5))
        ttk.Label(self, text="Audio Output", font=("Arial", 12, "bold")).grid(row=0, column=4, columnspan=2, pady=(0, 5))

        self._create_section(section_1, 0)
        self._create_section(section_2, 1)
        self._create_section(section_3, 2)
    
    def _create_section(self, keys, col_index, start_row=1):
        for row_index, key in enumerate(keys):
            ttk.Label(self, text=key).grid(row=start_row + row_index, column=col_index * 2, sticky="w", padx=5, pady=2)

            if key in self.dropdown_fields:  # Create a dropdown for specified fields
                combo = ttk.Combobox(self, values=self.dropdown_fields[key], state="readonly", width=18)
                combo.grid(row=start_row + row_index, column=col_index * 2 + 1, padx=5, pady=2)
                combo.current(0)  # Set default selection
                self.entry_widgets[key] = combo
            else:  # Default to Entry box
                entry = ttk.Entry(self, width=20)
                entry.grid(row=start_row + row_index, column=col_index * 2 + 1, padx=5, pady=2)
                self.entry_widgets[key] = entry


    def get_settings(self):
        return {key: self.entry_widgets[key].get() for key in self.entry_widgets}
    
    def all_fields_filled(self):
        """Check if all entry fields have a value."""
        return all(entry.get().strip() for entry in self.entry_widgets.values())
    
    def get_processing_type(self):
        return self.entry_widgets["Processing Type"].get()
    
    def get_payload(self):
        return self.templates.get(self.entry_widgets.get("Processing Type").get())

    def fill_json_template(self):
        """
        Fills a JSON template with data from entry widgets based on a mapping dictionary.
        The template is selected based on the 'Processing Type' field.

        :param template_path: Path to the JSON template file.
        """
        if not self.all_fields_filled():
            print("Please fill in all the fields before submitting.")
            return False

        try:
            # Get the selected processing type
            processing_type = self.entry_widgets.get("Processing Type").get()

            # Get the corresponding template path
            template_path = self.templates.get(processing_type)
            if not template_path:
                print(f"No template found for Processing Type: {processing_type}")
                return False

            # Load the JSON template
            with open(template_path, "r") as file:
                template = json.load(file)

            # Update the template with user inputs
            for ui_label, json_key in self.mapping_dict.items():
                if ui_label in self.entry_widgets:
                    value = self.entry_widgets[ui_label].get().strip()
                    if value:  # Ensure value is not empty
                        keys = json_key.split(".")  # Split nested keys
                        sub_template = template

                        # Traverse the JSON structure to set the value
                        for key in keys[:-1]:
                            sub_template = sub_template.setdefault(key, {})  # Create nested keys if not present

                        sub_template[keys[-1]] = value  # Set the final key

            # Save the updated JSON file
            with open(template_path, "w") as file:
                json.dump(template, file, indent=4)

            print(f"JSON file updated and saved to {template_path}")
            return True

        except Exception as e:
            print(f"Error processing JSON: {e}")
            return False




# # Example usage
# if __name__ == "__main__":
#     root = tk.Tk()
#     root.title("Configuration Panel")
    
#     config_panel = ConfigPanel(root)
#     config_panel.pack(padx=10, pady=10)
    
#     def print_settings():
#         print(config_panel.get_settings())
    
#     ttk.Button(root, text="Get Settings", command=print_settings).pack(pady=10)
    
#     root.mainloop()
