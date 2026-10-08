# 航天花板 ViewCube 化（v0.10.3，2026-08-13）

用户反馈链路：① 主视图旋转航天花板不跟随 → ② "正面为什么不是掌子面的正面图，
跟认知不一样" → 参考 Revit ViewCube 重做。全部内嵌 `drill_design_v09.py`。

## 需求本质（对齐 Revit ViewCube）

ViewCube 不是"模型的朝向指示器"而是"**世界/工程方向指示器**"：
- 标签 = 固定在世界方向的工程名（Revit 用 N/S/E/W/Up/Down）
- 立方体随相机同步旋转，任何时候都知道自己从哪个方向看模型
- 点面/点角 → 视图切到该方向正式视图（正视图/等轴测）

我们的工程方向（点云场景坐标 x=横向右正、y=高程上正、z=深度/掌子面法线）：

| 面 | 方向 | 跳转视角(az, el) |
|:--|:----|:-----|
| 掌子面 | +Z（打孔方向） | (0, 89) |
| 洞口 | -Z（台车来路） | (0, -89) |
| 拱顶 | +Y（高程上） | (90, 0) |
| 底板 | -Y | (270, 0) |
| 右侧墙 | +X | (0, 0) |
| 左侧墙 | -X | (180, 0) |

顶点索引不变（0~7），只重排 faces 的顶点组与标签：
```python
self.faces = [
    ([4,5,6,7], '#E74C3C', '掌子面', (0, 89)),     # +Z
    ([0,1,2,3], '#C0392B', '洞口',   (0, -89)),    # -Z
    ([2,6,7,3], '#27AE60', '拱顶',   (90, 0)),     # +Y
    ([0,1,5,4], '#1E8449', '底板',   (270, 0)),    # -Y
    ([1,5,6,2], '#5BA3EC', '右侧墙', (0, 0)),      # +X
    ([0,4,7,3], '#4A90D9', '左侧墙', (180, 0)),    # -X
]
```

## 关键技术决策（两次推导失败后的正解）

### 1. 投影用主视图 viewMatrix，不自己维护旋转公式

第一版手工旋转公式"绕Y(az)+绕X(el)"与 pyqtgraph 相机不一致 → 角度同步了
朝向仍错位。**别手工推 3D 旋转——直接复用主视图的 viewMatrix**：

```python
def _project(self, pt):
    w = self.width() / 2
    h = self.height() / 2
    scale = min(w, h) * 0.35
    if self.main_view is not None:
        v = self.main_view.viewMatrix().map(QVector3D(pt[0], pt[1], pt[2]))
        return int(w + v.x() * scale), int(h - v.y() * scale), v.z()
    return int(w + pt[0] * scale), int(h - pt[1] * scale), pt[2]
```

- `viewMatrix()` 是 GLViewWidget 的公开方法，世界→相机坐标
- z（相机深度）用于画家算法：**z 越大越靠近观察者**（OpenGL 负近端正远）
- front 面 = 投影后 z 最大的面（高亮用）

### 2. pyqtgraph 相机约定（offscreen 实测确认）

`cameraPosition()` 直接测量（distance=10, center=原点）：
```
az=0   el=0  → (10, 0, 0)   相机在 +X
az=90  el=0  → (0, 10, 0)   +Y
az=180 el=0  → (-10, 0, 0)  -X
az=270 el=0  → (0, -10, 0)  -Y
az=0   el=90 → (0, 0, 10)   +Z（注意：el 正方向让相机到 +Z，不是 -Z）
```
即：azimuth 绕 Z 轴，elevation 绕 Y 轴（负方向）。等价于"先绕Y(-el)再绕Z(az)"
（推导顺序与直觉相反，务必实测确认，别信直觉）。

### 3. el=±90 隐藏坑：up 与视线平行 → lookAt 退化

相机在 +Z 正上方时 up=(0,0,1) 与视线 (0,0,-1) 平行 → lookAt 零向量 →
viewMatrix 病态。**跳转表一律用 ±89**（视觉几乎无差，避免退化）。

### 4. 反向同步接线（第一轮修复）

`sync_from_main()` 定义了但无人调用 = 航天花板不动。接线方式：
```python
def eventFilter(self, obj, ev):
    if obj is self.gl:
        if ev.type() == QEvent.Resize:
            self._reposition_gizmo()
        elif ev.type() in (QEvent.MouseMove, QEvent.MouseButtonRelease):
            if ev.type() == QEvent.MouseButtonRelease or (ev.buttons() & Qt.LeftButton):
                self._sync_gizmo_from_gl()   # 读 opts → gizmo.sync_from_main()

def _sync_gizmo_from_gl(self):
    opts = self.gl.opts
    self.gizmo.sync_from_main(opts.get('azimuth', 45), opts.get('elevation', 25))
```
MouseMove 滞后一个事件但拖拽中视觉无感；MouseButtonRelease 兜底。

### 5. 点击命中 = "离标签最近"，不是"点在面多边形内"

- 第一版：多边形 containsPoint —— 斜视角下背面多边形与正面重叠，点"洞口"
  跳成"拱顶"
- 正解：paintEvent 缓存每个面的**标签中心点** (label, cx, cy, avg_z)；
  release 时 `min(hypot(px-cx, py-cy))`，≤42px 即命中
- 好处：所见即所得（点哪个字跳哪个方向），半透明背面标签也能点
- 点击/拖拽区分：press 记录起点，release 时 manhattanLength < 6px 视为点击

### 6. 当前正对面高亮（Revit 式）

front_label = z 最大的面：alpha 150 vs 90、边框 2px 白亮 vs 1px 暗、
标签字号 8pt vs 7pt。

## 验证方法（offscreen）

- **front 判定**：对 6 个视角 (az,el) 逐一 setCameraPosition，用 `_project` 算
  各面中心 z，断言 z 最大面 = 期望标签
- **点击跳转**：`g.grab()` 强制渲染填充 `_hit_polys`（update() 在 offscreen 不
  触发 paintEvent！），取标签中心构造 QMouseEvent press+release → 断言
  `gl.opts['azimuth'/'elevation']` 到达目标
- **拖拽回归**：press(30,30)+move(50,50)+release → 断言主视图 azimuth 变化
- **全 Tab 回归**：9Tab 切换 + 点云三模式 + Tab1 布孔 + 施工日志

## 踩坑清单（本会话实证）

1. 手工旋转公式与 pyqtgraph 相机不一致 → 改用 viewMatrix（根除）
2. offscreen 下 `update()` 不触发 paintEvent，`_hit_polys` 是空的 → 先 `grab()`
3. el=±90 lookAt 退化 → ±89
4. 多边形命中跳错面 → 标签距离命中
5. 断言想当然：记录后对比显示"无变"是正确行为；范围内参数不动是正确行为；
   指令记录区块在 cmd_log 空时不渲染（分阶段断言）
