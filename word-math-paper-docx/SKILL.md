---
name: word-math-paper-docx
description: 出数学试卷/习题册的Word文档时用（LaTeX转Word原生公式）。
version: 1.0.0
author: 甄der
license: MIT
metadata:
  hermes:
    tags: [word, docx, latex, omml, math, exam]
    related_skills: [word-docx, math-output-style]
---

# 含数学公式的 Word 文档生成

## When to Use / 何时用
要把公式排进 Word（试卷、习题册、计算书、公式推导文档），而不是在聊天里输出公式。
注意：`math-output-style` 管的是**聊天回复**里不要出现 LaTeX；本技能管的是**文档里要真公式**，两者不冲突。

## 环境：先自检，缺什么装什么（绝不假设已装好）
**任何一次开工前先跑自检**（换机器、换用户、重装系统后尤其要跑）：
```
D:\pyenv\kaoyan\Scripts\python.exe <skill目录>\references\bootstrap_env.py
```
若这台机器根本没建过环境，直接用任意 3.9~3.14 的 python 跑同一个脚本，它会自动建 venv 并装齐依赖：
```
python <skill目录>\references\bootstrap_env.py          # 默认建到 D:\pyenv\kaoyan
python <skill目录>\references\bootstrap_env.py --venv D:/pyenv/xxx --mirror <镜像源>
```
主人要双击的话，同目录的 `references\一键安装出卷环境.bat` 已做好（带 chcp 65001 防乱码）。

脚本会逐项检查并报结论（退出码 0 = 就绪）：
1. Python 环境（没有就自动建 venv；无 `py` 启动器的机器也能跑，已做兼容）
2. 依赖库：python-docx、lxml、latex2mathml、pymupdf、sympy、numpy
3. 公式样式表 MML2OMML.XSL（自动扫 Program Files / Program Files (x86) / 各 Office 版本；找不到 = 这台机器没装 Word）
4. 端到端探针：真生成一个带公式的 docx 并验证里面确实有 `m:oMath`

要点：
- 依赖装不上先看带宽（实测直连 PyPI 约 20 kB/s），开 VPN/代理后重跑，别反复重试同一个卡住的命令
- 样式表路径在 `omml_builder.py` 里是**自动探测**的（也支持环境变量 `MML2OMML`），换机器不用改代码
- 生成/排版时统一用自检脚本最后一行打印的那个解释器路径

## 管线
```
LaTeX 片段 --latex2mathml.convert--> MathML --lxml XSLT(MML2OMML.XSL)--> m:oMath --> 追加进 w:p
```
段落写作时用 `$...$` 切分：偶数段是文字 run，奇数段转公式元素追加到同一个 `<w:p>`（python-docx 的 `p._p.append(...)`，顺序自然保持）。

常用 LaTeX 预替换（latex2mathml 不支持）：`\limits`→空、`\dfrac`→`\frac`、`\displaystyle`→空、`\mathrm{d}`→`d`、`\text{`→`\mathrm{`、`\,`→`\;`。

## 必须自己造 OMML 的三种结构
`latex2mathml` 对 `\begin{pmatrix}` 等环境的 **换行符 `\\` 处理有 bug**（会把多行塞成一行）。必须自己解析：
1. 正则抓块：`\\begin\{(pmatrix|vmatrix|bmatrix|matrix|cases)\}(.*?)\\end\{\1\}`（re.S）
2. 切行：`body.split(chr(92)*2)`（**不要写正则，用 `chr(92)` 拼**，见坑 2）
3. 切列：`row.split('&')`，每个单元格单独转成 m:oMath 的 children，塞进 `m:e`
4. 组装 `m:m > m:mr > m:e`；带括号的再套一层 `m:d`（`m:dPr` 里 `m:begChr`/`m:endChr`：pmatrix 圆括号、vmatrix 竖线、bmatrix 方括号、cases 左花括号+右空）

可直接复用的实现见 `references/omml_builder.py`。

## 验收（交付前必做）
1. 数 `word/document.xml` 里的 `<m:oMath` 个数，核对题号 1..N 无缺
2. Word COM 导 PDF：PowerShell `New-Object -ComObject Word.Application` → `$doc.ExportAsFixedFormat($pdf,17)`；`$word.Documents.Open($path)` **不要传第三个参数（ReadOnly）**，传了会 COMException
3. pymupdf 渲染每页 PNG（dpi≈120），**自己用眼睛看图**：矩阵行列、括号、分段函数大括号、有没有错行
4. 数学答案用 sympy（符号积分/solve）+ mpmath.quad 数值复核；符号引擎算不出的（对称代换型定积分）用数值积分对一下
5. 交付前跑三件套：① `references/check_cjk_math.py <内容模块>`（公式里夹没夹汉字，必须 0 处）
   ② `references/check_omml.py <docx…>`（**最重要**：从 docx 里抽每段公式文字，查 LaTeX 宏名残留，
   出现 `dfrac/frac/mathrm/times/sigma` 这类就是公式压根没转成功，必须 0 处）
   ③ 逐页看图 + 字体体检（pymupdf 逐 span 查字体，出现 `MS Mincho`/`MS Gothic` 即不合格）

## Common Pitfalls
1. **heredoc 里的反斜杠会被折叠**：`python - <<'EOF'` 里写 `\\` 到 Python 里可能只剩一个 `\`，拿这种测试字符串得出的结论是错的（本次为牠白绕两圈）。要测含反斜杠的代码：用 write_file 落盘成 .py 再跑。
2. **脚本里的反斜杠字面量被多转义**：patch/write_file 写 `'\\'` 有时变 4 个。稳妥写法：`chr(92)*2`；写完用 `repr()` 打印那一行确认。
3. **PowerShell .ps1 含中文路径必须存成 UTF-8 with BOM**（Windows PowerShell 5.1 默认按 GBK 读 .ps1，中文路径会乱码 → COMException）。转法：`open(p,'w',encoding='utf-8-sig').write(s)`。
4. **pip 卡住先查网速，不要怪环境**：实测 3.14 和 3.11 都有 lxml wheel，卡住的真实原因是国际带宽慢（约 20 kB/s）+ ReadTimeout。判断方法：`pip list | grep lxml` 看装没装，同时测一下下载速度；开了 VPN 后同一条命令几秒就完。别把「装不上」归因到解释器版本。
5. **公式字体**：OMML 由 Word 用 Cambria Math 渲染，正文 run 设宋体+Times New Roman（`w:rFonts` 的 ascii/hAnsi/eastAsia 三个都要设）。
6. 打开 .docx 若公式变方块，检查元素命名空间是不是 `http://schemas.openxmlformats.org/officeDocument/2006/math`。
7. **不要写「假定依赖已装」的脚本**：技能自带的 `bootstrap_env.py` 就是为此存在；新机器/新用户先跑它再出卷。脚本里调外部命令（`py`、`powershell`）必须 try/except 兜底——本机没有 `py` 启动器，没兜底就直接 FileNotFoundError 挂掉。
8. **正文里不要用 ✔/✏/emoji 这类符号字符**：写解析时手滑用了一个 ✔，Word 为显示它嵌入了整个回退字体，导出的 PDF 从 250 KB 涨到 4.3 MB，而且在别人机器上很可能显示成方块。要表达「正确/一致」就用汉字（如“与结果一致”）；引号用中文 “” 而不是「」。交付前检查：对比各份 PDF 体积，若某一份明显偏大就查 `get_fonts()`；也可在生成前扫一遍内容里的非中英文字符（只留 Ⅰ Ⅱ Ⅲ 这类常规罗马数字）。
9. **公式里绝不能夹汉字**（比上一条更隐蔽）：分段函数写成 `\begin{cases}...\\0,&其它\end{cases}` 时，“其它”落在 OMML 里（按 Cambria Math 渲染），Cambria Math 没有汉字，Word 会回退到日文字体 **MS Mincho**，PDF 里那两个字段字变怪/变方框，而页面其他部分看不出异常。
   体检办法（必须做）：`pymupdf` 逐 span 查字体，出现 `MS Mincho`/`MS Gothic` 就是命中：
   ```python
   for pg in fitz.open(pdf):
       for b in pg.get_text('dict')['blocks']:
           for l in b.get('lines', []):
               for s in l['spans']:
                   if 'Mincho' in s['font'] or 'MS ' in s['font']:
                       print(pg.number, s['font'], repr(s['text']))
   ```
   根治：中文一律移到公式外面。分段函数用纯数学写法，如 `\begin{cases}\frac{2x}{\theta^{2}},&0<x<\theta\\0,&x\notin(0,\theta)\end{cases}`；
   确实要写中文说明就放在 `$...$` 之外的正文里。排版前先跑一个“$...$ 里有没有汉字”的扫描脚本，命中数为 0 才准排版。
10. **自定义分词时，加粗里套公式会被吞掉**：若排版器同时支持 `$公式$` 和 `**加粗**`，用正则 `(\$[^$]*\$|\*\*[^*]*\*\*)` 切分时，`**求 $A$ 端转角**` 会先被当成一个加粗整段，里面的 `$A$` 就变成普通文字输出去——页面上直接印出裸 LaTeX（`times`、`dfrac`、`mathrm` 这类斜体字母串），而公式计数、字体体检都不报错，只有逐页看图或扫“裸宏名”才看得出。
    正确做法：写递归分词器（遇到 `**` 找到配对的 `**`，对内层再用同一套规则处理，加粗标记向下传递），不要把正则拆成二选一。
    验收时必须多扫三项：残留 `$` 个数、残留 `**` 个数、裸宏名（`times` / `dfrac` / `mathrm` / `displaystyle` / `leq` / `sigma`）个数，三项全为 0 才合格：
    ```python
    t = ''.join(pg.get_text() for pg in fitz.open(pdf))
    print(t.count('$'), t.count('**'), sum(t.count(w) for w in ('times','dfrac','mathrm','displaystyle')))
    ```
11. **写完含反斜杠的检查脚本要落盘再跑**：`python -c "..."` 或 heredoc 里的 `$`、`\\` 会被 shell 先吃掉一层，扫描结果会假阴性（写过正则查 $...$ 的脚本，内联版报告 0 处，落盘版才查出真问题）。
12. **内容模块里的 LaTeX 必须写在 raw 字符串里**（`r'...'`）。写成普通字符串时 Python 会先吃掉一层转义：`\a` 变 BEL(0x07)、`\f` 变换页、`\b` 变退格，lxml 解析时报 `XMLSyntaxError: PCDATA invalid Char value 7`——得看报错值反推才能找到，很难一眼看出。
    另一类同源错误：整份模块的反斜杠被写成了**两个**（`\\dfrac`），latex2mathml 会把 `\\` 当换行、把 `dfrac` 当一串变量，页面上就印出斜体字母串（实际踩到过：整卷 90 处公式全废）。
    自检：两连反斜杠计数应当为 0（除非确实要写矩阵行分隔符）。
13. **抓“公式没转成功”不能用 ASCII 字符串匹配 PDF 文字**：PDF 里坏掉的字母是**数学斜体字符**（U+1D461 等），`text.count('times')` 永远是 0，字体体检也不报（Cambria Math 有这些字形，也没触发 Mincho 回退）。
    必须从 **docx 的 OMML** 里抽 `m:t` 文字来查，并使用字母边界正则（`(?<![A-Za-z])int(?![A-Za-z])`），否则 `sin t` 渲染成 `sint` 会误报 `int`。现成脚本：`references/check_omml.py`。
14. **两个现成工具 + 一道护栏**（都在 `references/`）：
    - `normalize_module.py`：把内容模块里的两连反斜杠压成一个（写多了、多转义一层时用）。
      **不要**让它自动给字符串补 `r` 前缀——早期版本这么干，把 `\'` 这种转义引号改成了 `\r'`，
      整个文件语法错误（实际踩到过）。LaTeX 一律自己写成 raw 字符串 `r'...'`。
    - `check_omml.py`：公式体检（见第 13 条）。
    - 护栏：排版器在导入内容模块前会检查“有两连反斜杠且不含 `\begin{`”，命中就**拒绝排版**并提示先跑 normalize_module.py。
    经验：用 write_file 写文件**不会**额外加倍反斜杠；模块里出现两连反斜杠就是自己写的时候多打了一个。

## 考研数学试卷规格（出卷时直接照抄）
- 满分 150 分，考试时间 180 分钟（数一/数二/数三一样）
- 结构：选择题 1–10 每小题 5 分共 50 分；填空题 11–16 每小题 5 分共 30 分；解答题 17–22 共 70 分（17 题 10 分，18–22 各 12 分）
- 数一科目分布（2021 年起新格式，已用 2015–2026 真题核验）：选择 高数 4 + 线代 3 + 概率 3；填空 高数 4（11–14）+ 线代 1（15）+ 概率 1（16）；解答 高数 4（17–20）+ 线代 1（21）+ 概率 1（22）。切勿写成“选择 6 高 2 线 2 概”（前五套就是这么写错的）
- 卷头写明「非历年真题」的模拟标注，别让主人误当真题
- 交付时同目录放一份导出的 PDF，方便直接打印
