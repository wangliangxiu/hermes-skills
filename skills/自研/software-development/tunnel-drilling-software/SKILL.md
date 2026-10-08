---
name: tunnel-drilling-software
description: 隧道/矿山工程设备配套智能软件开发——台车参数化布孔、3D模拟、定位数据接入（全站仪/RTK）、炮孔数据导出。覆盖全电脑凿岩台车的炮孔设计系统开发全流程。
triggers:
  - 凿岩台车
  - 炮孔设计
  - 隧道布孔
  - 全电脑凿岩台车
  - 智能炮孔
  - BIM+AI工程
  - 工程设备软件
---

# 隧道/矿山工程设备智能软件开发

## 架构原则

1. **离线优先** — 隧道施工环境无网络，所有功能必须纯本地运行，零联网依赖
2. **参数全可调** — 一线工人需要能现场调整所有参数，不能写死任何值
3. **成套系统视角** — 这是完整的智能台车系统，不是光一个设计软件。你跟小伙伴分工：你做软件+数据，小伙伴做机械+控制。见外人的时候要统一说"整套系统"，不要把话说小了

   整体架构分五层（DS参考版，按实际调整）：
   ```
   ⑤ 智能爆破设计与优化系统 —— 炮孔图/AI优化/质量评估（你们的软件）
   ④ 数据管理与信息化系统     —— 日志记录/数据追溯（你们的软件）
   ③ 自动控制与导航定位系统   —— 坐标计算/自动寻孔（你们的+台车对接）
   ② 液压与机械执行系统       —— 台车自有，你们不碰
   ① 传感与安全防护系统       —— 台车自有，你们不碰
   ```
   写架构或跟外人聊时，重点讲③④⑤，①和②说"台车本体自带"带过即可。每项数据说清楚来源是"你们软件算的"还是"台车传感器给的"还是"人工填的"，不模糊。
3. **3D渲染不在台车上跑** — 台车工控机配置不高，不装3D。3D渲染、点云处理、AI分析都在工程师笔记本上运行。设计文件（几十KB坐标文件）通过U盘/串口下发台车。台车只需要简单2D界面接收文件+控制钻孔+记录数据
4. **所有功能集成到主系统** — 新增功能必须作为标签页嵌入主窗口的 QTabWidget，不要另外启动独立窗口。用户明确要求「咱们是一个软件，要有一个模块显示这个」
5. **增量迭代** — 先用.py快速原型验证，功能稳定后再打包.exe给现场用
6. **批量反馈先听完再动手（用户 2026-08-10 明确要求）** — 用户一次
   提多条意见时（"先别行动，我继续说第二条/第三点/还有第四点"），
   **必须全部听完、逐条确认理解后再开工**，不要听到第一条就急着改。
   用户原话："我让你去做的时候，你再去做，先听我说完"。实施时只改
   点名的部分（"根据这四点，你在原有基础上优化这四点，其他的效果
   不要改动"）——不做顺手优化、不动无关功能。

## 技术选型

### 推荐：PyQt5 + matplotlib 3D
- 优点：界面专业、组件丰富、支持matplotlib嵌入式3D视图
- 安装：`pip install PyQt5 matplotlib`
- 注意：Windows中文用户名环境下可能出现DLL加载失败（exit code 3221226505）
  - 解决方案：**删除** `ctypes.windll.shcore.SetProcessDpiAwareness(2)` 这行，它会导致某些PyQt5版本加载platform DLL失败
  - `drawText()` 方法的所有坐标参数必须为 int 类型，不能传 float
  - tkinter不支持8位十六进制颜色码（如 `#64C8FF99`），只认6位（`#64C8FF`）

### 备选：tkinter（Windows自带）
- 优点：无需安装任何依赖，Python自带
- 适用：原型快速验证、PyQt5闪退时的平替方案
- 限制：界面不如PyQt5专业，不支持matplotlib 3D嵌入
- 如果仍然闪退，切换回tkinter

### 自行验证原则（off-screen 测试）

**不要在未确认的改动后让用户双点开程序验证。** 你应该自己用 `QT_QPA_PLATFORM=offscreen` 环境变量来执行无头测试：

```bash
set QT_QPA_PLATFORM=offscreen && python -c "
from PyQt5.QtWidgets import QApplication
app = QApplication([])
from mymodule import MyWidget
w = MyWidget()
print('OK')
"
```

这样可以验证导入和窗口初始化是否成功，不用让用户反复开闭程序。

**验证清单（自己跑完再告诉用户）：**
- [ ] 语法检查通过（`python -m py_compile file.py`）
- [ ] 导入无报错
- [ ] MainWindow 创建成功
- [ ] 新增Tab/控件能正常实例化

### PyQt5 兼容性注意事项（QLabel fixedWidth 坑）

本会话验证的 PyQt5 版本：5.15.2（Python 3.14）。

**`QLabel(fixedWidth=N)` 不是有效构造参数。**

在 PyQt5 5.15.2 中，以下写法会抛 `TypeError: 'fixedWidth' is an unknown keyword argument`：
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

**同样的坑也适用于：** `QSpinBox`, `QDoubleSpinBox`, `QComboBox`, `QCheckBox`, `QSlider` — 它们的 `fixedWidth` 都不能当构造参数。

**Import 遗漏检查：** 新加 Tab 页面时要确认头部的 import 列表覆盖了新用到的控件类。本会话踩过的遗漏：`QComboBox`, `QCheckBox`, `QSlider`。保险写法：`from PyQt5.QtWidgets import (..., QComboBox, QCheckBox, QSlider, QTextEdit, QFileDialog)`

**两个会导致"窗口最大化/显示时崩溃"的隐藏雷（2026-08 爆破设计Tab排查实证）：**

1. **实例属性名不能撞 QWidget 方法名（如 `self.height`）**
   - `self.height = 5.0` 会遮蔽 QWidget.height() 方法，Qt 内部再调 height() 拿到浮点数 → 直接崩溃（进程退出，bash 报 127）
   - **另一种表现（2026-08-10 画布空白实证）**：不崩溃，但 paintEvent 里
     `w,h = self.width(), self.height()` 调 self.height() 抛
     `TypeError: 'float' object is not callable`，异常被 Qt 吞掉 →
     画布整块空白不绘制（用户反馈"中间空了一大块"）。强制渲染排查法：
     `widget.grab()` 会重新走 paintEvent，配合 `sys.excepthook` 打印
     被吞的异常堆栈（或直接 `traceback.print_exc`）
   - 同理避开的属性名：`width`、`height`、`size`、`pos`、`rect`、`geometry`、`x`、`y`、`parent`、`font`、`layout` 等 QWidget/QObject 方法名
   - **paintEvent 里局部变量也别用 h/w/x/y**（2026-08-13 实证）：paintEvent 开头
     `w,h=self.width(),self.height()`，后续 `for h in self.holes:` 把局部 h 覆盖成
     孔 dict → 末尾 `h-8` 抛 TypeError 被 Qt 吞掉（画布静默失效，界面不崩）。
     修复：循环变量用 hh/hh2。排查：offscreen 回归看 stderr / `widget.grab()`
   - 修复：改名（如 `self.tunnel_height` / `self.sec_height`）。本案例 BlastCanvas、HoleCanvas、Simple3DView、RigHoleCanvas、PositioningPanel 都踩过
   - 排查方法：`grep -n "self\.\(height\|width\|size\|pos\)" file.py`，注意区分
     属性赋值（要改）与 `self.height()` 方法调用（不能动）
   - v0.11 又踩：dxf_panel.py 的 DxfPreview 也写了 `self.height`（2026-08-13 打包 exe
     后 paintEvent 静默报 TypeError 才暴露，offscreen 回归 tail 截断漏掉）——老坑会漏进
     新模块，交付打包前必须全项目 grep 复查本坑

2. **QPainter 的 drawLine/drawEllipse 等坐标参数传 float 会崩溃**
   - `p.drawLine(cx - r - 10, cy, ...)` 中 r=float → 崩溃（不仅是 drawText，所有 QPainter 绘图方法都要 int）
   - 修复：`p.drawLine(int(cx - r - 10), cy, int(cx + r + 10), cy)`
   - 验证手段：QT_QPA_PLATFORM=offscreen 下 show() 能复现崩溃（exit 127、stdout 缓冲丢失表现为"无输出"）；用继承子类覆盖 paintEvent 逐步二分（实例属性 monkey-patch 对 paintEvent 不生效，必须类级继承覆盖）

3. **PyQt5 实例属性覆盖 C++ 虚函数一律不可靠 → 用事件过滤器**
   - paintEvent/resizeEvent 等虚函数都不能靠 `self.xxx = 方法` 覆盖
     （PyQt5 事件分发走 C++ 虚表，实例属性不生效）
   - 需要监听控件事件（如 GLViewWidget 的 Resize）用
     `widget.installEventFilter(self)` + 实现 `eventFilter(obj, ev)`，
     判断 `ev.type() == QEvent.Resize` 后处理
   - 案例：航天花板定位曾用 `self.gl.resizeEvent = _on_resize` 失效，
     改 eventFilter 后窗口拉伸时小立方体才跟着走（2026-08）

4. **GLViewWidget 上叠加 QWidget 子控件（航天花板）两个坑**
   - 位置计算必须防越界：`x = max(15, gl.width() - gs - 15)`，
     窗口宽度小时裸算会得到负坐标，控件被移到屏幕外"消失"
   - 透明背景（WA_TranslucentBackground + fillRect 全透明）在 OpenGL
     父视图上可能合成失败导致看不到 → 画半透明深色面板
     `p.fillRect(0,0,w,h, QColor(15,20,35,190))` + 边框保证可见；
     并 `raise_()` 确保置顶

5. **pyqtgraph GLMeshItem 着色器：shaded 旋转会变暗；'edgeHighlight' 是拼写错误**
   - `shader='shaded'` 带固定方向光照（源码里写死 `vec3(1,-1,-1)` + ambient 0.2），
     旋转时明暗随法线角度变化 → 用户反馈"颜色会变暗"。
     **注意 pyqtgraph 0.14 注册名是 `'edgeHilight'`（少个g），写成 `'edgeHighlight'`
     会 KeyError 被 Qt 吞掉 → mesh 整体不渲染只剩点**（用户反馈"实体表面只剩点"
     的真凶）。查可用 shader：
     `from pyqtgraph.opengl import shaders; list(shaders.ShaderProgram.names.keys())`
   - **最终方案（用户集显环境实证）**：`shader='shaded'` + **法线全部指向光源**——
     `mesh_data._vertexNormals = np.tile(normalize(1,-1,-1), (N,1))`（MeshData 构造
     **不支持 normals 参数**，只能覆盖内部属性；smooth=True 时用 vertexNormals）。
     法线恒朝光源 → dot(n,L)=1 → 亮度恒满 → 旋转不变暗，且 shaded 在集显能渲染
   - 面颜色用高度 colormap（低蓝→中绿→高红，`_height_cmap` 分段插值）无光照也能
     看出起伏；`drawEdges=True` + `edgeColor=(0,0,0,0.4)` 显示三角网格线（褶皱结构）
   - **GLMeshItem 用 **kwargs 接收参数**（inspect.signature 看不到参数名），
     drawEdges/edgeColor/shader 等都以 kwds 传入；mesh 先降采样到 8000 点防卡顿
     （3万点剖分6万面集显渲染不动）
   - `heightColor` shader 按顶点z着色（uniformMap 9参数）理论可行，但用户集显
     GLSL 可能编译失败不渲染 → 弃用，优先用 shaded+法线技巧
   - 点云模式（GLScatterPlotItem）无光照不受影响；**半透明点/线在白色背景下会
     混合发白**（translucent 混合）→ 要求颜色恒定就 `alpha=1.0` + `glOptions='opaque'`
   - **paintEvent 静默异常排查法**：paint 里 Python 异常被 Qt 吞掉（不崩、只 stderr
     打印），表现为"面板画了、某元素没画"。排查先看 paintEvent 里 import 是否齐全、
     API 名拼写是否正确。实证案例：GizmoWidget 忘 import `QPolygonF` → 六面体
     drawPolygon 抛 NameError → 面板可见小方块不可见（2026-08）
   - **pyqtgraph 0.14 顶层没有 GLLinePlotItem**：`pg.GLLinePlotItem` 报
     AttributeError，必须 `from pyqtgraph.opengl import GLLinePlotItem`
     （同类顶层未暴露的项：查 `from pyqtgraph.opengl import ...`）。实证：
     点云分析"实际图"模式画设计轮廓线（2026-08-10）
   - **GLScatterPlotItem 单点循环 addItem 只显示轮廓框**：几百个单点
     item 逐个 addItem 在 GLViewWidget 上可能不渲染（用户反馈"只显示了
     一个框，里面的炮孔呢"）→ 合并成**一次** addItem（pos=N×3 数组 +
     color=N×4 数组），实测一次渲染全部可见
   - **实体表面"黑漆漆糊背景"（用户两次反馈才到位）**：_height_cmap 最低色从
     0.10 起步在深色背景下几乎不可见 → 第一次提亮到最低 (0.35,0.55,1.0)，
     用户仍嫌暗（"颜色看起来还是好暗...颜色深到看不出来有变化"）→ **最终版
     最低色 0.55 起步**：stops=[(0.0,(0.55,0.70,1.00)), (0.33,(0.45,0.95,0.95)),
     (0.55,(0.60,1.00,0.50)), (0.75,(1.00,0.92,0.45)), (1.0,(1.00,0.55,0.50))]，
     中间色阶对比拉开，深/白背景都清晰；网格线 edgeColor (0,0,0,0.4)→
     (0.15,0.15,0.15,0.25)。教训：colormap 提亮一次可能不够，用户环境
     （集显+shaded）感知更暗，按"亮到夸张"的标准给
   - 详见 `references/pyqtgraph-3d-mesh-pitfalls.md`

### 6. QTableWidget 列宽：resizeColumnsToContents() 会覆盖 Stretch/Fixed 模式
   - 先设 `setSectionResizeMode(QHeaderView.Stretch)` 等宽后，
     同一刷新函数末尾再调 `resizeColumnsToContents()` 会把列宽打回
     内容宽度，等宽失效 → 二者选其一

### 7. paintEvent 里忘 import Qt 类 → 绘制缺失不崩（被 Qt 吞）
   - paint 阶段 Python 异常被 Qt 吞：界面不崩、只 stderr 打印 Traceback，
     表现为"面板画了、某元素没画"（实证：GizmoWidget 用 QRect 但
     `from PyQt5.QtCore import ... QRect` 漏了 → 六面体标签一直画不出来，
     直到交付前回归抓 stderr 才发现）
   - 排查：offscreen 回归时**必须看 stderr**；或 `widget.grab()` 强制走
     paintEvent + sys.excepthook 打印被吞堆栈
   - 新加绘制代码后核对 import：QPainter 系（QPen/QColor/QBrush/QFont/
     QPolygonF/QPointF/QRect）集中在 QtGui/QtCore 两行 import

### 界面观感规范（用户铁律，2026-08 用户多次纠正后固化）

- **深色背景一律用浅色文字**（白/#ccc/#ddd），绝不用黑字——黑色在深底上
  看不清（用户原话"以后在做的时候也要避开这个问题"）。凡 QLabel/
  QTableWidgetItem 出现在深色面板上，显式设 `color:#fff` 或 `#ccc`
- **表格 cell 对齐统一规则**：数字居中、不超过一行的短文字居中、
  超过10字的文本换行居中。封装通用函数 `_set_center_cell(table, row, col, text)`：
  超10字用 cellWidget(QLabel wordWrap 居中)，否则 QTableWidgetItem
  setTextAlignment(Qt.AlignCenter) + setForeground(浅色)
- **纯示意图必须带读图说明**：如围岩分区图要标注"蓝弧=掌子面轮廓，
  彩色椭圆=分区等级"，用户看不懂无标注的示意（原话"那个蓝色半弧是什么"）
- **信息面板与图并排优先左右结构**（HBox），上下堆叠显得上面空下面挤；
  用户明确要求把"当前围岩状态|掌子面分区图"从上下改成左右
- **交付内容字号"客户看得清"铁律（2026-08-13 用户反馈"字体太小"）**：
  客户/现场人员要看的成品字号必须够大——**窗口放大≠内容放大**，Word 字号、
  QPainter 绘制字号都是固定值，必须直接调字号，且给用户调字号的能力：
  - Word 施工日志：正文默认放大到**五号 10.5pt**（原10pt仍被嫌小），UI 加
    字号下拉（小五9/五号10.5/小四12，默认五号）→ `generate_construction_log(
    data, path, font_size=10.5)` 参数化；章节标题 11→12pt
  - QPainter 绘制图上文字（原7~8pt 蚂蚁字）**放大一倍**（7→14、8→16），
    图例/说明布局同步防溢出（图例间距 15→24、底部说明 y 上移 h-10→h-34）
  - QTextEdit 正文 12px→18px（如"当前围岩状态"文本）

## 核心模块架构

一个完整的凿岩台车炮孔设计系统通常包含以下模块：

```
┌─────────────────────────────────────────┐
│          智能炮孔设计系统                  │
│                                          │
│  [串口设置] ─→ 连接全站仪/RTK等测量设备    │
│                                          │
│  功能模块：                               │
│  ① 参数化炮孔设计（BIM可视化）             │
│  ② 台车设备参数输入（尺寸/臂长/钻杆）       │
│  ③ 定位数据接入（全站仪/RTK坐标）          │
│  ④ 自动对位计算（台车位置→钻臂→炮孔）      │
│  ⑤ 3D模拟（俯视图+侧视图）                │
│  ⑥ 炮孔数据导出（JSON/DXF/CSV）           │
│  ⑦ 打完数据回读+偏差分析                  │
└─────────────────────────────────────────┘
```

## 炮孔设计参数体系

### 隧道参数
- 围岩等级（Ⅰ~Ⅴ级）
- 隧道跨度/断面尺寸
- 开挖方式（全断面/台阶法/CD法/双侧壁导坑）
- 炮孔类型：掏槽眼、辅助眼、周边眼、底板眼
- 各类型：数量、圈径、深度、角度

### 台车设备参数（全部可调）
- 台车外形尺寸（长×宽×高）
- 钻臂数量、钻臂长度、基座高度
- 钻臂运动范围（水平回转角、俯仰角、伸缩范围）
- 推进行程、钻杆长度

### 定位参数
- 台车当前坐标（X, Y, Z）
- 朝向角、俯仰角
- 距掌子面距离

## 参数修改两级保护（防误触设计）

所有可调参数必须分两级，不能锁死也不能让工人随手一碰就翻车：

### 🟢 一级：工人可调（实时生效，确认框防误触）
操作层面的参数，工人根据现场情况微调，弹确认框后直接生效：

| 参数 | 范围限制 |
|:----|:--------:|
| 炮孔深度 | ±0.5m |
| 炮孔角度 | ±5° |
| 孔位偏移 | ±10cm |
| 台车坐标微调 | ±5cm |

交互：拖拽/输入后弹窗「确认修改？[确定] [取消]」

### 🔴 二级：需审批（工程师/班长二次确认）
动了会影响整体设计的安全相关参数，不能一个人说了算：

| 参数 | 说明 |
|:----|:-----|
| 掏槽形式切换 | 楔形↔直眼↔混合 |
| 围岩等级变更 | Ⅰ↔Ⅱ↔Ⅲ↔Ⅳ↔Ⅴ |
| 开挖方式切换 | 全断面↔台阶法↔CD法 |
| 总炮孔数增减超过20% | 全局设计变动 |

交互：改完后弹窗「⚠️ 此修改将影响整体爆破设计，请输入工程师验证码确认」
或需另一位操作员刷卡/扫码二次确认。

代码实现：一个简单的权限标志位
```python
PARAM_LEVEL = {
    'hole_depth': 'green',      # 工人直接改
    'hole_angle': 'green',
    'blast_pattern': 'red',     # 需二次确认
    'rock_grade': 'red',
}
```

## 显示逻辑

### 3D模拟视图（必须带标注）
- **俯视图**：隧道左右壁、掌子面、台车（尺寸标注）、钻臂（数量+长度标注）、打孔方向箭头、距掌子面距离
- **侧视图**：隧道轮廓/跨度/净高、台车高度、基座高度、钻臂
- **底部图例**：颜色对应关系（台车/钻臂/钻头/掌子面/炮孔）
- **缩放逻辑**：自动适应窗口大小，按最大炮孔圈径缩放

## 坐标系约定

- 导出数据时：原点在断面中心，X水平向右，Y垂直向上（翻转屏幕Y轴）
- 最终以台车控制系统要求的坐标系为准，可在导出处做转换

## 钻进参数监控子系统

凿岩台车在钻孔过程中的实时参数监控，包含：

### 钻进参数列表（全部可调，带报警阈值）
| 参数 | 单位 | 说明 |
|:---|:---|:---|
| 钎头X/Y/Z | m | 钻头当前位置坐标 |
| 需钻深 | m | 当前孔的设计深度 |
| 推进速度 | m/min | 钻杆推进速率 |
| 推进压力 | bar | 推进油缸压力 |
| 冲击压力 | bar | 凿岩机冲击压力 |
| 回转压力 | bar | 钻杆旋转压力 |
| 领孔速度 | m/min | 钻头刚接触岩面时的推进速度（防止开孔跑偏） |
| 水流量 | L/min | 冲洗水流量 |

### 报警系统
- 每个参数独立设置**下限/上限**
- 超出范围 → 红色"⚠报警!" + 灯闪烁
- 正常 → 绿色"正常 ✓" + 常亮绿灯
- 模拟测试：用定时器+随机数波动模拟传感器数据

### 纯QPainter简易3D（替代matplotlib的方案）
当matplotlib安装有问题或导致闪退时，可用纯QPainter绘制等轴3D投影：
```python
def proj(x, y, z):
    # 等轴投影：先绕X轴转25°，再绕Y轴转60°
    rx = x
    ry = y * cos(25°) - z * sin(25°)
    rz = y * sin(25°) + z * cos(25°)
    px = cx + (rx * cos(60°) - rz * sin(60°)) * scale
    py = cy + (rx * sin(60°) + rz * cos(60°)) * scale
    return int(px), int(py)
```
注意：纯QPainter 3D不支持鼠标拖拽旋转（需要完整的OpenGL管线），适合展示静态3D效果

## 常见问题与解决

### 闪退排查
1. cmd中运行看错误信息（不要双击.py）
2. 常见原因：DLL加载失败（exit code 3221226505）、中文路径问题
3. 解决方案：加`chcp 65001`、使用%~dp0相对路径、删除`SetProcessDpiAwareness`行、切换tkinter
- 如果PyQt5反复闪退且matplotlib也报DLL错误，回退到纯PyQt5绘制简易3D（QPainter手动画等轴投影）
- tkinter：不支持8位十六进制颜色码（`#64C8FF99`），认6位（`#64C8FF`），否则抛 `_tkinter.TclError: invalid color name`

### 打开方式
- .py文件：右键→打开方式→选python.exe→勾选"始终使用"
- 或用.bat启动：
  ```bat
  @echo off
  chcp 65001 >nul
  "D:\python\python.exe" "%~dp0your_script.py"
  pause
  ```

## 导出格式

- JSON（结构化数据，含坐标/类型/深度/角度）
- 可扩展至DXF（CAD格式）、CSV（表格格式）
- 最终格式以台车控制系统要求为准

### 施工日志自动生成

打完一个循环后自动生成施工日志，**v0.10.1 起分8个板块**（新增「五、预警系统反应」
和「六、维保记录」，原五/六顺延为七/八）：一炮孔设计参数 / 二实际钻孔记录 /
三钻孔质量统计 / 四异常记录 / **五预警系统反应 / 六维保记录** / 七施工信息 / 八下循环建议。
JSON schema 新增两个顶层字段：`预警记录`（时间/参数/阈值/实测值/级别-严重红警告橙/处理）
和 `维保记录`（项目/计划日期/完成日期/执行人/状态-超期红），均以表格写入 Word。
预警记录后续可从钻进参数监控 Tab 的报警日志自动汇入。

**数据流转架构：**

```
台车工控机（任意系统：Windows/Linux/PLC/嵌入式）
  → 打完孔导出 JSON 数据文件（纯文本，通用格式）
  → U盘/串口传到工程师笔记本
  → 软件读取 JSON → 自动生成 施工日志.docx
```

**JSON 作为跨平台交换格式** — 任何系统都能读写 JSON（纯文本，几十KB），不依赖台车工控机安装额外软件。

**最终交付物是 .docx（Word 文档）** — 可打印签字归档，不是 txt。用 python-docx 生成。

**施工日志各字段属性：**

| 板块 | 字段 | 来源 | 是否可编辑 | 交互方式 |
|:----|:----|:----|:---------|:--------|
| 项目信息 | 项目名称 | 预设配置 | ✅ 可选 | 下拉选择 |
| | 施工里程 | 预设/手动 | ✅ 可选+手动 | 下拉+自由输入 |
| | 施工日期 | 系统自动 | ✅ 可改 | 日历选择 |
| | 班次 | 预设 | ✅ 可选 | 下拉（早班/中班/晚班）|
| | 循环编号 | 自动递增 | ✅ 可调 | 手动微调 |
| | 围岩等级 | 设计同步 | ⚠️ 只读 | 跟随设计文件 |
| | 开挖方式 | 设计同步 | ⚠️ 只读 | 跟随设计文件 |
| 设计参数 | 炮孔表 | 软件生成 | ⚠️ 只读 | 显示 |
| 实际钻孔 | 每条记录 | 台车传感器 | ⚠️ 只读 | 数据回传不可改 |
| 异常记录 | 自动检测部分 | 规则检测 | ⚠️ 只读 | 自动生成 |
| | 人工备注 | 操作员输入 | ✅ 可编辑 | 文本框自由填写 |
| 施工信息 | 台车编号 | 预设 | ✅ 可选 | 下拉选择 |
| | 操作员 | 手动 | ✅ 可选 | 下拉选择（预设名单）|
| | 纯钻孔时间 | 台车自动 | ⚠️ 只读 | 数据反馈 |
| 下循环建议 | 建议文本 | 规则生成 | ✅ 可编辑 | 文本框，自动填充后人工修改 |

**核心原则：传感器数据不可改，信息字段加下拉选项，建议由规则生成后人工确认。**

**⚠ 偏差计算公式（2026-08-10 揪出的"看着对实际错"bug）：**
钻孔偏差必须是 **实际−设计的矢量差**：
`dev = hypot(实际X−设计X, 实际Y−设计Y) × 100`（cm）。
若误用"实际坐标距断面原点的距离"（`hypot(实际X, 实际Y)×100`），掏槽孔
（设计坐标在0.6m圈上）会显示 63cm 假偏差，平均偏差、质量评级、下循环建议
全部跟着错——数据"看起来合理"实际全错，这类 bug 最危险。封成统一函数
`_hole_dev(h)` 供表格/摘要/质量统计/建议/Word 5处复用，样例数据必须
含 `设计X/设计Y` 字段才能算。

**预览区表格化（用户要求）**：样例/预览要横平竖直的表格（QTableWidget +
`setSectionResizeMode(Stretch)` 自动等宽，同列数同列宽），**日常每孔数据
都要列出**（不只异常记录）——用户原话"记录的内容不是说异样了才记录的，
而是日常没有异样的也要记录"。Word 表格用 `_set_table_widths(table)` 等分
列宽（15.4cm/N）保证横平竖直。

### python-docx 统一排版工具函数

生成施工日志.docx 时，所有表格单元格必须用以下统一函数设置，不能逐行手动设格式（否则字体大小会不一致）：

```python
def _set_cell_text(cell, text, bold=False, size=10.5,
                   align=WD_ALIGN_PARAGRAPH.CENTER, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    run = p.add_run(str(text))
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = '宋体'
    if color:
        run.font.color.rgb = color
    # 单元格垂直居中
    from docx.oxml.ns import qn
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    vAlign = tcPr.find(qn('w:vAlign'))
    if vAlign is None:
        vAlign = tcPr.makeelement(qn('w:vAlign'), {})
        tcPr.append(vAlign)
    vAlign.set(qn('w:val'), 'center')
```

禁止写法：`cell.text = str(x)` + 再套三层 for 循环去设字体（Python-docx 的 cell.text 会拆掉原有格式，导致字体样式不一致）。

### Word 排版标准（施工日志.docx 生成规范）

生成 .docx 时必须统一字体和格式，否则用户会注意到字体大小不一致：

| 元素 | 字体 | 字号 | 颜色 | 说明 |
|:----|:----|:----|:----|:-----|
| 标题「施 工 日 志」 | 黑体 | 16pt | #1A3C6E | 居中，段后12pt |
| 项目信息行 | 宋体 | 10.5pt | 黑色 | 左对齐，段前段后0 |
| 章节标题（一~六） | 黑体 | 12pt | 黑色 | 加粗，段后6pt |
| 正文/表格内容 | 宋体 | 10.5pt（可调9~12） | 黑色 | — |
| 表格表头 | 宋体 | 10.5pt（可调9~12） | 黑色 | 加粗 |
| 表格边框 | Table Grid 实线 | — | — | 不用 Light Grid Accent 1 |
| 单元格对齐 | — | — | — | 水平居中 + 垂直居中 |
| 偏差超标标记 | 宋体 | 同表格 | #FF0000 | 偏差>3cm的单元格标红 |
| 生成时间 | 宋体 | 9pt | #888888 | 右对齐 |

v0.12 起 `generate_construction_log(data, path, font_size=10.5)` 参数化字号，
UI 提供下拉（小五9/五号10.5/小四12，默认五号）——**客户打印看得清**（用户反馈
原 10pt 太小，窗口放大无效，必须直接调 Word 字号）。

表格内容用 `_set_cell_text()` 统一设置，不要逐行手动设格式。

详细模板见 `templates/construction-log-template.md`

### 下一循环建议——纯规则离线生成

**下循环建议不依赖 AI / 不依赖网络。** 全在软件里写死的 if-then 规则引擎执行：

```
if 平均偏差 > 3cm →
    "偏差偏大，建议检查围岩条件，调整布孔参数"
if 推进压力在某区域异常升高 →
    "XX附近围岩变化，建议下一循环辅助眼微调"
if 整体质量优秀 →
    "整体质量稳定，保持当前参数"
if 有超挖记录 →
    "建议周边眼外插角减小1°"
```

规则生成后显示在文本框中，操作员可以自己改或删，最后签字确认。

## 爆破设计计算公式体系（布孔算法依据）

凿岩台车布孔的岩土力学/爆破计算全链路公式见
`references/blast-design-formulas.md`：围岩分级（普氏f）→
炸药单耗q → 循环进尺 → 孔网参数（孔距/抵抗线/密集系数）
→ 单孔装药量 → 爆破振动验算（萨道夫斯基公式）→ 超欠挖验算。

- 用途：系统"爆破设计模块"的算法依据 + Coze凿岩台车Agent知识库素材
- 原则：理论公式写死在算法里；经验系数（q、K、α、孔径倍数、装药系数）
  全部做成可调参数，查《爆破安全规程》GB6722核对 + 现场试爆标定
- 向用户交付公式文档：用 .docx（python-docx 上下角标），见 math-output-style 技能
- 已实现为计算引擎：`blast_design.py`（Tab8），实现细节与关键算法决策
  见 `references/blast-design-engine.md`（掏槽孔线装药密度法、Qmax手算对照
  验证、保护目标场景=既有隧道/衬砌/边坡/管线勿用民房、GUI两列布局偏好、
  offscreen调试技巧：不show只实例化/faulthandler定位/脚本模式sys.path）

## 台车定位与纠偏骨架（v0.10，2026-08-10）

用户审架构发现两个硬伤后落地：① 布孔图不能是"均匀同心圆"理想分布，
要按真实掏槽/辅助/周边/底板方式列公式生成；② 要有坐标系概念——
台车定位 + 掌子面中心二次定位互检纠偏。**全部内嵌主程序**
drill_design_v09.py（见"模块化边界"），offscreen 验证通过。

### 坐标系体系（列公式的基础）
- 隧道全局系 G：X=里程方向，Y=横向，Z=高程
- 掌子面系 F：原点=掌子面中心（断面中心投影），Y右 Z上
- 台车系 T：原点=台车定位基准点，X_T=车头朝向（指向掌子面）
- 钻臂基座系 B：相对台车系固定偏移

### 四个核心函数（全部内嵌主程序，纯函数可单测）
| 函数 | 作用 | 要点 |
|:----|:-----|:-----|
| `design_to_rig(y,z,dy,dz,yaw)` | 掌子面系→台车系坐标变换 | 平移(dy,dz)+旋转yaw：`ey=y-dy; ez=z-dz; y'=ey·cos+ez·sin; z'=-ey·sin+ez·cos` |
| `compute_positioning(dy,dz,yaw,D)` | 二次定位 | 超5cm提示移车、超1°提示转向、D超范围提示进退；输出偏差明细+纠偏提示 |
| `check_reachability(holes,D,rp)` | 钻臂可达性校验 | 每孔反解距离/回转角/俯仰角，超臂展/超回转/超俯仰标红 |
| `gen_holes_realistic(span,height,depth,cut,shape,counts)` | 真实布孔 | 掏槽直眼/楔形 + 辅助梅花形(按行抽稀) + 周边轮廓(等弧距,跳过底部段) + 底板贴底部线 + 去重保险；counts=用户数量(0=自动)；shape=7种断面形状之一（见"多形状掌子面"节） |

### 真实布孔分布（替代均匀同心圆）
v0.10.1 最终签名 `gen_holes_realistic(span, height, hole_depth, cut_type, shape,
counts=None, depths=None, radii=None)`——
shape 决定周边孔沿哪种轮廓（见"多形状掌子面"节）；height 是断面高度（默认=跨度）；
- **counts**={'掏槽','辅助','周边','底板'} 为**用户设置数量**（0/缺省=自动按公式）。
  **数量参数必须生效**（用户改孔数→图要跟着变，曾因漏读 UI 数量被用户点名）
- **depths**={'掏槽','辅助','周边','底板'} 各类型独立钻孔深度（缺省用 hole_depth）
- **radii**={'掏槽':布置圈半径, '辅助':梅花孔距}
- **辅助眼理论数验算**：`aux_theory_count(span, height, shape, a_aux)`
  n ≈ (断面面积 − π·0.55²掏槽区 − 周长×0.4周边带) ÷ (孔距×排距)，UI 实时显示
  "辅助眼理论≈N个"——给用户"输入数量 vs 理论值"的验算抓手（曾填6 vs 理论27）
- **直眼掏槽**：中心1空孔（画空心圆）+ counts['掏槽']个装药孔一圈；**楔形**：两排对称，每排 ceil(n/2)
- **辅助孔**：梅花形网格（隔行偏移半格，孔距0.8m×排距0.8m），裁剪
  `_in_polygon` + `_dist_to_polygon ≥ 0.3` + **距所有掏槽孔 ≥0.4m**（防楔形掏槽孔紧贴）；
  **抽稀两步走**：① 按行（zz）分组保持梅花形行列结构（不能按"距中心排序后
  隔点取"——行列规律被打乱，看起来像随机布孔，用户原话"没有规律"）；
  ② 行分组后**扁平化为 flat 列表再全局均匀抽稀**（`step=len(flat)/n_aux`，
  `sel=[flat[int(i*step)]...]`）——只按行分组每行取 per_row 个会在孔数<行数时
  （如填6个）每行取最左点、**全部挤在一侧**（用户原话"为什么我输入6个它都会
  出现在一侧"）。扁平化+全局 step 抽稀后各行交错取点，少量孔也分散分布
- **周边孔**：沿轮廓等弧距（孔距0.65m），**跳过底部段**（z < zmin+0.4 的段）——
  底部由底板孔负责，否则周边∩底板同位重叠（现场施工不能重叠炮孔）
- **底板孔**：沿轮廓底部线分布。⚠ 圆断面下底板是**弧线不是水平线**——z=-r
  在 y≠0 处会越界。通用做法 `_bottom_line(contour)` 沿轮廓边做 y 向插值取
  最低 z（不要按轮廓采样点集取最低——矩形轮廓只有5个角点会漏点）
- **去重保险**：生成全部孔后，任意两孔间距 <0.1m 视为重叠，保留先布的删后孔
- 孔数据键用 `y`(横向)/`z`(高程)，旧画布读 `x`/`y`——画布兼容写法
  `hh.get('y', hh.get('x', 0))`、`hh.get('z', hh.get('y', 0))`；
  `empty` 键标记空孔画空心圆

### 钻臂几何参数——固定占位，不是可调UI
**用户决策（2026-08-10）**：所长确认参数"能有"但**还没给**，所以
"这个都可以是固定的"——用固定字典 `RIG_PARAMS` 写行业常见值占位
（臂长6m/推进梁4.5m/回转±40°/俯仰±45°/基座偏移/作业距离4~10m），
注释标注"待设备所实测数据替换"，拿到实测只改这一个字典，不做参数UI。
（与"参数全可调"原则不冲突：可调是**用户可调参数**；设备自身几何参数
是**设备属性**，实测后就是定值。）

### 定位数据源——手动输入版
台车现在只有平面坐标/部分，用户拍板"先做可手动输入的版本"：
dy(横向cm)/dz(高程cm)/yaw(偏航°)/D(到掌子面m) 四个输入框，
参数一改自动重算（valueChanged/currentIndexChanged 连 `_run`），
不用点按钮。真机联调后替换为惯导/传感器数据流。

### 纠偏双粒度（用户要求"两个都要"）
1. **台车级**：偏差超限提示移车/转向/进退（阈值 dy/dz±5cm、yaw±1°）
2. **钻臂级**：布孔坐标自动补偿——设计孔位经 design_to_rig 转到台车系，
   台车按补偿后坐标打孔，画布显示可达范围圆（半径 sqrt(mx²-(D-base_x)²)）
   与钻臂基座，超范围孔红色 ×

### 台车系布孔图画布（RigHoleCanvas）
画：掌子面轮廓（中心=掌子面中心在台车系坐标）+ 掌子面中心十字 +
台车基准点（黄色）+ 偏差线 + 钻臂基座（青色）+ 可达范围圆（虚线）+
补偿后孔位（可达实心/不可达红×）+ 图例。

### 与Tab1联动
Tab1 布孔参数区加"掏槽形式"下拉（直眼/楔形），`_gen()` 用
gen_holes_realistic，并同步定位面板（set_span + cut.setCurrentText +
手动 `_run()`）；定位面板独立生成孔（不依赖 design_holes），保证
自己改掏槽立刻生效。

### offscreen 验证要点（本次实证）
- 验证脚本：创建 MainWindow → 断言 Tab 数量/孔数/纠偏文本 →
  改跨度+掏槽重算 → 改定位参数自动重算 → 切所有 Tab
- 8m 跨度直眼时自动标出 4 孔超钻臂范围（可达性真实工作）
- 坐标变换单测：无偏移=不变、dy=0.5m=整体平移、yaw=90°=旋转变位
- 详见 `references/positioning-rectification.md`

### 复测检验与自动纠偏（v0.10.3，2026-08-13）

用户把定位校准从"提示人工移车"升级为"**出现偏差直接给台车指令，让台车
调整自身位置**"。全部内嵌 PositioningPanel（Tab9 右侧加宽 340→430）。

- 纯函数 `build_correction_cmds(dy_cm, dz_cm, yaw_deg, D)`：超限→指令序列
  `[(动作,轴,量,单位,原因)]`，动作=左移/右移(dy)、升高/下降(dz)、
  顺时针/逆时针转向(yaw)、前进/后退(D)；全达标返回 `[]`（可单测）
- 复测检验区（QGroupBox）：达标大标签（✓定位达标可开钻 绿 / ✗未达标 红，
  tooltip 列明细）、测量记录表（序号|时间|dy|dz|yaw|D|判定，深底浅字居中，
  ✓绿✗红）、较上次记录对比（记录后当前==记录值显示"无变"是**正常行为**，
  改参数后才显差异）、按钮：记录本次测量/清空记录/导出JSON
  （含允许偏差/作业范围/指令记录）
- 一键下发纠偏指令 `_send_correction()`：生成指令→**模拟执行**（dy/dz/yaw
  归零、D 回范围边界；**允许范围内参数不动**）→setValue 触发 valueChanged→
  自动重算→达标；指令+执行结果存 `cmd_log` 数据列表，由 `_run()` 统一
  setText 渲染；预留 `_send_to_rig()` 真实通信接口（Modbus/TCP/串口待设备所负责人
  协议，到位后替换发送函数）
- **模拟下发模式**：真机协议未定时，先"指令生成+模拟执行+JSON导出"演示
  完整闭环，通信接口留注释位置——符合"先落地再对接"原则

**坑（本会话实证，2026-08-13）：**
1. **QTextEdit append 的文本会被下一次 setText 覆盖丢失**——`_send_correction`
   里 result.append('[模拟执行]...') 后 setValue 触发 valueChanged→_run→
   setText('\n'.join(lines)) 把 append 内容冲掉。修复：持久信息（指令+执行
   结果）存 `cmd_log` 数据列表，`_run()` 统一渲染，不要依赖 append 跨 _run 存活
2. **search_files 中文路径 content 搜索可能漏命中**：搜"校准|标定|定位"在
   drill_design_v09.py 0 命中，但功能明明存在——用 terminal `grep -n` 交叉
   验证立刻找到。**功能存在但搜不到时，先怀疑搜索工具而非功能不存在**
3. **offscreen 验证断言别想当然**：① 指令记录区块在 cmd_log 空时不渲染——
   断言分阶段（下发后再断言）；② 记录后当前==记录值→对比"无变"是正确行为
   不是 bug；③ dz=-3 在 ±5 范围内不纠偏、保持原值是正确行为——测试断言
   必须按"只纠超限轴"语义写

详见 `references/positioning-recheck-autocorrect.md`

### 钻孔角度体系（v0.10.3，2026-08-13 用户问"钻孔的角度有呈现吗"后补齐）

**角度语义（工程习惯）**：相对掌子面平面，**90°=垂直**；掏槽内倾/周边外插/
底板上仰都 <90°，方向由孔位隐含（中心/轮廓/底部），角度值只记偏离量。
默认：掏槽 87°（直眼内倾3）/ 辅助 90°（垂直）/ 周边 87°（外插3，控超欠挖）/
底板 85°（上仰5，防底部欠挖）；中心空孔 90°。楔形掏槽用掏槽角度（55~70°）。

- `gen_holes_realistic(..., angles=None)` 每孔写 `'设计角度'` 字段（round 0.1）——
  施工日志 generate_construction_log 读 `h.get("设计角度", 0)` **自动联动，无需改日志代码**
- Tab1 布孔参数区加"角度(°)"列：表头 5 列（类型60|数量55|圈径65|深度70|角度70），
  每行 QDoubleSpinBox(30~120) + tooltip 说明角度含义；self.hp[nm] 变 4 元组
  `(sc,sr,sd,sa)`；左面板 setFixedWidth 360→400
- Tab1 画布底部 info 行加"角度 掏槽87° 辅助90°..."一览（从孔"设计角度"去重取）
- Tab9 定位面板结果文本加：**钻臂执行角度**（可达孔回转/俯仰 min~max°，check_reachability
  反解的 az/el 原本算了没展示）+ 设计角度一览；独立生成孔传 angles=self.angles
- 详细实现/验证见 `references/hole-angle-and-recheck.md`

### exe 打包（PyInstaller，2026-08-13 首次，交付小伙伴用）

```bash
"D:/python/python.exe" -m PyInstaller -F -w --name 智能炮孔设计系统 \
  --collect-all pyqtgraph --hidden-import matplotlib.tri --hidden-import docx \
  --clean drill_design_v09.py
```
- --collect-all pyqtgraph（动态导入多）；--hidden-import matplotlib.tri / docx；
  -F 单文件便于分发；-w 无控制台；产物 dist/智能炮孔设计系统.exe（中文名 OK）
- **改代码后必须重新打包**：打包启动时读的是当时源码，中途改代码不会进 exe。
  打包完先验证 exe 能启动（后台启动+检查进程存活）再交付
- **单文件 exe 外部资源必须显式处理**（2026-08-13 v0.11 实证）：AI助手资料库
  用相对源码路径 `../凿岩台车Agent资料库`，-F 打包后 `__file__` 指向 _MEIPASS
  临时目录 → 问答降级"搜不到"。修复：`_kb_dir()` 三级查找——_MEIPASS 内嵌
  → exe 同级 → 开发路径；spec datas 加 `[(资料库路径, '凿岩台车Agent资料库')]`。
  **exe 验证必须实测数据/问答功能，不只测启动**（启动成功≠外部资源可用）
- **offscreen 回归输出必须全量抓取**（2026-08-13 实证）：回归命令 tail 截断
  会漏掉 stderr 里的 Traceback——本次 exe 启动验证才抓到 dxf_panel paintEvent
  的 `TypeError: 'float' object is not callable`（self.height 遮蔽坑第3例，
  画布静默空白不崩）。验证用 `grep -E "Traceback|TypeError|ERR"` 全量过滤；
  PyQt5 控件直接 `grab()` 强制触发 paintEvent 排查被吞异常
- 打包约 5 分钟（PyQt5+pyqtgraph+matplotlib 全家桶），后台跑 + notify_on_complete
- **打包用 spec 文件**（`--clean --noconfirm 智能炮孔设计系统.spec`）而非命令行参数：
  外部资源文件夹（AI 助手《凿岩台车Agent资料库》）在 spec 的 `datas` 里内嵌，
  代码侧加 `_kb_dir()` 回退链（sys._MEIPASS → exe 同级 → 开发路径）——否则 -F 单文件
  模式下 `__file__` 指向 _MEIPASS 临时解压目录，`../资料库` 失效、问答静默降级
  （2026-08-13 实证，详见 references/pyinstaller-embed-resources.md）
- **offscreen 回归输出不能 tail 截断**：`| tail -15` 会截掉 Qt 吞掉的 paintEvent
  Traceback（界面不崩只 stderr 打印）——本次 dxf_panel self.height 遮蔽坑就是这么
  漏到 exe 里才暴露的。回归必须全量输出 + `grep -E "Traceback|TypeError|Error"`
- **验证 exe 启动用 background + process poll**：tasklist grep 中文 exe 名（GBK 编码）
  会失败、误判"exe 没起来"；process poll 的 status=running + output_preview 能同时
  看到真实 stderr（被 Qt 吞的异常会打在这里），确认无 Traceback 再 kill 交付

### 北大合作验收对标（v0.10.3，2026-08-13 用户要求"咱们也根据他们的要求去做"）

小伙伴厂（洛阳中铁强力机械）与北京大学先进制造与机器人学院合作三项目，
需求表在桌面《企业技术合作需求简要说明表-自动对接/全电脑控制/仿形记忆.docx》：
① 拱架智能识别与自主对接（视觉AI+点云建模+机械臂纠偏；识别≥98%/建模≤3mm/装配≤5mm）
② 凿岩台车全电脑电控系统（电控自主可控；验收含"**输入爆破布孔图，一键自动钻孔**"、
   岩层自适应、多臂同步≤20ms、故障诊断≥98%、安全联锁100%、人工干预降90%+、故障率降30%）
③ 机械臂仿形记忆与自主跟随（轨迹复刻≤5mm/角度≤0.5°、双臂匹配≥99%、单循环干预<1次）

**软件侧能覆盖/补强的验收点**（①③核心是北大算法+厂里硬件运动控制，软件侧不碰）：
- ②"一键自动钻孔"→ **钻孔执行表导出**（已做）：`build_hole_exec_table(holes, dy,dz,yaw,D,meta)`
  纯函数，每孔 孔号/类型/设计坐标→台车系执行坐标(design_to_rig)/深度/设计角度/钻臂回转俯仰
  (check_reachability)/装药量/可达性；Tab1「💾 导出钻孔执行表」按钮 JSON+CSV 双格式
  （CSV utf-8-sig 带 BOM，Excel 直接开）；**空孔(掏槽中心孔)药量=0**，装药孔=
  深度×CHARGE_COEF(掏0.75/辅0.55/周0.30/底0.55)×线装药密度0.9kg/m（与 blast_design 一致）
- ②"岩层自适应"→ **围岩凿岩参数推荐**（已做）：`RockParamPanel` 内嵌类，新 Tab10
  「⚙️ 凿岩参数推荐」；`ROCK_REC` Ⅰ~Ⅴ级经验表（冲击/推进/回转压力+推进/领孔速度+水流量，
  待现场试钻标定；越硬冲击越高推进越慢）；与 Tab1 围岩**双向联动**（setCurrentIndex 相同值
  不触发 currentIndexChanged，不会死循环）；「应用推荐到钻进监控」写 DrillMonitor.dv[key]['val']
  + label.setText + _check()
- ②施工智能化（成孔合格率/故障率）→ 偏差分析+质量统计+下循环建议+预警/维保记录（已有）
详细验收指标对照、导出表字段、推荐值表见 `references/pku-acceptance-benchmark.md`

## AI 设计助手（v0.11，2026-08-13 离线规则版 Agent）

用户要求"把 Agent 和炮孔设计系统合并成一个软件"——不是随机/规则生成，而是
**真正用 Agent 输出炮孔设计**：自然语言说需求 → 解析 → 调设计引擎出方案。

### 架构决策：先离线规则版，后在线大模型版
- 用户拍板选**离线规则版**（关键词/正则解析，不调 API）：零成本、断网可用、
  演示/答辩不怕穿帮。之后升级 DeepSeek API 只需改 ai_agent_core 解析层，
  UI/引擎不动（预留升级路径）
- 模块划分：`ai_agent_core.py`（纯逻辑：parse_all/run_design/run_qa，可单测）
  + `ai_agent_tab.py`（AIAgentPanel 面板）+ 主程序 `_apply_agent_params()` 回填

### 解析器要点（对照《04_Agent输入输出参数清单》）
- 支持说法：围岩（Ⅲ级/三级/3级/Ⅰ~Ⅵ罗马字/f=6）、断面（跨度6米/6米宽/
  6×5米）、开挖方式、孔径（45毫米/45mm）、进尺（循环进尺3米/孔深3米）、
  炸药品种、掏槽形式、保护距离（距民房20米→默认振速2.5）
- 缺参检查：必填 7 项缺啥报啥（不瞎猜），选填给默认（dist=30/v_allow=2.5/
  cut_type=直眼/explosive=乳化炸药/method=全断面）
- run_design → blast_design.calc_blast_design → build_report 出完整报告
- run_qa → 资料库 txt 关键词检索（长词拆 2-3 字子串加权命中，如"萨道夫斯基"）

### 面板与集成
- Tab11「🤖 AI设计助手」：对话区 + 示例下拉（点一下填入）+ 输入框回车发送 +
  意图判断（含设计类关键词→出方案，否则→知识问答）+「⚡ 一键应用到炮孔设计页」
- `_apply_agent_params(params)` 回填 Tab1：围岩等级（只有 f 值时按 ROCK_F
  就近映射 Ⅰ~Ⅴ）、span/height、四类孔深（底板按短 0.2）、掏槽形式 →
  _gen() → setCurrentIndex(0) 切回炮孔设计页
- 独立测试入口：`ai_agent_tab.py` 的 standalone_test（不连主窗口）

### 解析器踩坑（本会话实证，2026-08-13）
1. **"6米宽5米高" 解析顺序**：先匹配 `(\d+)米(宽|跨)` 数字在前形式，
   再退到 `(跨度|宽)为?\d+米`；否则"宽5米"先命中 → span 错成 5.0
2. **只给 f=6 时 blast_design 缺 rock_grade 键**：calc_blast_design 里
   `grade = params['rock_grade']` 直接 KeyError → parse_all 兜底补
   `rock_grade='自定义'`（rock_f 优先用 f_manual）
3. **解析函数返回 None 值污染 missing 检查**：parse_span_height 等必须
   只回填非 None 字段（`out={}; if x is not None: out['x']=x`），
   否则 None 写进 merged → missing 检查误判"已给"
4. **知识检索长词命中差**：整词匹配"萨道夫斯基公式"在资料库段落可能没有
   完整词 → 长词拆 2-3 字子串（`_expand_kws`），命中权重=关键词长度

详见 `references/ai-agent-offline-parser.md`

### 在线大模型版（v0.12，2026-08-13 使用者拍板"双版本"→当天合并"单版本自动模式"）

使用者决策演变：先要求"两个 exe"（离线版现场用 + AI版演示用）→ 实现自动模式后
发现**AI版（不填key）= 离线版**，功能完全一样 → 使用者拍板合并为**单版本**：
"一个版本不就好了，能够自动识别连没连网"。最终 v0.12 = 一个 exe 通吃：
不填key=纯离线 / 填key+有网=在线大模型 / 填key+断网=自动切离线。
AI 接入=最简方案"传问题→DeepSeek→传回结果"；使用者曾问"为什么还要 API"——
**DeepSeek 官方只开放 API Key 一条通道，没有第三方账号登录授权**（网页版登录只对
DeepSeek 自家网站有效）；SaaS 云服务器代理（用户登录我们平台，服务器背后调 key）
列入 v0.13 规划，现在用"填 key 存本地"方案。

- `ai_online.py`（独立模块，纯逻辑可单测）：
  - `chat_once/chat_once_json`：POST https://api.deepseek.com/v1/chat/completions
    （OpenAI 兼容，requests，60s 超时）；JSON模式 `response_format={"type":"json_object"}`
    需 prompt 含"JSON"字样
  - `parse_design_online`：模型提取参数 JSON → 与离线 parse_all 合并（在线结果优先）
    → 复用缺参检查 → blast_design 引擎
  - `qa_online`：**资料库整库（~19KB 5个txt）作为上下文喂 DeepSeek 归纳回答**——
    解决"把公式都列出来"只回引言的问题（离线关键词检索只能片段命中，罗列/归纳类
    问题必须整库喂大模型）
  - `check_network(timeout=2.0)`：socket TCP 连 api.deepseek.com:443，**不耗 token**
  - `load_config/save_config`：软件目录 ai_config.json（mode=online/offline + api_key，
    **key 只存本地配置，绝不打进 exe 防泄露**）
- 自动模式面板 `ai_agent_tab.py`：
  - `_NetCheckThread(QThread)` 后台探测网络（pyqtSignal 回传，不卡 UI），
    QTimer 12 秒定时刷新 + 启动立即查一次
  - `_effective_online()` = mode=online 配置下（强制off→False / 无key→False /
    强制on→True / auto→net_ok）
  - 模式下拉（自动/强制在线/强制离线，默认自动），状态标签 🟢在线(自动/手动)/
    🟡未填key/⚪离线(手动强制)/⚪离线(无网络自动切换)；网络状态变化时对话区提示
    "已恢复在线/已自动切换离线"
  - **在线请求失败仍自动降级离线规则**并提示（假 key→401→降级路径已测零异常）
- 离线问答改进：`run_qa(question, top_k=None)` 按意图扩 top_k——含
  "列出/全部/所有/清单/都有/有哪些/公式"→12段，普通问题→8段（原固定3段只回引言）
- 单版本打包（`智能炮孔设计系统.spec`）：datas 内嵌资料库 + `_pkg_online/ai_config.json`
  （mode=online，dest='.'= _MEIPASS 根）；hiddenimport 加 `requests`（chat_once 函数内
  import，显式声明保险）；配置查找顺序 exe同级（用户可写，key 保存处）→ _MEIPASS 内嵌
  → 默认 offline
- **验证内嵌配置用 archive_viewer**：`python -m PyInstaller.utils.cliutils.archive_viewer -l exe`
  列内嵌文件确认 ai_config.json（mode=online 34B）与资料库已进包
- 坑：PyInstaller 静态分析能抓函数内 import（requests 在 chat_once 内），
  但显式 hiddenimport 更保险；spec 的 datas 元组 dest 用 '.' 表示 _MEIPASS 根；
  **双版本无用武之地就果断合并**——同一代码 + 不同内嵌配置=两个exe，功能重复
  时多打一份只是浪费打包时间（使用者 2026-08-13 实证）
- **落地加锁规划（使用者 2026-08-13 决策：展示期不装，项目落地必装）**：
  ① 锁 token：月度额度（从 chat_once 响应 usage 累计统计）+ 超限自动锁死走
  离线 + 管理员密码提额；② 锁 key：本地加密存储 + 机器指纹绑定（首次激活记录，
  换机失效）；③ 彻底锁=v0.13 云服务器代理（key 只放服务器，本地无 key）。
  落地时实施位置：ai_online.py（用量统计/额度判断）+ ai_agent_tab.py
  （额度UI/锁定提示/管理员重置）
- **GL/OpenGL 界面截图：offscreen 抓不到，必须真机窗口+屏幕截图**（2026-08-14
  实证）：pyqtgraph GLViewWidget（点云分析 Tab）在 QT_QPA_PLATFORM=offscreen 下
  无 GPU 上下文，grab() 抓到 80% 纯白空白；真机方案：正常启动主窗口 →
  tabs.setCurrentIndex(点云Tab) → time.sleep(3~4s) 等 GL 渲染 →
  ctypes GetWindowRect 拿窗口矩形 → PIL ImageGrab.grab(bbox) 截屏保存。
  注意：窗口会闪现在用户屏幕（截完立即 close）；截图时别手动挡屏。

### 字体经验（v0.12，2026-08-13 使用者两次反馈"字体不舒服/特别小"）

- **Word 施工日志字号**：`generate_construction_log(data, path, font_size=10.5)`
  加字号参数，默认 10pt→**五号10.5pt**；表格 size=9 统一去掉用默认字号；
  章节标题 11→12pt；UI 加"日志字号"下拉（小五9/五号10.5推荐/小四12）——
  客户打印要看得清（使用者原话"窗口放大还是小，要能调"）
- **QPainter 图内文字放大必须防溢出**：RockMapWidget 7/8pt→14/16pt（使用者要求
  "放大一倍"）后，图例起始 y 从 h-70→h-110、行距 15→24，读图说明 y 从
  h-10→h-34（14pt 字高约19px，原位置会画到画布外）；QTextEdit 文本
  12px→18px（放大到 24px 太夸张，QTextEdit 可滚动但面板窄）

## 图纸导入（v0.11，2026-08-13 DXF 自动识别）

用户需求"能不能识图"落地：导入掌子面设计图纸（DXF/CAD 为主）→ 自动读出
断面形状和坐标 → 一键布孔。**工程图纸走 DXF 矢量解析是正道**（坐标精确、
离线、比 AI 识图准）；视觉模型只适合没有矢量数据的照片（掌子面实拍），
对毫米级布孔精度不可靠。

- 依赖：`pip install ezdxf`；DWG 是加密私有格式 Python 读不了，需 CAD 里
  "另存为 DXF" 再导入
- 解析管线 `dxf_import.py`（纯逻辑可单测）：实体(LINE/ARC/CIRCLE/LWPOLYLINE/
  POLYLINE/SPLINE)→炸线段→**按端点连通性聚类成环→取面积最大环**（自动排除
  中心线/尺寸标注线干扰）→几何识别形状（矩形/圆形/拱形/马蹄形）→测
  跨度/高度/面积→单位换算（`$INSUNITS`：毫米4/厘米5/米6，**面积要 x、y
  各换算一次**）→输出与 section_contour 兼容的米制轮廓点集
- 面板 `dxf_panel.py`（Tab12「📐 图纸导入」）：打开 DXF → 识别结果文本 +
  深色轮廓预览 → 「⚡ 应用布孔」→ `_apply_dxf_result` 回填 Tab1
  shape/span/height → _gen() → 切回炮孔设计页
- 依赖安装后记得在 exe 打包时带 ezdxf（PyInstaller 会按 import 自动收集）

**坑（本会话实证）：**
1. **线段拼接反向匹配下标 bug**：`(x1,y1,x2,y2)` 里找"以当前点结尾的段"时
   把 `s[3]` 写成 `s[1]` → 矩形点序乱跳识别失败。反向匹配必须比 s[2],s[3]
2. **闭合轮廓首尾点不能删**：`_smooth_close` 只应删**相邻重复点**（圆弧采样
   产生），不能删首尾闭合点——矩形 4 点变 3 点丢角、面积错（首尾相同是
   合法闭合表示，section_contour 矩形就是 5 点首尾相同）
3. LWPOLYLINE `get_points()` 返回 `(x,y,sw,ew,bulge)` 5 元组，取坐标用
   `pts[i][0], pts[i][1]`，不要整体 unpack 成 2 元素
4. 测试样例必须同时覆盖毫米和米单位（同几何存两份），验证单位换算

详见 `references/dxf-import.md`

## 多形状掌子面（v0.10 扩展，2026-08-10）

用户要求"把各种形状的掌子面都添加之前拱形掌子面的功能"——按实际项目
断面选形状。系统支持 7 种：圆形/拱形/城门洞/三心圆/五心圆/马蹄形/矩形，
每种都有轮廓生成+面积周长+布孔+画图。调研文档：
`凿岩台车Agent资料库/06_掌子面断面形状.txt`（形状种类/验证区别/应用选择）。

### 核心函数（全部内嵌主程序）
- `SECTION_SHAPES`：7种形状常量表
- `section_contour(shape, span, height, steps)`：轮廓折线点集
  [(y,z),...]，y=横向(右正)、z=高程(上正)，**逆时针凸多边形**
- `section_metrics(shape, span, height)`：面积（鞋带公式）/周长（折线累加）
- `_in_polygon(y,z,pts)`：点在凸多边形内（逆时针 cross≥-eps）
- `_dist_to_polygon(y,z,pts)`：点到轮廓线最小距离（辅助孔裁剪/验证用）
- `_bottom_line(pts)`：轮廓底部线（沿边插值取最低 z，底板孔用）

### 各形状轮廓构造（工程参数化，够布孔示意用）
| 形状 | 构造 | 典型用途 |
|:----|:-----|:-----|
| 圆形 | 整圆参数方程 | 盾构/引水洞 |
| 拱形 | 半圆拱(0→π弧)+直墙+平底 | 矿山法 |
| 城门洞 | 浅圆拱(矢高0.5h)+直墙+平底 | 矿山巷道 |
| 三心圆 | 顶大弧+斜肩过渡+直墙 | 公路隧道 |
| 五心圆 | 复用三心圆轮廓（近似，待规范细化） | 高铁隧道 |
| 马蹄形 | 三心圆轮廓+底部仰拱反弧(δ=0.2m) | 铁路隧道 |
| 矩形 | 4角点 | 明挖/车站 |

### 布孔适配
- 周边孔：沿轮廓**等弧距**采样（累计弧长→n=周长/0.65→插值取点），不用等分角度；
  **跳过底部段**（z < zmin+0.4），底部归底板孔，避免周边∩底板重叠
- 辅助孔：梅花形网格，裁剪 `_in_polygon` + `_dist_to_polygon ≥ 0.3` + 距掏槽孔≥0.4；
  **抽稀按行（zz）分组每行均匀取**，不能按距中心排序隔点取（打乱规律）
- 底板孔：`_bottom_line` 边插值（遍历边必须含闭合边 `(i+1)%n`，否则拱形底部
  是闭合边会被漏掉，底板孔全跑到断面中部）
- 掏槽孔：与形状无关（掌子面中心区域）
- 全孔生成后去重保险：间距<0.1m 删后孔

### 踩坑记录（2026-08-10 实证）
1. **圆弧角度约定**：`_arc_pts(cx,cz,R,a0,a1)` 中 0=右、π/2=上。
   拱形上半圆必须 0→π；写 π→2π 画出的是**下半圆**（面积只剩2.1m²的假拱）
2. **三心圆侧弧几何无解**：肩点-拱脚距离 > 2×R2 时"过两点+半径R2"的圆
   不存在（圆心到两点都=R2 无解）→ 放弃侧弧，改"顶大弧+斜肩直线过渡+直墙"
3. **稀疏轮廓点测试误报**：矩形轮廓只有5个角点，"点到采样点距离"校验会把
   边中点误判离廓>0.15m → 验证必须用 `_dist_to_polygon`（点到线），
   不能 `min(点到点)`
4. **drawPolygon 自动闭合首尾**：轮廓最后点(-r,-hw)自动连回首点(r,-hw)，
   即平底/底部段，无需手动补点
5. **辅助孔抽稀打乱规律**：按"距中心排序→隔点取"会把梅花形行列打乱，
   看起来像随机布孔（用户原话"没有规律"）→ 必须**按 zz 行分组保持行列结构，
   再扁平化全局均匀抽稀**（只按行取会在孔数<行数时全挤一侧，用户原话
   "输入6个它都会出现在一侧"）
6. **_bottom_line 漏闭合边**：遍历边只到 n-1，最后一条闭合边
   （pts[n-1]→pts[0]，拱形底部正是闭合边）没算 → "最低点"取成拱弧上的点，
   底板孔全跑到断面中部还和辅助孔重叠。必须 `for i in range(n)` + `(i+1) % n`

### 界面
Tab1 布孔参数区：表头「类型|数量|圈径(m)|深度(m)」四列（**单位必须写进表头**，
用户原话\"光有表头，单位呢\"），每类孔 tooltip 说明圈径语义
（**掏槽眼=布置圈半径、辅助眼=梅花孔距、底板眼=孔距**；周边眼沿轮廓等距，
圈径**已解除禁用可输入**——2026-08-10 用户点名\"周边眼的圈径没有办法输入
调整了，这个修复一下\"，tooltip 注明\"可输入备用（暂不参与计算）\"，不要再
setEnabled(False)）。
**布孔参数组内部 8 行（黄色表头+四眼+掏槽形式+断面形状+断面高度）必须
等高等间距均匀分布**：① 表头标签 `setFixedHeight(26)` 与输入框同高
（否则表头行矮一截、上下空隙大，用户原话\"表头和下面的间距太大了\"）；
② 行间距用 `g2l.addLayout(row); g2l.addStretch(1)` 行间等分伸缩条——
**不要用 `g2l.addLayout(row, 1)`**（嵌套 QHBoxLayout 的 stretch 参数对
子 layout 高度分配不可靠，实测表头不参与拉伸、第一行前空 317px）。
⚠ 辅助眼理论数公式 `aux_theory_count()` 保留为代码函数，但**UI 上的
\"辅助眼理论≈N个\"绿色小字提示已按用户要求删除**（2026-08-10 用户：
\"不要下面辅助眼绿色的这行小字\"）。
画布缩放**必须宽高分别适配**：`s = min((w-pad*2)/span, (h-pad*2)/height)`——
用 `half=max(span/2, height/2)` 单一缩放会在高宽比悬殊时截断（跨度2m×高5m
只显示一半，用户点名"不管怎么样也应该输出完整图形"）。
三块画布（2D/台车系）按 shape 画轮廓；定位面板 set_shape 同步。

详见 `references/multi-shape-sections.md`

### 点云与断面形状一致性（v0.10.2，用户两次点名）
- **模拟点云必须按设计断面形状撒点**：`_gen_cloud()` 原来用圆形
  （`r=cos(a)/sin(a)+1.5`）生成圆盘点云——用户切拱形后点云还是圆盘
  （\"掌子面都拱形了，点云图还是个圆盘\"）。改法：读 `self.design` 的
  shape/span/height → `section_contour` 取轮廓 → 拒绝采样
  （随机 x∈[-span/2,span/2]、y∈[zmin,zmax]，`_in_polygon` 在轮廓内才收，
  while 循环上限 n×20 次防死循环），超欠挖起伏叠加在轮廓内点上
- **\"实际图\"= 纯设计图**：只画设计断面轮廓线 + 炮孔（GLLinePlotItem +
  GLScatterPlotItem 合并一次 addItem），**不要叠加点云**——用户原话
  \"我都选择实际图了，为什么还有点云图啊\"。超欠挖分析明确引导去
  点云模式/实体表面切换，统计文本注明。原来叠加点云是画蛇添足
- 点云模式的示意炮孔也改用 `gen_holes_realistic` 生成（掏槽/辅助/周边
  贴真实轮廓），不再用圆形假孔

## 布局调整工具（layout_tuner.py v2.0，2026-08-10）

用户对 Tab1 布局不满意但**说不清具体数值**时（"你能调整宽度大小""这样我调整
板块，你就知道是该怎么布局了"），做独立布局原型工具，让用户自己拖：

- 文件：`智能炮孔设计系统\layout_tuner.py`（启动：`布局调整工具.bat` 或
  `D:/python/python.exe layout_tuner.py`，独立进程不影响主程序）
- 结构：横向3列（左参数/中画布/右监控）+ 左列纵向3板块（隧道/布孔/生成按钮）
  + 右列纵向2板块（钻进监控/警报阈值）；删减=每板块 QCheckBox → setVisible(False)
- 输出：点「生成布局报告」采集当前像素值 → 各板块像素/比例/显隐状态/主程序
  建议 → 显示 + 存 `布局报告.txt`，AI 按报告数值改主程序，不用猜
- 工作流：用户拖布局→生成报告→照报告改 `drill_design_v09.py` 的 stretch/宽度

### v2.0 关键升级（v1.0 QSplitter 被用户否掉，教训）
v1.0 用 QSplitter 分隔条，用户反馈三个问题全部重做：
1. **QSplitter handle 太窄不好抓**，用户以为"没办法改变模块大小" → v2.0 用
   自定义 `DragHandle(QFrame)`（8px 分隔条 + `setCursor(SizeHorCursor/SizeVerCursor)`），
   鼠标移到边缘就是双箭头，按住拖动
2. **拖两个板块中间，其他板块也被吸附带跑** → 用户明确语义（铁律）：
   **拖哪两个板块的分隔条，就只变这两个板块——一个变大另一个等量补偿、
   总面积守恒、其他板块纹丝不动**（"这两个板块原本的总面积不变，变的只是
   这两个板块，其他板块不变"）。实现：每个 _drag_hsepN/_drag_vsepN 只改
   相邻两个尺寸，`total = a + b; a = clamp(a+delta); b = total - a`
3. **到边界无声钳制 = 用户以为卡死**（"为什么那个竖线我往右移动到一定位置
   之后就卡死了"）→ 边界保护值必须配**视觉提示**：clamp 后值没变（dx≠0）
   就触发 `_edge('右')` 状态条红字"⚠ 已到边界：右，该方向拖不动了
   （保护其他板块）"，QTimer 1.6s 后恢复。边界最小值放宽（中列200→120、
   右列120→100）给更多调整空间

### 吸附对齐（用户要的 Word/PPT 手感）——必须"松手才吸附"！
- 用户原话："同一列或者同一行有近似的参照对照，就自动忽略小误差，直接
  设置成跟参照同等水平或竖直直线上，就和word表格，ppt板块那种一样"
- **正确实现（v2.1 修复实证）**：吸附只发生在**松开鼠标时**（DragHandle 加
  `on_drop` 回调，mouseReleaseEvent 触发），拖动过程中完全自由——
  只做 min/max 边界钳制，不做任何吸附。接近相等（±24px，SNAP*2）时
  在**拖的那对板块内**等分对齐（`abs(a - total/2) < SNAP*2 → a = total//2`），
  绝不波及第三个板块
- **⚠ 致命坑：吸附放 mouseMove 里会"卡死"**（用户原话"为什么那个竖线我
  往右移动到一定位置之后就卡死了"）：SNAP 窗口（±12px）内每次 move 都把
  新位置拽回等分点，慢速拖动时永远被吸在中间、看起来完全卡住。测试只测
  "到边界卡住"漏了这个——**吸附窗口=隐形磁铁，必须只在释放时生效**
- 到边界钳制（min/max）加状态条红字提示（_edge 防抖：已提示过不再刷），
  否则用户把钳制当 bug（"还是卡死""低级问题"）

### 固定像素布局必须防溢出（v2.1 实证坑）
用户问"钻进参数监控和警报阈值设置去哪里了，我在这上面看不到啊"——其实
没丢，是**固定像素布局总宽超过可视区**（三列 360+720+270=1350px vs
预览区实际 ~1030px = 窗口1300 − 控制区270），右列整个画在视口外被裁掉。
修复：`_relayout()` 开头检测 `total_w + 分隔条 > W` 时按比例缩放
（`k = (W-16)/total_w; w1=w1*k; ...`，各列下限保护），保证所有列始终在
窗口内，窗口拉大时恢复宽布局。
**测试教训**：只断言内部状态值（`w.w3` 逻辑值=270）不够——必须断言
**控件几何在父容器内**（`p.geometry().x()+width() <= stage.width()` 且
x≥0、y 同理），否则溢出类 bug 会漏网（本次就是检查逻辑值全过、实际
右列不可见）。GUI 布局验证清单：每个板块 geometry 落在父控件边界内。

### Tab1 布局重排经验（2026-08-10 用户点名，其他Tab也可参考）
- 横向比例用 **stretch 而非固定像素**：中画布 23 : 右监控 10（≈2.29:1，
  按布局报告用户实调值；最初 3:1 用户用 layout_tuner 拖后报告 305:133px
  ≈2.29:1 再微调）——**布局最终数值以《布局报告.txt》为准**，用户拖完
  生成报告，直接照报告数值改 stretch
- 右监控内部：钻进参数监控 14 : 警报阈值设置 10（≈1.43:1，同样按报告
  393:275px 换算）
- 左列垂直：隧道参数 → 布孔参数 `ll.addWidget(g2, 1)`（stretch=1 占满中间）→
  生成布孔按钮放最后；**不要在按钮后加 addStretch**——那会把按钮推离底部，
  用户要求"生成布孔按钮落到页面最下方"
- 左面板 `setFixedWidth` 235→360（布孔参数板块加宽）；掌子面图随左面板加宽
  自动右移，QHBoxLayout spacing 保持间距不变（满足"按原间距右移"）
- 板块内控件固定宽度同步加宽（标签70px、表头列 70/70/80/90）
- 主程序默认窗口 `self.resize(1560, 820)`——窗口太小右侧监控(1/3宽)被挤窄，
  用户误以为"右边没有东西了"（2026-08-10）
- 实体表面"黑漆漆糊背景"已提亮：`_height_cmap` 最低色 0.55 起步（亮蓝），
  中间色阶对比拉开（见 pyqtgraph 坑5）

## 项目推进日志（每次进展必须追加记录）

用户要求把项目推进写成日志，最终向评委/HR/甲方展示"怎么推进项目"。

- 日志文件：`桌面\我的小项目\智能炮孔设计系统\项目推进日志.txt`
- 每次项目有新进展（改功能/见对接人/对标竞品/参赛材料/理论梳理等）后，
  主动追加一条记录，不用等用户提醒
- 记录格式7要素：日期 / 主题 / 背景问题 / 做了什么 / 产出物 /
  关键思考决策 / 下一步
- 回溯补记技巧：session_search 查会话 + 项目文件 mtime 时间戳
  （`ls -la --time-style=long-iso`）坐实日期，绝不编造事件和时间；
  不确定的细节保守表述或标注"以实际为准"
- 历史已补记至 2026-07-22（项目启动）起
- **追加日志用 patch 工具时 old_string 必须唯一**（2026-08-14 实证）：日志长、
  段落可能重复，只拿末尾两行做 old_string 会匹配到文件中间的重复内容，
  把中间大段整段重写（\r\n→\n，内容无损但 diff 巨大且风险高）。安全做法：
  用包含足够长尾部上下文的唯一 old_string，或直接 `cat >> 文件 << 'EOF'`

## 参考资料

参考文件位于 `references/` 目录下，记录了本技能开发过程中遇到的具体技术细节和实现方案：

| 文件 | 说明 |
|:---|:---|
| `references/pyqt5-3d-hole-design-patterns.md` | PyQt5 3D炮孔设计模式 |
| `references/session-drill-params-alarms.md` | v0.8钻进参数+报警系统详细实现 |
| `references/tunnel-drilling-dev-notes.md` | 隧道钻孔软件开发笔记 |
| `references/innovation-competition-guide.md` | 青年科技创业大赛备战指南（BP框架/术语/赛道分析/时间线/角色分工） |
| `references/alarm-monitoring-pattern.md` | v0.8钻进参数报警子系统完整实现（参数列表/报警逻辑/模拟数据/指示灯） |
| `references/construction-log-json-schema.md` | 施工日志JSON交换格式完整schema + 字段属性 + 下循环建议规则引擎 |
| `references/pointcloud-3d-glview.md` | 点云3D渲染——pyqtgraph GLViewWidget集成（安装依赖、模拟数据、颜色编码、导入真实点云、三角网格实体表面模式） |
| `references/gizmo-axis-cube.md` | 轴向导航天花板——GLViewWidget叠加层实现拖拽旋转3D视图 |
| `references/viewcube-gizmo.md` | v0.10.3航天花板 ViewCube 化（工程方向标签/viewMatrix投影/点击跳转正式视图/pyqtgraph相机约定/el±89坑/标签命中法/offscreen验证） |
| `references/flask-web-version.md` | Flask网页版练手项目（A类本地脚本→B类后端服务升级，SQLite+canvas；⚠️含局域网隔离坑：WiFi/网线不同网段打不开，部署方案：cpolar内网穿透=演示用、云服务器=简历链接首选） |
| `references/blast-design-formulas.md` | 爆破设计计算公式全链路（普氏f/炸药单耗/孔网参数/装药量/萨道夫斯基振动/超欠挖），含经验系数边界与GB6722标定要求 |
| `references/blast-design-engine.md` | blast_design.py 计算引擎实现（函数结构/掏槽孔线装药密度法/孔数估算/振动验算验证/Qmax手算对照/offscreen多场景测试） |
| `references/pyqtgraph-3d-mesh-pitfalls.md` | pyqtgraph GLMeshItem/点云3D渲染避坑（shader名拼写'edgeHilight'、heightColor着色器uniformMap用法、mesh降采样、半透明点白背景下发白、背景黑白切换） |
| `references/positioning-rectification.md` | v0.10台车定位与纠偏骨架完整实现（RIG_PARAMS/design_to_rig/compute_positioning/check_reachability/gen_holes_realistic/PositioningPanel/RigHoleCanvas/offscreen验证脚本/实测结果） |
| `references/positioning-recheck-autocorrect.md` | v0.10.3复测检验+自动纠偏（build_correction_cmds/达标判定/测量记录表/一键下发模拟执行/_send_to_rig接口位置/三坑：QTextEdit append被setText冲掉、search_files中文路径漏命中、offscreen断言想当然） |
| `references/hole-angle-and-recheck.md` | v0.10.3钻孔角度体系（90°=垂直语义/默认87·90·87·85/UI角度列/施工日志联动/钻臂执行角度）+ 复测检验 + 自动纠偏 + PyInstaller打包命令与坑 |
| `references/pku-acceptance-benchmark.md` | v0.10.3北大合作验收对标（三项目验收指标/软件侧覆盖点/build_hole_exec_table钻孔执行表导出/RockParamPanel围岩凿岩参数推荐Tab10/ROCK_REC经验值表/offscreen验证） |
| `references/ai-agent-offline-parser.md` | v0.11 AI设计助手离线规则版Agent（解析器全字段/缺参默认值/意图判断/知识检索/踩坑4条/一键应用回填/升级DeepSeek路径） |
| `references/ai-online-deepseek.md` | v0.12 AI在线版+自动模式（DeepSeek chat completions API/json mode参数提取/整库问答/check_network TCP探测/配置三级查找+key不进exe/在线失败降级/自动模式QThread实现/单版本spec打包/验证清单） |
| `references/bp-financial-modeling.md` | BP财务建模铁律（软件口径≠台车造价/调研数据参考非依据/买断制单客户全生命周期模型/AI成本按套累加不摊薄/保险(商业险非社保)+小规模税务/B2B买断定价15万/销量口径=签约厂商数1-3-5家/9条专业审查意见/python-docx编辑BP坑：insert_paragraph_before命中目录、addnext插入） |
| `references/dxf-import.md` | v0.11 图纸导入DXF解析（实体炸线段/环聚类取最大环/形状识别/单位换算/坑4条/验证清单） |
| `references/multi-shape-sections.md` | v0.10多形状掌子面几何（7种轮廓构造公式/布孔适配/踩坑记录/验证数据） |
| `references/pyinstaller-embed-resources.md` | v0.11 PyInstaller打包（spec datas内嵌外部资料库/代码MEIPASS回退链/exe验证三坑：offscreen tail截断漏Traceback、tasklist中文名grep失败、必须process poll看stderr） |
| `references/competitive-landscape-and-positioning.md` | 竞品格局与项目定位（整机厂全自动/国内头部产品页原话证据、执行vs设计战场划分、四条对外口径、护城河重界定、掌子面拍照重建→自动布孔技术路线与依据） |

### 模板文件

| 文件 | 说明 |
|:---|:---|
| `templates/construction-log-template.md` | 施工日志自动生成格式（8板块：一炮孔设计参数~八下循环建议，含预警系统反应/维保记录；数据来源表） |
| `templates/drill_design_v07_reference.py` | v0.7完整源码参考（2D布孔+matplotlib 3D） |

## 信号/消息模式

### 报警信号设计
- 采用**定时轮询检查**（QTimer，1秒间隔），而非事件驱动。适合模拟和测试阶段
- 报检检查逻辑：
  ```python
  def _check_alarms(self):
      alarm = False
      for key, av in self.alarm_vars.items():
          lo = av['lo'].value(); hi = av['hi'].value()
          dv = self.drill_vars.get(key)
          if dv:
              val = dv['value']
              if val < lo or val > hi:
                  av['status'].setText('⚠报警!')
                  av['status'].setStyleSheet('color:#FF4444;font-weight:bold')
                  alarm = True
              else:
                  av['status'].setText('正常 ✓')
                  av['status'].setStyleSheet('color:#4CAF50;font-weight:bold')
      # 报警时红色闪烁灯
      if alarm:
          self.alarm_light.setStyleSheet('background:#FF4444')
          QTimer.singleShot(500, lambda: self.alarm_light.setStyleSheet('background:#2B579A'))
      else:
          self.alarm_light.setStyleSheet('background:#4CAF50')
  ```
- 报警指示灯设计：一个6px高的QLabel作为底部光条，配合颜色切换实现闪烁效果
- 注意：PyQt5中，用 `QTimer.singleShot(ms, callback)` 实现单次延迟切换，不要用sleep

## 纯QPainter等轴3D投影（替代matplotlib）

当matplotlib安装有问题或DLL冲突时可用纯QPainter绘制等轴3D视图。

**限制**：纯QPainter 3D不支持鼠标交互旋转，只展示固定视角。

### 3D视图绘制要点（v0.6验证模式）
- **隧道轮廓**：绘制两组弧线（掌子面轮廓 + 深部轮廓），用虚线连接对应点
- **炮孔**：从掌子面向深部画线，线端画圆点表示钻头位置
- **标注"掌子面"和"深部"文字**
- 底部显示跨度、炮孔总数等统计信息

### 2D断面图标注规范（v0.6+）
俯视图和侧视图必须包含以下标注，方便一线工人理解：
- **俯视图标注**：`隧道左壁`/`隧道右壁`、`← 掌子面`（黄色粗线）、`距掌子面: Xm`、台车尺寸 `长Xm×宽Xm`、`→打孔方向`（红色箭头）、`钻臂×N 长Xm`、炮孔用绿色小点
- **侧视图标注**：隧道跨度、净高、台车高度、`基座高Xm`、钻臂
- **底部图例**：台车/钻臂/钻头/掌子面/炮孔的颜色对应关系
- **比例尺**：右下角显示 `1m = XXpx`
- **滚轮缩放 + 动态比例尺（v0.10.2，用户要求"做成滚轮能够控制整个图大小"）**：
  HoleCanvas 加 `self.zoom`（0.3~5.0），`wheelEvent` 滚轮 `factor=1.15` 乘除缩放、
  `mouseDoubleClickEvent` 复位 1.0；paintEvent 里 `s = 基准s × self.zoom`（宽高分别
  适配后再乘 zoom），所有绘制（轮廓/孔/网格）共用 s。右下角 `_draw_scale(p,w,h,s)`：
  选刻度 m ∈ {0.5,1,2,5,10,20,50} 让 `m×px_per_m ≥ 50px`（线长保持50~150px适中），
  画刻度线+两端竖线+标注（m≥1 显示"X m"，<1 显示 cm）；放大自动切小刻度（0.5m）、
  缩小切大刻度（2m/5m）。tooltip 注明"滚轮缩放视图，双击恢复100%"
- **最大炮孔范围虚线**：黄色虚线标出最大圈径范围（v0.3+）
- **开挖方式扇形高亮**：半透明黄色扇形显示当前开挖方式的布孔范围（v0.4+）

### 自动缩放逻辑（v0.3+）
- 所有炮孔（含周边眼沿轮廓）的最大半径作为缩放基准
- 最大半径占画布可用空间的85%，留出边距
- 窗口resize时重新计算scale并重绘
```python
def proj(x, y, z, cx, cy, scale):
    # 绕X轴旋转25° → 绕Y轴旋转60°
    ry = y * math.cos(math.radians(25)) - z * math.sin(math.radians(25))
    rz = y * math.sin(math.radians(25)) + z * math.cos(math.radians(25))
    px = cx + (x * math.cos(math.radians(60)) - rz * math.sin(math.radians(60))) * scale
    py = cy + (x * math.sin(math.radians(60)) + rz * math.cos(math.radians(60))) * scale
    return int(px), int(py)
```

### 3D视图绘制要点
- 隧道轮廓：绘制两组弧线（掌子面轮廓 + 深部轮廓），用虚线连接对应点
- 炮孔：从掌子面向深部画线，线端画圆点表示钻头位置
- 标注"掌子面"和"深部"文字
- 底部显示跨度、炮孔总数等统计信息
- **局限性**：纯QPainter 3D不支持鼠标拖拽旋转，只做静态展示。如需交互式3D，必须用matplotlib或OpenGL

### 交互式3D点云视图（GLViewWidget）

进阶方案：用 pyqtgraph + PyOpenGL 实现全交互式 3D 点云查看器，支持两种渲染模式。

详见：
- `references/pointcloud-3d-glview.md` — 点云渲染、三角网格实体表面、颜色编码、导入真实数据
- `references/gizmo-axis-cube.md` — 轴向导航天花板（小立方体拖拽旋转主场景）

### v0.8 新增功能（钻进参数+报警）

参考文件 `references/session-drill-params-alarms.md` 记录了v0.8版本的完整架构和代码结构。

## 自行验证原则（off-screen 测试）

**不要在未确认的改动后直接让用户双点开程序验证。** 你应该自己用 offscreen 模式执行无头测试：

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
- [ ] 语法检查通过（`python -m py_compile file.py`）
- [ ] 导入无报错
- [ ] MainWindow 创建成功
- [ ] 新增Tab/控件能正常实例化

**交付前完整回归（用户 2026-08-10 明确铁律："以后给我之前，自己先跑一遍，
确保功能没有退化，没有产生新bug"）** ——每次改完主程序必须跑全链路回归，
不能只验证改动的部分：
- 12个Tab全部创建（9→10凿岩参数推荐，10→11 AI设计助手，11→12 图纸导入） + 逐个 setCurrentIndex 切换无异常
- Tab1：_gen() 布孔数>0 → 改数量/圈径/深度后布孔跟随 → 7种断面形状切换
- Tab11 AI助手：run_design 解析/缺参/问答断言 + 三态（离线构建无key框/在线构建有key框/假key 401降级）+ 自动模式（_check_net 真实网络探测、mode_combo 强制离线/断网切换断言）+ _apply_agent_params 回填断言
- Tab12 图纸导入：4 种 DXF 样例识别断言（形状/跨度/高度）+ _parse 后按钮可用 + _apply 回填 Tab1 断言
- 画布强制渲染 `hc.grab()` 尺寸>0（触发 paintEvent 抓被 Qt 吞的异常）
- 施工日志：btn_sample 后表格行数列数正确 + generate_construction_log 出 Word
- 点云分析：三种模式（点云/实体表面/实际图）_update 不抛异常
- 定位面板 result 文本含"布孔：共"
- **抓 stderr**：offscreen 下任何 Traceback（即使界面不崩）都是被 Qt 吞掉的
  绘制/事件异常，必须修（实证：GizmoWidget 忘 import QRect，界面不崩但
  小立方体一直画不出来，回归抓 stderr 才发现）

## 模块化边界（用户 2026-08-10 明确纠正）

**用户原话：「不要分开，咱们最后要做的就是一个程序，把现在所有的东西功能写入启动_v09」**

- 用户不要为了"模块化"而拆新文件/开新窗口。新增功能默认**写进主程序文件**
  `drill_design_v09.py`（启动_v09.bat 跑的入口），作为新类/新Tab内嵌；
  只有**既有**模块文件（drill_modules.py 的 MWD/围岩/维保/能耗、
  blast_design.py 的爆破设计引擎）保持原样不动。
- v0.10 的定位骨架（RIG_PARAMS/坐标变换/二次定位/真实布孔/定位Tab）就全部
  写进了 drill_design_v09.py 单个文件，没有开新模块。
- 拆分模块的唯一正当理由：文件已经大到难维护、且用户同意。

当前文件结构（v0.11）：
```
drill_design_v09.py        — 主窗口 + 全部Tab编排 + v0.10定位骨架（内嵌）+ Tab11 AI助手集成 + Tab12图纸导入集成
drill_modules.py           — 4 个智能模块（MWD/围岩识别/维保/能耗）
blast_design.py            — 爆破设计计算引擎（Tab8：公式计算+断面示意图+报告）
ai_agent_core.py           — AI设计助手纯逻辑（Tab11：自然语言→参数解析 + 知识问答检索，无GUI可单测）
ai_agent_tab.py            — AI设计助手面板（Tab11：双模式对话输入+报告展示+API Key设置+在线失败降级）
ai_online.py               — DeepSeek 在线层（Tab11：chat/JSON解析/整库问答/网络探测check_network/配置读写 ai_config.json）
dxf_import.py              — 图纸导入纯逻辑（Tab12：DXF实体解析/环聚类/形状识别/单位换算，无GUI可单测）
dxf_panel.py               — 图纸导入面板（Tab12：选文件+识别结果+轮廓预览+应用布孔回调）
pointcloud_viewer.py       — 独立点云查看器（备用）
```
**注（v0.11）**：ai_agent_core/ai_agent_tab 拆成独立文件与 blast_design.py 同属
"引擎/面板模块"——它们不是新窗口，仍是主程序 import + addTab 的集成方式；
纯逻辑（解析器）拆开是为了无GUI单测，符合"引擎类模块独立文件"既有惯例。

## v0.10 新增模块

### 1. MWD随钻测量 + 历史趋势图（对标铁建重工 MWD）

**类：** `MWDTracker`（drill_modules.py）

功能：
- 逐孔记录钻进参数（推进速度、冲击压力、回转扭矩、深度、偏位）
- 按循环分组的趋势曲线图（蓝色=推进速度曲线，橙色=冲击压力曲线）
- 循环号、围岩等级标注在X轴下方
- 数据表：显示最近100条记录，异常行红色高亮
- 导出为 JSON 文件
- 模拟数据生成（40条带围岩变化趋势的样本）

**趋势图实现：** 纯 QPainter 绘制，不支持交互缩放，只展示基本趋势。

**趋势图 X 轴标注坑（本会话踩过）：** 循环数一多（>15个），循环号和围岩等级挤在同一行会显示不全（等级只露一半）。修复方案：
- 用 `label_step = max(1, len(cycles) // 15 + 1)` 只间隔显示部分循环号
- 循环号和围岩等级**分两行**画：循环号在 y=h-32，等级在 y=h-22（单独一行）
- 字号用 6pt（比正文小一号），给每格留 30px 宽度画布

**围岩推断规则（TFGM 基础）：**
```python
if feed_speed < 0.8 and impact_pressure > 15: rock_grade = 'Ⅱ'  # 硬岩
elif feed_speed > 1.1 and impact_pressure < 13: rock_grade = 'Ⅳ'  # 软岩
else: rock_grade = 'Ⅲ'  # 中等
```

### 2. TFGM围岩识别面板（对标铁建重工 TFGM）

**类：** `RockIdentifier`（drill_modules.py）

功能：
- 根据钻进参数推断掌子面围岩等级
- 5区掌子面围岩分区图（左、右、中区、左下、右下），用半透明彩色椭圆标注
- 颜色：Ⅱ级=绿、Ⅲ级=黄、Ⅳ级=橙、Ⅴ级=红
- 趋势判断文本：与上一循环对比、异常区域预警

**分区图实现：** 纯 QPainter 绘制隧道拱形断面，叠加工个椭圆区域，每个区域标出围岩等级和描述。

### 3. 维保预警（对标铁建重工 IMW）

**类：** `MaintenanceTracker`（drill_modules.py）

功能：
- 累计运行工时统计
- 超过 1500h → 红色"请尽快大保养"
- 超过 1000h → 黄色"建议安排保养"
- 5 项标准维保项目表（液压油/滤芯/润滑/电气/钻臂），含周期、上次/下次日期、状态
- 提醒闭环（2026-08）：顶部指标卡（超期/即将到期计数按 self.items 实时算）负责"提醒"，
  表格"操作"列"🔧维保"按钮负责"执行"（弹确认→重置该项保养计时→状态变正常→指标联动），
  一提醒一执行；维保项目数据持久化为 self.items，点击按钮后更新 last 再 _refresh

### 4. 能耗统计（对标铁建重工能耗优化）

**类：** `EnergyTracker`（drill_modules.py）

功能：
- 每循环耗电量/用水量/钻孔数记录
- 平均值计算 + 单孔能耗
- ⚠ 2026-08 已删掉"与行业标杆对比"板块（用户：做产品不是介绍产品），
  基准改用自身平均值：高于平均耗电标橙、低于标绿，不再对比铁建重工117kWh

### 当前系统 Tab 布局

```
Tab1  🔧 炮孔设计      — 隧道参数 + 布孔参数（表头:类型|数量|圈径(m)|深度(m) + 掏槽形式 + 断面形状/高度，板块加宽360px）→ 生成布孔按钮沉底 + 2D断面(多形状,宽高自适应) + 钻进监控(压缩约1/3宽)
Tab2  📋 施工日志       — JSON导入 + Word生成（8板块：含预警系统反应/维保记录）
Tab3  🎯 点云分析       — 点云渲染 + 三角网格实体表面 + **实际图**（设计断面轮廓+炮孔，从Tab1同步）+ 航天花板Tab4  📈 MWD随钻       — MWD记录 + 趋势曲线
Tab5  🪨 围岩识别       — 掌子面分区 + 围岩推断
Tab6  🔧 维保           — 工时统计 + 保养提醒
Tab7  ⚡ 能耗           — 水电记录 + 平均值统计（无外部标杆对比）
Tab8  💣 爆破设计      — 公式引擎：输入参数→孔网/装药/振动验算/超欠挖建议（blast_design.py）
Tab9  📍 台车定位与纠偏 — v0.10：手动输入台车坐标→二次定位纠偏→台车系补偿布孔+可达性（内嵌主程序）
Tab10 ⚙️ 凿岩参数推荐 — v0.10.3：围岩Ⅰ~Ⅴ→推荐冲击/推进/回转压力+推进/领孔速度+水流量，应用推荐写入钻进监控（岩层自适应验收点软件侧，RockParamPanel 内嵌）
Tab11 🤖 AI设计助手   — v0.12自动模式单版本：有网自动走DeepSeek在线层（ai_online.py），没网自动切本地规则，不填key=纯离线；模式下拉可强制在线/离线；API Key存软件目录ai_config.json；在线失败自动降级（ai_agent_tab.py + ai_agent_core.py + ai_online.py）
Tab12 📐 图纸导入     — v0.11：DXF图纸自动识别断面形状/尺寸+轮廓预览+一键应用布孔（dxf_panel.py + dxf_import.py）
```

### 3D交互——轴向导航天花板（QPainter 六面体）

航天花板使用纯 QPainter（不是 GLViewWidget）绘制，固定在点云分析 Tab 右上角。

**类：** `GizmoWidget`（继承 QWidget，非 GLViewWidget）

**绘制原理（v0.10.3 起改为 ViewCube 式）：**
1. 8个顶点定义六面体坐标
2. **直接用主视图 `main_view.viewMatrix().map(QVector3D(...))` 投影顶点**——不再
   自己维护旋转公式（自己推导绕Y/绕X公式与 pyqtgraph 相机不一致，角度同步了
   朝向还是错位；用同一个 viewMatrix 从根上消除偏差）
3. 画家算法：按投影后 z 排序，**z 越大越靠近观察者**，远的先画近的后画
   （front 面 = z 最大的面，用它做当前朝向高亮）
4. 每个面填充颜色 + 工程方向标签（掌子面/洞口/拱顶/底板/右侧墙/左侧墙）
5. 白色半透明棱边线

**颜色方案（工程方向，2026-08-13 起）：**
| 面 | 方向 | 颜色 | 编码 |
|:--|:----|:-----|:-----|
| 掌子面 | +Z（打孔方向） | 亮红 | #E74C3C |
| 洞口 | -Z（台车来路） | 暗红 | #C0392B |
| 拱顶 | +Y（高程上） | 亮绿 | #27AE60 |
| 底板 | -Y | 暗绿 | #1E8449 |
| 右侧墙 | +X | 亮蓝 | #5BA3EC |
| 左侧墙 | -X | 深蓝 | #4A90D9 |

**交互（v0.10.3 起含 Revit ViewCube 式点击跳转）：**
- `mousePressEvent`: 记录拖拽起点
- `mouseMoveEvent`: 计算 dx/dy → 更新 azimuth/elevation → 调用 `main_view.orbit()` 同步主场景 → 调用 `self.update()` 重绘
- `mouseReleaseEvent`: **位移 < 6px = 点击** → `_jump_on_click()` 跳转正式视图；
  位移大 = 拖拽结束
- `sync_from_main(az, el)`: 供主场景反向同步航天花板视角
- **点击跳转**：离哪个面标签文字最近（≤42px）就 `main_view.setCameraPosition`
  切到该方向正式视图——跳转表：掌子面(0,89)/洞口(0,-89)/拱顶(90,0)/底板(270,0)
  /右侧墙(0,0)/左侧墙(180,0)。**el 用 ±89 不用 ±90**（el=±90 时相机 up=(0,0,1)
  与视线平行，pyqtgraph lookAt 退化）

**自适应尺寸：** `gs = max(60, min(gl_width, gl_height) // 3)`，窗口 resize 时重新计算

**2026-08 修复记录（曾出现"小立方体不见了"）：** 两个根因——① 位置裸算
`gl.width()-gs-15` 在窗口窄时为负坐标，控件跑到屏幕外；② 透明背景子控件在
OpenGL 父视图上合成失败。修复：`x = max(15, ...)` 防越界 + paintEvent 画
半透明深色面板 + `raise_()` 置顶 + resize 监听改用 installEventFilter
（详见"PyQt5 兼容性注意事项"坑3/坑4）

**投影（v0.10.3 起）直接用主视图 viewMatrix，不再手工旋转：**
```python
def _project(self, pt):
    w = self.width() / 2
    h = self.height() / 2
    scale = min(w, h) * 0.35
    if self.main_view is not None:
        v = self.main_view.viewMatrix().map(QVector3D(pt[0], pt[1], pt[2]))
        return int(w + v.x() * scale), int(h - v.y() * scale), v.z()
    return int(w + pt[0] * scale), int(h - pt[1] * scale), pt[2]   # 兜底正交
```

**ViewCube 化要点（2026-08-13 用户两次反馈后落地，详见 `references/viewcube-gizmo.md`）：**
1. **反向同步必须接线**：`sync_from_main()` 定义了但没人调用=航天花板不动。
   PointCloudPanel.eventFilter 监听 `MouseMove`（左键拖拽中实时）+ `MouseButtonRelease`
   （兜底）→ 读 `gl.opts['azimuth'/'elevation']` → `gizmo.sync_from_main()`
2. **pyqtgraph 相机约定（实测）**：azimuth 绕 Z 轴、elevation 绕 Y 轴（负方向），
   相机位置可用 `cameraPosition()` 验证：az=0/el=0→(10,0,0)、az=90→(0,10,0)、
   el=90→(0,0,10)；viewMatrix 映射后 **z 越大越靠近观察者**（front 面 = z 最大面）
3. **el=±90 隐藏坑**：up=(0,0,1) 与视线平行 → lookAt 退化（viewMatrix 病态）。
   跳转表统一用 ±89
4. **点击命中用"离标签最近"（42px 内）而非"点在面多边形内"**：斜视角下背面
   多边形与正面重叠，多边形命中会跳错面；标签命中直观且半透明背面也能点
5. **当前正对面高亮**（Revit 式）：z 最大的面更实（alpha 150 vs 90）+ 亮边框
   + 加大标签字

## BP/对外材料写作口径（2026-08-13 使用者 3 次纠偏后固化）

台车项目的 BP、路演、对外材料写市场/成本/盈利时，四条铁律：

1. **软件口径，不是设备口径**——台车造价/毛利（调研报告里 G1Z80 制作成本、260万/台、
   毛利率50%等）是台车**设备**的数据，与软件无关（使用者原话"这个台车造价，不是咱们软件
   造价，要分开的"）。市场=软件可服务台车数×软件单价；成本=软件人力/云服务器/AI调用；
   盈利=软件收入。台车数据只能当"软件服务对象数量"的基数参考（一台全电脑台车配一套软件），
   绝不把台车售价当软件收入。
2. **参考 ≠ 依据**——调研报告数据（厂家年产量/销量，如单臂台车国产年产量约470台/年）
   只能当行业盘子参照，不能直接作为软件市场规模的依据（使用者原话"你可以作为参考，但是
   不能以此为一句依据"）。软件的渗透率/定价/保有量全是假设，必须白纸黑字标注
   【待确认/假设值】，不冒充实测（写作铁律延伸）。
3. **token 成本用"正常使用口径"，不要保守夸大**（使用者原话"日常的token数量也不会很大吧"）——
   日常简单问答一次约 500~2000 token（一句话问题+相关段落+简短回答）。分清哪些走 AI 哪些
   不走：施工日志模板生成、爆破设计引擎、钻孔执行表都是**本地计算不耗 token**，AI 只做
   自然语言解析/润色/问答。资料库先检索再喂（只带相关段落），不整库发送。预算按测算值 ×2
   预留（覆盖波动），结论写"占比极低、完全可控"。参考价：deepseek-chat 输入约¥1/百万token、
   输出约¥2/百万token（见 api-consumption-monitor 技能）。
4. **锁 token 是成本管控亮点，写进 BP**——成本结构里写"软件内置 token 用量锁定（月度额度+
   用量可查+超限自动切换离线规则），AI 调用成本可控不超支，且不影响正常使用（额度内流畅
   在线、超出自动降级本地仍可完成设计出图）"——既是成本可控证明，也是产品成熟度卖点。
5. **销量口径 = 签约厂商数（买断授权）**，不是台车数——设备所负责人口径"厂商买下来就15w，
   卖出去多少台跟你没关系"；成本公式 = 固定成本 + 每套变动成本×套数（详见
   references/bp-financial-modeling.md：买断15万/家、AI厂商自配Key自负、税务小规模、
   第1年1家/第2年3家/第3年5家、税后利润2.9/31.4/56.8万）。
6. **能力对标分两层，不能混着写**——① **工程语义层**（炮孔坐标/角度/装药量/钻臂
   可达性/爆破计算/偏差闭环）是项目的护城河，写；② **通用视觉层**（三维真实感、
   渲染、建模）是通用大模型正在免费化的能力，**不写进卖点**。对外说"我们的三维是
   被工程数据和规则驱动的，不是拿来看的"，而不是跟人比画面。完整战场划分与
   四条口径见上文《竞品格局与项目定位》。

BP 修改用临时 python-docx 脚本（段落按文本片段定位，`set_para_text` 重建 run 保留段落样式，
\n 用 `run.add_break()`），脚本用完即删、BP 只留最新版（旧版待确认后删备份）。

## 界面截图与报名 PPT 交付（2026-08-14 报名 PPT 实证）

**批量抓真实界面截图（无需人工开窗）**：offscreen 启动 MainWindow，逐个 Tab
`setCurrentIndex` + 多轮 `app.processEvents()` 给渲染留时间 + `w.grab()` 保存
PNG（1560x820 与窗口一致），12 个 Tab 一次抓完零异常。截图存项目文件夹
`_screenshots/tabNN.png`（先抓 emoji 名再批量重命名简单名，供 python-pptx 引用）。

**⚠ 截图方法选择铁律（2026-08-14 实证翻车：真机屏幕截屏截到了使用者的游戏窗口！）**
- **`widget.grab()` 自渲染是首选**——PyQt 直接渲染窗口/控件内容到 QPixmap，
  不经过屏幕。普通控件（QTextEdit 对话、QPainter 画布、表格）offscreen/真机
  都能用，**任何情况下都不可能截到别的窗口内容**
- **真机 ImageGrab.grab(bbox=GetWindowRect) 屏幕截屏只用于 GLViewWidget**
  （OpenGL 无 offscreen 上下文），且必须：`SetForegroundWindow(hwnd)` 置前 +
  sleep 0.4s 等置顶 + **确认用户屏幕上没有其他窗口盖着目标窗口**——否则抓到
  的是盖在上面的内容。本次翻车：截图脚本跑时使用者桌面开着游戏，PPT 里就混进
  （用户原话"你放的是我的游戏截图，不是软件"）。深色界面截图
  缩进 PPT 后文字看不清，也容易被误判为"不是软件"——截对话类内容优先
  局部特写（对话区+输入区），保证缩小后仍可读
- **产品实拍图必须与标签功能真实对应**（用户原话"产品是ai智能，为什么产品
  实拍没有ai部分呢"）：放图前确认截图确实是该功能的界面（P5"AI设计助手"
  标签下曾放着一张深色渲染图，不是AI对话，使用者一眼看穿）。无视觉工具时用
  PIL 验证截图内容：行剖面（每行亮/暗占比）找对话区/白带位置、ASCII 缩略图
  看布局结构、文字像素 x 范围（全宽分布=正常长文本，只集中左侧=可疑）、
  彩色像素占比（>0.5% = 有 emoji，对话界面特征）

**⚠ OpenGL 视图 offscreen 渲染空白**（2026-08-14 实证）：点云分析 Tab 是
pyqtgraph GLViewWidget（OpenGL），offscreen 无 GPU 上下文 → grab() 白屏
（PIL 采样 80% 白色像素）。**这是抓图环境限制，不是软件 bug**（真机正常）。
排查法：PIL 按步长采样统计颜色分布——`白色占比>70% + 不同颜色数少` = 渲染失败。
解决：PPT 换用非 GL 的 Tab 截图（QPainter/普通控件 offscreen 正常，如 MWD 趋势图
白色仅25%）。**交付截图前逐个 Tab 做白色占比体检**，别等用户发现。

**python-pptx 生成报名 PPT 要点**（详见 `references/screenshots-and-ppt-delivery.md`）：
- 中文字体必须设 east-asian：`run.font.name` 只设 latin 不够，要
  `rPr = run._r.get_or_add_rPr(); ea=...; ea.set('typeface','微软雅黑')`
- 16:9 = `prs.slide_width/height = Inches(13.333)/Inches(7.5)`；深色封面/结束 +
  浅色内容（sandwich）；卡片用 ROUNDED_RECTANGLE + adjustments[0] 圆角
- QA（无 LibreOffice 时）：python-pptx 回读文本 + 统计图片 shape_type==13
  数量与坐标（left+width ≤ slide_width 不越界）
- **文本溢出检测用 PowerPoint COM 实测**（2026-08-14 实证）：python-pptx 量不到
  文字真实渲染高度；用 win32com 遍历文本框，`tf.TextRange.BoundHeight > shape.Height
  - tf.MarginTop - tf.MarginBottom + 4` 判定溢出。30pt 粗体长数字（"1,650万~4,950万"）
  在 3.30in 框里尾字"万"掉第二行就是这么抓到的；修复=内边距 MarginLeft/Right 归零
  （默认各 7.2pt）+ 框加宽到 3.71in（左对齐文字实际宽度在卡片内，框宽超卡片一点无妨）。
  BoundHeight==框高 是"文本恰好两行"的假象，用 `tr.Lines().Count` 确认真实行数
- **删除旧卡片必须连其内文本框一起删**（实证）：卡片内文本框 x 偏移 ≠ 卡片 x
  （卡 0.55in、内文 0.75in），按卡片坐标删会残留旧文本框叠在新内容上——按
  文本框自己的坐标/文本内容匹配删除，删完 grep 文本确认无残留
- 替换截图流程：删旧图+旧卡+旧文本框 → 加新图（add_picture 保持宽高比）→
  改横幅文字（run 级 replace）
- **⚠ 替换 media 图片必须用 r:embed 定位真实文件名**（2026-08-14 实证：
  `sh.image.filename` 返回 basename 会误导——多张图都显示 image.png，按它
  zipfile 替换会换错文件）。正确做法：blip 元素取 `r:embed` →
  `slide.part.rels[rId].target_ref` 得到 `../media/image2.png`；替换前全 PPT
  扫描该 media 的引用唯一性（image2.png 只被目标 shape 引用才安全）；zipfile
  原位替换 blob 后，python-pptx 回读提取 md5 确认已换（不只看尺寸）。新图
  比例不同必须先居中裁剪到目标比例（如 4.05:2.13）再替换，防 shape 里拉伸
- **PPT 数字/口径一律以 BP 定稿为准**：财务页"首年10.3万（研发4.8+迭代1.5+
  维护3.6+服务器0.4+保险预留1.5）"括号合计 11.8≠10.3 自相矛盾（评委一眼看
  出），按 BP v3 口径改"首年10.3万（研发4.8+迭代1.5+维护3.6+服务器0.4），
  此后约7万/年（含保险预留1.5）"；改前备份、改后对比备份验证格式无损
- **改文本/位置防误伤**（本次两个翻车点）：① set_para_text 清 runs 只留
  第一个会重建段落——条件必须完整匹配目标字符串，含关键词的相邻段落（如
  副标题也含"固定成本"）会被误处理，改后对比备份段落的 run 数/字号/粗体；
  ② 按关键词移动 shape 位置会误伤——"3D 点云"关键词把底部横幅（"3D 点云
  分析·围岩智能识别·台车定位纠偏"）从 y=5.60 移到 y=4.28 盖住点云图说明
  （用户反馈"点云图上面下面都没有文字描述"）。位置匹配必须排除横幅/非目标
  文本，改后导出 PNG 复查

## 竞品格局与项目定位（对外口径铁律）

**先分战场，再谈强弱。** 这个行业里有两个不同的战场，混着比就会得出"我们落后"的
错误结论，也会让路演自己弱下去：

| | 整机厂（Epiroc/Sandvik/铁建重工/五新隧装） | 本项目 |
|:--|:--|:--|
| 做什么 | **执行**：台车照图钻孔、自动定位、一键钻孔 | **设计**：那张炮孔图本身怎么来 |
| 交付形态 | 绑自家整机卖的附属功能 | 不换设备的软件层，服务存量台车 |
| 覆盖谁 | 通常只覆盖自家新机 | 存量全电脑/中低端台车 |

**铁证靠原话，不靠印象**：铁建重工 ZYS113/G 产品页写的是"爆破设计图**导入**电脑，
无需掌子面描点即可实现自动钻孔"；五新隧装宣传词里有"炮孔图生成"。**抓住"导入"与
"生成"的差别**——厂家做的是把人工画好的图导进去执行，布孔设计仍是设计院/技术员
手工完成，这一段厂家不碰，因为不是设备厂的事。同理，"存量设备没人做软件升级"
是空白，不是劣势。

**四条对外口径：**
1. **不说"我们做全自动凿岩"**——国外 Sandvik AutoMine Concept 已是无驾驶室、电池
   驱动、全自主双臂掘进台车（行走→就位→按图钻完→自行回去充电全程无人），Epiroc
   也已把 Deep Automation 扩到井下钻孔与锚杆。在自动化上正面比必然输。
2. **定位句**："设计到施工的数据决策层软件——不换设备，让现有台车会思考。"
3. **旧卖点"机械自动凿岩车 vs 全自动一键式"是自我弱化写法**，等于承认自己不是
   全自动、把对手的长处写进自己的定位，必须重写（使用者 2026-09 认可此判断）。
4. **护城河写在工程语义与规则上，不写在画面上**：爆破设计计算引擎、参数化布孔与
   7 种断面几何、坐标系变换与定位纠偏、DXF 图纸识别、钻孔执行表与施工日志闭环，
   加上设备所手里的真实数据（爆破后断面扫描点云 + 往期钻孔日志）。
   **"会三维建模/会渲染"不能当卖点**——通用大模型正持续把单点生成能力降级为
   基础能力（GPT-6 Astra 之后照片级 3D 建模变成可调用的一层能力，开源 3DGS 也已
   有可本地跑的方案），画面真实感会越来越不值钱，领域规则与数据闭环不会。
   被问"人家效果比你好"时，先区分尺子：那边是通用视觉真实感，这边是炮孔坐标/
   角度/装药量/可达性——不在同一把尺子上，输赢都不成立。

**"没测试过"怎么写**：算法层（布孔几何、爆破计算、DXF 识别、坐标变换、偏差分析）
可以自测且已做过 offscreen 全链路回归，缺的是现场标定。对外统一写
**"算法已实现并通过仿真验证，待现场数据标定"**——既不冒充实测，也别自贬成
"还没测试"（两个极端都在丢分）。

**用户自己怀疑项目时怎么做**（使用者会直接说"咱们已经落后了""总觉得怪怪的"）：
不要安慰、不要顺着说"确实落后"，按三步走——① 逐条查证他提出的对比对象
（官方产品页/官方文档原文，不信搜索摘要）；② 指出比错在哪里（哪个是执行、哪个是
设计；哪个是通用能力、哪个是领域能力）；③ 认账真正落后的部分，给出可执行的补法。
使用者要的是"找漏洞+纠偏"，不是安抚。**同时提醒：这类自我评估别实名发到公开内容里**，
会让评委和对手看到。

**下一步技术方向（不需真机的演示，性价比最高）**：
掌子面照片 → 三维重建 → 岩体结构面/迹线/平整度提取 → 反算优化爆破参数（增掏槽孔、
调辅助孔间距）→ 回灌布孔设计。依据：① 2026-05 MDPI 已发表该闭环框架（SfM+Poisson
重建、ISODATA 聚类结构面、最小代价路径取迹线、曲率算平整度）；② 传统 SfM 掌子面
重建慢是公认短板（实测 169/206 张照片耗时 22/25 小时，13 张约 14 分钟）——"慢"就是
产品化入口；③ 3DGS 在岩体表征上精度优于传统网格摄影测量（Postshot 实测相关性更高、
RMSE 更低）。
硬提醒：**隧道现场无网，重建只能在驻地/设计端做；照片重建得到的是相对尺度，工程用
必须靠标尺或已知断面尺寸标定绝对尺度**——这是工程与美术的分界线。

详见 `references/competitive-landscape-and-positioning.md`。

## 功能对标分析模式（铁建重工双项法）

当看到同类产品/竞品介绍时，按以下维度分析：

**⚠ 对标结果只用于内部研发和参赛/汇报材料，绝不放进产品界面。** 用户明确要求「咱们是做产品，不是介绍产品」——产品里不放"与XX对比/行业标杆"板块（2026-08 能耗板块已删掉铁建重工对比），数据基准用自身数据（如平均值）。另：**所有 UI 按钮必须绑定真实功能再交付**，用户会逐个点，未绑定事件的按钮会被批评（曾出现的"维保"死按钮）。

### 对标分析框架

```
铁建重工功能          → 我们现状    → 能不能加    → 优先级
─────────────────────────────────────────────────────
❶ 具体功能名           ✅/⚠️/❌    ✅/🔧/❌    ★★★★★
```

- **标注符号：** ✅ 已有 / ⚠️ 部分有 / ❌ 没有 / 🔧 硬件层
- **优先级：** ★★★★★ 核心 / ★★★★ 重要 / ★★★ 锦上添花
- **分工判断：** 软件能加的就加，硬件层面的标注 🔧 交给小伙伴厂

### 交给桌面端 Hermes 看图分析时——文档要写「全记录」

当用户说「把文档发给桌面端让它识图分析竞品」时，文档不要只写功能列表，要写**完整项目全记录**（用户明确要求过）：从参赛起点 → 系统开发过程 → 需求清单 → 竞品链接分析 → 待办 → 技术栈，全部一个文件（如 `台车项目全记录.txt`）。桌面端有视觉模型能看竞品截图，文档里要专门加一节「看图时关注的点」：
- 人家的炮孔设计界面/参数输入方式长啥样
- MWD 数据怎么展示（表格/图表/围岩叠加方式）
- 围岩识别怎么做（分区方式/热力图/地质剖面）
- 施工日志格式/签字流程/有没有我们漏掉的字段
- 还有啥我们没想到的功能

这样桌面端看图时能对照着判断「人家有啥我们缺啥」。

### 本会话对标铁建重工新台车结果

已对标的功能写入上方 v0.10 模块。硬件层（全景环视/臂架控制/碰撞预警/臂架姿态保持）标注为 🔧，交给小伙伴。

## 参考文件更新

### 需要小伙伴确认的外部接口

**2026-08-10 已与设备所（设备所负责人）对接确认的部分（对接清单.xlsx 已填）：**
- 台车机械设备参数12项（型号/钻臂数量/长度/行程/回转/俯仰/推进梁/钻杆/
  外形/基座/最小作业高度/凿岩机功率）：**所长均可提供**
- 控制系统类型：**嵌入式**；有二次开发接口/SDK 条件（需开发对接）
- 炮孔数据导入：**U盘/软件下发**；数据格式 **DXF/CSV/TXT**
- 通信协议：**Modbus/TCP/串口/CAN**
- 有 **GPS/惯导定位** + **角度/位置传感器**（台车能自动定位→定位骨架的前提）
- 爆破后断面扫描点云 + 以往施工记录/钻孔日志：**有**（数据闭环关键输入）
- 现有炮孔设计图（3-5份）：有；当前布孔=现场人工调整
- 隧道断面/衬砌/轴线/围岩等级/开挖方式、爆破效果/混凝土用量/围岩记录/
  出渣量：软件内用户自调
- 仍未明确（下次对接问）：工控机硬件配置、控制器型号/品牌、炮孔设计
  规范/标准、常用掏槽形式、围岩参数对照表、常用布孔模板

仍待确认项：
1. 台车控制系统读取的数据格式（JSON/CSV/DXF/专用格式？）
2. 坐标原点定义（隧道底部中心/拱顶中心/施工坐标系？）
3. 测量设备（全站仪/RTK）的串口通信协议和NMEA格式
4. 台车工控机的操作系统和可用的二次开发接口

### 坐标系转换
- 导出时：像素坐标 → 实际坐标（米），原点在断面中心
- 最终需对接施工坐标系（CGCS2000或独立施工坐标系）
- 在导出模块预留坐标系转换接口

## 超欠挖管控——数据需求清单

真正的超欠挖分析需要以下数据链，不是嘴上说说。逐条列出方便对接时问清楚：

### 设计数据（软件自己就有）
| 数据 | 来源 |
|:----|:-----|
| 隧道设计轮廓线坐标 | 设计图纸 |
| 各炮孔设计位置 (X, Y, Z) | 软件生成 |
| 炮孔设计深度/角度 | 软件生成 |
| 每循环设计开挖方量 | 轮廓×进尺 |

### 实际施工数据（需要台车/测量给）
| 数据 | 怎么来 | 用途 |
|:----|:-------|:-----|
| 实际钻孔坐标 | 全站仪复测或台车自动记录 | 对比设计孔位偏差 |
| 实际钻孔深度 | 台车推进传感器 | 看超打/少打 |
| 实际钻孔角度 | 台车钻臂角度传感器 | 看角度偏差 |
| 爆破后断面扫描 | 三维激光扫描仪或全站仪打点 | **核心数据**——扫出实际轮廓 |
| 实际出渣量 | 出渣车数×每车方量 | 估算实际开挖方量 |
| 喷射混凝土用量 | 每循环喷了多少方 | **直接反映超挖损失** |
| 超挖/欠挖值 | 扫描轮廓 - 设计轮廓 | 每个位置的偏差值 |

### 最有用的数据线
```
设计轮廓
  ├── 钻孔实际位置 ── 偏差分析 ── 下次调参数
  └── 爆破后实际轮廓 ── 超挖统计 ── 混凝土用量 ── 直接省钱数字
```

### 现阶段怎么写（不编数据）
> 「超欠挖管控需要以下数据支撑：钻孔坐标、钻孔深度、爆破后断面扫描、喷射混凝土用量等。待接入实际施工数据后，系统将基于以上数据建立超欠挖分析模型，逐步优化布孔参数，降低混凝土损耗。」

### 点云数据格式（对接雷达/激光扫描仪）
如果设备所引入了激光扫描仪，常见数据格式：
- `.las` / `.laz` — 行业标准点云格式
- `.ply` — 多边形格式，可含颜色
- `.xyz` — 纯坐标文本格式
- `.pcd` — Point Cloud Library 格式
- `.txt` — 最简单的坐标点文本

处理方式：用 numpy 加载坐标，pyqtgraph 的 GLViewWidget 直接渲染点云。

## 利益相关方对接——见面准备清单

当你需要跟设备所所长、厂方工程师、项目甲方等外部人员对接时，按以下结构准备：

### 关键对话策略：永远说「整套系统」

**不要只说自己做软件**，要强调你跟小伙伴的厂合起来做整套系统：

> 「我们跟XX（小伙伴名字）的厂合作，厂里做台车本体和控制系统，我来做上面的智能软件和数据分析。合在一起就是一整套智能台车方案。所长您这边能给到的支持——不管是台车参数、接口信息、还是现场数据——都能让我们把这个系统做扎实。」

这个说法让对方觉得你们是完整的方案，不是来卖半个东西的。

### 准备材料格式偏好

见面准备材料准备两份：
- **备忘录.txt** — 完整版话术，含：对方要什么 → 你能展示什么 → 确认事项 → 常见问题备答 → 跟进模板
- **数据清单.xlsx** — 按优先级分色的表格，核心项（绿色）、重要项（黄色）、辅助项（灰色），加Sheet记录"数据用途对照"和"核心问题"

用户偏好 Excel 数据清单（比纯 txt 看着方便），但正式话术用 txt 更灵活。

生成数据清单.xlsx 时按以下结构组织 Sheet：
| Sheet | 内容 |
|:------|:-----|
| 所需数据总表 | 按大类分节（台车参数/控制系统/炮孔资料/施工数据/隧道参数/自己准备），每项标优先级（核心/重要/辅助），用绿/黄/灰底色区分 |
| 见所长核心问题 | 5个必问问题，按优先级排列 |
| 数据用途对照 | 拿什么数据→乖乖能干什么，给对接人看价值 |

颜色方案：
- 核心项：#E2EFDA（浅绿底）
- 重要项：#FFF2CC（浅黄底）
- 辅助项：#F2F2F2（浅灰底）
- 分类标题：#4472C4（深蓝底白字）

### 你要问对方要什么
- 台车具体参数和型号
- 控制系统类型（Windows工控机？PLC？嵌入式？）
- 有没有二次开发接口/SDK
- 现在的炮孔数据导入方式（手动？U盘？软件？）
- 支持什么数据格式
- 以前的炮孔设计图、施工记录（能要到最好）
- 核心痛点：现在哪一步最费时？超挖严重吗？工人操作有啥困难？

### 你能给对方展示什么
- 一两句话说清楚你们做的：
  「我们在做全电脑凿岩台车的智能化升级——从传感感知、自动控制到炮孔设计、数据优化，整套系统都做。核心理念是设计到施工的数据闭环」
- 你的PyQt5原型（炮孔设计界面 + 3D模拟）
- 你们能解决的具体痛点（设计靠手动→自动布孔、超挖浪费→数据优化、施工记录靠手写→自动日志）

### 需要对方确认的事
- **最核心**：软件怎么跟台车对接？（装工控机上？外接笔记本？有没有指令接口？）
- 合作方式：配套出售还是单独报价？时间节点？
- 能否安排现场看台车？给一份技术手册？

### 常见问题怎么接
| 问题 | 回答要点 |
|:----|:---------|
| 跟市面现有方案有什么不同？ | 我们是设计→下发→反馈→优化闭环，打通设计施工断档 |
| 精度怎么样？ | 现阶段不编数据，等实际对接测试后给实测结果 |
| 优势在哪？ | 软件赋能，不改机械结构，深度定制化 |
| 什么时候出成品？ | 已有原型，下一步做对接测试，看接口复杂度 |

### 见面后24小时内
给对接人发一条跟进微信，总结谈话要点，提下一步需要的资料和后续安排。
