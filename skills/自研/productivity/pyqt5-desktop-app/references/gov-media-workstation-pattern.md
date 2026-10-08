# 政务全媒体工作台 v1.1 —— 完整实现模式

## 适用场景
为党政宣传单位/报社开发带AI能力的桌面工具，目标用户是非技术人员（记者、编辑、领导）。

## v1.1 相比 v0.2 的核心变化
- ❌ 不用API → ✅ 接入 DeepSeek/通义/GLM/Kimi API
- ❌ 不让用户编辑文件 → ✅ 资源文件外置（用户可自由编辑模板库.json、金句库.json）
- ❌ 功能只有检查 → ✅ 新增 AI润色 + AI写作 + 金句库 + 数据看板
- ❌ 无版本号 → ✅ 窗口标题/横幅/文件名统一标注 v1.1

## 功能模块（8个Tab）

### ✨ AI润色 Tab
- 粘贴稿件 → 选风格 → 一键AI改写
- 5种风格：正式公文风 / 精炼压缩 / 通俗易懂 / 政务宣传 / 反AI味
- 结果+修改说明分栏显示
- 导出Word / 复制 / 替换原文

### ✍️ AI写作 Tab
- 选文种（15种：会议通知/工作通报/工作方案/讲话稿/请示/函等）
- 输入要点 → AI生成完整公文
- 字数控制选项
- 系统提示词基于 official-document-skill（GitHub 214★）

### 🔍 安全检查 Tab（v0.2保留+升级）
- 内置30+敏感词规则（禁用/慎用/规范/时效）
- 一键检查：原文标注+分类报告+统计
- **新增**：AI辅助分析按钮（调API分析内容质量）

### 📖 词库管理 Tab（v0.2保留）
- 可增删敏感词、修改类型、恢复默认

### 📋 模板排版 Tab（v0.2模板库+智能排版合并）
- **结构化编辑模式**：双击模板→自动拆成命名模块（标题/副标题/正文/结尾等）  
- 每个模块显示为 **【模块名】标签 + 字体|字号|加粗格式栏 + 输入框**，用户逐模块填写并设格式  
- 24个模板带示例内容，6大分类：会议类/活动类/公文类/人物类/宣传类/其他  
- 右侧全局行距控制  
- 顶部「导入字体」按钮  
- 导出Word时按每个模块独立设置的字体/字号/加粗生成  
- **数据来源**：`资源库/模板库.json`（用户可编辑）

> 注：旧版「模板库」和「智能排版」两个独立Tab已合并为这一个Tab。每个模块自带格式控制，不再需要单独排版操作。

### 💎 金句库 Tab（v1.1新增）
- 领导金句（开头引用/表态承诺/部署要求/结尾收束/成语短语）
- 政务新媒体标题库
- **用 QListWidget 展示**（双击复制到剪贴板），比 QPushButton+QScrollArea 更稳定
- 底部状态栏显示加载结果（"✅ X条金句已加载"或错误原因）
- 支持刷新按钮（用户改完JSON后刷新）
- **数据来源**：`资源库/金句库.json`（用户可编辑）

### 📊 数据看板 Tab（v1.1新增）
- 统计数据（润色/写作/检查/导出次数）
- 完整使用说明
- 资源文件管理指引

## 外部资源目录架构

```
安装目录/
    ├── 政务全媒体工作台.exe
    ├── config.json            # API Key + 厂商配置
    ├── 敏感词库.json           # 敏感词规则
    ├── 资源库/
    │   ├── 模板库.json         # 24个模板（用户可编辑）
    │   ├── 金句库.json         # 30+金句（用户可编辑）
    │   └── 字体库/             # 用户导入的.ttf/.otf字体文件
    └── 输出/                   # Word导出默认目录
```

### 加载代码
```python
def get_resource_dir():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), '资源库')
    else:
        return os.path.join(os.path.dirname(__file__), '资源库')

def load_resource_json(filename, default_value):
    path = os.path.join(get_resource_dir(), filename)
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data = {k: v for k, v in data.items() if not k.startswith('_')}
                return data
    except: pass
    return default_value
```

⚠️ `get_resource_dir()` 在打包 exe 后不要用 `..` 回退——Inno Setup 安装后 exe 和资源目录都在 `{app}` 下。

## 模板结构化解析算法

```python
def parse_sections(self, content):
    lines = content.strip().split('\n')
    sections = []
    current_name = '正文'
    current_content = []
    
    section_keywords = ['标题', '副标题', '本报记者', '正文', '结尾', '出处',
                       '导语', '开头', '背景', '要求', '部署', '强调',
                       '一、', '二、', '三、', '四、', '五、']
    
    def is_section_header(line):
        for kw in section_keywords:
            if line.strip().startswith(kw) or line.strip().startswith(f'【{kw}】'):
                return kw
        return None
    
    for line in lines:
        stripped = line.strip()
        if not stripped: continue
        header = is_section_header(line)
        if header:
            if current_content:
                sections.append((current_name, '\n'.join(current_content).strip()))
            current_name = header
            # 提取冒号/等号后的内容作为初始填充
            content_part = stripped
            for sep in ['：', ':', '】']:
                if sep in content_part:
                    content_part = content_part[content_part.index(sep)+len(sep):].strip()
            current_content = [content_part] if content_part and content_part != header else []
        else:
            current_content.append(stripped)
    if current_content:
        sections.append((current_name, '\n'.join(current_content).strip()))
    if not sections:
        sections.append(('正文', content.strip()))
    return sections
```

## 字体库管理

### 目录
`资源库/字体库/` — 存放用户导入的 .ttf/.otf/.ttc 文件

### 导入流程
1. 用户点「导入字体」→ QFileDialog 选择字体文件
2. `shutil.copy2(源文件, FONT_DIR/文件名)` 复制到字体库
3. `QFontDatabase.addApplicationFont(路径)` 注册到 Qt
4. 刷新所有 QComboBox 字体下拉框

### 字体加载代码
```python
FONT_DIR = get_resource_path('字体库')

def get_custom_fonts():
    ensure_font_dir()
    fonts = []
    for f in os.listdir(FONT_DIR):
        if f.lower().endswith(('.ttf', '.otf', '.ttc')):
            font_path = os.path.join(FONT_DIR, f)
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id >= 0:
                for fn in QFontDatabase.applicationFontFamilies(font_id):
                    fonts.append((fn, font_path))
    return fonts
```

## AI 系统提示词（基于 official-document-skill）

```python
OFFICIAL_SYSTEM_PROMPT = """你是一位精通中文公文写作的资深笔杆子……
## 核心原则
1. 事实优先：每个判断必须有事实支撑，不编造数据/人名/文件名
2. 克制评语：宁可稳妥不要拔高
3. 反AI味：避免四字词堆叠、机械排比、万能结尾
4. 结构规范：严格按照所选文种格式
5. 具体明确：谁、做什么、怎么做、什么时间、什么标准

## 必须避免的问题
- 空泛套话、过度拔高、虚假具体、AI连接词过密、万能结尾

## 写完后自检
- 这篇公文被退回最可能是什么原因？
- 有没有哪句是只有意义没有事实的？"""
```

## Inno Setup 安装包脚本要点

```iss
[Setup]
DefaultDirName=D:\政务全媒体工作台
OutputBaseFilename=政务全媒体工作台_v1.1_安装程序
Compression=lzma
WizardStyle=modern

[Dirs]
Name: "{app}"; Permissions: users-modify
Name: "{app}\资源库"; Permissions: users-modify
Name: "{app}\输出"; Permissions: users-modify

[Files]
Source: ".\dist\政务全媒体工作台.exe"; DestDir: "{app}"
Source: ".\资源库\*"; DestDir: "{app}\资源库"; Flags: recursesubdirs
Source: ".\config.json"; DestDir: "{app}"; Flags: onlyifdoesntexist
Source: ".\敏感词库.json"; DestDir: "{app}"; Flags: onlyifdoesntexist
```

关键：资源文件用 `onlyifdoesntexist` 防止覆盖用户已修改的内容。目录权限设 `users-modify`。

## 版本规则
- 窗口标题、顶部横幅、exe文件名、安装包文件名四者版本号一致
- 文件名格式：`应用名_vX.X_便携版.zip` / `应用名_vX.X_安装程序.exe` / `应用名_vX.X.exe`
- 每次更新四处同步改
