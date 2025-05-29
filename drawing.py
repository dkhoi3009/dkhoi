import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QColorDialog, QMessageBox, QVBoxLayout, QGraphicsItem,
    QGraphicsLineItem, QGraphicsRectItem, QGraphicsEllipseItem
)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QColor, QPainter
from PyQt5.QtWidgets import QGraphicsSceneMouseEvent
from pad import Pad  # Import at module level to avoid circular imports
import traceback


class DrawingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Multi-Layer Drawing")
        self.setGeometry(100, 100, 800, 600)

        self.scene = QGraphicsScene()
        self.drawing_window = QGraphicsView(self.scene)
        self.setCentralWidget(self.drawing_window)

        # Configure view settings
        self.drawing_window.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.drawing_window.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.drawing_window.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.drawing_window.setRenderHint(QPainter.Antialiasing)
        self.drawing_window.setMouseTracking(True)

        # Enable zoom functionality
        self.drawing_window.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.drawing_window.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.zoom_factor = 1.15  # Zoom factor per step
        self.min_zoom = 0.1  # Minimum zoom level
        self.max_zoom = 10  # Maximum zoom level

        # Initialize drawing state
        self.drawing_mode = "select"
        self.selected_color = QColor(Qt.black)
        self.layer = None
        self.default_layer = "top_copper"

        # Initialize interaction states
        self.current_item = None
        self.start_point = None
        self.selected_item = None
        self.resize_handle = None
        self.resize_start = None
        self.is_dragging = False

        # Set up event handling
        self.drawing_window.viewport().installEventFilter(self)
        self.update_drag_mode()

    def update_drag_mode(self):
        """Update the drag mode based on the current drawing mode"""
        if self.drawing_mode == "select":
            self.drawing_window.setDragMode(QGraphicsView.RubberBandDrag)
            self.drawing_window.setInteractive(True)
        else:
            self.drawing_window.setDragMode(QGraphicsView.NoDrag)
            self.drawing_window.setInteractive(False)

    def set_drawing_mode(self, mode):
        """Set the drawing mode and update cursor and drag mode"""
        # Reset any ongoing operation
        self.current_item = None
        self.start_point = None
        self.is_dragging = False

        # Update mode and settings
        self.drawing_mode = mode
        self.set_cursor_for_mode()
        self.update_drag_mode()

    def eventFilter(self, source, event):
        if source is self.drawing_window.viewport():
            event_type = event.type()

            # Handle wheel events for zooming
            if event_type == event.Wheel:
                if event.modifiers() == Qt.ControlModifier:
                    # Zoom with Ctrl + Mouse Wheel
                    if event.angleDelta().y() > 0:
                        self.zoom_in(event.pos())
                    else:
                        self.zoom_out(event.pos())
                    return True

            # Handle double click first
            if event_type == event.MouseButtonDblClick:
                handled = self.mouse_double_click(event)
                if handled:
                    return True
                event.accept()
                return True

            # In select mode, let the view handle the events for rubber band selection
            if self.drawing_mode == "select" and event_type == event.MouseButtonPress:
                if not self.scene.itemAt(self.drawing_window.mapToScene(event.pos()), self.drawing_window.transform()):
                    # If clicking empty space in select mode, let the view handle it
                    return False

            # Handle other events
            if event_type == event.MouseButtonPress:
                return self.mouse_press(event)
            elif event_type == event.MouseButtonRelease:
                return self.mouse_release(event)
            elif event_type == event.MouseMove:
                return self.mouse_move(event)
            elif event_type == event.KeyPress:
                return self.keyPressEvent(event)

        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
        """Handle keyboard events"""
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.delete_selected_items()
            event.accept()
            return True
        else:
            super().keyPressEvent(event)
            return False

    def delete_selected_items(self):
        """Delete selected items from the scene"""
        try:
            selected_items = self.scene.selectedItems()
            if not selected_items:
                return

            for item in selected_items:
                self.scene.removeItem(item)

                # Remove from pads list if it's a pad
                if hasattr(self, 'pads') and item in self.pads:
                    self.pads.remove(item)

        except Exception as e:
            print(f"Error deleting items: {str(e)}")
            traceback.print_exc()

    def delete_selected_item(self):
        """Legacy method for compatibility - calls delete_selected_items"""
        self.delete_selected_items()

    def mouse_press(self, event):
        if event.button() != Qt.LeftButton:
            event.accept()
            return True

        scene_pos = self.drawing_window.mapToScene(event.pos())

        # Check if we're clicking on an existing item
        clicked_item = self.scene.itemAt(scene_pos, self.drawing_window.transform())

        # Ignore interaction if clicked item is a grid line
        if clicked_item and clicked_item.__class__.__name__ == 'GridLine':
            event.ignore()
            return False

        # Check if we're clicking on a resize handle
        if self.selected_item and self.is_near_corner(scene_pos, self.selected_item):
            self.resize_handle = self.get_resize_handle(scene_pos, self.selected_item)
            self.resize_start = scene_pos
            event.accept()
            return True

        if clicked_item:
            # Select the item
            if self.selected_item and self.selected_item != clicked_item:
                if hasattr(self.selected_item, 'setPen'):
                    self.selected_item.setPen(QPen(self.selected_color, 2))
                self.selected_item.setSelected(False)

            self.selected_item = clicked_item
            if hasattr(self.selected_item, 'setPen'):
                self.selected_item.setPen(QPen(Qt.red, 2, Qt.DashLine))
            self.selected_item.setSelected(True)
            self.start_point = scene_pos
            self.is_dragging = True
            event.accept()
            return True

        # If in drawing mode, prepare for drawing
        if self.drawing_mode and self.drawing_mode != "select":
            current_layer = self.get_current_layer()
            if current_layer is None:
                QMessageBox.warning(self, "Layer Error",
                                    "No active layer selected. Please select a layer first.")
                event.accept()
                return True

            self.start_point = scene_pos
            self.current_item = None
            self.is_dragging = True
            event.accept()
            return True
        else:
            # In select mode, clear selection when clicking empty space
            if self.selected_item:
                if hasattr(self.selected_item, 'setPen'):
                    self.selected_item.setPen(QPen(self.selected_color, 2))
                self.selected_item.setSelected(False)
                self.selected_item = None
            self.start_point = None
            self.is_dragging = False
            # Don't accept the event in select mode to allow rubber band selection
            return False

    def mouse_release(self, event):
        if event.button() != Qt.LeftButton:
            event.accept()
            return True

        if self.current_item:
            current_layer = self.get_current_layer()
            if current_layer is not None:
                try:
                    current_layer["items"].append(self.current_item)
                except Exception as e:
                    print(f"Error adding item to layer: {e}")
                    self.scene.removeItem(self.current_item)
                    QMessageBox.warning(self, "Layer Error",
                                        "Failed to add item to layer. Please try again.")

            self.current_item = None
            event.accept()
            return True

        # Reset all states on mouse release
        self.resize_handle = None
        self.resize_start = None
        self.start_point = None
        self.is_dragging = False
        event.accept()
        return True

    def create_graphics_scene_mouse_event(self, event, event_type):
        """Convert a QMouseEvent to a QGraphicsSceneMouseEvent"""
        scene_event = QGraphicsSceneMouseEvent(event_type)
        scene_event.setScenePos(self.drawing_window.mapToScene(event.pos()))
        scene_event.setPos(self.drawing_window.mapToScene(event.pos()))
        scene_event.setScreenPos(event.globalPos())
        scene_event.setButtonDownScreenPos(Qt.LeftButton, event.globalPos())
        scene_event.setButtonDownScenePos(Qt.LeftButton, self.drawing_window.mapToScene(event.pos()))
        scene_event.setButtons(event.buttons())
        scene_event.setButton(event.button())
        scene_event.setModifiers(event.modifiers())
        scene_event.setAccepted(False)
        return scene_event

    def mouse_move(self, event):
        if not event.buttons() & Qt.LeftButton:
            return False

        if not self.is_dragging:
            return False

        scene_pos = self.drawing_window.mapToScene(event.pos())

        if self.resize_handle and self.selected_item and self.resize_start:
            # Handle resizing
            if isinstance(self.selected_item, Pad):
                # Calculate the change in position
                delta = scene_pos - self.resize_start

                # Get current pad dimensions
                width = self.selected_item.pad_data['width'] * 100
                height = self.selected_item.pad_data['height'] * 100
                hole_diameter = self.selected_item.pad_data['hole_diameter'] * 100
                aspect_ratio = width / height if height != 0 else 1

                # Calculate hole ratio relative to the minimum dimension
                min_dimension = min(width, height)
                hole_ratio = hole_diameter / min_dimension if min_dimension != 0 else 0.5

                # Update dimensions based on resize handle
                if self.resize_handle == 'bottom_right':
                    # Use the larger delta to determine the scaling
                    if abs(delta.x()) > abs(delta.y()):
                        new_width = (width + delta.x() * 2) / 100
                        new_height = new_width / aspect_ratio
                    else:
                        new_height = (height + delta.y() * 2) / 100
                        new_width = new_height * aspect_ratio
                elif self.resize_handle == 'bottom_left':
                    if abs(delta.x()) > abs(delta.y()):
                        new_width = (width - delta.x() * 2) / 100
                        new_height = new_width / aspect_ratio
                    else:
                        new_height = (height + delta.y() * 2) / 100
                        new_width = new_height * aspect_ratio
                elif self.resize_handle == 'top_right':
                    if abs(delta.x()) > abs(delta.y()):
                        new_width = (width + delta.x() * 2) / 100
                        new_height = new_width / aspect_ratio
                    else:
                        new_height = (height - delta.y() * 2) / 100
                        new_width = new_height * aspect_ratio
                elif self.resize_handle == 'top_left':
                    if abs(delta.x()) > abs(delta.y()):
                        new_width = (width - delta.x() * 2) / 100
                        new_height = new_width / aspect_ratio
                    else:
                        new_height = (height - delta.y() * 2) / 100
                        new_width = new_height * aspect_ratio

                # Apply minimum size constraint while maintaining aspect ratio
                min_size = 0.5
                if new_width < min_size:
                    new_width = min_size
                    new_height = new_width / aspect_ratio
                if new_height < min_size:
                    new_height = min_size
                    new_width = new_height * aspect_ratio

                # Calculate new hole diameter based on the minimum dimension
                new_min_dimension = min(new_width, new_height)
                new_hole_diameter = new_min_dimension * hole_ratio

                # Ensure hole diameter doesn't exceed pad dimensions
                max_hole_diameter = min(new_width, new_height) * 0.9  # Maximum 90% of minimum dimension
                new_hole_diameter = min(new_hole_diameter, max_hole_diameter)

                # Ensure minimum hole diameter
                min_hole_diameter = 0.2  # Minimum hole diameter in mm
                new_hole_diameter = max(new_hole_diameter, min_hole_diameter)

                # Update pad dimensions
                self.selected_item.pad_data['width'] = new_width
                self.selected_item.pad_data['height'] = new_height
                if "THT" in self.selected_item.pad_data.get('type', ''):
                    self.selected_item.pad_data['hole_diameter'] = new_hole_diameter

                # Update the scene
                self.selected_item.prepareGeometryChange()
                self.selected_item.update()

                # Update tooltip with dimensions
                tooltip_text = f"Size: {new_width:.2f} x {new_height:.2f}"
                if "THT" in self.selected_item.pad_data.get('type', ''):
                    tooltip_text += f"\nHole: {new_hole_diameter:.2f}"
                self.selected_item.setToolTip(tooltip_text)

            else:
                delta = scene_pos - self.resize_start
                self.resize_item(self.selected_item, delta, self.resize_handle)
            self.resize_start = scene_pos
            event.accept()
            return True

        # Handle drawing - only create/update item if mouse button is pressed
        if self.start_point and self.drawing_mode != "select":
            if not self.current_item:  # Create item only when starting to drag
                if self.drawing_mode == "line":
                    self.current_item = QGraphicsLineItem(
                        self.start_point.x(), self.start_point.y(),
                        self.start_point.x(), self.start_point.y()
                    )
                elif self.drawing_mode == "rect":
                    self.current_item = QGraphicsRectItem(
                        QRectF(self.start_point, self.start_point)
                    )
                elif self.drawing_mode == "circle":
                    self.current_item = QGraphicsEllipseItem(
                        QRectF(self.start_point, self.start_point)
                    )

                if self.current_item:
                    self.current_item.setPen(QPen(self.selected_color, 2))
                    self.current_item.setFlag(QGraphicsItem.ItemIsSelectable)
                    self.current_item.setFlag(QGraphicsItem.ItemIsMovable)
                    self.scene.addItem(self.current_item)

            # Update the current item's geometry
            if self.current_item:
                if isinstance(self.current_item, QGraphicsLineItem):
                    self.current_item.setLine(
                        self.start_point.x(), self.start_point.y(),
                        scene_pos.x(), scene_pos.y()
                    )
                    # Update tooltip with line length and coordinates
                    dx = scene_pos.x() - self.start_point.x()
                    dy = scene_pos.y() - self.start_point.y()
                    length = (dx * dx + dy * dy) ** 0.5
                    self.current_item.setToolTip(
                        f"Length: {length:.1f}\n"
                        f"Start: ({self.start_point.x():.1f}, {self.start_point.y():.1f})\n"
                        f"End: ({scene_pos.x():.1f}, {scene_pos.y():.1f})"
                    )
                elif isinstance(self.current_item, (QGraphicsRectItem, QGraphicsEllipseItem)):
                    rect = QRectF(self.start_point, scene_pos).normalized()
                    self.current_item.setRect(rect)
                    # Update tooltip with size and position
                    self.current_item.setToolTip(
                        f"Size: {rect.width():.1f} x {rect.height():.1f}\n"
                        f"Position: ({rect.x():.1f}, {rect.y():.1f})"
                    )
            event.accept()
            return True

        elif self.selected_item and self.start_point:
            # Handle dragging
            if self.drawing_mode == "select" or not self.drawing_mode:
                delta = scene_pos - self.start_point
                self.selected_item.moveBy(delta.x(), delta.y())
                self.start_point = scene_pos

                # Update tooltip with current position
                pos = self.selected_item.pos()
                if isinstance(self.selected_item, Pad):
                    self.selected_item.setToolTip(
                        f"Position: ({pos.x():.1f}, {pos.y():.1f})\n"
                        f"Size: {self.selected_item.pad_data['width']:.2f} x {self.selected_item.pad_data['height']:.2f}"
                    )
                else:
                    self.selected_item.setToolTip(f"Position: ({pos.x():.1f}, {pos.y():.1f})")
                event.accept()
                return True

        return False

    def is_near_corner(self, pos, item):
        """Check if position is near any corner of the item"""
        rect = item.boundingRect()
        item_pos = item.pos()
        corners = [
            item_pos + QPointF(rect.left(), rect.top()),
            item_pos + QPointF(rect.right(), rect.top()),
            item_pos + QPointF(rect.left(), rect.bottom()),
            item_pos + QPointF(rect.right(), rect.bottom())
        ]
        return any((pos - corner).manhattanLength() < 10 for corner in corners)

    def get_resize_handle(self, pos, item):
        """Get which corner is being grabbed for resizing"""
        rect = item.boundingRect()
        item_pos = item.pos()
        corners = {
            'top_left': item_pos + QPointF(rect.left(), rect.top()),
            'top_right': item_pos + QPointF(rect.right(), rect.top()),
            'bottom_left': item_pos + QPointF(rect.left(), rect.bottom()),
            'bottom_right': item_pos + QPointF(rect.right(), rect.bottom())
        }

        for handle, corner in corners.items():
            if (pos - corner).manhattanLength() < 10:
                return handle
        return None

    def resize_item(self, item, delta, handle):
        """Resize the item based on the handle being dragged"""
        if isinstance(item, Pad):
            # Let the Pad handle its own resizing
            return

        if isinstance(item, QGraphicsLineItem):
            line = item.line()
            if handle == 'top_left':
                item.setLine(line.x1() + delta.x(), line.y1() + delta.y(), line.x2(), line.y2())
            elif handle == 'bottom_right':
                item.setLine(line.x1(), line.y1(), line.x2() + delta.x(), line.y2() + delta.y())
        else:
            rect = item.rect()
            if handle == 'top_left':
                rect.setTopLeft(rect.topLeft() + delta)
            elif handle == 'top_right':
                rect.setTopRight(rect.topRight() + delta)
            elif handle == 'bottom_left':
                rect.setBottomLeft(rect.bottomLeft() + delta)
            elif handle == 'bottom_right':
                rect.setBottomRight(rect.bottomRight() + delta)
            item.setRect(rect.normalized())

    def choose_color(self):
        color = QColorDialog.getColor(self.selected_color, self, "Choose Color")
        if color.isValid():
            self.selected_color = color

    def set_cursor_for_mode(self):
        """Set appropriate cursor based on current drawing mode"""
        if self.drawing_mode == "select":
            self.drawing_window.viewport().setCursor(Qt.ArrowCursor)
        else:
            self.drawing_window.viewport().setCursor(Qt.CrossCursor)

    def mouse_double_click(self, event):
        """Handle double click events"""
        if event.button() != Qt.LeftButton:
            return False

        scene_pos = self.drawing_window.mapToScene(event.pos())
        clicked_item = self.scene.itemAt(scene_pos, self.drawing_window.transform())

        # Reset any drawing state to prevent unwanted items
        self.current_item = None
        self.start_point = None
        self.resize_handle = None
        self.resize_start = None

        if clicked_item and isinstance(clicked_item, Pad):
            # Get reference to main window to access pad editor
            main_window = self.parent()
            if main_window and hasattr(main_window, 'show_pad_editor'):
                main_window.show_pad_editor(clicked_item)
                event.accept()
                return True

        # Always accept the event to prevent it from propagating
        event.accept()
        return True

    def get_current_layer(self):
        """Get the current active layer or default layer"""
        if self.layer is None:
            # Try to get the default layer from the layer manager
            main_window = self.parent()
            if main_window and hasattr(main_window, 'layer_manager'):
                try:
                    self.layer = main_window.layer_manager.layers.get(self.default_layer)
                    if self.layer is None:
                        # If default layer doesn't exist, try to get the first available layer
                        if main_window.layer_manager.layers:
                            self.layer = next(iter(main_window.layer_manager.layers.values()))
                except Exception as e:
                    print(f"Error getting default layer: {e}")
                    return None
        return self.layer

    def zoom_in(self, pos):
        """Zoom in centered on the given position"""
        current_scale = self.drawing_window.transform().m11()  # Get current horizontal scale
        if current_scale < self.max_zoom:
            self.drawing_window.scale(self.zoom_factor, self.zoom_factor)

    def zoom_out(self, pos):
        """Zoom out centered on the given position"""
        current_scale = self.drawing_window.transform().m11()  # Get current horizontal scale
        if current_scale > self.min_zoom:
            self.drawing_window.scale(1 / self.zoom_factor, 1 / self.zoom_factor)