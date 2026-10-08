---
name: docx-annotation-review
description: Word文档标黄审阅：黄色高亮标记不确定/空缺并统一其他颜色。触发：标黄、标注出来。
---

# Word 文档标注审阅（docx-annotation-review）

当用户要求"把不确定/空缺的地方标注出来"、"用黄色标注"、"标黄"时使用。
2026-08 实证于大赛BP多轮迭代（标黄28→22→17→12处的完整循环）。

## 核心思路

1. **黄色 = 不确定/空缺**（run 字符高亮，荧光笔效果），其余内容颜色统一归黑
   —— 让用户一眼分清"哪些没定"。用 `run.font.highlight_color = WD_COLOR_INDEX.YELLOW`，
   不是底纹（shading），打印/导出都看得到。
2. 标黄规则用**关键词判断**（见下），不是手工列段落——文档一改就要重跑，规则化才能反复用。
3. 每次改完**必须重跑标黄 + 验证**（黄色段清单 + 非黑颜色检查），防误伤、防漏标。

## 标准流程

### 1. 探查结构（改前必跑）
```python
from docx import Document
doc = Document(SRC)
# 打印每段 run 数、现有 highlight/color，注意文档里已有的设计色（蓝标题/橙小节/灰字）
for i, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if not txt: continue
    info = [f"run[{r.text[:10]!r}] hl={r.font.highlight_color} col={r.font.color.rgb if r.font.color and r.font.color.type is not None else None}" for r in p.runs if r.font.highlight_color is not None or (r.font.color and r.font.color.type is not None)]
    print(i, len(p.runs), txt[:40], "||".join(info))
```
现有颜色可能是**设计色**（蓝=大标题、橙FFC000=重点小节、灰404040/AAAAAA=次级/说明），
也可能是旧版标注色——先分清，再决定统一策略。

### 2. 标黄关键词规则（BP类文档实证）
```python
def should_highlight(txt):
    if not txt.strip(): return False
    marks = ["【待补","【待附","【待办","【待整理","待补","待附","待办","待整理","待核实","待验证"]
    if any(k in txt for k in marks): return True
    for k in ["假设","估算","推算","预算预留","参考基数","保守成本假设"]:
        if k in txt: return True
    return False
```
坑：关键词要**跟着内容改**——"渗透率"曾把已定稿的市场测算段误标黄
（定稿后数字仍含"渗透率10%~30%"），改稿后把已定稿关键词从规则里去掉再重跑。

### 3. 执行标注
```python
for i, p in enumerate(doc.paragraphs):
    hit = should_highlight(p.text)
    for r in p.runs:
        if hit:
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW
            r.font.color.rgb = RGBColor(0,0,0)          # 黄底黑字
        else:
            if r.font.highlight_color is not None: r.font.highlight_color = None
            if r.font.color and r.font.color.rgb is not None: r.font.color.rgb = RGBColor(0,0,0)
doc.save(SRC)
```

### 4. 验证（交付前必跑）
```python
doc = Document(SRC)
yellow = [p for p in doc.paragraphs if any(r.font.highlight_color and r.font.highlight_color.name=='YELLOW' for r in p.runs if r.text.strip())]
colors = {str(r.font.color.rgb) for p in doc.paragraphs for r in p.runs if r.font.color and r.font.color.rgb is not None}
print('黄色段数:', len(yellow), '| 剩余非黑颜色:', colors)  # 应只剩 {'000000'}
print('段落数:', len(doc.paragraphs), '| 图片数:', len(doc.inline_shapes))  # 完整性
```

## 配套编辑技巧（同批次常用）

```python
def set_para_text(p, new_text):   # 整段重写且保留格式：runs[0] 放全文，清空其余 run
    if not p.runs: p.add_run(new_text); return
    p.runs[0].text = new_text
    for r in p.runs[1:]: r.text = ""

def find_para(key):               # 按关键词定位段落（比硬编码索引稳，索引会漂移）
    for p in doc.paragraphs:
        if key in p.text: return p

def insert_after(anchor_p, text): # 在 anchor 段后插新段（用 lxml addnext，注意顺序）
    new_el = anchor_p._p.makeelement(qn('w:p'), {})
    anchor_p._p.addnext(new_el)
    np = Paragraph(new_el, anchor_p._parent); np.add_run(text)
    return np

# 删除段落（注意：删完索引全变，所以"先文本替换后删段"或按对象收集再删）
p._element.getparent().remove(p._element)

# 插图片（附录截图等）：run.add_picture(path, width=Cm(14))，A4可用宽约14.6cm
# 图片按顺序插：每次 insert_after 到上一张后面
```

## 用户确认段落 → 豁免集去黄（2026-08-17 实证）

使用者说"XX没问题/就那样写" = 该段内容确认 → 去黄；但确认不等于不改文本——新事实仍要落进文本再去黄（例：管理风险确认后，路演/商业角色=王工、无导师，先改文本再去黄）。

重跑标黄时用 **豁免集**，不要从关键词规则里全局删词：
```python
CONFIRMED_KEYS = ["客户付费意愿待验证", "商业与路演由王工担任"]  # 按文本特征，勿用段落索引！
hit = should_highlight(p.text) and not any(k in p.text for k in CONFIRMED_KEYS)
```
全局删关键词会误伤其他含同词但未确认的段——"待验证"同时命中风险2（已确认）和其他未确认段，删词会让未确认段悄悄漏黄。**豁免必须按文本特征不用索引**：删段后索引全漂移（本次删4段后 CONFIRMED={142,145} 错位，已确认去黄的风险2被重新标黄）。重跑后必须打印豁免段验证无黄。改完报**剩余黄色清单**给使用者核。

## 坑（2026-08-17 BP标黄收尾实证）

- **索引漂移**：删除段落（删章节/目录行）后所有后续段落索引前移，硬编码索引的豁免/定位全失效——本次删 6.2 章节4段后豁免索引错位，已确认去黄的风险2被重新标黄。删段操作后一律重新按文本特征定位/豁免；验证时打印豁免段确认无黄。
- **使用者可能正用 Word 手动改文档**：两次读取之间内容会变（本次 [109]渠道1、[121]成员1 的"6年"被使用者自己删了，脚本没动它们是对的）。动手前重新读当前状态，别用上一轮输出当依据；只改使用者明确要求的部分，不覆盖使用者手动改过的地方。
- **批量文本替换会误伤日期子串**："6年"→"多年" 若全文档 replace，会把"2026年8月"改成"202多年8月"（"2026年"含子串"6年"）。做法：按段落定位（打印命中段+上下文确认）+ 段内 run 替换；替换后验证残留时排除日期段。
- **替换前先打印 run 结构**：跨 run 文本（"6"在一个 run、"年"在另一个 run）r.text.replace 会漏；先打印段 runs 确认目标字符串在单个 run 内再改。
- **跨 run 字符串替换仍会静默失败，必须有兜底**：目标串拆在多个 run（如"负责人：王工、穆工、明工、徐工"各名字独立 run）时，单 run replace 一个都替换不到且不报错（本次团队3人改动 7 处仅 3 处生效）。改法：替换后立即整段复查（`if old in p.text` 判断是否生效），失败就改用 set_para_text 整段重写（全文放 runs[0]）；目标段无局部加粗/变色才可放心重写。
- **带手动目录的长文档删章节要删两处**：目录区（TOC 列表）+ 正文区各一组（"6.2 顾问/导师"在 [34][35] 和 [127][128] 各一份）。用 == 精确匹配循环删完所有命中，验证残留为 0 再交付。
- **联动数字改完做全文残留检查**：团队人数/成本/利润这类牵一发动全身的修改，验证脚本搜所有旧值（'4人×'、'16.2万'、'9.1万'、'成员4'）逐一确认 0 残留，防漏改前后矛盾。
- **业务事实变更必须跨文件联动扫描**：团队人数/定价/成本结构一改，数字跨文件连锁——BP(.docx) + 报名PPT(.pptx) + 路演稿(.txt) 全要同步（使用者明确要求"所有都改"）。流程：① 改前按数字/名字模式（16.2万/8万/9.1万/4人/成员4…）grep **每个文件**列全改动点——第一次 grep 必漏（实证：路演稿商业模式段 16.2万、PPT第13页财务页都是第二轮才抓到）；② 财务联动先算清再改（4人→3人 ⇒ 研发 8万→6万 ⇒ 首年 16.2万→14.2万 ⇒ 税后 9.1万→11.0万，此后年份不变）；③ 改完**每个文件**跑残留检查（旧数字/旧名字零命中）。

## 铁律

- **改前备份**：shutil.copy2(SRC, Temp备份)，改坏能还原
- **只留最新版**：覆盖原文件，不另存"标注版v2"（使用者桌面规矩）
- 临时脚本放 Temp，用完即删
- 多轮迭代节奏：改内容 → 重跑标黄 → 验证 → 汇报黄色清单给使用者（哪些是真待补）
