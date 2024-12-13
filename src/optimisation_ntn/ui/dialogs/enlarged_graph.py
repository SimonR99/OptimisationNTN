"""Enlarged graph dialog (popup)"""

from PySide6 import QtGui, QtWidgets
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt


class EnlargedGraphDialog(QtWidgets.QDialog):
    """Enlarged graph dialog"""

    def __init__(self, chart_view, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enlarged Graph View")
        self.setModal(True)
        self._setup_window_size()

        # Create layout
        layout = QtWidgets.QVBoxLayout()

        # Create and setup chart
        self.chart_view = self._create_chart_view(chart_view)

        # Create and add controls
        zoom_layout = self._create_zoom_controls()

        # Create stats table
        self.stats_table = self._create_stats_table()
        self.update_stats(chart_view.chart())

        # Add widgets to layout
        layout.addWidget(self.chart_view)
        layout.addLayout(zoom_layout)
        layout.addWidget(self.stats_table)

        self.setLayout(layout)

    def _setup_window_size(self):
        """Set initial window size to 80% of screen size"""
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))

    def _create_chart_view(self, original_chart_view):
        """Create a new chart view with copied data from original"""
        original_chart = original_chart_view.chart()
        new_chart = QChart()
        new_chart.setTitle(original_chart.title())
        new_chart.setBackgroundBrush(original_chart.backgroundBrush())

        self._copy_series_data(original_chart, new_chart)

        # Create new chart view with zoom/pan support
        chart_view = QChartView(new_chart)
        chart_view.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        chart_view.setRubberBand(QChartView.RubberBand.RectangleRubberBand)
        return chart_view

    def _copy_series_data(self, original_chart, new_chart):
        """Copy series data and axes from original chart to new chart"""
        for original_series in original_chart.series():
            new_series = QLineSeries()
            new_series.setName(original_series.name())
            for point in range(original_series.count()):
                new_series.append(original_series.at(point))
            new_chart.addSeries(new_series)
            new_series.setColor(original_series.color())

            self._copy_axes(original_chart, new_chart, new_series)

    def _copy_axes(self, original_chart, new_chart, new_series):
        """Copy axes from original chart to new chart"""
        for axis in original_chart.axes():
            new_axis = QValueAxis()
            new_axis.setTitleText(axis.titleText())
            new_axis.setRange(axis.min(), axis.max())

            alignment = (
                Qt.AlignmentFlag.AlignBottom
                if axis.orientation() == Qt.Orientation.Horizontal
                else Qt.AlignmentFlag.AlignLeft
            )
            new_chart.addAxis(new_axis, alignment)
            new_series.attachAxis(new_axis)

    def _create_zoom_controls(self):
        """Create zoom control buttons"""
        zoom_layout = QtWidgets.QHBoxLayout()

        zoom_in_btn = QtWidgets.QPushButton("Zoom In")
        zoom_in_btn.clicked.connect(lambda: self.zoom(1.2))
        zoom_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QtWidgets.QPushButton("Zoom Out")
        zoom_out_btn.clicked.connect(lambda: self.zoom(0.8))
        zoom_layout.addWidget(zoom_out_btn)

        reset_zoom_btn = QtWidgets.QPushButton("Reset View")
        reset_zoom_btn.clicked.connect(self.reset_view)
        zoom_layout.addWidget(reset_zoom_btn)

        return zoom_layout

    def _create_stats_table(self):
        """Create and setup statistics table"""
        stats_table = QtWidgets.QTableWidget()
        stats_table.setColumnCount(4)
        stats_table.setHorizontalHeaderLabels(
            ["Node", "Current Energy", "Peak Energy", "Average Energy"]
        )
        stats_table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        return stats_table

    def zoom(self, factor):
        """Zoom in or out"""
        self.chart_view.chart().zoom(factor)

    def reset_view(self):
        """Reset view"""
        self.chart_view.chart().zoomReset()

    def update_stats(self, original_chart):
        """Update statistics for each series"""
        self.stats_table.setRowCount(0)

        for series in original_chart.series():
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)

            # Node name
            self.stats_table.setItem(row, 0, QtWidgets.QTableWidgetItem(series.name()))

            # Calculate stats
            values = [series.at(i).y() for i in range(series.count())]
            if values:
                current = values[-1]
                peak = max(values)
                avg = sum(values) / len(values)

                # Current energy
                self.stats_table.setItem(
                    row, 1, QtWidgets.QTableWidgetItem(f"{current:.2f}")
                )

                # Peak energy
                self.stats_table.setItem(
                    row, 2, QtWidgets.QTableWidgetItem(f"{peak:.2f}")
                )

                # Average energy
                self.stats_table.setItem(
                    row, 3, QtWidgets.QTableWidgetItem(f"{avg:.2f}")
                )
