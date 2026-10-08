---
name: cn-doc-format
description: 要生成或修改中文 Word 文档时用；含表格单元格对齐硬规则。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [docx, 表格, 排版, 中文文档, 投标文件]
    related_skills: [docx, bid-document-writing]
---

# 中文文档排版规范

## 什么时候用它

- 生成或修改中文 Word 文档：投标文件、施工组织设计、公文、报告、简历
- 用户说“表格做得不行”“排版不对”“套个格式”时

## 表格规则（用户硬性偏好，优先于其他习惯）

按**单元格内容行数**二分，同一张表混用两种样式是正常的：

- 单元格内容 1~2 行 → 水平居中 + 垂直居中（上下左右都居中）
- 单元格内容较多行 → 左对齐 + 首行缩进两个字符（字号磅值 ×2）+ 垂直居中
- 表头 → 一律居中，不受上面规则影响
- 表格标题、表格以外的正文 → 按正文规则排，不受本规则影响

估算行数：每行可容纳汉字数 ≈ 列宽(cm) ÷ (字号pt × 0.0353)，把单元格文本按换行拆分后逐段向上取整求和；总数 ≤2 居中，否则首行缩进。

python-docx 实现要点：

```python
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER     # 两类都要垂直居中
p = cell.paragraphs[0]
if lines <= 2:
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
else:
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Pt(size_pt * 2)
```

## 字体与版式惯例

- 正文：宋体小四（12pt）、1.5 倍行距、首行缩进 2 字符
- 一级标题：黑体 15~16pt；二级标题：黑体 13pt；正文内强调小标题：楷体 12pt 加粗
- 表格正文：宋体五号（10.5pt）；列多排不开的宽表：九号并改横向页
- 页面：A4，页边距上下左右 2.5cm；宽表单独起横向节（`WD_ORIENT.LANDSCAPE` + 互换页宽高）

## 分页与目录

- **不要用 `add_page_break()`**：前一段刚好填满页时会产生整页空白。改用章节标题段落的 `paragraph_format.page_break_before = True`。
- 自动目录：标题段落必须用内置 `Heading 1`/`Heading 2` 样式（否则 TOC 域取不到内容），再插 `TOC \o "1-2" \h \z \u` 域；生成后用 Word COM `doc.Fields.Update()` + `TablesOfContents(1).Update()` 刷页码，否则目录是空的。
- 交付前必做：转 PDF 逐页扫空白页（字符数 <60 且无图 = 空白页）；用 python-docx 遍历 Heading 样式核对章节完整性。

## 只留最终稿（用户硬性规矩）

- 交付目录里**只能有最终稿**：中间产物一律清掉，不留在桌面或交付文件夹。包括：
  - 排版检查用的渲染图（`_check_png/` 之类）与检查用 PDF（`_check_*.pdf`）
  - 生成脚本产生的中间版本（`_v1`、`_旧的`、`最终版2`）
  - 一次性临时脚本（写到 `$LOCALAPPDATA/Temp`，用完删）
- 同一个文件重新生成后，**先把旧版删掉**，不保留历史版本；用户问“之前那份呢”时指当前最终稿即可。
- 检查类文件需要反复用时，统一放到交付目录之外的临时目录（如 `%LOCALAPPDATA%\Temp`），不要混在交付目录里。

## 常见坑

- 表格所有格子一律左对齐或一律居中 —— 不符合本规范，按行数二分。
- 只改已生成的 docx 而不改生成脚本：下次重新生成又变回去。规范改动要同步进生成脚本里的表格函数。
- Word COM 导出 PDF 时“先删旧文件再 SaveAs”：SaveAs 一旦失败旧 PDF 就丢了；残留 Word 进程还会报“对象已与其客户端断开连接”。做法是先 `taskkill /F /IM WINWORD.EXE` 再重开，且先导出到临时名、成功后再改名。
