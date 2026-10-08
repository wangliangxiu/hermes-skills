# 钻进参数监控 + 报警子系统（v0.8参考实现）

## 架构

```
DrillMonitor(QWidget)
  ├── 钻进参数显示区（10个参数，QLabel显示当前值）
  ├── 报警阈值设置区（6个参数，QSpinBox设下限/上限 + QLabel显示状态）
  ├── 模拟控制按钮（▶开始/⏸暂停 + 重置）
  └── 报警指示灯（6px高的QLabel光条，红/绿切换闪烁）
```

## 参数列表

| 参数Key | 显示名 | 默认值 | 单位 | 范围 |
|:---|:---|:---|:---|:---|
| bit_x | 钎头X | 0 | m | ±10 |
| bit_y | 钎头Y | 0 | m | ±10 |
| bit_z | 钎头Z | 0 | m | ±10 |
| target_dep | 需钻深 | 3.0 | m | 0.5~6 |
| feed_spd | 推进速度 | 1.2 | m/min | 0~5 |
| feed_prs | 推进压力 | 80 | bar | 0~200 |
| impact_prs | 冲击压力 | 150 | bar | 0~300 |
| rotary_prs | 回转压力 | 60 | bar | 0~200 |
| collar_spd | 领孔速度 | 0.5 | m/min | 0~2 |
| water_flow | 水流量 | 30 | L/min | 0~100 |

## 报警配置（默认阈值）

| 参数 | 下限 | 上限 |
|:---|:---|:---|
| 推进速度 | 0 | 3.0 |
| 推进压力 | 0 | 160 |
| 冲击压力 | 0 | 250 |
| 回转压力 | 0 | 150 |
| 领孔速度 | 0 | 1.5 |
| 水流量 | 10 | 80 |

## 关键实现

### 数据结构
```python
self.dv = {
    'feed_spd': {'label': QLabel, 'val': 1.2, 'min': 0, 'max': 5},
    ...
}
self.av = {
    'feed_spd': {'lo': QDoubleSpinBox, 'hi': QDoubleSpinBox, 'st': QLabel},
    ...
}
```

### 报警检查逻辑
```python
for k, av in self.av.items():
    lo = av['lo'].value(); hi = av['hi'].value()
    dv = self.dv.get(k)
    if dv:
        val = dv['val']
        if val < lo or val > hi:
            av['st'].setText('⚠报警!')
            av['st'].setStyleSheet('color:#FF4444;font-weight:bold')
            alarm = True
        else:
            av['st'].setText('正常 ✓')
            av['st'].setStyleSheet('color:#4CAF50;font-weight:bold')
```

### 报警指示灯闪烁效果
```python
# 报警时红色，500ms后恢复蓝色
if alarm:
    self.alarm_light.setStyleSheet('background:#FF4444')
    QTimer.singleShot(500, lambda: self.alarm_light.setStyleSheet('background:#2B579A'))
else:
    self.alarm_light.setStyleSheet('background:#4CAF50')
```

### 模拟数据更新（QTimer，1秒间隔）
```python
def _sim(self):
    for k, v in self.dv.items():
        delta = (random.random()-0.5) * v['val'] * 0.2 if v['val'] != 0 else (random.random()-0.5)*0.5
        v['val'] = max(v['min'], min(v['max'], v['val'] + delta))
        v['label'].setText(f"{v['val']:.1f}")
    self._check()
```

## 注意
- 报警阈值由用户在界面上设置，不写死
- 实际部署时，QTimer模拟改为串口/总线读取真实传感器数据
- 报警灯闪烁用`QTimer.singleShot`实现，不要用sleep
