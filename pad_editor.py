# modules/pad_editor.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QGroupBox, QGraphicsScene, QGraphicsView,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPathItem, QMessageBox,
    QGraphicsLineItem, QGraphicsTextItem
)
from PyQt5.QtGui import QPen, QBrush, QColor, QPainterPath, QPainter
from PyQt5.QtCore import Qt, QRectF

# Giả sử Pad là một class bạn định nghĩa ở nơi khác
try:
    from pad import Pad  # nếu bạn có một module riêng cho Pad
except ImportError:
    class Pad:
        pass  # placeholder nếu không có class Pad


class PadEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pad Editor")
        self.current_pad = None
        self.editing_existing = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Pad type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Pad Type:"))
        self.pad_type_combo = QComboBox()
        self.pad_type_combo.addItems(["THT (Through Hole)", "SMD (Surface Mount)", "NPTH (Non-Plated)"])
        self.pad_type_combo.currentIndexChanged.connect(self.update_pad_preview)
        type_layout.addWidget(self.pad_type_combo)
        layout.addLayout(type_layout)

        # Pad ID input
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Pad ID:"))
        self.pad_id_edit = QLineEdit("1")
        id_layout.addWidget(self.pad_id_edit)
        layout.addLayout(id_layout)

        # Pad shape selection
        shape_layout = QHBoxLayout()
        shape_layout.addWidget(QLabel("Shape:"))
        self.pad_shape_combo = QComboBox()
        self.pad_shape_combo.addItems(["Circle", "Rectangle", "Oval", "Custom"])
        self.pad_shape_combo.currentIndexChanged.connect(self.on_shape_changed)
        shape_layout.addWidget(self.pad_shape_combo)
        layout.addLayout(shape_layout)

        # Dimensions
        dims_group = QGroupBox("Dimensions")
        dims_layout = QGridLayout()

        # Width (Diameter for Circle)
        self.width_label = QLabel("Width:")
        dims_layout.addWidget(self.width_label, 0, 0)
        self.width_edit = QLineEdit("1.5")
        self.width_edit.textChanged.connect(self.on_width_changed)
        dims_layout.addWidget(self.width_edit, 0, 1)
        dims_layout.addWidget(QLabel("mm"), 0, 2)

        # Height
        self.height_label = QLabel("Height:")
        dims_layout.addWidget(self.height_label, 1, 0)
        self.height_edit = QLineEdit("1.5")
        self.height_edit.setEnabled(False)  # Disabled by default since Circle is the default shape
        dims_layout.addWidget(self.height_edit, 1, 1)
        dims_layout.addWidget(QLabel("mm"), 1, 2)

        # Hole diameter (for THT)
        dims_layout.addWidget(QLabel("Hole Diameter:"), 2, 0)
        self.hole_diameter_edit = QLineEdit("0.8")
        dims_layout.addWidget(self.hole_diameter_edit, 2, 1)
        dims_layout.addWidget(QLabel("mm"), 2, 2)

        # Corner radius (for rectangle)
        self.corner_radius_label = QLabel("Corner Radius:")
        dims_layout.addWidget(self.corner_radius_label, 3, 0)
        self.corner_radius_edit = QLineEdit("0")
        self.corner_radius_edit.setEnabled(False)  # Disabled by default since Circle is the default shape
        dims_layout.addWidget(self.corner_radius_edit, 3, 1)
        dims_layout.addWidget(QLabel("mm"), 3, 2)

        dims_group.setLayout(dims_layout)
        layout.addWidget(dims_group)

        # Layer configuration
        layer_group = QGroupBox("Layers")
        layer_layout = QVBoxLayout()

        # Copper layers
        self.top_copper_check = QCheckBox("Top Copper")
        self.top_copper_check.setChecked(True)
        layer_layout.addWidget(self.top_copper_check)

        self.bottom_copper_check = QCheckBox("Bottom Copper")
        layer_layout.addWidget(self.bottom_copper_check)

        # Mask layers
        self.top_mask_check = QCheckBox("Top Solder Mask")
        self.top_mask_check.setChecked(True)
        layer_layout.addWidget(self.top_mask_check)

        self.bottom_mask_check = QCheckBox("Bottom Solder Mask")
        layer_layout.addWidget(self.bottom_mask_check)

        # Paste layers
        self.top_paste_check = QCheckBox("Top Paste")
        self.top_paste_check.setChecked(True)
        layer_layout.addWidget(self.top_paste_check)

        self.bottom_paste_check = QCheckBox("Bottom Paste")
        layer_layout.addWidget(self.bottom_paste_check)

        layer_group.setLayout(layer_layout)
        layout.addWidget(layer_group)

        # Thermal settings for THT pads
        thermal_group = QGroupBox("Thermal Relief")
        thermal_layout = QGridLayout()

        self.thermal_enabled = QCheckBox("Enable Thermal Relief")
        self.thermal_enabled.setChecked(True)
        thermal_layout.addWidget(self.thermal_enabled, 0, 0, 1, 2)

        thermal_layout.addWidget(QLabel("Spoke Width:"), 1, 0)
        self.thermal_spoke_width = QLineEdit("0.3")
        thermal_layout.addWidget(self.thermal_spoke_width, 1, 1)

        thermal_layout.addWidget(QLabel("Gap Width:"), 2, 0)
        self.thermal_gap_width = QLineEdit("0.7")
        thermal_layout.addWidget(self.thermal_gap_width, 2, 1)

        thermal_group.setLayout(thermal_layout)
        layout.addWidget(thermal_group)

        # Preview area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.pad_preview_scene = QGraphicsScene()
        self.pad_preview_view = QGraphicsView(self.pad_preview_scene)
        self.pad_preview_view.setMinimumSize(200, 200)
        preview_layout.addWidget(self.pad_preview_view)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_pad)
        button_layout.addWidget(self.apply_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect signals for updating preview
        self.width_edit.textChanged.connect(self.update_pad_preview)
        self.height_edit.textChanged.connect(self.update_pad_preview)
        self.hole_diameter_edit.textChanged.connect(self.update_pad_preview)
        self.corner_radius_edit.textChanged.connect(self.update_pad_preview)
        self.pad_id_edit.textChanged.connect(self.update_pad_preview)

        # Connect thermal relief controls
        self.thermal_enabled.toggled.connect(self.update_pad_preview)
        self.thermal_spoke_width.textChanged.connect(self.update_pad_preview)
        self.thermal_gap_width.textChanged.connect(self.update_pad_preview)

        # Initial preview
        self.update_pad_preview()

    def update_pad_preview(self):
        """Update the pad preview based on current settings"""
        self.pad_preview_scene.clear()

        try:
            # Scale factors for preview (match the actual pad scale)
            scale = 100  # Match the scale used in Pad class
            width = float(self.width_edit.text()) * scale
            height = float(self.height_edit.text()) * scale
            hole_diameter = float(self.hole_diameter_edit.text()) * scale
            corner_radius = float(self.corner_radius_edit.text()) * scale

            # Get pad ID
            pad_id = self.pad_id_edit.text()

        except ValueError:
            # If any conversion fails, use default values
            width = 150
            height = 150
            hole_diameter = 80
            corner_radius = 0
            pad_id = "1"

        pad_type = self.pad_type_combo.currentText()
        pad_shape = self.pad_shape_combo.currentText()

        # Layer colors (matching the main application)
        layer_colors = {
            'top_copper': QColor(0, 100, 255, 180),  # Blue
            'bottom_copper': QColor(0, 180, 0, 180),  # Green
            'top_mask': QColor(255, 255, 255, 200),  # White
            'bottom_mask': QColor(180, 180, 180, 180),  # Gray
            'top_paste': QColor(255, 200, 0, 180),  # Yellow
            'bottom_paste': QColor(255, 100, 0, 200),  # Orange
        }

        # Map layer checkboxes to layer names
        layer_checks = {
            'top_copper': self.top_copper_check,
            'bottom_copper': self.bottom_copper_check,
            'top_mask': self.top_mask_check,
            'bottom_mask': self.bottom_mask_check,
            'top_paste': self.top_paste_check,
            'bottom_paste': self.bottom_paste_check
        }

        # Draw layers from bottom to top (match the order in actual pad)
        layer_order = ['bottom_paste', 'bottom_copper', 'bottom_mask',
                       'top_mask', 'top_copper', 'top_paste']

        for layer_name in layer_order:
            if layer_checks[layer_name].isChecked():
                color = layer_colors[layer_name]

                # Create pad shape based on selected type
                if pad_shape == "Circle":
                    diameter = max(width, height)
                    pad_item = QGraphicsEllipseItem(-diameter / 2, -diameter / 2, diameter, diameter)
                elif pad_shape == "Rectangle":
                    if corner_radius > 0:
                        path = QPainterPath()
                        path.addRoundedRect(-width / 2, -height / 2, width, height,
                                            corner_radius, corner_radius)
                        pad_item = QGraphicsPathItem(path)
                    else:
                        pad_item = QGraphicsRectItem(-width / 2, -height / 2, width, height)
                elif pad_shape == "Oval":
                    pad_item = QGraphicsEllipseItem(-width / 2, -height / 2, width, height)
                else:  # Custom - use rectangle for now
                    pad_item = QGraphicsRectItem(-width / 2, -height / 2, width, height)

                # Set appearance for this layer
                pad_item.setPen(QPen(color, 2))
                pad_item.setBrush(QBrush(color))
                self.pad_preview_scene.addItem(pad_item)

        # Draw hole for THT pads
        if "THT" in pad_type and hole_diameter > 0:
            # Draw hole
            hole_item = QGraphicsEllipseItem(-hole_diameter / 2, -hole_diameter / 2,
                                             hole_diameter, hole_diameter)
            hole_item.setPen(QPen(Qt.black, 1))
            hole_item.setBrush(QBrush(Qt.white))
            self.pad_preview_scene.addItem(hole_item)

            # Draw thermal relief if enabled
            if self.thermal_enabled.isChecked():
                try:
                    spoke_width = float(self.thermal_spoke_width.text()) * scale
                    gap_width = float(self.thermal_gap_width.text()) * scale

                    # Draw thermal relief spokes (match the actual pad rendering)
                    for angle in [0, 90, 180, 270]:
                        spoke = QGraphicsLineItem()
                        # Draw spoke from hole edge to gap width, not to pad edge
                        spoke.setLine(hole_diameter / 2, 0, gap_width / 2, 0)
                        spoke.setPen(QPen(layer_colors['top_copper'], spoke_width))
                        spoke.setRotation(angle)
                        self.pad_preview_scene.addItem(spoke)
                except ValueError:
                    pass  # Skip thermal relief if values are invalid

        # Add pad ID label
        if pad_id:
            text_item = QGraphicsTextItem(pad_id)
            text_item.setDefaultTextColor(Qt.black)
            # Center the text on the pad
            text_bounds = text_item.boundingRect()
            text_item.setPos(-text_bounds.width() / 2, -text_bounds.height() / 2)
            self.pad_preview_scene.addItem(text_item)

        # Center the view on the pad and scale appropriately
        margin = max(width, height) * 0.2  # Add 20% margin
        self.pad_preview_view.setSceneRect(QRectF(-width / 2 - margin, -height / 2 - margin,
                                                  width + 2 * margin, height + 2 * margin))
        self.pad_preview_view.centerOn(0, 0)
        self.pad_preview_view.setRenderHint(QPainter.Antialiasing)

    def apply_pad(self):
        try:
            # Create a pad with the current settings
            pad_data = {
                'type': self.pad_type_combo.currentText(),
                'shape': self.pad_shape_combo.currentText(),
                'width': float(self.width_edit.text()),
                'height': float(self.height_edit.text()),
                'hole_diameter': float(self.hole_diameter_edit.text()),
                'corner_radius': float(self.corner_radius_edit.text()),
                'id': self.pad_id_edit.text(),  # Add pad ID to the data
                'layers': {
                    'top_copper': self.top_copper_check.isChecked(),
                    'bottom_copper': self.bottom_copper_check.isChecked(),
                    'top_mask': self.top_mask_check.isChecked(),
                    'bottom_mask': self.bottom_mask_check.isChecked(),
                    'top_paste': self.top_paste_check.isChecked(),
                    'bottom_paste': self.bottom_paste_check.isChecked()
                },
                'thermal': {
                    'enabled': self.thermal_enabled.isChecked(),
                    'spoke_width': float(self.thermal_spoke_width.text()),
                    'gap_width': float(self.thermal_gap_width.text())
                }
            }

            # Validate the data
            if pad_data['width'] <= 0 or pad_data['height'] <= 0:
                raise ValueError("Width and height must be positive values")
            if pad_data['hole_diameter'] < 0:
                raise ValueError("Hole diameter cannot be negative")
            if pad_data['corner_radius'] < 0:
                raise ValueError("Corner radius cannot be negative")

            self.current_pad = pad_data
            self.accept()
            return pad_data

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def set_pad_data(self, pad_data):
        """Set the editor's values from existing pad data"""
        self.editing_existing = True
        self.setWindowTitle("Edit Pad")
        self.apply_button.setText("Update")

        # Set pad ID
        if 'id' in pad_data:
            self.pad_id_edit.setText(str(pad_data['id']))

        # Set pad type
        if 'type' in pad_data:
            index = self.pad_type_combo.findText(pad_data['type'])
            if index >= 0:
                self.pad_type_combo.setCurrentIndex(index)

        # Set pad shape
        if 'shape' in pad_data:
            index = self.pad_shape_combo.findText(pad_data['shape'])
            if index >= 0:
                self.pad_shape_combo.setCurrentIndex(index)

        # Set dimensions
        if 'width' in pad_data:
            self.width_edit.setText(str(pad_data['width']))
        if 'height' in pad_data:
            self.height_edit.setText(str(pad_data['height']))
        if 'hole_diameter' in pad_data:
            self.hole_diameter_edit.setText(str(pad_data['hole_diameter']))
        if 'corner_radius' in pad_data:
            self.corner_radius_edit.setText(str(pad_data['corner_radius']))

        # Set layers
        if 'layers' in pad_data:
            layers = pad_data['layers']
            self.top_copper_check.setChecked(layers.get('top_copper', False))
            self.bottom_copper_check.setChecked(layers.get('bottom_copper', False))
            self.top_mask_check.setChecked(layers.get('top_mask', False))
            self.bottom_mask_check.setChecked(layers.get('bottom_mask', False))
            self.top_paste_check.setChecked(layers.get('top_paste', False))
            self.bottom_paste_check.setChecked(layers.get('bottom_paste', False))

        # Set thermal relief settings
        if 'thermal' in pad_data:
            thermal = pad_data['thermal']
            self.thermal_enabled.setChecked(thermal.get('enabled', False))
            self.thermal_spoke_width.setText(str(thermal.get('spoke_width', 0.3)))
            self.thermal_gap_width.setText(str(thermal.get('gap_width', 0.2)))

        # Update preview
        self.update_pad_preview()

    def on_width_changed(self, new_width):
        """Handle width changes for circle shape"""
        if self.pad_shape_combo.currentText() == "Circle":
            self.height_edit.setText(new_width)

    def on_shape_changed(self):
        """Handle shape selection changes"""
        current_shape = self.pad_shape_combo.currentText()

        # Update labels and enable/disable fields based on shape
        if current_shape == "Circle":
            self.width_label.setText("Diameter:")
            self.height_label.setText("Height: (= Diameter)")
            self.corner_radius_label.setText("Corner Radius: (N/A)")
            self.height_edit.setEnabled(False)
            self.corner_radius_edit.setEnabled(False)
            self.height_edit.setText(self.width_edit.text())
            self.corner_radius_edit.setText("0")
        elif current_shape == "Rectangle":
            self.width_label.setText("Width:")
            self.height_label.setText("Height:")
            self.corner_radius_label.setText("Corner Radius:")
            self.height_edit.setEnabled(True)
            self.corner_radius_edit.setEnabled(True)
        elif current_shape == "Oval":
            self.width_label.setText("Width:")
            self.height_label.setText("Height:")
            self.corner_radius_label.setText("Corner Radius: (N/A)")
            self.height_edit.setEnabled(True)
            self.corner_radius_edit.setEnabled(False)
            self.corner_radius_edit.setText("0")
        else:  # Custom
            self.width_label.setText("Width:")
            self.height_label.setText("Height:")
            self.corner_radius_label.setText("Corner Radius:")
            self.height_edit.setEnabled(True)
            self.corner_radius_edit.setEnabled(True)

        self.update_pad_preview()
