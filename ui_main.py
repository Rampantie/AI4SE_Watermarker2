from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QListWidget, QListWidgetItem, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QSlider, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PIL import Image  # 添加 PIL 库用于图片处理
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片水印工具")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        # 主布局
        layout = QVBoxLayout()

        # 图片列表
        self.image_list = ImageListWidget()  # 替换为自定义的 QListWidget
        layout.addWidget(self.image_list)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.import_button = QPushButton("导入图片")
        self.import_folder_button = QPushButton("导入文件夹")  # 新增按钮
        self.export_button = QPushButton("导出图片")
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.import_folder_button)  # 添加到布局
        button_layout.addWidget(self.export_button)
        layout.addLayout(button_layout)

        # 输出选项
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("自定义前缀")
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("自定义后缀")
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(80)

        self.format_selector = QComboBox()  # 添加输出格式选择器
        self.format_selector.addItems(["JPEG", "PNG"])  # 添加选项
        layout.addWidget(QLabel("输出格式"))
        layout.addWidget(self.format_selector)

        layout.addWidget(QLabel("JPEG 压缩质量"))
        layout.addWidget(self.quality_slider)
        layout.addWidget(self.prefix_input)
        layout.addWidget(self.suffix_input)

        # 主窗口设置
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 信号连接
        self.import_button.clicked.connect(self.import_images)
        self.import_folder_button.clicked.connect(self.import_folder)  # 连接新功能
        self.export_button.clicked.connect(self.export_images)

    def import_images(self):
        # 弹出文件选择对话框
        files, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "Images (*.jpeg *.jpg *.png *.bmp *.tiff)")
        for file in files:
            self.image_list.add_image(file)  # 修改为调用 add_image 方法

    def import_folder(self):
        # 弹出文件夹选择对话框
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    if filename.lower().endswith(('.jpeg', '.jpg', '.png', '.bmp', '.tiff')):
                        self.image_list.add_image(os.path.join(root, filename))  # 修改为调用 add_image 方法

    def export_images(self):
        folder = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if folder:
            output_format = self.format_selector.currentText().lower()  # 获取用户选择的输出格式
            quality = self.quality_slider.value()  # 获取 JPEG 压缩质量
            prefix = self.prefix_input.text()  # 获取自定义前缀
            suffix = self.suffix_input.text()  # 获取自定义后缀

            for index in range(self.image_list.count()):
                item = self.image_list.item(index)
                input_path = item.toolTip()  # 获取图片的完整路径
                base_name, _ = os.path.splitext(os.path.basename(input_path))
                
                # 判断前缀是否为空，若非空则添加下划线
                output_name = f"{prefix + '_' if prefix else ''}{base_name}{suffix}.{output_format}"
                output_path = os.path.join(folder, output_name)

                # 使用 PIL 保存图片
                with Image.open(input_path) as img:
                    if output_format == "jpeg":
                        img = img.convert("RGB")  # 确保 JPEG 格式不包含透明通道
                        img.save(output_path, format="JPEG", quality=quality)
                    elif output_format == "png":
                        img.save(output_path, format="PNG")

                print(f"已导出: {output_path}")  # 调试输出

class ImageListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)  # 启用拖拽

    def dragEnterEvent(self, event):
        # 检查拖拽的文件是否是图片
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        # 处理拖拽的文件
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.jpeg', '.jpg', '.png', '.bmp', '.tiff')):
                    self.add_image(file_path)  # 修改为调用 add_image 方法

    def add_image(self, file_path):
        # 添加图片项并显示缩略图
        item = QListWidgetItem()
        pixmap = QPixmap(file_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # 缩略图大小
        item.setIcon(QIcon(pixmap))
        item.setText(os.path.basename(file_path))
        item.setToolTip(file_path)  # 显示完整路径作为工具提示
        self.addItem(item)
