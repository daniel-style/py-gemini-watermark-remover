# Gemini Watermark Remover - Python 版本快速入门

## 🎯 5 分钟上手指南

### 步骤 1: 安装依赖

**方式 1: 使用 uv（推荐）**

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync
```

**方式 2: 使用 pip**

```bash
pip install -r requirements.txt
```

就这么简单！只需要两个依赖：
- `opencv-python` - 图像处理
- `numpy` - 数值计算

---

### 步骤 2: 选择使用方式

有两种使用方式：**命令行** 或 **Python 函数调用**

---

## 方式 A: 命令行使用 (CLI)

### 最简单：就地编辑（会覆盖原文件！）

使用 uv：
```bash
uv run python cli.py watermarked.jpg
```

或传统方式：
```bash
python cli.py watermarked.jpg
```

### 推荐：指定输出文件

使用 uv：
```bash
uv run python cli.py -i watermarked.jpg -o clean.jpg
```

或传统方式：
```bash
python cli.py -i watermarked.jpg -o clean.jpg
```

### 批量处理目录

使用 uv：
```bash
uv run python cli.py -i ./input_folder/ -o ./output_folder/
```

或传统方式：
```bash
python cli.py -i ./input_folder/ -o ./output_folder/
```

### 查看帮助

```bash
uv run python cli.py --help
# 或
python cli.py --help
```

---

## 方式 B: Python 函数调用

### 1. 最简单的方式

```python
from watermark_remover import process_image

# 一行代码搞定
process_image('watermarked.jpg', 'clean.jpg')
```

### 2. 处理多个文件（推荐）

```python
from watermark_remover import WatermarkRemover
import cv2

# 创建移除器实例（可复用）
remover = WatermarkRemover()

# 处理多个图片
for img_file in ['img1.jpg', 'img2.jpg', 'img3.jpg']:
    image = cv2.imread(img_file)
    cleaned = remover.remove_watermark(image)
    cv2.imwrite(f'cleaned_{img_file}', cleaned)
```

### 3. 批量处理目录

```python
from watermark_remover import process_directory

# 处理整个目录
success, failed = process_directory('./input/', './output/')
print(f"成功: {success}, 失败: {failed}")
```

---

## 🧪 测试工具

运行测试脚本验证安装：

```bash
python test.py
```

这会：
1. ✓ 创建测试图片
2. ✓ 添加水印
3. ✓ 移除水印
4. ✓ 计算质量指标
5. ✓ 生成示例文件到 `test_output/` 目录

---

## 📝 更多示例

查看 `examples.py` 文件，包含 10 个实用示例：

1. 基础使用
2. 批量处理
3. 目录处理
4. 强制水印大小
5. 添加水印（测试用）
6. 自定义 alpha map
7. 检测水印大小
8. 计算 alpha map
9. 错误处理
10. 质量比较

---

## 🎛️ 高级选项

### 强制指定水印大小

```python
from watermark_remover import WatermarkRemover, WatermarkSize

remover = WatermarkRemover()
cleaned = remover.remove_watermark(
    image,
    force_size=WatermarkSize.SMALL  # 或 LARGE
)
```

### 自定义 logo 亮度值

```python
# 如果默认值 235 效果不好，可以调整
remover = WatermarkRemover(logo_value=230.0)  # 尝试 220-240 之间
```

---

## 📊 性能参考

| 图片尺寸 | 处理时间 | 内存占用 |
|---------|---------|---------|
| 800x600 | ~50ms | ~10MB |
| 1920x1080 | ~200ms | ~25MB |
| 4K (3840x2160) | ~800ms | ~100MB |

*测试环境: MacBook Pro M1, Python 3.11*

---

## ❓ 常见问题

### Q: 处理后图片看起来没变化？
A: 水印是半透明的，在图片查看器中放大到 100% 查看右下角。

### Q: 可以移除其他 AI 的水印吗？
A: 不行，这个工具专门针对 Gemini 的水印模式设计。

### Q: 会降低图片质量吗？
A: 轻微降低。保存时使用最高质量设置（JPEG quality=100），但 JPEG 仍然是有损格式。建议使用 PNG 获得最佳效果。

### Q: 可以移除隐形水印吗？
A: 不能。本工具只移除可见的半透明 logo 水印。

---

## 🎨 图片格式支持

支持的输入/输出格式：
- ✓ JPEG (.jpg, .jpeg)
- ✓ PNG (.png) - 推荐，无损
- ✓ WebP (.webp)
- ✓ BMP (.bmp)

---

## 🔧 故障排除

### ModuleNotFoundError: No module named 'cv2'

```bash
pip install opencv-python
```

### 图片无法加载

检查文件路径是否正确，确保文件存在且格式支持。

### 处理失败

尝试：
1. 使用 `--force-small` 或 `--force-large` 强制水印大小
2. 调整 `--logo-value` 参数（默认 235）
3. 检查图片是否真的有 Gemini 水印

---

## 📚 项目结构

```
python/
├── watermark_remover.py  # 核心引擎（402 行）
├── cli.py                # 命令行界面（241 行）
├── test.py               # 测试脚本（217 行）
├── examples.py           # 使用示例（100+ 行）
├── requirements.txt      # 依赖列表
├── README.md            # 完整文档
└── QUICKSTART.md        # 本文档
```

---

## 🚀 下一步

1. ✅ 运行 `python test.py` 验证安装
2. ✅ 查看 `test_output/` 目录中的测试结果
3. ✅ 尝试处理你自己的图片
4. ✅ 阅读 `examples.py` 了解更多用法
5. ✅ 阅读 `README.md` 了解完整 API 文档

---

## 💡 提示

- **备份原图**：处理前务必备份，特别是使用就地编辑模式
- **PNG 优先**：输出建议用 PNG 格式保证质量
- **批量处理**：使用 `WatermarkRemover` 实例可复用，更高效
- **测试参数**：如果效果不理想，尝试调整 `logo_value` 参数

---

## 📖 完整文档

查看 `README.md` 获取：
- 完整 API 文档
- 工作原理详解
- 性能优化建议
- 更多使用示例

---

**✨ 祝使用愉快！如有问题欢迎提 Issue。**
