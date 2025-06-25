import  traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QTreeWidget, QTreeWidgetItem,
    QWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QTabWidget,
    QGraphicsScene, QListWidget, QToolBar, QAction, QMessageBox, QDialog, QListWidgetItem, QGraphicsItem,
    QActionGroup, QGraphicsLineItem, QGroupBox, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem,
    QSpinBox)
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPen, QColor, QPainter
from PyQt5.QtPrintSupport import QPrinter

from drawing import DrawingApp
from pad_editor import PadEditor
from pad import Pad
from layer_manager import LayerManager
from layer_setting import LayerSetting
from grid import GridLine, GridText


# Layer type colors and groups
LAYER_GROUPS = {
    "Copper": {
        "top_copper": QColor(0, 100, 255, 180),  # Blue with transparency
        "bottom_copper": QColor(0, 180, 0, 180),  # Green with transparency
        "plane": QColor(100, 50, 0, 200),  # Brown with transparency
    },
    "Mask": {
        "top_mask": QColor(255, 255, 255, 200),  # White with transparency
        "bottom_mask": QColor(180, 180, 180, 180),  # Gray with transparency
    },
    "Paste": {
        "top_paste": QColor(255, 200, 0, 180),  # Yellow with transparency
        "bottom_paste": QColor(255, 100, 0, 200),  # Orange with transparency
    },
    "Documentation": {
        "silk": QColor(255, 255, 255, 200),  # White with transparency
        "assembly": QColor(255, 200, 0, 180),  # Yellow with transparency
        "dimension": QColor(100, 200, 255, 180),  # Light blue with transparency
    },
    "Manufacturing": {
        "drill": QColor(255, 50, 50, 200),  # Red with transparency
        "route": QColor(255, 100, 0, 200),  # Orange with transparency
    },
    "Design Rules": {
        "designRule": QColor(128, 0, 200, 150),  # Purple with transparency
        "keepoutRoute": QColor(255, 100, 100, 120),  # Light red with transparency
        "keepoutDrill": QColor(255, 150, 50, 120),  # Light orange with transparency
        "keepoutComponent": QColor(100, 255, 100, 120),  # Light green with transparency
        "heightLimit": QColor(100, 100, 255, 120),  # Light blue with transparency
    },
    "Components": {
        "padstack": QColor(0, 200, 200, 200),  # Cyan with transparency
        "viastack": QColor(200, 0, 200, 200),  # Magenta with transparency
    }
}

# Flatten layer colors for backward compatibility
LAYER_COLORS = {}
for group in LAYER_GROUPS.values():
    LAYER_COLORS.update(group)

class main_app(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle('PCB Design Studio')
            self.setGeometry(100, 100, 1200, 800)
            self.drawing_app = DrawingApp()  # Create an instance of DrawingApp
            self.drawing_app.setParent(self)  # Set the parent explicitly
            self.init_ui()  # Call init_ui method
            self.layer_manager = LayerManager(scene=self.drawing_app.scene, layers_widget=self.layers_widget)
            self.add_default_layers()
            
            # Connect layer manager signals
            self.layer_manager.layer_double_clicked.connect(self.on_layer_double_clicked)
            
            # Set initial drawing mode to select
            self.set_drawing_mode("select")
        except Exception as e:
            # Fallback error handling
            print(f"Initialization Error: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(None, "Initialization Error", str(e))

    def init_ui(self):
        try:
            # Create main layout components
            self.create_menu_bar()
            self.create_toolbar()
            self.create_left_sidebar()
            self.create_right_sidebar()
            self.create_central_canvas()
            self.create_bottom_panel()
        except Exception as e:
            # Fallback error handling
            print(f"UI Creation Error: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(None, "UI Creation Error", str(e))

    def create_menu_bar(self):
        # Create menubar if it doesn't exist
        if not hasattr(self, 'menubar'):
            self.menubar = self.menuBar()

        # File Menu
        file_menu = self.menubar.addMenu('File')
        new_project_action = QAction('New Project', self)
        open_project_action = QAction('Open Project', self)
        save_action = QAction('Save', self)
        export_action = QAction('Export', self)
        export_action.triggered.connect(lambda: self.export_to_pdf("my_drawing.pdf"))
        file_menu.addAction(new_project_action)
        file_menu.addAction(open_project_action)
        file_menu.addAction(save_action)
        file_menu.addAction(export_action)

        # Edit Menu
        edit_menu = self.menubar.addMenu('Edit')
        # select_all_action = QAction('Select All', self)
        # select_all_action.setShortcut('Ctrl+A')
        # select_all_action.triggered.connect(self.select_all_items)
        
        duplicate_action = QAction('Duplicate', self)
        duplicate_action.setShortcut('Ctrl+D')
        duplicate_action.triggered.connect(self.duplicate_selected)
        
        undo_action = QAction('Undo', self)
        redo_action = QAction('Redo', self)
        # edit_menu.addAction(select_all_action)
        edit_menu.addAction(duplicate_action)
        edit_menu.addSeparator()
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)

        # Design Menu
        design_menu = self.menubar.addMenu('Design')
        create_footprint_action = QAction('Create Footprint', self)
        layer_manager_menu = design_menu.addMenu('Layer Manager')
        add_layer_action = QAction('Add Layer', self)
        layer_setting_action = QAction('Layer Setting', self)
        add_layer_action.triggered.connect(lambda: self.add_custom_layer())
        layer_setting_action.triggered.connect(lambda: self.open_layer_setting_dialog())
        layer_manager_menu.addAction(add_layer_action)
        layer_manager_menu.addAction(layer_setting_action)
        design_menu.addAction(create_footprint_action)

    def create_toolbar(self):
        toolbar = QToolBar('Design Tools')
        self.addToolBar(toolbar)

        # Selection tools
        select_action = QAction('Select', self)
        select_action.setCheckable(True)
        select_action.setChecked(True)  # Set select mode as initially checked
        select_action.triggered.connect(lambda: self.set_drawing_mode("select"))
        toolbar.addAction(select_action)

        # select_all_action = QAction('Select All', self)
        # select_all_action.setShortcut('Ctrl+A')
        # select_all_action.triggered.connect(self.select_all_items)
        # toolbar.addAction(select_all_action)

        # Delete action
        delete_action = QAction('Delete', self)
        delete_action.triggered.connect(self.delete_selected)
        delete_action.setShortcut('Delete')  # Add keyboard shortcut
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        # Create action group for drawing tools to make them mutually exclusive
        drawing_tools = QActionGroup(self)
        drawing_tools.setExclusive(True)

        # Add select action to the group
        drawing_tools.addAction(select_action)

        # Drawing tools
        draw_line_action = QAction('Draw Line', self)
        draw_line_action.setCheckable(True)
        draw_line_action.triggered.connect(lambda: self.set_drawing_mode("line"))
        drawing_tools.addAction(draw_line_action)
        toolbar.addAction(draw_line_action)

        draw_rect_action = QAction('Draw Rectangle', self)
        draw_rect_action.setCheckable(True)
        draw_rect_action.triggered.connect(lambda: self.set_drawing_mode("rect"))
        drawing_tools.addAction(draw_rect_action)
        toolbar.addAction(draw_rect_action)

        draw_circle_action = QAction('Draw Circle', self)
        draw_circle_action.setCheckable(True)
        draw_circle_action.triggered.connect(lambda: self.set_drawing_mode("circle"))
        drawing_tools.addAction(draw_circle_action)
        toolbar.addAction(draw_circle_action)

        color_action = QAction('Choose Color', self)
        color_action.triggered.connect(self.choose_drawing_color)
        toolbar.addAction(color_action)

        toolbar.addSeparator()
        pad_editor_action = QAction('Pad Editor', self)
        pad_editor_action.triggered.connect(self.show_pad_editor)
        toolbar.addAction(pad_editor_action)

        # Add line thickness control
        toolbar.addSeparator()
        thickness_label = QLabel('Line Thickness:')
        thickness_spin = QSpinBox()
        thickness_spin.setRange(1, 20)
        thickness_spin.setValue(self.drawing_app.line_thickness)
        thickness_spin.setToolTip('Set line thickness for drawing')
        thickness_spin.valueChanged.connect(self.drawing_app.set_line_thickness)
        toolbar.addWidget(thickness_label)
        toolbar.addWidget(thickness_spin)

    def set_drawing_mode(self, mode):
        """Set the drawing mode and update cursor and drag mode"""
        if hasattr(self, 'drawing_app'):
            self.drawing_app.drawing_mode = mode
            self.drawing_app.set_cursor_for_mode()  # Update cursor based on mode

    def choose_drawing_color(self):
        if hasattr(self, 'drawing_app'):
            self.drawing_app.choose_color()

    def create_central_canvas(self):
        self.canvas_widget = QTabWidget()

        # Set up the scene for DrawingApp
        scene = QGraphicsScene(self)
        # Set scene rect centered around (0,0)
        scene.setSceneRect(-2000, -1000, 4000, 2000)  # Width: 4000, Height: 2000
        self.drawing_app.scene = scene
        self.drawing_app.drawing_window.setScene(scene)

        self.add_grid(scene)
        self.canvas_widget.addTab(self.drawing_app.drawing_window, 'PCB Design')
        self.setCentralWidget(self.canvas_widget)

    def add_grid(self, scene):
        grid_color = QColor(240, 240, 240)
        axis_color = QColor(200, 200, 200)
        grid_spacing = 10
        
        # Add grid lines
        for x in range(-2000, 2000 + 1, grid_spacing):  # From -2000 to +2000
            # Add coordinate labels every 100 pixels
            if x % 100 == 0:
                text = GridText(str(x))
                text.setPos(x, 0)
                text.setDefaultTextColor(axis_color)
                text.setScale(0.8)
                scene.addItem(text)
            line = GridLine(x, -1000, x, 1000, QPen(grid_color))
            scene.addItem(line)
            
        for y in range(-1000, 1000 + 1, grid_spacing):  # From -1000 to +1000
            # Add coordinate labels every 100 pixels
            if y % 100 == 0:
                text = GridText(str(y))
                text.setPos(0, y)
                text.setDefaultTextColor(axis_color)
                text.setScale(0.8)
                scene.addItem(text)
            line = GridLine(-2000, y, 2000, y, QPen(grid_color))
            scene.addItem(line)

        # Add X and Y axes with darker color
        x_axis = GridLine(-2000, 0, 2000, 0, QPen(QColor(150, 150, 150), 2))
        y_axis = GridLine(0, -1000, 0, 1000, QPen(QColor(150, 150, 150), 2))
        scene.addItem(x_axis)
        scene.addItem(y_axis)

        # Add center marker
        marker_size = 10
        
        # Vertical center line
        center_v = GridLine(0, -marker_size, 
                          0, marker_size, 
                          QPen(QColor(255, 0, 0), 2))
        # Horizontal center line
        center_h = GridLine(-marker_size, 0,
                          marker_size, 0,
                          QPen(QColor(255, 0, 0), 2))
        scene.addItem(center_v)
        scene.addItem(center_h)
    

    def create_left_sidebar(self):
        dock = QDockWidget('Component Library', self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        tree = QTreeWidget()
        tree.setHeaderLabel('Components')
        categories = [
            ('Passive', ['Resistor', 'Capacitor', 'Inductor']),
            ('Active', ['Transistor', 'IC', 'Diode']),
            ('Connectors', ['USB', 'HDMI', 'Pin Header'])
        ]
        for category, components in categories:
            cat_item = QTreeWidgetItem(tree, [category])
            for component in components:
                QTreeWidgetItem(cat_item, [component])
        dock.setWidget(tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def create_right_sidebar(self):
        layer_dock = QDockWidget('Layers', self)
        layer_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # Create a tree widget for layers
        self.layers_widget = QTreeWidget()
        self.layers_widget.setHeaderLabel('Layers')
        
        # Connect signals
        self.layers_widget.itemChanged.connect(self.on_layer_checked)
        self.layers_widget.itemSelectionChanged.connect(self.on_layer_selected)
        
        layer_dock.setWidget(self.layers_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, layer_dock)

    def on_layer_checked(self, item):
        """Handle layer visibility changes"""
        if not item.parent():  # Skip if this is a group item
            return
            
        layer_name = item.text(0)
        if layer_name in self.layer_manager.layers:
            # Skip if layer manager is already updating
            if self.layer_manager.is_updating:
                return
                
            # Get the current state without triggering the event
            is_checked = item.checkState(0) == Qt.Checked
            
            # Check if layer is locked
            if self.layer_manager.is_layer_locked(layer_name):
                # Force checked state for locked layers
                item.setCheckState(0, Qt.Checked)
                return
                
            # Update layer visibility through layer manager
            if is_checked:
                self.layer_manager.show_layer(layer_name)
            else:
                self.layer_manager.hide_layer(layer_name)

    def on_layer_selected(self):
        """Handle layer selection changes"""
        selected_items = self.layers_widget.selectedItems()
        if selected_items and selected_items[0].parent():  # Ensure it's a layer, not a group
            selected_layer_name = selected_items[0].text(0)
            if selected_layer_name in self.layer_manager.layers:
                # Set the selected layer in drawing app
                if self.drawing_app.layer == self.layer_manager.layers[selected_layer_name]:
                    return
                self.drawing_app.deselect_current_item()
                self.drawing_app.layer = self.layer_manager.layers[selected_layer_name]

    def create_bottom_panel(self):
        dock = QDockWidget('Item Properties', self)
        dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        
        # Create main widget and layout
        properties_widget = QWidget()
        layout = QGridLayout(properties_widget)
        
        # Position group
        pos_group = QGroupBox("Position")
        pos_layout = QGridLayout()
        
        # X position
        pos_layout.addWidget(QLabel("X:"), 0, 0)
        self.pos_x_edit = QLineEdit()
        self.pos_x_edit.setPlaceholderText("X position")
        self.pos_x_edit.textChanged.connect(lambda: self.update_item_property('position'))
        pos_layout.addWidget(self.pos_x_edit, 0, 1)
        
        # Y position
        pos_layout.addWidget(QLabel("Y:"), 0, 2)
        self.pos_y_edit = QLineEdit()
        self.pos_y_edit.setPlaceholderText("Y position")
        self.pos_y_edit.textChanged.connect(lambda: self.update_item_property('position'))
        pos_layout.addWidget(self.pos_y_edit, 0, 3)
        
        pos_group.setLayout(pos_layout)
        layout.addWidget(pos_group, 0, 0)
        
        # Size group
        size_group = QGroupBox("Size")
        size_layout = QGridLayout()
        
        # Width
        size_layout.addWidget(QLabel("Width:"), 0, 0)
        self.width_edit = QLineEdit()
        self.width_edit.setPlaceholderText("Width")
        self.width_edit.textChanged.connect(lambda: self.update_item_property('size'))
        size_layout.addWidget(self.width_edit, 0, 1)
        
        # Height
        size_layout.addWidget(QLabel("Height:"), 0, 2)
        self.height_edit = QLineEdit()
        self.height_edit.setPlaceholderText("Height")
        self.height_edit.textChanged.connect(lambda: self.update_item_property('size'))
        size_layout.addWidget(self.height_edit, 0, 3)
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group, 1, 0)
        
        # Line Properties group
        line_group = QGroupBox("Line Properties")
        line_layout = QGridLayout()
        
        # Line thickness
        line_layout.addWidget(QLabel("Thickness:"), 0, 0)
        self.thickness_edit = QSpinBox()
        self.thickness_edit.setRange(1, 20)
        self.thickness_edit.valueChanged.connect(lambda: self.update_item_property('thickness'))
        line_layout.addWidget(self.thickness_edit, 0, 1)
        
        line_group.setLayout(line_layout)
        layout.addWidget(line_group, 2, 0)
        
        # Set the widget as the dock widget's content
        dock.setWidget(properties_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)
        
        # Store reference to the dock widget
        self.properties_dock = dock
        
        # Connect to drawing app's selection changed signal
        self.drawing_app.scene.selectionChanged.connect(self.update_properties_panel)

    def update_properties_panel(self):
        """Update the properties panel with the selected item's properties"""
        selected_items = self.drawing_app.scene.selectedItems()
        
        # Enable/disable input fields based on selection
        has_selection = len(selected_items) == 1
        self.pos_x_edit.setEnabled(has_selection)
        self.pos_y_edit.setEnabled(has_selection)
        self.width_edit.setEnabled(has_selection)
        self.height_edit.setEnabled(has_selection)
        self.thickness_edit.setEnabled(has_selection)
        
        if not has_selection:
            # Clear all fields if no selection
            self.pos_x_edit.clear()
            self.pos_y_edit.clear()
            self.width_edit.clear()
            self.height_edit.clear()
            self.thickness_edit.setValue(1)
            return
            
        # Get the selected item
        item = selected_items[0]
        
        # Update position fields (center point)
        if isinstance(item, (QGraphicsRectItem, QGraphicsEllipseItem)):
            rect = item.rect()
            center = item.mapToScene(rect.center())
            self.pos_x_edit.setText(f"{center.x():.2f}")
            self.pos_y_edit.setText(f"{center.y():.2f}")
        elif isinstance(item, QGraphicsLineItem):
            line = item.line()
            center = item.mapToScene((line.p1() + line.p2()) / 2)
            self.pos_x_edit.setText(f"{center.x():.2f}")
            self.pos_y_edit.setText(f"{center.y():.2f}")
        elif hasattr(item, 'pad_data'):
            pos = item.scenePos()
            self.pos_x_edit.setText(f"{pos.x():.2f}")
            self.pos_y_edit.setText(f"{pos.y():.2f}")
        else:
            pos = item.scenePos()
            self.pos_x_edit.setText(f"{pos.x():.2f}")
            self.pos_y_edit.setText(f"{pos.y():.2f}")
        
        # Update line thickness
        if hasattr(item, 'pen'):
            self.thickness_edit.setValue(item.pen().width())
        
        # Update size fields
        if isinstance(item, (QGraphicsRectItem, QGraphicsEllipseItem)):
            rect = item.rect()
            self.width_edit.setText(f"{rect.width():.2f}")
            self.height_edit.setText(f"{rect.height():.2f}")
            self.width_edit.setEnabled(True)
            self.height_edit.setEnabled(True)
        elif isinstance(item, QGraphicsLineItem):
            line = item.line()
            width = abs(line.x2() - line.x1())
            height = abs(line.y2() - line.y1())
            self.width_edit.setText(f"{width:.2f}")
            self.height_edit.setText(f"{height:.2f}")
            # Disable size editing for lines
            self.width_edit.setEnabled(False)
            self.height_edit.setEnabled(False)
        elif hasattr(item, 'pad_data'):
            # Handle pad items
            self.width_edit.setText(f"{item.pad_data['width']:.2f}")
            self.width_edit.setEnabled(True)
            if item.pad_data['shape'] == 'Circle':
                self.height_edit.setText(f"{item.pad_data['width']:.2f}")
                self.height_edit.setEnabled(False)
            else:
                self.height_edit.setText(f"{item.pad_data['height']:.2f}")
                self.height_edit.setEnabled(True)

    def update_item_property(self, property_type):
        """Update the selected item's properties based on user input"""
        selected_items = self.drawing_app.scene.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        
        try:
            if property_type == 'position':
                try:
                    x = float(self.pos_x_edit.text() or '0')
                    y = float(self.pos_y_edit.text() or '0')
                    if isinstance(item, (QGraphicsRectItem, QGraphicsEllipseItem)):
                        rect = item.rect()
                        center = item.mapToScene(rect.center())
                        delta = QPointF(x, y) - center
                        item.moveBy(delta.x(), delta.y())
                    elif isinstance(item, QGraphicsLineItem):
                        line = item.line()
                        center = item.mapToScene((line.p1() + line.p2()) / 2)
                        delta = QPointF(x, y) - center
                        item.moveBy(delta.x(), delta.y())
                    elif hasattr(item, 'pad_data'):
                        # For pads, keep using scenePos
                        item.setPos(x, y)
                    else:
                        item.setPos(x, y)
                except ValueError:
                    return
                    
            elif property_type == 'size':
                try:
                    width = float(self.width_edit.text() or '0')
                    height = float(self.height_edit.text() or '0')
                    
                    if isinstance(item, (QGraphicsRectItem, QGraphicsEllipseItem)):
                        # Keep the top-left position fixed while resizing
                        rect = item.rect()
                        rect.setWidth(width)
                        rect.setHeight(height)
                        item.setRect(rect)
                    elif hasattr(item, 'pad_data'):
                        # Update pad dimensions
                        item.pad_data['width'] = width
                        item.pad_data['height'] = height
                        item.update()  # Trigger visual update
                except ValueError:
                    return
            
            elif property_type == 'thickness':
                if hasattr(item, 'pen'):
                    # Get current pen and update its width
                    pen = item.pen()
                    pen.setWidth(self.thickness_edit.value())
                    item.setPen(pen)
                    
        except Exception as e:
            print(f"Error updating item property: {e}")
            return

    def show_error_message(self, title, message):
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle(title)
        error_dialog.setText(message)
        error_dialog.setDetailedText(traceback.format_exc())
        error_dialog.exec_()

    def show_pad_editor(self, existing_pad=None):
        # Open the pad editor dialog
        try:
            pad_editor = PadEditor(self)
            pad_editor.setWindowModality(Qt.ApplicationModal)

            # If editing an existing pad, set its data in the editor
            if existing_pad:
                pad_editor.set_pad_data(existing_pad.pad_data)

            # Use a safe approach to show the dialog
            if pad_editor.exec_() == QDialog.Accepted and pad_editor.current_pad:
                if existing_pad:
                    # Update existing pad with new data
                    existing_pad.update_pad_data(pad_editor.current_pad)
                else:
                    # Add new pad
                    self.add_pad_to_design(pad_editor.current_pad)
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"Error in pad editor: {str(e)}\n{traceback_str}")
            self.show_error_message("Pad Editor Error", f"Error in pad editor: {str(e)}")

    def add_pad_to_design(self, pad_data):
        """Add a pad to the PCB design"""
        try:
            pad = Pad(pad_data)
            # Position the pad at the center of the view (0,0)
            pad.setPos(0, 0)

            # Add pad directly to scene first
            self.drawing_app.scene.addItem(pad)

            # Set initial layer visibility based on pad settings
            for pad_layer, enabled in pad_data['layers'].items():
                mapped_layer = self.layer_manager.pad_layer_map.get(pad_layer)
                if mapped_layer:
                    layer_name = mapped_layer.split('/')[-1]
                    if layer_name in self.layer_manager.layers:
                        # Set the visibility based on both pad settings and layer visibility
                        is_visible = enabled and self.layer_manager.layers[layer_name]["visible"]
                        pad.set_layer_visibility(pad_layer, is_visible)
                        
                        # Add pad to layer's item list for management (without adding to scene again)
                        self.layer_manager.layers[layer_name]["items"].append(pad)

            # Store in drawing app's pad list
            if not hasattr(self.drawing_app, 'pads'):
                self.drawing_app.pads = []
            self.drawing_app.pads.append(pad)

            # Select the pad so the user can move it
            pad.setSelected(True)
        except Exception as e:
            self.show_error_message("Pad Creation Error", f"Error creating pad: {str(e)}")

    # Open layer dialog
    def open_layer_setting_dialog(self):
        try:
            layer_setting = LayerSetting(self)
            layer_setting.setWindowModality(Qt.ApplicationModal)
            layer_setting.exec_()
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"Error in layer settings: {str(e)}\n{traceback_str}")
            self.show_error_message("Layer Settings Error", f"Error in layer settings: {str(e)}")

    def delete_selected(self):
        """Delete the currently selected items in the drawing app"""
        try:
            selected_items = self.drawing_app.scene.selectedItems()
            
            for item in selected_items:
                # Remove from scene
                self.drawing_app.scene.removeItem(item)
                
                # Remove from layer manager
                for layer_name, layer_data in self.layer_manager.layers.items():
                    if item in layer_data["items"]:
                        layer_data["items"].remove(item)
                
                # Remove from drawing app's pad list if it's a pad
                if hasattr(self.drawing_app, 'pads') and item in self.drawing_app.pads:
                    self.drawing_app.pads.remove(item)
                    
        except Exception as e:
            self.show_error_message("Delete Error", f"Error deleting selected items: {str(e)}")

    # def select_all_items(self):
    #     try:
    #         # Select each item
    #         for item in self.drawing_app.layer.get("items", []):
    #             if isinstance(item, QGraphicsItem) and item.flags() & QGraphicsItem.ItemIsSelectable:
    #                 item.setSelected(True)                    
    #     except Exception as e:
    #         self.show_error_message("Selection Error", f"Error selecting all items: {str(e)}")

    def add_custom_layer(self):
        """Add a custom layer to the PCB design"""
        layer_name = f'Custom {len(self.layer_manager.layers) - 6}'
        self.layer_manager.add_layer(layer_name)

    def add_default_layers(self):
        """Add default layers to the PCB design"""
        index = 0
        first_layer_name = None
        for group_name, layers in LAYER_GROUPS.items():
            for layer_name, color in layers.items():
                self.layer_manager.add_layer(
                    layer_name, 
                    color=color, 
                    z_index=index-len(LAYER_COLORS),
                    group_name=group_name
                )
                if first_layer_name is None:
                    first_layer_name = layer_name
                index += 1

        # Select the first layer
        if first_layer_name:
            # Find and select the layer item in the tree widget
            root = self.layers_widget.invisibleRootItem()
            for group_index in range(root.childCount()):
                group_item = root.child(group_index)
                for layer_index in range(group_item.childCount()):
                    layer_item = group_item.child(layer_index)
                    if layer_item.text(0) == first_layer_name:
                        self.layers_widget.setCurrentItem(layer_item)
                        # Set as active layer in drawing app
                        self.drawing_app.layer = self.layer_manager.layers[first_layer_name]
                        return

    def duplicate_selected(self):
        """Duplicate the currently selected items"""
        try:
            selected_items = self.drawing_app.scene.selectedItems()
            
            # Clear current selection
            for item in selected_items:
                item.setSelected(False)
            
            # Create duplicates with slight offset
            offset = 20  # pixels
            for item in selected_items:
                if hasattr(item, 'pad_data'):  # For pads
                    # Create a new pad with the same data
                    pad_data = item.pad_data.copy()
                    new_pad = self.add_pad_to_design(pad_data)
                    if new_pad:
                        # Position the new pad relative to the original
                        new_pos = item.pos() + QPointF(offset, offset)
                        new_pad.setPos(new_pos)
                        new_pad.setSelected(True)
                else:  # For other items (lines, rectangles, etc.)
                    new_item = type(item)()
                    self.drawing_app.scene.addItem(new_item)
                    
                    # Copy properties
                    new_item.setPen(item.pen())
                    new_item.setBrush(item.brush())
                    if hasattr(item, 'rect'):
                        new_rect = item.rect()
                        new_rect.translate(offset, offset)
                        new_item.setRect(new_rect)
                    elif hasattr(item, 'line'):
                        new_line = item.line()
                        new_line.translate(offset, offset)
                        new_item.setLine(new_line)
                    
                    new_item.setSelected(True)
                    
                    # Add to appropriate layer
                    for layer_name, layer_data in self.layer_manager.layers.items():
                        if item in layer_data["items"]:
                            self.layer_manager.add_item_to_layer(new_item, layer_name)
                            break
        except Exception as e:
            self.show_error_message("Duplicate Error", f"Error duplicating selected items: {str(e)}")

    def on_layer_double_clicked(self, layer_name):
        """Handle double click on a layer by opening layer settings"""
        try:
            layer_setting = LayerSetting(self)
            layer_setting.setWindowModality(Qt.ApplicationModal)
            
            # Pre-select the double-clicked layer
            if hasattr(layer_setting, 'select_layer'):
                layer_setting.select_layer(layer_name)
                
            layer_setting.exec_()
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"Error opening layer settings: {str(e)}\n{traceback_str}")
            self.show_error_message("Layer Settings Error", f"Error opening layer settings: {str(e)}")

    def export_to_pdf(self, filename="drawing.pdf"):
        """Export the current view to a PDF file"""
        try:
            # Create printer object
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            
            # Set page size to match view size
            printer.setPageSize(QPrinter.A4)
            
            # Create painter for drawing
            painter = QPainter()
            painter.begin(printer)
            
            # Set rendering hints for better quality
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # Render the view to PDF
            for item in self.drawing_app.scene.items():
                if isinstance(item, GridLine) or isinstance(item, GridText):
                    item.setVisible(False)
            self.drawing_app.drawing_window.render(painter)
            for item in self.drawing_app.scene.items():
                if isinstance(item, GridLine) or isinstance(item, GridText):
                    item.setVisible(True)
            
            # End painting
            painter.end()
            
            return True
        except Exception as e:
            print(f"Error exporting to PDF: {e}")
            return False