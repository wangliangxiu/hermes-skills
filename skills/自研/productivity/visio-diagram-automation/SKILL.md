---
name: visio-diagram-automation
category: productivity
description: 要出/改 Visio 工程图（组织机构图、流程图）或复用往期 Word 里的 Visio 图时用。
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [visio, vsdx, com, pywin32, 组织机构图, 流程图, 投标, 施组, docx]
---

# 用 Visio 出图 / 复用现成图

（用 Python COM 直接生成 `.vsdx` 原生文件 —— 用户后期能在 Visio 里自己改；
并从 docx 里把嵌入的 Visio 图按图题抠出来，攒成可复用的图库。）

## 什么时候用它

- 要出组织机构图、管理流程图、体系框图、工艺流程框图这类**线条图**，而且**后期还要改**
- 要复用往期 Word 文档里的 Visio 图（改项目名称、换机构、换工区数）
- 用户说：用 Visio 画、这图我后期不好改、能不能出 Visio 文件

## 硬规矩（用户偏好，先守住）

1. **交 .vsdx 原生文件，不是图片** —— 用户后期要在 Visio 里自己改字挪框；图片改不动，
   等于把活推回给他。同时给一张 PNG 预览方便快速看。
2. **能少改就少改：优先复用现成的图**，只改必须改的那几处（项目名称、机构名、工区数）；
   与本次内容冲突了才重画。
3. **交付前自己把导出的 PNG 看一遍**：连线有没有断、有没有压字/出界/乱码 —— 别让用户当测试。
4. 文件名用**中文可读**的名字（照文档里原来的图题），不要 Drawing1、image4。
5. 出完/改完**把文件打开给用户看**，并说清改了什么、哪些是可改的原生文件。
6. **他一边讲“图该怎画”一边纠正是常态 —— 他说“先别出了”就立刻停手**，把修改点攒着、
   等他说完再一次性重画；他问“你能出这个图吗 / 能画吗”时**先答能不能、打算怎么画**，
   他明说“不用做出来”就别动手（抢在他讲完前出图、或一条一条地重画，都会让他烦）。

## 链条 A：复用 —— 从 docx 里抠嵌入的 Visio 图

Word 里那些"双击能进 Visio 编辑"的图，就是 docx 里的 OLE 对象：

- docx 就是 zip：`word/embeddings/*.vsdx`、`*.vsd`（另有 xlsx、bin）
- **认图/命名**：解析 `word/document.xml`，找图片所在段落，往后（找不到就往前）取最近的**图题段落**
  （"××图 / ××框图 / ××流程图"，≤30 字）当文件名 —— 比按画面内容猜准得多，也便于跟往期标对上；
  没有图题就退而用最近的小节标题（`^\d+(\.\d+)*` 开头那类）
- **图片引用与 OLE 引用是两码事**：同一段里 `r:embed` 指向 `word/media/*`（图片），
  `r:id`（在 `<o:OLEObject>` 上）才指向 `word/embeddings/*` —— 想要**能改的源文件**就得按 `r:id` 找
- **老格式 `.vsd`**：用 Visio 打开再另存 → `d = app.Documents.OpenEx(path, 4)`（只读、不带工作区）、
  `d.SaveAs(新路径 + '.vsdx')`、`d.Close()`；`.vsd` 不是 zip，读不出文字，得用 Visio 遍历
  `page.Shapes` 读 `.Text` 来认图
- **只有图片的（EMF / PNG / JPG）**：EMF 是矢量，插进 Word 后右键"**取消组合**"就能改字（改完还是矢量）；
  PNG/JPG 是位图，只能重画或用图片软件处理
- 工具：`scripts/extract_docx_visio_figures.py <docx> <输出目录>`（加 `--vsdx` 顺带转老格式）
  —— 一条命令导出全部嵌入 Visio 图，**按图题命名**并打出索引

## 链条 B：生成 —— Python COM 驱动 Visio

前提：装了 Visio（可查注册表 `HKLM\SOFTWARE\Classes\Visio.Application`）＋ Python 有 pywin32。

```python
import win32com.client as wc
app = wc.Dispatch('Visio.Application')
app.Visible = False
doc = app.Documents.Add('')
pg = doc.Pages.Item(1)
pg.PageSheet.CellsU('PageWidth').FormulaU  = '420 mm'    # A3 横向
pg.PageSheet.CellsU('PageHeight').FormulaU = '297 mm'
s = pg.DrawRectangle(x1, y1, x2, y2)                     # 坐标是英寸！mm ÷ 25.4
s.Text = '项目经理'
s.CellsU('Rounding').FormulaU    = '1.2 mm'              # 圆角
s.CellsU('FillForegnd').FormulaU = 'RGB(232,238,248)'
s.CellsU('Char.Size').FormulaU   = '10 pt'
s.CellsU('Char.Font').FormulaU   = str(doc.Fonts.ItemU('微软雅黑').ID)
s.CellsU('VerticalAlign').FormulaU = '1'                 # 0上 1中 2下
s.CellsU('Para.HorzAlign').FormulaU = '1'                # 0左 1中 2右
ln = pg.DrawLine(x1, y1, x2, y2); ln.CellsU('EndArrow').FormulaU = '13'
doc.SaveAs(r'C:\...\图.vsdx')                            # 原生文件
doc.Pages.Item(1).Export(r'C:\...\图.png')              # 逐页导 PNG 预览
app.Quit()
```

**画线结构照用户的习惯**（他点过两次，照做）：

- 每一排：**上面一根横线**（由上一排那根单线喂进来，每格用竖线接上去）＋ **下面一根横线**把这一排收口
  （每格底边用竖线接下去）＋ **从下横线中间一根单线**接到下一排的上横线 —— 上下一排排都连通，
  中间干线也不会穿过方块
- **最底下一排不画下横线**（它是末端，下面不接任何东西）
- 分层图（组织机构图）：右侧竖排标**层名**（领导层 / 管理层 / 作业层），每层用**虚线大框**圈起来
- 每画完一次都导出 PNG 自己看一遍再交付

现成脚本（改参数即可）：`scripts/visio_org_chart.py`（组织机构图）、
`scripts/flow_visio.py`（管理流程图，带判定框与"不合格→反馈"回路）。
不依赖 Office 的退路：matplotlib 出 PNG + SVG。

## 链条 C：攒图库（做一次，以后写标书直接拿）

1. 拿一份内容全的往期文档（.docx），用链条 A 的脚本把嵌入 Visio 图全导出来
2. 老格式 `.vsd` 转 `.vsdx`
3. 分类放好：**01 组织机构图 / 02 管理体系图 / 03 管理流程图 / 04 工艺流程图 /
   05 信息化与智慧工地 / 06 其他**；图片类（EMF/PNG）也收进来并标注"EMF 可在 Word 里取消组合改字"
4. 写一份 `索引.txt`：图名 ↔ 源文件 ↔ 图题 ↔ 所属章节（便于以后定位）
5. 命名以**文档里原来的图题**为准，哪怕图题与画面略有出入 —— 这样跟往期标对得上

## 常见坑

- `Dispatch('Visio.Application')` **接管已经打开的那个 Visio 实例**，脚本结尾 `Quit()` 会把用户正看着的
  Visio 窗口一起关掉 —— 写文件前先确认同名文件没被占用（先关 Visio 再跑），跑完再打开给他看
- **坐标单位是英寸**（mm ÷ 25.4），不是毫米也不是磅
- **菱形（判定框）不要用 `DrawPolyline`** —— 传 list 或 tuple 都会报"无效的参数数目"；
  用流程图模具：`app.Documents.OpenEx('BASFLO_U.VSSX', 64)` 里有『流程 / 判定 / 子流程 / 开始/结束 /
  动态连接线』等母版，`page.Drop(master, x, y)` 即可；拿不到母版就退化成方框，不耽误出图
- Visio 的矩形**不会自动长高**：注释/说明文字多要手动把框加高，否则字压框
- 文件名里带 `/ : * ? " < > |` 会写失败（报 FileNotFound）—— 先替换成 `_`
- 多条反馈回路要**每条走不同的竖直通道**（x 不同），否则回路叠在一条线上看不清
- 一次跑几十个文件用后台跑并打印进度，别塞进一次前台调用里等超时
- **导出 PNG / 存文件时路径别混用**：给原生程序（Visio / Python）传路径不要用 MSYS 风格 `/c/...`，
  否则 `Page.Export` 会报 `OSError: Invalid argument` —— 先 `cd` 到目标目录传 `"."`，
  或写 `C:/Users/...` 正斜杠
- **要预览图就用 Visio 自己导（`Page.Export`），别绕道 PowerShell 去转 EMF**：
  `.ps1` 里带中文路径或中文注释会被 PowerShell 5.1 按 ANSI 解析、报“字符串缺少终止符”之类语法错，
  白折腾一圈

## 交付时要说清

文件在哪（绝对路径）、哪些是原生可改的（.vsdx）、哪些只是图片（EMF 需在 Word 里取消组合改字）；
再说一句自己核过什么（导出 PNG 看过、连线连通、没出界）。
