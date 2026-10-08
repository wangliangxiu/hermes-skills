# v0.8 钻进参数监控与报警子系统 实现笔记

## 核心数据结构

### 钻进参数定义
```python
self.dv = {}
items = [
    ('bit_x', '钎头X', 0.0, ('m', -10, 10)),
    ('bit_y', '钎头Y', 0.0, ('m', -10, 10)),
    ('bit_z', '钎头Z', 0.0, ('m', -10, 10)),
    ('target_dep', '需钻深', 3.0, ('m', 0.5, 6)),
    ('feed_spd', '推进速度', 1.2, ('m/min', 0, 5)),
    ('feed_prs', '推进压力', 80, ('bar', 0, 200)),
    ('impact_prs', '冲击压力', 150, ('bar', 0, 300)),
    ('rotary_prs', '回转压力', 60, ('bar', 0, 200)),
    ('collar_spd', '领孔速度', 0.5, ('m/min', 0, 2)),
    ('water_flow', '水流量', 30, ('L/min', 0, 100)),
]
# 每个item存为 {'label': QLabel, 'val': float, 'min': float, 'max': float}
```

### 报警阈值定义
```python
self.av = {}
alarms = [
    ('feed_spd', '推进速度', 0, 3.0),       # (key, 显示名, 下限, 上限)
    ('feed_prs', '推进压力', 0, 160),
    ('impact_prs', '冲击压力', 0, 250),
    ('rotary_prs', '回转压力', 0, 150),
    ('collar_spd', '领孔速度', 0, 1.5),
    ('water_flow', '水流量', 10, 80),
]
# 每个item存为 {'lo': QDoubleSpinBox, 'hi': QDoubleSpinBox, 'st': QLabel(状态文本)}
```

## 模拟数据更新逻辑

```python
def _sim_update():
    for key, v in self.dv.items():
        # 随机波动：当前值的±10%范围内
        delta = (random.random() - 0.5) * v['val'] * 0.2 if v['val'] != 0 else (random.random()-0.5)*0.5
        v['val'] = max(v['min'], min(v['max'], v['val'] + delta))
        v['label'].setText(f"{v['val']:.1f}")
    self._check_alarms()
```

## 报警检测逻辑

```python
def _check_alarms():
    alarm = False
    for key, av in self.av.items():
        lo = av['lo'].value()
        hi = av['hi'].value()
        dv = self.dv.get(key)
        if dv:
            val = dv['val']
            if val < lo or val > hi:
                av['st'].setText('⚠报警!')
                av['st'].setStyleSheet('color:#FF4444;font-weight:bold')
                alarm = True
            else:
                av['st'].setText('正常 ✓')
                av['st'].setStyleSheet('color:#4CAF50;font-weight:bold')
    # 报警时闪烁底部指示灯
    if alarm:
        self.alarm_light.setStyleSheet('background:#FF4444')
        QTimer.singleShot(500, lambda: self.alarm_light.setStyleSheet('background:#2B579A'))
    else:
        self.alarm_light.setStyleSheet('background:#4CAF50')
```

## 纯QPainter等轴3D投影（替代matplotlib）

当matplotlib安装失败或DLL冲突时使用：

```python
def proj(x, y, z):
    """等轴投影：先绕X轴转25°，再绕Y轴转60°"""
    rx = x
    ry = y * math.cos(math.radians(25)) - z * math.sin(math.radians(25))
    rz = y * math.sin(math.radians(25)) + z * math.cos(math.radians(25))
    px = cx + (rx * math.cos(math.radians(60)) - rz * math.sin(math.radians(60))) * scale
    py = cy + (rx * math.sin(math.radians(60)) + rz * math.cos(math.radians(60))) * scale
    return int(px), int(py)
```

**限制**：纯QPainter 3D不支持鼠标交互旋转，只展示固定视角。

## 布局结构（v0.8最终布局）

```
┌──────────┬──────────────┬──────────────────────┐
│ 布孔参数  │  2D断面图    │  钻进参数监控        │
│ (左200px) │  (中  flex)  │  + 报警阈值           │
│          │              │  (右  flex)          │
│          ├──────────────┤                      │
│          │  简易3D视图   │                      │
│          │  (中  flex)  │                      │
└──────────┴──────────────┴──────────────────────┘
```

## Hermes Desktop 端口占用解决

启动dashboard时提示 `9120~9140 all ports claimed`：

1. `netstat -ano | findstr :9120` 找到占用PID
2. `taskkill /F /PID <PID>` 杀掉进程
3. 还不行就加上 `netstat -ano | findstr :912` 找9121~9140
