import ctypes
import math
import random
import sys

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCharts import QChart, QChartView, QLineSeries

from optimisation_ntn.simulation import Simulation

# Task bar Icon on Windows 11
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("optimisation_ntn")


class SimulationUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NTN Simulation Manager")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet("background-color: #2e2e2e; color: white;")
        self.current_view = "close"  # Initialize with close-up view
        self.setWindowIcon(QtGui.QIcon("images/logo.png"))  # Set the logo icon
        self.simulation = None
        self.initUI()

    def initUI(self):
        main_layout = QtWidgets.QHBoxLayout()

        # Left Panel for Simulation Management and Parameters
        left_panel = QtWidgets.QVBoxLayout()
        left_panel.setAlignment(QtCore.Qt.AlignTop)
        left_panel.addWidget(self.create_simulation_manager())
        left_panel.addWidget(self.create_parameter_panel())
        main_layout.addLayout(left_panel, 1)

        # Main Display Tabs
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.create_real_time_view(), "Real-Time View")
        tabs.addTab(self.create_results_tab(), "Results History")
        main_layout.addWidget(tabs, 3)

        # Set central widget
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def create_simulation_manager(self):
        sim_manager_box = QtWidgets.QGroupBox("Simulations")
        sim_layout = QtWidgets.QVBoxLayout()
        self.sim_list = QtWidgets.QListWidget()
        self.sim_list.itemSelectionChanged.connect(self.update_simulation_selection)
        sim_layout.addWidget(self.sim_list)

        add_sim_btn = QtWidgets.QPushButton("Add Simulation")
        add_sim_btn.clicked.connect(self.add_simulation)
        reset_sim_btn = QtWidgets.QPushButton("Reset Simulation")
        reset_sim_btn.clicked.connect(self.reset_simulation)
        play_btn = QtWidgets.QPushButton("Play Simulation")
        play_btn.clicked.connect(self.start_simulation)

        sim_layout.addWidget(add_sim_btn)
        sim_layout.addWidget(reset_sim_btn)
        sim_layout.addWidget(play_btn)
        sim_manager_box.setLayout(sim_layout)
        return sim_manager_box

    def create_parameter_panel(self):
        param_box = QtWidgets.QGroupBox("Simulation Parameters")
        param_layout = QtWidgets.QVBoxLayout()

        param_layout.addWidget(QtWidgets.QLabel("Number of LEO Satellites"))
        self.num_leo_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.num_leo_slider.setRange(1, 10)
        param_layout.addWidget(self.num_leo_slider)

        param_layout.addWidget(QtWidgets.QLabel("Number of Base Stations"))
        self.num_bs_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.num_bs_slider.setRange(1, 10)
        param_layout.addWidget(self.num_bs_slider)

        param_layout.addWidget(QtWidgets.QLabel("Satellite Initial Position"))
        self.satellite_position = QtWidgets.QSpinBox()
        self.satellite_position.setRange(0, 360)
        param_layout.addWidget(self.satellite_position)

        param_layout.addWidget(QtWidgets.QLabel("Select Algorithm"))
        self.algorithm_dropdown = QtWidgets.QComboBox()
        self.algorithm_dropdown.addItems(["Genetic Algorithm", "Q-Learning"])
        param_layout.addWidget(self.algorithm_dropdown)

        param_box.setLayout(param_layout)
        return param_box

    def create_real_time_view(self):
        layout = QtWidgets.QVBoxLayout()

        # Schematic View with QGraphicsView
        self.schematic_view = QtWidgets.QGraphicsView()
        layout.addWidget(self.schematic_view)

        # Add toggle button to switch between views
        self.view_toggle_btn = QtWidgets.QPushButton("Switch to Far View")
        self.view_toggle_btn.clicked.connect(self.toggle_view)
        layout.addWidget(self.view_toggle_btn)

        # Energy Graphs
        live_graph_layout = QtWidgets.QHBoxLayout()
        self.energy_chart = self.create_live_graph("Component Energy")
        self.system_energy_chart = self.create_live_graph("Total System Energy")
        live_graph_layout.addWidget(self.energy_chart)
        live_graph_layout.addWidget(self.system_energy_chart)
        layout.addLayout(live_graph_layout)

        # Load initial close-up view
        self.load_close_up_view()

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container

    def toggle_view(self):
        if self.current_view == "close":
            self.load_far_view()
            self.current_view = "far"
            self.view_toggle_btn.setText("Switch to Close-Up View")
        else:
            self.load_close_up_view()
            self.current_view = "close"
            self.view_toggle_btn.setText("Switch to Far View")

    def load_close_up_view(self):
        scene = QtWidgets.QGraphicsScene()
        if self.simulation:  # Only load components if a simulation is selected
            self.add_grid(scene)
            haps_pixmap = QtGui.QPixmap("images/haps.png")
            haps_item = QtWidgets.QGraphicsPixmapItem(haps_pixmap)
            haps_item.setPos(300, 100)
            scene.addItem(haps_item)

            base_station_pixmap = QtGui.QPixmap("images/base_station.png")
            for i in range(4):
                bs_item = QtWidgets.QGraphicsPixmapItem(base_station_pixmap)
                bs_item.setPos(100 + i * 150, 500)
                scene.addItem(bs_item)

            leo_pixmap = QtGui.QPixmap("images/leo.png")
            for i in range(2):
                leo_item = QtWidgets.QGraphicsPixmapItem(leo_pixmap)
                leo_item.setPos(400 + i * 100, 50)
                scene.addItem(leo_item)

        self.schematic_view.setScene(scene)

    def load_far_view(self):
        scene = QtWidgets.QGraphicsScene()
        if self.simulation:  # Only load components if a simulation is selected
            earth_pixmap = QtGui.QPixmap("images/earth.png")
            earth_item = QtWidgets.QGraphicsPixmapItem(earth_pixmap)
            earth_item.setPos(300, 300)
            scene.addItem(earth_item)

            leo_pixmap = QtGui.QPixmap("images/leo.png")
            for i in range(4):
                angle = i * 90
                x = 300 + 150 * math.cos(math.radians(angle))
                y = 300 + 150 * math.sin(math.radians(angle))
                leo_item = QtWidgets.QGraphicsPixmapItem(leo_pixmap)
                leo_item.setPos(x, y)
                scene.addItem(leo_item)

            self.schematic_view.setScene(scene)

    def add_simulation(self):
        # Create a new simulation based on parameters
        self.simulation = Simulation()  # TODO : Add parameters

        item = QtWidgets.QListWidgetItem(f"Simulation {self.sim_list.count() + 1}")
        self.sim_list.addItem(item)

    def reset_simulation(self):
        if self.simulation:
            self.simulation.reset()
            print("Simulation reset.")

    def start_simulation(self):
        if self.simulation:
            print("Starting simulation...")
            self.simulation.run(max_time=1000)

    def update_simulation_selection(self):
        if self.sim_list.currentItem():
            # Enable components in the view if a simulation is selected
            self.load_close_up_view()
        else:
            self.schematic_view.setScene(
                QtWidgets.QGraphicsScene()
            )  # Clear the view if no simulation is selected

    def add_grid(self, scene):
        grid_size = 50
        for x in range(0, 800, grid_size):
            line = scene.addLine(x, 0, x, 600, QtGui.QPen(QtGui.QColor("#444")))
            line.setOpacity(0.5)
        for y in range(0, 600, grid_size):
            line = scene.addLine(0, y, 800, y, QtGui.QPen(QtGui.QColor("#444")))
            line.setOpacity(0.5)

    def create_live_graph(self, title):
        series = QLineSeries()
        series.append(0, random.uniform(50, 150))
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.createDefaultAxes()
        chart.setBackgroundBrush(QtGui.QColor("#2e2e2e"))
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        return chart_view

    def create_results_tab(self):
        layout = QtWidgets.QVBoxLayout()
        self.results_list = QtWidgets.QListWidget()
        layout.addWidget(QtWidgets.QLabel("Previous Simulation Results"))
        layout.addWidget(self.results_list)
        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container


app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon("images/logo.png"))  # Taskbar icon
window = SimulationUI()
window.show()
sys.exit(app.exec())
