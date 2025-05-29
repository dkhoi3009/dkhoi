# modules/pad_item.py

import json
import traceback
from PyQt5.QtWidgets import QGraphicsItem, QMessageBox, QGraphicsTextItem
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtCore import QRectF, Qt, QPointF


class Pad(QGraphicsItem):
    def __init__(self, pad_data, parent=None):
        super().__init__(parent)
        self.pad_data = json.loads(json.dumps(pad_data))  # deep copy to avoid reference issues

        # Set default values for any missing data
        if 'width' not in self.pad_data or not isinstance(self.pad_data['width'], (int, float)):
            self.pad_data['width'] = 1.5
        if 'height' not in self.pad_data or not isinstance(self.pad_data['height'], (int, float)):
            self.pad_data['height'] = 1.5
        if 'hole_diameter' not in self.pad_data or not isinstance(self.pad_data['hole_diameter'], (int, float)):
            self.pad_data['hole_diameter'] = 0.8
        if 'corner_radius' not in self.pad_data or not isinstance(self.pad_data['corner_radius'], (int, float)):
            self.pad_data['corner_radius'] = 0
        if 'id' not in self.pad_data:
            self.pad_data['id'] = '1'

        # Ensure layers and thermal data exists
        if 'layers' not in self.pad_data:
            self.pad_data['layers'] = {
                'top_copper': True, 'bottom_copper': False,
                'top_mask': True, 'bottom_mask': False,
                'top_paste': True, 'bottom_paste': False
            }
        if 'thermal' not in self.pad_data:
            self.pad_data['thermal'] = {'enabled': True, 'spoke_width': 0.3, 'gap_width': 0.2}

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        self.resize_handles = []
        self.current_handle = None
        self.is_resizing = False

        # Layer-specific colors
        self.layer_colors = {
            'top_copper': QColor(0, 100, 255, 180),  # Blue
            'bottom_copper': QColor(0, 180, 0, 180),  # Green
            'top_mask': QColor(255, 255, 255, 200),  # White
            'bottom_mask': QColor(180, 180, 180, 180),  # Gray
            'top_paste': QColor(255, 200, 0, 180),  # Yellow
            'bottom_paste': QColor(255, 100, 0, 200),  # Orange
        }

        # Store layer visibility state
        self.layer_visibility = {layer: True for layer in self.pad_data['layers'].keys()}

        # Create text item for ID
        self.id_text = QGraphicsTextItem(self)
        self.update_id_text()

    def show_error_message(self, title, message):
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle(title)
        error_dialog.setText(message)
        tb_str = traceback.format_exc()
        if tb_str != "NoneType: None\n":
            error_dialog.setDetailedText(tb_str)
        print(f"{title}: {message}\n{tb_str}")
        error_dialog.exec_()

    def boundingRect(self):
        # Get the basic pad bounds
        width = float(self.pad_data['width']) * 100
        height = float(self.pad_data['height']) * 100

        # Add some padding for the ID text
        text_bounds = self.id_text.boundingRect()
        pad_bounds = QRectF(-width / 2, -height / 2, width, height)

        # Return a rectangle that encompasses both the pad and the text
        return pad_bounds.united(text_bounds)

    def get_handle_rects(self):
        """Return the rectangles for the resize handles"""
        width = self.pad_data['width'] * 100
        height = self.pad_data['height'] * 100
        handle_size = 10
        half_handle = handle_size / 2

        return {
            'top_left': QRectF(-width / 2 - half_handle, -height / 2 - half_handle, handle_size, handle_size),
            'top_right': QRectF(width / 2 - half_handle, -height / 2 - half_handle, handle_size, handle_size),
            'bottom_left': QRectF(-width / 2 - half_handle, height / 2 - half_handle, handle_size, handle_size),
            'bottom_right': QRectF(width / 2 - half_handle, height / 2 - half_handle, handle_size, handle_size)
        }

    def paint(self, painter, option, widget):
        """Paint the pad"""
        try:
            # Get dimensions
            width = float(self.pad_data['width']) * 100
            height = float(self.pad_data['height']) * 100
            hole_diameter = float(self.pad_data.get('hole_diameter', 0)) * 100
            corner_radius = float(self.pad_data.get('corner_radius', 0)) * 100

            # Update ID text position
            text_bounds = self.id_text.boundingRect()
            self.id_text.setPos(-text_bounds.width() / 2, -text_bounds.height() / 2)

            # Draw pad shape for each visible layer
            for layer_name, is_enabled in self.pad_data['layers'].items():
                if is_enabled and self.layer_visibility[layer_name]:
                    color = self.layer_colors[layer_name]
                    painter.setPen(QPen(color, 2))
                    painter.setBrush(QBrush(color))

                    # Draw the pad shape
                    if self.pad_data['shape'] == 'Circle':
                        diameter = max(width, height)
                        painter.drawEllipse(-diameter / 2, -diameter / 2, diameter, diameter)
                    elif self.pad_data['shape'] == 'Rectangle':
                        if corner_radius > 0:
                            painter.drawRoundedRect(-width / 2, -height / 2, width, height,
                                                    corner_radius, corner_radius)
                        else:
                            painter.drawRect(-width / 2, -height / 2, width, height)
                    elif self.pad_data['shape'] == 'Oval':
                        painter.drawEllipse(-width / 2, -height / 2, width, height)

            # Draw hole for THT pads
            if "THT" in self.pad_data['type'] and hole_diameter > 0:
                painter.setPen(QPen(Qt.black, 1))
                painter.setBrush(QBrush(Qt.white))
                painter.drawEllipse(-hole_diameter / 2, -hole_diameter / 2,
                                    hole_diameter, hole_diameter)

                # Draw thermal relief if enabled
                if self.pad_data['thermal']['enabled']:
                    spoke_width = self.pad_data['thermal']['spoke_width'] * 100
                    gap_width = self.pad_data['thermal']['gap_width'] * 100

                    # Draw thermal relief spokes
                    for angle in [0, 90, 180, 270]:
                        painter.save()
                        painter.rotate(angle)

                        # Draw spoke
                        painter.setPen(QPen(self.layer_colors['top_copper'], spoke_width))
                        painter.drawLine(hole_diameter / 2, 0, gap_width / 2, 0)

                        painter.restore()

            # Draw selection indicator
            if self.isSelected():
                painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(self.boundingRect())

        except Exception as e:
            self.show_error_message("Paint Error", f"An error occurred while painting the pad: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            # Check if clicking on a resize handle
            for handle_name, handle_rect in self.get_handle_rects().items():
                if handle_rect.contains(pos):
                    self.current_handle = handle_name
                    self.is_resizing = True
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing and self.current_handle:
            pos = event.pos()
            width = self.pad_data['width'] * 100
            height = self.pad_data['height'] * 100

            # Calculate the new dimensions based on the handle being dragged
            if self.current_handle == 'bottom_right':
                new_width = (pos.x() + width / 2) * 2
                new_height = (pos.y() + height / 2) * 2
            elif self.current_handle == 'bottom_left':
                new_width = (-pos.x() + width / 2) * 2
                new_height = (pos.y() + height / 2) * 2
            elif self.current_handle == 'top_right':
                new_width = (pos.x() + width / 2) * 2
                new_height = (-pos.y() + height / 2) * 2
            elif self.current_handle == 'top_left':
                new_width = (-pos.x() + width / 2) * 2
                new_height = (-pos.y() + height / 2) * 2

            # Update pad dimensions (with minimum size constraint)
            self.pad_data['width'] = max(0.5, new_width / 100)
            self.pad_data['height'] = max(0.5, new_height / 100)

            # Update the scene
            self.prepareGeometryChange()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_resizing:
            self.is_resizing = False
            self.current_handle = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.update()  # Redraw to show/hide resize handles
        return super().itemChange(change, value)

    def set_layer_visibility(self, layer_name, visible):
        """Set visibility for a specific layer"""
        if layer_name in self.layer_visibility:
            self.layer_visibility[layer_name] = visible
            self.update()  # Trigger a repaint

    def update_layer_settings(self, layer_settings):
        """Update layer settings from pad editor"""
        for layer_name, enabled in layer_settings.items():
            if layer_name in self.pad_data['layers']:
                self.pad_data['layers'][layer_name] = enabled
        self.update()  # Trigger a repaint

    def update_id_text(self):
        """Update the ID text item with current pad data"""
        self.id_text.setPlainText(str(self.pad_data.get('id', '1')))
        self.id_text.setDefaultTextColor(Qt.black)
        # Center the text
        text_bounds = self.id_text.boundingRect()
        self.id_text.setPos(-text_bounds.width() / 2, -text_bounds.height() / 2)

    def update_pad_data(self, new_data):
        """Update pad data and refresh the display"""
        self.pad_data = json.loads(json.dumps(new_data))  # deep copy
        self.update()
        self.update_id_text()

    def update_color(self, layer_name: str, color: QColor):
        """Update the color for a specific layer of the pad"""
        if layer_name in self.layer_colors:
            self.layer_colors[layer_name] = color
            self.update()  # Trigger a repaint