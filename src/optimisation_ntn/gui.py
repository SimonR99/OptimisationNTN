""" Main GUI class """

import ctypes
import platform
import sys

from PySide6 import QtCore, QtGui, QtWidgets

from optimisation_ntn.networks.request import RequestStatus
from optimisation_ntn.ui.dialogs.enlarged_graph import EnlargedGraphDialog
from optimisation_ntn.ui.graphs import EnergyGraph
from optimisation_ntn.ui.simulation_controls import SimulationControls
from optimisation_ntn.ui.stats_table import NodeStatsTable
from optimisation_ntn.ui.theme_manager import ThemeManager
from optimisation_ntn.ui.views import CloseUpView, FarView

# Task bar Icon on Windows
if platform.system() == "Windows":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("optimisation_ntn")


# pylint: disable=too-many-instance-attributes
class SimulationUI(QtWidgets.QMainWindow):
    """Main GUI class"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimisation NTN")
        self.setGeometry(100, 100, 1400, 800)
        self.current_view = "close"
        self.show_links = True
        self.is_dark_theme = True
        self.setWindowIcon(QtGui.QIcon("images/logo.png"))

        self.schematic_view = QtWidgets.QGraphicsView()
        self.view_toggle_btn = QtWidgets.QPushButton("Switch to Far View")
        self.node_stats_table = NodeStatsTable()
        self.show_links_checkbox = QtWidgets.QCheckBox("Show Communication Links")
        self.current_time_label = QtWidgets.QLabel("0.0s")
        self.current_step_label = QtWidgets.QLabel("0")
        self.current_energy_label = QtWidgets.QLabel("0.0 J")
        self.simulation_rate_label = QtWidgets.QLabel("0.0 steps/s")
        self.last_step_time = None

        # Add UI refresh timer with 5 Hz (200ms)
        self.ui_refresh_timer = QtCore.QTimer()
        self.ui_refresh_timer.timeout.connect(self.refresh_ui)
        self.ui_refresh_timer.start(200)  # 5 Hz refresh rate

        # Add trackers for last plotted points
        self.last_total_energy_index = 0
        self.node_energy_indices = {}

        # Add rate tracking for rolling average
        self.rate_history = []
        self.rate_window = 10  # Number of samples to average
        self.last_step_time = None

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        """Initialize the UI"""
        main_layout = QtWidgets.QHBoxLayout()

        # Create simulation controls
        self.sim_controls = SimulationControls(self)
        left_panel = QtWidgets.QVBoxLayout()
        left_panel.addWidget(self.create_simulation_list())
        left_panel.addWidget(self.create_simulation_control())

        # Add theme toggle button
        self.theme_toggle = QtWidgets.QPushButton("Toggle Theme")
        self.theme_toggle.clicked.connect(self.toggle_theme)
        left_panel.addWidget(self.theme_toggle)

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

        # Create energy graphs
        self.node_energy_graph = EnergyGraph("Node Energy", parent=self)
        self.total_energy_graph = EnergyGraph("Total Energy", parent=self)

        # Right panel for graphs
        right_panel = QtWidgets.QVBoxLayout()
        right_panel.addWidget(self.node_energy_graph.chart_view, 1)
        right_panel.addWidget(self.total_energy_graph.chart_view, 1)
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

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def apply_theme(self):
        """Apply the current theme to all components"""
        # Apply stylesheet
        self.setStyleSheet(ThemeManager.get_theme_stylesheet(self.is_dark_theme))

        # Update chart themes
        ThemeManager.apply_theme_to_chart(
            self.node_energy_graph.chart, self.is_dark_theme
        )
        ThemeManager.apply_theme_to_chart(
            self.total_energy_graph.chart, self.is_dark_theme
        )

        # Update button text
        self.theme_toggle.setText(
            "Switch to Light Theme" if self.is_dark_theme else "Switch to Dark Theme"
        )

        # Force update of the view
        self.update_view()

    def create_simulation_list(self):
        """Create the simulation list"""
        sim_list_box = QtWidgets.QGroupBox("Simulations")
        sim_layout = QtWidgets.QVBoxLayout()

        # Add simulation controls
        sim_layout.addWidget(self.sim_controls.sim_list)
        sim_layout.addWidget(self.sim_controls.run_pause_btn)
        sim_layout.addWidget(self.sim_controls.reset_btn)

        sim_list_box.setLayout(sim_layout)
        return sim_list_box

    def create_simulation_control(self):
        """Create simulation control panel"""
        control_panel = QtWidgets.QGroupBox("Simulation Control")
        control_layout = QtWidgets.QVBoxLayout()

        # Add simulation controls widget
        control_layout.addWidget(self.sim_controls.widget)

        control_panel.setLayout(control_layout)
        return control_panel

    def create_real_time_view(self):
        """Create the real-time view"""
        layout = QtWidgets.QVBoxLayout()

        # Schematic View with QGraphicsView
        layout.addWidget(self.schematic_view)

        # Toggle button to switch between views
        self.view_toggle_btn.clicked.connect(self.toggle_view)
        layout.addWidget(self.view_toggle_btn)

        # Load initial close-up view
        self.update_view()

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container

    def create_results_tab(self):
        """Create the results tab"""
        layout = QtWidgets.QVBoxLayout()

        # Create table for node statistics
        layout.addWidget(self.node_stats_table)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container

    def create_simulation_parameters(self):
        """Create the simulation parameters"""
        # Create horizontal layout for parameters and info
        horizontal_layout = QtWidgets.QHBoxLayout()

        # Create Parameters Panel (left side)
        param_box = QtWidgets.QGroupBox("Animation Parameters")
        param_layout = QtWidgets.QVBoxLayout()

        # Add simulation speed control
        speed_layout = QtWidgets.QHBoxLayout()
        speed_layout.addWidget(QtWidgets.QLabel("Simulation Speed (steps/s):"))
        speed_layout.addWidget(self.sim_controls.time_inputs["simulation_speed"])
        param_layout.addLayout(speed_layout)

        # Add toggle for communication links
        self.show_links_checkbox = QtWidgets.QCheckBox("Show Communication Links")
        self.show_links_checkbox.setChecked(True)
        self.show_links_checkbox.stateChanged.connect(self.toggle_links)
        param_layout.addWidget(self.show_links_checkbox)

        param_box.setLayout(param_layout)
        horizontal_layout.addWidget(param_box)

        # Create right side panel
        right_panel = QtWidgets.QVBoxLayout()
        right_panel.setSpacing(5)  # Reduce spacing between elements

        # Create Info Panel
        info_box = QtWidgets.QGroupBox("Simulation Info")
        info_layout = QtWidgets.QGridLayout()
        info_layout.setVerticalSpacing(2)  # Reduce vertical spacing

        # Current simulation info
        info_layout.addWidget(QtWidgets.QLabel("Current Time:"), 0, 0)
        info_layout.addWidget(self.current_time_label, 0, 1)
        info_layout.addWidget(QtWidgets.QLabel("Current Step:"), 0, 2)
        info_layout.addWidget(self.current_step_label, 0, 3)
        info_layout.addWidget(QtWidgets.QLabel("Simulation Rate:"), 1, 0)
        info_layout.addWidget(self.simulation_rate_label, 1, 1)
        info_layout.addWidget(QtWidgets.QLabel("Energy Consumed:"), 1, 2)
        info_layout.addWidget(self.current_energy_label, 1, 3)

        info_box.setLayout(info_layout)
        right_panel.addWidget(info_box)

        # Create Request Statistics Panel
        stats_box = QtWidgets.QGroupBox("Request Statistics")
        stats_layout = QtWidgets.QHBoxLayout()
        stats_layout.setSpacing(5)  # Reduce spacing between frames

        # Create labels for each request status with better formatting
        self.request_stats_labels = {}
        for status in RequestStatus:
            # Create a frame for each status
            frame = QtWidgets.QFrame()
            frame.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
            frame_layout = QtWidgets.QVBoxLayout()
            frame_layout.setSpacing(2)  # Reduce spacing within frames
            frame_layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins

            # Add status name label
            name_label = QtWidgets.QLabel(status.name)
            name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            frame_layout.addWidget(name_label)

            # Add count label
            self.request_stats_labels[status] = QtWidgets.QLabel("0")
            self.request_stats_labels[status].setAlignment(
                QtCore.Qt.AlignmentFlag.AlignCenter
            )
            self.request_stats_labels[status].setStyleSheet("font-weight: bold;")
            frame_layout.addWidget(self.request_stats_labels[status])

            frame.setLayout(frame_layout)
            stats_layout.addWidget(frame)

        stats_box.setLayout(stats_layout)
        right_panel.addWidget(stats_box)

        # Add right panel to main layout
        horizontal_layout.addLayout(right_panel)

        # Create container widget
        container = QtWidgets.QWidget()
        container.setLayout(horizontal_layout)
        return container

    def toggle_view(self):
        """Toggle between close-up and far views"""
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
            CloseUpView.load(
                self.schematic_view,
                self.sim_controls.current_simulation,
                self.show_links,
                self.is_dark_theme,
            )
        else:
            FarView.load(
                self.schematic_view,
                self.sim_controls.current_simulation,
                self.is_dark_theme,
            )

    def toggle_links(self, state):
        """Toggle communication links"""
        self.show_links = bool(state)
        self.update_view()

    def show_enlarged_graph(self, chart_view):
        """Show the enlarged version of the clicked graph"""
        dialog = EnlargedGraphDialog(chart_view, self)
        dialog.exec()

    def on_simulation_step(self):
        """Handle simulation step completion"""
        if self.sim_controls.current_simulation:
            self.sim_controls.current_simulation.steps_since_last_ui_update += 1

    def on_new_simulation(self):
        """Handle UI updates when a new simulation is created"""
        if self.sim_controls.current_simulation is None:
            return

        self.node_stats_table.update_stats(
            self.sim_controls.current_simulation.network.nodes,
            self.handle_checkbox_change,
        )
        self.update_view()
        self.total_energy_graph.clear()
        self.node_energy_graph.clear()

        # Reset graph indices for new simulation
        self.last_total_energy_index = 0
        self.node_energy_indices.clear()

        # Plot initial data if available
        if self.sim_controls.current_simulation.system_energy_history:
            cumulative_energy = 0
            for energy in self.sim_controls.current_simulation.system_energy_history:
                cumulative_energy += energy
                self.total_energy_graph.add_point(cumulative_energy)
            self.last_total_energy_index = len(
                self.sim_controls.current_simulation.system_energy_history
            )

    def on_simulation_selected(self):
        """Handle UI updates when a simulation is selected"""
        if self.sim_controls.current_simulation is None:
            return

        self.node_stats_table.update_stats(
            self.sim_controls.current_simulation.network.nodes,
            self.handle_checkbox_change,
        )
        self.update_view()

        # Clear existing graphs
        self.total_energy_graph.clear()
        self.node_energy_graph.clear()

        # Reset graph indices for selected simulation
        self.last_total_energy_index = 0
        self.node_energy_indices.clear()

        # Plot existing data for total energy
        if self.sim_controls.current_simulation.system_energy_history:
            cumulative_energy = 0
            for energy in self.sim_controls.current_simulation.system_energy_history:
                cumulative_energy += energy
                self.total_energy_graph.add_point(cumulative_energy)
            self.last_total_energy_index = len(
                self.sim_controls.current_simulation.system_energy_history
            )

        # Plot existing data for checked nodes
        self.update_checked_nodes_graphs()

    def on_simulation_reset(self):
        """Handle UI updates when a simulation is reset"""
        self.update_view()
        self.total_energy_graph.clear()
        self.node_energy_graph.clear()
        self.current_time_label.setText("0.0s")
        self.current_step_label.setText("0")
        self.current_energy_label.setText("0.0 J")
        self.simulation_rate_label.setText("0.0 steps/s")
        self.last_step_time = None
        self.rate_history.clear()  # Clear rate history on reset

        # Reset graph indices
        self.last_total_energy_index = 0
        self.node_energy_indices.clear()

        # Reset request statistics
        for label in self.request_stats_labels.values():
            label.setText("0")

    def on_nodes_updated(self):
        """Handle UI updates when nodes are added/removed"""
        self.update_view()

    def handle_checkbox_change(self, item):
        """Handle checkbox state changes in the stats table"""
        if self.sim_controls.current_simulation is None:
            return

        if not item or item.column() != 0:
            return

        row = item.row()
        node_item = self.node_stats_table.item(row, 1)
        if node_item:
            node_text = node_item.text()
            if item.checkState() == QtCore.Qt.Checked:
                # Add node to graph with all history
                node = None
                for n in self.sim_controls.current_simulation.network.nodes:
                    if f"{type(n).__name__} {n.node_id}" == node_text:
                        node = n
                        break

                if node and len(node.energy_history) > 0:
                    self.node_energy_indices[node_text] = (
                        0  # Reset index for new selection
                    )
                    for energy in node.energy_history:
                        self.node_energy_graph.add_node_point(node_text, energy)
                    self.node_energy_indices[node_text] = len(node.energy_history)
            else:
                # Remove node from graph and its index tracker
                self.node_energy_graph.remove_node_series(node_text)
                self.node_energy_indices.pop(node_text, None)

    def update_checked_nodes_graphs(self):
        """Update graphs for checked nodes"""
        if self.sim_controls.current_simulation is None:
            return

        # Create a lookup dictionary for quick node access
        node_lookup = {
            f"{type(node).__name__} {node.node_id}": node
            for node in self.sim_controls.current_simulation.network.nodes
        }

        # Process only checked rows
        for row in range(self.node_stats_table.rowCount()):
            checkbox_item = self.node_stats_table.item(row, 0)
            if not (
                checkbox_item
                and checkbox_item.checkState() == QtCore.Qt.CheckState.Checked
            ):
                continue

            node_item = self.node_stats_table.item(row, 1)
            if not node_item:
                continue

            node_text = node_item.text()
            if node := node_lookup.get(node_text):
                # Initialize index tracker for new nodes
                if node_text not in self.node_energy_indices:
                    self.node_energy_indices[node_text] = 0

                # Add only new points
                start_idx = self.node_energy_indices[node_text]
                new_points = node.energy_history[start_idx:]
                for energy in new_points:
                    self.node_energy_graph.add_node_point(node_text, energy)

                # Update the last plotted index
                self.node_energy_indices[node_text] = len(node.energy_history)

    def refresh_ui(self):
        """Update UI elements at fixed rate"""
        if (
            self.sim_controls.current_simulation
            and not self.sim_controls.current_simulation.is_paused
        ):
            self.update_view()
            self.update_simulation_info()

    def update_simulation_info(self):
        """Update simulation information displays"""
        simulation = self.sim_controls.current_simulation
        if simulation is None:
            return

        # Calculate simulation rate with rolling average
        current_time_ns = QtCore.QDateTime.currentMSecsSinceEpoch() * 1_000_000
        if self.last_step_time is not None:
            time_diff = (current_time_ns - self.last_step_time) / 1_000_000_000
            if time_diff > 0:
                current_rate = simulation.steps_since_last_ui_update / time_diff

                # Add current rate to history
                self.rate_history.append(current_rate)

                # Keep only the last N samples
                if len(self.rate_history) > self.rate_window:
                    self.rate_history.pop(0)

                # Calculate average rate
                avg_rate = sum(self.rate_history) / len(self.rate_history)
                self.simulation_rate_label.setText(f"{avg_rate:.1f} steps/s")
        self.last_step_time = current_time_ns
        simulation.steps_since_last_ui_update = 0

        # Update info displays
        self.current_time_label.setText(f"{simulation.current_time:.1f}s")
        self.current_step_label.setText(str(simulation.current_step))
        self.current_energy_label.setText(f"{simulation.system_energy_consumed:.2f} J")

        # Add only new points to total energy graph
        if len(simulation.system_energy_history) > self.last_total_energy_index:
            cumulative_energy = sum(
                simulation.system_energy_history[: self.last_total_energy_index]
            )
            new_points = simulation.system_energy_history[
                self.last_total_energy_index :
            ]

            for energy in new_points:
                cumulative_energy += energy
                self.total_energy_graph.add_point(cumulative_energy)

            self.last_total_energy_index = len(simulation.system_energy_history)

        # Update stats and node energy graphs
        self.node_stats_table.update_stats(
            simulation.network.nodes, self.handle_checkbox_change
        )
        self.update_checked_nodes_graphs()

        # Update request statistics
        if hasattr(simulation, "request_state_stats"):
            for status, count in simulation.request_state_stats.items():
                self.request_stats_labels[status].setText(str(count))


app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon("images/logo.png"))  # Taskbar icon
window = SimulationUI()
window.show()
sys.exit(app.exec())
