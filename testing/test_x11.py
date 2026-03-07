# test_gui.py
import tkinter as tk

root = tk.Tk()
root.title("Test GUI")
label = tk.Label(root, text="Hello from Raspberry Pi!")
label.pack()
root.mainloop()