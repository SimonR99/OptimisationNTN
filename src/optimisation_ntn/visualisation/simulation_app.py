import threading
import time
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from optimisation_ntn.network import Network
from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.leo import LEO


class SimulationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NTN Optimization Simulation")

        self.network = Network()

        self.running = False
        self.simulation_speed = 1.0  # Speed factor for the simulation
        self.simulation_thread = None

        # Create UI Elements
        self.start_button = ttk.Button(
            root, text="Start", command=self.start_simulation
        )
        self.start_button.grid(row=0, column=0, padx=10, pady=10)

        self.stop_button = ttk.Button(root, text="Stop", command=self.stop_simulation)
        self.stop_button.grid(row=0, column=1, padx=10, pady=10)

        self.reset_button = ttk.Button(
            root, text="Reset", command=self.reset_simulation
        )
        self.reset_button.grid(row=0, column=2, padx=10, pady=10)

        self.speed_label = ttk.Label(root, text="Speed:")
        self.speed_label.grid(row=1, column=0, padx=10, pady=10)

        self.speed_scale = ttk.Scale(
            root, from_=0.1, to=5.0, orient="horizontal", command=self.change_speed
        )
        self.speed_scale.set(1.0)
        self.speed_scale.grid(row=1, column=1, columnspan=2, padx=10, pady=10)

        self.status_label = ttk.Label(root, text="Status: Stopped")
        self.status_label.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

        # Images for base stations, HAPS, and LEO
        self.load_images()
        self.display_node_counts()

    def load_images(self):
        self.base_station_image = Image.open("images/base_station.png")
        self.base_station_image = self.base_station_image.resize((50, 50))
        self.base_station_photo = ImageTk.PhotoImage(self.base_station_image)

        self.haps_image = Image.open("images/haps.png")
        self.haps_image = self.haps_image.resize((50, 50))
        self.haps_photo = ImageTk.PhotoImage(self.haps_image)

        self.leo_image = Image.open("images/leo.png")
        self.leo_image = self.leo_image.resize((50, 50))
        self.leo_photo = ImageTk.PhotoImage(self.leo_image)

    def display_node_counts(self):
        base_station_count = len(
            [node for node in self.network.nodes if isinstance(node, BaseStation)]
        )
        haps_count = len(
            [node for node in self.network.nodes if isinstance(node, HAPS)]
        )
        leo_count = len([node for node in self.network.nodes if isinstance(node, LEO)])

        self.base_station_label = ttk.Label(self.root, image=self.base_station_photo)
        self.base_station_label.grid(row=3, column=0, padx=10, pady=10)
        self.base_station_count_label = ttk.Label(
            self.root, text=f"Base Stations: {base_station_count}"
        )
        self.base_station_count_label.grid(row=4, column=0, padx=10, pady=10)

        self.haps_label = ttk.Label(self.root, image=self.haps_photo)
        self.haps_label.grid(row=3, column=1, padx=10, pady=10)
        self.haps_count_label = ttk.Label(self.root, text=f"HAPS: {haps_count}")
        self.haps_count_label.grid(row=4, column=1, padx=10, pady=10)

        self.leo_label = ttk.Label(self.root, image=self.leo_photo)
        self.leo_label.grid(row=3, column=2, padx=10, pady=10)
        self.leo_count_label = ttk.Label(self.root, text=f"LEO Satellites: {leo_count}")
        self.leo_count_label.grid(row=4, column=2, padx=10, pady=10)

    def start_simulation(self):
        if not self.running:
            self.running = True
            self.simulation_thread = threading.Thread(target=self.run_simulation)
            self.simulation_thread.start()
            self.status_label.config(text="Status: Running")

    def stop_simulation(self):
        self.running = False
        if self.simulation_thread is not None:
            self.simulation_thread.join()
        self.status_label.config(text="Status: Stopped")

    def reset_simulation(self):
        self.stop_simulation()
        self.status_label.config(text="Status: Reset")
        self.display_node_counts()

    def change_speed(self, value):
        self.simulation_speed = float(value)

    def run_simulation(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationApp(root)
    root.mainloop()
