import ctypes
import math
import random
import sys

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCharts import QChart, QChartView, QLineSeries

from .nodes.base_station import BaseStation
from .nodes.haps import HAPS
from .nodes.leo import LEO
from .nodes.user_device import UserDevice
from .simulation import Simulation
from .utils.type import Position

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
        self.simulations = {}
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

        # Add list widget with context menu
        self.sim_list = QtWidgets.QListWidget()
        self.sim_list.itemSelectionChanged.connect(self.update_simulation_selection)
        self.sim_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.sim_list.customContextMenuRequested.connect(self.show_sim_context_menu)
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

        # Create button layout
        button_layout = QtWidgets.QHBoxLayout()

        # Run/Pause button
        self.run_pause_btn = QtWidgets.QPushButton("Run")
        self.run_pause_btn.clicked.connect(self.toggle_simulation)
        button_layout.addWidget(self.run_pause_btn)

        # Reset button
        reset_btn = QtWidgets.QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_simulation)
        button_layout.addWidget(reset_btn)

        # Save button
        save_btn = QtWidgets.QPushButton("Save")
        button_layout.addWidget(save_btn)

        control_layout.addLayout(button_layout)

        # Add max simulation time display
        max_time_layout = QtWidgets.QHBoxLayout()
        max_time_layout.addWidget(QtWidgets.QLabel("Max Time:"))
        self.max_time_label = QtWidgets.QLabel(f"{Simulation.MAX_SIMULATION_TIME}s")
        max_time_layout.addWidget(self.max_time_label)
        control_layout.addLayout(max_time_layout)

        control_box.setLayout(control_layout)
        return control_box

    def toggle_simulation(self):
        """Toggle between running and paused states"""
        if self.simulation:
            if hasattr(self, "timer") and self.timer.isActive():
                # Pause simulation
                self.timer.stop()
                self.simulation.is_paused = True
                self.run_pause_btn.setText("Resume")
            else:
                # Start/Resume simulation
                self.start_simulation()
                self.run_pause_btn.setText("Pause")

    def create_simulation_parameters(self):
        # Create horizontal layout for parameters and info
        horizontal_layout = QtWidgets.QHBoxLayout()

        # Create Parameters Panel (left side)
        param_box = QtWidgets.QGroupBox("Simulation Parameters")
        param_layout = QtWidgets.QHBoxLayout()

        # Node controls
        node_controls = QtWidgets.QGridLayout()

        # Base Stations
        node_controls.addWidget(QtWidgets.QLabel("Base Stations:"), 0, 0)
        self.num_bs_input = QtWidgets.QSpinBox()
        self.num_bs_input.setRange(1, 10)
        self.num_bs_input.valueChanged.connect(self.update_base_stations)
        node_controls.addWidget(self.num_bs_input, 0, 1)

        # HAPS
        node_controls.addWidget(QtWidgets.QLabel("HAPS:"), 1, 0)
        self.num_haps_input = QtWidgets.QSpinBox()
        self.num_haps_input.setRange(1, 5)
        self.num_haps_input.valueChanged.connect(self.update_haps)
        node_controls.addWidget(self.num_haps_input, 1, 1)

        # Users
        node_controls.addWidget(QtWidgets.QLabel("Users:"), 2, 0)
        self.num_users_input = QtWidgets.QSpinBox()
        self.num_users_input.setRange(0, 20)
        self.num_users_input.valueChanged.connect(self.update_users)
        node_controls.addWidget(self.num_users_input, 2, 1)

        param_layout.addLayout(node_controls)

        # Add toggle for communication links
        self.show_links_checkbox = QtWidgets.QCheckBox("Show Communication Links")
        self.show_links_checkbox.stateChanged.connect(self.toggle_links)
        param_layout.addWidget(self.show_links_checkbox)

        param_box.setLayout(param_layout)
        horizontal_layout.addWidget(param_box)

        # Create Info Panel (right side)
        info_box = QtWidgets.QGroupBox("Simulation Info")
        info_layout = QtWidgets.QGridLayout()

        # Step Duration
        info_layout.addWidget(QtWidgets.QLabel("Step Duration (s):"), 0, 0)
        self.step_duration_input = QtWidgets.QDoubleSpinBox()
        self.step_duration_input.setRange(0.001, 10.0)
        self.step_duration_input.setValue(0.1)
        self.step_duration_input.setSingleStep(0.1)
        self.step_duration_input.valueChanged.connect(self.update_step_duration)
        info_layout.addWidget(self.step_duration_input, 0, 1)

        # Time per step (UI update interval)
        info_layout.addWidget(QtWidgets.QLabel("UI Update Interval (ms):"), 1, 0)
        self.time_step_input = QtWidgets.QSpinBox()
        self.time_step_input.setRange(0, 1000)
        self.time_step_input.setValue(100)
        self.time_step_input.valueChanged.connect(self.update_time_step)
        info_layout.addWidget(self.time_step_input, 1, 1)

        # Current simulation info
        info_layout.addWidget(QtWidgets.QLabel("Current Time:"), 2, 0)
        self.current_time_label = QtWidgets.QLabel("0.0s")
        info_layout.addWidget(self.current_time_label, 2, 1)

        info_layout.addWidget(QtWidgets.QLabel("Current Step:"), 3, 0)
        self.current_step_label = QtWidgets.QLabel("0")
        info_layout.addWidget(self.current_step_label, 3, 1)

        info_box.setLayout(info_layout)
        horizontal_layout.addWidget(info_box)

        # Create container widget
        container = QtWidgets.QWidget()
        container.setLayout(horizontal_layout)
        return container

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
            self.current_view = "far"
            self.view_toggle_btn.setText("Switch to Close-Up View")
        else:
            self.current_view = "close"
            self.view_toggle_btn.setText("Switch to Far View")
        self.update_view()

    def update_view(self):
        """Update the current view"""
        if self.current_view == "close":
            self.load_close_up_view()
        else:
            self.load_far_view()

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

            # Add LEO satellites
            leo_pixmap = QtGui.QPixmap("images/leo.png").scaled(30, 30)
            leo_positions = {}

            for node in self.simulation.network.nodes:
                if isinstance(node, LEO) and node.is_visible:
                    # Calculate position based on visible angle range
                    view_width = 400  # Width of the view

                    # Map angle from [-13.6, 13.6] to screen coordinates
                    angle_range = np.abs(LEO.initial_angle - LEO.final_angle)
                    x_pos = (
                        (node.current_angle - LEO.initial_angle) / angle_range
                    ) * view_width - view_width / 2
                    y_pos = 50  # Keep constant height for horizontal movement

                    leo_item = QtWidgets.QGraphicsPixmapItem(leo_pixmap)
                    leo_item.setPos(x_pos, y_pos)
                    scene.addItem(leo_item)

                    # Add angle text
                    angle_text = scene.addText(
                        f"LEO {node.node_id}\nAngle: {node.current_angle:.1f}°"
                    )
                    angle_text.setDefaultTextColor(QtGui.QColor("white"))
                    angle_text.setPos(x_pos, y_pos - 40)

        self.schematic_view.setScene(scene)
        self.schematic_view.centerOn(0, 200)

    def load_far_view(self):
        # Determine dimensions based on the view
        view_width = self.schematic_view.width()
        view_height = self.schematic_view.height()

        # Set the scene to fit the view and center on (0, 0)
        scene = QtWidgets.QGraphicsScene(
            -view_width / 2, -view_height / 2, view_width, view_height
        )

        # Radius for Earth, HAPS, and LEO layers
        earth_radius = min(view_width, view_height) * 0.3
        haps_radius = earth_radius + 40  # HAPS layer above the Earth
        leo_radius = earth_radius + 80  # LEO layer further out

        # Add Earth at center
        earth = scene.addEllipse(
            -earth_radius,
            -earth_radius,
            2 * earth_radius,
            2 * earth_radius,
            QtGui.QPen(QtGui.QColor("blue")),
            QtGui.QBrush(QtGui.QColor(0, 0, 139, 100)),
        )

        # Add HAPS layer as a circular orbit on top
        haps_circle = scene.addEllipse(
            -haps_radius,
            -haps_radius,
            2 * haps_radius,
            2 * haps_radius,
            QtGui.QPen(QtGui.QColor("gray"), 1, QtCore.Qt.DashLine),
        )

        # Add LEO layer as a circular orbit on top
        leo_circle = scene.addEllipse(
            -leo_radius,
            -leo_radius,
            2 * leo_radius,
            2 * leo_radius,
            QtGui.QPen(QtGui.QColor("gray"), 1, QtCore.Qt.DashLine),
        )

        # Add nodes to the scene
        for node in self.simulation.network.nodes:
            if isinstance(node, LEO):
                # Position LEO satellites based on current angle with 0 degrees at the top
                angle_rad = math.radians(node.current_angle)
                x = leo_radius * math.cos(angle_rad)
                y = -leo_radius * math.sin(angle_rad)  # Negative to move upward

                # Add LEO satellite icon
                leo_item = scene.addRect(
                    x - 5,
                    y - 5,
                    10,
                    10,
                    QtGui.QPen(QtGui.QColor("yellow")),
                    QtGui.QBrush(QtGui.QColor("yellow")),
                )

                # Add label
                text = scene.addText(f"LEO {node.node_id}")
                text.setDefaultTextColor(QtGui.QColor("white"))
                text.setPos(x + 10, y)

            elif isinstance(node, HAPS):
                # Position HAPS nodes directly on top of the Earth (0-degree position)
                x = haps_radius * math.cos(math.radians(0))  # Fixed at 0 degrees
                y = -haps_radius * math.sin(math.radians(0))

                # Add HAPS icon
                haps_item = scene.addRect(
                    x - 5,
                    y - 5,
                    10,
                    10,
                    QtGui.QPen(QtGui.QColor("green")),
                    QtGui.QBrush(QtGui.QColor("green")),
                )

                # Add label
                text = scene.addText(f"HAPS {node.node_id}")
                text.setDefaultTextColor(QtGui.QColor("white"))
                text.setPos(x + 10, y)

        # Set the scene and fit it to the view
        self.schematic_view.setScene(scene)
        self.schematic_view.fitInView(scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        self.schematic_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.schematic_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

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
            self.simulation.is_paused = False
            update_interval = (
                self.time_step_input.value()
            )  # Get UI update interval in ms

            # Update simulation step duration
            self.simulation.step_duration = self.step_duration_input.value()

            # Create timer for UI updates
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.simulation_step)
            self.timer.start(update_interval)  # Start timer with specified interval
            self.run_pause_btn.setText("Pause")

    def simulation_step(self):
        """Handle one simulation step with UI update"""
        if self.simulation and not self.simulation.is_paused:
            if self.simulation.step():  # Returns True if simulation should continue
                # Update simulation display (e.g., satellite positions)
                self.update_simulation_display()
                # Reload the current view to update LEO positions
                self.update_view()
            else:
                self.timer.stop()
                self.run_pause_btn.setText("Run")

    def update_simulation_display(self):
        """Update UI elements showing simulation state"""
        if self.simulation:
            # Update time labels
            self.current_time_label.setText(f"{self.simulation.current_time:.1f}s")
            self.current_step_label.setText(str(self.simulation.current_step))

    def reset_simulation(self):
        if self.simulation:
            # Stop timer if running
            if hasattr(self, "timer") and self.timer.isActive():
                self.timer.stop()
                self.run_pause_btn.setText("Run")

            self.simulation.reset()
            self.update_ui_parameters()
            self.update_view()
            self.current_time_label.setText("0.0s")
            print("Simulation reset.")

    def load_simulation(self):
        # Placeholder for loading a simulation
        pass

    def duplicate_simulation(self):
        # Placeholder for duplicating a simulation
        pass

    def update_simulation_selection(self):
        if self.sim_list.currentItem():
            simulation_name = self.sim_list.currentItem().text()
            self.simulation = self.simulations[simulation_name]
            self.update_ui_parameters()
            self.load_close_up_view()
        else:
            self.simulation = None
            self.schematic_view.setScene(QtWidgets.QGraphicsScene())

    def create_new_simulation(self):
        """Create a new simulation and add it to the list"""
        simulation_name = f"Simulation {self.sim_list.count() + 1}"
        self.sim_list.addItem(simulation_name)

        # Create new simulation instance
        simulation = Simulation()

        # Store simulation
        self.simulations[simulation_name] = simulation
        self.simulation = simulation

        self.sim_list.setCurrentRow(self.sim_list.count() - 1)
        self.load_close_up_view()

        # Update UI with simulation parameters
        self.update_ui_parameters()

    def update_ui_parameters(self):
        """Update UI controls to match current simulation"""
        if self.simulation:
            # Update spinboxes without triggering their signals
            self.num_bs_input.blockSignals(True)
            self.num_haps_input.blockSignals(True)
            self.num_users_input.blockSignals(True)

            # Count nodes of each type
            bs_count = len(
                [n for n in self.simulation.network.nodes if isinstance(n, BaseStation)]
            )
            haps_count = len(
                [n for n in self.simulation.network.nodes if isinstance(n, HAPS)]
            )
            users_count = len(
                [n for n in self.simulation.network.nodes if isinstance(n, UserDevice)]
            )

            # Update UI values
            self.num_bs_input.setValue(bs_count)
            self.num_haps_input.setValue(haps_count)
            self.num_users_input.setValue(users_count)

            # Re-enable signals
            self.num_bs_input.blockSignals(False)
            self.num_haps_input.blockSignals(False)
            self.num_users_input.blockSignals(False)

    def update_base_stations(self):
        """Update the number of base stations in the simulation and view"""
        if self.simulation:
            num_bs = self.num_bs_input.value()
            self.set_base_stations(num_bs)
            self.load_close_up_view()

    def set_base_stations(self, num_base_stations: int):
        """Remove all existing base stations and create new ones."""
        network = self.simulation.network
        # Remove all existing base stations
        network.nodes = [
            node for node in network.nodes if not isinstance(node, BaseStation)
        ]

        # Add new base stations
        start_x = -(num_base_stations - 1) * 1.5 / 2
        for i in range(num_base_stations):
            x_pos = start_x + (i * 1.5)
            base_station = BaseStation(i, Position(x_pos, 0))
            network.add_node(base_station)

    def update_haps(self):
        if self.simulation:
            num_haps = self.num_haps_input.value()
            self.set_haps(num_haps)
            self.load_close_up_view()

    def set_haps(self, num_haps: int):
        network = self.simulation.network
        # Remove all existing HAPS
        network.nodes = [node for node in network.nodes if not isinstance(node, HAPS)]

        # Add new HAPS
        start_x = -(num_haps - 1) * 2 / 2
        height = 20  # Height for HAPS layer
        for i in range(num_haps):
            x_pos = start_x + (i * 2)
            haps = HAPS(i, Position(x_pos, height))
            network.add_node(haps)

    def update_users(self):
        if self.simulation:
            num_users = self.num_users_input.value()
            self.set_users(num_users)
            self.load_close_up_view()

    def set_users(self, num_users: int):
        network = self.simulation.network
        # Remove all existing users
        network.nodes = [
            node for node in network.nodes if not isinstance(node, UserDevice)
        ]

        # Add new users with random positions
        for i in range(num_users):
            x_pos = random.uniform(-4, 4)
            height = -2  # Height for users (below base stations)
            user = UserDevice(i, Position(x_pos, height))
            network.add_node(user)

    def toggle_links(self, state):
        self.show_links = bool(state)
        self.load_close_up_view()

    def update_time_step(self):
        """Update UI update interval"""
        if hasattr(self, "timer") and self.timer.isActive():
            update_interval = self.time_step_input.value()
            self.timer.setInterval(update_interval)

    def show_sim_context_menu(self, position):
        """Show context menu for simulation list items"""
        menu = QtWidgets.QMenu()

        # Only show menu if an item is selected
        if self.sim_list.currentItem():
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(self.rename_simulation)

            # Show menu at cursor position
            menu.exec_(self.sim_list.mapToGlobal(position))

    def rename_simulation(self):
        """Rename the selected simulation"""
        current_item = self.sim_list.currentItem()
        if current_item:
            old_name = current_item.text()

            # Show dialog for new name
            new_name, ok = QtWidgets.QInputDialog.getText(
                self,
                "Rename Simulation",
                "Enter new name:",
                QtWidgets.QLineEdit.Normal,
                old_name,
            )

            if ok and new_name:
                # Update simulation name in dictionary
                self.simulations[new_name] = self.simulations.pop(old_name)
                current_item.setText(new_name)

    def update_step_duration(self):
        """Update simulation step duration"""
        if self.simulation:
            self.simulation.step_duration = self.step_duration_input.value()


app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon("images/logo.png"))  # Taskbar icon
window = SimulationUI()
window.show()
sys.exit(app.exec())
