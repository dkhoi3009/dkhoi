from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout,
                             QHBoxLayout, QCheckBox, QLabel, QScrollArea, QGridLayout,
                             QGroupBox, QPushButton, QRadioButton)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPixmap
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QSize
from typing import Dict, List, Optional
import sys

# Color constants
BLACK = QColor(0, 0, 0)
WHITE = QColor(255, 255, 255)
GRAY = QColor(128, 128, 128)
LIGHT_GRAY = QColor(200, 200, 200)
RED = QColor(255, 0, 0)
GREEN = QColor(0, 255, 0)
BLUE = QColor(0, 0, 255)
YELLOW = QColor(255, 255, 0)

# Layer type colors (example colors - adjust as needed)
LAYER_COLORS = {
    "silk": QColor(255, 255, 255, 200),  # White with transparency
    "electric": QColor(0, 100, 255, 180),  # Blue with transparency
    "solder": QColor(0, 180, 0, 180),  # Green with transparency
    "paste": QColor(180, 180, 180, 180),  # Gray with transparency
    "assembly": QColor(255, 200, 0, 180),  # Yellow with transparency
    "board": QColor(30, 30, 30, 255),  # Dark gray
    "plane": QColor(100, 50, 0, 200),  # Brown with transparency
    "drill": QColor(255, 50, 50, 200),  # Red with transparency
    "route": QColor(255, 100, 0, 200),  # Orange with transparency
    "padstack": QColor(0, 200, 200, 200),  # Cyan with transparency
    "viastack": QColor(200, 0, 200, 200),  # Magenta with transparency
    "designRule": QColor(128, 0, 200, 150),  # Purple with transparency
    "dimension": QColor(100, 200, 255, 180),  # Light blue with transparency
    "keepoutRoute": QColor(255, 100, 100, 120),  # Light red with transparency
    "keepoutDrill": QColor(255, 150, 50, 120),  # Light orange with transparency
    "keepoutComponent": QColor(100, 255, 100, 120),  # Light green with transparency
    "heightLimit": QColor(100, 100, 255, 120)  # Light blue with transparency
}


class PCBLayer:
    """Represents a single PCB layer with properties and content"""

    def __init__(self, name: str, layer_type: str, side: str, layer_id: int):
        self.name = name
        self.type = layer_type
        self.side = side  # top, bottom, other, system
        self.id = layer_id
        self.visible = True
        self.locked = False
        self.color = LAYER_COLORS.get(layer_type, QColor(150, 150, 150, 150))

        # Create a QPixmap for the layer content
        self.pixmap = QPixmap(800, 600)
        self.pixmap.fill(Qt.transparent)

        # Add some example content for visualization
        self._add_sample_content()

    def _add_sample_content(self):
        """Add sample visual content to the layer for demonstration"""
        painter = QPainter(self.pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(self.color, 2)
        painter.setPen(pen)
        brush = QBrush(self.color)

        # Different sample content based on layer type
        if self.type == "board":
            # Fill the entire board
            painter.fillRect(50, 50, 700, 500, brush)
        elif self.type == "silk":
            # Add some text-like elements
            for i in range(5):
                painter.drawLine(100 + i * 100, 100, 150 + i * 100, 100)
                painter.drawLine(100 + i * 100, 120, 170 + i * 100, 120)
        elif self.type in ["electric", "route"]:
            # Add some traces
            for i in range(3):
                painter.drawLine(100, 200 + i * 50, 700, 200 + i * 50)
                painter.drawLine(100 + i * 50, 300, 100 + i * 50, 500)
        elif self.type == "drill":
            # Add some drill holes
            for x in range(150, 650, 100):
                for y in range(150, 450, 100):
                    painter.drawEllipse(x - 5, y - 5, 10, 10)
        elif self.type == "plane":
            # Add a ground plane
            painter.setOpacity(0.3)
            painter.fillRect(100, 350, 600, 200, brush)
        elif self.type in ["keepoutRoute", "keepoutDrill", "keepoutComponent"]:
            # Add some keepout zones
            painter.setOpacity(0.4)
            if self.side == "top":
                painter.fillRect(200, 100, 200, 150, brush)
            else:
                painter.fillRect(400, 300, 250, 200, brush)

        painter.end()

    def render(self, painter: QPainter) -> None:
        """Render the layer to the given painter"""
        if self.visible:
            painter.drawPixmap(0, 0, self.pixmap)


class PCBLayerManager(QWidget):
    """Manages the PCB layers and rendering"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create main PCB drawing surface
        self.pcb_size = QSize(800, 600)
        self.setMinimumSize(self.pcb_size)

        # Initialize layer collections
        self.next_layer_id = 0
        self.layers: Dict[str, PCBLayer] = {}

        # Create all layers from the section definitions
        # Top layers
        for layer_type in ["silk", "electric", "solder", "paste", "assembly", "designRule", "dimension"]:
            layer_name = f"top.{layer_type}"
            self.layers[layer_name] = PCBLayer(layer_name, layer_type, "top", self.next_layer_id)
            self.next_layer_id += 1

        # Additional top layers shown in the image
        for layer_type in ["route", "plane", "padstack", "viastack"]:
            layer_name = f"top.{layer_type}"
            self.layers[layer_name] = PCBLayer(layer_name, layer_type, "top", self.next_layer_id)
            self.next_layer_id += 1

        # Top keepout layers
        for layer_type in ["keepoutRoute", "keepoutDrill", "keepoutComponent", "heightLimit"]:
            layer_name = f"top.{layer_type}"
            self.layers[layer_name] = PCBLayer(layer_name, layer_type, "top", self.next_layer_id)
            self.next_layer_id += 1

        # Bottom layers
        for layer_type in ["silk", "electric", "solder", "paste", "assembly"]:
            layer_name = f"bottom.{layer_type}"
            self.layers[layer_name] = PCBLayer(layer_name, layer_type, "bottom", self.next_layer_id)
            self.next_layer_id += 1

        # Other layers
        self.layers["other.board"] = PCBLayer("other.board", "board", "other", self.next_layer_id)
        self.next_layer_id += 1

        # Other keepout and design rule layers
        for layer_type in ["keepoutRoute", "keepoutDrill", "keepoutComponent", "heightLimit", "designRule",
                           "dimension"]:
            layer_name = f"other.{layer_type}"
            self.layers[layer_name] = PCBLayer(layer_name, layer_type, "other", self.next_layer_id)
            self.next_layer_id += 1

        # System layers
        self.layers["system.drill"] = PCBLayer("system.drill", "drill", "system", self.next_layer_id)
        self.next_layer_id += 1

        # Current selected layer
        self.current_layer = None
        self.current_layer_only_mode = False

    def set_layer_visibility(self, side: str, layer_type: str, is_visible: bool) -> None:
        """Set visibility for a specific layer"""
        layer_name = f"{side}.{layer_type}"
        if layer_name in self.layers:
            self.layers[layer_name].visible = is_visible
            self.update()  # Trigger a repaint

    def set_layer_locked(self, side: str, layer_type: str, is_locked: bool) -> None:
        """Set locked status for a specific layer"""
        layer_name = f"{side}.{layer_type}"
        if layer_name in self.layers:
            self.layers[layer_name].locked = is_locked

    def set_current_layer_only(self, enabled: bool) -> None:
        """Toggle 'Current Layer Only' mode"""
        self.current_layer_only_mode = enabled
        self.update()  # Trigger a repaint

    def set_current_layer(self, layer_name: str) -> None:
        """Set the current active layer"""
        if layer_name in self.layers:
            self.current_layer = self.layers[layer_name]
            self.update()  # Trigger a repaint


def paintEvent(self, event) -> None:
    painter = QPainter(self)
    painter.fillRect(self.rect(), BLACK)  # Chỉ fill nền đen



class LayerPanel(QScrollArea):
    """Panel for controlling layer visibility and properties"""

    layer_changed = pyqtSignal(str, bool)  # Signal to notify when layer visibility changes

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create layer sections
        self.create_layer_section("Top Layers", "top")
        self.create_layer_section("Bottom Layers", "bottom")
        self.create_layer_section("Other Layers", "other")
        self.create_layer_section("System Layers", "system")

        # Layer manager reference
        self.layer_manager = None

    def create_layer_section(self, title: str, side: str) -> None:
        """Create a section of layer controls"""
        group = QGroupBox(title)
        group_layout = QVBoxLayout()
        group.setLayout(group_layout)

        # Add different layer types based on side
        if side == "top":
            layer_types = ["silk", "electric", "solder", "paste", "assembly",
                           "route", "plane", "padstack", "viastack",
                           "keepoutRoute", "keepoutDrill", "keepoutComponent", "heightLimit",
                           "designRule", "dimension"]
        elif side == "bottom":
            layer_types = ["silk", "electric", "solder", "paste", "assembly"]
        elif side == "other":
            layer_types = ["board", "keepoutRoute", "keepoutDrill", "keepoutComponent",
                           "heightLimit", "designRule", "dimension"]
        else:  # system
            layer_types = ["drill"]

        # Create controls for each layer
        for layer_type in layer_types:
            # Create a horizontal layout for the layer row
            row_layout = QHBoxLayout()

            # Radio button for selecting current layer
            radio = QRadioButton()
            radio.setObjectName(f"radio_{side}.{layer_type}")
            radio.clicked.connect(lambda checked, s=side, t=layer_type: self.set_current_layer(s, t))
            row_layout.addWidget(radio)

            # Checkbox for visibility
            visible_cb = QCheckBox(f"{layer_type}")
            visible_cb.setObjectName(f"visible_{side}.{layer_type}")
            visible_cb.setChecked(True)  # Default to visible
            visible_cb.toggled.connect(
                lambda checked, s=side, t=layer_type: self.toggle_layer_visibility(s, t, checked))
            row_layout.addWidget(visible_cb)

            # Checkbox for locked status
            locked_cb = QCheckBox("Lock")
            locked_cb.setObjectName(f"locked_{side}.{layer_type}")
            locked_cb.toggled.connect(lambda checked, s=side, t=layer_type: self.toggle_layer_locked(s, t, checked))
            row_layout.addWidget(locked_cb)

            # Color indicator (could be improved with a custom widget)
            color_label = QLabel()
            color_label.setMinimumSize(16, 16)
            color_label.setMaximumSize(16, 16)
            color_label.setStyleSheet(f"background-color: {LAYER_COLORS.get(layer_type, GRAY).name()}")
            row_layout.addWidget(color_label)

            group_layout.addLayout(row_layout)

        self.main_layout.addWidget(group)

    def set_layer_manager(self, manager: PCBLayerManager) -> None:
        """Connect this panel to a layer manager"""
        self.layer_manager = manager

    def toggle_layer_visibility(self, side: str, layer_type: str, is_visible: bool) -> None:
        """Handle layer visibility toggle"""
        if self.layer_manager:
            self.layer_manager.set_layer_visibility(side, layer_type, is_visible)
            self.layer_changed.emit(f"{side}.{layer_type}", is_visible)

    def toggle_layer_locked(self, side: str, layer_type: str, is_locked: bool) -> None:
        """Handle layer locked toggle"""
        if self.layer_manager:
            self.layer_manager.set_layer_locked(side, layer_type, is_locked)

    def set_current_layer(self, side: str, layer_type: str) -> None:
        """Handle current layer selection"""
        if self.layer_manager:
            self.layer_manager.set_current_layer(f"{side}.{layer_type}")

    def toggle_current_layer_only(self, enabled: bool) -> None:
        """Handle 'Current Layer Only' mode toggle"""
        if self.layer_manager:
            self.layer_manager.set_current_layer_only(enabled)


class PCBDesignerApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Set up the main window
        self.setWindowTitle("PyQt5 PCB Layer Manager")
        self.setGeometry(100, 100, 1200, 700)

        # Create main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create PCB layer manager (right side)
        self.layer_manager = PCBLayerManager()

        # Create layer panel (left side)
        self.layer_panel = LayerPanel()
        self.layer_panel.set_layer_manager(self.layer_manager)
        self.layer_panel.setMaximumWidth(300)

        # Add widgets to main layout
        main_layout.addWidget(self.layer_panel)
        main_layout.addWidget(self.layer_manager)


def main():
    app = QApplication(sys.argv)
    window = PCBDesignerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()