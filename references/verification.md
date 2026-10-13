# 检查流程

从当前 SKILL.md 所在目录找到 scripts；不要把 Skill 安装目录当作任务输出目录。以下 `python3` 代表环境中有相应依赖的 Python。

1. `python3 scripts/check_inventory.py /task/page/inventory.json`，核查实际像素尺寸、对象位置、资产文件和未解决项。
2. `python3 scripts/validate_svg_assets.py /task/page/svg/`，检查图标内部文字、位图、外部引用和 viewBox。
3. `python3 scripts/visual_compare.py /task/page/source.png /task/preview/slide-1.png --out-dir /task/qa/page-1 --inventory /task/page/inventory.json`，生成并排图、叠加图、热力图和源图框标注。
4. 打开这些图，逐项核对元素清单。差异数值用于寻找问题，不代表自动评分或还原百分比。
5. 打开背景、框架和隐藏普通文本的诊断预览，检查残字、重复图标、重复主体、错 Logo 与缺插图。
6. `python3 scripts/verify_pptx_media.py /task/out/deck.pptx --source /task/page/source.png --require-svg 8 --require-native-text 20`。按本任务实际需求设置数量，多页 source 参数可以重复。
7. 使用当前构建环境的包结构、文本溢出与布局检查。若具备 PowerPoint 本机渲染能力，再确认软件兼容性；未打开 PowerPoint 时不要声称已经做过本机检查。

媒体检查器会追踪实际的幻灯片关系与对象引用、检查媒体哈希，并报告原生文本数量。它不能识别重编码的原始整页图，不能检测图中残字，也不能证明字体和画面准确。

交付前所有可读文字与清晰元素应完成。无法辨认内容、缺失授权资产或缺少生成能力时说明具体未完成区域，不得发明。用户接受局部近似时把近似记录在清单与交付说明中。
