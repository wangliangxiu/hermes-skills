---
name: docx-textbox-editing
description: 改含文本框的Word文档（简历/模板）。触发词：docx文本框、简历修改。
---

# Word 文本框（Textbox）内容修改

适用：python-docx 改 .docx 时发现正文内容在文本框里（`doc.paragraphs` 读不到/只有一个段落）。
常见场景：简历（视觉模板）、带文本框排版的文档。真实案例：简历_王工.docx 内容全在文本框中（2026-08）。

## 一、识别：内容是否在文本框里

```python
doc = Document(path)
print('段落数:', len(doc.paragraphs))   # 只有1个（body），内容都在文本框 → 文本框结构
# 遍历含文本框的所有段落：
for p in doc.element.body.iter(qn('w:p')):
    txt = ''.join(t.text or '' for t in p.iter(qn('w:t'))).strip()
```

## 二、关键结构：AlternateContent 的 Choice / Fallback

- 文本框在 `w:drawing > AlternateContent` 里有**两个分支**：
  - `Choice`：`... > graphicData > wsp > txbx > txbxContent`（**Word 实际显示用这个**）
  - `Fallback`：`... > pict > shape > textbox > txbxContent`（兼容模式才用，**Word 不显示**）
- **只改 Choice 分支**（Fallback 改了不影响显示，还可能因插入层级错误污染正文）
- 判断分支：沿父链找 tag，`wsp`=Choice，`pict`=Fallback

```python
def in_choice(p):
    cur = p.getparent()
    while cur is not None:
        tag = cur.tag.split('}')[-1]
        if tag == 'wsp': return True
        if tag == 'pict': return False
        cur = cur.getparent()
    return False
```

## 三、插入新段落的两个大坑

### 坑1：不要 deepcopy 参考段落
- `copy.deepcopy(参考段)` 会把该段落内嵌套的**文本框 drawing 一起复制** → 文档出现大量脏数据/重复内容
- **用 body.makeelement 创建干净节点**，只复制 `pPr`（段落格式）和 `rPr`（run 格式）：

```python
def make_para(ref_p, text):
    new_p = body.makeelement(qn('w:p'), {})
    pPr = ref_p.find(qn('w:pPr'))
    if pPr is not None: new_p.append(copy.deepcopy(pPr))
    r = body.makeelement(qn('w:r'), {})
    ref_r = ref_p.find(qn('w:r'))
    if ref_r is not None:
        rPr = ref_r.find(qn('w:rPr'))
        if rPr is not None: r.append(copy.deepcopy(rPr))
    t = body.makeelement(qn('w:t'), {})
    t.set(qn('xml:space'), 'preserve')
    t.text = text
    r.append(t); new_p.append(r)
    return new_p
```

### 坑2：插入位置必须显式在父元素内
- `anchor.addnext(new_p)` 在复杂嵌套下可能插到**错误层级**（跑到 body 正文，污染页面）
- 用显式同级插入：`parent = p.getparent(); parent.insert(list(parent).index(p) + 1, new_p)`
- 插入后验证：新段落的父链应含 `txbxContent`，不在 body 直接子元素里

```python
# 验证父链
chain = []
cur = new_p
while cur is not None:
    chain.append(cur.tag.split('}')[-1]); cur = cur.getparent()
# 期望包含 txbxContent；如果只有 body > p 就是插错到正文了
```

## 四、替换段落文本（保留格式）

```python
def set_text(p, text):
    runs = p.findall(qn('w:r'))
    if not runs: return
    r0 = runs[0]
    for t in r0.findall(qn('w:t')): r0.remove(t)
    t = r0.makeelement(qn('w:t'), {})
    t.set(qn('xml:space'), 'preserve')
    t.text = text
    r0.append(t)
    for r in runs[1:]: p.remove(r)
```

- 只改第一个 run 的文本、删其余 run：格式（rPr）保留在第一个 run 上
- **坑（2026-08 实测）：段落里可能藏嵌套元素（超链接/书签容器）里的旧文本**，只删 `runs[1:]`（直接子 run）会残留——替换后行尾还跟着旧公司名如「北京XX有限公司」。要删除段落所有子元素，只保留 pPr 和第一个 run：

```python
def set_lines(p, lines):
    runs = p.findall(qn('w:r'))
    if not runs: return
    r0 = runs[0]
    pPr = p.find(qn('w:pPr'))
    for child in list(p):
        if child is pPr or child is r0:
            continue
        p.remove(child)
    # 再清 r0 内旧 w:t/w:br，写入新行（多行用 <w:br/> 分隔）
```
- 删除段落：`p.getparent().remove(p)`

## 五、描述列表 / 标题+内容段的结构（2026-08 实测补充）

- **工作经历描述 1/2/3/4 条各自是一个独立 `<w:p>`**（前面往往还有「工作描述：」标题段）——不是一段多行。只匹配第一段替换会留下第 2/3/4 条旧段落 → 验证时残留检查仍报错。正确做法：每条旧段落分别建规则（各自唯一匹配串）→ 替换成对应新行，保持模板段落结构
- 同理「主修课程：」标题段 + 课程内容段是两段，分开处理（标题保留，内容段换成本专业真实课程，别照抄模板原专业）
- **遍历 `txbxContent` 会同时碰到 Choice 和 VML Fallback 两份**（VML textbox 的 `<w:txbxContent>` 也在遍历范围），每条规则命中 2 次是正常的、两份都换即可；Word 只显示 Choice，VML 层同改避免旧版 Word 打开露馅
- 替换后验证：全文 join 起来查残留占位（`XX有限公司`/模板姓名/`20XX`/模板课程名）；某规则命中数 < 2 说明某一层文本有差异（如全角空格 vs 普通空格），先查差异再交付，不要直接交

## 五、交付前验证

1. body 直接子元素干净：`list(doc.element.body)` 应只有原始段落+sectPr，没有凭空多出的正文段
2. Choice 文本框内段落顺序正确（打印验证）
3. 交付 Word 打开实测视觉效果（python-docx 无法渲染，结构对≠视觉对）

## 相关
- `word-template-fill`：套模板填内容（模板路径不同，无文本框场景）
- 用户偏好：改简历生成**新文件**在桌面，不覆盖原文件；教育经历按入学年往前推（9月开学/7月毕业）
