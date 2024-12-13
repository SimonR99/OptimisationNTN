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
        self.blockSignals(True)

        # Get current state
        checked_nodes = self._get_checked_nodes()
        selected_rows = self._get_selected_rows()

        # Update table size if needed
        if self.rowCount() != len(nodes):
            self.setRowCount(len(nodes))

        # Update each row
        for row, node in enumerate(nodes):
            self._update_row(row, node, checked_nodes)

        # Restore selection and signals
        self._restore_selection(selected_rows)
        self._ensure_checkbox_signal(on_checkbox_change)

    def _get_checked_nodes(self):
        """Get set of currently checked node names"""
        checked_nodes = set()
        for row in range(self.rowCount()):
            checkbox_item = self.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == QtCore.Qt.Checked:
                node_item = self.item(row, 1)
                if node_item:
                    checked_nodes.add(node_item.text())
        return checked_nodes

    def _get_selected_rows(self):
        """Get set of currently selected row indices"""
        return set(item.row() for item in self.selectedItems())

    def _update_row(self, row, node, checked_nodes):
        """Update a single row in the table"""
        node_text = f"{type(node).__name__} {node.node_id}"

        # Update checkbox
        self._update_checkbox(row, node_text, checked_nodes)

        # Update node name
        self._update_node_name(row, node_text)

        # Update statistics
        self._update_statistics(row, node)

    def _update_checkbox(self, row, node_text, checked_nodes):
        """Update checkbox state for a row"""
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

    def _update_node_name(self, row, node_text):
        """Update node name cell"""
        name_item = self.item(row, 1)
        if not name_item or name_item.text() != node_text:
            self.setItem(row, 1, QtWidgets.QTableWidgetItem(node_text))

    def _update_statistics(self, row, node):
        """Update statistics cells for a node"""
        if node.energy_history:
            self._update_energy_stats(row, node)
        else:
            self._update_empty_stats(row, node)

    def _update_energy_stats(self, row, node):
        """Update statistics when energy history exists"""
        current = node.energy_history[-1]
        peak = max(node.energy_history)
        avg = sum(node.energy_history) / len(node.energy_history)
        cumulated = node.energy_consumed

        # Update energy values
        self._update_cell(row, 2, f"{current:.2f}")
        self._update_cell(row, 3, f"{peak:.2f}")
        self._update_cell(row, 4, f"{avg:.2f}")
        self._update_cell(row, 5, f"{cumulated:.2f}")

        # Update battery
        remaining_str = (
            f"{node.battery_capacity - node.energy_consumed:.2f}"
            if node.battery_capacity > 0
            else "∞"
        )
        self._update_cell(row, 6, remaining_str)

    def _update_empty_stats(self, row, node):
        """Update statistics when no energy history exists"""
        for col in range(2, 6):
            self._update_cell(row, col, "0.00")

        # Set remaining battery
        battery_str = (
            f"{node.battery_capacity:.2f}" if node.battery_capacity > 0 else "∞"
        )
        self._update_cell(row, 6, battery_str)

    def _restore_selection(self, selected_rows):
        """Restore previously selected rows"""
        for row in selected_rows:
            self.selectRow(row)

    def _ensure_checkbox_signal(self, on_checkbox_change):
        """Ensure checkbox signal is connected and unblock signals"""
        self.blockSignals(False)
        if not self.checkbox_signal_connected:
            self.itemChanged.connect(on_checkbox_change)
            self.checkbox_signal_connected = True

    def _update_cell(self, row, col, value):
        """Helper method to update table cell only if value changed"""
        current_item = self.item(row, col)
        if not current_item or current_item.text() != value:
            self.setItem(row, col, QtWidgets.QTableWidgetItem(value))
