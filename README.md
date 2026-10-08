# 考研模拟卷出题技能包（Hermes Skills）

用 Hermes Agent 出考研模拟卷的一整套技能与排版管线。作者自撰，公开分享，随取随用。

## 里面有什么

| 目录 | 作用 |
|---|---|
| `kaoyan-paper-pipeline/` | 出卷全流程：第 0 步推「到底考什么」→ 取考纲 → 取真题 → 做命题地图 → 出题 → 核验 → 超纲检查 → 排版交付 |
| `word-math-paper-docx/` | 把 LaTeX 排成 Word **原生公式**（OMML，可在 Word 里直接编辑）的管线，含环境自检脚本 |
| `math-formula-memory/` | 做公式记忆材料（公式卡、默写打卡表）的方法 |
| `math-output-style/` | 面向不熟悉 LaTeX 的使用者，在聊天里怎么规范地写数学 |
| `样例/` | 数学（一）第六、七套模拟卷（docx + pdf）及配套的超纲检查报告 |

## 三个最值钱的东西（都是踩坑换来的）

1. **考试结构先推、别背**：考什么由「学位类型 × 学科门类/专业代码 × 当年该校招生专业目录」决定，不由科目名决定，**也不由全日制/非全决定**。技能里有完整推导链与科目代码规律。
2. **答案不许口算**：所有数值题先用 sympy / mpmath 算出来打印，再排版，两边数字必须对上；能用两种方法互验的必须互验（曲线积分直接算 vs 补线+格林，无偏性用大样本模拟等）。
3. **交付前四关**：
   - `check_cjk_math.py` 扫公式里有没有夹汉字（公式按 Cambria Math 渲染，没汉字 → Word 回退到日文字体 MS Mincho → PDF 出方框。这是实战踩出来的坑）
   - 逐题对大纲做超纲检查（正向映射 + 反向扫黑名单；数一黑名单含一致收敛、单侧置信限、包络/正交轨线、雅可比换元、留数、拉普拉斯变换、若尔当标准形、奇异值/广义逆、含参量积分、随机过程）
   - 公式计数（`word/document.xml` 里 `<m:oMath` 个数）
   - 字体体检 + 逐页看图（pymupdf 逐 span 查字体，出现 MS Mincho / MS Gothic 即不合格）

## 怎么装

把四个技能目录拷进 Hermes 的 skills 目录（Windows 是 `%LOCALAPPDATA%\hermes\skills\`），
`word-math-paper-docx` 放到 `skills/productivity/` 下，两个 math-* 放到 `skills/writing/` 下。

然后建出卷环境：

```bash
python <skill目录>/references/bootstrap_env.py --venv D:/pyenv/kaoyan --mirror https://pypi.tuna.tsinghua.edu.cn/simple
```

依赖：python-docx、lxml、latex2mathml、pymupdf、sympy、numpy。
导 PDF 走 Microsoft Word 的 COM 接口，机器上要装 Word；公式样式表 MML2OMML.XSL 随 Office 安装，脚本会自动定位。

## 使用

对 Hermes 说：「按 kaoyan-paper-pipeline 出一套 <科目> 模拟卷」。
它会先给一张分布表（题号 → 考点 → 分值）让你过目，点头后再排版成 docx + PDF。

## 边界说明

- 本包只针对**数学（一）**给出了完整的出卷明细（`references/math-one-rules.md`）；考数二/数三/英语二/管综 199 等，按 SKILL.md 末尾的说明另建对应的事实文件即可，流程通用。
- 自命题专业课（如 849 材料力学）多数不公开真题，技能里的做法是「用官方考纲 + 指定教材典型题型命题」，并明确标注题型结构为推断。
- 样例卷均为自撰模拟题，**非历年真题**；引用真题仅用于分析命题规律，不随包分发真题原文。
