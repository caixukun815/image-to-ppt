# 元素与坐标记录

将每页的 `inventory.json` 写在任务页目录中。所有相对文件路径以该 JSON 所在目录为基准。bbox 一律是原图像素 `[x1, y1, x2, y2]`，不是 `[x, y, width, height]`。

```json
{
  "source": "source.png",
  "source_size": [1672, 941],
  "slide_size_pt": [960, 540],
  "elements": [
    {
      "id": "warning",
      "kind": "svg_icon",
      "bbox": [58, 370, 113, 425],
      "z_order": 5,
      "asset": "svg/warning.svg",
      "placement": "tight",
      "status": "ready"
    },
    {
      "id": "body",
      "kind": "native_text",
      "bbox": [130, 410, 650, 450],
      "z_order": 6,
      "text": "原文内容",
      "font": "实际使用的字体",
      "font_size_pt": 18,
      "status": "ready"
    }
  ]
}
```

kind 使用 `native_text`、`native_shape`、`svg_icon`、`svg_illustration`、`brand_asset`、`transparent_png`、`background_raster`、`native_chart`、`native_table`。

资产项还应记录来源、使用权限、输出哈希、编辑提示词、生成工具、是否补绘。native_text 可增加字重、颜色、对齐、行距。`status` 为 `planned`、`ready` 或 `needs_input`。

若图来自缩略显示，先把所有坐标分别乘以原宽/显示宽、原高/显示高。以中心点调整大小可避免漂移：`left = center_x - width/2`，top 同理。

运行本 Skill 的 `scripts/check_inventory.py inventory.json` 检查源图尺寸、bbox 边界、对象 id、文件路径、比例和未完成项。检查通过只表示记录一致；脚本不能确定框是否圈住了正确对象。
