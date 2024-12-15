""" Energy graph class """

import random

from PySide6 import QtCore, QtGui
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis

from optimisation_ntn.ui.dialogs.enlarged_graph import EnlargedGraphDialog
from optimisation_ntn.ui.theme_manager import ThemeManager


class EnergyGraph:
    """Energy graph class"""

    def __init__(self, title, parent=None):
        self.parent = parent
        self.chart = QChart()
        self.chart.setTitle(title)

        # Set initial theme (dark by default)
        ThemeManager.apply_theme_to_chart(self.chart, True)

        # Create axes
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Steps")
        self.axis_x.setRange(0, 100)
        self.axis_x.setTickCount(11)
        self.axis_x.setLabelFormat("%d")

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText(
            "Energy (J)" if title == "Total Energy" else "Energy per tick (W)"
        )

        # Add axes to chart
        self.chart.addAxis(self.axis_x, QtCore.Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, QtCore.Qt.AlignmentFlag.AlignLeft)

        # Initialize series
        if title == "Total Energy":
            self.series = QLineSeries()
            self.chart.addSeries(self.series)
            self.series.attachAxis(self.axis_x)
            self.series.attachAxis(self.axis_y)
            self.point_count = 0  # Track points for total energy
        else:
            self.node_series = {}  # Dictionary to store node series

        # Create chart view
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Enable mouse tracking and connect double-click event
        self.chart_view.setMouseTracking(True)
        self.chart_view.mouseDoubleClickEvent = self.show_enlarged_graph

        # Track current step
        self.current_step = 0

        self.max_points = 1000  # Maximum number of points to display
        self.decimation_factor = 1  # Will be adjusted based on data size

    def show_enlarged_graph(self, event):
        """Show the enlarged version of the graph"""
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            return

        if self.parent:
            dialog = EnlargedGraphDialog(self.chart_view, self.parent)
            dialog.exec()

    def decimate_data(self, series):
        """Reduce number of points in a series if it exceeds max_points"""
        point_count = series.count()
        if point_count > self.max_points:
            self.decimation_factor = (
                point_count + self.max_points - 1
            ) // self.max_points

            # Create new decimated series
            decimated_series = QLineSeries()
            decimated_series.setName(series.name())

            # Keep first and last points, decimate points in between
            decimated_series.append(series.at(0).x(), series.at(0).y())
            for i in range(1, point_count - 1, self.decimation_factor):
                point = series.at(i)
                decimated_series.append(point.x(), point.y())
            decimated_series.append(
                series.at(point_count - 1).x(), series.at(point_count - 1).y()
            )

            return decimated_series
        return series

    def add_point(self, value):
        """Add a point to the total energy series"""
        if not hasattr(self, "series"):
            return

        self.series.append(self.point_count, value)
        self.point_count += 1

        # Apply decimation if needed
        if self.series.count() > self.max_points:
            decimated = self.decimate_data(self.series)
            self.chart.removeSeries(self.series)
            self.series = decimated
            self.chart.addSeries(self.series)
            self.series.attachAxis(self.axis_x)
            self.series.attachAxis(self.axis_y)

        # Update axis ranges
        if self.point_count >= self.axis_x.max():
            new_max = self.point_count + int(self.point_count * 0.1)
            self.axis_x.setRange(0, new_max)
        self.update_y_axis_range()

    def add_node_point(self, node_name, value):
        """Add a point to a node's energy series"""
        if not hasattr(self, "node_series"):
            return

        if node_name not in self.node_series:
            series = QLineSeries()
            series.setName(node_name)
            # Assign a random color
            color = QtGui.QColor(
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255),
            )
            series.setColor(color)
            self.node_series[node_name] = series
            self.chart.addSeries(series)
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)

        series = self.node_series[node_name]
        current_count = series.count()
        series.append(current_count, value)

        # Apply decimation if needed
        if series.count() > self.max_points:
            decimated = self.decimate_data(series)
            self.chart.removeSeries(series)
            self.node_series[node_name] = decimated
            self.chart.addSeries(decimated)
            decimated.attachAxis(self.axis_x)
            decimated.attachAxis(self.axis_y)

        # Update axis ranges
        if current_count >= self.axis_x.max():
            new_max = current_count + int(current_count * 0.1)
            self.axis_x.setRange(0, new_max)
        self.update_y_axis_range()
        self.chart.legend().setVisible(len(self.node_series) > 1)

    def remove_node_series(self, node_text):
        """Remove a node's energy series"""
        if hasattr(self, "node_series") and node_text in self.node_series:
            series = self.node_series[node_text]
            self.chart.removeSeries(series)
            del self.node_series[node_text]
            self.update_y_axis_range()
            self.chart.legend().setVisible(len(self.node_series) > 1)

    def update_y_axis_range(self):
        """Update the y-axis range based on the maximum value"""
        max_energy = 0
        if hasattr(self, "node_series"):
            for series in self.node_series.values():
                for i in range(series.count()):
                    max_energy = max(max_energy, series.at(i).y())
        elif hasattr(self, "series"):
            for i in range(self.series.count()):
                max_energy = max(max_energy, self.series.at(i).y())

        if max_energy > 0:
            self.axis_y.setRange(0, max_energy * 1.2)

    def clear(self):
        """Clear all data from the graph"""
        if hasattr(self, "node_series"):
            for series in list(self.node_series.values()):
                self.chart.removeSeries(series)
            self.node_series.clear()
        elif hasattr(self, "series"):
            self.series.clear()
            self.point_count = 0

        self.axis_y.setRange(0, 100)  # Reset to default range
        self.axis_x.setRange(0, 100)  # Reset x-axis range
        self.current_step = 0  # Reset step counter
