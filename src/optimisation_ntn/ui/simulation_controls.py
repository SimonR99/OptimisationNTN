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
from optimisation_ntn.simulation import Simulation, SimulationConfig
from optimisation_ntn.algorithms.assignment.matrix_based import MatrixBasedAssignment


# pylint: disable=too-many-instance-attributes
class SimulationControls:
    """Simulation controls UI"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.simulations = {}
        self.current_simulation = None

        # Initialize UI component containers
        self.sim_list = None
        self.run_pause_btn = None
        self.reset_btn = None
        self.node_inputs = {}
        self.time_inputs = {}
        self.strategy_combos = {}
        self.widget = None
        self._assignment_vector = None

        # Initialize timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.simulation_step)

        # Initialize simulation timer
        self.simulation_timer = QtCore.QTimer()
        self.simulation_timer.timeout.connect(self.simulation_step)

        # Create UI components
        self._create_ui_components()
        self._setup_ui_layout()

    def _create_ui_components(self):
        """Create all UI components"""
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

        # Create input controls
        self._create_input_controls()
        self._create_strategy_controls()

    def _create_input_controls(self):
        """Create spinbox controls for simulation parameters"""
        # Node count inputs
        self.node_inputs = {
            "bs": self._create_spinbox(1, 10, self._on_bs_value_changed),
            "haps": self._create_spinbox(1, 5, self._on_haps_value_changed),
            "users": self._create_spinbox(0, 200, self._on_users_value_changed),
        }

        # Time control inputs
        step_duration_config = {
            "min_val": 0.00001,
            "max_val": 10.0,
            "decimals": 5,
            "step": 0.0001,
            "initial": 0.001,
        }

        simulation_speed_config = {
            "min_val": 0.1,
            "max_val": 1000.0,
            "decimals": 1,
            "step": 1.0,
            "initial": 10.0,
        }

        self.time_inputs = {
            "step_duration": self._create_double_spinbox(
                config=step_duration_config, on_change=self._on_step_duration_changed
            ),
            "simulation_speed": self._create_double_spinbox(
                config=simulation_speed_config,
                on_change=self._on_simulation_speed_changed,
            ),
            "max_time": self._create_spinbox(1, 3600, self._on_max_time_changed, 300),
        }
        self.time_inputs["simulation_speed"].setRange(1, 1000)
        self.time_inputs["simulation_speed"].setValue(100)
        self.time_inputs["max_time"].setRange(1, 3600)
        self.time_inputs["max_time"].setValue(300)

    def _create_strategy_controls(self):
        """Create strategy selection controls"""
        # Assignment strategy combo
        all_strategies = AssignmentStrategyFactory.available_strategies()

        assignment_combo = self._create_combobox(
            all_strategies, self._on_assignment_strategy_changed
        )

        self.strategy_combos = {
            "assignment": assignment_combo,
            "power": self._create_combobox(
                ["AllOn", "OnDemand", "OnDemandWithTimeout", "Random"],
                self._on_power_strategy_changed,
            ),
        }

    @staticmethod
    def _create_spinbox(min_val, max_val, on_change, initial_value=None):
        """Create a QSpinBox with given parameters"""
        spinbox = QtWidgets.QSpinBox()
        spinbox.setRange(min_val, max_val)
        if initial_value is not None:
            spinbox.setValue(initial_value)
        spinbox.valueChanged.connect(on_change)
        return spinbox

    @staticmethod
    def _create_double_spinbox(*, config, on_change):
        """Create a QDoubleSpinBox with given configuration

        Args:
            config (dict): Configuration with min_val, max_val, decimals, step, initial
            on_change (callable): Callback for value changes
        """
        spinbox = QtWidgets.QDoubleSpinBox()
        spinbox.setRange(config["min_val"], config["max_val"])
        spinbox.setDecimals(config["decimals"])
        spinbox.setSingleStep(config["step"])
        spinbox.setValue(config["initial"])
        spinbox.valueChanged.connect(on_change)
        return spinbox

    @staticmethod
    def _create_combobox(items, on_change):
        """Create a QComboBox with given items"""
        combo = QtWidgets.QComboBox()
        combo.addItems(items)
        combo.currentTextChanged.connect(on_change)
        return combo

    def create_new_simulation(self):
        """Create a new simulation and add it to the list"""
        try:
            simulation_name = f"Simulation {self.sim_list.count() + 1}"

            # Get power strategy as proper Literal type
            power_strategy_text = self.strategy_combos["power"].currentText()
            if power_strategy_text not in [
                "AllOn",
                "OnDemand",
                "OnDemandWithTimeout",
                "Random",
            ]:
                power_strategy_text = "OnDemand"  # Default fallback

            # cast to Literal
            power_strategy = cast(
                Literal["AllOn", "OnDemand", "OnDemandWithTimeout", "Random"],
                power_strategy_text,
            )

            # Create simulation with selected strategies
            simulation = Simulation(
                config=SimulationConfig(
                    debug=False,
                    power_strategy=power_strategy,
                    optimizer=None,
                    time_step=1.0 / self.time_inputs["simulation_speed"].value(),
                    max_time=self.time_inputs["max_time"].value(),
                )
            )
            simulation.enable_stats_tracking()

            # Set assignment strategy
            strategy = self.strategy_combos["assignment"].currentText()

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
            self.time_inputs["step_duration"].setEnabled(True)

            # Notify parent of new simulation
            self.parent.on_new_simulation()

        except ValueError as e:
            print(f"Error creating simulation: {str(e)}")

    def update_ui_parameters(self):
        """Update UI controls to match current simulation"""
        if self.current_simulation:
            # Block signals during update
            self.node_inputs["bs"].blockSignals(True)
            self.node_inputs["haps"].blockSignals(True)
            self.node_inputs["users"].blockSignals(True)
            self.time_inputs["step_duration"].blockSignals(True)
            self.strategy_combos["power"].blockSignals(True)
            self.strategy_combos["assignment"].blockSignals(True)
            self.time_inputs["max_time"].blockSignals(True)

            # Count nodes of each type
            bs_count = self.current_simulation.network.count_nodes_by_type(BaseStation)
            haps_count = self.current_simulation.network.count_nodes_by_type(HAPS)
            users_count = self.current_simulation.network.count_nodes_by_type(
                UserDevice
            )

            # Update UI values
            self.node_inputs["bs"].setValue(bs_count)
            self.node_inputs["haps"].setValue(haps_count)
            self.node_inputs["users"].setValue(users_count)
            self.time_inputs["step_duration"].setValue(
                self.current_simulation.time_step
            )

            # Update strategy combos
            if hasattr(self.current_simulation, "power_strategy"):
                self.strategy_combos["power"].setCurrentText(
                    self.current_simulation.config.power_strategy
                )

            if self.current_simulation.optimizer:
                self.strategy_combos["assignment"].setCurrentText(
                    self.current_simulation.optimizer
                )
            elif hasattr(self.current_simulation.assignment_strategy, "__class__"):
                strategy_name = (
                    self.current_simulation.assignment_strategy.__class__.__name__
                )
                self.strategy_combos["assignment"].setCurrentText(strategy_name)

            # Update max time
            self.time_inputs["max_time"].setValue(int(self.current_simulation.max_time))

            # Re-enable signals
            self.node_inputs["bs"].blockSignals(False)
            self.node_inputs["haps"].blockSignals(False)
            self.node_inputs["users"].blockSignals(False)
            self.time_inputs["step_duration"].blockSignals(False)
            self.strategy_combos["power"].blockSignals(False)
            self.strategy_combos["assignment"].blockSignals(False)
            self.time_inputs["max_time"].blockSignals(False)

    def toggle_simulation(self):
        """Toggle between running and paused states"""
        if self.current_simulation:
            if self.simulation_timer.isActive():
                # Pause simulation
                self.simulation_timer.stop()
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
            speed = self.time_inputs["simulation_speed"].value()
            interval = int(1000 / speed)  # Convert steps/s to timer interval in ms
            self.simulation_timer.start(interval)
            self.run_pause_btn.setText("Pause")

    def simulation_step(self):
        """Handle one simulation step"""
        if self.current_simulation and not self.current_simulation.is_paused:
            try:
                can_continue = self.current_simulation.step()

                # Notify parent of step completion
                self.parent.on_simulation_step()

                if not can_continue:
                    self.simulation_timer.stop()
                    self.run_pause_btn.setText("Run")
                    QtWidgets.QMessageBox.information(
                        self.parent,
                        "Simulation Complete",
                        "The simulation has reached the end of available data.",
                    )

            except IndexError as e:
                self.simulation_timer.stop()
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
            if self.timer.isActive():
                self.timer.stop()
                self.run_pause_btn.setText("Run")

            # Re-enable step duration input
            self.time_inputs["step_duration"].setEnabled(True)

            # Reset the simulation
            self.current_simulation.reset()

            # If using matrix-based strategy, reapply the assignment vector
            if isinstance(
                self.current_simulation.assignment_strategy, MatrixBasedAssignment
            ):
                if hasattr(self, "_assignment_vector"):
                    matrix_strategy = MatrixBasedAssignment(
                        self.current_simulation.network
                    )
                    matrix_strategy.set_assignment_matrix(self._assignment_vector)
                    self.current_simulation.assignment_strategy = matrix_strategy

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
                QtWidgets.QLineEdit.EchoMode.Normal,
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

    def _on_simulation_speed_changed(self, value):
        """Handle simulation speed changes"""
        if value > 0:
            # Only update timer interval, don't change step duration
            interval = int(1000 / value)
            if self.simulation_timer.isActive():
                self.simulation_timer.setInterval(interval)

    def _on_assignment_strategy_changed(self, strategy):
        """Handle assignment strategy changes"""
        if not self.current_simulation:
            self.create_new_simulation()

        if strategy == "MatrixBased":
            self.current_simulation.optimizer = None
            self._setup_matrix_assignment()
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

    def _setup_matrix_assignment(self):
        """Setup matrix-based assignment with user input vector"""
        if not self.current_simulation:
            return

        n_nodes = len(self.current_simulation.network.compute_nodes)
        n_users = self.current_simulation.user_count

        # Create dialog for vector input
        dialog = QtWidgets.QDialog(self.parent)
        dialog.setWindowTitle("Assignment Vector")
        layout = QtWidgets.QVBoxLayout()

        # Add explanation
        layout.addWidget(
            QtWidgets.QLabel(
                f"Enter {n_users} comma-separated integers between 0 and {n_nodes-1}\n"
                "representing the node assignments for each user."
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
                    # Store the vector for later use
                    self._assignment_vector = vector

                    # Reset simulation first
                    self.current_simulation.reset()

                    # Create and set matrix-based strategy after reset
                    matrix_strategy = MatrixBasedAssignment(
                        self.current_simulation.network
                    )
                    matrix_strategy.set_assignment_matrix(self._assignment_vector)
                    self.current_simulation.assignment_strategy = matrix_strategy

                    # Update UI
                    self.update_ui_parameters()

                    # Notify parent of reset
                    self.parent.on_simulation_reset()
                else:
                    QtWidgets.QMessageBox.warning(
                        self.parent,
                        "Invalid Input",
                        f"Please enter exactly {n_users} integers between 0 and {n_nodes-1}.",
                    )
                    # Revert to default strategy
                    self.strategy_combos["assignment"].setCurrentText("TimeGreedy")
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self.parent,
                    "Invalid Input",
                    "Please enter valid comma-separated integers.",
                )
                # Revert to default strategy
                self.strategy_combos["assignment"].setCurrentText("TimeGreedy")

    def _setup_ui_layout(self):
        """Setup the layout of UI components"""
        # Create main layout
        layout = QtWidgets.QVBoxLayout()

        # Add control buttons in two rows
        button_layout = QtWidgets.QVBoxLayout()

        # First row: New, Run/Pause and Reset
        top_buttons = QtWidgets.QHBoxLayout()
        new_btn = QtWidgets.QPushButton("New Simulation")
        new_btn.clicked.connect(self.create_new_simulation)
        top_buttons.addWidget(new_btn)
        top_buttons.addWidget(self.run_pause_btn)
        top_buttons.addWidget(self.reset_btn)
        button_layout.addLayout(top_buttons)

        # Second row: Delete and Apply
        bottom_buttons = QtWidgets.QHBoxLayout()
        delete_btn = QtWidgets.QPushButton("Delete Simulation")
        delete_btn.clicked.connect(self.delete_current_simulation)
        self.apply_btn = QtWidgets.QPushButton("Apply Changes")
        self.apply_btn.clicked.connect(self.apply_changes)
        bottom_buttons.addWidget(delete_btn)
        bottom_buttons.addWidget(self.apply_btn)
        button_layout.addLayout(bottom_buttons)

        layout.addLayout(button_layout)

        # Add node count controls
        node_group = QtWidgets.QGroupBox("Node Counts")
        node_layout = QtWidgets.QFormLayout()
        node_layout.addRow("Base Stations:", self.node_inputs["bs"])
        node_layout.addRow("HAPS:", self.node_inputs["haps"])
        node_layout.addRow("Users:", self.node_inputs["users"])
        node_group.setLayout(node_layout)
        layout.addWidget(node_group)

        # Add time controls
        time_group = QtWidgets.QGroupBox("Time Controls")
        time_layout = QtWidgets.QFormLayout()
        time_layout.addRow("Step Duration (s):", self.time_inputs["step_duration"])
        time_layout.addRow("Max Simulation Time (s):", self.time_inputs["max_time"])
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # Add strategy controls
        strategy_group = QtWidgets.QGroupBox("Strategies")
        strategy_layout = QtWidgets.QFormLayout()
        strategy_layout.addRow(
            "Assignment Strategy:", self.strategy_combos["assignment"]
        )
        strategy_layout.addRow("Power Strategy:", self.strategy_combos["power"])
        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)

        # Create a widget to hold the layout
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(layout)

    def delete_current_simulation(self):
        """Delete the currently selected simulation"""
        if not self.sim_list.currentItem():
            return

        simulation_name = self.sim_list.currentItem().text()
        reply = QtWidgets.QMessageBox.question(
            self.parent,
            "Delete Simulation",
            f"Are you sure you want to delete {simulation_name}?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            # Remove from simulations dict
            del self.simulations[simulation_name]

            # Remove from list widget
            self.sim_list.takeItem(self.sim_list.row(self.sim_list.currentItem()))

            # Clear current simulation if it was deleted
            if (
                self.current_simulation
                and simulation_name == self.sim_list.currentItem().text()
            ):
                self.current_simulation = None

            # Update UI
            self.parent.on_simulation_selected()

    def apply_changes(self):
        """Apply parameter changes to current simulation"""
        if not self.current_simulation:
            return

        # Store current values
        config = SimulationConfig(
            time_step=self.time_inputs[
                "step_duration"
            ].value(),  # Use step duration directly
            max_time=self.time_inputs["max_time"].value(),
            power_strategy=self.strategy_combos["power"].currentText(),
            assignment_strategy=self.strategy_combos["assignment"].currentText(),
            user_count=self.node_inputs["users"].value(),
            debug=self.current_simulation.debug,  # Preserve debug setting
            save_results=self.current_simulation.save_results,  # Preserve save setting
            print_output=self.current_simulation.print_output,  # Preserve print setting
            optimizer=self.current_simulation.optimizer,  # Preserve optimizer setting
        )

        # Create new simulation with current config
        new_simulation = Simulation(config)
        new_simulation.enable_stats_tracking()

        # Set node counts
        new_simulation.set_nodes(BaseStation, self.node_inputs["bs"].value())
        new_simulation.set_nodes(HAPS, self.node_inputs["haps"].value())
        new_simulation.set_nodes(UserDevice, self.node_inputs["users"].value())

        # Replace current simulation
        simulation_name = self.sim_list.currentItem().text()
        self.simulations[simulation_name] = new_simulation
        self.current_simulation = new_simulation

        # Stop any running simulation
        if self.simulation_timer.isActive():
            self.simulation_timer.stop()
            self.run_pause_btn.setText("Run")

        # Update UI without resetting parameters
        self.update_ui_parameters_preserve()
        self.parent.on_simulation_reset()

        QtWidgets.QMessageBox.information(
            self.parent,
            "Changes Applied",
            "Simulation parameters have been updated.",
        )

    def update_ui_parameters_preserve(self):
        """Update UI controls while preserving current parameter values"""
        if self.current_simulation:
            # Only update what needs to be synchronized
            self.time_inputs["simulation_speed"].blockSignals(True)
            self.time_inputs["simulation_speed"].setValue(
                1.0 / self.current_simulation.time_step
            )
            self.time_inputs["simulation_speed"].blockSignals(False)

            # Update strategy combos if needed
            if hasattr(self.current_simulation, "power_strategy"):
                self.strategy_combos["power"].setCurrentText(
                    self.current_simulation.config.power_strategy
                )

            if self.current_simulation.optimizer:
                self.strategy_combos["assignment"].setCurrentText(
                    self.current_simulation.optimizer
                )
            elif hasattr(self.current_simulation.assignment_strategy, "__class__"):
                strategy_name = (
                    self.current_simulation.assignment_strategy.__class__.__name__
                )
                self.strategy_combos["assignment"].setCurrentText(strategy_name)

    @property
    def num_bs_input(self):
        """Get base station count input"""
        return self.node_inputs["bs"]

    @property
    def num_haps_input(self):
        """Get HAPS count input"""
        return self.node_inputs["haps"]

    @property
    def num_users_input(self):
        """Get user count input"""
        return self.node_inputs["users"]

    def _on_max_time_changed(self, value):
        """Handle max time changes"""
        if self.current_simulation:
            self.current_simulation.max_time = value
            # Reset if current time is beyond new max time
            if self.current_simulation.current_time >= value:
                self.reset_simulation()
