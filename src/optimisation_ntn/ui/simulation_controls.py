from PySide6 import QtCore, QtWidgets
from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.simulation import Simulation


class SimulationControls:
    def __init__(self, parent):
        self.parent = parent
        self.simulations = {}
        self.current_simulation = None
        self.setup_ui()

    def setup_ui(self):
        # Create simulation list
        self.sim_list = QtWidgets.QListWidget()
        self.sim_list.itemSelectionChanged.connect(self.update_simulation_selection)
        self.sim_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.sim_list.customContextMenuRequested.connect(self.show_context_menu)

        # Create control buttons
        self.run_pause_btn = QtWidgets.QPushButton("Run")
        self.run_pause_btn.clicked.connect(self.toggle_simulation)

        self.reset_btn = QtWidgets.QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_simulation)

        # Create spinboxes for node counts
        self.num_bs_input = QtWidgets.QSpinBox()
        self.num_bs_input.setRange(1, 10)
        self.num_bs_input.valueChanged.connect(self._on_bs_value_changed)

        self.num_haps_input = QtWidgets.QSpinBox()
        self.num_haps_input.setRange(1, 5)
        self.num_haps_input.valueChanged.connect(self._on_haps_value_changed)

        self.num_users_input = QtWidgets.QSpinBox()
        self.num_users_input.setRange(0, 200)
        self.num_users_input.valueChanged.connect(self._on_users_value_changed)

        # Create step duration input
        self.step_duration_input = QtWidgets.QDoubleSpinBox()
        self.step_duration_input.setRange(0.00001, 10.0)
        self.step_duration_input.setDecimals(5)
        self.step_duration_input.setSingleStep(0.0001)
        self.step_duration_input.setValue(0.001)
        self.step_duration_input.valueChanged.connect(self._on_step_duration_changed)

        # Create time step input for UI updates
        self.time_step_input = QtWidgets.QSpinBox()
        self.time_step_input.setRange(1, 100)
        self.time_step_input.setValue(100)
        self.time_step_input.valueChanged.connect(self._on_time_step_changed)

    def create_new_simulation(self):
        """Create a new simulation and add it to the list"""
        try:
            simulation_name = f"Simulation {self.sim_list.count() + 1}"
            simulation = Simulation(debug=False)
            self.simulations[simulation_name] = simulation
            self.current_simulation = simulation

            # Add to list and select it
            self.sim_list.addItem(simulation_name)
            self.sim_list.setCurrentRow(self.sim_list.count() - 1)

            # Update UI parameters
            self.update_ui_parameters()

            # Enable step duration input
            self.step_duration_input.setEnabled(True)

            # Notify parent of new simulation
            self.parent.on_new_simulation()

        except Exception as e:
            print(f"Error creating simulation: {str(e)}")

    def update_ui_parameters(self):
        """Update UI controls to match current simulation"""
        if self.current_simulation:
            # Update spinboxes without triggering their signals
            self.num_bs_input.blockSignals(True)
            self.num_haps_input.blockSignals(True)
            self.num_users_input.blockSignals(True)
            self.step_duration_input.blockSignals(True)

            # Count nodes of each type
            bs_count = self.current_simulation.network.count_nodes_by_type(BaseStation)
            haps_count = self.current_simulation.network.count_nodes_by_type(HAPS)
            users_count = self.current_simulation.network.count_nodes_by_type(
                UserDevice
            )

            # Update UI values
            self.num_bs_input.setValue(bs_count)
            self.num_haps_input.setValue(haps_count)
            self.num_users_input.setValue(users_count)
            self.step_duration_input.setValue(self.current_simulation.time_step)

            # Re-enable signals
            self.num_bs_input.blockSignals(False)
            self.num_haps_input.blockSignals(False)
            self.num_users_input.blockSignals(False)
            self.step_duration_input.blockSignals(False)

    def toggle_simulation(self):
        """Toggle between running and paused states"""
        if self.current_simulation:
            if hasattr(self, "timer") and self.timer.isActive():
                # Pause simulation
                self.timer.stop()
                self.current_simulation.is_paused = True
                self.run_pause_btn.setText("Resume")
            else:
                # Start/Resume simulation
                self.start_simulation()
                self.run_pause_btn.setText("Pause")

    def start_simulation(self):
        if self.current_simulation:
            self.current_simulation.is_paused = False
            update_interval = self.time_step_input.value()

            # Disable step duration input while simulation is running
            self.step_duration_input.setEnabled(False)

            # Create timer for UI updates
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.simulation_step)
            self.timer.start(update_interval)
            self.run_pause_btn.setText("Pause")

    def simulation_step(self):
        """Handle one simulation step"""
        if self.current_simulation and not self.current_simulation.is_paused:
            can_continue = self.current_simulation.step()

            if can_continue:
                # Notify parent to update UI
                self.parent.on_simulation_step()
            else:
                self.timer.stop()
                self.run_pause_btn.setText("Run")

    def reset_simulation(self):
        """Reset the current simulation"""
        if self.current_simulation:
            # Stop timer if running
            if hasattr(self, "timer") and self.timer.isActive():
                self.timer.stop()
                self.run_pause_btn.setText("Run")

            # Re-enable step duration input
            self.step_duration_input.setEnabled(True)

            self.current_simulation.reset()
            self.update_ui_parameters()

            # Notify parent of reset
            self.parent.on_simulation_reset()

    def update_simulation_selection(self):
        """Update the selected simulation"""
        try:
            if self.sim_list.currentItem():
                simulation_name = self.sim_list.currentItem().text()
                if simulation_name in self.simulations:
                    self.current_simulation = self.simulations[simulation_name]
                    self.update_ui_parameters()
                    # Notify parent of selection change
                    self.parent.on_simulation_selected()
                else:
                    print(f"Warning: Simulation '{simulation_name}' not found")
        except Exception as e:
            print(f"Error updating simulation selection: {str(e)}")

    def show_context_menu(self, position):
        """Show context menu for simulation list items"""
        menu = QtWidgets.QMenu()

        if self.sim_list.currentItem():
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(self.rename_simulation)
            menu.exec_(self.sim_list.mapToGlobal(position))

    def rename_simulation(self):
        """Rename the selected simulation"""
        current_item = self.sim_list.currentItem()
        if current_item:
            old_name = current_item.text()
            new_name, ok = QtWidgets.QInputDialog.getText(
                self.parent,
                "Rename Simulation",
                "Enter new name:",
                QtWidgets.QLineEdit.Normal,
                old_name,
            )

            if ok and new_name:
                self.simulations[new_name] = self.simulations.pop(old_name)
                current_item.setText(new_name)

    def _on_bs_value_changed(self, value):
        """Handle base station count changes"""
        if self.current_simulation:
            self.current_simulation.set_nodes(BaseStation, value)
            self.parent.on_nodes_updated()

    def _on_haps_value_changed(self, value):
        """Handle HAPS count changes"""
        if self.current_simulation:
            self.current_simulation.set_nodes(HAPS, value)
            self.parent.on_nodes_updated()

    def _on_users_value_changed(self, value):
        """Handle user count changes"""
        if self.current_simulation:
            self.current_simulation.set_nodes(UserDevice, value)
            self.parent.on_nodes_updated()

    def _on_step_duration_changed(self, value):
        """Handle step duration changes"""
        if self.current_simulation:
            self.current_simulation.time_step = value

    def _on_time_step_changed(self, value):
        """Handle UI update interval changes"""
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.setInterval(value)
