# 台车定位与纠偏骨架（v0.10）实现细节

2026-08-10 会话落地。全部内嵌 `drill_design_v09.py`（启动_v09.bat 主程序），
用户明确要求不拆模块不开新窗。

## 数据结构

```python
RIG_PARAMS = {
    'boom_len': 6.0,          # 钻臂长度 m（固定占位，待设备所实测替换）
    'feed_len': 4.5,          # 推进梁长度 m
    'swing_deg': 40.0,        # 水平回转范围 ±deg
    'lift_deg': 45.0,         # 俯仰范围 ±deg
    'base_x': 2.5,            # 钻臂基座 相对台车定位点 X向距离 m（向掌子面为正）
    'base_y': 0.9,            # 钻臂基座 横向偏移 m（右臂）
    'base_z': 1.8,            # 钻臂基座 距轨面高度 m
    'D_min': 4.0,             # 台车距掌子面最小距离 m
    'D_max': 10.0,            # 台车距掌子面最大距离 m
}
POS_TOLERANCE = {'dy_cm': 5.0, 'dz_cm': 5.0, 'yaw_deg': 1.0}
```

## 核心函数

### design_to_rig —— 掌子面系 → 台车系（纠偏补偿）
```python
def design_to_rig(y, z, dy, dz, yaw_deg):
    a = math.radians(yaw_deg)
    ca, sa = math.cos(a), math.sin(a)
    ey, ez = y - dy, z - dz
    return round(ey * ca + ez * sa, 3), round(-ey * sa + ez * ca, 3)
```
单测对照：无偏移不变 (1,2)→(1,2)；dy=0.5 整体平移 (1,2)→(0.5,2)；
yaw=90° 旋转 (1,0)→(0,-1)。

### check_reachability —— 钻臂可达性
```python
mx = rp['boom_len'] + rp['feed_len']
for h in holes_rig:
    dx = D
    dy = h['y'] - rp['base_y']
    dz = h['z'] - rp['base_z']
    dist = math.sqrt(dx*dx + dy*dy + dz*dz)
    az = math.degrees(math.atan2(dy, dx))   # 水平回转角
    el = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))  # 俯仰角
    note = ''
    if dist > mx: note = '超臂展'
    elif abs(az) > rp['swing_deg']: note = '超回转'
    elif abs(el) > rp['lift_deg']: note = '超俯仰'
```
可达范围圆（画布用）：`cover_r = sqrt(mx² - (D - base_x)²)`，圆心=钻臂基座
(base_y, base_z)。D - base_x ≥ mx 时无覆盖。

### gen_holes_realistic —— 真实布孔
- 直眼掏槽：中心空孔 `{'y':0,'z':0,'empty':True}` + 8孔一圈 r=0.28m
- 楔形掏槽：两排（row=±1）×3孔（k=-1,0,1），y=k×0.45, z=row×0.30
- 辅助孔梅花形：孔距0.8/排距0.8，隔行偏移0.4，裁剪 0.55<dist<r-0.4
- 周边孔：n=max(8, round(2πr/0.65))，从拱顶顺时针
- 底板孔：**贴弧线** `zz=-sqrt(max(0, r²-yy²))`，y 范围 span-1.2（两侧各留0.6m）
  ——圆断面下 z=-r 在 y≠0 会越界（8个孔越界的实测教训）

## UI 集成

### PositioningPanel（Tab9）
- 输入：dy(cm)/dz(cm)/yaw(°)/D(m) 四个 QDoubleSpinBox + 掏槽形式 QComboBox
- 自动重算：`sb.valueChanged.connect(self._run)` + `cut.currentIndexChanged.connect(self._run)`
  （注意：信号要在 setValue 之后连接，否则初始化时会提前触发）
- `_run()` 流程：compute_positioning → gen_holes_realistic（用 self.span+cut，
  不依赖主窗口 design_holes，保证面板独立可控）→ design_to_rig 补偿 →
  check_reachability → rig_canvas.set_data → 结果文本
- 结果文本：偏差明细（✓/⚠ 超限 + 移车提示）+ 距离检查 + 孔数统计 +
  超范围孔列表（前12条）+ 钻臂参数占位说明

### RigHoleCanvas（台车系布孔图）
- 掌子面轮廓：圆心=掌子面中心在台车系坐标 `design_to_rig(0,0,dy,dz,yaw)`
- 台车基准点(0,0)黄色 + 偏差线（台车基准点→掌子面中心）
- 钻臂基座青色 + 可达范围圆虚线
- 孔：可达=实心圆+中心点，不可达=红色×
- 底部统计：总/可达/超范围

### MainWindow 集成
- `self.pos_panel = PositioningPanel(get_holes=self._get_design_holes)` 参数保留
  但 _run 已改为独立生成孔（get_holes 不强制）
- Tab1 布孔参数区加"掏槽形式"下拉 `self.cut_type`
- `_gen()`：`holes = gen_holes_realistic(span, depth, cut)` →
  `self.design_holes = holes` → 画布 → 同步定位面板
  （set_span + cut.setCurrentText + 手动 _run）
- 画布兼容：HoleCanvas/Simple3DView 读 `hh.get('y', hh.get('x', 0))`、
  `hh.get('z', hh.get('y', 0))`；`empty` 孔画空心圆（2D）/空心端面（3D）

## offscreen 验证脚本骨架

```python
QT_QPA_PLATFORM=offscreen python -c "
import sys
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
import drill_design_v09 as dd
w = dd.MainWindow(); w.show()
assert w.tabs.count() == 9
assert len(w.design_holes) > 0
w.span.setValue(8.0); w.cut_type.setCurrentText('楔形'); w._gen()   # Tab1→定位面板联动
w.pos_panel.dy.setValue(30.0)          # 自动重算
txt = w.pos_panel.result.toPlainText()
assert '台车需向左移' in txt
for i in range(w.tabs.count()): w.tabs.setCurrentIndex(i)  # 全Tab切换不崩
print('PASS')
"
```

## 实测结果（本会话）
- 6m直眼77孔 / 6m楔形74孔 / 8m直眼119孔 / 8m楔形116孔，越界0
- 8m直眼：自动标出4孔"超臂展"（可达性真实工作）
- dy=30cm→"台车需向左移30.0"；dz=8cm→"台车需下降8.0"；yaw=2°→"需逆时针转向2.0"

## 下一步（未做）
- 3D 视图加台车简笔画（车体+钻臂示意）
- 等所长实测 RIG_PARAMS 替换占位值
- 真机惯导坐标流接入替代手动输入
- 断面升级拱形（和 blast_design 一致，底板变水平线）
