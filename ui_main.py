from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QListWidget, QListWidgetItem, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QSlider, QLineEdit, QComboBox, QMessageBox, QFontComboBox, QCheckBox, QSpinBox, QColorDialog, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PIL import Image, ImageDraw, ImageFont  # 添加 ImageDraw, ImageFont
import os

try:
    resample_method = Image.Resampling.LANCZOS
except AttributeError:
    resample_method = Image.LANCZOS

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

def get_fonts_in_folder(folder):
    fonts = []
    for fname in os.listdir(folder):
        if fname.lower().endswith(('.ttf', '.otf')):
            fonts.append(os.path.splitext(fname)[0])
    return fonts

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片水印工具")
        self.setGeometry(100, 100, 800, 600)
        self.watermark_color = (255, 255, 255)  # 默认白色
        self.image_watermark_path = None
        self.image_watermark_scale = 30  # 百分比
        self.image_watermark_opacity = 80  # 百分比
        self.init_ui()

    def add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #bbb; background: #bbb; min-height: 2px;")
        line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(line)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(18, 12, 18, 12)

        # 图片列表
        self.image_list = ImageListWidget()
        self.image_list.setStyleSheet("background: #fafbfc; border: 1px solid #e0e0e0;")
        layout.addWidget(self.image_list)

        # 分割线
        self.add_separator(layout)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.import_button = QPushButton("导入图片")
        self.import_folder_button = QPushButton("导入文件夹")
        self.export_button = QPushButton("导出图片")
        for btn in [self.import_button, self.import_folder_button, self.export_button]:
            btn.setStyleSheet("padding: 6px 18px; font-weight: bold;")
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.import_folder_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 分割线
        self.add_separator(layout)

        # 输出选项
        layout.addWidget(QLabel("导出图片格式"))
        self.format_selector = QComboBox()
        self.format_selector.addItems(["JPEG", "PNG"])
        layout.addWidget(self.format_selector)

        layout.addWidget(QLabel("JPEG 压缩质量"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(80)
        layout.addWidget(self.quality_slider)

        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("自定义导出图片名前缀")
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("自定义导出图片名后缀")
        layout.addWidget(self.prefix_input)
        layout.addWidget(self.suffix_input)

        # 分割线
        self.add_separator(layout)

        # 文本水印功能块
        font_title = QLabel("文本水印设置")
        font_title.setStyleSheet("font-weight: bold; font-size: 15px; margin-top: 8px;")
        layout.addWidget(font_title)

        self.watermark_text_input = QLineEdit()
        self.watermark_text_input.setPlaceholderText("输入水印文本")
        layout.addWidget(self.watermark_text_input)

        font_layout = QHBoxLayout()
        font_layout.setSpacing(8)
        self.font_combo = QComboBox()
        self.font_files = {}
        if os.path.isdir(FONTS_DIR):
            for fname in os.listdir(FONTS_DIR):
                if fname.lower().endswith(('.ttf', '.otf')):
                    font_name = os.path.splitext(fname)[0]
                    base_font = font_name.split('-')[0]
                    if base_font not in self.font_files:
                        self.font_combo.addItem(base_font)
                        self.font_files[base_font] = {}
                    style = font_name[len(base_font):].lower()
                    self.font_files[base_font][style] = os.path.join(FONTS_DIR, fname)
        font_layout.addWidget(QLabel("字体"))
        font_layout.addWidget(self.font_combo)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 1000)
        self.font_size_spin.setValue(64)
        font_layout.addWidget(QLabel("字号"))
        font_layout.addWidget(self.font_size_spin)
        self.bold_checkbox = QCheckBox("粗体")
        self.italic_checkbox = QCheckBox("斜体")
        font_layout.addWidget(self.bold_checkbox)
        font_layout.addWidget(self.italic_checkbox)
        font_layout.addStretch()
        layout.addLayout(font_layout)

        # 水印透明度滑块
        opacity_layout = QHBoxLayout()
        self.watermark_opacity_slider = QSlider(Qt.Horizontal)
        self.watermark_opacity_slider.setRange(0, 100)
        self.watermark_opacity_slider.setValue(50)
        opacity_layout.addWidget(QLabel("水印透明度（%）"))
        opacity_layout.addWidget(self.watermark_opacity_slider)
        layout.addLayout(opacity_layout)

        # 字体颜色选择
        color_layout = QHBoxLayout()
        self.color_button = QPushButton("选择水印颜色")
        self.color_button.setStyleSheet("background-color: rgb(255,255,255);")
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(QLabel("水印颜色"))
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        layout.addLayout(color_layout)

        # 水印样式选项
        style_layout = QHBoxLayout()
        self.shadow_checkbox = QCheckBox("阴影")
        self.outline_checkbox = QCheckBox("描边")
        style_layout.addWidget(self.shadow_checkbox)
        style_layout.addWidget(self.outline_checkbox)
        style_layout.addStretch()
        layout.addLayout(style_layout)

        # 分割线
        self.add_separator(layout)

        # 图片水印功能块
        imgwm_title = QLabel("图片水印设置")
        imgwm_title.setStyleSheet("font-weight: bold; font-size: 15px; margin-top: 8px;")
        layout.addWidget(imgwm_title)

        imgwm_layout = QHBoxLayout()
        self.imgwm_button = QPushButton("选择图片水印")
        self.imgwm_button.clicked.connect(self.choose_image_watermark)
        self.imgwm_label = QLabel("未选择")
        self.imgwm_preview = QLabel()
        self.imgwm_preview.setFixedSize(60, 60)
        self.imgwm_preview.setStyleSheet("border:1px solid #ccc; background:#fff;")
        imgwm_layout.addWidget(self.imgwm_button)
        imgwm_layout.addWidget(self.imgwm_label)
        imgwm_layout.addWidget(self.imgwm_preview)
        imgwm_layout.addStretch()
        layout.addLayout(imgwm_layout)

        scale_layout = QHBoxLayout()
        self.imgwm_scale_slider = QSlider(Qt.Horizontal)
        self.imgwm_scale_slider.setRange(5, 100)
        self.imgwm_scale_slider.setValue(self.image_watermark_scale)
        self.imgwm_scale_slider.valueChanged.connect(self.update_imgwm_scale_label)
        self.imgwm_scale_label = QLabel(f"缩放: {self.image_watermark_scale}%")
        scale_layout.addWidget(self.imgwm_scale_label)
        scale_layout.addWidget(self.imgwm_scale_slider)
        scale_layout.addStretch()
        layout.addLayout(scale_layout)

        img_opacity_layout = QHBoxLayout()
        self.imgwm_opacity_slider = QSlider(Qt.Horizontal)
        self.imgwm_opacity_slider.setRange(0, 100)
        self.imgwm_opacity_slider.setValue(self.image_watermark_opacity)
        self.imgwm_opacity_slider.valueChanged.connect(self.update_imgwm_opacity_label)
        self.imgwm_opacity_label = QLabel(f"图片水印透明度: {self.image_watermark_opacity}%")
        img_opacity_layout.addWidget(self.imgwm_opacity_label)
        img_opacity_layout.addWidget(self.imgwm_opacity_slider)
        img_opacity_layout.addStretch()
        layout.addLayout(img_opacity_layout)

        # 主窗口设置
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 信号连接
        self.import_button.clicked.connect(self.import_images)
        self.import_folder_button.clicked.connect(self.import_folder)
        self.export_button.clicked.connect(self.export_images)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(*self.watermark_color), self, "选择水印颜色")
        if color.isValid():
            self.watermark_color = (color.red(), color.green(), color.blue())
            self.color_button.setStyleSheet(f"background-color: rgb({color.red()},{color.green()},{color.blue()});")

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

    def choose_image_watermark(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片水印", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff)")
        if path:
            self.image_watermark_path = path
            self.imgwm_label.setText(os.path.basename(path))
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.imgwm_preview.setPixmap(pixmap.scaled(self.imgwm_preview.width(), self.imgwm_preview.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.imgwm_preview.clear()
        else:
            self.image_watermark_path = None
            self.imgwm_label.setText("未选择")
            self.imgwm_preview.clear()

    def update_imgwm_scale_label(self):
        val = self.imgwm_scale_slider.value()
        self.image_watermark_scale = val
        self.imgwm_scale_label.setText(f"缩放: {val}%")

    def update_imgwm_opacity_label(self):
        val = self.imgwm_opacity_slider.value()
        self.image_watermark_opacity = val
        self.imgwm_opacity_label.setText(f"图片水印透明度: {val}%")

    def export_images(self):
        folder = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if not folder:
            return  # 用户取消选择

        # 检查是否与原文件夹相同
        for index in range(self.image_list.count()):
            item = self.image_list.item(index)
            input_path = item.toolTip()  # 获取图片的完整路径
            input_dir = os.path.dirname(input_path)
            if os.path.abspath(folder) == os.path.abspath(input_dir):
                QMessageBox.warning(self, "警告", "禁止导出到原文件夹，请选择其他文件夹。")
                return  # 终止导出操作

        output_format = self.format_selector.currentText().lower()  # 获取用户选择的输出格式
        quality = self.quality_slider.value()  # 获取 JPEG 压缩质量
        prefix = self.prefix_input.text()  # 获取自定义前缀
        suffix = self.suffix_input.text()  # 获取自定义后缀
        watermark_text = self.watermark_text_input.text()  # 获取水印文本
        watermark_opacity = self.watermark_opacity_slider.value()  # 获取透明度
        font_base = self.font_combo.currentText()
        font_size = self.font_size_spin.value()
        is_bold = self.bold_checkbox.isChecked()
        is_italic = self.italic_checkbox.isChecked()
        shadow_enabled = self.shadow_checkbox.isChecked()
        outline_enabled = self.outline_checkbox.isChecked()
        imgwm_path = self.image_watermark_path
        imgwm_scale = self.imgwm_scale_slider.value()
        imgwm_opacity = self.imgwm_opacity_slider.value()
        # 组合风格后缀
        style = ""
        if is_bold and is_italic:
            style = "-bolditalic"
        elif is_bold:
            style = "-bold"
        elif is_italic:
            style = "-italic"
        font_path = None
        if font_base in self.font_files:
            # 优先找完全匹配的风格
            if style in self.font_files[font_base]:
                font_path = self.font_files[font_base][style]
            # 退而求其次
            elif "-bold" in self.font_files[font_base] and is_bold:
                font_path = self.font_files[font_base]["-bold"]
            elif "-italic" in self.font_files[font_base] and is_italic:
                font_path = self.font_files[font_base]["-italic"]
            elif "" in self.font_files[font_base]:
                font_path = self.font_files[font_base][""]
            else:
                # 任意一个
                font_path = list(self.font_files[font_base].values())[0]
        for index in range(self.image_list.count()):
            item = self.image_list.item(index)
            input_path = item.toolTip()  # 获取图片的完整路径
            base_name, _ = os.path.splitext(os.path.basename(input_path))
            
            # 判断前缀是否为空，若非空则添加下划线
            output_name = f"{prefix + '_' if prefix else ''}{base_name}{suffix}.{output_format}"
            output_path = os.path.join(folder, output_name)

            with Image.open(input_path) as img:
                # 文本水印处理
                if watermark_text:
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")
                    watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(watermark_layer)
                    # 字体加载（仅用fonts文件夹下的字体）
                    try:
                        if font_path:
                            font = ImageFont.truetype(font_path, font_size)
                        else:
                            font = ImageFont.load_default()
                    except Exception:
                        font = ImageFont.load_default()
                    # 获取文本尺寸
                    try:
                        bbox = draw.textbbox((0, 0), watermark_text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except AttributeError:
                        text_width, text_height = font.getsize(watermark_text)
                    # 右下角留边距，向上移动 40 像素
                    x = img.size[0] - text_width - 20
                    y = img.size[1] - text_height * 1.2 - 40
                    alpha = int(255 * (watermark_opacity / 100))
                    # 阴影
                    if shadow_enabled:
                        shadow_offset = 2
                        draw.text((x + shadow_offset, y + shadow_offset), watermark_text, font=font, fill=(0, 0, 0, alpha))
                    # 描边
                    if outline_enabled:
                        outline_range = 2
                        for dx in range(-outline_range, outline_range + 1):
                            for dy in range(-outline_range, outline_range + 1):
                                if dx == 0 and dy == 0:
                                    continue
                                draw.text((x + dx, y + dy), watermark_text, font=font, fill=(0, 0, 0, alpha))
                    # 正文
                    draw.text((x, y), watermark_text, font=font, fill=(*self.watermark_color, alpha))
                    img = Image.alpha_composite(img.convert("RGBA"), watermark_layer)
                else:
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")

                # 图片水印处理（必须在文本水印之后，且在保存之前）
                if imgwm_path:
                    try:
                        with Image.open(imgwm_path) as wm_img:
                            wm_img = wm_img.convert("RGBA")
                            # 缩放
                            scale = imgwm_scale / 100.0
                            new_w = int(img.size[0] * scale)
                            new_h = int(wm_img.size[1] * (new_w / wm_img.size[0]))
                            wm_img = wm_img.resize((new_w, new_h), resample=resample_method)
                            # 透明度
                            if imgwm_opacity < 100:
                                alpha = wm_img.split()[-1].point(lambda p: int(p * imgwm_opacity / 100))
                                wm_img.putalpha(alpha)
                            # 粘贴到右下角
                            x = img.size[0] - wm_img.size[0] - 20
                            y = img.size[1] - wm_img.size[1] - 20
                            # 合成
                            img.alpha_composite(wm_img, (x, y))
                    except Exception as e:
                        print(f"图片水印处理失败: {e}")

                # 保存图片
                if output_format == "jpeg":
                    img = img.convert("RGB")
                    img.save(output_path, format="JPEG", quality=quality)
                elif output_format == "png":
                    img.save(output_path, format="PNG")
            print(f"已导出: {output_path}")  # 调试输出
            # 图片水印处理
            if imgwm_path:
                try:
                    with Image.open(imgwm_path) as wm_img:
                        wm_img = wm_img.convert("RGBA")
                        # 缩放
                        scale = imgwm_scale / 100.0
                        new_w = int(img.size[0] * scale)
                        new_h = int(wm_img.size[1] * (new_w / wm_img.size[0]))
                        wm_img = wm_img.resize((new_w, new_h), resample=resample_method)
                        # 透明度
                        if imgwm_opacity < 100:
                            alpha = wm_img.split()[-1].point(lambda p: int(p * imgwm_opacity / 100))
                            wm_img.putalpha(alpha)
                        # 粘贴到右下角
                        x = img.size[0] - wm_img.size[0] - 20
                        y = img.size[1] - wm_img.size[1] - 20
                        # 合成
                        if img.mode != "RGBA":
                            img = img.convert("RGBA")
                        img.paste(wm_img, (x, y), wm_img)
                except Exception as e:
                    print(f"图片水印处理失败: {e}")


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
        self.addItem(item)
