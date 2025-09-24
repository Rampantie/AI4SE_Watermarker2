from PIL import Image
import os

def process_images(image_paths, output_folder, prefix="", suffix="", quality=80, resize=None, output_format="JPEG"):
    for image_path in image_paths:
        with Image.open(image_path) as img:
            # 调整尺寸
            if resize:
                img = img.resize(resize)

            # 设置输出文件名
            base_name = os.path.basename(image_path)
            name, ext = os.path.splitext(base_name)
            new_name = f"{prefix}{name}{suffix}.{output_format.lower()}"
            output_path = os.path.join(output_folder, new_name)

            # 保存图片
            img.save(output_path, format=output_format, quality=quality if output_format == "JPEG" else None)
