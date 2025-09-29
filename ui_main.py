from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QListWidget, QListWidgetItem, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QSlider, QLineEdit, QComboBox, QMessageBox, QFontComboBox, QCheckBox, QSpinBox, QColorDialog, QFrame, QSizePolicy, QInputDialog
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QIcon, QColor, QImage, QPainter
from PIL import Image, ImageDraw, ImageFont  # 添加 ImageDraw, ImageFont
import os
import json
import sys

try:
    resample_method = Image.Resampling.LANCZOS
except AttributeError:
    resample_method = Image.LANCZOS

def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容 PyInstaller 打包后的环境"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

FONTS_DIR = resource_path("fonts")

def get_user_data_path():
    """获取用户本地数据目录"""
    if sys.platform == "win32":
        return os.path.join(os.getenv("APPDATA"), "PhotoWatermarker")
    else:
        return os.path.join(os.path.expanduser("~"), ".PhotoWatermarker")

USER_DATA_DIR = get_user_data_path()
TEMPLATES_FILE = os.path.join(USER_DATA_DIR, "templates.json")
DEFAULT_TEMPLATES_FILE = resource_path("templates.json")

# 确保用户数据目录存在
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

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
        self.preview_pixmap = None
        self.preview_img = None
        self.current_preview_index = 0
        self.watermark_pos_mode = "right_bottom"  # 九宫格/自定义
        self.watermark_offset = None  # 拖拽偏移
        self.dragging = False
        self.custom_pos = None  # (x, y)
        self.templates = self.load_templates()
        self.init_ui()
        self.load_default_template()  # 自动加载默认模板

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

        # ======= 导出设置（含尺寸设置） =======
        export_settings_layout = QVBoxLayout()
        export_settings_layout.setSpacing(8)

        # 导出尺寸设置（移到导出设置顶部）
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("导出尺寸："))
        self.size_mode_combo = QComboBox()
        self.size_mode_combo.addItems(["原图", "指定宽度", "指定高度", "按百分比缩放"])
        self.size_mode_combo.currentIndexChanged.connect(self.update_size_mode)
        size_layout.addWidget(self.size_mode_combo)
        self.width_input = QSpinBox()
        self.width_input.setRange(1, 10000)
        self.width_input.setValue(800)
        self.width_input.setPrefix("宽度:")
        self.height_input = QSpinBox()
        self.height_input.setRange(1, 10000)
        self.height_input.setValue(600)
        self.height_input.setPrefix("高度:")
        self.percent_input = QSpinBox()
        self.percent_input.setRange(1, 1000)
        self.percent_input.setValue(100)
        self.percent_input.setSuffix("%")
        size_layout.addWidget(self.width_input)
        size_layout.addWidget(self.height_input)
        size_layout.addWidget(self.percent_input)
        size_layout.addStretch()
        export_settings_layout.addLayout(size_layout)
        self.update_size_mode()  # 初始化禁用状态

        # 导出格式与质量
        export_settings_layout.addWidget(QLabel("导出图片格式"))
        self.format_selector = QComboBox()
        self.format_selector.addItems(["JPEG", "PNG"])
        export_settings_layout.addWidget(self.format_selector)

        export_settings_layout.addWidget(QLabel("JPEG 压缩质量"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(80)
        export_settings_layout.addWidget(self.quality_slider)

        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("自定义导出图片名前缀")
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("自定义导出图片名后缀")
        export_settings_layout.addWidget(self.prefix_input)
        export_settings_layout.addWidget(self.suffix_input)

        layout.addLayout(export_settings_layout)
        # ======= 导出设置结束 =======

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

        # 图片水印缩放方式选择
        imgwm_size_layout = QHBoxLayout()
        imgwm_size_layout.addWidget(QLabel("图片水印缩放方式："))
        self.imgwm_size_mode_combo = QComboBox()
        self.imgwm_size_mode_combo.addItems(["按比例缩放", "指定宽度", "指定高度"])
        self.imgwm_size_mode_combo.currentIndexChanged.connect(self.update_imgwm_size_mode)
        imgwm_size_layout.addWidget(self.imgwm_size_mode_combo)
        self.imgwm_scale_slider = QSlider(Qt.Horizontal)
        self.imgwm_scale_slider.setRange(5, 100)
        self.imgwm_scale_slider.setValue(self.image_watermark_scale)
        self.imgwm_scale_slider.valueChanged.connect(self.update_imgwm_scale_label)
        self.imgwm_scale_label = QLabel(f"缩放: {self.image_watermark_scale}%")
        self.imgwm_width_input = QSpinBox()
        self.imgwm_width_input.setRange(1, 10000)
        self.imgwm_width_input.setValue(200)
        self.imgwm_width_input.setPrefix("宽度:")
        self.imgwm_height_input = QSpinBox()
        self.imgwm_height_input.setRange(1, 10000)
        self.imgwm_height_input.setValue(100)
        self.imgwm_height_input.setPrefix("高度:")
        imgwm_size_layout.addWidget(self.imgwm_scale_label)
        imgwm_size_layout.addWidget(self.imgwm_scale_slider)
        imgwm_size_layout.addWidget(self.imgwm_width_input)
        imgwm_size_layout.addWidget(self.imgwm_height_input)
        imgwm_size_layout.addStretch()
        layout.addLayout(imgwm_size_layout)
        self.update_imgwm_size_mode()  # 初始化禁用状态

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

        # 预览区
        preview_layout = QVBoxLayout()
        preview_label = QLabel("图片预览（实时水印效果）")
        preview_label.setStyleSheet("font-weight: bold; font-size: 15px; margin-top: 8px;")
        preview_layout.addWidget(preview_label)
        self.preview_area = PreviewLabel(self)
        self.preview_area.setFixedSize(400, 300)
        self.preview_area.setStyleSheet("background: #eee; border: 1px solid #bbb;")
        preview_layout.addWidget(self.preview_area, alignment=Qt.AlignCenter)
        layout.addLayout(preview_layout)

        # 九宫格位置按钮
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("水印位置："))
        self.pos_buttons = []
        pos_names = [
            ("左上", "left_top"), ("上中", "center_top"), ("右上", "right_top"),
            ("左中", "left_center"), ("中心", "center"), ("右中", "right_center"),
            ("左下", "left_bottom"), ("下中", "center_bottom"), ("右下", "right_bottom")
        ]
        for text, mode in pos_names:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode: self.set_watermark_pos_mode(m))
            self.pos_buttons.append(btn)
            pos_layout.addWidget(btn)
        pos_layout.addStretch()
        layout.addLayout(pos_layout)
        self.update_pos_buttons()

        # 配置管理功能
        config_layout = QHBoxLayout()
        self.save_template_button = QPushButton("保存模板")
        self.load_template_button = QPushButton("加载模板")
        self.delete_template_button = QPushButton("删除模板")
        self.template_selector = QComboBox()
        self.update_template_selector()
        config_layout.addWidget(QLabel("模板管理："))
        config_layout.addWidget(self.template_selector)
        config_layout.addWidget(self.save_template_button)
        config_layout.addWidget(self.load_template_button)
        config_layout.addWidget(self.delete_template_button)
        layout.addLayout(config_layout)

        # 主窗口设置
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 信号连接
        self.import_button.clicked.connect(self.import_images)
        self.import_folder_button.clicked.connect(self.import_folder)
        self.export_button.clicked.connect(self.export_images)

        # 信号连接（预览相关）
        self.image_list.currentRowChanged.connect(self.on_image_selected)
        self.watermark_text_input.textChanged.connect(self.update_preview)
        self.font_combo.currentIndexChanged.connect(self.update_preview)
        self.font_size_spin.valueChanged.connect(self.update_preview)
        self.bold_checkbox.stateChanged.connect(self.update_preview)
        self.italic_checkbox.stateChanged.connect(self.update_preview)
        self.watermark_opacity_slider.valueChanged.connect(self.update_preview)
        self.color_button.clicked.connect(self.update_preview)
        self.shadow_checkbox.stateChanged.connect(self.update_preview)
        self.outline_checkbox.stateChanged.connect(self.update_preview)
        self.imgwm_button.clicked.connect(self.update_preview)
        self.imgwm_scale_slider.valueChanged.connect(self.update_preview)
        self.imgwm_width_input.valueChanged.connect(self.update_preview)
        self.imgwm_height_input.valueChanged.connect(self.update_preview)
        self.imgwm_size_mode_combo.currentIndexChanged.connect(self.update_preview)
        self.imgwm_opacity_slider.valueChanged.connect(self.update_preview)
        self.size_mode_combo.currentIndexChanged.connect(self.update_preview)
        self.width_input.valueChanged.connect(self.update_preview)
        self.height_input.valueChanged.connect(self.update_preview)
        self.percent_input.valueChanged.connect(self.update_preview)

        # 信号连接（模板管理）
        self.save_template_button.clicked.connect(self.save_template)
        self.load_template_button.clicked.connect(self.load_template)
        self.delete_template_button.clicked.connect(self.delete_template)

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

    def update_size_mode(self):
        mode = self.size_mode_combo.currentIndex()
        self.width_input.setEnabled(mode == 1)
        self.height_input.setEnabled(mode == 2)
        self.percent_input.setEnabled(mode == 3)

    def update_imgwm_size_mode(self):
        mode = self.imgwm_size_mode_combo.currentIndex()
        self.imgwm_scale_slider.setEnabled(mode == 0)
        self.imgwm_scale_label.setEnabled(mode == 0)
        self.imgwm_width_input.setEnabled(mode == 1)
        self.imgwm_height_input.setEnabled(mode == 2)

    def export_images(self):
        folder = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if not folder:
            return  # 用户取消选择

        # 检查是否与原文件夹相同
        for index in range(self.image_list.count()):
            item = self.image_list.item(index)
            input_path = item.toolTip()
            input_dir = os.path.dirname(input_path)
            if os.path.abspath(folder) == os.path.abspath(input_dir):
                QMessageBox.warning(self, "警告", "禁止导出到原文件夹，请选择其他文件夹。")
                return

        output_format = self.format_selector.currentText().lower()
        quality = self.quality_slider.value()
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        watermark_text = self.watermark_text_input.text()
        watermark_opacity = self.watermark_opacity_slider.value()
        font_base = self.font_combo.currentText()
        font_size = self.font_size_spin.value()
        is_bold = self.bold_checkbox.isChecked()
        is_italic = self.italic_checkbox.isChecked()
        shadow_enabled = self.shadow_checkbox.isChecked()
        outline_enabled = self.outline_checkbox.isChecked()
        imgwm_path = self.image_watermark_path
        imgwm_scale = self.imgwm_scale_slider.value()
        imgwm_opacity = self.imgwm_opacity_slider.value()
        imgwm_size_mode = self.imgwm_size_mode_combo.currentIndex()
        imgwm_width = self.imgwm_width_input.value()
        imgwm_height = self.imgwm_height_input.value()
        size_mode = self.size_mode_combo.currentIndex()
        width = self.width_input.value()
        height = self.height_input.value()
        percent = self.percent_input.value()

        style = ""
        if is_bold and is_italic:
            style = "-bolditalic"
        elif is_bold:
            style = "-bold"
        elif is_italic:
            style = "-italic"
        font_path = None
        if font_base in self.font_files:
            if style in self.font_files[font_base]:
                font_path = self.font_files[font_base][style]
            elif "-bold" in self.font_files[font_base] and is_bold:
                font_path = self.font_files[font_base]["-bold"]
            elif "-italic" in self.font_files[font_base] and is_italic:
                font_path = self.font_files[font_base]["-italic"]
            elif "" in self.font_files[font_base]:
                font_path = self.font_files[font_base][""]
            else:
                font_path = list(self.font_files[font_base].values())[0]

        for index in range(self.image_list.count()):
            item = self.image_list.item(index)
            input_path = item.toolTip()
            base_name, _ = os.path.splitext(os.path.basename(input_path))
            output_name = f"{prefix + '_' if prefix else ''}{base_name}{suffix}.{output_format}"
            output_path = os.path.join(folder, output_name)

            with Image.open(input_path) as img:
                orig_w, orig_h = img.size
                if size_mode == 1:
                    new_w = width
                    new_h = int(orig_h * (width / orig_w))
                    img = img.resize((new_w, new_h), resample=resample_method)
                elif size_mode == 2:
                    new_h = height
                    new_w = int(orig_w * (height / orig_h))
                    img = img.resize((new_w, new_h), resample=resample_method)
                elif size_mode == 3:
                    scale = percent / 100.0
                    new_w = int(orig_w * scale)
                    new_h = int(orig_h * scale)
                    img = img.resize((new_w, new_h), resample=resample_method)

                img = img.convert("RGBA")
                if watermark_text:
                    watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(watermark_layer)
                    try:
                        if font_path:
                            font = ImageFont.truetype(font_path, font_size)
                        else:
                            font = ImageFont.load_default()
                    except Exception:
                        font = ImageFont.load_default()
                    try:
                        bbox = draw.textbbox((0, 0), watermark_text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except AttributeError:
                        text_width, text_height = font.getsize(watermark_text)
                    alpha = int(255 * (watermark_opacity / 100))
                    x, y = self.get_watermark_pos(img.size, (text_width, text_height))
                    if shadow_enabled:
                        shadow_offset = 2
                        draw.text((x + shadow_offset, y + shadow_offset), watermark_text, font=font, fill=(0, 0, 0, alpha))
                    if outline_enabled:
                        outline_range = 2
                        for dx in range(-outline_range, outline_range + 1):
                            for dy in range(-outline_range, outline_range + 1):
                                if dx == 0 and dy == 0:
                                    continue
                                draw.text((x + dx, y + dy), watermark_text, font=font, fill=(0, 0, 0, alpha))
                    draw.text((x, y), watermark_text, font=font, fill=(*self.watermark_color, alpha))
                    img = Image.alpha_composite(img, watermark_layer)

                if imgwm_path:
                    try:
                        with Image.open(imgwm_path) as wm_img:
                            wm_img = wm_img.convert("RGBA")
                            if imgwm_size_mode == 0:
                                scale = imgwm_scale / 100.0
                                new_w = int(img.size[0] * scale)
                                new_h = int(wm_img.size[1] * (new_w / wm_img.size[0]))
                            elif imgwm_size_mode == 1:
                                new_w = imgwm_width
                                new_h = int(wm_img.size[1] * (new_w / wm_img.size[0]))
                            elif imgwm_size_mode == 2:
                                new_h = imgwm_height
                                new_w = int(wm_img.size[0] * (new_h / wm_img.size[1]))
                            else:
                                new_w, new_h = wm_img.size
                            wm_img = wm_img.resize((new_w, new_h), resample=resample_method)
                            if imgwm_opacity < 100:
                                alpha = wm_img.split()[-1].point(lambda p: int(p * imgwm_opacity / 100))
                                wm_img.putalpha(alpha)
                            x, y = self.get_watermark_pos(img.size, (new_w, new_h))
                            img.alpha_composite(wm_img, (x, y))
                    except Exception as e:
                        print(f"图片水印处理失败: {e}")

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


    def set_watermark_pos_mode(self, mode):
        self.watermark_pos_mode = mode
        self.custom_pos = None
        self.update_pos_buttons()
        self.update_preview()

    def update_pos_buttons(self):
        for btn, (_, mode) in zip(self.pos_buttons, [
            ("左上", "left_top"), ("上中", "center_top"), ("右上", "right_top"),
            ("左中", "left_center"), ("中心", "center"), ("右中", "right_center"),
            ("左下", "left_bottom"), ("下中", "center_bottom"), ("右下", "right_bottom")
        ]):
            btn.setChecked(self.watermark_pos_mode == mode)

    def on_image_selected(self, index):
        self.current_preview_index = index
        # 删除重置 custom_pos 的逻辑，保留拖拽后的水印位置
        self.update_preview()

    def update_preview(self):
        # 获取当前图片
        if self.image_list.count() == 0 or self.current_preview_index < 0:
            self.preview_area.clear()
            return
        item = self.image_list.item(self.current_preview_index)
        img_path = item.toolTip()
        try:
            with Image.open(img_path) as img:
                # 尺寸调整
                size_mode = self.size_mode_combo.currentIndex()
                width = self.width_input.value()
                height = self.height_input.value()
                percent = self.percent_input.value()
                orig_w, orig_h = img.size
                if size_mode == 1:
                    new_w = width
                    new_h = int(orig_h * (width / orig_w))
                    img = img.resize((new_w, new_h), resample=resample_method)
                elif size_mode == 2:
                    new_h = height
                    new_w = int(orig_w * (height / orig_h))
                    img = img.resize((new_w, new_h), resample=resample_method)
                elif size_mode == 3:
                    scale = percent / 100.0
                    new_w = int(orig_w * scale)
                    new_h = int(orig_h * scale)
                    img = img.resize((new_w, new_h), resample=resample_method)
                # 水印合成（与导出一致，位置用 self.get_watermark_pos）
                img = img.convert("RGBA")
                preview_img = img.copy()
                # 文本水印
                watermark_text = self.watermark_text_input.text()
                if watermark_text:
                    watermark_layer = Image.new("RGBA", preview_img.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(watermark_layer)
                    font_path = None
                    font_base = self.font_combo.currentText()
                    font_size = self.font_size_spin.value()
                    is_bold = self.bold_checkbox.isChecked()
                    is_italic = self.italic_checkbox.isChecked()
                    style = ""
                    if is_bold and is_italic:
                        style = "-bolditalic"
                    elif is_bold:
                        style = "-bold"
                    elif is_italic:
                        style = "-italic"
                    if font_base in self.font_files:
                        if style in self.font_files[font_base]:
                            font_path = self.font_files[font_base][style]
                        elif "-bold" in self.font_files[font_base] and is_bold:
                            font_path = self.font_files[font_base]["-bold"]
                        elif "-italic" in self.font_files[font_base] and is_italic:
                            font_path = self.font_files[font_base]["-italic"]
                        elif "" in self.font_files[font_base]:
                            font_path = self.font_files[font_base][""]
                        else:
                            font_path = list(self.font_files[font_base].values())[0]
                    try:
                        if font_path:
                            font = ImageFont.truetype(font_path, font_size)
                        else:
                            font = ImageFont.load_default()
                    except Exception:
                        font = ImageFont.load_default()
                    try:
                        bbox = draw.textbbox((0, 0), watermark_text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except AttributeError:
                        text_width, text_height = font.getsize(watermark_text)
                    alpha = int(255 * (self.watermark_opacity_slider.value() / 100))
                    # 位置
                    x, y = self.get_watermark_pos(preview_img.size, (text_width, text_height))
                    # 阴影
                    if self.shadow_checkbox.isChecked():
                        shadow_offset = 2
                        draw.text((x + shadow_offset, y + shadow_offset), watermark_text, font=font, fill=(0, 0, 0, alpha))
                    # 描边
                    if self.outline_checkbox.isChecked():
                        outline_range = 2
                        for dx in range(-outline_range, outline_range + 1):
                            for dy in range(-outline_range, outline_range + 1):
                                if dx == 0 and dy == 0:
                                    continue
                                draw.text((x + dx, y + dy), watermark_text, font=font, fill=(0, 0, 0, alpha))
                    # 正文
                    draw.text((x, y), watermark_text, font=font, fill=(*self.watermark_color, alpha))
                    preview_img = Image.alpha_composite(preview_img, watermark_layer)
                # 图片水印
                imgwm_path = self.image_watermark_path
                imgwm_scale = self.imgwm_scale_slider.value()
                imgwm_opacity = self.imgwm_opacity_slider.value()
                imgwm_size_mode = self.imgwm_size_mode_combo.currentIndex()
                imgwm_width = self.imgwm_width_input.value()
                imgwm_height = self.imgwm_height_input.value()
                if imgwm_path:
                    try:
                        with Image.open(imgwm_path) as wm_img:
                            wm_img = wm_img.convert("RGBA")
                            if imgwm_size_mode == 0:
                                scale = imgwm_scale / 100.0
                                new_w = int(preview_img.size[0] * scale)
                                new_h = int(wm_img.size[1] * (new_w / wm_img.size[0]))
                            elif imgwm_size_mode == 1:
                                new_w = imgwm_width
                                new_h = int(wm_img.size[1] * (new_w / wm_img.size[0]))
                            elif imgwm_size_mode == 2:
                                new_h = imgwm_height
                                new_w = int(wm_img.size[0] * (new_h / wm_img.size[1]))
                            else:
                                new_w, new_h = wm_img.size
                            wm_img = wm_img.resize((new_w, new_h), resample=resample_method)
                            if imgwm_opacity < 100:
                                alpha = wm_img.split()[-1].point(lambda p: int(p * imgwm_opacity / 100))
                                wm_img.putalpha(alpha)
                            # 位置
                            x, y = self.get_watermark_pos(preview_img.size, (new_w, new_h))
                            preview_img.alpha_composite(wm_img, (x, y))
                    except Exception as e:
                        pass
                # 转为QPixmap显示
                qimg = QImage(preview_img.tobytes("raw", "RGBA"), preview_img.size[0], preview_img.size[1], QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimg)
                self.preview_pixmap = pixmap
                self.preview_area.setPixmap(pixmap.scaled(self.preview_area.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception:
            self.preview_area.clear()

    def get_watermark_pos(self, img_size, wm_size):
        # 九宫格/自定义坐标
        if self.custom_pos:
            x_percent, y_percent = self.custom_pos
            x = int(x_percent * img_size[0])
            y = int(y_percent * img_size[1])
            return x, y
        mode = self.watermark_pos_mode
        W, H = img_size
        w, h = wm_size
        margin = 20
        pos_map = {
            "left_top": (margin, margin),
            "center_top": ((W - w) // 2, margin),
            "right_top": (W - w - margin, margin),
            "left_center": (margin, (H - h) // 2),
            "center": ((W - w) // 2, (H - h) // 2),
            "right_center": (W - w - margin, (H - h) // 2),
            "left_bottom": (margin, H - h - margin),
            "center_bottom": ((W - w) // 2, H - h - margin),
            "right_bottom": (W - w - margin, H - h - margin),
        }
        return pos_map.get(mode, (W - w - margin, H - h - margin))

    def save_template(self):
        name, ok = QInputDialog.getText(self, "保存模板", "请输入模板名称：")
        if ok and name.strip():
            name = name.strip()
            if name in self.templates:
                reply = QMessageBox.question(self, "覆盖模板", f"模板 '{name}' 已存在，是否覆盖？", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            template = self.get_current_settings()
            self.templates[name] = template
            self.save_templates_to_file()
            self.update_template_selector()
            QMessageBox.information(self, "成功", f"模板 '{name}' 已保存")

    def load_template(self):
        name = self.template_selector.currentText()
        if name in self.templates:
            template = self.templates[name]
            self.apply_settings(template)
            QMessageBox.information(self, "成功", f"模板 {name} 已加载")

    def delete_template(self):
        name = self.template_selector.currentText()
        if name in self.templates:
            del self.templates[name]
            self.save_templates_to_file()
            self.update_template_selector()
            QMessageBox.information(self, "成功", f"模板 {name} 已删除")

    def update_template_selector(self):
        self.template_selector.clear()
        self.template_selector.addItems(self.templates.keys())

    def get_current_settings(self):
        return {
            "watermark_text": self.watermark_text_input.text(),
            "font": self.font_combo.currentText(),
            "font_size": self.font_size_spin.value(),
            "bold": self.bold_checkbox.isChecked(),
            "italic": self.italic_checkbox.isChecked(),
            "color": self.watermark_color,
            "opacity": self.watermark_opacity_slider.value(),
            "shadow": self.shadow_checkbox.isChecked(),
            "outline": self.outline_checkbox.isChecked(),
            "image_watermark_path": self.image_watermark_path,
            "image_watermark_scale": self.imgwm_scale_slider.value(),
            "image_watermark_opacity": self.imgwm_opacity_slider.value(),
            "position_mode": self.watermark_pos_mode,
            "custom_pos": self.custom_pos,
        }

    def apply_settings(self, settings):
        self.watermark_text_input.setText(settings.get("watermark_text", ""))
        self.font_combo.setCurrentText(settings.get("font", ""))
        self.font_size_spin.setValue(settings.get("font_size", 64))
        self.bold_checkbox.setChecked(settings.get("bold", False))
        self.italic_checkbox.setChecked(settings.get("italic", False))
        self.watermark_color = settings.get("color", (255, 255, 255))
        self.color_button.setStyleSheet(f"background-color: rgb{self.watermark_color};")
        self.watermark_opacity_slider.setValue(settings.get("opacity", 50))
        self.shadow_checkbox.setChecked(settings.get("shadow", False))
        self.outline_checkbox.setChecked(settings.get("outline", False))
        self.image_watermark_path = settings.get("image_watermark_path", None)
        self.imgwm_scale_slider.setValue(settings.get("image_watermark_scale", 30))
        self.imgwm_opacity_slider.setValue(settings.get("image_watermark_opacity", 80))
        self.watermark_pos_mode = settings.get("position_mode", "right_bottom")
        self.custom_pos = settings.get("custom_pos", None)
        self.update_pos_buttons()
        self.update_preview()  # 确保预览更新时应用正确的位置

    def load_default_template(self):
        if "default" in self.templates:
            self.apply_settings(self.templates["default"])

    def load_templates(self):
        if os.path.exists(TEMPLATES_FILE):
            with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
                templates = json.load(f)
        elif os.path.exists(DEFAULT_TEMPLATES_FILE):
            with open(DEFAULT_TEMPLATES_FILE, "r", encoding="utf-8") as f:
                templates = json.load(f)
        else:
            templates = {}

        # 如果没有默认模板，则创建一个默认模板
        if "default" not in templates:
            templates["default"] = {
                "watermark_text": "Add Watermark",
                "font": "Arial",
                "font_size": 100,
                "bold": True,
                "italic": False,
                "color": (255, 255, 255),
                "opacity": 80,
                "shadow": True,
                "outline": True,
                "image_watermark_path": None,
                "image_watermark_scale": 30,
                "image_watermark_opacity": 80,
                "position_mode": "right_bottom",
                "custom_pos": None,
            }
            self.save_templates_to_file(templates)

        return templates

    def save_templates_to_file(self, templates=None):
        if templates is None:
            templates = self.templates
        with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=4)


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


class PreviewLabel(QLabel):
    def __init__(self, mainwin):
        super().__init__()
        self.mainwin = mainwin
        self.setMouseTracking(True)
        self.dragging = False
        self.last_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.mainwin.preview_pixmap:
            wm_rect = self.get_watermark_rect()
            if wm_rect and wm_rect.contains(event.pos()):
                self.dragging = True
                self.last_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and self.mainwin.preview_pixmap:
            delta = event.pos() - self.last_pos
            self.last_pos = event.pos()
            pixmap = self.mainwin.preview_pixmap
            label_size = self.size()
            pixmap_size = pixmap.size()
            scale = min(label_size.width() / pixmap_size.width(), label_size.height() / pixmap_size.height())
            offset_x = (label_size.width() - pixmap_size.width() * scale) / 2
            offset_y = (label_size.height() - pixmap_size.height() * scale) / 2
            # 当前水印左上角
            x, y = self.mainwin.get_watermark_pos((pixmap_size.width(), pixmap_size.height()), self.get_wm_size())
            # 鼠标偏移映射到原图
            dx = int(delta.x() / scale)
            dy = int(delta.y() / scale)
            new_x = x + dx
            new_y = y + dy
            # 限制不超界
            new_x = max(0, min(pixmap_size.width() - self.get_wm_size()[0], new_x))
            new_y = max(0, min(pixmap_size.height() - self.get_wm_size()[1], new_y))
            self.mainwin.custom_pos = (new_x / pixmap_size.width(), new_y / pixmap_size.height())  # 转换为百分比
            self.mainwin.watermark_pos_mode = "custom"
            self.mainwin.update_pos_buttons()
            self.mainwin.update_preview()
        else:
            # 鼠标悬停时变手型
            wm_rect = self.get_watermark_rect()
            if wm_rect and wm_rect.contains(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def get_watermark_rect(self):
        # 获取当前水印在label上的rect
        pixmap = self.mainwin.preview_pixmap
        if not pixmap:
            return None
        label_size = self.size()
        pixmap_size = pixmap.size()
        scale = min(label_size.width() / pixmap_size.width(), label_size.height() / pixmap_size.height())
        offset_x = (label_size.width() - pixmap_size.width() * scale) / 2
        offset_y = (label_size.height() - pixmap_size.height() * scale) / 2
        wm_size = self.get_wm_size()
        x, y = self.mainwin.get_watermark_pos((pixmap_size.width(), pixmap_size.height()), wm_size)
        rect_x = int(x * scale + offset_x)
        rect_y = int(y * scale + offset_y)
        rect_w = int(wm_size[0] * scale)
        rect_h = int(wm_size[1] * scale)
        from PyQt5.QtCore import QRect
        return QRect(rect_x, rect_y, rect_w, rect_h)

    def get_wm_size(self):
        # 估算当前水印大小（文本或图片）
        # 只用于判断鼠标是否点中
        if self.mainwin.image_watermark_path:
            imgwm_size_mode = self.mainwin.imgwm_size_mode_combo.currentIndex()
            imgwm_scale = self.mainwin.imgwm_scale_slider.value()
            imgwm_width = self.mainwin.imgwm_width_input.value()
            imgwm_height = self.mainwin.imgwm_height_input.value()
            try:
                with Image.open(self.mainwin.image_watermark_path) as wm_img:
                    if imgwm_size_mode == 0:
                        scale = imgwm_scale / 100.0
                        new_w = int(self.mainwin.preview_pixmap.width() * scale)
                        new_h = int(wm_img.size[1] * (new_w / wm_img.size[0]))
                    elif imgwm_size_mode == 1:
                        new_w = imgwm_width
                        new_h = int(wm_img.size[1] * (new_w / wm_img.size[0]))
                    elif imgwm_size_mode == 2:
                        new_h = imgwm_height
                        new_w = int(wm_img.size[0] * (new_h / wm_img.size[1]))
                    else:
                        new_w, new_h = wm_img.size
                    return (new_w, new_h)
            except Exception:
                pass
        # 文本水印
        watermark_text = self.mainwin.watermark_text_input.text()
        if watermark_text:
            font_path = None
            font_base = self.mainwin.font_combo.currentText()
            font_size = self.mainwin.font_size_spin.value()
            is_bold = self.mainwin.bold_checkbox.isChecked()
            is_italic = self.mainwin.italic_checkbox.isChecked()
            style = ""
            if is_bold and is_italic:
                style = "-bolditalic"
            elif is_bold:
                style = "-bold"
            elif is_italic:
                style = "-italic"
            if font_base in self.mainwin.font_files:
                if style in self.mainwin.font_files[font_base]:
                    font_path = self.mainwin.font_files[font_base][style]
                elif "-bold" in self.mainwin.font_files[font_base] and is_bold:
                    font_path = self.mainwin.font_files[font_base]["-bold"]
                elif "-italic" in self.mainwin.font_files[font_base] and is_italic:
                    font_path = self.mainwin.font_files[font_base]["-italic"]
                elif "" in self.mainwin.font_files[font_base]:
                    font_path = self.mainwin.font_files[font_base][""]
                else:
                    font_path = list(self.mainwin.font_files[font_base].values())[0]
            try:
                if font_path:
                    font = ImageFont.truetype(font_path, font_size)
                else:
                    font = ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()
            try:
                dummy_img = Image.new("RGBA", (100, 100))
                draw = ImageDraw.Draw(dummy_img)
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except Exception:
                text_width, text_height = 100, 40
            return (text_width, text_height)
        return (60, 40)  # 默认
        return (60, 40)  # 默认
        return (60, 40)  # 默认
