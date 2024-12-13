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

        # Set initial size to 80% of screen size
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))

        # Create layout
        layout = QtWidgets.QVBoxLayout()

        # Create a new chart with the same data
        original_chart = chart_view.chart()
        new_chart = QChart()
        new_chart.setTitle(original_chart.title())
        new_chart.setBackgroundBrush(original_chart.backgroundBrush())

        # Copy series data and preserve colors
        for original_series in original_chart.series():
            new_series = QLineSeries()
            new_series.setName(original_series.name())  # Copy series name
            for point in range(original_series.count()):
                new_series.append(original_series.at(point))
            new_chart.addSeries(new_series)
            new_series.setColor(original_series.color())  # Copy series color

            # Copy axes
            for axis in original_chart.axes():
                new_axis = QValueAxis()
                new_axis.setTitleText(axis.titleText())
                new_axis.setRange(axis.min(), axis.max())

                if axis.orientation() == Qt.Orientation.Horizontal:
                    new_chart.addAxis(new_axis, Qt.AlignmentFlag.AlignBottom)
                else:
                    new_chart.addAxis(new_axis, Qt.AlignmentFlag.AlignLeft)

                new_series.attachAxis(new_axis)

        # Create new chart view with zoom/pan support
        self.chart_view = QChartView(new_chart)
        self.chart_view.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.chart_view.setRubberBand(QChartView.RubberBand.RectangleRubberBand)

        # Add zoom controls
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

        # Add stats panel
        self.stats_table = QtWidgets.QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(
            ["Node", "Current Energy", "Peak Energy", "Average Energy"]
        )
        self.stats_table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.update_stats(original_chart)

        # Add widgets to layout
        layout.addWidget(self.chart_view)
        layout.addLayout(zoom_layout)
        layout.addWidget(self.stats_table)

        self.setLayout(layout)

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
