from PyQt5.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QCheckBox, QLabel, QLineEdit, QPushButton, QGridLayout,
                             QGraphicsScene, QGraphicsView, QGraphicsEllipseItem,
                             QGraphicsRectItem, QGraphicsPathItem, QTabWidget,
                             QTreeWidget, QTreeWidgetItem, QSplitter, QFrame,
                             QSpacerItem, QSizePolicy, QComboBox, QApplication,
                             QColorDialog, QStyledItemDelegate)
from PyQt5.QtGui import QPen, QBrush, QPainterPath, QColor, QPainter
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QRect
from typing import Dict, List, Optional, Tuple
import sys


class ColorBoxDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index):
        if index.column() == 3:  # Color column
            # Get the color from the background role
            color = index.data(Qt.BackgroundRole)
            if color:
                # Calculate the box size and position
                box_size = min(option.rect.height() - 4, 16)  # Max size of 16px
                x = option.rect.right() - box_size - 4  # 4px padding from right
                y = option.rect.center().y() - box_size // 2

                # Draw the color box with border
                painter.save()
                painter.setPen(QPen(Qt.black, 1))
                painter.setBrush(QBrush(color))
                painter.drawRect(x, y, box_size, box_size)
                painter.restore()
        else:
            super().paint(painter, option, index)


class LayerSetting(QDialog):
    """Layer settings dialog that works with the layer manager"""

    # Signals
    layer_changed = pyqtSignal(str)
    layer_visibility_changed = pyqtSignal(str, bool)
    layer_properties_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Layer Settings")
        self.setGeometry(100, 100, 500, 600)

        # Get reference to layer manager from parent
        self.layer_manager = parent.layer_manager if parent else None

        # UI components
        self.layer_tree = None
        self.layer_name_label = None
        self.layer_type_label = None
        self.color_preview = None
        self.color_button = None

        self.init_ui()

    def init_ui(self):
        """Initialize the layer settings UI"""
        main_layout = QVBoxLayout()

        # Layer tree
        self.layer_tree = QTreeWidget()
        self.layer_tree.setHeaderLabels(["Layer", "Visible", "Locked", "Color"])
        self.layer_tree.setColumnWidth(0, 200)
        self.layer_tree.setColumnWidth(1, 60)
        self.layer_tree.setColumnWidth(2, 60)
        self.layer_tree.setColumnWidth(3, 30)  # Reduced width for color column
        self.layer_tree.itemClicked.connect(self.handle_tree_item_clicked)
        self.layer_tree.itemChanged.connect(self.handle_layer_property_changed)

        # Set custom delegate for color boxes
        color_delegate = ColorBoxDelegate(self.layer_tree)
        self.layer_tree.setItemDelegate(color_delegate)

        # Populate tree from layer manager
        self.populate_layer_tree()
        main_layout.addWidget(self.layer_tree)

        # Layer properties panel
        properties_group = QGroupBox("Layer Properties")
        properties_layout = QGridLayout()

        # Layer name
        self.layer_name_label = QLabel()
        properties_layout.addWidget(QLabel("Name:"), 0, 0)
        properties_layout.addWidget(self.layer_name_label, 0, 1)

        # Layer type
        self.layer_type_label = QLabel()
        properties_layout.addWidget(QLabel("Type:"), 1, 0)
        properties_layout.addWidget(self.layer_type_label, 1, 1)

        # Color selection
        properties_layout.addWidget(QLabel("Color:"), 2, 0)
        color_layout = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(20, 20)
        self.color_preview.setFrameShape(QFrame.Box)
        color_layout.addWidget(self.color_preview)

        self.color_button = QPushButton("Change Color")
        self.color_button.clicked.connect(self.change_layer_color)
        color_layout.addWidget(self.color_button)
        properties_layout.addLayout(color_layout, 2, 1)

        properties_group.setLayout(properties_layout)
        main_layout.addWidget(properties_group)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def populate_layer_tree(self):
        """Populate the layer tree from layer manager data"""
        if not self.layer_manager:
            return

        self.layer_tree.clear()

        # Create group items first
        group_items = {}
        for layer_name, layer_data in self.layer_manager.layers.items():
            group_name = layer_data.get("group")
            if group_name and group_name not in group_items:
                group_item = QTreeWidgetItem(self.layer_tree, [group_name])
                group_item.setFlags(group_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                group_items[group_name] = group_item

        # Add layers to their groups
        for layer_name, layer_data in self.layer_manager.layers.items():
            group_name = layer_data.get("group")
            parent = group_items.get(group_name, self.layer_tree)

            layer_item = QTreeWidgetItem(parent, [layer_name])
            layer_item.setFlags(layer_item.flags() | Qt.ItemIsUserCheckable)

            # Set visibility checkbox
            is_locked = layer_data.get("locked", False)
            is_visible = layer_data.get("visible", True)

            # Set visibility state
            layer_item.setCheckState(1, Qt.Checked if is_visible else Qt.Unchecked)
            if is_locked:
                # Disable visibility checkbox for locked layers
                layer_item.setFlags(layer_item.flags() & ~Qt.ItemIsUserCheckable)
                layer_item.setData(1, Qt.UserRole, "disabled")

            # Set lock checkbox
            layer_item.setCheckState(2, Qt.Checked if is_locked else Qt.Unchecked)

            # Set color indicator
            if layer_data.get("color"):
                layer_item.setBackground(3, layer_data["color"])

        # Expand all groups
        for group_item in group_items.values():
            group_item.setExpanded(True)

    def handle_tree_item_clicked(self, item, column):
        """Handle clicks on tree items"""
        if not item.parent():  # Skip group items
            return

        layer_name = item.text(0)
        if layer_name in self.layer_manager.layers:
            layer_data = self.layer_manager.layers[layer_name]
            self.update_layer_properties_panel(layer_name, layer_data)

    def handle_layer_property_changed(self, item, column):
        """Handle changes to layer properties in the tree"""
        if not item.parent():  # Skip group items
            return

        layer_name = item.text(0)
        if layer_name in self.layer_manager.layers:
            if column == 2:  # Lock checkbox
                locked = item.checkState(2) == Qt.Checked
                self.layer_manager.set_layer_locked(layer_name, locked)

                # Update visibility checkbox state
                if locked:
                    # Disable visibility checkbox and ensure it's checked
                    item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
                    item.setCheckState(1, Qt.Checked)
                    item.setData(1, Qt.UserRole, "disabled")
                else:
                    # Re-enable visibility checkbox
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setData(1, Qt.UserRole, None)

                # Make sure the lock checkbox remains interactive
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)

            elif column == 1:  # Visibility checkbox
                if not item.data(1, Qt.UserRole) == "disabled":  # Only handle if not disabled
                    visible = item.checkState(1) == Qt.Checked
                    if visible:
                        self.layer_manager.show_layer(layer_name)
                    else:
                        self.layer_manager.hide_layer(layer_name)

    def update_layer_properties_panel(self, layer_name, layer_data):
        """Update the properties panel with layer data"""
        self.layer_name_label.setText(layer_name)
        self.layer_type_label.setText(layer_data.get("group", ""))

        color = layer_data.get("color")
        if color:
            self.color_preview.setStyleSheet(f"background-color: {color.name()}")

    def change_layer_color(self):
        """Change the color of the selected layer"""
        selected_items = self.layer_tree.selectedItems()
        if not selected_items or not selected_items[0].parent():
            return

        layer_name = selected_items[0].text(0)
        if layer_name in self.layer_manager.layers:
            current_color = self.layer_manager.layers[layer_name].get("color", QColor(Qt.black))
            color = QColorDialog.getColor(current_color, self, "Choose Layer Color")

            if color.isValid():
                self.layer_manager.set_layer_color(layer_name, color)
                selected_items[0].setBackground(3, color)
                self.color_preview.setStyleSheet(f"background-color: {color.name()}")

    def select_layer(self, layer_name):
        """Pre-select a specific layer in the settings dialog"""
        # Find and select the layer in the tree widget
        root = self.layer_tree.invisibleRootItem()
        for group_index in range(root.childCount()):
            group_item = root.child(group_index)
            for layer_index in range(group_item.childCount()):
                layer_item = group_item.child(layer_index)
                if layer_item.text(0) == layer_name:
                    self.layer_tree.setCurrentItem(layer_item)
                    return