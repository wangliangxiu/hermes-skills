# pyqtgraph GLMeshItem / 点云3D 渲染避坑（2026-08 实测，pyqtgraph 0.14）

台车系统点云分析Tab（PointCloudPanel，GLViewWidget + GLScatterPlotItem + GLMeshItem）多轮排查实证。
用户环境：集显 + Windows 11 + pyqtgraph 0.14.0。

## 1. shader 名字有拼写陷阱：'edgeHilight' 不是 'edgeHighlight'
- pyqtgraph 0.14 注册的 shader 名：`None, 'balloon', 'viewNormalColor', 'normalColor', 'shaded', 'edgeHilight', 'heightColor'`
- 传 `shader='edgeHighlight'`（多一个 g）→ `getShaderProgram` 查表 KeyError，在 paint() 里被 Qt 吞掉 → **mesh 整个不渲染，画面只剩其他 scatter 点**，不报错不崩溃（用户反馈"实体表面只剩点"的真凶）
- 查可用 shader：`from pyqtgraph.opengl import shaders; list(shaders.ShaderProgram.names.keys())`

## 2. GLMeshItem 是 **kwargs 接收参数
- `inspect.signature(GLMeshItem.__init__)` 只能看到 `(parentItem=None, **kwds)`
- 参数名要看源码/文档：meshdata, color, edgeColor, drawEdges, drawFaces, shader, smooth, computeNormals
- 全部以关键字传入，`shader='...'` 会被 GLMeshItem 单独 pop 出来走 setShader

## 3. 最终方案：shaded + 法线全部指向光源（用户集显实证可行）
用户对 shaded 不满的是"旋转变暗"，对 heightColor/None 的问题是"不渲染"。最终解法组合：
```python
# 面颜色：按高度渐变（低=蓝欠挖 → 中=绿合格 → 高=红超挖）
z_avg = np.mean(vertices[faces][:, :, 2], axis=1)
face_colors = np.zeros((len(faces), 4))
for i, z in enumerate(z_avg):
    t = (z - zmin) / max(zmax - zmin, 1e-6)
    face_colors[i] = _height_cmap(t) + [1.0]

# 法线全部指向 shaded 固定光源方向(1,-1,-1)/√3：
# dot(n,L) 恒=1 → 亮度恒满 → 旋转不变暗
nrm = np.array([1.0, -1.0, -1.0]) / np.sqrt(3.0)
mesh_data = pg.opengl.MeshData(vertexes=vertices, faces=faces, faceColors=face_colors)
mesh_data._vertexNormals = np.tile(nrm, (len(vertices), 1))  # 覆盖内部属性（smooth=True 时使用）

mesh_item = GLMeshItem(meshdata=mesh_data, smooth=True, shader='shaded',
                       glOptions='opaque', drawEdges=True, edgeColor=(0, 0, 0, 0.4))
```
- **MeshData 构造不支持 normals 参数**（只有 vertexes/faces/edges/vertexColors/faceColors），
  只能构造后覆盖内部属性 `_vertexNormals`
- smooth=True 时 GLMeshItem 用 vertexNormals（→ 用我们覆盖的值）；
  smooth=False 时用 faceNormals（自动计算，覆盖无效）
- shaded shader 源码：光源方向写死 `vec3(1,-1,-1)`，ambient 0.2 写死，不可从外部调
- 高度 colormap 建议分段插值：`[(0.0,(0.10,0.30,0.90)),(0.33,(0.10,0.85,0.90)),(0.55,(0.20,0.85,0.30)),(0.75,(0.95,0.80,0.15)),(1.0,(0.90,0.20,0.15))]`

## 4. 弃用方案记录（为什么不用）
- `shader='heightColor'`：内置按顶点z着色（uniformMap 9参数：`clamp(pow(scale*(z+offset), power))`，
  blue 通道要"z低时蓝"则 scale 取负），理论最优，**但用户集显 GLSL 可能编译失败 → 不渲染**，
  且无法 offscreen 验证 → 弃用
- `shader=None`：无光照纯色，需要 faceColors，某些版本渲染不稳定（0.14 实测不渲染）
- `shader='edgeHighlight'`：拼写错误，KeyError（见第1节）

## 5. 点云 mesh 必须降采样
- 3 万点 Delaunay 剖分 → 约 6 万三角形 + drawEdges 6 万边线，集显渲染极卡/显示不出来
- 实体表面模式先 `np.random.choice(n, 8000, replace=False)` 降采样，面数 ~1.6 万流畅

## 6. drawEdges=True 显示网格线（褶皱/连接结构）
- GLMeshItem 支持 `drawEdges=True, edgeColor=(r,g,b,a)`
- 无光照纯色 + 网格线 = 既能看出三角网格结构又不随旋转明暗变化

## 7. 半透明点/线在白色背景下会"发白"（translucent 混合）
- GLScatterPlotItem 默认 translucent 混合，alpha<1.0 时白色背景混合 → 颜色变淡像"变白"
- 切背景颜色恒定的要求：所有点/线 alpha 设 1.0（不透明）+ `glOptions='opaque'`
- 轮廓线同样处理：颜色加深如 `[0.1, 0.3, 0.8, 1.0]`，白/深背景都可见

## 8. 背景黑白切换
```python
self.gl.setBackgroundColor(QColor(238, 240, 245))  # 白
self.gl.setBackgroundColor(QColor(20, 20, 30))     # 深
```
- 切换只改底色，内容颜色不变（前提是内容不透明）

## 9. paintEvent 静默异常排查法（Qt 吞异常）
- **paint 里 Python 异常被 Qt 吞掉**：不崩溃、只在 stderr 打印，表现为
  "面板画了、某个元素没画出来"。排查顺序：
  1. 先看 paintEvent 里用到的类是否全部 import（实证：GizmoWidget 忘 import
     `QPolygonF` → drawPolygon 抛 NameError → 半透明面板可见、六面体不可见）
  2. 再看 API 名/枚举名拼写（shader='edgeHighlight' 同理）
- 这不是 offscreen 限制——真实环境下同样发生，用户只看到"东西没了"
