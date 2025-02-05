import tkinter as tk
from tkinter import filedialog

class FileSelector(tk.Frame):
    def __init__(self, parent, initial_directory="./payloads"):
        super().__init__(parent)
        self.initial_directory = initial_directory
        self.selected_file_path = None

        self.select_btn = tk.Button(self, text="Select File", command=self.select_file, width=20, font=("Arial", 16))
        self.select_btn.pack(pady=5)

        # Add status_label to display selected file path
        self.status_label = tk.Label(self, text="", font=("Arial", 12), fg="green")
        self.status_label.pack(pady=5)

    def select_file(self):
        """Let the user select a file from the specified directory."""
        path = filedialog.askopenfilename(initialdir=self.initial_directory)  # Open file dialog at the specified directory

        if not path:  # User canceled the dialog
            return  

        self.status_label.config(text=f"Selected File: {path}")
        self.selected_file_path = path


# # Example usage in a Tkinter app
# if __name__ == "__main__":
#     root = tk.Tk()
#     root.title("File Selector")

#     # Initialize the component with a specified directory
#     selector = FileSelector(root, initial_directory="./your/directory")  # Change to the desired directory path
#     selector.pack(padx=20, pady=20)

#     root.mainloop()
