import random
from PySide6 import QtCore, QtGui
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from optimisation_ntn.ui.dialogs.enlarged_graph import EnlargedGraphDialog
from optimisation_ntn.ui.theme_manager import ThemeManager


class EnergyGraph:
    def __init__(self, title, max_time=300, parent=None):
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
        self.chart.addAxis(self.axis_x, QtCore.Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, QtCore.Qt.AlignLeft)

        if title == "Total Energy":
            self.series = QLineSeries()
            self.chart.addSeries(self.series)
            self.series.attachAxis(self.axis_x)
            self.series.attachAxis(self.axis_y)
        else:
            self.series = {}

        # Create chart view
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Enable mouse tracking and connect double-click event
        self.chart_view.setMouseTracking(True)
        self.chart_view.mouseDoubleClickEvent = self.show_enlarged_graph

        # Track current step
        self.current_step = 0

    def show_enlarged_graph(self, event):
        """Show the enlarged version of the graph"""
        if self.parent:
            dialog = EnlargedGraphDialog(self.chart_view, self.parent)
            dialog.exec()

    def add_point(self, x, y):
        """Add a point to the total energy series"""
        if hasattr(self, "series") and isinstance(self.series, QLineSeries):
            self.current_step += 1
            self.series.append(self.current_step, y)

            # Adjust x-axis range more fluidly
            if self.current_step >= self.axis_x.max():
                new_max = self.current_step + int(
                    self.current_step * 0.05
                )  # Increase by 50 steps
                self.axis_x.setRange(0, new_max)

            self.update_y_axis_range()

    def add_node_point(self, node_text, x, y):
        """Add a point to a node's energy series"""
        if node_text not in self.series:
            series = QLineSeries()
            series.setName(node_text)
            self.chart.addSeries(series)
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)
            self.series[node_text] = series
            self.series[node_text].current_step = 0

            # Assign a random color
            color = QtGui.QColor(
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255),
            )
            series.setColor(color)

        self.series[node_text].current_step += 1
        self.series[node_text].append(self.series[node_text].current_step, y)

        # Adjust x-axis range more fluidly
        if self.series[node_text].current_step >= self.axis_x.max():
            new_max = self.series[node_text].current_step + int(
                self.series[node_text].current_step * 0.05
            )  # Increase by 50 steps
            self.axis_x.setRange(0, new_max)

        self.update_y_axis_range()
        self.chart.legend().setVisible(len(self.series) > 1)

    def remove_node_series(self, node_text):
        """Remove a node's energy series"""
        if node_text in self.series:
            series = self.series[node_text]
            self.chart.removeSeries(series)
            del self.series[node_text]
            self.update_y_axis_range()
            self.chart.legend().setVisible(len(self.series) > 1)

    def update_y_axis_range(self):
        """Update the y-axis range based on the maximum value"""
        max_energy = 0
        if isinstance(self.series, dict):
            for series in self.series.values():
                for i in range(series.count()):
                    max_energy = max(max_energy, series.at(i).y())
        else:
            for i in range(self.series.count()):
                max_energy = max(max_energy, self.series.at(i).y())

        if max_energy > 0:
            self.axis_y.setRange(0, max_energy * 1.2)

    def clear(self):
        """Clear all data from the graph"""
        if isinstance(self.series, dict):
            for series in list(self.series.values()):
                self.chart.removeSeries(series)
            self.series.clear()
        else:
            self.series.clear()
        self.axis_y.setRange(0, 100)  # Reset to default range
        self.axis_x.setRange(0, 100)  # Reset x-axis range
        self.current_step = 0  # Reset step counter
