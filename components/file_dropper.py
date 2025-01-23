import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox


class FileDropper(tk.Frame):
    def __init__(self, parent, save_directory="./payloads", width=600, height=300, color="lightblue"):
        """
        Initialize the FileDropper component.

        Args:
            parent (tk.Widget): Parent widget.
            save_directory (str): Directory where files will be saved.
            width (int): Width of the FileDropper.
            height (int): Height of the FileDropper.
        """
        super().__init__(parent, bg="white", width=width, height=height)

        self.save_directory = save_directory
        self.width = width
        self.height = height

        # Configure the frame
        self.configure(width=self.width, height=self.height, relief="ridge", borderwidth=2)

        # Add instructions
        self.label = tk.Label(
            self,
            text="Click to Add a File",
            bg=color,
            fg="black",
            font=("Arial", 12),
            wraplength=width - 20,
        )
        self.label.pack(expand=True, fill="both")

        # Bind click event to select files
        self.bind("<Button-1>", self.browse_file)
        self.label.bind("<Button-1>", self.browse_file)

    def browse_file(self, event=None):
        """Opens a file dialog to select a file."""
        file_path = filedialog.askopenfilename(title="Select a File")
        if file_path:
            self.process_file(file_path)

    # def save_file(self, file_path):
    #     """Saves the selected file to the specified directory."""
    #     if not os.path.exists(self.save_directory):
    #         os.makedirs(self.save_directory)

    #     filename = os.path.basename(file_path)
    #     destination = os.path.join(self.save_directory, filename)

    #     try:
    #         with open(file_path, "rb") as src_file:
    #             with open(destination, "wb") as dest_file:
    #                 dest_file.write(src_file.read())
    #         messagebox.showinfo("Success", f"File saved to: {destination}")
    #     except Exception as e:
    #         messagebox.showerror("Error", f"Failed to save file: {e}")

    def process_file(self, file_path):
            # Read and determine service type
            try:
                with open(file_path, "r") as f:
                    file_data = json.load(f)

                # Get processing type
                service_type = file_data.get("processing", {}).get("processingType", "").lower()

                # Map service type to directory
                if "transcode" in service_type:
                    save_path = os.path.join(self.save_directory, "transcode")
                elif "decode" in service_type:
                    save_path = os.path.join(self.save_directory, "decode")
                elif "descramble" in service_type:
                    save_path = os.path.join(self.save_directory, "descramble")
                else:
                    print(f"Unknown processing type: {service_type}. File will not be saved.")
                    return

                # Ensure the directory exists
                os.makedirs(save_path, exist_ok=True)

                # Save the file
                base_filename = os.path.basename(file_path)
                save_file_path = os.path.join(save_path, base_filename)
                with open(save_file_path, "w") as f:
                    json.dump(file_data, f, indent=4)

                print(f"File saved to: {save_file_path}")

            except Exception as e:
                print(f"Error processing file: {e}")
