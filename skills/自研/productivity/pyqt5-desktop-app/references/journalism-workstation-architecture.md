# 全媒体工作台 - Reference Architecture

A PyQt5 desktop app for journalism/media workflow, built for 本地日报社.

## Three-Module Structure

### 1. 采编日历 (Editorial Calendar)
- 二十四节气 display (filtered to upcoming only)
- Configurable news nodes (editable via dialog, persisted to config.json)
- Countdown: weekend + nearest news node
- Tips widget (random selection from curated list)

### 2. 写稿助手 (Writing Assistant)
- **Article assembler**: toggle buttons for 开头/中间/结尾
  - 记者 name field: 2-char names get 2 spaces between characters, 3-char names get none
  - "本报讯（记者XXX）" / "本报讯（通讯员XXX）" as toggle buttons
  - 中间句式 and 结尾句式 as toggle-button strips
  - Clear button resets all toggles
- **Cliche library**: 7 categories, 80+ entries
  - Category filter buttons
  - Keyword search
  - Click-to-copy to clipboard
- **Title generator**: keyword input → 8 template titles → random pick 4
- **Word counter**: real-time, reading time = chars / 300

### 3. 舆情热榜 (Trending Topics)
- Hot keywords (tag display)
- Trending news items (randomized text)
- Editorial direction suggestions
- Publishing stats with gradient banner (今日已发 / 待审 / 退回修改 / 本周总计)

## Configuration
- `config.json` lives next to the exe (resolved via `sys.executable`, NOT `__file__`)
- News nodes format: `{"news_nodes": [{"date": "2月", "name": "本地市两会", "desc": "本地地方两会报道"}]}`
- UI has an inline "编辑节点" button that opens `QInputDialog.getMultiLineText()` for bulk editing
  - Format: one line per node, pipe-separated: `日期|名称|描述`
  - On save: writes to config.json AND refreshes the calendar tab in-place

## Data Sources

### Local (hardcoded)
- 7-category cliche library (80+ entries: 治国理政, 经济发展, 民生保障, 乡村振兴, 文化自信, 党建作风, 奋斗励志)
- Article templates: 开头(记者/通讯员), 中间句式(10条), 结尾句式(6条)
- Title generator templates (8 patterns)
- Editorial tips (5 items)
- Hot keywords (12 items)

### Online (free, no API key)
- **一言 API** `https://v1.hitokoto.cn?c={category}` — free, unlimited
  - `c=d` 文学, `c=i` 诗词, `c=k` 哲学
  - Returns JSON: `{hitokoto, from, from_who}`
  - Implementation: `urllib.request` with 5s timeout, wrapped in try/except
  - Display format: `「{text} —— {author}《{source}》」`
- No other online APIs are currently used (no external data fetching for news/trends)

## Styling
- Red/white gradient header (#c62828 → #e53935)
- Individual module frames use distinct pastel backgrounds
- Tab bar: red selected, grey unselected
- Buttons: red primary, with .active green variant for toggle state
