#!/usr/bin/env python3
"""
Gemini Watermark Remover - Python Implementation

Core watermark removal engine using reverse alpha blending.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Union
from enum import Enum


class WatermarkSize(Enum):
    """Watermark size enumeration"""
    SMALL = (48, 48, 32)  # (width, height, margin)
    LARGE = (96, 96, 64)  # (width, height, margin)


class WatermarkRemover:
    """
    Gemini Watermark Removal Engine

    Uses reverse alpha blending to mathematically remove watermarks:
    original = (watermarked - alpha * logo_value) / (1 - alpha)
    """

    def __init__(self, logo_value: float = 255.0):
        """
        Initialize the watermark remover.

        Args:
            logo_value: The brightness value of the Gemini logo (default: 255 = white)
        """
        self.logo_value = logo_value
        self.alpha_threshold = 0.002  # Ignore very small alpha (noise)
        self.max_alpha = 0.99  # Avoid division by near-zero

        # Load real alpha maps from Gemini watermark captures
        script_dir = Path(__file__).parent
        bg_48_path = script_dir / 'bg_48.png'
        bg_96_path = script_dir / 'bg_96.png'

        # Fallback to assets directory for development
        if not bg_48_path.exists():
            script_dir = Path(__file__).parent.parent.parent / 'assets'
            bg_48_path = script_dir / 'bg_48.png'
            bg_96_path = script_dir / 'bg_96.png'

        if bg_48_path.exists() and bg_96_path.exists():
            self.alpha_map_small = self.calculate_alpha_map(cv2.imread(str(bg_48_path)))
            self.alpha_map_large = self.calculate_alpha_map(cv2.imread(str(bg_96_path)))
        else:
            # Fall back to default alpha maps if files not found
            self.alpha_map_small = None
            self.alpha_map_large = None

    @staticmethod
    def get_watermark_size(image_width: int, image_height: int) -> WatermarkSize:
        """
        Determine watermark size based on image dimensions.

        Gemini's rules:
        - Large (96x96, 64px margin): BOTH width AND height > 1024
        - Small (48x48, 32px margin): Otherwise (including 1024x1024)

        Args:
            image_width: Image width in pixels
            image_height: Image height in pixels

        Returns:
            WatermarkSize enum (SMALL or LARGE)
        """
        if image_width > 1024 and image_height > 1024:
            return WatermarkSize.LARGE
        return WatermarkSize.SMALL

    @staticmethod
    def calculate_alpha_map(bg_capture: np.ndarray) -> np.ndarray:
        """
        Calculate alpha map from background capture.

        Takes the maximum value across RGB channels and normalizes to [0, 1].

        Args:
            bg_capture: Background capture image (BGR format)

        Returns:
            Alpha map as float32 array with values in [0, 1]
        """
        # Take max of RGB channels for brightness
        if len(bg_capture.shape) == 3 and bg_capture.shape[2] == 3:
            gray = np.max(bg_capture, axis=2)
        else:
            gray = bg_capture

        # Normalize to [0, 1]
        alpha_map = gray.astype(np.float32) / 255.0
        return alpha_map

    @staticmethod
    def create_default_alpha_map(size: WatermarkSize) -> np.ndarray:
        """
        Create a default alpha map when no background capture is available.

        Creates a circular gradient mask centered on the logo.

        Args:
            size: Watermark size (SMALL or LARGE)

        Returns:
            Default alpha map
        """
        width, height, _ = size.value

        # Create circular gradient mask
        y, x = np.ogrid[:height, :width]
        center_y, center_x = height // 2, width // 2

        # Distance from center
        dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        max_dist = min(width, height) // 2

        # Normalize and invert (center = high alpha, edges = low alpha)
        alpha = np.clip(1.0 - (dist / max_dist), 0.0, 1.0)

        # Apply smoothing for more realistic effect
        alpha = alpha ** 1.5  # Power curve for smooth falloff

        return alpha.astype(np.float32)

    def get_watermark_position(self, image_width: int, image_height: int,
                               size: WatermarkSize) -> Tuple[int, int]:
        """
        Calculate watermark position (bottom-right with margin).

        Args:
            image_width: Image width
            image_height: Image height
            size: Watermark size

        Returns:
            (x, y) position of top-left corner of watermark
        """
        w, h, margin = size.value
        x = image_width - w - margin
        y = image_height - h - margin
        return (x, y)

    def remove_watermark_from_region(self, image_region: np.ndarray,
                                     alpha_map: np.ndarray) -> np.ndarray:
        """
        Apply reverse alpha blending to remove watermark from image region.

        Formula: original = (watermarked - alpha * logo) / (1 - alpha)

        Args:
            image_region: Image region containing watermark (BGR, uint8)
            alpha_map: Alpha map for the watermark (float32, [0, 1])

        Returns:
            Restored image region (BGR, uint8)
        """
        # Convert to float for computation
        image_f = image_region.astype(np.float32)

        # Expand alpha to 3 channels (BGR)
        alpha_3ch = np.expand_dims(alpha_map, axis=2)

        # Create mask for pixels above threshold
        valid_mask = alpha_map >= self.alpha_threshold

        # Clamp alpha to avoid division issues (only upper limit!)
        alpha_clamped = np.minimum(alpha_3ch, self.max_alpha)
        one_minus_alpha = 1.0 - alpha_clamped

        # Apply reverse alpha blending
        original = (image_f - alpha_clamped * self.logo_value) / one_minus_alpha

        # Only update pixels with significant watermark effect
        result = image_f.copy()
        for c in range(3):  # Process each channel
            result[:, :, c] = np.where(valid_mask, original[:, :, c], image_f[:, :, c])

        # Clamp to valid range and convert back
        result = np.clip(result, 0, 255).astype(np.uint8)
        return result

    def remove_watermark(self, image: np.ndarray,
                        force_size: Optional[WatermarkSize] = None,
                        alpha_map: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Remove watermark from image.

        Args:
            image: Input image (BGR format)
            force_size: Optional forced watermark size
            alpha_map: Optional custom alpha map (if None, uses default)

        Returns:
            Image with watermark removed
        """
        if image is None or image.size == 0:
            raise ValueError("Empty image provided")

        # Ensure BGR format
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        # Make a copy to avoid modifying original
        result = image.copy()

        # Determine watermark size
        height, width = image.shape[:2]
        size = force_size or self.get_watermark_size(width, height)

        # Get watermark position
        x, y = self.get_watermark_position(width, height, size)
        w, h, _ = size.value

        # Get or create alpha map
        if alpha_map is None:
            # Use preloaded real alpha maps if available
            if size == WatermarkSize.SMALL and self.alpha_map_small is not None:
                alpha_map = self.alpha_map_small
            elif size == WatermarkSize.LARGE and self.alpha_map_large is not None:
                alpha_map = self.alpha_map_large
            else:
                # Fall back to default
                alpha_map = self.create_default_alpha_map(size)
        elif alpha_map.shape != (h, w):
            # Resize if needed
            alpha_map = cv2.resize(alpha_map, (w, h), interpolation=cv2.INTER_LINEAR)

        # Ensure alpha map is within image bounds
        if x < 0 or y < 0 or x + w > width or y + h > height:
            print(f"Warning: Watermark position ({x}, {y}) with size {w}x{h} exceeds image bounds")
            # Adjust to fit within bounds
            x = max(0, min(x, width - w))
            y = max(0, min(y, height - h))

        # Extract region of interest
        roi = result[y:y+h, x:x+w]

        # Remove watermark from region
        cleaned_roi = self.remove_watermark_from_region(roi, alpha_map)

        # Put cleaned region back
        result[y:y+h, x:x+w] = cleaned_roi

        return result

    def add_watermark(self, image: np.ndarray,
                     force_size: Optional[WatermarkSize] = None,
                     alpha_map: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Add watermark to image (for testing purposes).

        Formula: watermarked = alpha * logo + (1 - alpha) * original

        Args:
            image: Input image (BGR format)
            force_size: Optional forced watermark size
            alpha_map: Optional custom alpha map

        Returns:
            Image with watermark added
        """
        if image is None or image.size == 0:
            raise ValueError("Empty image provided")

        # Ensure BGR format
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        result = image.copy()

        # Determine watermark size
        height, width = image.shape[:2]
        size = force_size or self.get_watermark_size(width, height)

        # Get watermark position
        x, y = self.get_watermark_position(width, height, size)
        w, h, _ = size.value

        # Get or create alpha map
        if alpha_map is None:
            # Use preloaded real alpha maps if available
            if size == WatermarkSize.SMALL and self.alpha_map_small is not None:
                alpha_map = self.alpha_map_small
            elif size == WatermarkSize.LARGE and self.alpha_map_large is not None:
                alpha_map = self.alpha_map_large
            else:
                # Fall back to default
                alpha_map = self.create_default_alpha_map(size)
        elif alpha_map.shape != (h, w):
            alpha_map = cv2.resize(alpha_map, (w, h), interpolation=cv2.INTER_LINEAR)

        # Extract ROI
        roi = result[y:y+h, x:x+w].astype(np.float32)
        alpha_3ch = np.expand_dims(alpha_map, axis=2)

        # Apply alpha blending
        watermarked = alpha_3ch * self.logo_value + (1.0 - alpha_3ch) * roi
        result[y:y+h, x:x+w] = np.clip(watermarked, 0, 255).astype(np.uint8)

        return result


def process_image(input_path: Union[str, Path],
                 output_path: Union[str, Path],
                 remove: bool = True,
                 force_size: Optional[WatermarkSize] = None,
                 logo_value: float = 255.0) -> bool:
    """
    Process a single image file.

    Args:
        input_path: Path to input image
        output_path: Path to output image
        remove: If True, remove watermark; if False, add watermark
        force_size: Optional forced watermark size
        logo_value: Logo brightness value

    Returns:
        True if successful, False otherwise
    """
    try:
        input_path = Path(input_path)
        output_path = Path(output_path)

        # Read image
        image = cv2.imread(str(input_path), cv2.IMREAD_COLOR)
        if image is None:
            print(f"Error: Failed to load image: {input_path}")
            return False

        height, width = image.shape[:2]
        print(f"Processing: {input_path.name} ({width}x{height})")

        # Process image
        engine = WatermarkRemover(logo_value=logo_value)

        if remove:
            result = engine.remove_watermark(image, force_size=force_size)
        else:
            result = engine.add_watermark(image, force_size=force_size)

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine output quality based on format
        ext = output_path.suffix.lower()
        if ext in ['.jpg', '.jpeg']:
            # JPEG: 100 = best quality (still lossy)
            success = cv2.imwrite(str(output_path), result, [cv2.IMWRITE_JPEG_QUALITY, 100])
        elif ext == '.png':
            # PNG: lossless, compression level affects size/speed
            success = cv2.imwrite(str(output_path), result, [cv2.IMWRITE_PNG_COMPRESSION, 6])
        elif ext == '.webp':
            # WebP: 101 = lossless mode
            success = cv2.imwrite(str(output_path), result, [cv2.IMWRITE_WEBP_QUALITY, 101])
        else:
            success = cv2.imwrite(str(output_path), result)

        if not success:
            print(f"Error: Failed to write image: {output_path}")
            return False

        print(f"Saved: {output_path.name}")
        return True

    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False


def process_directory(input_dir: Union[str, Path],
                     output_dir: Union[str, Path],
                     remove: bool = True,
                     force_size: Optional[WatermarkSize] = None,
                     logo_value: float = 235.0) -> Tuple[int, int]:
    """
    Process all images in a directory.

    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        remove: If True, remove watermark; if False, add watermark
        force_size: Optional forced watermark size
        logo_value: Logo brightness value

    Returns:
        Tuple of (successful_count, failed_count)
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        print(f"Error: Input directory does not exist: {input_dir}")
        return (0, 0)

    # Supported image formats
    extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']

    # Find all image files
    image_files = []
    for ext in extensions:
        image_files.extend(input_dir.glob(f'*{ext}'))
        image_files.extend(input_dir.glob(f'*{ext.upper()}'))

    if not image_files:
        print(f"No image files found in {input_dir}")
        return (0, 0)

    print(f"Found {len(image_files)} image(s) to process")

    success_count = 0
    fail_count = 0

    for image_file in image_files:
        output_file = output_dir / image_file.name

        if process_image(image_file, output_file, remove, force_size, logo_value):
            success_count += 1
        else:
            fail_count += 1

    print(f"\nProcessing complete: {success_count} succeeded, {fail_count} failed")
    return (success_count, fail_count)
