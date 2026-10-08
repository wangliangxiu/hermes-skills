# 维基 / 维基文库 API：取词条正文与古籍原句

触发：查某个典故、神祇、成语、宝物的来历与原文（整理文化素材、给内容或产品找文化根），
或 web_search 返 0 条、web_extract 抓 zh.wikipedia 报后端错时。

## 为什么走 API
- 中文短词在搜索后端常被拆词，返 0 条；不是没资料
- 维基网页版抓取易被 keyless 后端挡下（CRAWL_NOT_FOUND / Unrecognized MCP response shape），
  而同一 URL 用 curl 就是 200
- 网页 HTML 大、导航噪音多；API 的 `extracts` 直接给纯文本正文，好切好引

## 1. 词条正文
```bash
cd "$LOCALAPPDATA/Temp"
curl -s --max-time 25 -x http://127.0.0.1:17890 -G "https://zh.wikipedia.org/w/api.php" \
  --data-urlencode "action=query" \
  --data-urlencode "prop=extracts" \
  --data-urlencode "explaintext=1" \
  --data-urlencode "format=json" \
  --data-urlencode "redirects=1" \
  --data-urlencode "titles=聚寶盆" \
  -o w.json -w "http=%{http_code}\n"
```
- 多标题用竖线：`--data-urlencode "titles=財神|貔貅|石崇"`
- 返回结构：`query.pages.<pageid>.{title, extract}`，`extract` 即正文；页面不存在时 pageid 为负（-1）
- 简体/繁体、重定向都由 `redirects=1` 兜住
- **批量时个别标题 extract 为 len=0**（页面存在）：实测一次抓
  `穷鬼|正月初六|搖錢樹|貔貅` 四个都空，逐个单抓分别得 345 / 464 / 2013 / 2914 字
  → 批量只用来扫，正文一律单条抓

## 2. 猜不准标题名时先搜
```bash
curl -s --max-time 20 -x http://127.0.0.1:17890 -G "https://zh.wikipedia.org/w/api.php" \
  --data-urlencode "action=query" --data-urlencode "list=search" \
  --data-urlencode "format=json" --data-urlencode "srlimit=4" \
  --data-urlencode "srsearch=青蚨"
```
实测："送穷" → `穷鬼`、`正月初六`；"摇钱树" → `搖錢樹 (器具)`；"青蚨" → 无对应词条
（说明该典故维基没有，改走维基文库/古籍）。带括号的标题原样传即可。

## 3. 古籍原句（要引原文时）
换 `zh.wikisource.org`，同一个 action=query 接口：
```bash
... -G "https://zh.wikisource.org/w/api.php" --data-urlencode "titles=搜神記/第13卷" ...
```
实测拿到《搜神记》卷十三整卷纯文本，其中"青蚨还钱"原文：南方有虫名青蚨，取其子母必飞来；
以母血涂钱八十一文、以子血涂钱八十一文，每市物或先用母钱或先用子钱，皆复飞归，轮转无已。
→ 材料里写得出**典名 + 卷次 + 原句**，比引百科可信。

坑（2026-09 实测）：**同名篇目要带作者消歧义**。`titles=送窮文` 只返回 27 字的消歧义页
（列出 `送窮文 (段成式)` / `送窮文 (韓愈)`），必须传 `送窮文 (韓愈)` 才拿到正文
（元和六年正月乙丑晦；五鬼名：智穷、学穷、文穷、命穷、交穷）。抓到极短的 extract 先怀疑
是消歧义页，别当成"原文就这么短"。

## 4. 解析
```python
import json
d = json.load(open(path, encoding="utf-8"))
for pid, p in d["query"]["pages"].items():
    print(p.get("title"), (p.get("extract") or "")[:1500])
```
- 终端里别跑 `python -c`（会被审批拦，纯 curl 放行），解析一律走 execute_code
- 大 JSON 别整段 print，只打需要字段

## 5. 这类调研的汇报形态
文化素材最怕"把传说当典籍"，按三档标源：
- **典籍有载**：《搜神记》《尚书》《史记》《礼记》这类能引原句的，写典名+卷次
- **民间说法/民俗**：有文献出处但属传说（沈万三聚宝盆出自周人龙《挑灯集异》；
  "刘海戏金蟾，步步钓金钱"见于工艺/民俗介绍）
- **后世演绎**：近代才流行的说法（"貔貅是龙第九子、没有肛门只进不出"——
  典籍里貔貅只是猛兽名），写材料时不能当典故

另外：
- 单列一节"不要碰"：历史上有争议的神祇（五通神在宋代志怪里半是邪神）、
  宗教修法本尊（藏传五姓财神）、赌性玩法——说清为什么，别等使用者自己踩到
- 结论按"能变成什么机制/玩法"组织，不堆典故；末尾附出处清单
- **"民间说法"这一档也要落到权威出处**（实测可用）：中国非物质文化遗产网 ihchina.cn
  （年俗条目，如《春节礼俗之正月初五赶五穷》）、新华网/人民网科普/光明网/中国天气网的
  年俗稿、故宫博物院 dpm.org.cn 词条库（人物类，如"刘海蟾"）、拍卖行等机构文章
  （工艺寓意类，如苏富比写"刘海戏金蟾，步步钓金钱"）。只找到自媒体转述的，降级为"待核实"
- **生僻民俗名要交代通行度**：像"赶五穷"这类只在部分地区和年俗正式表述里用的叫法，要写明
  "并非各地都这么叫"（使用者本人就没听过，会当场质疑）——地区性叫法当常识写会翻车；
  对外内容用大众熟的词（"送穷""破五"），生僻术语当细节彩蛋
- 同一元素若有多套流行说法（如五路财神有"赵公明+四部将"和"比干/关羽/柴荣/赵公明"两说），
  两说都写明并注明"民间另有说法"，别只挑一个当唯一答案
