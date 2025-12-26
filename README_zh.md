# Gemini Watermark Remover - Python Edition

[![PyPI version](https://badge.fury.io/py/py-gemini-watermark-remover.svg)](https://pypi.org/project/py-gemini-watermark-remover/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python 实现的 Gemini 水印移除工具，使用数学精确的反向 Alpha 混合算法。

> 本项目是 [GeminiWatermarkTool](https://github.com/allenk/GeminiWatermarkTool) 的 Python 版本实现。

[English](README.md)

## 效果展示

| 原图（带水印） | 处理后 |
|:---:|:---:|
| <img src="examples/example1.jpg" width="400"> | <img src="examples/example1_cleaned.jpg" width="400"> |
| <img src="examples/example2.jpg" width="400"> | <img src="examples/example2_cleaned.jpg" width="400"> |

## 特性

- 🚀 简单易用：纯 Python 实现，无需编译
- 🎯 精确算法：使用反向 Alpha 混合数学公式
- 📦 最小依赖：仅需 OpenCV 和 NumPy
- 🔄 批量处理：支持单文件和目录批处理
- 🎨 自动检测：自动识别水印尺寸（48x48 或 96x96）
- 🔍 智能检测：多方法评分系统检测水印是否存在（可用 `--no-detect` 禁用）
- 🌐 远程URL支持：直接处理网络图片，无需手动下载

## 安装

### 使用 pip（推荐）

```bash
pip install py-gemini-watermark-remover
```

### 从源码安装

使用 [uv](https://docs.astral.sh/uv/)（极快的 Python 包管理器）：

```bash
# 安装 uv（如果还没有安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖（会自动创建虚拟环境）
uv sync

# 直接运行
uv run python -m gemini_watermark_remover.cli image.jpg
```


## 快速开始

### 示例测试

```bash
# 处理示例图片
uv run python -m gemini_watermark_remover.cli -i examples/example1.jpg -o examples/example1_cleaned.jpg
uv run python -m gemini_watermark_remover.cli -i examples/example2.jpg -o examples/example2_cleaned.jpg
```

### 命令行使用

通过 pip 安装后：

```bash
# 最简单方式 - 就地编辑（会覆盖原文件！）
gemini-watermark watermarked.jpg

# 指定输出文件
gemini-watermark -i watermarked.jpg -o clean.jpg

# 批量处理目录
gemini-watermark -i ./input_folder/ -o ./output_folder/

# 强制指定水印大小
gemini-watermark -i image.jpg -o clean.jpg --force-small

# 显示横幅
gemini-watermark -i image.jpg -o clean.jpg --banner

# 直接处理远程URL
gemini-watermark -i "https://example.com/image.webp" -o clean.webp
```

或使用模块方式：

```bash
# 最简单方式 - 就地编辑（会覆盖原文件！）
uv run python -m gemini_watermark_remover.cli watermarked.jpg

# 指定输出文件
uv run python -m gemini_watermark_remover.cli -i watermarked.jpg -o clean.jpg

# 批量处理目录
uv run python -m gemini_watermark_remover.cli -i ./input_folder/ -o ./output_folder/

# 强制指定水印大小
uv run python -m gemini_watermark_remover.cli -i image.jpg -o clean.jpg --force-small

# 显示横幅
uv run python -m gemini_watermark_remover.cli -i image.jpg -o clean.jpg --banner

# 直接处理远程URL
uv run python -m gemini_watermark_remover.cli -i "https://example.com/image.webp" -o clean.webp
```

或从源码使用：

```bash
# 激活虚拟环境后
python -m gemini_watermark_remover.cli watermarked.jpg
python -m gemini_watermark_remover.cli -i watermarked.jpg -o clean.jpg
```

### Python 函数调用

```python
from gemini_watermark_remover import WatermarkRemover, process_image, process_directory
import cv2

# 方式 1: 使用便捷函数处理单个文件
process_image('watermarked.jpg', 'clean.jpg')

# 方式 1b: 直接处理远程URL
process_image('https://example.com/image.webp', 'clean.webp')

# 方式 2: 使用便捷函数处理目录
success, failed = process_directory('./input/', './output/')

# 方式 3: 使用 WatermarkRemover 类（更多控制）
remover = WatermarkRemover(logo_value=235.0)

# 读取图片
image = cv2.imread('watermarked.jpg')

# 移除水印
cleaned = remover.remove_watermark(image)

# 保存结果
cv2.imwrite('clean.jpg', cleaned)

# 也可以添加水印（用于测试）
watermarked = remover.add_watermark(image)
```

### 高级用法

```python
from gemini_watermark_remover import WatermarkRemover, WatermarkSize
import cv2

# 创建自定义水印移除器
remover = WatermarkRemover(logo_value=235.0)

# 读取图片
image = cv2.imread('image.jpg')

# 强制使用小尺寸水印
cleaned = remover.remove_watermark(
    image,
    force_size=WatermarkSize.SMALL
)

# 使用自定义 alpha map
import numpy as np
custom_alpha = np.ones((48, 48), dtype=np.float32) * 0.5
cleaned = remover.remove_watermark(
    image,
    force_size=WatermarkSize.SMALL,
    alpha_map=custom_alpha
)

# 保存
cv2.imwrite('output.jpg', cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `<file>` | 简单模式：就地编辑图片 |
| `-i, --input` | 输入文件、目录或URL |
| `-o, --output` | 输出文件或目录 |
| `-r, --remove` | 移除水印（默认行为）|
| `--add` | 添加水印（测试用）|
| `--force-small` | 强制使用 48×48 水印 |
| `--force-large` | 强制使用 96×96 水印 |
| `--no-detect` | 跳过水印检测，始终处理 |
| `--logo-value` | Logo 亮度值（默认：235.0）|
| `-v, --verbose` | 详细输出 |
| `-q, --quiet` | 静默模式 |
| `-b, --banner` | 显示 ASCII 横幅 |
| `-V, --version` | 显示版本信息 |
| `-h, --help` | 显示帮助信息 |

## 工作原理

### Gemini 水印机制

Gemini 使用 Alpha 混合添加水印：

```
watermarked = α × logo + (1 - α) × original
```

### 反向 Alpha 混合算法

通过数学逆运算恢复原始像素：

```python
original = (watermarked - α × logo) / (1 - α)
```

### 自动尺寸检测

| 图片尺寸 | 水印大小 | 边距 |
|---------|----------|------|
| W ≤ 1024 **或** H ≤ 1024 | 48×48 | 32px |
| W > 1024 **且** H > 1024 | 96×96 | 64px |

## API 参考

### WatermarkRemover 类

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

### 便捷函数

```python
def process_image(
    input_path: Union[str, Path],  # 本地路径或URL
    output_path: Union[str, Path],
    remove: bool = True,
    force_size: Optional[WatermarkSize] = None,
    logo_value: float = 235.0
) -> bool

def is_url(path: str) -> bool  # 检查路径是否为URL

def load_image_from_url(url: str) -> Optional[np.ndarray]  # 从URL加载图片

def process_directory(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    remove: bool = True,
    force_size: Optional[WatermarkSize] = None,
    logo_value: float = 235.0
) -> Tuple[int, int]
```

## 支持的图片格式

- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- BMP (.bmp)

## 项目结构

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

## 性能

- 单张图片处理：~200-800ms（取决于图片大小和硬件）
- 批量处理：支持顺序处理多个文件
- 内存占用：约为图片大小的 3-4 倍（用于浮点运算）

## 限制

- 仅移除可见水印（右下角半透明 logo）
- 不移除隐藏/隐写水印
- 针对 2025 年 Gemini 当前水印模式设计

## 故障排除

### 问题：处理后图片看起来没变化

水印是半透明的，如果背景色与水印接近，差异可能很微妙。请放大到 100% 查看右下角区域。

### 问题：水印尺寸检测错误

使用 `--force-small` 或 `--force-large` 手动指定：

```bash
uv run python -m gemini_watermark_remover.cli -i image.jpg -o clean.jpg --force-small
```

### 问题：ModuleNotFoundError

确保已安装依赖：

```bash
uv sync
```

## 与 C++ 版本对比

| 特性 | C++ 版本 | Python 版本 |
|------|----------|-------------|
| 安装 | 无需安装（单文件） | 需要 Python 环境 |
| 文件大小 | ~15MB | ~2KB（不含依赖）|
| 运行速度 | 快 | 中等（NumPy 优化）|
| 代码量 | ~1000 行 | ~600 行 |
| 开发效率 | 需要编译 | 改完即用 |
| 易于修改 | 中等 | 容易 |
| 适合场景 | 分发给用户 | 开发/集成 |

## 许可证

MIT License

## 免责声明

本工具仅供**个人和教育用途**。用户需自行确保使用符合适用法律和服务条款。

作者不对因使用本工具而导致的任何数据丢失或图片损坏承担责任。**使用前请备份原始图片。**

## 作者

基于 [GeminiWatermarkTool](https://github.com/allenk/GeminiWatermarkTool) C++ 版本的 Python 实现

---

<p align="center">
  <i>如果这个工具帮到了你，请给项目一个 ⭐</i>
</p>
