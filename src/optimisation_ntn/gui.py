import ctypes
import math
import platform
import random
import sys

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt

from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.leo import LEO
from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.simulation import Simulation
from optimisation_ntn.utils.position import Position
from optimisation_ntn.ui.dialogs.enlarged_graph import EnlargedGraphDialog

# Task bar Icon on Windows
if platform.system() == "Windows":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("optimisation_ntn")


class SimulationUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimisation NTN")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("background-color: #2e2e2e; color: white;")
        self.current_view = "close"
        self.show_links = True
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
        tabs.addTab(self.create_real_time_view(), "Animation view")
        tabs.addTab(self.create_results_tab(), "Graph selection")
        center_layout.addWidget(tabs)
        upper_content.addLayout(center_layout, 2)

        # Right panel for graphs
        right_panel = QtWidgets.QVBoxLayout()
        right_panel.addWidget(
            self.create_live_graph("Node Energy"), 1
        )  # Larger graph for selected node
        right_panel.addWidget(
            self.create_live_graph("Total Energy"), 1
        )  # Smaller graph for total
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
        self.max_time_label = QtWidgets.QLabel(
            f"{Simulation.DEFAULT_MAX_SIMULATION_TIME}s"
        )
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
        self.show_links_checkbox.setChecked(True)
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
        self.step_duration_input.setRange(0.00001, 10.0)
        self.step_duration_input.setDecimals(5)
        self.step_duration_input.setSingleStep(0.0001)
        self.step_duration_input.setValue(0.001)
        self.step_duration_input.valueChanged.connect(self.update_step_duration)
        info_layout.addWidget(self.step_duration_input, 0, 1)

        # Time per step (UI update interval)
        info_layout.addWidget(QtWidgets.QLabel("UI Update Interval (ms):"), 1, 0)
        self.time_step_input = QtWidgets.QSpinBox()
        self.time_step_input.setRange(1, 100)
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

        # Add energy consumption display to info layout
        info_layout.addWidget(QtWidgets.QLabel("Energy Consumed:"), 4, 0)
        self.current_energy_label = QtWidgets.QLabel("0.0 J")
        info_layout.addWidget(self.current_energy_label, 4, 1)

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
                -800,
                270,
                1600,
                200,
                QtGui.QPen(QtGui.QColor("darkgreen")),
                QtGui.QBrush(QtGui.QColor("darkgreen")),
            )

            sky = scene.addRect(
                -800,
                0,
                1600,
                270,
                QtGui.QPen(QtGui.QColor("skyblue")),
                QtGui.QBrush(QtGui.QColor("skyblue")),
            )

            haps_pixmap = QtGui.QPixmap("images/haps.png").scaled(30, 30)
            haps_positions = {}

            bs_pixmap = QtGui.QPixmap("images/base_station.png").scaled(30, 30)
            bs_positions = {}

            user_pixmap = QtGui.QPixmap("images/person.png").scaled(20, 20)
            user_positions = {}

            leo_pixmap = QtGui.QPixmap("images/leo.png").scaled(30, 30)
            leo_positions = {}

            for node in self.simulation.network.nodes:
                # Add HAPS
                if isinstance(node, HAPS):
                    x_pos = node.position.x * 50
                    y_pos = 100
                    haps_item = QtWidgets.QGraphicsPixmapItem(haps_pixmap)
                    haps_item.setPos(x_pos, y_pos)

                    if not node.state:
                        haps_item.setOpacity(0.2)

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
                if isinstance(node, BaseStation):
                    x_pos = node.position.x * 50
                    y_pos = 250  # Just above the floor
                    bs_item = QtWidgets.QGraphicsPixmapItem(bs_pixmap)
                    bs_item.setPos(x_pos, y_pos)

                    if not node.state:
                        bs_item.setOpacity(0.2)

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

                # Add LEO satellites
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

                    if not node.state:
                        leo_item.setOpacity(0.2)

                    scene.addItem(leo_item)

                    leo_positions[node] = (
                        x_pos + leo_pixmap.width() / 2,
                        y_pos + leo_pixmap.height() / 2,
                    )

                    # Add angle text
                    angle_text = scene.addText(
                        f"LEO {node.node_id}\nAngle: {node.current_angle:.1f}°"
                    )
                    angle_text.setDefaultTextColor(QtGui.QColor("white"))
                    angle_text.setPos(x_pos, y_pos - 40)

            # Draw communication links if enabled
            if self.show_links:
                # Draw all communication links from the network
                for link in self.simulation.network.communication_links:
                    source = link.node_a
                    target = link.node_b
                    # Get positions based on node types
                    source_pos = None
                    if isinstance(source, UserDevice):
                        source_pos = user_positions.get(source)
                    elif isinstance(source, HAPS):
                        source_pos = haps_positions.get(source)
                    elif isinstance(source, BaseStation):
                        source_pos = bs_positions.get(source)
                    elif isinstance(source, LEO):
                        source_pos = leo_positions.get(source)

                    target_pos = None
                    if isinstance(target, UserDevice):
                        target_pos = user_positions.get(target)
                    elif isinstance(target, HAPS):
                        target_pos = haps_positions.get(target)
                    elif isinstance(target, BaseStation):
                        target_pos = bs_positions.get(target)
                    elif isinstance(target, LEO):
                        target_pos = leo_positions.get(target)

                    if source_pos and target_pos:
                        # Use different colors based on connection type
                        color = "yellow"  # Default color
                        if isinstance(source, LEO) or isinstance(target, LEO):
                            color = "cyan"  # LEO connections
                        elif isinstance(source, BaseStation) or isinstance(
                            target, BaseStation
                        ):
                            color = "yellow"  # BS connections
                        elif isinstance(source, HAPS) or isinstance(target, HAPS):
                            color = "orange"  # HAPS connections
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

                        # Add requests in transit for this link
                        if link.transmission_queue:
                            self.add_in_transit_requests(
                                scene, link, source_pos, target_pos
                            )

            # Store node positions for request visualization
            node_positions = {}

            # After drawing each node, store its position and add its processing requests
            for node in self.simulation.network.nodes:
                if isinstance(node, BaseStation):
                    x_pos = node.position.x * 50
                    y_pos = 250
                    node_positions[node] = (
                        x_pos + 15,
                        y_pos + 15,
                    )  # Center of the node
                    self.add_processing_requests(scene, node, x_pos + 15, y_pos + 15)

                elif isinstance(node, HAPS):
                    x_pos = node.position.x * 50
                    y_pos = 100
                    node_positions[node] = (x_pos + 15, y_pos + 15)
                    self.add_processing_requests(scene, node, x_pos + 15, y_pos + 15)

                elif isinstance(node, UserDevice):
                    x_pos = node.position.x * 50
                    y_pos = 270
                    node_positions[node] = (x_pos + 10, y_pos + 10)
                    self.add_processing_requests(scene, node, x_pos + 10, y_pos + 10)

            # Draw communication links and requests in transit
            if self.show_links:
                for link in self.simulation.network.communication_links:
                    source_pos = node_positions.get(link.node_a)
                    target_pos = node_positions.get(link.node_b)

                    if source_pos and target_pos:
                        # Draw the link
                        pen = QtGui.QPen(
                            QtGui.QColor(
                                "yellow"
                                if isinstance(link.node_a, BaseStation)
                                or isinstance(link.node_b, BaseStation)
                                else "white"
                            )
                        )
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

                        # Add requests in transit
                        self.add_in_transit_requests(
                            scene, link, source_pos, target_pos
                        )

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

        night_sky = scene.addRect(
            -view_width / 2,
            -view_height / 2,
            view_width,
            view_height,
            QtGui.QPen(QtGui.QColor("black")),
            QtGui.QBrush(QtGui.QColor("black")),
        )

        # Radius for Earth, HAPS, and LEO layers
        earth_radius = min(view_width, view_height) * 0.3
        haps_radius = earth_radius + 3  # HAPS layer above the Earth
        leo_radius = earth_radius + 75  # LEO layer further out

        # Add Earth at center
        earth = scene.addEllipse(
            -earth_radius,
            -earth_radius,
            2 * earth_radius,
            2 * earth_radius,
            QtGui.QPen(QtGui.QColor("blue")),
            QtGui.QBrush(QtGui.QColor("green")),
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
                    QtGui.QPen(QtGui.QColor("orange")),
                    QtGui.QBrush(QtGui.QColor("orange")),
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
        """Create a live graph widget for energy monitoring"""
        chart = QChart()

        # Update title and axis labels for energy consumption history
        if title == "Node Energy":
            chart.setTitle("Node Energy Consumption History")
            axis_y = QValueAxis()
            axis_y.setTitleText("Energy per tick (J)")
            self.node_energy_series = {}  # Dictionary to store series for each node
        else:  # Total Energy
            series = QLineSeries()
            chart.addSeries(series)
            chart.setTitle(title)
            axis_y = QValueAxis()
            axis_y.setTitleText("Energy (J)")
            self.total_energy_series = series

        # Create x axis
        axis_x = QValueAxis()
        axis_x.setTitleText("Time (s)")
        axis_x.setRange(0, self.simulation.max_time if self.simulation else 300)

        # Store axis references
        if title == "Total Energy":
            self.total_energy_y_axis = axis_y
        else:  # Node Energy
            self.node_energy_y_axis = axis_y
            self.node_energy_chart = chart

        # Add axes to chart
        chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
        chart.addAxis(axis_y, QtCore.Qt.AlignLeft)

        if title == "Total Energy":
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)

        chart.setBackgroundBrush(QtGui.QColor("#2e2e2e"))
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Make the chart view clickable
        chart_view.mouseDoubleClickEvent = lambda event: self.show_enlarged_graph(
            chart_view
        )

        return chart_view

    def show_enlarged_graph(self, chart_view):
        """Show the enlarged version of the clicked graph"""
        dialog = EnlargedGraphDialog(chart_view, self)
        dialog.exec()

    def create_results_tab(self):
        layout = QtWidgets.QVBoxLayout()

        # Create table for node statistics and selection
        self.node_stats_table = QtWidgets.QTableWidget()
        self.node_stats_table.setColumnCount(7)
        self.node_stats_table.setHorizontalHeaderLabels(
            [
                "Show",
                "Node",
                "Current Energy",
                "Peak Energy",
                "Average Energy",
                "Cumulated Energy",
                "Remaining Battery",
            ]
        )
        self.node_stats_table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )

        # Make the checkbox column smaller
        self.node_stats_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents
        )

        # Initialize signal connection flag
        self.checkbox_signal_connected = False

        layout.addWidget(self.node_stats_table)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container

    def update_node_stats_table(self):
        """Update the node statistics table"""
        if not self.simulation:
            return

        # Block signals during update
        self.node_stats_table.blockSignals(True)

        # Store currently checked states and preserve current selection
        checked_nodes = set()
        current_selection = self.node_stats_table.selectedItems()
        selected_rows = set(item.row() for item in current_selection)

        for row in range(self.node_stats_table.rowCount()):
            checkbox_item = self.node_stats_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == QtCore.Qt.Checked:
                node_item = self.node_stats_table.item(row, 1)
                if node_item:
                    checked_nodes.add(node_item.text())

        # Update table contents without clearing it
        if self.node_stats_table.rowCount() != len(self.simulation.network.nodes):
            self.node_stats_table.setRowCount(len(self.simulation.network.nodes))

        for row, node in enumerate(self.simulation.network.nodes):
            node_text = f"{type(node).__name__} {node.node_id}"

            # Update checkbox if needed
            checkbox_item = self.node_stats_table.item(row, 0)
            if not checkbox_item:
                checkbox_item = QtWidgets.QTableWidgetItem()
                checkbox_item.setFlags(
                    QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
                )
                self.node_stats_table.setItem(row, 0, checkbox_item)

            checkbox_item.setCheckState(
                QtCore.Qt.Checked if node_text in checked_nodes else QtCore.Qt.Unchecked
            )

            # Update node name if needed
            name_item = self.node_stats_table.item(row, 1)
            if not name_item or name_item.text() != node_text:
                self.node_stats_table.setItem(
                    row, 1, QtWidgets.QTableWidgetItem(node_text)
                )

            # Update statistics
            if len(node.energy_history) > 0:
                current = node.energy_history[-1]
                peak = max(node.energy_history)
                avg = sum(node.energy_history) / len(node.energy_history)
                cumulated = node.energy_consumed

                # Calculate remaining battery
                if node.battery_capacity > 0:
                    remaining = node.battery_capacity - node.energy_consumed
                    remaining_str = f"{remaining:.2f}"
                else:
                    remaining_str = "∞"

                # Update values
                self.update_table_cell(row, 2, f"{current:.2f}")
                self.update_table_cell(row, 3, f"{peak:.2f}")
                self.update_table_cell(row, 4, f"{avg:.2f}")
                self.update_table_cell(row, 5, f"{cumulated:.2f}")
                self.update_table_cell(row, 6, remaining_str)
            else:
                # Fill with zeros if no history yet
                for col in range(2, 6):
                    self.update_table_cell(row, col, "0.00")
                # Set remaining battery
                if node.battery_capacity > 0:
                    self.update_table_cell(row, 6, f"{node.battery_capacity:.2f}")
                else:
                    self.update_table_cell(row, 6, "∞")

        # Restore selection
        for row in selected_rows:
            self.node_stats_table.selectRow(row)

        # Unblock signals and ensure connection
        self.node_stats_table.blockSignals(False)

        # Connect signal if not already connected
        if not self.checkbox_signal_connected:
            self.node_stats_table.itemChanged.connect(self.handle_checkbox_change)
            self.checkbox_signal_connected = True

    def update_table_cell(self, row, col, value):
        """Helper method to update table cell only if value changed"""
        current_item = self.node_stats_table.item(row, col)
        if not current_item or current_item.text() != value:
            self.node_stats_table.setItem(row, col, QtWidgets.QTableWidgetItem(value))

    def handle_checkbox_change(self, item):
        """Handle checkbox state changes in the stats table"""
        if not item or item.column() != 0:  # Only handle checkbox column
            return

        # Process the change without blocking signals
        row = item.row()
        node_item = self.node_stats_table.item(row, 1)
        if node_item:
            node_text = node_item.text()
            if item.checkState() == QtCore.Qt.Checked:
                # Add series if not exists
                if node_text not in self.node_energy_series:
                    series = QLineSeries()
                    series.setName(node_text)
                    self.node_energy_chart.addSeries(series)
                    series.attachAxis(self.node_energy_chart.axes()[0])
                    series.attachAxis(self.node_energy_chart.axes()[1])
                    self.node_energy_series[node_text] = series

                    # Assign a color to the series
                    color = QtGui.QColor(
                        random.randint(50, 255),
                        random.randint(50, 255),
                        random.randint(50, 255),
                    )
                    series.setColor(color)

                    # Update series data
                    for node in self.simulation.network.nodes:
                        if f"{type(node).__name__} {node.node_id}" == node_text:
                            series.clear()
                            for i, energy in enumerate(node.energy_history):
                                time_point = i * self.simulation.time_step
                                series.append(time_point, energy)
                            break
            else:
                # Remove series if exists
                if node_text in self.node_energy_series:
                    series = self.node_energy_series[node_text]
                    self.node_energy_chart.removeSeries(series)
                    del self.node_energy_series[node_text]

            # Update y-axis range
            max_energy = 0
            for series in self.node_energy_series.values():
                for i in range(series.count()):
                    max_energy = max(max_energy, series.at(i).y())
            if max_energy > 0:
                self.node_energy_y_axis.setRange(0, max_energy * 1.2)

            # Show/hide legend based on number of series
            self.node_energy_chart.legend().setVisible(len(self.node_energy_series) > 1)

    def start_simulation(self):
        if self.simulation:
            self.simulation.is_paused = False
            update_interval = self.time_step_input.value()

            # Disable step duration input while simulation is running
            self.step_duration_input.setEnabled(False)

            # Create timer for UI updates
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.simulation_step)
            self.timer.start(update_interval)  # Start timer with specified interval
            self.run_pause_btn.setText("Pause")

    def simulation_step(self):
        """Handle one simulation step with UI update"""
        if self.simulation and not self.simulation.is_paused:
            can_continue = self.simulation.step()

            # Update UI
            if can_continue:
                self.update_simulation_display()
                current_time = self.simulation.current_time

                # Update total energy graph
                total_energy = self.simulation.system_energy_consumed
                self.total_energy_series.append(current_time, total_energy)
                self.total_energy_y_axis.setRange(0, max(total_energy * 1.2, 200))

                # Update node statistics and graphs
                self.update_node_stats_table()
                self.update_checked_nodes_graphs(current_time)

                # Update view based on current view mode
                if self.current_view == "close":
                    self.load_close_up_view()
                else:
                    self.load_far_view()

                self.schematic_view.viewport().update()
            else:
                self.timer.stop()
                self.run_pause_btn.setText("Run")

    def update_checked_nodes_graphs(self, current_time):
        """Update graphs for checked nodes"""
        for row in range(self.node_stats_table.rowCount()):
            checkbox_item = self.node_stats_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == QtCore.Qt.Checked:
                node_item = self.node_stats_table.item(row, 1)
                if node_item:
                    node_text = node_item.text()
                    if node_text in self.node_energy_series:
                        # Find corresponding node and update its series
                        for node in self.simulation.network.nodes:
                            if f"{type(node).__name__} {node.node_id}" == node_text:
                                series = self.node_energy_series[node_text]
                                if node.energy_history.size > 0:
                                    series.append(current_time, node.energy_history[-1])
                                break

    def update_simulation_display(self):
        """Update UI elements showing simulation state"""
        if self.simulation:
            # Update time labels
            self.current_time_label.setText(f"{self.simulation.current_time:.1f}s")
            self.current_step_label.setText(str(self.simulation.current_step))

            # Add energy consumption display
            if hasattr(self, "current_energy_label"):
                self.current_energy_label.setText(
                    f"{self.simulation.system_energy_consumed:.2f} J"
                )

    def reset_simulation(self):
        if self.simulation:
            # Stop timer if running
            if hasattr(self, "timer") and self.timer.isActive():
                self.timer.stop()
                self.run_pause_btn.setText("Run")

            # Re-enable step duration input
            self.step_duration_input.setEnabled(True)

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
        """Update the selected simulation"""
        try:
            if self.sim_list.currentItem():
                simulation_name = self.sim_list.currentItem().text()
                if simulation_name in self.simulations:
                    self.simulation = self.simulations[simulation_name]
                    self.update_ui_parameters()
                    self.load_close_up_view()
                else:
                    print(f"Warning: Simulation '{simulation_name}' not found")
        except Exception as e:
            print(f"Error updating simulation selection: {str(e)}")

    def create_new_simulation(self):
        """Create a new simulation and add it to the list"""
        try:
            simulation_name = f"Simulation {self.sim_list.count() + 1}"
            simulation = Simulation(debug=False)
            self.simulations[simulation_name] = simulation
            self.simulation = simulation

            # Add to list and select it
            self.sim_list.addItem(simulation_name)
            self.sim_list.setCurrentRow(self.sim_list.count() - 1)

            # Update UI parameters
            self.update_ui_parameters()

            # Initialize node statistics table
            self.update_node_stats_table()

            # Update views
            self.load_close_up_view()

            # Enable step duration input
            self.step_duration_input.setEnabled(True)

            # Reset energy graphs
            if hasattr(self, "total_energy_series"):
                self.total_energy_series.clear()
            if hasattr(self, "node_energy_series"):
                for series in self.node_energy_series.values():
                    self.node_energy_chart.removeSeries(series)
                self.node_energy_series.clear()

            # Reset time labels
            self.current_time_label.setText("0.0s")
            self.current_step_label.setText("0")
            self.current_energy_label.setText("0.0 J")

        except Exception as e:
            print(f"Error creating simulation: {str(e)}")

    def update_ui_parameters(self):
        """Update UI controls to match current simulation"""
        if self.simulation:
            # Update spinboxes without triggering their signals
            self.num_bs_input.blockSignals(True)
            self.num_haps_input.blockSignals(True)
            self.num_users_input.blockSignals(True)
            self.step_duration_input.blockSignals(True)

            # Count nodes of each type using new method
            bs_count = self.simulation.network.count_nodes_by_type(BaseStation)
            haps_count = self.simulation.network.count_nodes_by_type(HAPS)
            users_count = self.simulation.network.count_nodes_by_type(UserDevice)

            # Update UI values
            self.num_bs_input.setValue(bs_count)
            self.num_haps_input.setValue(haps_count)
            self.num_users_input.setValue(users_count)
            self.step_duration_input.setValue(self.simulation.time_step)

            # Re-enable signals
            self.num_bs_input.blockSignals(False)
            self.num_haps_input.blockSignals(False)
            self.num_users_input.blockSignals(False)
            self.step_duration_input.blockSignals(False)

    def update_base_stations(self):
        """Update the number of base stations in the simulation and view"""
        if self.simulation:
            num_bs = self.num_bs_input.value()
            self.simulation.set_nodes(BaseStation, num_bs)
            self.load_close_up_view()

    def update_haps(self):
        if self.simulation:
            num_haps = self.num_haps_input.value()
            self.simulation.set_nodes(HAPS, num_haps)
            self.load_close_up_view()

    def update_users(self):
        if self.simulation:
            num_users = self.num_users_input.value()
            self.simulation.set_nodes(UserDevice, num_users)
            self.load_close_up_view()

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
        """Update simulation time step when UI value changes"""
        if self.simulation:
            self.simulation.time_step = self.step_duration_input.value()

    def add_processing_requests(self, scene, node, node_x, node_y):
        """Add visual representation of requests being processed by a node"""
        if hasattr(node, "processing_queue") and node.processing_queue:
            request_pixmap = QtGui.QPixmap("images/file.png")
            if request_pixmap.isNull():
                print("ERROR: Could not load file.png for processing requests")
                return

            request_pixmap = request_pixmap.scaled(15, 15)

            # Position requests in a semi-circle above the node
            num_requests = len(node.processing_queue)
            radius = 25  # Radius of the circle
            start_angle = -140  # Start angle in degrees
            angle_span = 100  # Total angle span in degrees

            for i, request in enumerate(node.processing_queue):
                # Calculate angle for this request
                angle = math.radians(
                    start_angle
                    + (angle_span * i / (num_requests - 1 if num_requests > 1 else 1))
                )

                # Calculate position
                x = node_x + radius * math.cos(angle)
                y = node_y + radius * math.sin(angle)

                # Add request icon
                request_item = QtWidgets.QGraphicsPixmapItem(request_pixmap)
                request_item.setPos(
                    x - request_pixmap.width() / 2, y - request_pixmap.height() / 2
                )
                scene.addItem(request_item)

                # Add request ID label
                text = scene.addText(f"R{request.id}")
                text.setDefaultTextColor(QtGui.QColor("white"))
                text.setPos(
                    x - text.boundingRect().width() / 2,
                    y - request_pixmap.height() - 15,
                )

    def add_in_transit_requests(self, scene, link, source_pos, target_pos):
        """Add visual representation of requests in transit on a link"""
        if link.transmission_queue:
            request_pixmap = QtGui.QPixmap("images/file.png")
            if request_pixmap.isNull():
                print("ERROR: Could not load file.png for in-transit requests")
                return

            request_pixmap = request_pixmap.scaled(15, 15)

            for i, request in enumerate(link.transmission_queue):
                # Calculate position along the link
                if i == 0:  # First request - show actual progress
                    progress = min(1.0, max(0.0, link.request_progress / request.size))
                else:  # Queue other requests behind the first one
                    progress = max(0.0, (i * -0.1))  # Space them out behind the source

                # Calculate position along the line
                x = source_pos[0] + (target_pos[0] - source_pos[0]) * progress
                y = source_pos[1] + (target_pos[1] - source_pos[1]) * progress

                # Add request icon
                request_item = QtWidgets.QGraphicsPixmapItem(request_pixmap)
                request_item.setPos(
                    x - request_pixmap.width() / 2, y - request_pixmap.height() / 2
                )
                scene.addItem(request_item)

                # Add request ID label
                text = scene.addText(f"R{request.id}")
                text.setDefaultTextColor(QtGui.QColor("white"))
                text.setPos(
                    x - text.boundingRect().width() / 2,
                    y - request_pixmap.height() - 15,
                )

    def update_energy_table(self):
        """Update the energy consumption table in the results tab"""
        if self.simulation:
            self.energy_table.setRowCount(0)  # Clear existing rows

            # Add a row for each node
            for node in self.simulation.network.nodes:
                row = self.energy_table.rowCount()
                self.energy_table.insertRow(row)

                # Node identifier
                self.energy_table.setItem(
                    row,
                    0,
                    QtWidgets.QTableWidgetItem(f"{type(node).__name__} {node.node_id}"),
                )

                # Node type
                self.energy_table.setItem(
                    row, 1, QtWidgets.QTableWidgetItem(type(node).__name__)
                )

                # Energy consumed
                self.energy_table.setItem(
                    row, 2, QtWidgets.QTableWidgetItem(f"{node.energy_consumed:.2f}")
                )


app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon("images/logo.png"))  # Taskbar icon
window = SimulationUI()
window.show()
sys.exit(app.exec())
