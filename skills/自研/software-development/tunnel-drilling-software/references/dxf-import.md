# v0.11 图纸导入（DXF）——Tab12 完整实现与踩坑

2026-08-13 会话实证。用户需求："导入掌子面设计图纸（DXF/CAD 为主），自动读出断面形状和坐标，不用手填参数"。决策：**工程图纸走 DXF 矢量解析是正道**（坐标精确、离线、比任何 AI 识图都准）；视觉模型识图只适合没有矢量数据的照片（如掌子面实拍），对毫米级布孔精度不可靠。

## 文件结构

```
dxf_import.py   — 纯逻辑（无GUI，可单测）：实体→线段→环聚类→形状识别→测尺寸
dxf_panel.py    — DxfImportPanel 面板（Tab12）+ DxfPreview 轮廓预览画布
drill_design_v09.py — import + addTab + _apply_dxf_result() 回填
```

依赖：`pip install ezdxf`（D:/python/python.exe -m pip install ezdxf）。

## 解析管线（parse_dxf 主入口）

1. **读实体 → 炸成线段** `_explode_entity(e)`：
   LINE/LWPOLYLINE/POLYLINE/ARC/CIRCLE/SPLINE 都转成 `[(x1,y1,x2,y2),...]`
   线段列表（ARC/CIRCLE 按弧度采样、SPLINE 用 construction_tool().flattening()）
2. **线段聚类成环** `_cluster_rings(all_segs)`（核心，见下）
3. **取面积最大环** = 断面轮廓（排除中心线/尺寸标注线等干扰）
4. **几何识别形状** `_identify_shape(pts)`：矩形（角点≥4且宽高比>0.9）/
   圆形（宽高比 0.9~1.15 且点多且角点≤2）/ 拱形（宽>高）/ 马蹄形（兜底）
5. **测尺寸** `_measure(pts, unit)`：跨度=w_max-w_min、高度=z_max-z_min、面积
6. **单位换算** `_to_m(v, unit)`：读 `doc.header.get('$INSUNITS', 6)`（DXF 单位码）
   - 毫米=4 (×0.001)、厘米=5 (×0.01)、米=6 (×1.0)、公里=7
   - **面积换算要 x、y 各换算一次**：`_to_m(_to_m(area_raw, unit), unit)`

## 环聚类（对抗标注线/中心线干扰）

真实 CAD 图纸不止一条轮廓线——还有尺寸标注线、中心线、文字。不能把所有线段
整体贪心拼一条折线（标注线会把轮廓拼歪）。做法：

```python
def _cluster_rings(all_segs, tol=1e-4):
    # ① 线段按端点连通性聚类（任一端点接近=同组，BFS）
    # ② 组内贪心拼折线 _polyline_from_segs
    # ③ 首尾闭合且≥4点的组 = 候选环，算面积
    # ④ 按面积降序排序，最大环 = 断面轮廓
```

验证：拱形轮廓+竖直中心线+两条水平尺寸线+箭头短线的图纸，正确识别 6×5 拱形。

## 形状识别与系统对接

- 识别的 shape 名与主程序 `SECTION_SHAPES` 一致（圆形/拱形/矩形/马蹄形…），
  `_apply_dxf_result` 直接 `self.shape_cb.setCurrentText(shape)` 回填
- `points` 输出米制轮廓点集 `[(y,z),...]`，与 `section_contour` 约定兼容
  （y=横向右正、z=高程上正），供预览画布直接画

## 面板交互

- Tab12「📐 图纸导入」：打开 DXF → 识别结果文本（形状/跨度/高度/面积/单位）
  + 深色轮廓预览（DxfPreview 归一化到画布、保留宽高比、网格背景）
  + 「⚡ 应用布孔」→ `_apply_dxf_result` → 回填 shape/span/height → _gen() → 切回 Tab1
- DWG 提示：DWG 是 Autodesk 加密私有格式，Python 读不了，需在 CAD 里
  "另存为 DXF" 再导入（面板 unit_tip 里已注明）

## 踩坑记录（本会话实证）

1. **线段拼接反向匹配的坐标下标 bug**：`_polyline_from_segs` 里找"以当前点
   结尾的线段"时写了 `math.hypot(s[2]-cur[0], s[1]-cur[1])`——**s[1] 应为 s[3]**。
   症状：矩形 LWPOLYLINE 拼接点序乱跳（点集顺序错误但点数对），矩形识别失败。
   线段元组是 `(x1,y1,x2,y2)`，反向匹配必须比 `s[2], s[3]` 与 cur。
2. **闭合轮廓的首尾点不能删（矩形丢角变三角形）**：第一版 `_smooth_close`
   把"首尾重复点"当垃圾删掉，矩形从 4 点变 3 点 → 丢一个角、面积算错、
   报"轮廓点太少"。**闭合轮廓首尾点相同是合法表示**（主程序 section_contour
   的矩形也是 5 点首尾相同），`_smooth_close` 只应删**相邻重复点**
   （圆弧采样可能产生），不能删首尾闭合点；若首尾不同（非闭合）才补闭合点。
3. **DXF 多段线 get_points() 返回带 bulge 的元组**：LWPOLYLINE 的
   `get_points()` 默认返回 `(x,y,start_width,end_width,bulge)`，取坐标必须
   `pts[i][0], pts[i][1]`，不要整体 unpack 成 2 元素。
4. **识别测试样例要覆盖单位**：同一几何用毫米($INSUNITS=4)和米($INSUNITS=6)
   各存一份，验证单位换算不是碰巧对。
5. **矩形轮廓只有 4 个角点**：形状识别角点计数 `abs(dot)<0.15` 判 90°，
   矩形 corners≥4 → '矩形'；但 `_identify_shape` 开头 `if n < 5: return '矩形'`
   兜底（点数少的闭合环先按矩形处理，避免误判）。

## 验证清单（offscreen）

- 4 种样例（拱形毫米/拱形米/圆形/矩形）识别 shape/span/height 全部正确
- 带标注干扰图纸取最大环正确
- 面板 `_parse()` 后 btn_apply 可用、result 非空
- `_apply()` 后 Tab1 shape_cb/span/height 正确、design_holes>0、tabs 切回 0
- 全 12 Tab 回归：布孔/爆破设计/执行表/AI助手 无退化
