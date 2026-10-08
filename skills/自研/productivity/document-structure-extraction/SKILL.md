---
name: document-structure-extraction
description: 当要从大文件里取章节结构或表格版式时使用。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [docx, pdf, 文档结构, 表格版式, 招标文件, extraction]
    related_skills: [ocr-and-documents]
---

# 从大文件里取结构（章节 / 表格版式 / 原文片段）

适用于：几百页、上百 MB 的 docx 或 PDF，要的是它的**结构**而不是全文 —— 目录、章节骨架、某一章原文、
某张表的版式；以及常规工具打不开的场合（`python-docx` 报错、整份太大不能整体处理）。

不适用：扫描件的 OCR、公式、版式还原（用 ocr-and-documents 那套）；只要全文纯文本时 `get_text()` 就够。

## 规矩

1. **先量再取**：docx 先看 `document.xml` 字符数，PDF 先看 `page_count`。心里有数才不会瞎猜
   （一份 779 页的标书，正文段落也就一万六千段）。
2. **按关键词定位页码，再只取那几页 / 那几段**。逐页打印全文会把上下文撑爆，后面每一步都变慢。
3. **量出来的数（列宽、行高、页数、缩进）是这一份文件的实测值，不是规则**。写进别的文档时要标注
   "举例 / 按本次文件"，否则下次会被当成通用标准照搬。
4. 只读不写：不要顺手整体 `re.sub(r'\s+', '', ...)`，换行一没段落就粘成一坨、再也切不开。

## docx：zip + XML 兜底读法

超大或坏的 `.docx` 会让 `python-docx` 直接崩：`KeyError: "There is no item named 'word/NULL' in the
archive"` —— 包里有个断链的关系项，而 `Document()` 会遍历所有 part。**别反复重试、别换库**，直接读压缩包
里的 `word/document.xml`（不走 OPC 遍历，也就碰不到那条坏链接）：

```python
import zipfile, re
with zipfile.ZipFile(path) as z:
    xml = z.read('word/document.xml').decode('utf-8', errors='replace')
paras = []
for p in xml.split('</w:p>'):
    if 'PAGEREF _Toc' in p:            # 目录域行 —— 不跳掉的话你拿到的是目录，不是正文
        continue
    t = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, flags=re.S))
    t = re.sub(r'<[^>]+>', '', t).strip()
    if t:
        paras.append(t)
```

本技能自带 `scripts/docx_text.py`：

```bash
python scripts/docx_text.py <文件>                 # 列章节目录
python scripts/docx_text.py <文件> 第五章 40        # 第五章起 40 段
python scripts/docx_text.py <文件> 第五章 40 1      # 第 4 个参数：跳过前几处命中（目录那次），落到正文
```

- 章节名在目录里也出现一次，所以要跳过第一处命中才落到正文；命中判定用 `key in t[:40]`
- title 行通常很短，列目录时用 `^第[一二三四五六七八九十百]+章` 加长度限制过滤

## docx：页码地图（按章取原文、核篇幅用）

做一份"章 → 起始页码"清单贴在项目笔记里，后面靠它定位。目录域里的 `PAGEREF _Toc… \h <页码>` 就能批量
提取（这也是判断"该跳哪些行"的依据）。有了它，"把第 X 章原文提出来""核哪一章篇幅太薄"都是随手的事。

## PDF：表格版式（列宽、行高、合并分格）

要照抄一张表的格式，光有文字不够，得把格子量出来：

```python
import fitz
tbl = fitz.open(path)[page_no].find_tables().tables[0]
grid = tbl.extract()          # 每行一个列表
```

- `extract()` 里的 `None` **不是空数据，是那一格被上边纵跨或被左边横跨**（合并单元格的延续）——
  靠它能反推 `rowspan` / `colspan`：某列在下一行是 `None`，上面那格就是纵跨两行
- 列宽 / 行高：把 `tbl.cells` 所有 bbox 的 x、y 边界去重排序，相邻边界之差就是列宽、行高
  （pt，1pt = 0.3528mm）。表头多行合并的那块，`extract()` 只在第一行写字，其余行是 `None`
- 缩进：拿文字 bbox 的 x0（或 `get_text('dict')` 里 span 的 x0）跟基准比 —— 与表格左边缘差 ≈ 2 个字符宽
  就是"首行缩进两字"；与页边距差则是段落缩进
- 字号：`get_text('dict')` 里 span 的 `size`（中文 10.6pt ≈ 五号）

结论：**文字 + 格子结构（横跨几列 × 纵跨几行）+ 列宽行高** 三样齐了，才算"照格式抄了一张表"。

## 常见坑

- `python-docx` 在坏 / 大 docx 上抛 `word/NULL` 那类 `KeyError` → 是包里有断链，不是路径写错；
  换 zip 读 `document.xml` 一次就过
- 不跳 `PAGEREF _Toc` 目录域行 → 搜"第五章"命中的是目录而不是正文，看起来"章节是空的"
- 用整串标题做字典键 / 精确匹配 → 全角半角引号、多一个空格就匹配不上；**用前缀匹配**，
  匹配不到时先把实际标题清单打出来
- 一次性打印整份文件 → 上下文爆掉；先定位页码 / 段号，再取片段
- 把量出来的列宽行高、页码、缩进当通用规则写进别处 → 必须标注"这是某份文件的实测值"

## 验证清单

- [ ] 先报出规模（页数 / 段落数 / XML 字符数），再动手取
- [ ] 取到的是正文不是目录（跳掉了 `PAGEREF _Toc`，或命中的是正文那一处）
- [ ] 表格量了：列数、每格横跨几列 × 纵跨几行、列宽行高
- [ ] 实测值都标了"举例 / 按本次文件"，没被当成通用规则
- [ ] 临时脚本写在 `$LOCALAPPDATA/Temp`，用完删
