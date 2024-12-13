""" Node stats table """

from PySide6 import QtCore, QtWidgets


class NodeStatsTable(QtWidgets.QTableWidget):
    """Node stats table"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.checkbox_signal_connected = False
        self.setup_ui()

    def setup_ui(self):
        """Initialize the table structure"""
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(
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

        # Set column resize modes
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )

    def update_stats(self, nodes, on_checkbox_change):
        """Update the statistics table with current node data"""
        # Block signals during update
        self.blockSignals(True)

        # Store currently checked states and selection
        checked_nodes = set()
        current_selection = self.selectedItems()
        selected_rows = set(item.row() for item in current_selection)

        for row in range(self.rowCount()):
            checkbox_item = self.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == QtCore.Qt.Checked:
                node_item = self.item(row, 1)
                if node_item:
                    checked_nodes.add(node_item.text())

        # Update table contents
        if self.rowCount() != len(nodes):
            self.setRowCount(len(nodes))

        for row, node in enumerate(nodes):
            node_text = f"{type(node).__name__} {node.node_id}"

            # Update checkbox
            checkbox_item = self.item(row, 0)
            if not checkbox_item:
                checkbox_item = QtWidgets.QTableWidgetItem()
                checkbox_item.setFlags(
                    QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
                )
                self.setItem(row, 0, checkbox_item)

            checkbox_item.setCheckState(
                QtCore.Qt.Checked if node_text in checked_nodes else QtCore.Qt.Unchecked
            )

            # Update node name
            name_item = self.item(row, 1)
            if not name_item or name_item.text() != node_text:
                self.setItem(row, 1, QtWidgets.QTableWidgetItem(node_text))

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
                self._update_cell(row, 2, f"{current:.2f}")
                self._update_cell(row, 3, f"{peak:.2f}")
                self._update_cell(row, 4, f"{avg:.2f}")
                self._update_cell(row, 5, f"{cumulated:.2f}")
                self._update_cell(row, 6, remaining_str)
            else:
                # Fill with zeros if no history
                for col in range(2, 6):
                    self._update_cell(row, col, "0.00")
                # Set remaining battery
                if node.battery_capacity > 0:
                    self._update_cell(row, 6, f"{node.battery_capacity:.2f}")
                else:
                    self._update_cell(row, 6, "∞")

        # Restore selection
        for row in selected_rows:
            self.selectRow(row)

        # Unblock signals and ensure connection
        self.blockSignals(False)

        # Connect signal if not already connected
        if not self.checkbox_signal_connected:
            self.itemChanged.connect(on_checkbox_change)
            self.checkbox_signal_connected = True

    def _update_cell(self, row, col, value):
        """Helper method to update table cell only if value changed"""
        current_item = self.item(row, col)
        if not current_item or current_item.text() != value:
            self.setItem(row, col, QtWidgets.QTableWidgetItem(value))
