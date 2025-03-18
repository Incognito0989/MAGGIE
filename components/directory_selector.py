import tkinter as tk
from tkinter import filedialog

class DirectorySelector(tk.Frame):
    def __init__(self, parent, initial_directory="./payloads"):
        super().__init__(parent)
        self.initial_directory = initial_directory
        self.selected_directory_path = None

        self.select_btn = tk.Button(self, text="Select Directory", command=self.select_directory, width=20, font=("Arial", 16))
        self.select_btn.pack(pady=5)

        # Add status_label to display selected directory path
        self.status_label = tk.Label(self, text="", font=("Arial", 12), fg="green")
        self.status_label.pack(pady=5)

    def select_directory(self):
        """Let the user select a directory from the specified directory."""
        path = filedialog.askdirectory(initialdir=self.initial_directory)  # Open directory dialog at the specified directory

        if not path:  # User canceled the dialog
            return  

        self.status_label.config(text=f"Selected Directory: {path}")
        self.selected_directory_path = path


# # Example usage in a Tkinter app
# if __name__ == "__main__":
#     root = tk.Tk()
#     root.title("Directory Selector")

#     # Initialize the component with a specified directory
#     selector = DirectorySelector(root, initial_directory="./your/directory")  # Change to the desired directory path
#     selector.pack(padx=20, pady=20)

#     root.mainloop()
