import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time
import csv
import os
import math
from datetime import datetime

try:
    from sensors import init_i2c, init_bme280, init_bno085
    SENSORS_IMPORT_ERROR = None
except Exception as e:
    init_i2c = None
    init_bme280 = None
    init_bno085 = None
    SENSORS_IMPORT_ERROR = e

class LabControlSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Laser Analysis & Sample Control System")
        self.root.geometry("1000x700")

        # --- Variables ---
        self.is_experimenting = False
        self.current_file = None
        self.current_sample = tk.IntVar(value=1)
        self.accel_val = tk.DoubleVar(value=0.00)
        self.temp_val = tk.DoubleVar(value=0.00)
        self.humid_val = tk.DoubleVar(value=0.00)

        # Sensor state
        self.i2c = None
        self.bme280 = None
        self.bno = None
        self.sensor_error_logged = False
        
        # New variables for File Saving
        self.save_to_file = tk.BooleanVar(value=False)
        self.file_path_var = tk.StringVar(value="")
        
        # --- UI Layout ---
        self.setup_ui()

        # --- Camera Setup ---
        self.cap = cv2.VideoCapture(0)
        self.update_camera()

        # --- Sensor Setup ---
        self.init_sensors()

        # --- Sensor Refresh ---
        self.update_sensors()

        # Ensure hardware resources are released on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # Left Panel: Camera Feed (Fixed side to match your provided code)
        self.video_frame = tk.Frame(self.root, bg="black", width=640, height=480)
        self.video_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.cam_label = tk.Label(self.video_frame)
        self.cam_label.pack()

        # Right Panel: Controls
        self.control_panel = tk.Frame(self.root)
        self.control_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # Section 1: Readouts
        tk.Label(self.control_panel, text="Sensor Readouts", font=('Arial', 14, 'bold')).pack(pady=5)
        self.create_readout("Acceleration (g):", self.accel_val)
        self.create_readout("Temperature (°C):", self.temp_val)
        self.create_readout("Humidity (%):", self.humid_val)

        tk.Frame(self.control_panel, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=10)

        # Section 2: Sample Navigation
        tk.Label(self.control_panel, text="Platform Control", font=('Arial', 12, 'bold')).pack()
        nav_frame = tk.Frame(self.control_panel)
        nav_frame.pack(pady=5)
        
        tk.Label(nav_frame, text="Current Sample:").grid(row=0, column=0)
        tk.Entry(nav_frame, textvariable=self.current_sample, width=5).grid(row=0, column=1)
        tk.Button(nav_frame, text="Go to Sample", command=self.move_platform).grid(row=0, column=2, padx=5)
        tk.Button(self.control_panel, text="Next Sample", command=self.next_sample).pack(pady=5)

        tk.Frame(self.control_panel, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=10)

        # Section 3: File Settings
        tk.Label(self.control_panel, text="Data Logging Settings", font=('Arial', 12, 'bold')).pack()
        tk.Checkbutton(self.control_panel, text="Save Data to File", variable=self.save_to_file).pack()
        
        file_frame = tk.Frame(self.control_panel)
        file_frame.pack(pady=5)
        tk.Label(file_frame, text="File Path:").pack(side=tk.LEFT)
        tk.Entry(file_frame, textvariable=self.file_path_var, width=20).pack(side=tk.LEFT, padx=5)

        # Section 4: Experiment Control
        self.btn_exp = tk.Button(self.control_panel, text="START EXPERIMENT", bg="green", fg="white", 
                                 font=('Arial', 12, 'bold'), command=self.toggle_experiment)
        self.btn_exp.pack(pady=10, fill=tk.X)

        self.btn_fire = tk.Button(self.control_panel, text="FIRE LASER", bg="#2e2e2e", fg="#555555", font=('Arial',14,'bold'), 
                                    state=tk.DISABLED, relief=tk.FLAT, highlightthickness=0, command=self.fire_laser)
        self.btn_fire.pack(pady=10, fill=tk.X)

    def create_readout(self, label_text, variable):
        f = tk.Frame(self.control_panel)
        f.pack(fill=tk.X, pady=2)
        tk.Label(f, text=label_text).pack(side=tk.LEFT)
        tk.Label(f, textvariable=variable, font=('Courier', 12, 'bold'), fg="blue").pack(side=tk.RIGHT)

    def update_camera(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (640, 480))
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=img)
            self.cam_label.imgtk = imgtk
            self.cam_label.configure(image=imgtk)
        self.root.after(10, self.update_camera)

    def init_sensors(self):
        if SENSORS_IMPORT_ERROR is not None:
            print(f"Sensor module unavailable: {SENSORS_IMPORT_ERROR}")
            return

        try:
            self.i2c = init_i2c()
            self.bme280 = init_bme280(self.i2c)
            self.bno = init_bno085(self.i2c)
            print("Sensors initialized successfully")
        except Exception as e:
            print(f"Sensor init failed: {e}")
            self.i2c = None
            self.bme280 = None
            self.bno = None

    def update_sensors(self):
        if self.bme280 is not None and self.bno is not None:
            try:
                temperature = self.bme280.temperature
                humidity = self.bme280.relative_humidity
                accel_x, accel_y, accel_z = self.bno.acceleration

                accel_magnitude_g = (
                    math.sqrt(accel_x ** 2 + accel_y ** 2 + accel_z ** 2) / 9.80665
                )

                self.temp_val.set(round(temperature, 2))
                self.humid_val.set(round(humidity, 2))
                self.accel_val.set(round(accel_magnitude_g, 3))
                self.sensor_error_logged = False
            except Exception as e:
                if not self.sensor_error_logged:
                    print(f"Sensor read failed: {e}")
                    self.sensor_error_logged = True

        self.root.after(500, self.update_sensors)

    def on_close(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()

        if self.i2c is not None:
            try:
                self.i2c.deinit()
            except Exception:
                pass

        self.root.destroy()

    def move_platform(self):
        print(f"Moving platform to Sample {self.current_sample.get()} position...")

    def next_sample(self):
        self.current_sample.set(self.current_sample.get() + 1)
        self.move_platform()

    def toggle_experiment(self):
        if not self.is_experimenting:
            self.is_experimenting = True
            
            # --- File Initialization Logic ---
            if self.save_to_file.get():
                path = self.file_path_var.get().strip()
                if not path:
                    # Create new timestamped file if path is empty
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    self.current_file = f"experiment_{timestamp}.csv"
                else:
                    # Use specified path (ensure .csv extension)
                    self.current_file = path if path.endswith('.csv') else path + ".csv"
                
                # If file doesn't exist, create it and write header
                if not os.path.exists(self.current_file):
                    with open(self.current_file, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(["Timestamp", "Sample_No", "Accel_g", "Temp_C", "Humidity_Prc"])
            else:
                self.current_file = None

            self.btn_exp.config(text="STOP EXPERIMENT", bg="orange")
            self.btn_fire.config(state=tk.NORMAL, bg="red", fg="white", activebackground="#ff6666")
        else:
            self.is_experimenting = False
            self.btn_exp.config(text="START EXPERIMENT", bg="green")
            self.btn_fire.config(state=tk.DISABLED, bg="#2e2e2e", fg="#555555")

    def fire_laser(self):
        print("LASER FIRED")
        if self.is_experimenting and self.save_to_file.get() and self.current_file:
            data = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.current_sample.get(),
                self.accel_val.get(),
                self.temp_val.get(),
                self.humid_val.get()
            ]
            with open(self.current_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(data)
            print(f"Data Appended to {self.current_file}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LabControlSystem(root)
    root.mainloop()