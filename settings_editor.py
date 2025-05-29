from PyQt5.QtWidgets import QDockWidget, QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QMainWindow, QMessageBox
import PyQt5.QtCore as Qt
import traceback
class main_app(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCB Design Studio")
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()

    def init_ui(self):
        """
        Khởi tạo giao diện người dùng.
        """
        self.create_left_sidebar()  # Tạo khung bên trái
        self.create_central_canvas()  # Tạo khu vực vẽ chính
        self.create_menu_bar()  # Tạo thanh menu
        self.create_toolbar()  # Tạo thanh công cụ

    def create_left_sidebar(self):
        """
        Tạo khung bên trái với các lựa chọn Layer, Object, PCB Print.
        """
        dock = QDockWidget("Settings", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # Tạo danh sách các mục lựa chọn
        tree_widget = QTreeWidget()
        tree_widget.setHeaderHidden(True)  # Ẩn tiêu đề cột

        # Thêm các mục chính
        layer_item = QTreeWidgetItem(tree_widget, ["Layer"])
        object_item = QTreeWidgetItem(tree_widget, ["Objects"])
        pcb_print_item = QTreeWidgetItem(tree_widget, ["PCB Print"])

        # Thêm các mục con (nếu cần)
        QTreeWidgetItem(layer_item, ["Physical Layer"])
        QTreeWidgetItem(layer_item, ["Layer Settings"])
        QTreeWidgetItem(layer_item, ["Display Layer Settings"])

        QTreeWidgetItem(object_item, ["Grid Settings"])
        QTreeWidgetItem(object_item, ["Snap Settings"])

        QTreeWidgetItem(pcb_print_item, ["Print Resolution"])
        QTreeWidgetItem(pcb_print_item, ["Color Mode"])

        # Kết nối sự kiện khi nhấp vào mục
        tree_widget.itemClicked.connect(self.handle_tree_item_click)

        dock.setWidget(tree_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def handle_tree_item_click(self, item, column):
        """
        Xử lý sự kiện khi nhấp vào một mục trong danh sách.
        """
        if item.text(0) == "Physical Layer":
            self.show_physical_layer_settings()
        elif item.text(0) == "Layer Settings":
            self.show_layer_settings()
        elif item.text(0) == "Display Layer Settings":
            self.show_display_layer_settings()
        elif item.text(0) == "Grid Settings":
            self.show_grid_settings()
        elif item.text(0) == "Snap Settings":
            self.show_snap_settings()
        elif item.text(0) == "Print Resolution":
            self.show_print_resolution_settings()
        elif item.text(0) == "Color Mode":
            self.show_color_mode_settings()

    def show_physical_layer_settings(self):
        QMessageBox.information(self, "Settings", "Physical Layer Settings")

    def show_layer_settings(self):
        QMessageBox.information(self, "Settings", "Layer Settings")

    def show_display_layer_settings(self):
        QMessageBox.information(self, "Settings", "Display Layer Settings")

    def show_grid_settings(self):
        QMessageBox.information(self, "Settings", "Grid Settings")

    def show_snap_settings(self):
        QMessageBox.information(self, "Settings", "Snap Settings")

    def show_print_resolution_settings(self):
        QMessageBox.information(self, "Settings", "Print Resolution Settings")

    def show_color_mode_settings(self):
        QMessageBox.information(self, "Settings", "Color Mode Settings")


class SettingsEditor:
    pass