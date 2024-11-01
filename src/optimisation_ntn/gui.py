import ctypes
import math
import random
import sys

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCharts import QChart, QChartView, QLineSeries

from .nodes.base_station import BaseStation
from .nodes.haps import HAPS
from .nodes.user_device import UserDevice
from .simulation import Simulation

# Task bar Icon on Windows 11
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("optimisation_ntn")


class SimulationUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimisation NTN")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("background-color: #2e2e2e; color: white;")
        self.current_view = "close"
        self.show_links = False
        self.setWindowIcon(QtGui.QIcon("images/logo.png"))
        self.simulation = None
        self.initUI()

    def initUI(self):
        main_layout = QtWidgets.QHBoxLayout()

        # Left Panel for Simulation Management and Control (full height)
        left_panel = QtWidgets.QVBoxLayout()
        left_panel.addWidget(self.create_simulation_list())
        left_panel.addWidget(self.create_simulation_control())
        main_layout.addLayout(left_panel, 1)

        # Center and Right content
        center_right_layout = QtWidgets.QVBoxLayout()

        # Upper content (Simulation view and graphs)
        upper_content = QtWidgets.QHBoxLayout()

        # Center display with tabs
        center_layout = QtWidgets.QVBoxLayout()
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.create_real_time_view(), "Real-time")
        tabs.addTab(self.create_results_tab(), "Result")
        center_layout.addWidget(tabs)
        upper_content.addLayout(center_layout, 2)

        # Right panel for graphs
        right_panel = QtWidgets.QVBoxLayout()
        right_panel.addWidget(self.create_live_graph("Throughput"))
        right_panel.addWidget(self.create_live_graph("Energy"))
        upper_content.addLayout(right_panel, 1)

        # Add upper content to center-right layout
        center_right_layout.addLayout(upper_content)

        # Add simulation parameters at the bottom
        bottom_panel = self.create_simulation_parameters()
        center_right_layout.addWidget(bottom_panel)

        # Add center-right content to main layout
        main_layout.addLayout(center_right_layout, 3)

        # Set central widget
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def create_simulation_list(self):
        sim_list_box = QtWidgets.QGroupBox("Simulations")
        sim_layout = QtWidgets.QVBoxLayout()
        self.sim_list = QtWidgets.QListWidget()
        self.sim_list.itemSelectionChanged.connect(self.update_simulation_selection)
        sim_layout.addWidget(self.sim_list)

        create_btn = QtWidgets.QPushButton("New")
        create_btn.clicked.connect(self.create_new_simulation)
        delete_btn = QtWidgets.QPushButton("Delete")
        load_btn = QtWidgets.QPushButton("Load")
        load_btn.clicked.connect(self.load_simulation)
        duplicate_btn = QtWidgets.QPushButton("Duplicate")
        duplicate_btn.clicked.connect(self.duplicate_simulation)

        sim_layout.addWidget(create_btn)
        sim_layout.addWidget(delete_btn)
        sim_layout.addWidget(load_btn)
        sim_layout.addWidget(duplicate_btn)
        sim_list_box.setLayout(sim_layout)
        return sim_list_box

    def create_simulation_control(self):
        control_box = QtWidgets.QGroupBox("Simulation Control")
        control_layout = QtWidgets.QVBoxLayout()

        run_btn = QtWidgets.QPushButton("Run")
        run_btn.clicked.connect(self.start_simulation)
        reset_btn = QtWidgets.QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_simulation)
        save_btn = QtWidgets.QPushButton("Save")

        control_layout.addWidget(run_btn)
        control_layout.addWidget(reset_btn)
        control_layout.addWidget(save_btn)
        control_box.setLayout(control_layout)
        return control_box

    def create_simulation_parameters(self):
        param_box = QtWidgets.QGroupBox("Simulation Parameters")
        param_layout = QtWidgets.QHBoxLayout()

        # Left column
        left_column = QtWidgets.QVBoxLayout()

        # Duration
        duration_layout = QtWidgets.QHBoxLayout()
        duration_layout.addWidget(QtWidgets.QLabel("Duration:"))
        self.duration_input = QtWidgets.QSpinBox()
        self.duration_input.setRange(1, 10000)
        duration_layout.addWidget(self.duration_input)
        left_column.addLayout(duration_layout)

        # Base Stations
        bs_layout = QtWidgets.QHBoxLayout()
        bs_layout.addWidget(QtWidgets.QLabel("Base Stations:"))
        self.num_bs_input = QtWidgets.QSpinBox()
        self.num_bs_input.setRange(1, 10)
        self.num_bs_input.valueChanged.connect(self.update_base_stations)
        bs_layout.addWidget(self.num_bs_input)
        left_column.addLayout(bs_layout)

        param_layout.addLayout(left_column)

        # Right column
        right_column = QtWidgets.QVBoxLayout()

        # HAPS
        haps_layout = QtWidgets.QHBoxLayout()
        haps_layout.addWidget(QtWidgets.QLabel("HAPS:"))
        self.num_haps_input = QtWidgets.QSpinBox()
        self.num_haps_input.setRange(1, 5)
        self.num_haps_input.valueChanged.connect(self.update_haps)
        haps_layout.addWidget(self.num_haps_input)
        right_column.addLayout(haps_layout)

        # Users
        users_layout = QtWidgets.QHBoxLayout()
        users_layout.addWidget(QtWidgets.QLabel("Users:"))
        self.num_users_input = QtWidgets.QSpinBox()
        self.num_users_input.setRange(0, 20)
        self.num_users_input.valueChanged.connect(self.update_users)
        users_layout.addWidget(self.num_users_input)
        right_column.addLayout(users_layout)

        param_layout.addLayout(right_column)

        # Add toggle for communication links at the bottom
        self.show_links_checkbox = QtWidgets.QCheckBox("Show Communication Links")
        self.show_links_checkbox.stateChanged.connect(self.toggle_links)
        param_layout.addWidget(self.show_links_checkbox)

        param_box.setLayout(param_layout)
        return param_box

    def create_real_time_view(self):
        layout = QtWidgets.QVBoxLayout()

        # Schematic View with QGraphicsView
        self.schematic_view = QtWidgets.QGraphicsView()
        layout.addWidget(self.schematic_view)

        # Toggle button to switch between views
        self.view_toggle_btn = QtWidgets.QPushButton("Switch to Far View")
        self.view_toggle_btn.clicked.connect(self.toggle_view)
        layout.addWidget(self.view_toggle_btn)

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
        scene = QtWidgets.QGraphicsScene(-200, 0, 400, 400)
        if self.simulation:
            # Add green floor
            floor = scene.addRect(
                -200,
                290,
                400,
                20,
                QtGui.QPen(QtGui.QColor("darkgreen")),
                QtGui.QBrush(QtGui.QColor("darkgreen")),
            )

            # Add HAPS
            haps_pixmap = QtGui.QPixmap("images/haps.png").scaled(30, 30)
            haps_positions = {}

            for node in self.simulation.network.nodes:
                if isinstance(node, HAPS):
                    x_pos = node.position.x * 50
                    y_pos = 100
                    haps_item = QtWidgets.QGraphicsPixmapItem(haps_pixmap)
                    haps_item.setPos(x_pos, y_pos)
                    scene.addItem(haps_item)

                    haps_positions[node] = (
                        x_pos + haps_pixmap.width() / 2,
                        y_pos + haps_pixmap.height() / 2,
                    )

                    text = scene.addText(f"HAPS {node.node_id}")
                    text.setDefaultTextColor(QtGui.QColor("white"))
                    text.setPos(
                        x_pos
                        + haps_pixmap.width() / 2
                        - text.boundingRect().width() / 2,
                        y_pos - 20,
                    )

            # Add Base Stations
            bs_pixmap = QtGui.QPixmap("images/base_station.png").scaled(30, 30)
            bs_positions = {}

            for node in self.simulation.network.nodes:
                if isinstance(node, BaseStation):
                    x_pos = node.position.x * 50
                    y_pos = 250  # Just above the floor
                    bs_item = QtWidgets.QGraphicsPixmapItem(bs_pixmap)
                    bs_item.setPos(x_pos, y_pos)
                    scene.addItem(bs_item)

                    bs_positions[node] = (
                        x_pos + bs_pixmap.width() / 2,
                        y_pos + bs_pixmap.height() / 2,
                    )

                    text = scene.addText(f"BS {node.node_id}")
                    text.setDefaultTextColor(QtGui.QColor("white"))
                    text.setPos(
                        x_pos + bs_pixmap.width() / 2 - text.boundingRect().width() / 2,
                        y_pos + bs_pixmap.height() + 5,
                    )

            # Add Users
            user_pixmap = QtGui.QPixmap("images/person.png").scaled(20, 20)
            user_positions = {}

            for node in self.simulation.network.nodes:
                if isinstance(node, UserDevice):
                    x_pos = node.position.x * 50
                    y_pos = 270
                    user_item = QtWidgets.QGraphicsPixmapItem(user_pixmap)
                    user_item.setPos(x_pos, y_pos)
                    scene.addItem(user_item)
                    user_positions[node] = (
                        x_pos + user_pixmap.width() / 2,
                        y_pos + user_pixmap.height() / 2,
                    )

            # Draw communication links if enabled
            if self.show_links:
                for link in self.simulation.network.communication_links:
                    source = link.node_a
                    target = link.node_b

                    # Get positions based on node types
                    source_pos = None
                    target_pos = None

                    if isinstance(source, UserDevice):
                        source_pos = user_positions.get(source)
                    elif isinstance(source, HAPS):
                        source_pos = haps_positions.get(source)
                    elif isinstance(source, BaseStation):
                        source_pos = bs_positions.get(source)

                    if isinstance(target, UserDevice):
                        target_pos = user_positions.get(target)
                    elif isinstance(target, HAPS):
                        target_pos = haps_positions.get(target)
                    elif isinstance(target, BaseStation):
                        target_pos = bs_positions.get(target)

                    if source_pos and target_pos:
                        # Use different colors based on connection type
                        if isinstance(source, BaseStation) or isinstance(
                            target, BaseStation
                        ):
                            color = "yellow"  # BS connections
                        else:
                            color = "white"  # Other connections

                        pen = QtGui.QPen(QtGui.QColor(color))
                        pen.setStyle(QtCore.Qt.SolidLine)
                        pen.setWidth(1)

                        line = scene.addLine(
                            source_pos[0],
                            source_pos[1],
                            target_pos[0],
                            target_pos[1],
                            pen,
                        )
                        line.setOpacity(0.5)

        self.schematic_view.setScene(scene)
        self.schematic_view.centerOn(0, 200)

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

    def start_simulation(self):
        if self.simulation:
            print("Starting simulation...")
            self.simulation.run(max_time=1000)

    def reset_simulation(self):
        if self.simulation:
            self.simulation.reset()
            print("Simulation reset.")

    def load_simulation(self):
        # Placeholder for loading a simulation
        pass

    def duplicate_simulation(self):
        # Placeholder for duplicating a simulation
        pass

    def update_simulation_selection(self):
        if self.sim_list.currentItem():
            self.load_close_up_view()
        else:
            self.schematic_view.setScene(
                QtWidgets.QGraphicsScene()
            )  # Clear view if no simulation selected

    def create_new_simulation(self):
        """Create a new simulation and add it to the list"""
        simulation_name = f"Simulation {self.sim_list.count() + 1}"
        self.sim_list.addItem(simulation_name)
        self.simulation = Simulation()  # Create new simulation instance
        self.sim_list.setCurrentRow(self.sim_list.count() - 1)
        self.load_close_up_view()  # Refresh the view

    def update_base_stations(self):
        """Update the number of base stations in the simulation and view"""
        if self.simulation:
            num_bs = self.num_bs_input.value()
            self.simulation.set_base_stations(num_bs)
            self.load_close_up_view()

    def update_haps(self):
        if self.simulation:
            num_haps = self.num_haps_input.value()
            self.simulation.set_haps(num_haps)
            self.load_close_up_view()

    def update_users(self):
        if self.simulation:
            num_users = self.num_users_input.value()
            self.simulation.set_users(num_users)
            self.load_close_up_view()

    def toggle_links(self, state):
        self.show_links = bool(state)
        self.load_close_up_view()


app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon("images/logo.png"))  # Taskbar icon
window = SimulationUI()
window.show()
sys.exit(app.exec())
