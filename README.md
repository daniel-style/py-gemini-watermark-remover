# Gemini Watermark Remover - Python Edition

A Python implementation of Gemini watermark removal tool using mathematical reverse alpha blending.

> This project is a Python port of [GeminiWatermarkTool](https://github.com/allenk/GeminiWatermarkTool).

[中文文档](README_zh.md)

## Demo

| Original (Watermarked) | Cleaned |
|:---:|:---:|
| ![example1](examples/example1.jpg) | ![example1_cleaned](examples/example1_cleaned.jpg) |
| ![example2](examples/example2.jpg) | ![example2_cleaned](examples/example2_cleaned.jpg) |

## Features

- 🚀 Easy to use: Pure Python implementation, no compilation needed
- 🎯 Precise algorithm: Uses reverse alpha blending mathematics
- 📦 Minimal dependencies: Only requires OpenCV and NumPy
- 🔄 Batch processing: Supports single file and directory processing
- 🎨 Auto detection: Automatically detects watermark size (48x48 or 96x96)

## Installation

### Using uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package and project manager.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (creates virtual environment automatically)
uv sync

# Run directly
uv run python -m gemini_watermark_remover.cli image.jpg
```

## Quick Start

### Example Test

```bash
# Process example images
uv run python -m gemini_watermark_remover.cli -i examples/example1.jpg -o examples/example1_cleaned.jpg
uv run python -m gemini_watermark_remover.cli -i examples/example2.jpg -o examples/example2_cleaned.jpg
```

### CLI Usage

Using uv (recommended):

```bash
# Simple mode - in-place edit (overwrites original!)
uv run python -m gemini_watermark_remover.cli watermarked.jpg

# Specify output file
uv run python -m gemini_watermark_remover.cli -i watermarked.jpg -o clean.jpg

# Batch process directory
uv run python -m gemini_watermark_remover.cli -i ./input_folder/ -o ./output_folder/

# Force watermark size
uv run python -m gemini_watermark_remover.cli -i image.jpg -o clean.jpg --force-small

# Show banner
uv run python -m gemini_watermark_remover.cli -i image.jpg -o clean.jpg --banner
```

Or using traditional method:

```bash
# After activating virtual environment
python -m gemini_watermark_remover.cli watermarked.jpg
python -m gemini_watermark_remover.cli -i watermarked.jpg -o clean.jpg
```

### Python API

```python
from gemini_watermark_remover import WatermarkRemover, process_image, process_directory
import cv2

# Method 1: Use convenience function for single file
process_image('watermarked.jpg', 'clean.jpg')

# Method 2: Use convenience function for directory
success, failed = process_directory('./input/', './output/')

# Method 3: Use WatermarkRemover class (more control)
remover = WatermarkRemover(logo_value=235.0)

# Read image
image = cv2.imread('watermarked.jpg')

# Remove watermark
cleaned = remover.remove_watermark(image)

# Save result
cv2.imwrite('clean.jpg', cleaned)

# Can also add watermark (for testing)
watermarked = remover.add_watermark(image)
```

### Advanced Usage

```python
from gemini_watermark_remover import WatermarkRemover, WatermarkSize
import cv2

# Create custom watermark remover
remover = WatermarkRemover(logo_value=235.0)

# Read image
image = cv2.imread('image.jpg')

# Force small watermark size
cleaned = remover.remove_watermark(
    image,
    force_size=WatermarkSize.SMALL
)

# Use custom alpha map
import numpy as np
custom_alpha = np.ones((48, 48), dtype=np.float32) * 0.5
cleaned = remover.remove_watermark(
    image,
    force_size=WatermarkSize.SMALL,
    alpha_map=custom_alpha
)

# Save
cv2.imwrite('output.jpg', cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])
```

## CLI Arguments

| Argument | Description |
|----------|-------------|
| `<file>` | Simple mode: edit image in-place |
| `-i, --input` | Input file or directory |
| `-o, --output` | Output file or directory |
| `-r, --remove` | Remove watermark (default behavior) |
| `--add` | Add watermark (for testing) |
| `--force-small` | Force 48×48 watermark |
| `--force-large` | Force 96×96 watermark |
| `--logo-value` | Logo brightness value (default: 235.0) |
| `-v, --verbose` | Enable verbose output |
| `-q, --quiet` | Quiet mode |
| `-b, --banner` | Show ASCII banner |
| `-V, --version` | Show version |
| `-h, --help` | Show help |

## How It Works

### Gemini Watermark Mechanism

Gemini adds watermarks using alpha blending:

```
watermarked = α × logo + (1 - α) × original
```

### Reverse Alpha Blending Algorithm

Recover original pixels through mathematical inversion:

```python
original = (watermarked - α × logo) / (1 - α)
```

### Automatic Size Detection

| Image Size | Watermark Size | Margin |
|------------|----------------|--------|
| W ≤ 1024 **or** H ≤ 1024 | 48×48 | 32px |
| W > 1024 **and** H > 1024 | 96×96 | 64px |

## API Reference

### WatermarkRemover Class

```python
class WatermarkRemover:
    def __init__(self, logo_value: float = 235.0)

    def remove_watermark(
        self,
        image: np.ndarray,
        force_size: Optional[WatermarkSize] = None,
        alpha_map: Optional[np.ndarray] = None
    ) -> np.ndarray

    def add_watermark(
        self,
        image: np.ndarray,
        force_size: Optional[WatermarkSize] = None,
        alpha_map: Optional[np.ndarray] = None
    ) -> np.ndarray

    @staticmethod
    def get_watermark_size(width: int, height: int) -> WatermarkSize

    @staticmethod
    def calculate_alpha_map(bg_capture: np.ndarray) -> np.ndarray
```

### Convenience Functions

```python
def process_image(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    remove: bool = True,
    force_size: Optional[WatermarkSize] = None,
    logo_value: float = 235.0
) -> bool

def process_directory(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    remove: bool = True,
    force_size: Optional[WatermarkSize] = None,
    logo_value: float = 235.0
) -> Tuple[int, int]
```

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- BMP (.bmp)

## Project Structure

```
py-gemini-watermark-remover/
├── assets/
│   ├── bg_48.png
│   └── bg_96.png
├── src/
│   └── gemini_watermark_remover/
│       ├── __init__.py
│       ├── cli.py
│       └── watermark_remover.py
├── tests/
│   └── test.py
├── examples/
│   ├── example1.jpg
│   ├── example1_cleaned.jpg
│   ├── example2.jpg
│   └── example2_cleaned.jpg
├── README.md
├── README_zh.md
└── pyproject.toml
```

## Performance

- Single image processing: ~200-800ms (depends on image size and hardware)
- Batch processing: Sequential processing of multiple files
- Memory usage: ~3-4x image size (for floating-point operations)

## Limitations

- Only removes visible watermarks (bottom-right semi-transparent logo)
- Does not remove hidden/steganographic watermarks
- Designed for Gemini's current watermark pattern (2025)

## Troubleshooting

### Issue: Processed image looks unchanged

The watermark is semi-transparent. If the background color is similar to the watermark, the difference may be subtle. Zoom to 100% and check the bottom-right corner.

### Issue: Wrong watermark size detected

Use `--force-small` or `--force-large` to manually specify:

```bash
uv run python -m gemini_watermark_remover.cli -i image.jpg -o clean.jpg --force-small
```

### Issue: ModuleNotFoundError

Make sure dependencies are installed:

```bash
uv sync
```

## Comparison with C++ Version

| Feature | C++ Version | Python Version |
|---------|-------------|----------------|
| Installation | No installation (single file) | Requires Python environment |
| File size | ~15MB | ~2KB (excluding dependencies) |
| Speed | Fast | Medium (NumPy optimized) |
| Code size | ~1000 lines | ~600 lines |
| Development | Requires compilation | Edit and run |
| Easy to modify | Medium | Easy |
| Best for | Distribution to users | Development/Integration |

## License

MIT License

## Disclaimer

This tool is for **personal and educational use only**. Users must ensure their use complies with applicable laws and terms of service.

The author is not responsible for any data loss or image corruption caused by using this tool. **Please backup original images before use.**

## Credits

Python implementation based on [GeminiWatermarkTool](https://github.com/allenk/GeminiWatermarkTool) C++ version.

---

<p align="center">
  <i>If this tool helped you, please give the project a ⭐</i>
</p>
