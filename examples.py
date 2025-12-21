#!/usr/bin/env python3
"""
Simple usage examples for Gemini Watermark Remover
"""

# ============================================================================
# Example 1: 最简单的使用方式 - 使用便捷函数
# ============================================================================

from watermark_remover import process_image

# 处理单个文件
process_image('input.jpg', 'output.jpg')


# ============================================================================
# Example 2: 使用 WatermarkRemover 类（推荐用于批量处理）
# ============================================================================

from watermark_remover import WatermarkRemover
import cv2

# 创建水印移除器实例（可复用）
remover = WatermarkRemover(logo_value=235.0)

# 处理多个图片
image_files = ['image1.jpg', 'image2.jpg', 'image3.jpg']

for img_file in image_files:
    # 读取图片
    image = cv2.imread(img_file)

    # 移除水印
    cleaned = remover.remove_watermark(image)

    # 保存结果
    output_file = img_file.replace('.jpg', '_cleaned.jpg')
    cv2.imwrite(output_file, cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])
    print(f"✓ Processed: {img_file} -> {output_file}")


# ============================================================================
# Example 3: 批量处理整个目录
# ============================================================================

from watermark_remover import process_directory
from pathlib import Path

# 处理整个目录
input_dir = Path('./watermarked_images/')
output_dir = Path('./cleaned_images/')

success_count, fail_count = process_directory(input_dir, output_dir)
print(f"Processed: {success_count} succeeded, {fail_count} failed")


# ============================================================================
# Example 4: 强制指定水印大小
# ============================================================================

from watermark_remover import WatermarkRemover, WatermarkSize
import cv2

remover = WatermarkRemover()
image = cv2.imread('image.jpg')

# 强制使用小尺寸水印（48x48）
cleaned = remover.remove_watermark(image, force_size=WatermarkSize.SMALL)

# 或强制使用大尺寸水印（96x96）
cleaned = remover.remove_watermark(image, force_size=WatermarkSize.LARGE)

cv2.imwrite('output.jpg', cleaned)


# ============================================================================
# Example 5: 添加水印（用于测试）
# ============================================================================

from watermark_remover import WatermarkRemover
import cv2

remover = WatermarkRemover()
image = cv2.imread('original.jpg')

# 添加 Gemini 风格的水印
watermarked = remover.add_watermark(image)
cv2.imwrite('watermarked.jpg', watermarked)


# ============================================================================
# Example 6: 自定义 alpha map
# ============================================================================

from watermark_remover import WatermarkRemover, WatermarkSize
import cv2
import numpy as np

remover = WatermarkRemover()
image = cv2.imread('image.jpg')

# 创建自定义 alpha map（例如：均匀透明度）
custom_alpha = np.ones((48, 48), dtype=np.float32) * 0.3

# 使用自定义 alpha map
cleaned = remover.remove_watermark(
    image,
    force_size=WatermarkSize.SMALL,
    alpha_map=custom_alpha
)

cv2.imwrite('output.jpg', cleaned)


# ============================================================================
# Example 7: 检测图片应该使用的水印大小
# ============================================================================

from watermark_remover import WatermarkRemover
import cv2

image = cv2.imread('image.jpg')
height, width = image.shape[:2]

# 检测应该使用的水印大小
size = WatermarkRemover.get_watermark_size(width, height)
print(f"Image size: {width}x{height}")
print(f"Watermark size: {size.name} ({size.value[0]}x{size.value[1]}, margin: {size.value[2]}px)")


# ============================================================================
# Example 8: 计算 alpha map（从背景捕获）
# ============================================================================

from watermark_remover import WatermarkRemover
import cv2

# 如果你有背景捕获图片（纯色背景 + 水印）
bg_capture = cv2.imread('background_capture.png')

# 计算 alpha map
alpha_map = WatermarkRemover.calculate_alpha_map(bg_capture)

# 使用计算出的 alpha map 处理图片
remover = WatermarkRemover()
image = cv2.imread('watermarked.jpg')
cleaned = remover.remove_watermark(image, alpha_map=alpha_map)
cv2.imwrite('cleaned.jpg', cleaned)


# ============================================================================
# Example 9: 错误处理
# ============================================================================

from watermark_remover import process_image
from pathlib import Path

input_file = Path('watermarked.jpg')

# 检查文件是否存在
if not input_file.exists():
    print(f"Error: File not found: {input_file}")
else:
    # 处理图片
    try:
        success = process_image(input_file, 'output.jpg')
        if success:
            print("✓ Successfully processed!")
        else:
            print("✗ Processing failed!")
    except Exception as e:
        print(f"Error: {e}")


# ============================================================================
# Example 10: 比较原图和处理后的图片质量
# ============================================================================

from watermark_remover import WatermarkRemover
import cv2
import numpy as np

def calculate_psnr(img1, img2):
    """计算 PSNR (Peak Signal-to-Noise Ratio)"""
    mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
    if mse == 0:
        return float('inf')
    return 20 * np.log10(255.0 / np.sqrt(mse))

# 测试：添加水印然后移除，看看能恢复多少
remover = WatermarkRemover()
original = cv2.imread('original.jpg')

# 添加水印
watermarked = remover.add_watermark(original.copy())

# 移除水印
cleaned = remover.remove_watermark(watermarked)

# 计算质量指标
psnr = calculate_psnr(original, cleaned)
print(f"PSNR (original vs cleaned): {psnr:.2f} dB")
print(f"Quality: {'Excellent' if psnr > 50 else 'Good' if psnr > 30 else 'Poor'}")
