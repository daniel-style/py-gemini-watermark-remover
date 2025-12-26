# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python implementation of a Gemini watermark removal tool using mathematical reverse alpha blending. The tool removes the semi-transparent Gemini logo watermark from images in the bottom-right corner.

## Core Algorithm

The watermark removal uses reverse alpha blending mathematics:
- **Gemini's watermark formula**: `watermarked = α × logo + (1 - α) × original`
- **Removal formula**: `original = (watermarked - α × logo) / (1 - α)`
- **Logo value**: Default brightness of 255.0 (white, adjustable)
- **Alpha threshold**: 0.002 minimum to filter noise
- **Real alpha maps**: Uses extracted alpha maps from actual Gemini watermarks (`bg_48.png`, `bg_96.png`)

### Alpha Maps

The tool uses **real alpha maps** extracted from Gemini's actual watermark implementation:
- `bg_48.png`: 48×48 alpha map for small watermarks
- `bg_96.png`: 96×96 alpha map for large watermarks
- Alpha values range from 0.0 to ~0.5 (center ~0.502)
- These are loaded at initialization and provide accurate watermark removal

## Watermark Size Detection Rules

Critical logic in `src/gemini_watermark_remover/watermark_remover.py:41-58`:
- **LARGE (96×96, 64px margin)**: When BOTH width AND height > 1024
- **SMALL (48×48, 32px margin)**: Otherwise (including exactly 1024×1024)

The watermark is always positioned in the bottom-right corner with the specified margin.

## Watermark Detection

The tool includes automatic watermark detection (can be disabled with `--no-detect`). Detection logic at line 268-450 uses a multi-method scoring system:

1. **Differential analysis**: Simulates watermark removal and checks if difference pattern correlates with alpha map (up to 60 points)
2. **Template correlation**: Compares ROI brightness with alpha map pattern (up to 20 points)
3. **Brightness analysis**: Checks brightness difference between high/low alpha regions and uniformity (up to 25 points)
4. **Edge density**: Watermarks have soft edges, penalizes sharp content (up to 10 points, -10 penalty)
5. **Gradient direction**: Watermarks have radial gradient from center (up to 10 points)

Detection threshold: score >= 50. This scoring system provides robust detection on various backgrounds (light, dark, textured).

## Development Commands

### Install Dependencies

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies (creates .venv automatically)
uv sync

# Or install uv first if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Dependencies: `opencv-python>=4.8.0` and `numpy>=1.24.0` (defined in `pyproject.toml`)

### Run Tests
```bash
# Using uv
uv run python tests/test.py

# Or activate venv manually
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python tests/test.py
```
Creates test images in `test_output/`, adds/removes watermarks, and calculates PSNR quality metrics.

### CLI Usage
```bash
# Using uv (recommended)
uv run python -m gemini_watermark_remover.cli -i watermarked.jpg -o clean.jpg

# Or activate venv manually
source .venv/bin/activate
python -m gemini_watermark_remover.cli -i watermarked.jpg -o clean.jpg

# Process single image
uv run python -m gemini_watermark_remover.cli -i watermarked.jpg -o clean.jpg

# Batch process directory
uv run python -m gemini_watermark_remover.cli -i ./input_folder/ -o ./output_folder/

# In-place edit (overwrites original)
uv run python -m gemini_watermark_remover.cli image.jpg

# Force watermark size
uv run python -m gemini_watermark_remover.cli -i image.jpg -o clean.jpg --force-small
uv run python -m gemini_watermark_remover.cli -i image.jpg -o clean.jpg --force-large
```

## Code Architecture

### Core Module: `src/gemini_watermark_remover/watermark_remover.py` (~400 lines)

**WatermarkRemover Class** (main engine):
- `__init__(logo_value=235.0)`: Initialize with logo brightness
- `remove_watermark(image, force_size, alpha_map)`: Remove watermark from image
- `add_watermark(image, force_size, alpha_map)`: Add watermark for testing
- Static methods for size detection and alpha map calculation

**Key Processing Flow** (`remove_watermark` at line 171):
1. Detect or use forced watermark size
2. Calculate watermark position (bottom-right corner)
3. Get or create alpha map (circular gradient by default)
4. Extract ROI (region of interest)
5. Apply reverse alpha blending formula
6. Clamp results to valid range [0, 255]

**Convenience Functions**:
- `process_image(input_path, output_path, ...)`: Single file processing
- `process_directory(input_dir, output_dir, ...)`: Batch processing with count tracking

### CLI Interface: `src/gemini_watermark_remover/cli.py` (~240 lines)

Argument parser with two modes:
- **Simple mode**: Single positional argument (in-place edit)
- **Standard mode**: `-i/--input` and `-o/--output` required

Supports both file and directory processing with automatic detection.

### Test Suite: `tests/test.py` (~220 lines)

Comprehensive test coverage:
- Creates gradient test images of various sizes
- Tests both watermark addition and removal
- Tests size detection edge cases (e.g., exactly 1024×1024)
- Calculates PSNR quality metrics
- Demonstrates CLI and API usage

## Image Format Support

**Supported formats**: JPEG, PNG, WebP, BMP
**Quality settings**:
- JPEG: Quality 100 (best, but still lossy)
- PNG: Compression level 6 (lossless, recommended for best quality)
- WebP: Quality 101 (lossless mode)

## Important Implementation Details

### Alpha Map Creation (`create_default_alpha_map` at line 84)
Creates a circular gradient mask centered on the logo with power curve smoothing (`alpha ** 1.5`) for realistic falloff.

### Reverse Alpha Blending (`remove_watermark_from_region` at line 132)
- Converts to float32 for precision
- Expands alpha to 3 channels (BGR)
- Only processes pixels above threshold
- Clamps alpha between `alpha_threshold` and `max_alpha` to avoid division issues
- Clips final result to valid uint8 range

### Error Handling
- Validates image exists and loads successfully
- Converts grayscale/RGBA to BGR automatically
- Checks watermark position stays within image bounds
- Adjusts position if needed to prevent out-of-bounds access

## Known Limitations

- Only removes visible watermarks (not hidden/steganographic watermarks)
- Designed specifically for Gemini's 2025 watermark pattern
- Cannot remove watermarks from other AI systems
- JPEG output has some quality loss despite quality=100

## Testing Strategy

When modifying the algorithm:
1. Run `uv run python tests/test.py` to verify basic functionality
2. Check PSNR values remain high (>30 dB is good, >50 dB is excellent)
3. Visually inspect test images in `test_output/` directory
4. Test edge cases: exactly 1024×1024, forced size overrides
5. Verify both small (48×48) and large (96×96) watermarks work correctly

## Project Management

This project uses `uv` for dependency management with all dependencies defined in `pyproject.toml`. The `requirements.txt` file is kept for backwards compatibility but `pyproject.toml` is the source of truth.
