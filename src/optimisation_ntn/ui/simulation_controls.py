""" Simulation controls UI for managing simulations and their parameters """

from typing import Literal, cast

import numpy as np
from PySide6 import QtCore, QtWidgets

from optimisation_ntn.algorithms.assignment.strategy_factory import (
    AssignmentStrategyFactory,
)
from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.simulation import Simulation


class SimulationControls:
    """Simulation controls UI"""

    def __init__(self, parent):
        self.parent = parent
        self.simulations = {}
        self.current_simulation = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI"""
        # Create simulation list
        self.sim_list = QtWidgets.QListWidget()
        self.sim_list.itemSelectionChanged.connect(self.update_simulation_selection)
        self.sim_list.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
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

        # Create strategy selection combos
        self.assignment_strategy_combo = QtWidgets.QComboBox()
        all_strategies = AssignmentStrategyFactory.available_strategies() + [
            "GA",
            "DE",
            "PSO",
        ]
        self.assignment_strategy_combo.addItems(all_strategies)
        self.assignment_strategy_combo.currentTextChanged.connect(
            self._on_assignment_strategy_changed
        )

        self.power_strategy_combo = QtWidgets.QComboBox()
        self.power_strategy_combo.addItems(["AllOn", "OnDemand", "OnDemandWithTimeout"])
        self.power_strategy_combo.currentTextChanged.connect(
            self._on_power_strategy_changed
        )

    def create_new_simulation(self):
        """Create a new simulation and add it to the list"""
        try:
            simulation_name = f"Simulation {self.sim_list.count() + 1}"

            # Get power strategy as proper Literal type
            power_strategy_text = self.power_strategy_combo.currentText()
            if power_strategy_text not in ["AllOn", "OnDemand", "OnDemandWithTimeout"]:
                power_strategy_text = "OnDemand"  # Default fallback

            # cast to Literal
            power_strategy = cast(
                Literal["AllOn", "OnDemand", "OnDemandWithTimeout"], power_strategy_text
            )

            # Create simulation with selected strategies
            simulation = Simulation(
                debug=False,
                power_strategy=power_strategy,
                optimizer=None,
            )

            # Set assignment strategy
            strategy = self.assignment_strategy_combo.currentText()
            if strategy in ["GA", "DE", "PSO"]:
                simulation.optimizer = strategy
                self.simulations[simulation_name] = simulation
                self.current_simulation = simulation

                # Add to list and select it
                self.sim_list.addItem(simulation_name)
                self.sim_list.setCurrentRow(self.sim_list.count() - 1)

                # Update UI parameters
                self.update_ui_parameters()

                # Prompt for vector before enabling simulation
                self._prompt_for_assignment_vector()
            else:
                strategy_obj = AssignmentStrategyFactory.get_strategy(
                    strategy, simulation.network
                )
                simulation.assignment_strategy = strategy_obj
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

        except ValueError as e:
            print(f"Error creating simulation: {str(e)}")

    def update_ui_parameters(self):
        """Update UI controls to match current simulation"""
        if self.current_simulation:
            # Block signals during update
            self.num_bs_input.blockSignals(True)
            self.num_haps_input.blockSignals(True)
            self.num_users_input.blockSignals(True)
            self.step_duration_input.blockSignals(True)
            self.power_strategy_combo.blockSignals(True)
            self.assignment_strategy_combo.blockSignals(True)

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

            # Update strategy combos
            if hasattr(self.current_simulation, "power_strategy"):
                self.power_strategy_combo.setCurrentText(
                    self.current_simulation.power_strategy
                )

            if self.current_simulation.optimizer:
                self.assignment_strategy_combo.setCurrentText(
                    self.current_simulation.optimizer
                )
            elif hasattr(self.current_simulation.assignment_strategy, "__class__"):
                strategy_name = (
                    self.current_simulation.assignment_strategy.__class__.__name__
                )
                self.assignment_strategy_combo.setCurrentText(strategy_name)

            # Re-enable signals
            self.num_bs_input.blockSignals(False)
            self.num_haps_input.blockSignals(False)
            self.num_users_input.blockSignals(False)
            self.step_duration_input.blockSignals(False)
            self.power_strategy_combo.blockSignals(False)
            self.assignment_strategy_combo.blockSignals(False)

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
        """Start or resume simulation"""
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
            try:
                can_continue = self.current_simulation.step()

                if can_continue:
                    # Notify parent to update UI
                    self.parent.on_simulation_step()
                else:
                    self.timer.stop()
                    self.run_pause_btn.setText("Run")
                    # Optionally show a message that simulation has ended
                    QtWidgets.QMessageBox.information(
                        self.parent,
                        "Simulation Complete",
                        "The simulation has reached the end of available data.",
                    )

            except IndexError as e:
                # Handle matrix bounds error
                self.timer.stop()
                self.run_pause_btn.setText("Run")
                QtWidgets.QMessageBox.warning(
                    self.parent,
                    "Simulation Ended",
                    f"The simulation has reached the end of the request data matrix. {e}",
                )

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

        except ValueError as e:
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

    def _on_assignment_strategy_changed(self, strategy):
        """Handle assignment strategy changes"""
        if self.current_simulation:
            if strategy in ["GA", "DE", "PSO"]:
                self.current_simulation.optimizer = strategy
                self._prompt_for_assignment_vector()
            else:
                self.current_simulation.optimizer = None
                strategy_obj = AssignmentStrategyFactory.get_strategy(
                    strategy, self.current_simulation.network
                )
                self.current_simulation.assignment_strategy = strategy_obj

    def _on_power_strategy_changed(self, strategy):
        """Handle power strategy changes"""
        if self.current_simulation:
            # Update power strategy
            self.current_simulation.power_strategy = strategy

            # Reset simulation to apply new power strategy
            self.current_simulation.reset()

            # Update UI
            self.update_ui_parameters()

            # Notify parent of reset
            self.parent.on_simulation_reset()

    def _prompt_for_assignment_vector(self):
        """Prompt user for initial assignment vector when using optimization"""
        if not self.current_simulation:
            return

        n_nodes = len(self.current_simulation.network.compute_nodes)
        n_users = self.current_simulation.user_count

        # Create dialog for vector input
        dialog = QtWidgets.QDialog(self.parent)
        dialog.setWindowTitle("Initial Assignment Vector")
        layout = QtWidgets.QVBoxLayout()

        # Add explanation
        layout.addWidget(
            QtWidgets.QLabel(
                f"Enter {n_users} comma-separated integers between 0 and {n_nodes-1}\n"
                "representing the initial node assignments for each user."
            )
        )

        # Add text input
        text_input = QtWidgets.QLineEdit()
        text_input.setPlaceholderText(f"e.g., 0,1,2,1,0 (for {n_users} users)")
        layout.addWidget(text_input)

        # Add random vector option
        random_btn = QtWidgets.QPushButton("Generate Random Vector")

        def set_random_vector():
            vector = np.random.randint(0, n_nodes, n_users)
            text_input.setText(",".join(map(str, vector)))

        random_btn.clicked.connect(set_random_vector)
        layout.addWidget(random_btn)

        # Add buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            try:
                vector = np.array(
                    [int(x.strip()) for x in text_input.text().split(",")]
                )
                if len(vector) == n_users and all(0 <= x < n_nodes for x in vector):
                    self.current_simulation.initial_assignment = vector
                else:
                    QtWidgets.QMessageBox.warning(
                        self.parent,
                        "Invalid Input",
                        f"Please enter exactly {n_users} integers between 0 and {n_nodes-1}.",
                    )
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self.parent,
                    "Invalid Input",
                    "Please enter valid comma-separated integers.",
                )
