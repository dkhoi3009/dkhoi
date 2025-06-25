import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from main_app import main_app
import traceback
import faulthandler
faulthandler.enable()
def main():
    try:
        app = QApplication(sys.argv)  # Tạo ứng dụng PyQt
        pcb_app = main_app()  # Khởi tạo ứng dụng chính
        pcb_app.showMaximized()  # Hiển thị ứng dụng ở chế độ toàn màn hình
        sys.exit(app.exec_())  # Chạy vòng lặp sự kiện chính
    except Exception as e:
        print(f"Fatal Error: {e}")  # In lỗi ra console
        traceback.print_exc()  # In chi tiết lỗi ra console
        # Hiển thị hộp thoại thông báo lỗi
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)  # Đặt biểu tượng lỗi
        error_dialog.setWindowTitle("Fatal Error")  # Tiêu đề hộp thoại
        error_dialog.setText(f"A fatal error occurred: {str(e)}")  # Nội dung lỗi
        error_dialog.setDetailedText(traceback.format_exc())  # Chi tiết lỗi
        error_dialog.exec_()  # Hiển thị hộp thoại

if __name__ == '__main__':
    main()  # Gọi hàm chính