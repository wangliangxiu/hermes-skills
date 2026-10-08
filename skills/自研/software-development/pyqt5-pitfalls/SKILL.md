---
name: pyqt5-pitfalls
description: 写/改PyQt5界面（台车系统、政务工作台）前先加载，防崩溃防坑。触发词：PyQt5报错、界面闪退、最大化卡退。
---

# PyQt5 开发避坑清单

适用：所有 PyQt5 桌面项目（凿岩台车智能炮孔系统、政务全媒体工作台等）。
写代码前扫一遍第一节，写完用第四节方法验证。

## 一、致命坑（会导致程序崩溃/闪退，最优先）

### 1. 实例属性名不能撞 QWidget/QObject 方法名
```python
# ❌ 会崩：self.height 遮蔽 QWidget.height() 方法
self.height = 5.0

# ✅ 改名
self.tunnel_height = 5.0
```
- Qt 内部调用 height() 时拿到浮点数/控件对象 → 直接崩溃（进程退出）
- **必须避开的属性名**：`width` `height` `size` `pos` `rect` `geometry` `x` `y` `parent` `font` `layout` `children` 等 QWidget/QObject 方法名
- 排查：`grep -n "self\.\(height\|width\|size\|pos\|rect\|geometry\)" *.py`
- 真实案例：爆破设计Tab `self.height = 5.0` 导致窗口一显示就崩（2026-08）

### 2. QPainter 绘图坐标传 float 会崩
```python
# ❌ 会崩：r 是 float
p.drawLine(cx - r - 10, cy, cx + r + 10, cy)

# ✅ 全部 int()
p.drawLine(int(cx - r - 10), cy, int(cx + r + 10), cy)
```
- 适用：`drawLine` `drawEllipse` `drawRect` `drawText` `fillRect` 等所有 QPainter 方法
- 凡坐标表达式里有除法/乘法产生 float 的，一律 int() 包住

### 3. 崩溃的伪装现象（误导排查）
- offscreen 下 show() 崩溃 = `exit 127` + **无任何输出**（stdout 缓冲丢失）
- 看到 127+无输出 = **代码崩溃**，不是命令/环境问题，不要往环境方向排查

## 二、API 使用坑（报错/样式不对）

### 4. fixedWidth/fixedHeight 不能当构造参数
```python
# ❌ TypeError: 'fixedWidth' is an unknown keyword argument
QLabel('text', fixedWidth=43)

# ✅ 拆两行
lbl = QLabel('text')
lbl.setFixedWidth(43)
```
- 同样适用于：`QSpinBox` `QDoubleSpinBox` `QComboBox` `QCheckBox` `QSlider`

### 5. Import 遗漏
- 新加 Tab/控件时确认 import 覆盖：`QComboBox, QCheckBox, QSlider, QTextEdit, QFileDialog, QGridLayout`
- 漏 import 的报错特征：`NameError: name 'XXX' is not defined`

### 6. 布局观感（用户高频反馈点）
- 参数面板一列太长 → 用 QGridLayout 或 HBox 排两列
- 表格行少 → 压缩行高 `verticalHeader().setDefaultSectionSize(28)` + 限高 `setMaximumHeight(140)`
- 界面空白多 → 检查 stretch 因子分配；窗口拉伸时用 `ll.addLayout(row1, 2)` 让区域跟着涨
- 写 GUI 前先画布局草图：哪块放哪、空白怎么处理，一次到位，避免返工

## 三、Windows 环境坑

### 7. 中文用户名 DLL 加载失败（exit code 3221226505）
- 删除 `ctypes.windll.shcore.SetProcessDpiAwareness(2)` 这行
- 或回退 tkinter 平替

### 8. 启动脚本
```bat
@echo off
chcp 65001 >nul
"D:\python\python.exe" "%~dp0your_script.py"
pause
```

## 四、验证与排查方法论

### offscreen 标准验证（每次改完 GUI 必做，别让用户双击试错）
```bash
set QT_QPA_PLATFORM=offscreen && python -c "
from PyQt5.QtWidgets import QApplication
app = QApplication([])
from mymodule import MyWidget
w = MyWidget()
print('OK')
"
```
- **只实例化，不 show()**（offscreen 下 show 可能崩，不代表真实运行）
- 验证清单：py_compile 通过 → import 无报错 → MainWindow 创建成功 → 新 Tab 能实例化
- 临时验证脚本要 `sys.path.insert(0, 项目目录)`，否则 ModuleNotFoundError

### 崩溃二分定位法（show 就崩时）
1. offscreen 下 show() 复现（127+无输出=崩）
2. **用继承子类覆盖 paintEvent** 逐步加减内容（实例属性 monkey-patch 对 paintEvent 不生效，必须类级继承）
3. 从"只画背景"开始，逐段加回 网格→轮廓→炮孔→图例，找到触发段
4. 锁定后检查：float 坐标？遮蔽属性？越界绘制？

## 五、写代码前检查清单
- [ ] 实例属性名没撞 Qt 方法名（height/width/size/pos/rect/geometry...）
- [ ] 所有 QPainter 坐标 int()
- [ ] fixedWidth 都拆成 setFixedWidth
- [ ] import 覆盖新控件
- [ ] 布局草图先画：无大面积空白、表格压缩、参数两列
- [ ] 改完 offscreen 标准验证通过
