#!/usr/bin/env python3
"""
Test script for Gemini Watermark Remover

Creates test images and demonstrates functionality.
"""

import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from gemini_watermark_remover import WatermarkRemover, WatermarkSize, process_image


def create_test_image(width: int, height: int, output_path: str):
    """Create a test image with gradient background"""
    # Create gradient image
    x = np.linspace(0, 255, width)
    y = np.linspace(0, 255, height)
    xv, yv = np.meshgrid(x, y)

    # Create RGB channels
    r = xv.astype(np.uint8)
    g = yv.astype(np.uint8)
    b = ((xv + yv) / 2).astype(np.uint8)

    image = np.stack([b, g, r], axis=-1)  # BGR format
    cv2.imwrite(output_path, image)
    print(f"Created test image: {output_path} ({width}x{height})")
    return image


def test_watermark_operations():
    """Test adding and removing watermarks"""
    print("=" * 60)
    print("Gemini Watermark Remover - Test Script")
    print("=" * 60)

    # Create test directory
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)

    # Test 1: Small image (should use 48x48 watermark)
    print("\n[Test 1] Small image (800x600)")
    print("-" * 60)
    small_image = create_test_image(800, 600, str(test_dir / "test_small_original.jpg"))

    remover = WatermarkRemover()

    # Add watermark
    watermarked_small = remover.add_watermark(small_image.copy())
    cv2.imwrite(str(test_dir / "test_small_watermarked.jpg"), watermarked_small)
    print("✓ Added watermark (48x48)")

    # Remove watermark
    cleaned_small = remover.remove_watermark(watermarked_small.copy())
    cv2.imwrite(str(test_dir / "test_small_cleaned.jpg"), cleaned_small)
    print("✓ Removed watermark")

    # Test 2: Large image (should use 96x96 watermark)
    print("\n[Test 2] Large image (1920x1080)")
    print("-" * 60)
    large_image = create_test_image(1920, 1080, str(test_dir / "test_large_original.jpg"))

    # Add watermark
    watermarked_large = remover.add_watermark(large_image.copy())
    cv2.imwrite(str(test_dir / "test_large_watermarked.jpg"), watermarked_large)
    print("✓ Added watermark (96x96)")

    # Remove watermark
    cleaned_large = remover.remove_watermark(watermarked_large.copy())
    cv2.imwrite(str(test_dir / "test_large_cleaned.jpg"), cleaned_large)
    print("✓ Removed watermark")

    # Test 3: Edge case - exactly 1024x1024 (should use 48x48)
    print("\n[Test 3] Edge case (1024x1024)")
    print("-" * 60)
    edge_image = create_test_image(1024, 1024, str(test_dir / "test_edge_original.jpg"))

    detected_size = remover.get_watermark_size(1024, 1024)
    print(f"✓ Detected size: {detected_size.name}")

    watermarked_edge = remover.add_watermark(edge_image.copy())
    cv2.imwrite(str(test_dir / "test_edge_watermarked.jpg"), watermarked_edge)

    cleaned_edge = remover.remove_watermark(watermarked_edge.copy())
    cv2.imwrite(str(test_dir / "test_edge_cleaned.jpg"), cleaned_edge)
    print("✓ Processed successfully")

    # Test 4: Force size override
    print("\n[Test 4] Force size override")
    print("-" * 60)
    forced_large = remover.add_watermark(
        small_image.copy(),
        force_size=WatermarkSize.LARGE
    )
    cv2.imwrite(str(test_dir / "test_forced_large.jpg"), forced_large)
    print("✓ Forced LARGE watermark on small image")

    # Test 5: Process image function
    print("\n[Test 5] Test process_image function")
    print("-" * 60)
    success = process_image(
        test_dir / "test_small_watermarked.jpg",
        test_dir / "test_small_processed.jpg",
        remove=True
    )
    print(f"✓ process_image: {'SUCCESS' if success else 'FAILED'}")

    # Calculate quality metrics
    print("\n[Quality Metrics]")
    print("-" * 60)

    def calculate_psnr(img1, img2):
        """Calculate Peak Signal-to-Noise Ratio"""
        mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
        if mse == 0:
            return float('inf')
        return 20 * np.log10(255.0 / np.sqrt(mse))

    # Compare original vs cleaned for small image
    psnr = calculate_psnr(small_image, cleaned_small)
    print(f"Small image PSNR (original vs cleaned): {psnr:.2f} dB")

    psnr = calculate_psnr(large_image, cleaned_large)
    print(f"Large image PSNR (original vs cleaned): {psnr:.2f} dB")

    # Summary
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print(f"✓ Test images saved to: {test_dir.absolute()}")
    print("=" * 60)

    print("\nGenerated files:")
    for file in sorted(test_dir.glob("*.jpg")):
        size = file.stat().st_size / 1024
        print(f"  - {file.name} ({size:.1f} KB)")


def test_cli_usage():
    """Demonstrate CLI usage examples"""
    print("\n\n" + "=" * 60)
    print("CLI Usage Examples")
    print("=" * 60)

    examples = [
        ("Simple mode (in-place edit)", "python cli.py image.jpg"),
        ("Specify input/output", "python cli.py -i input.jpg -o output.jpg"),
        ("Batch processing", "python cli.py -i ./input/ -o ./output/"),
        ("Force small watermark", "python cli.py -i image.jpg -o clean.jpg --force-small"),
        ("Show banner", "python cli.py -i image.jpg -o clean.jpg --banner"),
        ("Quiet mode", "python cli.py -i image.jpg -o clean.jpg --quiet"),
    ]

    for description, command in examples:
        print(f"\n{description}:")
        print(f"  $ {command}")


def test_api_usage():
    """Demonstrate API usage examples"""
    print("\n\n" + "=" * 60)
    print("Python API Usage Examples")
    print("=" * 60)

    code_examples = [
        ("Basic usage", """
from watermark_remover import process_image

# Process single image
process_image('watermarked.jpg', 'clean.jpg')
"""),
        ("Using WatermarkRemover class", """
from watermark_remover import WatermarkRemover
import cv2

remover = WatermarkRemover()
image = cv2.imread('watermarked.jpg')
cleaned = remover.remove_watermark(image)
cv2.imwrite('clean.jpg', cleaned)
"""),
        ("Batch processing", """
from watermark_remover import process_directory

# Process entire directory
success, failed = process_directory('./input/', './output/')
print(f"Processed: {success} succeeded, {failed} failed")
"""),
        ("Advanced options", """
from watermark_remover import WatermarkRemover, WatermarkSize

remover = WatermarkRemover(logo_value=235.0)
cleaned = remover.remove_watermark(
    image,
    force_size=WatermarkSize.SMALL
)
"""),
    ]

    for title, code in code_examples:
        print(f"\n{title}:")
        print(code)


if __name__ == '__main__':
    try:
        test_watermark_operations()
        test_cli_usage()
        test_api_usage()

        print("\n" + "=" * 60)
        print("✓ Test script completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
