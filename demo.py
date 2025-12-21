#!/usr/bin/env python3
"""
Quick demo script - Shows the most common use cases
"""

print("=" * 70)
print("Gemini Watermark Remover - Quick Demo")
print("=" * 70)

# Demo 1: Simple function call
print("\n[Demo 1] Single image processing")
print("-" * 70)
print("""
from watermark_remover import process_image

# Process one image
process_image('watermarked.jpg', 'clean.jpg')
""")

# Demo 2: Batch processing
print("\n[Demo 2] Batch processing")
print("-" * 70)
print("""
from watermark_remover import WatermarkRemover
import cv2

remover = WatermarkRemover()

for img_file in ['img1.jpg', 'img2.jpg', 'img3.jpg']:
    image = cv2.imread(img_file)
    cleaned = remover.remove_watermark(image)
    cv2.imwrite(f'cleaned_{img_file}', cleaned)
""")

# Demo 3: Directory processing
print("\n[Demo 3] Process entire directory")
print("-" * 70)
print("""
from watermark_remover import process_directory

success, failed = process_directory('./input/', './output/')
print(f"Results: {success} succeeded, {failed} failed")
""")

# CLI Examples
print("\n[CLI Usage]")
print("-" * 70)
print("# Simple mode (in-place, overwrites original)")
print("$ python cli.py watermarked.jpg")
print()
print("# Recommended: specify output")
print("$ python cli.py -i watermarked.jpg -o clean.jpg")
print()
print("# Batch processing")
print("$ python cli.py -i ./input/ -o ./output/")

print("\n" + "=" * 70)
print("Run 'python test.py' to see a full working example!")
print("=" * 70)
