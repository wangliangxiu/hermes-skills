# 轴向导航天花板——QPainter 六面体实现

**2026-07-30 更新：从 GLViewWidget 方案改为纯 QPainter 方案。**

原方案使用缩小的 `GLViewWidget` 作为叠加层渲染 RGB 三色轴 + 点阵立方体。用户反馈点阵不像立方体，要求做成真六面体带颜色标签（像 Revit 的 View Cube）。改用纯 QPainter 绘制后，形状更准确、文字标签清晰、无 OpenGL 上下文冲突。

## 类

`GizmoWidget(QWidget)` — 位于 `drill_design_v09.py`。

## 构造参数

- `main_view`: 关联的主 GLViewWidget，拖拽时调用 `main_view.orbit(dx, dy)`
- `azimuth`: 初始 45°，方位角
- `elevation`: 初始 25°，俯仰角
- 固定尺寸由 `_add_gizmo()` 自适应计算：`gs = max(60, min(gl_width, gl_height) // 3)`

## 六面体定义

8 个顶点（边长 s=1.0，原点居中）：
```
背面: (-1,-1,-1), (1,-1,-1), (1,1,-1), (-1,1,-1)
正面: (-1,-1,1),  (1,-1,1),  (1,1,1),  (-1,1,1)
```

6 个面，每个面由 [顶点索引, 颜色, 中文标签] 构成：
```
[0,1,2,3], '#4A90D9', '背面'   — Back (-Z) 深蓝
[4,5,6,7], '#5BA3EC', '正面'   — Front (+Z) 亮蓝
[1,5,6,2], '#E74C3C', '右面'   — Right (+X) 红
[0,4,7,3], '#C0392B', '左面'   — Left (-X) 暗红
[2,6,7,3], '#27AE60', '顶面'   — Top (+Y) 绿
[0,1,5,4], '#1E8449', '底面'   — Bottom (-Y) 暗绿
```

## 3D→2D 投影

```python
def _project(self, pt):
    az = math.radians(self.azimuth)
    el = math.radians(self.elevation)
    x, y, z = pt
    x1 = x * math.cos(az) + z * math.sin(az)
    z1 = -x * math.sin(az) + z * math.cos(az)
    y2 = y * math.cos(el) - z1 * math.sin(el)
    w, h = self.width()/2, self.height()/2
    scale = min(w, h) * 0.8
    return int(w + x1*scale), int(h - y2*scale), z2  # (sx, sy, z_depth_for_sorting)
```

## paintEvent 流程

1. 投影全部 8 个顶点 → `proj`
2. 对每个面计算 4 个顶点的平均 Z 深度
3. 按 Z 深度升序排序（画家算法，远→近）
4. 绘制面：`QPolygonF` + `QBrush`（颜色半透明 200）
5. 在面中心绘制中文标签（`drawText`, 微软雅黑 7pt, 白色）
6. 绘制 12 条棱边线（`QPen` 白色半透明 60）

## 交互

- `mousePressEvent`: 记录 `drag_start`，设 `dragging=True`
- `mouseMoveEvent`:
  - 计算 `dx = ev.x() - drag_start.x()`, `dy = ev.y() - drag_start.y()`
  - 更新 `azimuth = (azimuth - dx*0.5) % 360`
  - 更新 `elevation = max(-89, min(89, elevation + dy*0.5))`
  - 调用 `main_view.orbit(-dx*0.5, dy*0.5)`
  - 调用 `self.update()`
- `mouseReleaseEvent`: 设 `dragging=False`

## 主场景反向同步

```python
def sync_from_main(self, az, el):
    self.azimuth = az % 360
    self.elevation = max(-89, min(89, el))
    self.update()
```

## 背景透明

- `setAttribute(Qt.WA_TranslucentBackground)`
- `setStyleSheet('background: transparent')`
- paintEvent 首行：`p.fillRect(0, 0, w, h, QColor(0, 0, 0, 0))`

## 自适应定位

```python
gs = max(60, min(self.gl.width(), self.gl.height()) // 3)
self.gizmo = GizmoWidget(self.gl)
self.gizmo.main_view = self.gl
self.gizmo.setFixedSize(gs, gs)
self.gizmo.move(self.gl.width() - gs - 15, 15)
```

窗口 resize 时重新计算尺寸和位置。

## 依赖

- `PyQt5.QtWidgets.QWidget`（基类）
- `PyQt5.QtGui.QPainter`（绘制）
- 不需要 `pyqtgraph.opengl` 或 `PyOpenGL`
