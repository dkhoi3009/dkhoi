from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QPen, QColor, QIcon, QPixmap, QPainter, QBrush
from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsItem, QListWidget,
                             QTreeWidgetItem, QMenu, QFrame, QListWidgetItem)


class LayerManager(QObject):
    # Add signal for layer double click
    layer_double_clicked = pyqtSignal(str)

    def __init__(self, scene: QGraphicsScene, layers_widget: QListWidget):
        """
        Manage layers in the scene.
        :param scene: QGraphicsScene where layers will be managed.
        """
        super().__init__()  # Initialize QObject for signals
        self.scene = scene
        self.layers_widget = layers_widget
        self.layers = {}  # Dictionary to store layers and their items
        self.layer_groups = {}  # Dictionary to store layer groups
        self.is_updating = False  # Flag to prevent recursive updates
        self.pad_layer_map = {
            'top_copper': 'Copper/top_copper',
            'bottom_copper': 'Copper/bottom_copper',
            'top_mask': 'Mask/top_mask',
            'bottom_mask': 'Mask/bottom_mask',
            'top_paste': 'Paste/top_paste',
            'bottom_paste': 'Paste/bottom_paste'
        }

        # Create the lock icon
        self.lock_icon = self._create_lock_icon()

        # Set up tree widget columns
        self.layers_widget.setHeaderLabels(["Layer", "Color"])
        self.layers_widget.setColumnWidth(0, 200)
        self.layers_widget.setColumnWidth(1, 60)

        # Connect signals
        self.layers_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.layers_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.layers_widget.customContextMenuRequested.connect(self._show_context_menu)

    def _create_lock_icon(self):
        """Create a custom lock icon"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Draw a simple lock shape
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(Qt.black))

        # Draw lock body (rectangle)
        painter.drawRect(4, 8, 8, 6)

        # Draw lock shackle (arc)
        painter.drawArc(4, 4, 8, 8, 0, 180 * 16)

        painter.end()
        return QIcon(pixmap)

    def _on_item_double_clicked(self, item):
        """Handle double click on layer items"""
        if item.parent():  # Only handle layer items, not group items
            layer_name = item.text(0)
            if layer_name in self.layers:
                self.layer_double_clicked.emit(layer_name)

    def _show_context_menu(self, position):
        """Show context menu for layer items"""
        item = self.layers_widget.itemAt(position)
        if item and item.parent():  # Only for layer items, not group items
            layer_name = item.text(0)
            if layer_name in self.layers:
                menu = QMenu()
                is_locked = self.layers[layer_name].get("locked", False)

                # Create lock/unlock action
                lock_action = menu.addAction("Unlock" if is_locked else "Lock")
                lock_action.triggered.connect(lambda: self.set_layer_locked(layer_name, not is_locked))

                # Show menu at cursor position
                menu.exec_(self.layers_widget.viewport().mapToGlobal(position))

    def add_layer(self, layer_name: str, color: QColor = None, z_index: int = 0, group_name: str = None):
        """
        Add a new layer to the scene.
        :param layer_name: Name of the layer.
        :param color: Default color for the layer.
        :param z_index: Display order of the layer (z-index).
        :param group_name: Name of the layer group.
        """
        if layer_name in self.layers:
            return  # Skip if layer already exists

        # Create a new layer
        self.layers[layer_name] = {
            "items": [],  # List of items in the layer
            "visible": True,
            "locked": False,  # Add locked property
            "z_index": z_index,
            "color": color,
            "group": group_name
        }

        # Find or create the group item
        group_item = None
        if group_name:
            # Search for existing group in the layer_groups dictionary
            if group_name in self.layer_groups:
                group_item = self.layer_groups[group_name]
            else:
                # Create new group
                group_item = QTreeWidgetItem(self.layers_widget, [group_name])
                group_item.setFlags(group_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                self.layer_groups[group_name] = group_item

        # Create layer item
        if group_item:
            # Check if layer already exists in group
            for i in range(group_item.childCount()):
                if group_item.child(i).text(0) == layer_name:
                    return  # Skip if layer already exists in group
            layer_item = QTreeWidgetItem(group_item, [layer_name, ""])  # Empty text for color column
        else:
            layer_item = QTreeWidgetItem(self.layers_widget, [layer_name, ""])  # Empty text for color column

        layer_item.setFlags(layer_item.flags() | Qt.ItemIsUserCheckable)
        layer_item.setCheckState(0, Qt.Checked)  # Set visibility in layer name column

        # Create color preview frame
        if color:
            color_preview = QFrame()
            color_preview.setFixedSize(40, 16)
            color_preview.setFrameShape(QFrame.Box)
            color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
            self.layers_widget.setItemWidget(layer_item, 1, color_preview)

        # Expand the group
        if group_item:
            group_item.setExpanded(True)

        # Update the tree widget item
        self._update_layer_item_state(layer_name)

    def add_layer_to_list(self, layer_name: str, color: QColor):
        item = QListWidgetItem(layer_name)
        icon = QIcon(QPixmap(16, 16))
        icon.pixmap(16, 16).fill(color)
        item.setIcon(icon)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked)
        self.layers_widget.addItem(item)
        self.layers_widget.setCurrentItem(item)

    def remove_layer(self, layer_name: str):
        """
        Xóa một layer khỏi cảnh.
        :param layer_name: Tên của layer cần xóa.
        """
        if layer_name not in self.layers:
            raise ValueError(f"Layer '{layer_name}' không tồn tại.")

        # Xóa tất cả các đối tượng trong layer khỏi scene
        for item in self.layers[layer_name]["items"]:
            self.scene.removeItem(item)
        del self.layers[layer_name]

    def hide_layer(self, layer_name: str):
        """
        Hide a layer in the scene.
        :param layer_name: Name of the layer to hide.
        """
        if layer_name not in self.layers:
            raise ValueError(f"Layer '{layer_name}' does not exist.")

        # Don't hide if layer is locked
        if self.layers[layer_name].get("locked", False):
            self._update_layer_item_state(layer_name)  # Ensure checkbox state is correct
            return

        self.layers[layer_name]["visible"] = False

        # Update visibility of items in this layer
        for item in self.layers[layer_name]["items"]:
            if isinstance(item, QGraphicsItem):
                if hasattr(item, 'pad_data') and hasattr(item, 'set_layer_visibility'):
                    # For pads, only update the visibility of the corresponding layer
                    for pad_layer, mapped_layer in self.pad_layer_map.items():
                        if mapped_layer.endswith(layer_name):
                            item.set_layer_visibility(pad_layer, False)
                else:
                    # For non-pad items, simply hide them
                    item.setVisible(False)

        # Update the tree widget item
        self._update_layer_item_state(layer_name)

    def show_layer(self, layer_name: str):
        """
        Show a layer in the scene.
        :param layer_name: Name of the layer to show.
        """
        if layer_name not in self.layers:
            raise ValueError(f"Layer '{layer_name}' does not exist.")

        self.layers[layer_name]["visible"] = True

        # Update visibility of items in this layer
        for item in self.layers[layer_name]["items"]:
            if isinstance(item, QGraphicsItem):
                if hasattr(item, 'pad_data') and hasattr(item, 'set_layer_visibility'):
                    # For pads, only update the visibility of the corresponding layer
                    for pad_layer, mapped_layer in self.pad_layer_map.items():
                        if mapped_layer.endswith(layer_name):
                            item.set_layer_visibility(pad_layer, True)
                else:
                    # For non-pad items, simply show them
                    item.setVisible(True)

        # Update the tree widget item
        self._update_layer_item_state(layer_name)

    def add_item_to_layer(self, item: QGraphicsItem, layer_name: str):
        """
        Add an item to a layer.
        :param item: QGraphicsItem to add.
        :param layer_name: Name of the layer.
        """
        if layer_name not in self.layers:
            raise ValueError(f"Layer '{layer_name}' does not exist.")

        # Add item to layer's management list
        self.layers[layer_name]["items"].append(item)

        # Set Z-index based on layer
        item.setZValue(self.layers[layer_name]["z_index"])

        # Handle visibility
        if hasattr(item, 'pad_data') and hasattr(item, 'set_layer_visibility'):
            # For pads, set visibility for specific layers
            for pad_layer, mapped_layer in self.pad_layer_map.items():
                target_layer = mapped_layer.split('/')[-1]
                if target_layer == layer_name:
                    item.set_layer_visibility(pad_layer, self.layers[layer_name]["visible"])
        else:
            # For non-pad items, set overall visibility
            item.setVisible(self.layers[layer_name]["visible"])
            self.scene.addItem(item)  # Only add non-pad items here

    def clear_layer(self, layer_name: str):
        """
        Xóa tất cả các đối tượng trong một layer.
        :param layer_name: Tên của layer cần xóa.
        """
        if layer_name not in self.layers:
            raise ValueError(f"Layer '{layer_name}' không tồn tại.")

        for item in self.layers[layer_name]["items"]:
            self.scene.removeItem(item)
        self.layers[layer_name]["items"].clear()

    def set_layer_color(self, layer_name: str, color: QColor):
        """
        Set color for all items in the layer.
        :param layer_name: Name of the layer.
        :param color: New color to apply.
        """
        if layer_name not in self.layers:
            raise ValueError(f"Layer '{layer_name}' does not exist.")

        # Update layer color in the layer data
        self.layers[layer_name]["color"] = color

        # Update all items in the layer
        for item in self.layers[layer_name]["items"]:
            if isinstance(item, QGraphicsItem):
                if hasattr(item, 'pad_data') and hasattr(item, 'update_color'):
                    # For pads, update the specific layer color
                    for pad_layer, mapped_layer in self.pad_layer_map.items():
                        if mapped_layer.endswith(layer_name):
                            item.update_color(pad_layer, color)
                else:
                    # For non-pad items, update their pen and brush
                    pen = item.pen()
                    pen.setColor(color)
                    item.setPen(pen)

                    if hasattr(item, 'brush'):
                        brush = item.brush()
                        brush.setColor(color)
                        item.setBrush(brush)

                # Force a visual update
                item.update()

        # Update the tree widget item color if it exists
        layer_item = self._find_layer_item(layer_name)
        if layer_item:
            color_preview = QFrame()
            color_preview.setFixedSize(40, 16)
            color_preview.setFrameShape(QFrame.Box)
            color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
            self.layers_widget.setItemWidget(layer_item, 1, color_preview)

    def get_layer_group(self, layer_name: str):
        """Get the group name for a layer"""
        if layer_name in self.layers:
            return self.layers[layer_name]["group"]
        return None

    def remove_item_from_layer(self, item: QGraphicsItem, layer_name: str):
        """Remove an item from a specific layer"""
        if layer_name in self.layers and item in self.layers[layer_name]["items"]:
            self.layers[layer_name]["items"].remove(item)

    def set_layer_locked(self, layer_name: str, locked: bool):
        """
        Set the locked state of a layer.
        :param layer_name: Name of the layer.
        :param locked: Whether the layer should be locked.
        """
        if layer_name not in self.layers:
            raise ValueError(f"Layer '{layer_name}' does not exist.")

        self.layers[layer_name]["locked"] = locked

        # If locking the layer, ensure it's visible
        if locked:
            self.show_layer(layer_name)

        # Update the tree widget item
        self._update_layer_item_state(layer_name)

    def is_layer_locked(self, layer_name: str) -> bool:
        """
        Check if a layer is locked.
        :param layer_name: Name of the layer.
        :return: True if the layer is locked, False otherwise.
        """
        if layer_name not in self.layers:
            raise ValueError(f"Layer '{layer_name}' does not exist.")
        return self.layers[layer_name].get("locked", False)

    def _update_layer_item_state(self, layer_name: str):
        """
        Update the tree widget item state for a layer.
        :param layer_name: Name of the layer.
        """
        if self.is_updating:
            return

        self.is_updating = True
        try:
            # Find the layer item in the tree
            layer_item = self._find_layer_item(layer_name)
            if not layer_item:
                return

            # Get layer data
            layer_data = self.layers[layer_name]
            is_locked = layer_data.get("locked", False)
            is_visible = layer_data.get("visible", True)

            # Update visibility checkbox and lock icon in layer name column
            if is_locked:
                # For locked layers, force visible and disable checkbox
                layer_item.setCheckState(0, Qt.Checked)
                layer_item.setFlags(layer_item.flags() & ~Qt.ItemIsUserCheckable)
                layer_item.setData(0, Qt.UserRole, "disabled")
                # Set lock icon
                layer_item.setIcon(0, self.lock_icon)
            else:
                # For unlocked layers, allow checkbox interaction
                layer_item.setFlags(layer_item.flags() | Qt.ItemIsUserCheckable)
                layer_item.setCheckState(0, Qt.Checked if is_visible else Qt.Unchecked)
                layer_item.setData(0, Qt.UserRole, None)
                # Clear lock icon
                layer_item.setIcon(0, QIcon())
        finally:
            self.is_updating = False

    def _find_layer_item(self, layer_name: str) -> QTreeWidgetItem:
        """
        Find a layer item in the tree widget.
        :param layer_name: Name of the layer to find.
        :return: The QTreeWidgetItem for the layer, or None if not found.
        """
        root = self.layers_widget.invisibleRootItem()
        for group_index in range(root.childCount()):
            group_item = root.child(group_index)
            for layer_index in range(group_item.childCount()):
                layer_item = group_item.child(layer_index)
                if layer_item.text(0) == layer_name:
                    return layer_item
        return None