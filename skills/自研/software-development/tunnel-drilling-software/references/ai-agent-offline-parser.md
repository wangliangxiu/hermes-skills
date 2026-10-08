# AI 设计助手（v0.11 离线规则版 Agent）完整实现

2026-08-13 会话实证。用户要求把《凿岩台车Agent资料库》规划的大模型 Agent 与
炮孔设计系统合并成一个软件——"真正能用 agent 输出炮孔设计，而不是随机生成"。

## 架构决策（用户拍板）

| 方案 | 结论 |
|:----|:----|
| DeepSeek API 大模型版 | 先不做（要花钱、演示怕断网、答辩怕穿帮） |
| Coze 工作流 API | 先不做（接外部平台） |
| **离线规则版**（关键词/正则解析） | ✅ 用户选中——零成本、断网可用、能先跑通"对话→设计"闭环 |

升级路径：后续换 DeepSeek API 时只改 `ai_agent_core.py` 的解析层为
function calling（LLM 决定调哪个引擎函数），UI/引擎不动。

## 文件结构

```
ai_agent_core.py   — 纯逻辑，无GUI，可单独跑 __main__ 自测
  parse_all(text)  → {'params': {...}, 'missing': [...]}
  run_design(text) → 解析→调 calc_blast_design→build_report
  run_qa(question) → 资料库 txt 关键词检索
  kb_load_all() / kb_search(question, top_k=3)
ai_agent_tab.py    — AIAgentPanel(QWidget)，Tab11 面板
  _send() 意图判断 → _handle_design / _handle_qa
  on_apply 回调 → 主窗口 _apply_agent_params()
drill_design_v09.py — import + addTab + _apply_agent_params()
```

## 解析器字段（对照《04_Agent输入输出参数清单》）

| 字段 | 支持说法 | 默认/缺参行为 |
|:----|:--------|:-------------|
| 围岩等级 | Ⅲ级/三级/3级/Ⅰ~Ⅵ罗马字/f=6 | 必填；只给 f 时补 rock_grade='自定义' |
| f_manual | f=6、f6、f值6 | 与 rock_grade 可并存，rock_f 优先用 f_manual |
| span/height | 跨度6米/6米宽/跨度6m/6×5 | 必填；6×5 时大数为跨度小数为高 |
| method | 全断面/台阶法/CD法/双侧壁导坑 | 必填，默认全断面（缺参仍报缺） |
| hole_dia_mm | 45毫米/45mm/孔径45/钻杆45 | 必填 |
| hole_depth | 循环进尺3米/孔深3米/3米的孔 | 必填 |
| explosive | 乳化炸药/铵油炸药 | 必填，默认乳化炸药 |
| cut_type | 直眼/楔形 | 选填，默认直眼 |
| dist/target | 距民房20米/离管线15米 | 选填，默认 30m；民房→v_allow=2.5 |
| v_allow | 由 target 映射（PROTECT_DEFAULT） | 民房2.5/管线2.0/隧道15/衬砌3/边坡7 |

必填 7 项：围岩、跨度、高度、开挖方式、孔径、进尺、炸药。缺参时 hint 列出
全部缺失项+参考格式，不瞎猜默认。

## 意图判断（_send 里）

```python
design_kw = ('设计','布孔','炮孔','方案','掏槽','开挖','断面','进尺','孔深','孔径','炸药')
is_design = any(k in text for k in design_kw)
```

含设计关键词 → run_design；否则 → run_qa。示例下拉 5 条（4 设计 + 2 问答）。

## 一键应用到炮孔设计页

`_apply_agent_params(params)`（主程序）：
- 围岩：解析出的等级；只有 f 值时按 ROCK_F 就近映射
  `_map = sorted([(abs(fv-f), g) for g, f in ROCK_F.items()])`
- span/height → setValue；四类孔深同步（底板 max(0.5, d-0.2)）
- cut_type → setCurrentText；_gen()；tabs.setCurrentIndex(0)

## 踩坑 4 条（2026-08-13 实证）

1. **"6米宽5米高" span 解析错成 5.0**——正则 `(?:跨度|宽度|宽)为?(\d+)米`
   会先命中"宽5米"。修复：**数字在前形式优先**
   `(\d+)[米m](宽|跨度|跨)`，再退到"跨度/宽度为X米"。
2. **只给 f=6 时 blast_design 抛 KeyError 'rock_grade'**——calc_blast_design
   第一行 `grade = params['rock_grade']`。parse_all 里
   `if 'f_manual' in merged and 'rock_grade' not in merged: merged['rock_grade']='自定义'`
   （rock_f 有 f_manual 就优先用，等级只是占键）。
3. **解析函数返回 None 值污染 missing 检查**——parse_span_height 若返回
   `{'span': None, 'height': None}`，merged.update 后 missing 误判"已给"。
   必须只回填非 None：`out={}; if span is not None: out['span']=span`。
4. **知识检索整词命中差**——问"萨道夫斯基公式是什么"，资料库段落是
   "萨道夫斯基公式 v = K×(³√Q÷R)^α"（有完整词）但其他段落只有"萨道夫斯基"。
   `_expand_kws` 把 ≥4 字词拆 2/3 字子串，命中权重=len(kw)，长词命中更值钱。

## 知识问答检索（run_qa）

- 资料库路径：`../凿岩台车Agent资料库/`（相对 ai_agent_core.py 所在目录）
- 只读 .txt（01 计算书是 docx 暂不索引；02/03/04/05/06 是 txt）
- 段落切分：按行，len>=6 才收；打分=命中关键词长度和，取 top3
- 无命中返回提示语，不编答案

## 验证记录（offscreen 全 PASS）

- 设计解析：Ⅲ级/6×5/全断面/45mm/3m/乳化/距民房20m → 78 孔、振动安全 True
- 二级围岩 f=9、8米宽6米高、台阶法、51mm、3.5m → 解析 f_manual=9 + rock_grade='Ⅱ'
  （修复踩坑1/2后）；应用回填 rock='Ⅱ' span=8.0
- 缺参提示 7 项齐全；知识问答命中"萨道夫斯基公式"
- Tab 数 11；_apply_agent_params 回填 span=6.0 height=5.0 rock='Ⅲ' 孔数=59；
  应用后自动切回 index 0
- 回归：5 种断面布孔/爆破设计面板报告/施工日志样本/定位面板 _run/
  执行表 59 行/凿岩参数推荐/知识问答——全部 PASS 无退化

## 测试脚本要点

- `_test_ai_agent.py`：纯逻辑断言（解析/缺参/问答）+ GUI（MainWindow 实例化、
  Tab 数、_handle_design 走真实路径、_apply_agent_params 回填断言）
- `_test_regression.py`：原有功能回归（各 Tab、执行表、断面切换）
- **坑：offscreen 下 QTimer.singleShot 兜底 20s 强制 quit**，防止断言失败后
  app.exec_() 挂死导致 terminal 超时（首次测试就踩了：断言失败没 quit →
  180s 超时）
- 测试中模拟 Agent 对话必须走 `w.agent_panel._handle_design(t1)`（真实路径），
  直接塞 last_params 会绕过解析，断言 last_params 必然失败

## 版本与交付

- 主窗口标题 v0.9 → v0.11（'智能炮孔设计系统 v0.11 - AI设计助手版'）
- 导出执行表 meta 版本同步 v0.10.3 → v0.11
- 推进日志已追加【记录12】
- 下一步：用户实测对话体验补解析规则 → 确认后打包 v0.11 exe/zip →
  后续升级 DeepSeek API 版
