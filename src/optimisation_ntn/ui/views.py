""" Close up view and far view panel """

import math

from PySide6 import QtCore, QtGui, QtWidgets

from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.leo import LEO
from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.ui.node_visualizer import NodeVisualizer
from optimisation_ntn.ui.theme_manager import ThemeManager


class CloseUpView:
    """Close up view"""

    @staticmethod
    def load(view, simulation, show_links=True, is_dark_theme=True):
        """Load the close-up view of the network"""
        scene = QtWidgets.QGraphicsScene(-200, 0, 400, 400)
        if not simulation:
            view.setScene(scene)
            return

        # Add green floor
        scene.addRect(
            -800,
            270,
            1600,
            200,
            QtGui.QPen(QtGui.QColor("darkgreen")),
            QtGui.QBrush(QtGui.QColor("darkgreen")),
        )

        # Add sky
        sky_color = "#1e1e1e" if is_dark_theme else "#87CEEB"  # Dark blue or light blue
        scene.addRect(
            -800,
            0,
            1600,
            270,
            QtGui.QPen(QtGui.QColor(sky_color)),
            QtGui.QBrush(QtGui.QColor(sky_color)),
        )

        # Load node images
        haps_pixmap = QtGui.QPixmap("images/haps.png").scaled(30, 30)
        bs_pixmap = QtGui.QPixmap("images/base_station.png").scaled(30, 30)
        user_pixmap = QtGui.QPixmap("images/person.png").scaled(20, 20)
        leo_pixmap = QtGui.QPixmap("images/leo.png").scaled(30, 30)

        node_positions = {}

        # Add nodes to the scene
        for node in simulation.network.nodes:
            if isinstance(node, HAPS):
                CloseUpView._add_haps(scene, node, haps_pixmap, node_positions)
            elif isinstance(node, BaseStation):
                CloseUpView._add_base_station(scene, node, bs_pixmap, node_positions)
            elif isinstance(node, UserDevice):
                CloseUpView._add_user(scene, node, user_pixmap, node_positions)
            elif isinstance(node, LEO) and node.is_visible:
                CloseUpView._add_leo(scene, node, leo_pixmap, node_positions)

        # Draw communication links if enabled
        if show_links:
            CloseUpView._draw_links(scene, simulation, node_positions)

        view.setScene(scene)
        view.centerOn(0, 200)

    def reset(self, view):
        """Reset the close-up view"""
        view.setScene(None)

    @staticmethod
    def _add_haps(scene, node, pixmap, node_positions):
        x_pos = node.position.x * 50
        y_pos = 100
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        item.setPos(x_pos, y_pos)

        if not node.state:
            item.setOpacity(0.2)

        scene.addItem(item)
        node_positions[node] = (x_pos + pixmap.width() / 2, y_pos + pixmap.height() / 2)

        text = scene.addText(f"HAPS {node.node_id}")
        text.setDefaultTextColor(QtGui.QColor("white"))
        text.setPos(
            x_pos + pixmap.width() / 2 - text.boundingRect().width() / 2,
            y_pos - 20,
        )

    @staticmethod
    def _add_base_station(scene, node, pixmap, node_positions):
        x_pos = node.position.x * 50
        y_pos = 250
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        item.setPos(x_pos, y_pos)

        if not node.state:
            item.setOpacity(0.2)

        scene.addItem(item)
        node_positions[node] = (x_pos + pixmap.width() / 2, y_pos + pixmap.height() / 2)

        text = scene.addText(f"BS {node.node_id}")
        text.setDefaultTextColor(QtGui.QColor("white"))
        text.setPos(
            x_pos + pixmap.width() / 2 - text.boundingRect().width() / 2,
            y_pos + pixmap.height() + 5,
        )

    @staticmethod
    def _add_user(scene, node, pixmap, node_positions):
        x_pos = node.position.x * 50
        y_pos = 270
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        item.setPos(x_pos, y_pos)
        scene.addItem(item)
        node_positions[node] = (x_pos + pixmap.width() / 2, y_pos + pixmap.height() / 2)

    @staticmethod
    def _add_leo(scene, node, pixmap, node_positions):
        view_width = 400
        angle_range = abs(LEO.initial_angle - LEO.final_angle)
        x_pos = (
            (node.current_angle - LEO.initial_angle) / angle_range
        ) * view_width - view_width / 2
        y_pos = 50

        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        item.setPos(x_pos, y_pos)

        if not node.state:
            item.setOpacity(0.2)

        scene.addItem(item)
        node_positions[node] = (x_pos + pixmap.width() / 2, y_pos + pixmap.height() / 2)

        text = scene.addText(f"LEO {node.node_id}\nAngle: {node.current_angle:.1f}°")
        text.setDefaultTextColor(QtGui.QColor("white"))
        text.setPos(x_pos, y_pos - 40)

    @staticmethod
    def _draw_links(scene, simulation, node_positions):
        for link in simulation.network.communication_links:
            source_pos = node_positions.get(link.node_a)
            target_pos = node_positions.get(link.node_b)

            if source_pos and target_pos:
                color = CloseUpView._get_link_color(link.node_a, link.node_b)
                pen = QtGui.QPen(QtGui.QColor(color))
                pen.setStyle(QtCore.Qt.SolidLine)
                pen.setWidth(1)

                line = scene.addLine(
                    source_pos[0],
                    source_pos[1],
                    target_pos[0],
                    target_pos[1],
                    pen,
                )
                line.setOpacity(0.5)

                NodeVisualizer.add_in_transit_requests(
                    scene, link, source_pos, target_pos
                )

    @staticmethod
    def _get_link_color(source, target):
        if isinstance(source, LEO) or isinstance(target, LEO):
            return "cyan"
        if isinstance(source, BaseStation) or isinstance(target, BaseStation):
            return "yellow"
        if isinstance(source, HAPS) or isinstance(target, HAPS):
            return "orange"
        return "white"


class FarView:
    """Far view (Orbit view)"""

    @staticmethod
    def load(view, simulation, is_dark_theme=True):
        """Load the far view of the network"""
        view_width = view.width()
        view_height = view.height()

        scene = QtWidgets.QGraphicsScene(
            -view_width / 2, -view_height / 2, view_width, view_height
        )

        theme = ThemeManager.DARK_THEME if is_dark_theme else ThemeManager.LIGHT_THEME

        # Add background
        scene.addRect(
            -view_width / 2,
            -view_height / 2,
            view_width,
            view_height,
            QtGui.QPen(QtGui.QColor(theme["app_background"])),
            QtGui.QBrush(QtGui.QColor(theme["app_background"])),
        )

        # Calculate radii
        earth_radius = min(view_width, view_height) * 0.3
        haps_radius = earth_radius + 3
        leo_radius = earth_radius + 75

        # Add Earth
        scene.addEllipse(
            -earth_radius,
            -earth_radius,
            2 * earth_radius,
            2 * earth_radius,
            QtGui.QPen(QtGui.QColor("blue")),
            QtGui.QBrush(QtGui.QColor("green")),
        )

        # Add orbit circles
        for radius in [haps_radius, leo_radius]:
            scene.addEllipse(
                -radius,
                -radius,
                2 * radius,
                2 * radius,
                QtGui.QPen(QtGui.QColor("gray"), 1, QtCore.Qt.PenStyle.DashLine),
            )

        if simulation:
            FarView._add_nodes(scene, simulation.network.nodes, leo_radius, haps_radius)

        view.setScene(scene)
        view.fitInView(scene.sceneRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    @staticmethod
    def reset(view):
        """Reset the far view"""
        view.setScene(None)

    @staticmethod
    def _add_nodes(scene, nodes, leo_radius, haps_radius):
        """Add nodes with images to the far view"""
        # Load node images
        leo_pixmap = QtGui.QPixmap("images/leo.png").scaled(20, 20)
        haps_pixmap = QtGui.QPixmap("images/haps.png").scaled(20, 20)

        for node in nodes:
            if isinstance(node, LEO):
                FarView._add_leo(scene, node, leo_radius, leo_pixmap)
            elif isinstance(node, HAPS):
                FarView._add_haps(scene, node, haps_radius, haps_pixmap)

    @staticmethod
    def _add_leo(scene, node, radius, pixmap):
        """Add LEO satellite with image"""
        angle_rad = math.radians(node.current_angle)
        x = radius * math.cos(angle_rad)
        y = -radius * math.sin(angle_rad)

        # Add LEO image
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        # Center the image on the calculated position
        item.setPos(x - pixmap.width() / 2, y - pixmap.height() / 2)

        if not node.state:
            item.setOpacity(0.2)

        scene.addItem(item)

        # Add text label
        text = scene.addText(f"LEO {node.node_id}")
        text.setDefaultTextColor(QtGui.QColor("white"))
        text.setPos(x + pixmap.width(), y)

    @staticmethod
    def _add_haps(scene, node, radius, pixmap):
        """Add HAPS with image"""
        # Calculate position based on node's x position
        angle_rad = math.radians(node.position.x * 30)  # Scale x position to angle
        x = radius * math.cos(angle_rad)
        y = -radius * math.sin(angle_rad)

        # Add HAPS image
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        # Center the image on the calculated position
        item.setPos(x - pixmap.width() / 2, y - pixmap.height() / 2)

        if not node.state:
            item.setOpacity(0.2)

        scene.addItem(item)

        # Add text label
        text = scene.addText(f"HAPS {node.node_id}")
        text.setDefaultTextColor(QtGui.QColor("white"))
        text.setPos(x + pixmap.width(), y)
