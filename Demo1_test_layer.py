from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QDockWidget,
    QVBoxLayout, QWidget, QCheckBox, QLabel, QHBoxLayout, QPushButton, QColorDialog
)
from PyQt5.QtGui import QColor 
from PyQt5.QtCore import Qt


class LayerViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layer Viewer")
        self.setGeometry(100, 100, 600, 800)

        # Create a dockable widget for layer controls
        self.create_layer_controls()
    
    def create_color_change_handler(self, layer_name, color_label):
        """
        Returns a function that opens a QColorDialog and updates the color label.
        """
        def handler(event):
            new_color = QColorDialog.getColor()
            if new_color.isValid():
                color_label.setStyleSheet(f"background-color: {new_color.name()};")
                print(f"Layer '{layer_name}' color changed to {new_color.name()}")
        return handler
    def create_layer_controls(self):
        """
        Create a dockable widget for layer selection and controls.
        """
        dock = QDockWidget("Layer Controls", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # Create a widget to hold the controls
        dock_widget = QWidget()
        layout = QVBoxLayout()

        # Create a tree widget for layers
        self.layer_tree = QTreeWidget()
        self.layer_tree.setHeaderLabels(["Layer", "Color", "Visible", "Lock"])
        self.layer_tree.setColumnWidth(0, 150)  # Width for "Layer"
        self.layer_tree.setColumnWidth(1, 50)   # Width for "Color"
        self.layer_tree.setColumnWidth(2, 50)   # Width for "Visible"
        self.layer_tree.setColumnWidth(3, 50)   # Width for "Lock"

        # Populate the tree with layers
        self.populate_layer_tree()

        layout.addWidget(self.layer_tree)

        # Add a settings button at the bottom
        settings_button = QPushButton("Settings")
        layout.addWidget(settings_button)

        dock_widget.setLayout(layout)
        dock.setWidget(dock_widget)

        # Add the dock to the main window
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def populate_layer_tree(self):
        """
        Populate the tree widget with layers and their controls.
        """
        # Example parent layers
        parent_layers = ["Top", "Bottom"]
        child_layers = [
            {"name": "Silk", "color": QColor("lightgray")},
            {"name": "Electric", "color": QColor("blue")},
            {"name": "Route", "color": QColor("green")},
            {"name": "Plane", "color": QColor("cyan")},
            {"name": "PadStack", "color": QColor("yellow")},
            {"name": "ViaStack", "color": QColor("magenta")},
            {"name": "Paste", "color": QColor("orange")},
            {"name": "Solder", "color": QColor("red")},
            {"name": "Assembly", "color": QColor("purple")},
            {"name": "Keepout(Route)", "color": QColor("darkblue")},
            {"name": "Keepout(Drill)", "color": QColor("darkgreen")},
            {"name": "Keepout(Component)", "color": QColor("darkred")},
            {"name": "HeightLimit", "color": QColor("brown")},
            {"name": "DesignRule", "color": QColor("pink")},
            {"name": "Dimension", "color": QColor("gray")},
        ]

        for parent_name in parent_layers:
            # Create a parent item
            parent_item = QTreeWidgetItem(self.layer_tree)
            parent_item.setText(0, parent_name)

            for child in child_layers:
                # Extract child name and layer data
                child_name = child["name"]
                layer_color = child["color"]

                # Create a child item
                child_item = QTreeWidgetItem(parent_item)
                child_item.setText(0, child_name)

                # Add a color label with a click event to change the color
                color_label = QLabel()
                color_label.setStyleSheet(f"background-color: {layer_color.name()};")
                color_label.mousePressEvent = self.create_color_change_handler(child_name, color_label)
                self.layer_tree.setItemWidget(child_item, 1, color_label)

                # Add a visibility checkbox
                visibility_widget = QWidget()
                visibility_layout = QHBoxLayout(visibility_widget)
                visibility_layout.setContentsMargins(0, 0, 0, 0)
                visibility_layout.setAlignment(Qt.AlignCenter)
                visibility_checkbox = QCheckBox()
                visibility_checkbox.setChecked(True)
                visibility_layout.addWidget(visibility_checkbox)
                self.layer_tree.setItemWidget(child_item, 2, visibility_widget)

                # Add a lock checkbox
                lock_widget = QWidget()
                lock_layout = QHBoxLayout(lock_widget)
                lock_layout.setContentsMargins(0, 0, 0, 0)
                lock_layout.setAlignment(Qt.AlignCenter)
                lock_checkbox = QCheckBox()
                lock_checkbox.setChecked(False)
                lock_layout.addWidget(lock_checkbox)
                self.layer_tree.setItemWidget(child_item, 3, lock_widget)
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = LayerViewer()
    window.show()
    sys.exit(app.exec_())