---
name: pyqt5-desktop-app
description: Build standalone Windows desktop applications with PyQt5 and package to .exe via PyInstaller.
version: 1.2.1
author: Hermes Agent
platforms: [windows]
tags: [pyqt5, desktop, exe, pyinstaller, gui]
---

# PyQt5 Desktop App Builder

Build functional Windows desktop applications using Python + PyQt5, then package into a standalone .exe with PyInstaller.

## When to use

- User wants a Windows GUI tool (not web-based)
- Need a standalone .exe that can be shared or moved around
- Tool needs tabs, forms, lists, text editing, clipboard operations
- Audience is non-technical (journalists, editors, office workers)
- Building engineering design tools (tunnel drill hole design, BIM visualization) that run offline

## Workflow

### 1. Plan the modules
Identify 2-4 core feature tabs. For journalism tools, the proven pattern:
- Calendar/schedule with countdowns, configurable news nodes
- Writing aids: templates, cliches library, title generator, word count
- Trending topics, editorial suggestions, publishing stats

### 2. Build the skeleton
- Single-file .py with QMainWindow + layout. Version during dev (v01, v02, v03)
- Use setStyleSheet() for theming
- Key imports: PyQt5.QtWidgets.*, PyQt5.QtCore.Qt, PyQt5.QtGui

### 3. Data architecture
- Hardcode stable reference data as module-level constants
- User-editable data in separate config.json alongside executable
- Use os.path.dirname(sys.executable) for exe, __file__ for script

### 4. Chinese text handling
- All strings MUST use straight quotes, NOT smart quotes
- Chinese punctuation is safe
- Extract Chinese strings to variables before interpolating in f-strings
- Use encode("utf-8") explicitly on file I/O

### 5. Build to .exe
```bash
pip install PyQt5 pyinstaller
pyinstaller --onefile --windowed --name "AppName" --noconfirm main.py
```

### 6. Copy to desktop
```bash
cp "dist/AppName.exe" "/c/Users/用户名/Desktop/AppName.exe"
```

---

## Engineering/Industrial Desktop Apps

For users building engineering design tools that must run offline on Windows.

### App Architecture (Tunnel Design Example)

```
TunnelCanvas(QWidget)      # 自定义绘图控件：QPainter 绘制断面、炮孔
ParameterPanel(QWidget)     # 参数设置面板：QGroupBox + QSpinBox + ComboBox
MainWindow(QMainWindow)     # 主窗口：水平拆分（画布:参数面板 = 2:1）
```

### Coordinate System Design
- Display: pixel coordinates, origin at canvas center (cx, cy = w//2, h//2)
- Export: real-world meters, origin at tunnel cross-section center
- Conversion: real_x = (px_x - cx) / pixel_scale
- Always ask the user what coordinate system their target system uses

### Auto-scaling Canvas (Critical)

When users can change radii/spans, the canvas must auto-scale:

```python
max_r = max(all_user_radii, tunnel_span / 2)
available = min(canvas_width, canvas_height) / 2
pixel_scale = available / max_r * 0.85  # 15% margin
```

Also implement resizeEvent() to re-scale on window resize.

### 可视化自标注原则（使用者偏好）

使用者明确表示看不懂没有标注的图。**每个绘制元素必须在图上直接标注**，不能依赖图例或外部说明。

标注规范：
- **几何元素旁写尺寸**：如"台车 长8m×宽2.5m"、"净高~3m"
- **方向箭头**：用红色箭头+文字说明方向，如"→打孔方向"
- **距离线**：关键间距（如"距掌子面: 2.0m"）用虚线+文字标在图上
- **图例**：底部或右下角放置颜色-形状对应说明
- **比例尺**：右下角画标尺棒+标注"1m=XXpx"
- **坐标信息**：底部显示当前位置坐标

```python
# 示例：图上标注
p.setPen(QColor(180,200,220))
p.setFont(QFont('微软雅黑', 9, QFont.Bold))
p.drawText(10, 22, '【俯视图】从正上方看')

# 尺寸标注
p.drawText(rx, ry-10, f'台车 长{self.rig_len:.1f}m×宽{self.rig_wid:.1f}m')

# 方向箭头
p.drawLine(start_x, start_y, end_x, end_y)  # 箭头线
p.drawLine(end_x-5, end_y-4, end_x, end_y)   # 箭头尖
p.drawLine(end_x-5, end_y+4, end_x, end_y)
p.drawText(end_x+5, end_y+3, '→打孔方向')
```

### Circular Distribution Template (for drill holes)

```
掏槽眼 (Cut holes) → evenly on circle (360/N, adjustable radius)
辅助眼 (Helper holes) → evenly on circle (360/N, adjustable radius)
周边眼 (Peripheral holes) → evenly along upper arch (-90 to 90)
底板眼 (Floor holes) → evenly along lower arc (90 to 270, adjustable radius)
```

This is a generic template. Replace with user's domain knowledge.

### Export Format
- Default: JSON with tunnel_span, rock_grade, hole list
- CRITICAL: Ask before finalizing. Target controller may need DXF, CSV, etc.

### Multiple Python Environments
- User may have PyQt5 in one Python install but not another
- Always verify: specific_python.exe -c "import PyQt5"
- Never assume python3 is the right interpreter for PyQt5 apps

### QLabel(fixedWidth=N) 不是有效构造参数（PyQt5 5.15.2 / Python 3.14 验证）

以下写法会抛 `TypeError: 'fixedWidth' is an unknown keyword argument`：
```python
# ❌ 错误
hr.addWidget(QLabel('text', fixedWidth=43))
```

必须拆成两行：
```python
# ✅ 正确
lbl = QLabel('text')
lbl.setFixedWidth(43)
hr.addWidget(lbl)
```

**同样的坑适用于** `QSpinBox`, `QDoubleSpinBox`, `QComboBox`, `QCheckBox`, `QSlider` — fixedWidth 都不能当构造参数。

**批量替换教训：** 用正则把 `QLabel(xxx,fixedWidth=N)` 直接替换成 `QLabel(xxx).setFixedWidth(N)` 会引入新 bug——链式调用返回 None，`addWidget(None)` 直接崩。正确改法是先建变量再 setFixedWidth 再 addWidget。

**Import 遗漏检查：** 新增 Tab/控件时确认头部 import 覆盖了新控件类（本会话踩过漏掉 QComboBox/QCheckBox/QSlider）。保险写法：`from PyQt5.QtWidgets import (..., QComboBox, QCheckBox, QSlider, QTextEdit, QFileDialog)`

### 自行验证原则（offscreen 无头测试）

**不要在未确认的改动后让用户双点开程序验证**（用户明确抱怨过「每次还要我去点开才能看」）。改完代码先用 offscreen 模式自己验证：

```bash
set QT_QPA_PLATFORM=offscreen && python -c "
from PyQt5.QtWidgets import QApplication
app = QApplication([])
from mymodule import MyWidget
w = MyWidget()
print('OK')
"
```

**验证清单（自己跑完再告诉用户）：**
- [ ] 语法检查：`python -m py_compile file.py`
- [ ] 导入无报错
- [ ] MainWindow / 新控件能实例化
- [ ] 新增 Tab 能正常创建（offscreen 下遍历 tabs.count()）

offscreen 模式能验证导入+构造，但看不到渲染效果——视觉问题仍需用户打开确认，但「能不能跑」这类问题必须自己先测。

### 版本编号规则（使用者偏好）

每个版本必须在以下三个地方一致标注版本号，方便使用者一眼区分新旧：

1. **窗口标题**：`self.setWindowTitle('应用名 v1.1 · 副标题')`
2. **顶部横幅**：`QLabel('🏛️ 应用名 v1.1 · 功能1 · 功能2 · 功能3')`
3. **文件名**：安装包/便携版文件名带版本号，如 `应用名_v1.1_便携版.zip`

主窗口标题用小号字 `v1.1`，横幅也用 `v1.1`，两个保持一致。更新时三个地方一起改。

### 外部资源目录模式

对于需要用户自定义内容的桌面应用，不要将数据硬编码在 Python 代码中，而是：

```
应用根目录/
    ├── 应用名.exe
    ├── config.json             # API 配置
    ├── 敏感词库.json           # 用户可编辑
    ├── 资源库/                 # 外部资源目录
    │   ├── 模板库.json         # 可自由增删
    │   └── 金句库.json         # 可自由增删
    └── 输出/                   # Excel/Word 导出目录
```

**路径处理（兼容开发环境和打包exe）：**
```python
def get_resource_dir():
    if getattr(sys, 'frozen', False):
        # 打包后：资源目录和 exe 在同一级（Inno Setup 安装时都在 {app} 下）
        return os.path.join(os.path.dirname(sys.executable), '资源库')
    else:
        return os.path.join(os.path.dirname(__file__), '资源库')
```

⚠️ 不要用 `..` 回退——Inno Setup 安装后 exe 和资源目录都在 `{app}` 下。用 `..` 会指向父目录导致找不到文件。

**启动时动态加载：**
```python
DEFAULT_TEMPLATES = load_resource_json('模板库.json', fallback_dict)
DEFAULT_JINKU = load_resource_json('金句库.json', fallback_dict)
```

**底部状态栏显示路径：**
```python
st2 = QLabel(f'📁 资源目录：{res_path}（可直接编辑模板/金句/敏感词文件）')
```

优势：用户发新版时只需替换 exe，资源文件保留；用户可自行定制内容；不同单位可用不同模板库。

### 分发包策略：便携版 + 安装包双通道

**便携版 ZIP**（立即可用）：
```python
import zipfile, os
with zipfile.ZipFile('应用名_vX.X_便携版.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(portable_dir):
        for file in files:
            zf.write(os.path.join(root, file), os.path.relpath(...))
```

目录结构即最终目录结构。大文件（~45MB）直接发 ZIP。

**Inno Setup 安装包**（给正式用户/需要选安装目录的场景）：
- 编写 setup.iss 脚本
- 安装时让用户选路径，自动创建 资源库/ 输出/ 文件夹
- 设置 `users-modify` 权限，保证用户可以编辑资源文件
- 首次安装时用 `onlyifdoesntexist` 防止覆盖用户已修改的资源文件
- Inno Setup 下载：https://jrsoftware.org/isdl.php

编译命令：`ISCC.exe setup.iss`

### AI API 集成模式

桌面应用调 AI API 的标准模式：

```python
def call_ai_api(messages, config, timeout=60):
    data = json.dumps({
        "model": config.get_model(),
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096
    }).encode('utf-8')
    req = urllib.request.Request(config.get_url(), data=data,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {config.get_key()}"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        result = json.loads(resp.read())
        return result['choices'][0]['message']['content'], None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:200]}"
```

**多厂商支持**：在配置中提供快速切换预设：
- DeepSeek: `https://api.deepseek.com/v1/chat/completions` / `deepseek-chat`
- 通义千问: `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions` / `qwen-turbo`
- GLM-4: `https://open.bigmodel.cn/api/paas/v4/chat/completions` / `glm-4-flash`
- Kimi: `https://api.moonshot.cn/v1/chat/completions` / `moonshot-v1-8k`

**API Key 管理**：用 Password 模式的 QLineEdit 输入，存储到同级 config.json。不在代码中硬编码任何 Key。

**AI 调用用线程**：API 请求用 threading.Thread 异步执行，防止界面卡死。配合 QProgressBar(maximum=0) 显示等待动画。

### Flash-Close / Exit Code 3221226505 (STATUS_DLL_NOT_FOUND)

On Windows, PyQt5 apps may flash-close with exit code 3221226505.

**🚫 DO NOT use `SetProcessDpiAwareness(2)`** — this line was verified to **cause** exit code 3221226505 on some PyQt5+Windows configurations. Removing it fixes the flash-close.

**Correct approach:**
```python
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # NO DPI awareness calls — they cause STATUS_DLL_NOT_FOUND
```

**If still flashing:**
1. Install PyQt5 in the specific Python that `d:/python/python.exe` points to (not PyManager)
2. Verify: `d:/python/python.exe -c "from PyQt5.QtWidgets import QApplication; print('OK')"`
3. Run via cmd.exe (not bash) to avoid MSYS path conversion issues
4. If all else fails, switch to tkinter (Windows built-in, no deps needed)
5. tkinter limitation: does NOT support 8-digit hex colors (`#64C8FF99`) — use 6-digit (`#64C8FF`) only

### 3D Sim View Split Layout

For engineering apps showing equipment position in tunnel/mine:

Layout: Left half = Top View (俯视图), Right half = Side View (侧视图)

```python
mid = self.width() // 2
self._draw_top(p, 0, 0, mid, h)   # 左半
self._draw_side(p, mid, 0, mid, h) # 右半
p.drawLine(mid, 0, mid, h)         # 分隔线
```

- Top View: 从正上方看，显示隧道左右壁、台车矩形、钻臂水平伸出
- Side View: 从侧面看，显示隧道拱形轮廓、台车高度、钻臂基座高度
- 两侧视图独立缩放 (scale = min(w,h) / 12 和 /10 分别控制)

### 模板结构化编辑模式（使用者偏好）

对于模板类功能（公文模板、报告模板等），不要将模板内容作为一个大的 QTextEdit 展示，而是：

**解析模板 → 拆成命名模块 → 每个模块生成 [标签 + 输入框]**

```python
def parse_sections(self, content):
    """把模板内容按段落标题拆成模块列表"""
    lines = content.strip().split('\\n')
    sections = []
    current_name = '正文'
    current_content = []
    
    section_keywords = ['标题', '副标题', '本报记者', '正文', '结尾', '出处',
                       '导语', '开头', '背景', '要求', '部署', '强调',
                       '一、', '二、', '三、', '四、', '五、']
    
    def is_section_header(line):
        line_stripped = line.strip()
        for kw in section_keywords:
            if line_stripped.startswith(kw) or line_stripped.startswith(f'【{kw}】'):
                return kw
        return None
    
    for line in lines:
        stripped = line.strip()
        if not stripped: continue
        header = is_section_header(line)
        if header:
            if current_content:
                sections.append((current_name, '\\n'.join(current_content).strip()))
            current_name = header
            content_part = stripped
            for sep in ['：', ':', '】']:
                if sep in content_part:
                    content_part = content_part[content_part.index(sep)+len(sep):].strip()
            current_content = [content_part] if content_part and content_part != header else []
        else:
            current_content.append(stripped)
    if current_content:
        sections.append((current_name, '\\n'.join(current_content).strip()))
    if not sections:
        sections.append(('正文', content.strip()))
    return sections
```

**显示方式**：放入 QScrollArea，每个模块生成一个 QLabel('【模块名】') + QTextEdit(预设内容)。

**进阶：每个模块自带格式控制（模板+排版合并）**
将模板编辑与排版设置合并到同一个 Tab，每个模块独立控制字体/字号/加粗：

```python
for sec_name, sec_content in sections:
    # 1. 模块名
    sec_label = QLabel(f'【{sec_name}】')
    self.section_layout.addWidget(sec_label)
    
    # 2. 格式栏：字体 | 字号 | 加粗
    fmt_bar = QHBoxLayout()
    cb_font = QComboBox(); cb_font.addItems(all_fonts)
    cb_font.setCurrentText(default_font_map.get(sec_name, '仿宋'))
    sb_size = QSpinBox(); sb_size.setRange(8, 48)
    sb_size.setValue(default_size_map.get(sec_name, 12))
    cb_bold = QComboBox(); cb_bold.addItems(['正常', '加粗'])
    fmt_bar.addWidget(QLabel('字体')); fmt_bar.addWidget(cb_font)
    fmt_bar.addWidget(QLabel('字号')); fmt_bar.addWidget(sb_size)
    fmt_bar.addWidget(cb_bold)
    self.section_layout.addLayout(fmt_bar)
    
    # 3. 内容输入框
    edit = QTextEdit()
    edit.setPlainText(sec_content)
    self.section_layout.addWidget(edit)
```

**导出时注意**：导出 Word 时不是简单拼接文本，而是按每个模块独立设置的字体/字号/加粗生成：
```python
for sec in section_data:
    p = doc.add_paragraph()
    run = p.add_run(sec['text'])
    run.font.name = sec['font']
    run.font.size = Pt(sec['size'])
    run.bold = sec['bold']
    run.element.rPr.rFonts.set(qn('w:eastAsia'), sec['font'])
    p.paragraph_format.line_spacing = global_line_spacing
```

这取代了旧版「自动判断格式」的猜测式逻辑——用户手动设置的格式才是最准确的。

```python
scroll = QScrollArea()
scroll.setWidgetResizable(True)
scroll.setFrameShape(QFrame.NoFrame)

self.section_container = QWidget()
self.section_layout = QVBoxLayout(self.section_container)
scroll.setWidget(self.section_container)

for sec_name, sec_content in sections:
    sec_label = QLabel(f'【{sec_name}】')
    sec_label.setStyleSheet('color:#2B579A;font-weight:bold;...')
    edit = QTextEdit()
    edit.setPlaceholderText(f'请输入{sec_name}……')
    edit.setPlainText(sec_content)
    edit.setMinimumHeight(60)
    edit.setMaximumHeight(120)
    self.section_layout.addWidget(sec_label)
    self.section_layout.addWidget(edit)
```

**导出时合并**：遍历所有输入框，按 `{模块名}：{内容}` 格式拼回完整文本。

### 数据看板卡片布局（使用者偏好：等宽四列）

数据看板（统计面板）的卡片布局应遵循以下规则：

**不推荐**：2×2 网格（图标+标题+数据全部叠在一个卡片里）
```python
# ❌ 使用者反感这种
card_grid = QGridLayout()
for i in (title, value, icon):
    card_layout.addWidget(icon)  # 单独一行
    card_layout.addWidget(title) # 单独一行  
    card_layout.addWidget(value) # 单独一行
```

**推荐**：一行四列等宽，每列卡片内部分两行（第一行图标+标题，第二行数据值）
```python
# ✅ 使用者认可
card_grid = QGridLayout()
card_grid.setSpacing(8)

for col, (title, value, icon) in enumerate(card_data):
    card = QFrame()
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(8, 5, 8, 5)
    card_layout.setSpacing(2)
    
    # 第一行：图标 + 标题（水平排列）
    row1 = QHBoxLayout()
    row1.setSpacing(5)
    lbl_icon = QLabel(icon)
    lbl_icon.setStyleSheet('font-size:20px')
    row1.addWidget(lbl_icon)
    lbl_title = QLabel(title)
    lbl_title.setStyleSheet('font-size:13px;color:#666')
    row1.addWidget(lbl_title)
    row1.addStretch()
    card_layout.addLayout(row1)
    
    # 第二行：数据值
    lbl_val = QLabel(value)
    lbl_val.setStyleSheet('font-size:24px;font-weight:bold;color:#1a3a6b')
    card_layout.addWidget(lbl_val)
    
    card_grid.addWidget(card, 0, col)
    card_grid.setColumnStretch(col, 1)  # 四列等宽
```

关键点：用 `QGridLayout` + `setColumnStretch(col, 1)` 保证四列等宽，而不是 QHBoxLayout（内容不同会导致宽度不一致）。

### 金句库 / 可点击列表模式

对于"点击即复制"的参考内容库，**最稳定的方案是用 QListWidget**（不要用 QPushButton + QScrollArea——动态按钮经常不显示）：

```python
# ✅ 推荐：QListWidget，不会出现按钮不显示的问题
self.list_widget = QListWidget()
self.list_widget.itemDoubleClicked.connect(self.copy_jinku)

def load_jinku(self):
    self.list_widget.clear()
    
    with open(jinku_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for category, sub_data in data.items():
        if category.startswith('_'): continue
        
        # 分类标题（不可选中）
        cat_item = QListWidgetItem(f'── {category} ──')
        cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsSelectable)
        font = cat_item.font(); font.setBold(True); font.setPointSize(12)
        cat_item.setFont(font)
        self.list_widget.addItem(cat_item)
        
        for sub_cat, items in sub_data.items():
            if sub_cat.startswith('_'): continue
            if not isinstance(items, list) or not items: continue
            
            # 子分类标题（不可选中）
            sub_item = QListWidgetItem(f'  {sub_cat}')
            sub_item.setFlags(sub_item.flags() & ~Qt.ItemIsSelectable)
            self.list_widget.addItem(sub_item)
            
            for text in items:
                item = QListWidgetItem(f'📋 {text}')
                item.setData(Qt.UserRole, text)  # 存原始文本
                self.list_widget.addItem(item)
    
    self.status_label.setText(f'✅ {count} 条已加载')

def copy_jinku(self, item):
    text = item.data(Qt.UserRole)
    if not text: return
    clipboard = QApplication.clipboard()
    clipboard.setText(text)
```

关键点：
- 分类和子分类标题用 `setFlags(... & ~Qt.ItemIsSelectable)` 设为不可选中
- 金句文本用 `setData(Qt.UserRole, text)` 存储，双击时取出
- 底部状态栏显示加载结果（成功条数/失败原因），方便排查问题
- 加「刷新」按钮让用户编辑 JSON 后重新加载

### 字体库管理（导入 .ttf / .otf）

给桌面应用增加自定义字体支持：

**目录结构**：`资源库/字体库/`（与 exe 同级）

**导入流程**：
1. 用户点「导入字体」→ QFileDialog 选 .ttf/.otf/.ttc 文件
2. `shutil.copy2(源文件, 字体库目录/文件名)`复制到字体库
3. `QFontDatabase.addApplicationFont(字体文件路径)`注册到 Qt 系统
4. 刷新所有字体下拉框（`QComboBox.clear()` + `addItems(新字体列表)`）

**字体加载（启动时）**：
```python
FONT_DIR = get_resource_path('字体库')

def get_custom_fonts():
    """扫描字体库，返回可用字体列表"""
    ensure_font_dir()
    fonts = []
    for f in os.listdir(FONT_DIR):
        if f.lower().endswith(('.ttf', '.otf', '.ttc')):
            font_path = os.path.join(FONT_DIR, f)
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id >= 0:
                font_names = QFontDatabase.applicationFontFamilies(font_id)
                for fn in font_names:
                    fonts.append((fn, font_path))
    return fonts

def get_builtin_fonts():
    return ['微软雅黑', '仿宋', '宋体', '黑体', '楷体', '方正小标宋']

def get_all_fonts():
    builtin = get_builtin_fonts()
    custom = [fn for fn, fp in get_custom_fonts()]
    return builtin + [c for c in custom if c not in builtin]
```

**QComboBox 刷新**：导入字体后保留当前选中项
```python
current = fmt['font'].currentText()
fmt['font'].clear()
fmt['font'].addItems(all_fonts)
if current in all_fonts:
    fmt['font'].setCurrentText(current)
```

### 版本迭代策略（面向非开发者使用者）

- 每个版本独立文件：app_v01.py → app_v02.py → app_v03.py
- 先跑起来再优化，不要一次性写大代码
- 发布新版本时清理旧.py文件（使用者桌面整洁偏好）
- 跑.py的方式：直接在cmd里 `d:/python/python.exe app_vNN.py`
- 不要通过Hermes后台进程启动GUI（窗口会闪退）

### Running GUI Apps from Hermes
- DO NOT launch GUI apps as Hermes background processes (window closes on exit)
- DO instruct user to double-click the .py file directly
- Right-click .py -> Open With -> their Python executable
- Keep numbered versions (v01, v02, v03) so user can fall back

### .py vs .exe Explanation
When user asks "为什么是py不是exe":
- 开发阶段用.py方便改，功能定好了再打包成.exe
- 打包后双击就能跑，不用装Python

---

## Pitfalls

- Chinese smart quotes inside f-strings cause SyntaxError. Never use f"...从\"有没有\"到\"好不好\"..." — extract to variables first.
- QPushButton.setCheckable(True) = toggle button. Connect to toggled signal, not clicked.
- Config file path: In PyInstaller exe, __file__ points to temp dir. Use os.path.dirname(sys.executable).
- Online API calls: use urllib.request with timeout. Wrap in try/except for offline users.
- Layout overflow: use QScrollArea + inner QWidget. Set scroll.setWidgetResizable(True).
- Gradient backgrounds: use qlineargradient syntax with NO spaces after commas.
- Full PyInstaller build takes ~40-50s, produces ~50MB exe.
- Auto-scaling with large radii: if user sets 10m radius in 6m tunnel, drawing MUST auto-shrink. Don't let elements clip.
- Launching via Hermes background: GUI apps will flash and close. Always tell user to run file directly.
- User may not understand coordinate systems in code. Ask directly: "你们台车坐标系原点在哪？导出要什么格式？"
- **金句库/按钮列表不要用QPushButton+QScrollArea**：动态创建按钮经常不显示，lambda闭包易出错。用QListWidget+setData(Qt.UserRole,text)更稳定。
- **字体下拉框刷新要保留当前值**：导入字体后QComboBox.clear()丢失当前值，必须先currentText()再addItems()再setCurrentText()。

## Related
- skill_view(name='word-template-fill')
- skill_view(name='ocr-and-documents')
- skill_view(name='python-zero-to-hero')

## Reference Patterns
- `references/gov-media-workstation-pattern.md` — 政务全媒体工作台 v1.1 完整实现模式（AI润色 + AI写作 + 外部资源目录 + 金句库 + Inno Setup安装包）
- `references/journalism-workstation-architecture.md`
- `references/tunnel-drill-design-session-20260722.md`
