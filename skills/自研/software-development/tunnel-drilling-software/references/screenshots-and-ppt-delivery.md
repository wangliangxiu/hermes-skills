# 界面截图与报名 PPT 交付（2026-08-14 实证）

## 一、offscreen 批量抓取软件界面截图

```python
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
app = QApplication([])
import drill_design_v09 as m
w = m.MainWindow(); w.show(); app.processEvents()
w.resize(1560, 820); app.processEvents()
tabs = w.findChild(QTabWidget)
for i in range(tabs.count()):
    tabs.setCurrentIndex(i)
    for _ in range(5): app.processEvents()   # 给渲染留时间
    w.grab().save(f'_screenshots/tab{i+1:02d}.png')
```

- 结果：12 个 Tab 一次抓完零异常，1560x820 与窗口一致
- 文件名含 emoji（🔧 等）保存没问题，但 python-pptx 引用前批量重命名简单名 tabNN.png
- sys.excepthook 挂上打印被 Qt 吞的异常（画布空白等），ERR_COUNT=0 才算干净

## 二、OpenGL 视图 offscreen 渲染空白（点云分析白屏）

- **现象**：tab03（点云分析）截图大片白色；用户反馈"云点图看着不太对"
- **根因**：pyqtgraph GLViewWidget 需要 GPU/OpenGL 上下文，offscreen 平台没有 →
  grab() 抓到的是空白背景 + 少量 UI。**不是软件 bug，真机显示正常**
- **体检法**（PIL 采样统计，交付前对每个 Tab 跑）：
  ```python
  img = Image.open(fn).convert('RGB'); px = img.load()
  cnt = Counter()
  for y in range(0, h, 20):
      for x in range(0, w, 20): cnt[px[x,y]] += 1
  white = sum(n for c,n in cnt.items() if c[0]>235 and c[1]>235 and c[2]>235)
  # 白色>70% + 不同颜色数少 → 渲染失败，换 Tab
  ```
  实测：tab03 白色79.6%（失败）；tab01 深色画布正常；tab04 MWD 白色25.2%正常
- **解决**：PPT 换用非 GL Tab（QPainter/普通控件 offscreen 正常）
- **结论**：交付截图前逐个 Tab 做白色占比体检，别等用户发现

## 三、python-pptx 生成报名 PPT

### 中文字体（关键！）

`run.font.name = '微软雅黑'` 只设置 latin typeface，中文仍走默认字体：
```python
rPr = run._r.get_or_add_rPr()
ea = rPr.find(qn('a:ea'))
if ea is None:
    ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
ea.set('typeface', '微软雅黑')
```
封装成 `set_font(run, ...)` helper，所有 run 走它。

### 布局常量

- 16:9：`prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)`
- 配色（工程风）：深蓝 1E3A5F + 橙 F5A623 + 浅底 F7F9FC + 卡片白底 D8DEE9 描边
- 卡片：`add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, ...)` + `adjustments[0]=0.08~0.15` 圆角 +
  `shadow.inherit=False`（防默认阴影）
- 截图按宽度放、保持比例：`h = w * 820/1560`

### QA（无 LibreOffice 时的替代）

- 文本回读：遍历 slide.shapes，has_text_frame 打印文本，确认无乱码、顺序正确
- 图片检查：`shape_type == 13`（PICTURE）数量 + 坐标 `left+width ≤ slide_width`
- 残留检查：grep 所有文本是否含已删除模块的关键词（如"点云"）

## 四、PPT 修改（删除/替换元素）坑

**删除旧卡片必须连其内文本框一起删**：卡片是 ROUNDED_RECTANGLE（x=0.55in），
它内部的两个文本框 x=0.75in——按卡片坐标删除会漏掉文本框，残留旧文字叠在
新内容上（使用者会发现"旧标题还在"）。

修复模式：
1. 按 x≈卡片列 + top 范围删图片和卡片形状
2. 再按**文本内容**匹配删除残留文本框（'点云分析'、'3D 点云 / 实体表面'）
3. 重新 add_picture + add_textbox + 卡片
4. 修改横幅文字用 run 级 replace（`r.text.replace(...)`，段落里多个 run 逐个找）
5. 收尾 grep 全文确认无残留关键词

### 1. 体检三步（改之前先全量体检，别等用户发现）

1. **python-pptx 布局扫描**：每页每个 shape 打印 类型/坐标/宽高/文本，
   找重叠、越界、图片尺寸不齐（如 P6 三张图高 2.23 vs 2.13 英寸底部不齐）
2. **PowerPoint COM 溢出检测**（win32com 打开演示文稿）：
   ```python
   bh = sh.TextFrame.TextRange.BoundHeight
   usable = sh.Height - sh.TextFrame.MarginTop - sh.TextFrame.MarginBottom
   if bh > usable + 4:  # 溢出
   ```
   30pt 粗体长数字"1,650万~4,950万"在 3.30in 框内 BoundWidth < 框宽却仍
   换行成两行（尾字"万"孤行）——这是内边距+测量临界，**加宽没用，把
   MarginLeft/Right 归零 + 加宽**（如 3.55~3.71in），COM `Lines().Count==1`
   验证单行
3. **PIL 像素体检**：导出 PNG 后按页面区域统计亮/暗/白占比，确认截图
   区域有内容（不是白屏黑屏）、布局无大块空白

### 2. 数字口径铁律

PPT 财务页出现"首年10.3万（研发4.8+迭代1.5+维护3.6+服务器0.4+保险预留1.5）"
——括号合计 11.8≠10.3 自相矛盾（使用者+设备所负责人拍板的 BP v3 定稿口径：首年10.3万
不含保险、此后约7万/年含保险1.5）。**PPT 一切数字/口径以 BP 定稿为准**，
修正后营收行（2.9/31.4/56.8万）与 BP 完全一致才算对。

### 3. 文本/位置修改的误伤坑（两个翻车点）

- **set_para_text 误伤相邻段落**：清 runs 只留第一个会重建段落，条件 `'固定
  成本' in t` 同时命中副标题"成本公式模型：总成本=固定成本+..."和"单套毛利…
  覆盖年固定成本"两段（幸好它们本来就是单 run 同格式，对比备份确认零损失）。
  教训：条件必须完整匹配目标字符串；改后对比备份段落的 run 数/字号/粗体
- **按关键词移位置误伤横幅**：匹配"3D 点云"想移动点云图说明，结果把底部
  横幅"3D 点云分析·围岩智能识别·台车定位纠偏 ｜ 系统 v0.12 可运行版本"
  从 y=5.60 移到 y=4.28，盖住点云图说明 → 用户反馈"点云图上面下面都没有
  文字描述"。教训：位置匹配先排除横幅/全宽文本（如先按 x 范围过滤），
  改后导出 PNG 复查

### 4. 替换 media 图片（换错文件的教训）

`sh.image.filename` 返回 basename（image.png），多张图显示同名——按它 zipfile
替换会**换错文件**（本次先把 image.png 换了，实际目标是 image2.png）。

正确流程：
```python
# 1. 定位真实 media 文件
blip = sh._element.find('.//' + qn('a:blip'))
rId = blip.get(qn('r:embed'))
target = slide.part.rels[rId].target_ref   # ../media/image2.png
# 2. 全 PPT 扫描该 media 引用唯一性（image2.png 只被目标 shape 引用才安全）
# 3. 新图先居中裁剪到目标框比例（4.05/2.13=1.902，防 shape 拉伸）
# 4. zipfile 原位替换 ppt/media/image2.png 的 blob
# 5. python-pptx 回读 + md5 验证（不只看尺寸）
```

## 六、流程总结

截图体检（PIL 白色占比）→ 选非 GL 图 → python-pptx 生成（ea 字体 helper）→
文本回读 QA → 修改时按文本匹配删残留 → 交付前再回读一遍。
