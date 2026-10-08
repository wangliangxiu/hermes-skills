---
name: math-output-style
description: 向主人输出数学内容时的格式规范。主人看不懂 LaTeX/$/上标符号，必须用汉字描述数学表达式。
---

# 数学输出格式规范

## 适用场景
当你需要向主人展示数学公式、导数、积分、方程等数学内容时。

## 核心规则

### 1. 正式文档（计算书/技术文件）用标准数学符号 + Word 上下标
主人明确要求（2026-08）：公式不用纯汉字描述，要规范书写，
上角标就是上角标，下角标就是下角标，公式后面紧跟每个符号的含义。

- 输出文件用 .docx（python-docx），公式用 run.font.superscript /
  run.font.subscript 实现真正的上/下角标，不用 Unicode 上下标字符
- 公式行居中，符号含义紧随其后缩进列出
- txt 写不出规范上下标，不要用 txt 出公式文档
- 公式风格示例：
  f = Rc ÷ 10（c为下标）
  Qmax = R³ × (vallow ÷ K)^(3/α)（max、allow为下标，3、(3/α)为上标）
  - 立方根写 ³√Q（³ 和 √ 常见字体都支持，不要用 ∛ 可能缺字形）

  - python-docx 实现模板（segments 列表驱动，本会话验证可用）：
    ```python
    def add_formula(p, segments):
        """segments: [(text, 'sup'|'sub'|'')]"""
        for text, st in segments:
            r = p.add_run(text)
            if st == 'sup':
                r.font.superscript = True
            elif st == 'sub':
                r.font.subscript = True
    # 例：Qmax = R³ × (vallow ÷ K)^(3/α)
    add_formula(p, [('Q', ''), ('max', 'sub'), (' = R', ''), ('3', 'sup'),
                    (' × (v', ''), ('allow', 'sub'), (' ÷ K)', ''), ('(3/α)', 'sup')])
    ```

### 2. 对话中口头表达公式时，用汉字辅助（简单公式可符号化）
聊天里不要堆 LaTeX/$/^ 转义，主人看不懂纯符号堆砌：
- 优先：f 等于 Rc 除以 10（Rc 的 c 是下标）
- 简单公式可直接写符号：v = K × (³√Q ÷ R)的α次方
- 不要用 $...$、x^2 这种转义写法

### 3. 分步展示
复杂推导要分步骤写，每步一行，不要挤在一起。

### 4. 文件输出
正式技术文档用 .docx；简单文本记录可用 .txt（纯文字描述）。
