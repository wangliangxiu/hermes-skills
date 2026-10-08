# 钻孔角度体系 + 复测检验/自动纠偏 + exe打包（v0.10.3，2026-08-13）

## 钻孔角度体系（用户问"钻孔的角度系统中有呈现吗"→ 补齐）

### 角度语义（工程习惯）
- 相对掌子面平面，**90°=垂直**；掏槽内倾/周边外插/底板上仰都 <90°，
  方向由孔位隐含（中心/轮廓/底部），角度值只记偏离量。
- 默认值：掏槽 87°（直眼内倾3°）/ 辅助 90°（垂直）/ 周边 87°（外插3°，控超欠挖）/
  底板 85°（上仰5°，防底部欠挖）；中心空孔 90°。楔形掏槽用掏槽角度（切楔形时调 55~70°）。

### 实现
- `gen_holes_realistic(..., angles=None)` 新增参数；angles={'掏槽','辅助','周边','底板'}。
  每孔写入 `'设计角度'` 字段（round 到 0.1）——施工日志 generate_construction_log
  读 `h.get("设计角度", 0)` 自动联动，无需改日志代码。
- Tab1 布孔参数区新增"角度(°)"列：表头加列 + 每行 QDoubleSpinBox（30~120，step 1），
  tooltip 说明各类型角度含义。self.hp[nm] 从 3 元组变 4 元组 `(sc,sr,sd,sa)`，
  `_gen()` 里 angles={'掏槽':hp['掏槽眼'][3].value(), ...}。
  ⚠ 左面板 setFixedWidth 360→400 容纳 5 列（60+55+65+70+70），列宽要同步压。
- Tab1 画布（HoleCanvas）底部 info 行加"角度 掏槽87° 辅助90°..."一览。
- Tab9 定位面板结果文本加两行：
  - 钻臂执行角度（可达孔）：回转 min~max°，俯仰 min~max°（check_reachability 反解的 az/el，
    工人按此摆臂；原本算了但没展示）
  - 设计角度一览（按孔类型去重）
- PositioningPanel 加 `self.angles` 默认 + `set_angles()`；MainWindow._gen 同步；
  独立生成孔时传 `angles=self.angles`。

### ⚠ paintEvent 局部变量名冲突（本次实证 bug）
HoleCanvas.paintEvent 开头 `w,h=self.width(),self.height()`，新加的
`for h in self.holes:` 把局部 h 覆盖成孔 dict → 末尾 `h-8` 报 TypeError，
**被 Qt 吞掉**（画布静默失效，界面不崩）。修复：循环变量用 hh/hh2。
教训：paintEvent 里局部循环变量别用 h/w/x/y（与尺寸变量冲突）；offscreen 回归必须看 stderr。

## 复测检验 + 自动纠偏（用户要求"出现偏差直接给台车指令"）

### 复测检验区（Tab9 右列下方 QGroupBox）
- 达标判定大标签：✓定位达标可开钻（绿）/ ✗未达标(N项)（红），tooltip 列明细；
  `_pass_state()` 规则：|dy|≤5cm、|dz|≤5cm、|yaw|≤1°、D∈[4,10]m。
- 「记录本次测量」：存 records（time/dy/dz/yaw/D/pass）+ 表格
  （序号|时间|dy|dz|yaw|D|判定，✓绿✗红居中）+ 结果文本【测量记录历史】区块。
- 「较上次记录」实时对比（对比最近一条；记录后当前值==记录值显示"无变"是**正确行为**，
  改参数后才显示差异）。
- 导出JSON：测量记录+允许偏差+作业范围+指令记录（现场闭环存档）。
- **result 文本用 setText 重渲染（含历史区块），不要 append**——append 的临时文本会被
  下一次 setText 冲掉（实证：[模拟执行] 行丢失）。持久信息写进 records/cmd_log 再渲染。

### 自动纠偏（一键下发）
- `build_correction_cmds(dy_cm, dz_cm, yaw_deg, D)` 纯函数：超限轴生成指令
  （左移/右移、升高/下降、顺时针/逆时针转向、前进/后退 + 原因），可单测。
- 「下发纠偏指令」：生成指令 → **模拟执行**（dy/dz/yaw 归零、D 回范围边界；只纠偏
  超限轴，范围内参数不动）→ 输入框 setValue 自动重算 → 达标变绿。
- 预留真实通信接口位置：`# def _send_to_rig(self, payload): → Modbus/TCP/串口`
  （协议待设备所负责人确认后替换）。指令+执行结果存 cmd_log 显示在【纠偏指令记录】区块。

## exe 打包（PyInstaller，2026-08-13 首次）

```bash
"D:/python/python.exe" -m PyInstaller -F -w --name 智能炮孔设计系统 \
  --collect-all pyqtgraph --hidden-import matplotlib.tri --hidden-import docx \
  --clean drill_design_v09.py
```
- 要点：--collect-all pyqtgraph（动态导入多）；--hidden-import matplotlib.tri（mtri）；
  --hidden-import docx（python-docx）；-F 单文件便于分发；-w 无控制台。
- 产物：dist/智能炮孔设计系统.exe（单文件，中文名 OK）。
- ⚠ **改代码后必须重新打包**：打包启动时读的是当时的源码，打包中途改代码不会进 exe。
  打包完验证 exe 能启动（后台启动+检查进程存活）再交付。
- 打包时间约 5 分钟（PyQt5+pyqtgraph+matplotlib 全家桶），后台跑 + notify_on_complete。
