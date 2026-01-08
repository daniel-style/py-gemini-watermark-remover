#!/usr/bin/env python3
"""
Gemini Watermark Remover - Python Implementation

Core watermark removal engine using reverse alpha blending.
"""

import cv2
import numpy as np
import urllib.request
import urllib.error
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
                        alpha_map: Optional[np.ndarray] = None,
                        auto_detect: bool = True) -> np.ndarray:
        """
        Remove watermark from image.

        Args:
            image: Input image (BGR format)
            force_size: Optional forced watermark size
            alpha_map: Optional custom alpha map (if None, uses default)
            auto_detect: If True, detect watermark before processing (default: True)

        Returns:
            Image with watermark removed (or original if no watermark detected)
        """
        if image is None or image.size == 0:
            raise ValueError("Empty image provided")

        # Ensure BGR format
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        # Auto-detect watermark if enabled
        if auto_detect:
            has_watermark = self.detect_watermark(image, force_size=force_size)
            if not has_watermark:
                return image.copy()

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

    def detect_watermark(self, image: np.ndarray,
                        force_size: Optional[WatermarkSize] = None) -> bool:
        """
        Detect if image has Gemini watermark in bottom-right corner.

        Uses a robust multi-method scoring system combining:
        1. Differential analysis (simulated removal)
        2. Template correlation with alpha maps
        3. Brightness pattern analysis
        4. Edge density analysis

        Args:
            image: Input image (BGR format)
            force_size: Optional forced watermark size to check

        Returns:
            True if watermark detected, False otherwise
        """
        if image is None or image.size == 0:
            return False

        # Ensure BGR format
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        height, width = image.shape[:2]
        size = force_size or self.get_watermark_size(width, height)

        # Get watermark position
        x, y = self.get_watermark_position(width, height, size)
        w, h, _ = size.value

        # Check bounds
        if x < 0 or y < 0 or x + w > width or y + h > height:
            return False

        # Extract ROI
        roi = image[y:y+h, x:x+w]

        # Convert to grayscale for analysis
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY).astype(np.float32)

        # Get alpha map for this size
        if size == WatermarkSize.SMALL and self.alpha_map_small is not None:
            alpha_map = self.alpha_map_small
        elif size == WatermarkSize.LARGE and self.alpha_map_large is not None:
            alpha_map = self.alpha_map_large
        else:
            alpha_map = self.create_default_alpha_map(size)

        # Initialize score
        score = 0.0

        # =================================================================
        # Pre-check: Detect uniform regions (likely plain background)
        # Uniform regions cause false positives because diff pattern always
        # correlates with alpha map when the region has no texture
        # =================================================================
        roi_std = np.std(gray)
        is_uniform_region = roi_std < 15.0  # Low variance = uniform/near-uniform

        # =================================================================
        # Pre-compute: Template Correlation (needed for Method 1 validation)
        # =================================================================
        alpha_normalized = (alpha_map * 255).astype(np.float32)
        try:
            template_correlation = np.corrcoef(gray.flatten(), alpha_normalized.flatten())[0, 1]
            if np.isnan(template_correlation):
                template_correlation = 0
        except Exception:
            template_correlation = 0

        # =================================================================
        # Method 1: Differential Analysis
        # Try removing watermark and check if the difference matches alpha pattern
        # IMPORTANT: Only trust this if template_correlation is also positive,
        # otherwise high diff_correlation on non-watermarked images is false positive
        # =================================================================
        recovered = self.remove_watermark_from_region(roi, alpha_map)
        diff = roi.astype(np.float32) - recovered.astype(np.float32)
        diff_gray = np.mean(np.abs(diff), axis=2)  # Average across channels

        # Check if difference pattern correlates with alpha map
        # Real watermarks create differences that match alpha pattern
        diff_flat = diff_gray.flatten()
        alpha_flat = alpha_map.flatten()

        # Only compute correlation if there's variance in both
        # Skip for uniform regions - correlation is meaningless there
        # Also require positive template correlation to avoid false positives
        if np.std(diff_flat) > 1.0 and np.std(alpha_flat) > 0.01 and not is_uniform_region and template_correlation > 0.1:
            diff_correlation = np.corrcoef(diff_flat, alpha_flat)[0, 1]
            if not np.isnan(diff_correlation):
                if diff_correlation > 0.7:
                    score += 35
                elif diff_correlation > 0.5:
                    score += 25
                elif diff_correlation > 0.3:
                    score += 15

        # Check if difference magnitude is reasonable for watermark
        # Watermark creates noticeable but not extreme differences
        max_diff = np.max(diff_gray)
        mean_diff_high_alpha = np.mean(diff_gray[alpha_map > 0.3]) if np.any(alpha_map > 0.3) else 0

        if 5 < mean_diff_high_alpha < 150 and not is_uniform_region and template_correlation > 0.1:
            score += 15
        if 10 < max_diff < 200 and not is_uniform_region and template_correlation > 0.1:
            score += 10

        # =================================================================
        # Method 2: Template Correlation
        # Watermark creates brightness pattern matching alpha map
        # =================================================================
        if template_correlation > 0.5:
            score += 20
        elif template_correlation > 0.3:
            score += 12
        elif template_correlation > 0.15:
            score += 5

        # =================================================================
        # Method 3: Brightness Analysis
        # High-alpha regions should be brighter than low-alpha regions
        # =================================================================
        high_alpha_mask = alpha_map > 0.3
        low_alpha_mask = alpha_map < 0.1

        if np.any(high_alpha_mask) and np.any(low_alpha_mask):
            mean_high = np.mean(gray[high_alpha_mask])
            mean_low = np.mean(gray[low_alpha_mask])
            brightness_diff = mean_high - mean_low

            # Watermark makes high-alpha regions brighter
            if brightness_diff > 30:
                score += 15
            elif brightness_diff > 15:
                score += 10
            elif brightness_diff > 5:
                score += 5

            # Check uniformity in high-alpha region (watermark is smooth)
            std_high = np.std(gray[high_alpha_mask])
            if std_high < 30:
                score += 10
            elif std_high < 50:
                score += 5

        # =================================================================
        # Method 4: Edge Density Analysis
        # Watermark has soft edges, not sharp content
        # =================================================================
        edges = cv2.Canny(roi, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size

        if edge_density < 0.05:
            score += 10
        elif edge_density < 0.10:
            score += 5
        elif edge_density > 0.15:
            score -= 15  # Penalize high edge density (likely real content)
        elif edge_density > 0.10:
            score -= 5

        # =================================================================
        # Method 4b: Color Variance Analysis
        # Real content often has color variation, watermark is monochrome
        # =================================================================
        roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        saturation = roi_hsv[:, :, 1].astype(np.float32)
        sat_std = np.std(saturation)
        sat_mean = np.mean(saturation)

        # High saturation variance suggests real colorful content
        if sat_std > 30 or sat_mean > 50:
            score -= 15

        # =================================================================
        # Method 4c: Local Contrast Analysis
        # Real content has sharp local contrast, watermark is smooth gradient
        # =================================================================
        # Use Laplacian to detect sharp transitions
        laplacian = cv2.Laplacian(gray, cv2.CV_32F)
        laplacian_std = np.std(np.abs(laplacian))

        if laplacian_std > 20:
            score -= 15  # Sharp local contrast = real content
        elif laplacian_std > 10:
            score -= 5

        # =================================================================
        # Method 5: Gradient Direction Analysis
        # Watermark has radial gradient from center
        # =================================================================
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)

        # Calculate gradient pointing toward/away from center
        center_y, center_x = h // 2, w // 2
        y_coords, x_coords = np.ogrid[:h, :w]
        dx = x_coords - center_x
        dy = y_coords - center_y
        dist = np.sqrt(dx**2 + dy**2) + 1e-6

        # Normalize direction vectors
        dx_norm = dx / dist
        dy_norm = dy / dist

        # Project gradient onto radial direction
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        radial_component = np.abs(grad_x * dx_norm + grad_y * dy_norm)

        # For radial gradient, radial component should dominate
        if np.mean(grad_mag) > 1.0:
            radial_ratio = np.mean(radial_component) / (np.mean(grad_mag) + 1e-6)
            if radial_ratio > 0.6:
                score += 10
            elif radial_ratio > 0.4:
                score += 5

        # =================================================================
        # Final Decision
        # Threshold of 50 provides good balance
        # =================================================================
        return score >= 50

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


def is_url(path: str) -> bool:
    """Check if the path is a URL."""
    return path.startswith(('http://', 'https://'))


def load_image_from_url(url: str) -> Optional[np.ndarray]:
    """
    Load image from URL directly into memory.

    Args:
        url: Image URL

    Returns:
        Image as numpy array (BGR format), or None if failed
    """
    try:
        # Set User-Agent to avoid some server restrictions
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = np.frombuffer(resp.read(), np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_COLOR)
            return image
    except urllib.error.URLError as e:
        print(f"Error: Failed to download image: {e.reason}")
        return None
    except Exception as e:
        print(f"Error: Failed to load image from URL: {e}")
        return None


def process_image(input_path: Union[str, Path],
                 output_path: Union[str, Path],
                 remove: bool = True,
                 force_size: Optional[WatermarkSize] = None,
                 logo_value: float = 255.0,
                 auto_detect: bool = True) -> bool:
    """
    Process a single image file or URL.

    Args:
        input_path: Path to input image or URL
        output_path: Path to output image
        remove: If True, remove watermark; if False, add watermark
        force_size: Optional forced watermark size
        logo_value: Logo brightness value
        auto_detect: If True, detect watermark before processing

    Returns:
        True if successful, False otherwise
    """
    try:
        input_str = str(input_path)
        output_path = Path(output_path)

        # Check if input is URL
        if is_url(input_str):
            print(f"Downloading: {input_str[:80]}...")
            image = load_image_from_url(input_str)
            if image is None:
                return False
            input_name = input_str.split('/')[-1].split('?')[0] or 'remote_image'
        else:
            input_path = Path(input_str)
            # Read image from local file
            image = cv2.imread(str(input_path), cv2.IMREAD_COLOR)
            if image is None:
                print(f"Error: Failed to load image: {input_path}")
                return False
            input_name = input_path.name

        height, width = image.shape[:2]
        print(f"Processing: {input_name} ({width}x{height})")

        # Process image
        engine = WatermarkRemover(logo_value=logo_value)

        if remove:
            result = engine.remove_watermark(image, force_size=force_size, auto_detect=auto_detect)
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
        print(f"Error processing {input_str}: {e}")
        return False


def process_directory(input_dir: Union[str, Path],
                     output_dir: Union[str, Path],
                     remove: bool = True,
                     force_size: Optional[WatermarkSize] = None,
                     logo_value: float = 235.0,
                     auto_detect: bool = True) -> Tuple[int, int, int]:
    """
    Process all images in a directory.

    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        remove: If True, remove watermark; if False, add watermark
        force_size: Optional forced watermark size
        logo_value: Logo brightness value
        auto_detect: If True, detect watermark before processing

    Returns:
        Tuple of (successful_count, skipped_count, failed_count)
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        print(f"Error: Input directory does not exist: {input_dir}")
        return (0, 0, 0)

    # Supported image formats
    extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']

    # Find all image files
    image_files = []
    for ext in extensions:
        image_files.extend(input_dir.glob(f'*{ext}'))
        image_files.extend(input_dir.glob(f'*{ext.upper()}'))

    if not image_files:
        print(f"No image files found in {input_dir}")
        return (0, 0, 0)

    print(f"Found {len(image_files)} image(s) to process")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for image_file in image_files:
        output_file = output_dir / image_file.name

        result = process_image(image_file, output_file, remove, force_size, logo_value, auto_detect)
        if result:
            success_count += 1
        else:
            fail_count += 1

    print(f"\nProcessing complete: {success_count} succeeded, {fail_count} failed")
    return (success_count, skip_count, fail_count)
