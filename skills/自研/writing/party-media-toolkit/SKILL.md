---
name: party-media-toolkit
description: 党政宣传/政务报道类全媒体工具开发。覆盖敏感词库管理（可增删）、政务公文模板、一键排版（标题/副标题/记者/正文/结尾/出处分区）、稿件统计分析、Word文档导出。全部本地运行，打包为exe交付。
trigger: 当用户说"政务工具""全媒体工作台""党政宣传""报社工具""敏感词""政务报道模板""公文AI润色""AI写作""政务skill"时触发
---

# 党政宣传全媒体工具开发技能

## 核心原则

### 版本号规范
- 每次更新代码、文件、exe时，必须带上版本号（如 v1.0、v1.1）
- 在文件名、窗口标题、底部状态栏、导出文件默认名中都体现版本号
- 让用户一眼能看出是否新版本，避免混淆

### Skill转exe模式（核心模式）
用户总结的金句：**"这不就相当于做了一个程序版本的skill吗"**

Hermes Skill 是"让AI自己会干"，exe是"让不会用AI的人也能用AI"——殊途同归。

转换步骤：
1. 找到对应领域的优质 Skill（如 GitHub 上的 official-document-skill）
2. 将 Skill 的 system prompt / 知识规则提取出来，写入 AI 调用的 system message
3. 用 PyQt5 搓界面，把 Skill 的功能变成按钮和输入框
4. 接通用 OpenAI 格式的 API（DeepSeek / 通义 / GLM / Kimi 等）
5. 打包成 exe 交付，用户双击即用，不依赖 Hermes 命令行

优势：Skill 赚口碑（免费发布），exe 赚收入（卖给不会用命令行的用户）

### 云端资源自动更新（用户提出的好方案）
既然 exe 能联网调 API，不如让资源库也联网自动更新。

架构：
```
exe启动时
  → GET 云端/version.json 检查版本
  → 如果云端版本 > 本地版本，下载最新资源文件
  → 替换本地资源（敏感词库.json、模板库.json、金句库.json）
  → 用户无感，下次打开直接用最新的
```

资源放在 GitHub/Gitee 公开仓库即可，纯 JSON 文件，不需要服务器。
用户只需在网页上编辑文件→所有已售出的 exe 下次启动自动更新。

这个功能是卖点之一——"买一次，永久自动更新知识库"。

### 产品思维：有了不等于值钱（每次迭代都要问自己）
- 功能做出来只是开始，让用户愿意掏钱才是目标
- 核心追问：**"这个东西有了，但它真的行吗？"**
- 常见的"有了但不行"陷阱：
  1. 模板有了，但全是空壳子没有示例内容 → 用户拿到手还得自己填？那要模板干啥
  2. 敏感词检查有了，但查出来不告诉用户改啥 → 查了等于白查
  3. 功能堆上去了，但UI太素 → 领导打开第一眼就觉得"这不值钱"
  4. 能导出了，但要手动填6个区 → 用户想要一键搞定，不是填一堆框
  5. AI接上了，但没想好API Key怎么给用户 --> 要提供注册教程+体验模式
- 功能做出来只是开始，让用户愿意掏钱才是目标
- 四个让用户买单的要素：
  1. **核心功能让人离不开**：AI润色、敏感词检查（政治错误是命门）
  2. **外观像样**：领导打开第一眼就觉得"值这个价"
  3. **数据统计可汇报**：本月写稿XX篇、查出敏感词XX处——领导向上汇报的刚需
  4. **门槛低到离谱**：解压→双击→填一次Key→开用，附带纸质说明书

### 参考资源（每次开干前先搜）
- GitHub 搜 `official-document-skill` (214★) — 基于数百篇人民日报文章的公文写作Skill，含12种法定公文+15种事务文书+反AI味规则
- GitHub 搜 `official-document-writing-skill` (213★) — 基于GB/T 9704-2012国家标准的公文写作
- 这两个 Skill 是现成的公文知识库，可以直接转换为桌面版 exe 的 AI 润色规则

### 多Provider架构（不锁死在DeepSeek）
- config.json 配 api_url + api_key + model，支持一键切换
- DeepSeek（最便宜）/ 通义千问 / GLM-4 / Kimi / 文心 都兼容 OpenAPI 格式
- 同一份代码，换三行配置就能换"大脑"

## 一、敏感词检测模块

### 词库结构
- 每项：词 + 类型 + 说明
- 类型分四类：**禁用**（必须修改）、**慎用**（建议修改）、**规范**（政治表述）、**时效**（时间性检查）
- 词库存储在JSON文件中，程序启动时加载

### 管理功能（界面化，不让用户碰文件）
- 添加词：输入框+类型选择+说明（可空）
- 删除词：表格选中行→删除
- 恢复默认：一键重置到内置词库
- 修改后自动保存，实时生效

### 检查流程
1. 用户粘贴稿件
2. 点击「一键安全检查」
3. 程序遍历词库，在稿件中检索每个词
4. 输出按类型分组的检测报告
5. 在原文中用不同颜色标注命中词（禁用红/慎用橙/规范黄/时效蓝）

## 二、政务模板库模块

### 分类体系
- 会议类（常委会/常务会/专题会/座谈会/动员会/视频会/推进会/汇报会）
- 活动类（调研/视察/慰问/签约/开工/揭牌/启动/主题/走访）
- 公文类（通知/通报/简报/纪要/方案/报告/整改/汇报）
- 人物类（讲话稿/先进事迹/人物通讯/表彰）
- 宣传类（公众号推文/短视频脚本/标语/公益文案）
- 其他（贺词/总结/心得体会/倡议书/公开信）

### 模板格式
- 每行一个区段标记：`【标注】内容` 或 `【内容】`
- 关键标记：`【标题】`、`【副标题】`、`【本报记者】`、`【正文】`、`【结尾】`、`【出处】`
- 不填的分区自动忽略，向前递进

## 三、一键排版模块（分区排版）

### 六个分区
| 分区 | 用途 | 典型格式 |
|------|------|----------|
| 标题 | 主标题 | 方正小标宋 22pt 居中 加粗 |
| 副标题 | 副标题 | 楷体 16pt 居中 |
| 本报记者 | 记者署名 | 楷体 12pt 居中 |
| 正文 | 稿件正文 | 仿宋 12pt 首行缩进2字符 |
| 结尾 | 结束语 | 仿宋 12pt |
| 出处 | 来源标注 | 仿宋 10pt 灰色 右对齐 |

### 格式设置
- 每个分区独立：字体（下拉选）、字号（8~48范围）、加粗（0/1）
- 全局：行距（0~5，步长0.1）、段前/段后（0~50px）
- 不填的分区自动隐藏不显示

## 四、Word文档导出

### 导出方式
- 用 `tkinter.filedialog.asksaveasfilename` 弹出保存对话框（比PyQt的QFileDialog打包后更稳定）
- 默认扩展名 `.docx`
- 自动判断段落格式：标题用方正小标宋22pt居中、副标题用楷体16pt居中、正文用仿宋12pt首行缩进

### 打包为exe
```bash
pyinstaller --onefile --windowed --name "政务全媒体工作台" main.py
```
- 用 `execute_code` 调用PyInstaller通过d:/python/python.exe执行
- 打包前清理旧build目录和spec文件

## 五、AI润色模块（v1.0新增）

### 功能定位
- 把大白话改成规范的政务文风
- 支持5种润色风格：正式公文风、精炼压缩风、通俗易懂风、政务宣传风（公众号）、反AI味润色
- 反AI味润色额外输出"如果被退回最可能的原因"

### 技术实现
- 通过 `urllib.request` 调 DeepSeek API（OpenAI兼容格式）
- 每次请求通过**独立线程**（threading.Thread）发送，防止 UI 卡死
- 配 QProgressBar（setMaximum(0) = 无限循环动画）提示用户等待
- 在 config.json 中配 `api_key` + `api_url` + `model`，支持一键切换提供商
- 设置对话框提供快捷切换按钮：DeepSeek / 通义千问 / GLM-4 / Kimi

### API设置对话框设计
- Key 用 Password 模式（不明文显示）
- 提供预设按钮一键填 URL 和模型名
- 提示文字：\"Key 存储在本地 config.json，不会上传到第三方\"
- 支持运行时修改，修改后立即生效

### Prompt设计要点（参考 official-document-skill 的反AI味规则）
1. **事实密度**：删除形容词和四字口号后，段落仍需回答"谁做了什么、怎么做、做到什么程度"
2. **判断强度匹配**：证据弱就降级判断（"已启动"≠"重大突破"）
3. **抽象词控制**：每个抽象词后面必须跟具体内容（"赋能"后面要跟赋能对象和方法）
4. **禁用清单**：堆四字词、万能结尾（"谱写新篇章"）、AI连接句式（"不仅…而且…"）
5. **文种匹配**：通知不能写成讲话稿，请示不能夹带汇报事项

### 评分自查（输出前跑一遍）
- 低于80分要重写
- 关键问题："如果这篇公文被退回，最可能被批评哪里像AI写的？"

## 六、AI智能写作模块（v1.0新增）

### 输入方式
- 用户输入3-5个要点/提纲
- 或用户选择模板类型+填写关键信息

### 输出
- 完整的政务报道/公文/讲话稿
- 附带「需补充信息」列表（当关键事实缺失时）

### 典型场景
- 写一份常委会会议报道，议题是XX
- 帮我写一份关于XX的工作总结，要点如下：
- 写一篇调研报告，去了XX地方，发现XX问题，建议XX

### 支持的文种（15种）
会议通知、工作通报、工作方案、工作总结、调研报告、讲话稿、汇报材料、学习心得体会、倡议书、微信公众号推文、宣传稿/简报、请示、函、表彰通报、先进事迹报道

### 字数控制
通过下拉选择：不限 / 500字以内 / 800字左右 / 1000-1500字 / 1500-2000字
在 prompt 中直接指定，无需额外处理

### 自检输出
每次生成完成后，附带一句自评
让用户知道AI不是盲目的，也引导用户检查修改

## 七、产品包装要素（让用户买单）

### 视觉升级
- 政务蓝主题色（#2B579A为主色）
- 启动页显示单位名称（"XX单位·AI政务工作台"）
- 导出Word自带红头格式

### 数据统计Dashboard
- 本月AI辅助写稿 XX 篇
- 检查出敏感词 XX 处
- 已排版 XX 篇
- 这个功能是让领导觉得"值得买"的关键——他要向上汇报

### 使用门槛
- 附带一张打印好的说明书（三步走，带截图）
- API Key 获取教程（注册→充值→复制→粘贴，每一步截图说明）
- config.json 后备方案：支持用户自己配或管理员统一配

## 八、金句库模块（v1.1新增）

### 功能定位
- 一个内置的公文常用金句/短语库，写稿时一键复制粘贴
- 分场景分类：开头引用、表态承诺、部署要求、结尾收束、常用成语短语、政务新媒体标题
- 用户点击金句按钮→自动复制到剪贴板

### 数据存储
- 存储在 `资源库/金句库.json`，用户可自由增删
- 格式：按分类组织，每个分类下按子场景分组的字符串列表
- 程序启动时自动加载，修改后重启生效，无需重新打包

### UI设计
- 使用 QScrollArea 包裹内容，避免长列表溢出
- 每个分类用 QLabel 标题（`▎分类名`）加底部加粗边框线分隔
- 每个子场景用小号蓝色 QLabel 作为段标题
- 每条金句是一个 QPushButton（📋 + 金句文本），点按式样式（背景浅灰+边框），Cursor 设为手型
- 按钮用 `setCursor(Qt.PointingHandCursor)` 提示可点击
- 点击后触发复制到剪贴板 + 弹窗提示"已复制"
- lambda 绑定金句内容时用默认参数捕获值：`lambda checked, t=item_text: self.copy_jinku(t)`

## 九、外部资源文件架构（v1.1重构）

### 设计目标
将硬编码在 Python 代码中的模板库、金句库等资源文件抽取到外部 JSON 文件，使用户可自由增删，开发者更新时只需替换资源文件。

### 目录结构（安装后）
```
安装目录/
├── 政务全媒体工作台.exe    ← 主程序
├── config.json             ← API 配置
├── 敏感词库.json            ← 敏感词
├── 资源库/                 ← 用户可自由编辑！
│   ├── 模板库.json         ← 公文模板
│   └── 金句库.json         ← 金句短语库
└── 输出/                   ← Word导出默认路径
```

### get_resource_dir() 模式（关键设计）
```python
def get_resource_dir():
    """兼容开发环境和打包后的exe"""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), '资源库')
    else:
        return os.path.join(os.path.dirname(__file__), '资源库')
```

⚠️ 不要用 `..` 回退——Inno Setup 安装后 exe 和资源目录都在 `{app}` 下，没有嵌套关系。用 `..` 会指向父目录导致资源加载失败。

原理：`sys.frozen` 在 PyInstaller 打包后为 True，此时 `sys.executable` 指向 exe 本身。exe 和资源库在同一个目录下。

### 外部资源加载函数
```python
def load_resource_json(filename, default_value):
    """从资源目录加载JSON文件，失败则返回默认值"""
    path = get_resource_path(filename)
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 去掉私有字段（_开头，用于注释）
                if isinstance(data, dict):
                    data = {k: v for k, v in data.items() if not k.startswith('_')}
                return data
    except:
        pass
    return default_value
```

关键设计决策：
- JSON 文件中以 `_` 开头的键视为注释/元数据，加载时自动过滤
- 加载失败时返回默认值，不崩溃
- 文件不存在时使用内置 fallback

### 用户可编辑的 JSON 文件
所有资源 JSON 文件都放在用户能直接编辑的位置，且：
- 文件编码：UTF-8
- 格式：带缩进，方便用户用记事本编辑
- 在程序底部状态栏显示资源目录的绝对路径
- 在数据看板中说明"修改后重启程序即可生效，无需重新打包"

## 十、安装包分发（v1.1新增）

### 分发渠道对比
| 方式 | 怎么做 | 用户体验 | 专业度 |
|------|--------|---------|--------|
| 便携版ZIP | 打包成压缩包发用户 | 解压→双击exe | ⭐⭐ |
| 安装包exe | 用 Inno Setup 编译 | 安装向导→选目录→快捷方式 | ⭐⭐⭐⭐⭐ |

### Inno Setup 安装包制作

#### 安装 Inno Setup
- 下载：https://jrsoftware.org/isdl.php
- 或 winget：`winget install JRSoftware.InnoSetup`

#### ISS 脚本关键配置
```pascal
[Setup]
DefaultDirName=D:\政务全媒体工作台     ; 默认安装目录
PrivilegesRequired=lowest              ; 不需要管理员权限

[Dirs]
Name: "{app}"; Permissions: users-modify
Name: "{app}\资源库"; Permissions: users-modify    ; 用户可写
Name: "{app}\输出"; Permissions: users-modify

[Files]
; 配置文件仅在首次安装时创建（onlyifdoesntexist）
Source: "..\config.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "..\敏感词库.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

[Icons]
Name: "{group}\资源库文件夹"; Filename: "{app}\资源库"  ; 快捷方式直达资源目录
```

关键设计：
- `PrivilegesRequired=lowest` → 不需要管理员权限，普通用户可装
- `onlyifdoesntexist` 标志 → 首次安装创建配置文件，后续升级/修复时保留用户已配置的 Key
- 安装完成后创建「开始菜单→资源库文件夹」快捷方式
- 卸载时删除 config.json，保留用户输出文件

#### 编译命令
```bash
ISCC.exe setup.iss
```

#### 目录结构关系（编译时）
```
项目根目录/
├── installer/
│   ├── setup.iss              ← 安装包脚本
│   ├── 编译安装包.bat          ← 一键编译脚本
│   └── 安装包输出/
│       └── 政务全媒体工作台_v1.1_安装程序.exe  ← 最终产物
├── dist/
│   └── 政务全媒体工作台.exe    ← PyInstaller 打包的 exe
├── 资源库/
│   ├── 模板库.json
│   └── 金句库.json
├── config.json
└── 敏感词库.json
```

ISS 脚本中用 `..\` 引用父目录的文件。

### 便携版 ZIP 制作
用 Python zipfile 模块打包（比手动压缩更可控）：
```python
with zipfile.ZipFile('xxx.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(portable_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, portable_dir)
            zf.write(file_path, arcname)
```

ZIP 内同时包含使用说明.txt（带 API Key 获取教程和功能介绍）。

### 用户拿到手的完整体验
1. 给用户发一个 `setup.exe`（约 45-50MB）
2. 双击 → 安装向导 → 选目录 → 自动建文件夹 → 桌面快捷方式
3. 打开 → 设置 API Key → 开用
4. 以后想加模板 → 直接编辑 `资源库/模板库.json`
5. 想重新打包 → 改代码 → 运行 `installer/编译安装包.bat`

## Pitfalls
- PyQt5打包后用QFileDialog可能不弹窗，改用tkinter的filedialog
- 敏感词库要内置在代码中（DEFAULT_WORDS常量），同时支持用JSON文件持久化用户修改
- 所有参数必须可调，不能写死——一线工人/编辑需要根据实际情况调整
- 界面要傻瓜式，不能让用户碰配置文件
- 打包时报错 `fixedWidth` 是QLabel的未知参数，需移除
- matplotlib打包后可能崩溃，改用纯PyQt5绘制
- 导出Word时注意中文字体名要通过 `run.element.rPr.rFonts.set(qn('w:eastAsia'), font_name)` 设置
- **AI请求必须在子线程中执行**，否则UI会卡死。用 threading.Thread + 回调更新UI
- **QProgressBar无限循环动画**：`setMaximum(0)` 让进度条变成跑马灯效果，告诉用户"在跑了"
- **API Key获取是最大门槛**：要让用户自己注册（写三步说明书），同时提供体验模式（用你自己的Key但限频）
- **API Key字段用Password模式**：`setEchoMode(QLineEdit.Password)` 防止别人看到
- **联网API调用必须设超时**：`timeout=60`（润色）/ `timeout=120`（写作），防止卡死
- **不要锁死在DeepSeek**：用 OpenAPI 兼容格式，config.json 三行配置就能换提供商
- **启动时检测API配置**：如果没配Key，弹窗提醒用户配置，不硬性阻止使用其他本地功能
