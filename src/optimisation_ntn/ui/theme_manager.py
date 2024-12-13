""" Theme manager """

from PySide6 import QtGui


class ThemeManager:
    """Theme manager"""

    DARK_THEME = {
        "app_background": "#2e2e2e",
        "text": "white",
        "chart_background": "#2e2e2e",
        "grid_lines": "#444444",
        "button_background": "#3e3e3e",
        "button_text": "white",
        "border": "#555555",
        "spinbox_arrow": "#cccccc",
        "spinbox_background": "#3e3e3e",
        "tab_background": "#2e2e2e",
        "input_background": "#3e3e3e",
        "sky_color": "#1e1e1e",
        "selection_background": "#505050",
        "selection_text": "white",
        "graphics_view_background": "#1e1e1e",
        "chart_border": "#3e3e3e",
    }

    LIGHT_THEME = {
        "app_background": "#f0f0f0",
        "text": "black",
        "chart_background": "white",
        "grid_lines": "#e0e0e0",
        "button_background": "#e0e0e0",
        "button_text": "black",
        "border": "#cccccc",
        "spinbox_arrow": "#333333",
        "spinbox_background": "#ffffff",
        "tab_background": "#f0f0f0",
        "input_background": "white",
        "sky_color": "#87CEEB",
        "selection_background": "#0078d7",
        "selection_text": "white",
        "graphics_view_background": "white",
        "chart_border": "#cccccc",
    }

    @staticmethod
    def get_theme_stylesheet(is_dark):
        """Get the stylesheet for the current theme"""
        theme = ThemeManager.DARK_THEME if is_dark else ThemeManager.LIGHT_THEME
        return f"""
            QMainWindow, QDialog {{
                background-color: {theme['app_background']};
                color: {theme['text']};
            }}
            QGroupBox {{
                background-color: {theme['app_background']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 5px;
                margin-top: 1em;
                padding-top: 0.5em;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                background-color: {theme['app_background']};
            }}
            QPushButton {{
                background-color: {theme['button_background']};
                color: {theme['button_text']};
                border: 1px solid {theme['border']};
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {theme['text']};
                color: {theme['app_background']};
            }}
            QTableWidget {{
                background-color: {theme['app_background']};
                color: {theme['text']};
                gridline-color: {theme['grid_lines']};
                border: 1px solid {theme['border']};
            }}
            QHeaderView::section {{
                background-color: {theme['button_background']};
                color: {theme['button_text']};
                border: 1px solid {theme['border']};
            }}
            QLabel {{
                color: {theme['text']};
            }}
            QCheckBox {{
                color: {theme['text']};
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: {theme['input_background']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 3px;
                padding: 2px;
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                background-color: {theme['button_background']};
                border: 1px solid {theme['border']};
                border-radius: 2px;
                margin: 1px;
                min-width: 15px;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                background-color: {theme['button_background']};
                border: 1px solid {theme['border']};
                border-radius: 2px;
                margin: 1px;
                min-width: 15px;
            }}
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
                image: none;
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 4px solid {theme['spinbox_arrow']};
            }}
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
                image: none;
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {theme['spinbox_arrow']};
            }}
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: {theme['text']};
            }}
            QSpinBox::up-button:hover::up-arrow, QDoubleSpinBox::up-button:hover::up-arrow {{
                border-bottom-color: {theme['app_background']};
            }}
            QSpinBox::down-button:hover::down-arrow, QDoubleSpinBox::down-button:hover::down-arrow {{
                border-top-color: {theme['app_background']};
            }}
            QListWidget {{
                background-color: {theme['input_background']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {theme['selection_background']};
                color: {theme['selection_text']};
            }}
            QTabWidget::pane {{
                border: 1px solid {theme['border']};
                background-color: {theme['tab_background']};
            }}
            QTabBar::tab {{
                background-color: {theme['button_background']};
                color: {theme['button_text']};
                border: 1px solid {theme['border']};
                padding: 5px 10px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme['selection_background']};
                color: {theme['selection_text']};
            }}
            QTabBar::tab:hover {{
                background-color: {theme['selection_background']};
                color: {theme['selection_text']};
            }}
            QGraphicsView {{
                background-color: {theme['graphics_view_background']};
                border: 1px solid {theme['border']};
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: {theme['app_background']};
                width: 10px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme['button_background']};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme['selection_background']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
                background: none;
            }}
            QScrollBar:horizontal {{
                border: none;
                background-color: {theme['app_background']};
                height: 10px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {theme['button_background']};
                border-radius: 5px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {theme['selection_background']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
                background: none;
            }}
            QLineEdit {{
                background-color: {theme['input_background']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 3px;
                padding: 2px;
            }}
        """

    @staticmethod
    def apply_theme_to_chart(chart, is_dark):
        """Apply theme to a QChart"""
        theme = ThemeManager.DARK_THEME if is_dark else ThemeManager.LIGHT_THEME
        chart.setBackgroundBrush(QtGui.QColor(theme["chart_background"]))
        chart.setTitleBrush(QtGui.QColor(theme["text"]))

        # Set chart border
        pen = QtGui.QPen(QtGui.QColor(theme["chart_border"]))
        pen.setWidth(1)
        chart.setBackgroundPen(pen)

        # Update axes colors
        for axis in chart.axes():
            axis.setLabelsBrush(QtGui.QColor(theme["text"]))
            axis.setTitleBrush(QtGui.QColor(theme["text"]))
            pen = axis.linePen()
            pen.setColor(QtGui.QColor(theme["text"]))
            axis.setLinePen(pen)

            # Update grid lines
            pen = axis.gridLinePen()
            pen.setColor(QtGui.QColor(theme["grid_lines"]))
            axis.setGridLinePen(pen)
