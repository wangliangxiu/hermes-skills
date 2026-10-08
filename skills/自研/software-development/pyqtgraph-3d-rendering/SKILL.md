---
name: pyqtgraph-3d-rendering
description: pyqtgraph 3D可视化避坑（点云/实体表面/mesh不渲染）。触发词：pyqtgraph点云。
---

# pyqtgraph 3D 渲染避坑

适用：任何用 pyqtgraph `GLViewWidget` 做 3D 可视化的 PyQt5 项目
（凿岩台车点云分析、实体表面、轴导航立方体等）。
与 `pyqt5-pitfalls` 互补（那是通用 2D/Qt 坑，这是 3D 渲染专属）。

## 一、shader 选择（mesh 不渲染的头号原因）

- **pyqtgraph 内置 shader 名**：`None`、`'balloon'`、`'viewNormalColor'`、`'normalColor'`、`'shaded'`、`'edgeHilight'`（**注意拼写，少个 g**）、`'heightColor'`
- 名字拼错 → `getShaderProgram` 直接 KeyError → paint 阶段异常被 Qt 吞 → **mesh 整个不渲染，画面只剩点/轮廓**
- 集成显卡环境：`'shaded'` 最稳（被实测验证）；`'heightColor'`、`None`、`'edgeHilight'` 可能不渲染——**先用 shaded 跑通，再优化**
- 验证 shader 存在：`'shaded' in pyqtgraph.opengl.shaders.ShaderProgram.names`

## 二、shaded 旋转不变暗技巧（要起伏又要颜色恒定）

shaded 的明暗 = 面法线·固定光源 `(1,-1,-1)/√3`，旋转时夹角变化→变暗。
把**所有法线强制指向光源方向** → 夹角恒0 → 亮度恒满：

```python
nrm = np.array([1.0, -1.0, -1.0]) / np.sqrt(3.0)
normals = np.tile(nrm, (len(vertices), 1))
mesh_data = pg.opengl.MeshData(vertexes=vertices, faces=faces, faceColors=face_colors)
mesh_data._vertexNormals = normals   # 覆盖内部法线（smooth=True 时使用）
mesh_item = GLMeshItem(meshdata=mesh_data, smooth=True, shader='shaded',
                       glOptions='opaque', drawEdges=True, edgeColor=(0,0,0,0.4))
```

- **MeshData 构造参数只有**：`vertexes, faces, edges, vertexColors, faceColors`（传 `normals=` 会 TypeError）
- 覆盖法线用内部属性 `_vertexNormals`（`vertexNormals()` 返回它时非 None 直接返回）
- 看出起伏：faceColors 按高度做 colormap（蓝→绿→红）；褶皱结构：`drawEdges=True` 画网格线

## 三、颜色在白色背景下发白

- **GLScatterPlotItem 默认 translucent**（混合渲染）：半透明色在浅色背景下变淡发白
- 修复：`glOptions='opaque'` + 颜色 alpha=1.0——切深/白背景颜色恒定
- 适用于点云、炮孔、轮廓线所有 scatter 点

## 四、透明背景 widget 叠在 GLViewWidget 上不显示

- `Qt.WA_TranslucentBackground` 子 widget 在 OpenGL 父视图上可能合成失败
- 修复：paintEvent 里画**半透明深色面板**（`QColor(15,20,35,190)` + 边框）再画内容，保证可见

## 五、3D 投影 scale 过大 → 物体超出面板

- 边长2的立方体旋转后投影范围约 ±2.2，`scale = min(w,h)*0.8` 会画出面板
- 用 `scale = min(w,h)*0.35` 占面板中心约75%
- 验证：实例化后 `_project` 所有顶点，确认 x/y 都在 [0, size] 内

## 六、监听 GL 视图 resize（实例属性覆盖不可靠）

```python
self.gl.installEventFilter(self)
def eventFilter(self, obj, ev):
    if obj is self.gl and ev.type() == QEvent.Resize:
        self._reposition_gizmo()
    return super().eventFilter(obj, ev)
```

- 位置计算防越界：`x = max(15, gl.width() - gs - 15)`
- 初始位置就放最终位置（右上角），不要依赖后续重定位

## 七、offscreen 验证边界

- offscreen 下 GLViewWidget 能创建、代码路径能跑通，但**不真正渲染**——mesh 是否显示必须用户实测
- 能验证的：`_render_mesh()` 不抛异常、GL items 数量、shader 注册名存在、投影坐标在面板内

## 相关
- `pyqt5-pitfalls`：通用 PyQt5 坑（属性遮蔽、float 坐标、offscreen 验证）
- 本会话详细排查记录：见项目推进日志（点云/实体/航天花板三轮修复）
