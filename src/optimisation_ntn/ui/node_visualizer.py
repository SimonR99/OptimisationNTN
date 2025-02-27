""" Node visualizer class """

import math

from PySide6 import QtGui, QtWidgets

from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.user_device import UserDevice


class NodeVisualizer:
    """Node visualizer class"""

    @staticmethod
    def add_processing_requests(scene, node, node_x, node_y):
        """Add visual representation of requests being processed by a node"""
        if not (hasattr(node, "processing_queue") and node.processing_queue):
            return

        request_pixmap = QtGui.QPixmap("images/file.png")
        if request_pixmap.isNull():
            print("ERROR: Could not load file.png for processing requests")
            return

        request_pixmap = request_pixmap.scaled(15, 15)
        NodeVisualizer._draw_requests_semicircle(
            scene, node.processing_queue, node_x, node_y, request_pixmap
        )

    @staticmethod
    def _draw_requests_semicircle(
        scene, processing_queue, node_x, node_y, request_pixmap
    ):
        """Helper method to draw requests in a semicircle above the node"""
        num_requests = len(processing_queue)
        radius = 25
        start_angle = -140
        angle_span = 100

        for i, request in enumerate(processing_queue):
            # Calculate position on semicircle
            angle = math.radians(
                start_angle
                + (angle_span * i / (num_requests - 1 if num_requests > 1 else 1))
            )
            x = node_x + radius * math.cos(angle)
            y = node_y + radius * math.sin(angle)

            # Add request icon and label
            NodeVisualizer._add_request_icon_and_label(
                scene, request, x, y, request_pixmap
            )

    @staticmethod
    def _add_request_icon_and_label(scene, request, x, y, request_pixmap):
        """Helper method to add a request icon and its label"""
        request_item = QtWidgets.QGraphicsPixmapItem(request_pixmap)
        request_item.setPos(
            x - request_pixmap.width() / 2, y - request_pixmap.height() / 2
        )
        scene.addItem(request_item)

        text = scene.addText(f"R{request.id}")
        text.setDefaultTextColor(QtGui.QColor("white"))
        text.setPos(
            x - text.boundingRect().width() / 2,
            y - request_pixmap.height() - 15,
        )

    @staticmethod
    def add_in_transit_requests(scene, link, source_pos, target_pos):
        """Add visual representation of requests in transit on a link"""
        if link.transmission_queue:
            request_pixmap = QtGui.QPixmap("images/file.png")
            if request_pixmap.isNull():
                print("ERROR: Could not load file.png for in-transit requests")
                return

            request_pixmap = request_pixmap.scaled(15, 15)

            for i, request in enumerate(link.transmission_queue):
                # Calculate position along the link
                if i == 0:  # First request - show actual progress
                    progress = min(1.0, max(0.0, link.request_progress / request.size))
                else:  # Queue other requests behind the first one
                    progress = max(0.0, (i * -0.1))  # Space them out behind the source

                # Calculate position along the line
                x = source_pos[0] + (target_pos[0] - source_pos[0]) * progress
                y = source_pos[1] + (target_pos[1] - source_pos[1]) * progress

                # Add request icon
                request_item = QtWidgets.QGraphicsPixmapItem(request_pixmap)
                request_item.setPos(
                    x - request_pixmap.width() / 2, y - request_pixmap.height() / 2
                )
                scene.addItem(request_item)

                # Add request ID label
                text = scene.addText(f"R{request.id}")
                text.setDefaultTextColor(QtGui.QColor("white"))
                text.setPos(
                    x - text.boundingRect().width() / 2,
                    y - request_pixmap.height() - 15,
                )

    @staticmethod
    def get_node_positions(node, pixmap_width, pixmap_height):
        """Calculate node positions based on node type"""
        x_pos = node.position.x * 50
        if isinstance(node, BaseStation):
            y_pos = 250
        elif isinstance(node, HAPS):
            y_pos = 100
        elif isinstance(node, UserDevice):
            y_pos = 270
        else:
            y_pos = 0

        return (x_pos + pixmap_width / 2, y_pos + pixmap_height / 2)
