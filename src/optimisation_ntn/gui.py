import ctypes
import platform
import sys

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCharts import QChartView

from optimisation_ntn.ui.dialogs.enlarged_graph import EnlargedGraphDialog
from optimisation_ntn.ui.graphs import EnergyGraph
from optimisation_ntn.ui.simulation_controls import SimulationControls
from optimisation_ntn.ui.stats_table import NodeStatsTable
from optimisation_ntn.ui.theme_manager import ThemeManager
from optimisation_ntn.ui.views import CloseUpView, FarView

# Task bar Icon on Windows
if platform.system() == "Windows":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("optimisation_ntn")


class SimulationUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimisation NTN")
        self.setGeometry(100, 100, 1200, 700)
        self.current_view = "close"
        self.show_links = True
        self.is_dark_theme = True
        self.setWindowIcon(QtGui.QIcon("images/logo.png"))
        self.initUI()
        self.apply_theme()

    def initUI(self):
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
        sim_list_box = QtWidgets.QGroupBox("Simulations")
        sim_layout = QtWidgets.QVBoxLayout()

        # Add simulation controls
        sim_layout.addWidget(self.sim_controls.sim_list)
        sim_layout.addWidget(self.sim_controls.run_pause_btn)
        sim_layout.addWidget(self.sim_controls.reset_btn)

        # Add buttons
        create_btn = QtWidgets.QPushButton("New")
        create_btn.clicked.connect(self.sim_controls.create_new_simulation)
        sim_layout.addWidget(create_btn)

        sim_list_box.setLayout(sim_layout)
        return sim_list_box

    def create_simulation_control(self):
        control_box = QtWidgets.QGroupBox("Simulation Control")
        control_layout = QtWidgets.QVBoxLayout()

        # Add node controls
        node_controls = QtWidgets.QGridLayout()
        node_controls.addWidget(QtWidgets.QLabel("Base Stations:"), 0, 0)
        node_controls.addWidget(self.sim_controls.num_bs_input, 0, 1)
        node_controls.addWidget(QtWidgets.QLabel("HAPS:"), 1, 0)
        node_controls.addWidget(self.sim_controls.num_haps_input, 1, 1)
        node_controls.addWidget(QtWidgets.QLabel("Users:"), 2, 0)
        node_controls.addWidget(self.sim_controls.num_users_input, 2, 1)
        control_layout.addLayout(node_controls)

        # Add step duration and time step controls
        step_controls = QtWidgets.QGridLayout()
        step_controls.addWidget(QtWidgets.QLabel("Step Duration (s):"), 0, 0)
        step_controls.addWidget(self.sim_controls.step_duration_input, 0, 1)
        step_controls.addWidget(QtWidgets.QLabel("UI Update Interval (ms):"), 1, 0)
        step_controls.addWidget(self.sim_controls.time_step_input, 1, 1)
        control_layout.addLayout(step_controls)

        control_box.setLayout(control_layout)
        return control_box

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
        self.update_view()

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container

    def create_results_tab(self):
        layout = QtWidgets.QVBoxLayout()

        # Create table for node statistics
        self.node_stats_table = NodeStatsTable()
        layout.addWidget(self.node_stats_table)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container

    def create_simulation_parameters(self):
        # Create horizontal layout for parameters and info
        horizontal_layout = QtWidgets.QHBoxLayout()

        # Create Parameters Panel (left side)
        param_box = QtWidgets.QGroupBox("Simulation Parameters")
        param_layout = QtWidgets.QHBoxLayout()

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

        # Current simulation info
        info_layout.addWidget(QtWidgets.QLabel("Current Time:"), 2, 0)
        self.current_time_label = QtWidgets.QLabel("0.0s")
        info_layout.addWidget(self.current_time_label, 2, 1)

        info_layout.addWidget(QtWidgets.QLabel("Current Step:"), 3, 0)
        self.current_step_label = QtWidgets.QLabel("0")
        info_layout.addWidget(self.current_step_label, 3, 1)

        # Add energy consumption display
        info_layout.addWidget(QtWidgets.QLabel("Energy Consumed:"), 4, 0)
        self.current_energy_label = QtWidgets.QLabel("0.0 J")
        info_layout.addWidget(self.current_energy_label, 4, 1)

        info_box.setLayout(info_layout)
        horizontal_layout.addWidget(info_box)

        # Create container widget
        container = QtWidgets.QWidget()
        container.setLayout(horizontal_layout)
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
        self.show_links = bool(state)
        self.update_view()

    def show_enlarged_graph(self, chart_view):
        """Show the enlarged version of the clicked graph"""
        dialog = EnlargedGraphDialog(chart_view, self)
        dialog.exec()

    def on_simulation_step(self):
        """Handle UI updates after each simulation step"""
        simulation = self.sim_controls.current_simulation
        current_time = simulation.current_time

        # Update time labels
        self.current_time_label.setText(f"{current_time:.1f}s")
        self.current_step_label.setText(str(simulation.current_step))
        self.current_energy_label.setText(f"{simulation.system_energy_consumed:.2f} J")

        # Update total energy graph
        self.total_energy_graph.add_point(
            current_time, simulation.system_energy_consumed
        )

        # Update node statistics and graphs
        self.node_stats_table.update_stats(
            simulation.network.nodes, self.handle_checkbox_change
        )
        self.update_checked_nodes_graphs(current_time)

        # Update view
        self.update_view()

    def on_new_simulation(self):
        """Handle UI updates when a new simulation is created"""
        self.node_stats_table.update_stats(
            self.sim_controls.current_simulation.network.nodes,
            self.handle_checkbox_change,
        )
        self.update_view()
        self.total_energy_graph.clear()
        self.node_energy_graph.clear()

    def on_simulation_selected(self):
        """Handle UI updates when a simulation is selected"""
        self.node_stats_table.update_stats(
            self.sim_controls.current_simulation.network.nodes,
            self.handle_checkbox_change,
        )
        self.update_view()

    def on_simulation_reset(self):
        """Handle UI updates when a simulation is reset"""
        self.update_view()
        self.total_energy_graph.clear()
        self.node_energy_graph.clear()
        self.current_time_label.setText("0.0s")
        self.current_step_label.setText("0")
        self.current_energy_label.setText("0.0 J")

    def on_nodes_updated(self):
        """Handle UI updates when nodes are added/removed"""
        self.update_view()

    def handle_checkbox_change(self, item):
        """Handle checkbox state changes in the stats table"""
        if not item or item.column() != 0:
            return

        row = item.row()
        node_item = self.node_stats_table.item(row, 1)
        if node_item:
            node_text = node_item.text()
            if item.checkState() == QtCore.Qt.Checked:
                # Add node to graph
                node = None
                for n in self.sim_controls.current_simulation.network.nodes:
                    if f"{type(n).__name__} {n.node_id}" == node_text:
                        node = n
                        break

                if node and len(node.energy_history) > 0:
                    for i, energy in enumerate(node.energy_history):
                        time_point = i * self.sim_controls.current_simulation.time_step
                        self.node_energy_graph.add_node_point(
                            node_text, time_point, energy
                        )
            else:
                # Remove node from graph
                self.node_energy_graph.remove_node_series(node_text)

    def update_checked_nodes_graphs(self, current_time):
        """Update graphs for checked nodes"""
        for row in range(self.node_stats_table.rowCount()):
            checkbox_item = self.node_stats_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == QtCore.Qt.Checked:
                node_item = self.node_stats_table.item(row, 1)
                if node_item:
                    node_text = node_item.text()
                    for node in self.sim_controls.current_simulation.network.nodes:
                        if f"{type(node).__name__} {node.node_id}" == node_text:
                            if len(node.energy_history) > 0:
                                self.node_energy_graph.add_node_point(
                                    node_text, current_time, node.energy_history[-1]
                                )
                            break


app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon("images/logo.png"))  # Taskbar icon
window = SimulationUI()
window.show()
sys.exit(app.exec())
