# 爆破设计计算引擎（blast_design.py）实现要点

2026-08-03 集成进主系统，新增 Tab8「💣 爆破设计」。
文件：`桌面\我的小项目\智能炮孔设计系统\blast_design.py`
公式依据：references/blast-design-formulas.md（用户可展示版=Agent资料库/01计算书.docx）

## 模块结构（公式引擎与界面分离）
- `calc_blast_design(params) -> dict`：纯计算函数，无 GUI 依赖，可单独测试
- `build_report(res) -> str`：七步公式链文字报告（带公式步骤，现场能复核）
- `BlastCanvas(QWidget)`：QPainter 断面布孔示意图（拱形轮廓+孔点+图例+标注）
- `BlastDesignPanel(QWidget)`：新 Tab 界面（输入面板+画布+结果表格+报告）
- 主系统 `drill_design_v09.py`：`from blast_design import BlastDesignPanel`，
  `self.tabs.addTab(self.blast_panel, '💣 爆破设计')`

## 输入参数（全部界面可调，不锁死）
隧道参数：围岩等级Ⅰ~Ⅴ（下拉联动普氏f，f可手改）、跨度、高度、
  开挖方式（全断面/台阶法/CD法/双侧壁，按面积修正系数1.0/0.6/0.5/0.4）、
  孔径mm、孔深m
爆破参数：炸药品种（乳化/铵油）、掏槽形式（直眼/楔形）、η、孔距倍数(8~15)、
  抵抗线倍数(10~20)
安全参数：保护距离R、允许振速v、场地系数K、衰减指数α

## 关键算法决策（踩过坑，别改回去）
1. **掏槽孔必须用"装药长度×线装药密度"算，不用体积法**
   - 体积法（q×掏槽区体积÷孔数）算出单孔 0.19kg，明显偏小
   - 正确：Q_cut = L掏 × ξ掏 × 线装药密度（φ32乳化药卷约 0.9 kg/m）
   - 辅助/底板孔同样用 ξ×L×线密度；周边孔用光爆低密度 0.30 kg/m
   - 结果量级验证：6m×5m 断面、3m 孔深 → 掏槽 2.13kg/孔、总药量 77kg，符合实际
2. **铵油炸药自动修正**：线密度 ×0.9（密度略低），炸药品种也影响 q
3. **软岩外插角自动放大**：f≥6→3°、f 3~6→4°、f<3→5°
4. **q 的经验式**：q = q_base + q_fcoef × f（默认 0.45 + 0.11×f），
   f=6 → 1.11 kg/m³，再按炸药品种修正；报告里必须标注"需试爆标定"
5. **围岩等级→f 映射**：Ⅰ=12、Ⅱ=9、Ⅲ=6、Ⅳ=3、Ⅴ=1.5（可手改）

## 孔数估算（简化但量级合理）
- 断面几何：拱形 = 半圆拱 + 两侧矩形；
  面积 = πr²/2 + span×(h−r)，轮廓周长 = πr + 2(h−r) + span
- 周边孔数 = 周长 ÷ a（沿轮廓等距采样 contour_samples()，
  折线顶点+弧长插值，原点在断面中心、y 向上）
- 辅助孔数 = (有效面积 − 掏槽区 − 周边带) ÷ (a辅助×b辅助)
- 掏槽：直眼 = 1 空孔 + 8 装药孔（r=0.15m 圈）；楔形 = 10 个
- 底板孔数 = span ÷ a

## 振动验算（与手算对照验证过）
- Qmax = R³ × (v允 ÷ K)^(3/α)；n_seg = ceil(Q_total / Qmax)
- v_pred = K × (∛Q_seg ÷ R)^α；safe = v_pred ≤ v_allow
- **验证技巧**：近距场景（如 R=20m、K=50、α=1.5、v=2.0）
  算出 Qmax=12.8kg，与计算书手算完全一致 → 公式实现可信
- 分段结果示例：总 77.4kg / Qmax 12.8 → 自动分 7 段，每段 11.06kg

## offscreen 验证命令（改完必跑）
```bash
"D:/python/python.exe" -m py_compile blast_design.py drill_design_v09.py
QT_QPA_PLATFORM=offscreen "D:/python/python.exe" -c "
import sys; from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
from blast_design import calc_blast_design, build_report, BlastDesignPanel
from drill_design_v09 import MainWindow
# 纯函数多场景 + GUI 实例化 + 主窗口 Tab 数
"
```
多场景必测：标准Ⅲ级 / 保护目标场景（既有隧道30m、管线30m触发分段）/ 软岩Ⅴ级+铵油 / 楔形掏槽。

## 保护目标场景（用户纠错：场景必须贴合隧道施工实际）
⚠ 教训：初次测试用"距民房20m"举例，被用户直接质疑——
凿岩台车在隧道内施工，振动保护目标不可能是地面民房。
已改为 PROTECT_TARGETS 下拉（UI选场景自动带出允许振速，可手改）：
- 既有隧道/洞室 15 cm/s（默认，最贴合隧道场景）
- 新浇混凝土衬砌 3.0（按龄期调整）
- 浅埋段地表建筑 2.5（砖混参考2~3）
- 矿山边坡 7.0（参考5~9）
- 管线 2.0（敏感取低值）
- 自定义 2.0
允许振速一律标注"参考GB6722，以规范原文为准"，不冒充规范数据。
UI联动：self.target.currentTextChanged → _sync_v()；报告显示保护目标名称。

## GUI布局偏好（用户明确反馈，别再犯）
- 参数面板两列排布：隧道参数|爆破参数 GroupBox 并排，
  安全验算用 QGridLayout 两列网格横跨整行（左区 setFixedWidth(470)）
- 右侧不留大块空白：画布+结果表格并排在上（stretch 5），
  计算报告填满下方（stretch 3），表格取消 setMaximumHeight 限高
- 用户原话："中间太多空白、上方都是空白的"——任何新 Tab 都要按
  "内容填满、不留白"检查布局

## offscreen 验证调试技巧（Windows + 中文路径环境）
- **offscreen 下 show()+processEvents() 会崩**（bash 报 127、无任何输出），
  这是 Qt offscreen 插件的环境限制，不是代码问题；标准验证只实例化不 show
- 崩溃定位：python 输出是块缓冲，进程崩溃时 print 全部丢失 → 用
  `"D:/python/python.exe" -u -X faulthandler -c "exec(open(r'脚本.py', encoding='utf-8').read())"`
  看崩溃前最后一步输出在哪（曾定位到 show 触发 paintEvent 崩溃）
- 长命令行含中文/特殊Unicode字符时 bash 可能解析失败返回 127 →
  把验证脚本写成 .py 文件再运行，别塞进 -c 长命令
- **脚本文件模式 sys.path 不含 cwd**：python xxx.py 运行临时脚本时
  import 不到项目模块（ModuleNotFoundError），脚本开头要
  sys.path.insert(0, 项目目录)；python -c 模式自动含 cwd
