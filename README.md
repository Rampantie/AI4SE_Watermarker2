# 图片水印工具

## 项目简介
这是一个基于 Python 和 PyQt5 的本地图片水印工具，支持批量导入图片、调整图片格式、添加前缀/后缀命名规则，并导出为 JPEG 或 PNG 格式。

## 功能特性
- 支持单张图片拖拽导入。
- 支持批量导入图片或整个文件夹。
- 支持主流图片格式（JPEG、PNG、BMP、TIFF），PNG 支持透明通道。
- 用户可选择输出格式（JPEG 或 PNG）。
- 支持自定义文件命名规则（前缀/后缀）。
- 支持调整 JPEG 图片质量。
- 支持缩略图预览。

## 环境依赖
- Python 3.6 或更高版本
- PyQt5
- Pillow

## 安装依赖
在终端或命令提示符中运行以下命令安装依赖：
```bash
pip install PyQt5 Pillow
```

## 运行程序
1. 确保项目文件结构如下：
   ```
   f:\研究生阶段\研一上\AI4SE-photowatermarker2\
   ├── main.py
   ├── ui_main.py
   ├── image_processor.py
   ├── README.md
   ```
2. 运行以下命令启动程序：
   ```bash
   python main.py
   ```

## 使用说明
1. **导入图片**：
   - 点击“导入图片”按钮选择单张或多张图片。
   - 点击“导入文件夹”按钮选择包含图片的文件夹。
   - 支持拖拽图片文件到程序窗口。

2. **设置导出选项**：
   - 选择输出格式（JPEG 或 PNG）。
   - 设置自定义前缀和后缀。
   - 调整 JPEG 压缩质量（仅在选择 JPEG 格式时生效）。

3. **导出图片**：
   - 点击“导出图片”按钮，选择目标文件夹。
   - 程序会将处理后的图片保存到目标文件夹。

## 打包为可执行文件
使用 PyInstaller 将程序打包为 Windows 可执行文件：
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole -i icon.ico main.py
```
打包完成后，生成的可执行文件位于 `dist` 文件夹中。

## 注意事项
- 如果需要忽略某些文件夹（如 `images_test` 或 `__pycache__`），请在 `.gitignore` 文件中添加相应规则。
- 如果遇到网络问题导致无法推送到 GitHub，请检查代理设置或使用 SSH 连接。

## 许可证
本项目遵循 MIT 许可证。
