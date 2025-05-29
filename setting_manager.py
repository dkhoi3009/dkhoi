import json
import os

class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        """
        Quản lý cài đặt của ứng dụng.
        :param settings_file: Đường dẫn đến file cài đặt.
        """
        self.settings_file = settings_file
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """
        Tải cài đặt từ file JSON.
        """
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as file:
                self.settings = json.load(file)
        else:
            self.settings = self.default_settings()
            self.save_settings()

    def save_settings(self):
        """
        Lưu cài đặt vào file JSON.
        """
        with open(self.settings_file, "w") as file:
            json.dump(self.settings, file, indent=4)

    def default_settings(self):
        """
        Trả về cài đặt mặc định.
        """
        return {
            "layers": {
                "TopPlacement": True,
                "TopSilk": True,
                "TopPattern": True,
                "BottomPattern": True,
                "BottomSilk": True,
                "BottomPlacement": True
            },
            "objects": {
                "show_grid": True,
                "snap_to_grid": True
            },
            "pcb_print": {
                "resolution": 300,
                "color_mode": "Color"
            }
        }

    def get_setting(self, category, key, default=None):
        """
        Lấy giá trị của một cài đặt.
        :param category: Danh mục cài đặt (layers, objects, pcb_print).
        :param key: Tên cài đặt.
        :param default: Giá trị mặc định nếu cài đặt không tồn tại.
        """
        return self.settings.get(category, {}).get(key, default)

    def set_setting(self, category, key, value):
        """
        Đặt giá trị cho một cài đặt.
        :param category: Danh mục cài đặt (layers, objects, pcb_print).
        :param key: Tên cài đặt.
        :param value: Giá trị cần đặt.
        """
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value
        self.save_settings()