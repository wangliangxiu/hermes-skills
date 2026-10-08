# 复测检验与自动纠偏（v0.10.3）实现细节

2026-08-13 会话落地。用户把定位校准从"提示人工移车"升级为"出现偏差
直接给台车指令，让台车调整自身位置来调整"。全部内嵌
`drill_design_v09.py` 的 PositioningPanel（Tab9）。

## 核心函数（模块级，可单测）

### build_correction_cmds(dy_cm, dz_cm, yaw_deg, D)
偏差超限 → 纠偏指令序列 `[(动作, 轴, 调整量, 单位, 原因), ...]`：

| 超限条件 | 指令 |
|:----|:-----|
| dy > +5cm | 左移 dy cm（横向右偏→左移回正） |
| dy < -5cm | 右移 -dy cm |
| dz > +5cm | 下降 dz cm |
| dz < -5cm | 升高 -dz cm |
| yaw > +1° | 逆时针转向 yaw° |
| yaw < -1° | 顺时针转向 -yaw° |
| D < 4m | 后退 (4-D) m |
| D > 10m | 前进 (D-10) m |

全达标返回 `[]`。单测样本：
- `(12, -3, 2, 6)` → `[('左移','dy',12,'cm',...), ('逆时针转向','yaw',2,'°',...)]`
  （dz=-3 在 ±5 内 → 无指令）
- `(-8, 9, -1.5, 3.0)` → `['右移','下降','顺时针转向','后退']`

## 复测检验区（Tab9 右侧 QGroupBox）

布局：达标大标签 → 按钮行1（📡下发纠偏指令/📝记录本次测量）→
按钮行2（💾导出JSON/🗑清空记录）→ 指令预览（黄色小字）→
较上次对比（灰色小字）→ 记录表（7列，最高160px）。

- **达标判定 `_pass_state`**：dy/dz±5cm、yaw±1°、D∈[4,10]m 全部满足才
  pass；返回 (ok, fails列表)，fails 显示在 tooltip
- **记录表 `_refresh_table`**：序号|时间|dy|dz|yaw|D|判定，QTableWidgetItem
  setTextAlignment(AlignCenter) + setForeground（✓绿 #7CFC9A / ✗红 #FF9A7C /
  其他 #ddd），深色底 #1e1e2e，表头 stylesheet 设浅色否则黑字看不见
- **较上次对比 `_refresh_recheck`**：只对比 records[-1]；`d = cur - last`，
  |d|<0.05 显示"无变"。**记录动作后立即对比必然"无变"——记录不改输入值，
  这是正确行为不是 bug**；改参数后才显示差异（如 dy 12→2 显示 dy-10.0）
- **导出JSON**：类型/台车编号(占位)/导出时间/允许偏差/作业距离范围/
  测量记录/纠偏指令记录，ensure_ascii=False + indent=2

## 一键下发纠偏指令 `_send_correction()`

流程：build_correction_cmds → payload（type/time/台车编号/cmds 含 action/
axis/amount/unit/reason）→ **模拟执行** → 更新输入框 → 自动重算 → 达标。

模拟执行规则（现场语义）：
```
new_dy += amt if 动作=='右移' else -amt    # 左移减，右移加
new_dz += amt if 动作=='升高' else -amt    # 下降减，升高加
new_yaw += amt if 动作=='顺时针转向' else -amt
new_D  = D_min if 动作=='后退' else D_max  # D 回范围边界
```
只纠超限轴，允许范围内参数保持原值（"没超不动"）。

**真实通信接口位置**：代码注释标注 `# def _send_to_rig(self, payload): →
Modbus/TCP/串口发送给台车控制系统`，协议（设备所负责人确认）到位后替换模拟执行
部分。先模拟+导出JSON演示闭环，符合"先落地再对接"原则。

## 实证坑

### 坑1：QTextEdit append 被 setText 覆盖（调试过程）
初版 `_send_correction` 用 `result.append('[模拟执行]...')` 追加提示，
随后 `self.dy.setValue(...)` 触发 valueChanged → `_run()` → 
`result.setText('\n'.join(lines))` 把 append 的内容全部冲掉。结果文本里
只剩【纠偏指令记录】（cmd_log 渲染的），[模拟执行] 行消失。
修复：**持久信息一律存数据列表（cmd_log），由 `_run()` 统一 setText 渲染；
不要依赖 append 跨 _run 存活**。cmd_log 存两行：下发指令 + 执行结果。

### 坑2：search_files 中文路径 content 搜索漏命中
用 search_files 搜 "校准|标定|定位"（file_glob=*.py）对 drill_design_v09.py
返回 0 命中，但功能明明存在（PositioningPanel 等）。用 terminal
`grep -n "PositioningPanel|design_to_rig|定位"` 立刻找到。
教训：**功能存在但搜不到时，先怀疑搜索工具，用 grep 交叉验证**，别急着
下"没做过这个功能"的结论。

### 坑3：offscreen 验证断言想当然（两次失败都是断言错不是代码错）
- 断言 result 含"【纠偏指令记录】"：cmd_log 为空时该区块不渲染 → 断言要
  分阶段（下发指令后再断言），或单独断言历史区块
- 断言记录后对比文本显示差异：记录后当前==记录值→"无变"是正确行为
- 断言下发后 dy/dz/yaw 全归零：dz=-3 在 ±5 范围内→无 dz 指令→保持 -3 是
  正确行为。断言必须按"只纠超限轴"语义写

## offscreen 验证脚本骨架

```python
QT_QPA_PLATFORM=offscreen python -c "
import sys
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
import drill_design_v09 as dd
w = dd.MainWindow(); w.show()
p = w.pos_panel

# 1) 纯函数单测
assert dd.build_correction_cmds(12,-3,2,6) == [('左移','dy',12.0,'cm',...), ...]
assert dd.build_correction_cmds(0,0,0,6) == []

# 2) 记录闭环
p.dy.setValue(12.0); p._record_measure()
p.dy.setValue(2.0)
assert 'dy-10.0' in p.cmp_label.text()      # 前后对比
p._record_measure()
p.yaw.setValue(0.5); p._record_measure()
assert p.records[2]['pass'] is True          # 达标判定

# 3) 一键下发（模拟执行）
p.dy.setValue(12.0); p.yaw.setValue(2.0)
p._send_correction()
assert abs(p.dy.value()) < 0.01 and abs(p.yaw.value()) < 0.01
assert p.dz.value() == -3.0                  # 范围内不动
assert '定位达标' in p.pass_label.text()
assert len(p.cmd_log) == 2                   # 下发指令+执行结果两行
assert '【纠偏指令记录】' in p.result.toPlainText()

# 4) 全Tab回归 + Tab1 联动（铁律）
for i in range(w.tabs.count()):
    w.tabs.setCurrentIndex(i); app.processEvents()
"
```

## 实测结果（2026-08-13）
- 指令生成：+12/-3/+2 → 左移+逆时针；全达标 → []; -8/+9/-1.5/3 → 4条全对
- 记录闭环：3条记录、dy-10.0 对比、达标判定逐条正确
- 一键下发：dy 12→0、yaw 2→0、dz -3 保持、D 3→4、D 12→10
- 9Tab切换/8m楔形布孔/画布grab/施工日志/点云三模式全部无退化
