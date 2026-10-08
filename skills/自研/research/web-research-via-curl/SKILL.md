---
name: web-research-via-curl
description: 查资料/调研但无web_search工具时用curl+代理+公开API联网检索。
---

# 终端网络调研（curl + 代理 + 公开 API）

当环境没有 web_search 工具、但使用者要求查资料/调研/找信息时，用终端 curl
完成。2026-08 实证流程（查 EverOS/1024维向量模型资料成功跑通）。

## 核心认知

1. **curl 默认不走系统代理**——使用者开着 VPN/Clash 也没用，curl 是直连。
   必须先检测代理端口再 export，否则国外站点（HuggingFace/GitHub）超时，
   会被误判成"被墙"（其实只是没走代理）。
2. **搜索引擎 HTML 反爬严重**（百度/必应/DuckDuckGo lite 都抓不到结果），
   优先用**公开 JSON API**，它们通常可直连或走代理后稳定返回。
3. 网络环境先探测再动手，别盲目猜。

## 标准流程

### 1. 连通性探测（先花10秒）
```bash
for u in https://www.baidu.com https://github.com https://huggingface.co https://www.bing.com; do
  curl -s -m 15 -o /dev/null -w "%{http_code} $u\n" "$u"
done
# 200/302=通；000=超时不通（大概率没走代理）
```

### 2. 走系统代理（Windows，检测 Clash/v2rayN 等监听端口）
```bash
# 查系统代理配置（ProxyEnable=1 时 ProxyServer 就是代理地址）
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" | grep -i proxy
# 确认端口在监听
netstat -ano | grep LISTENING | grep -E "7890|7897|10808|10809|17890"
# 导出后所有 curl 走代理（当前 shell 会话内有效）
export https_proxy=http://127.0.0.1:17890 http_proxy=http://127.0.0.1:17890
# 实测补充（2026-08-14）：用户说"把代理关了"（ProxyEnable=0）≠ 代理不可用——
# Clash 类代理软件仍在监听端口，curl 显式 -x http://127.0.0.1:17890 依然 200。
# 先 netstat 确认端口在监听，端口在就能 -x 直连，不用管 ProxyEnable
# 反向补充（2026-09）：netstat 查不到端口 = 代理真没开，此时 -x 只会 code=000。
# 别因为代理不在就判定"这个任务做不了"——先不加 -x 直连试目标 URL，
# 公开 JSON API（api.fxtwitter.com 等）常常直连就通，很多调研根本不需要代理。
```

### 3. 公开 API 优先（按需选用）
| 目标 | 命令 | 说明 |
|:----|:-----|:-----|
| GitHub 搜仓库 | `curl "https://api.github.com/search/repositories?q=关键词&per_page=10" -H "User-Agent: curl"` | 用 `grep -oP '"full_name": "[^"]*"|"description": [^,]*'` 提取 |
| GitHub 抓 README | `curl "https://raw.githubusercontent.com/owner/repo/main/README.md"` | 抓官方文档原文（.zh-CN.md 是中文版） |
| HuggingFace 搜模型 | `curl "https://huggingface.co/api/models?search=关键词&limit=10"` | 需走代理（国内直连不通）；看 tags/pipeline_tag 判断模型类型 |
| 任意 JSON API | `curl -s -m 25 "URL"` | 先 `-o /dev/null -w "%{http_code}"` 探状态 |

### 4. 数据提取
- JSON 用 `grep -oP '"key": "值"'` 或下载到文件后逐段分析
- 大 README 先存文件再 grep：`curl ... > /tmp/x.md && grep -n -i "关键词" /tmp/x.md`
- 中文站抓不到时换英文关键词再搜（中文资料少、反爬更严）

### 5. 社交平台单条内容 + 上游版本差距（2026-09 实证）

**X/Twitter 单条推文**：x.com 本身抓不到正文，用免鉴权镜像 API：

```bash
curl -s -m 25 "https://api.fxtwitter.com/status/<推文ID>"
```

返回 JSON，可用字段：`tweet.text`（**全文**，含换行，比搜索摘要/截图完整）、
`tweet.author.name / screen_name / followers`、`tweet.created_at`、
`tweet.likes / replies / retweets / views`、`tweet.media`。推文 ID 从 URL 尾部取：
`x.com/<用户名>/status/<ID>`。域名换 `api.vxtwitter.com` 同理。
**优先用这个，别用 x.com/oembed**（要鉴权且常失败）；
`cdn.syndication.twimg.com/tweet-result?id=...` 在国内直连常 000，不必试。

URL 两种形态都能用：`api.fxtwitter.com/<用户名>/status/<ID>`（用户给的链接原样替换域名，
最省事）和 `api.fxtwitter.com/status/<ID>`。

**X 长文（Article）另走 `tweet.article`**：当 `tweet.text` 只剩一个
`https://x.com/i/article/<articleId>` 链接、且 `is_note_tweet` 为 false 时，正文不在 text 里，
而在同一份 JSON 的 `tweet.article`：

```bash
curl -s -m 25 "https://api.fxtwitter.com/<用户名>/status/<ID>" -o fx.json
# 解析走 execute_code 的 Python（终端里别跑 python，见陷阱）：
#   a = json.load(...)["tweet"]["article"]
#   a["title"] 标题；a["preview_text"] 摘要；a["cover_media"] 头图
#   a["content"]["blocks"] 是正文段落列表，每块 {"text": ..., "type": ...}
#     type: unstyled | ordered-list-item | atomic（配图占位，text 为空）| header-*
#   拼 block["text"] 即全文；inlineStyleRanges/entityRanges 可忽略
```

JSON 约 25KB，**别在终端整段打印**：下载到文件后由 execute_code 解析、拼成纯文本再打印。
这样抓 X 长文比截图/搜索摘要完整，也比 r.jina.ai 稳（后者匿名访问要鉴权）。

分析这类推荐帖要区分事实与软文：无任何技术细节 + "我真的哭死"式强情绪 +
结尾"去 GitHub 点个 Star" + 配图 = 多半是项目方/合作者推广，汇报时明说。
使用者丢来一条推荐文（常常只是链接、不带到指令）问"靠不靠谱"时，按
`references/verifying-ai-tool-promo-articles.md` 的阶梯逐条核（官方文档支持矩阵 →
免费边界 → 官方定价 → 模型名/单价 → 推广动机），别只复述文章内容。

**判断"本地代码比上游落后多少"**：绝不要相信本地 git 的计数。

浅克隆（`ls .git/shallow`，文件存在且行数 > 0）下 `git rev-list --count HEAD..origin/main`
只在浅边界内数，会报"落后 1 个提交"，而真实差距是几千个。**用 API 量**：

```bash
curl -s "https://api.github.com/repos/<owner>/<repo>/compare/<本地HEAD sha>...main"  # 看 "total_commits"
curl -s "https://api.github.com/repos/<owner>/<repo>/commits/main"                   # 上游 tip sha + 日期
curl -s "https://api.github.com/repos/<owner>/<repo>/releases?per_page=8"            # 带 body 的发行说明
```

实证（本机 Hermes）：本地 HEAD 2026-08-19、上游 main 2026-09-10，本地 git 说落后 **1** 个，
compare API 说 **9532** 个——差三个数量级。**先 `ls .git/shallow` 判断，再用 API 报数字。**

`/releases` 是"这次更新了什么"的最快来源：`body` 里有 `## ✨ Highlights` 和各模块小节，
先取小节标题列表再决定深入哪段。长度差异极大（小补丁只有 1~2KB 的 "About this release"，
大版本可达 39KB）。本地 `git log --oneline HEAD..origin/main` 在浅克隆下同样不可信。

## 招聘岗位调研（社招/校招，2026-08 实证）

查某公司有没有适合的岗位（内容运营/增长/AI产品运营等非编程岗）时：

1. **官网找招聘入口**：`curl 首页 | grep -iE 'career|jobs|join|recruit'`。
   常见形态：自建 careers 页（如 unitree.com/careers）、飞书招聘
   （`<tenant>.jobs.feishu.cn`）、阿里/字节大厂招聘站（talent.alibaba.com、
   jobs.bytedance.com）。
2. **判断 SSR 还是 SPA**：抓招聘页 HTML，含岗位文本=SSR 可直接提取
   （宇树 unitree.com/careers 实测如此）；只有几KB~十几KB壳页面=SPA，
   curl 拿不到岗位列表。智元官网 /join_us 的"社会招聘"按钮实测跳
   agirobot.jobs.feishu.cn/socialrecruitment。
2.5 **AI/大模型公司岗位聚合站优先（2026-08-24 实证）**：
   datahub.ac.cn/ai-jobs/ 收录 8,517 条 AI 行业岗位、39 家公司。
   公司页 `/ai-jobs/companies/company-<hash>.html`（如百川智能 77 岗）
   含在招岗位明细+岗位方向分布统计（"产品与运营 13"可直接数运营岗多寡）；
   活跃榜 `/ai-jobs/data/ai-company-ranking.html` 看各家岗位量级
   （阶跃719/智谱558/面壁498/MiniMax412/DeepSeek224/昆仑135/商汤82）。
   公司页 URL 从 `/ai-jobs/topics/ai-company-hiring.html` 或必应
   site:datahub.ac.cn 找。坑：`/ai-jobs/companies/` 目录 index 403、
   `/ai-jobs/` 列表页 JS 渲染（显示"没有匹配的岗位"），公司页本身可直抓。
2.6 **SPA 招聘站先翻 JS bundle 再放弃**：DeepSeek talent.deepseek.com
   首页只有 `<div id="root">`+一个 JS 文件，但岗位全量 JSON 内嵌在
   /static/main.<hash>.js 里，抓下来正则提取即可（正则见 references/
   china-ai-company-career-portals.md），投递走 mokahr：
   app.mokahr.com/social-recruitment/<tenant>/<id>#/job/<uuid>。
   别被 SPA 壳吓退——先看 JS 里有没有岗位数据。
3. **飞书招聘（jobs.feishu.cn）全是 SPA，别逆向**：岗位数据走 JS 异步
   加载，`/api/v1/search/job`（含 /posts 旧式）经 curl 直调返回"字节跳动
   猎头平台"HTML 壳，页面 HTML 里只有表单 schema（职位名称/职位类别
   i18n 定义），没有岗位数据。**岗位细节改用聚合站/第三方平台快照
   （DataHub、BOSS直聘/猎聘/牛客/智联）**，官方飞书页只作投递入口。
   常见 URL：`/index/`、`/socialrecruitment`（社招）、
   `/campusrecruitment`、`/internrecruitment`。
4. **360 搜索岗位快照**：结果条目解析正则
   `<li class="res-list"[\s\S]*?<h3[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>\s*</h3>([\s\S]*?)</li>`
   摘要带岗位名、薪资、经验要求、平台收录时间（如"2026-08-15&nbsp;-"），
   可直接提炼成"岗位名|地点|要求摘要|薪资"，还能看到岗位类别统计
   （如"技术181 客服/运营2"）判断该公司运营岗多不多。
5. **必应 site: 查询对本类任务无效**（返回 JS 壳、无 b_algo 结果），直接上 360。
6. **输出报告**：公司|岗位|地点|要求摘要|投递入口|匹配度 表格 + 总结
   （最值得投/值得试/不推荐），注明岗位快照时效与未能抓取项（SPA列表），
   不编造岗位。

各公司招聘入口与 SPA/SSR 实测明细见
references/recruitment-research-cn-2026-08.md
中国 AI 大模型公司招聘入口速查（DeepSeek/智谱/MiniMax/百川/零一/昆仑/商汤/
阶跃/面壁 + DataHub 聚合站 + mokahr + JS bundle 解析要点）见
references/china-ai-company-career-portals.md

## 批量核链接与清单整理（使用者分批发资料时）

使用者从文章/群里一份份抄来资料清单（链接 + 他的一句说明）时，按这套走：

1. **静默收集**：他一次发一批，连发好几批。别每条都回一段分析或核验报告（等于打断他），
   中间最多一句"已记 N 个"，全部收完再一次性汇总——这也是他对"中间短查询不要汇报"的一贯要求。
2. **落盘用 patch 追加**：write_file 是整体覆盖，会把前面已收的内容吃掉；
   同时同步改标题里的条数、分类覆盖计数等元信息，别留旧数字。
3. **逐条核链接**（他给的是要用的入口，链接错了等于没给）：
   ```bash
   curl -sL --max-time 20 --proxy http://127.0.0.1:17890 -o /dev/null \
     -w '%{http_code}|%{url_effective}' -A 'Mozilla/5.0' "$url"
   ```
   - 一律用 GET 取（`curl -sL`），**别用 `-I`/HEAD 探活**：不少 CDN 直接拒绝 HEAD，
     返回 `000`/`403`，会把能开的链接误判成死链（uiverse.io、reactbits.dev 实测如此）
   - `403` 多半是反爬/Cloudflare 挡脚本，**不等于链接坏**（浏览器能开），汇报时说明清楚
   - `%{url_effective}` 暴露跳转后的真实域名（如 vo.app → v0.app），按真实域名写进清单
   - `404` 先怀疑**粘贴时被截断**，按前缀补全再试一次（实测 services-maintenanc → 404，
     补成 services-maintenance → 200）；`000` 重试仍不通才判不可达
4. **用来源的结构反推遗漏**：原文摘要/目录里列了 N 类（如"按页面类型找参考"列了 10 类），
   使用者抄来的常只覆盖一部分——按类目对照，主动点出"还差哪几类"，比等他抄完更省事。
5. **汇总文件**：按类目分组，保留使用者原话的那句说明（那才是他要的价值），带来源、
   整理时间、逐条核验结论；文件按桌面规范归入 `我的小项目/<项目名>/`。

## 中文古籍/民俗文化素材（维基 + 维基文库 API）

要给内容/产品找文化出处（某个神祇、典故、成语、宝物的来历与原文）时，别指望搜索引擎，
直接走 MediaWiki API——它给纯文本正文，还能拿到古籍原句：

```bash
cd "$LOCALAPPDATA/Temp"   # 落盘用原生 Windows 路径，别用 /tmp
# 词条正文（纯文本）；-G + --data-urlencode 负责中文编码
curl -s --max-time 25 -x http://127.0.0.1:17890 -G "https://zh.wikipedia.org/w/api.php" \
  --data-urlencode "action=query" --data-urlencode "prop=extracts" \
  --data-urlencode "explaintext=1" --data-urlencode "format=json" \
  --data-urlencode "redirects=1" --data-urlencode "titles=聚寶盆" -o w.json -w "http=%{http_code}\n"
# 猜不准词条名：把 action=query 换成 list=search、prop 换成 srsearch=关键词、加 srlimit=4
# 要古籍原句：域名换 zh.wikisource.org，titles=搜神記/第13卷
```

解析用 execute_code 的 Python（终端 `python -c` 会被审批拦），别在终端整段打印 JSON。

坑：
- **中文短词 web_search 常返回 0 条**（"青蚨""善财童子""和合二仙"这类），0 条 ≠ 没资料，
  换长一点的短语或直接上 API；工具报后端错（keyless / CRAWL_NOT_FOUND / Unrecognized MCP
  response shape）也一律切回 curl，别据此回使用者"查不到"
- **一次传多个 titles 时个别条目 extract 会返回 0 长度**（页面存在，批量空、单抓有）
  → 单独再抓一次那个标题，别以为词条不存在
- REST 摘要端点 `/api/rest_v1/page/summary/<中文>` 中文不编码会返回空壳 → 用 action=query
- 带括号的标题原样传：`--data-urlencode "titles=搖錢樹 (器具)"`
- **民间说法与典籍记载必须分开**：古籍能引原句的写典名+卷次，"龙生九子""只进不出"
  这类是后世演绎，写材料时不能当典故用
- 素材结论按"典籍有载 / 民间说法 / 后世演绎"三档标源，并单列一节"不要碰"
  （历史上有争议的神祇、宗教修法本尊、赌性玩法）——提前替使用者排掉，别等他自己发现
- 详细命令、返回结构、汇报形态见 `references/mediawiki-wikisource-api.md`

## 陷阱

- **微信公众号文章（mp.weixin.qq.com）正文抓不到，但元数据能拿**：非微信环境打开回"环境异常"
  页，正文不在返回的 HTML 里（换微信 UA 变 17KB 空壳、走 r.jina.ai 也被要求验证，
  标了 is_only_read 的更死）。**别反复换 UA/换阅读器重试**。能拿的部分在页面内嵌 JSON：
  `window.cgiDataNew` 的 `title / nick_name / create_time / desc / content_noencode`
  （`desc` 常是全文摘要+结构目录，足够判断文章框架），`<meta name="description">` 是同一份；
  作者名在 `alias`。拿到元数据后请使用者复制正文或截图发来，再用摘要里的结构反推他漏抄了哪部分。
- **登录墙文档抓不到正文 → 直接请使用者贴（2026-09 实证）**：飞书文档/知识库
  （my.feishu.cn/wiki/<token>、docx）非公开分享时，curl 拿回的 200 HTML 是空壳——
  全文搜不到任何正文词（只有"登录/集群/私有部署"这类导航词），文档接口
  （/space/api/wiki/v2/tree/get_info、/space/api/docx/doc/get）回
  `{"code":5,"msg":"Login Required"}` 或 302。**别枚举接口、别换路由重试**：
  需要本人登录态的页面任何存档/阅读器都渲染不出来（Notion/语雀/腾讯文档/
  Google Docs 同理）。一次探测确认是空壳后就停手，请使用者复制正文或导出 PDF/Word
  发本地路径——他本来就在登录态，30 秒的事。使用者贴来的正文就是唯一准信，
  不许拿搜索摘要去拼凑补全。
- **抓取工具报错不等于页面抓不到**：web_extract（Firecrawl）无 key 会直接 403、
  web_search 的 Exa 后端也可能报配置错误——这是后端凭证问题，立刻回到本 skill 的
  curl 路径（同一 URL 常常 curl 直连就是 200），别因为工具报错就回使用者"查不到"。
- **中文长query用360搜索（2026-08-20实证）**：百度/必应/搜狗都不行时，
  `https://www.so.com/s?q=关键词` 可直连且摘要里带关键数据+来源链接
  （查"2026考研国家线 工学"直接拿到264分和中公教育链接，正文明文可见）。
  必应国内版对"2026考研XXX"类query拆词严重（变成"2026年"+旅游/日历泛结果），
  site: 限定也被忽略——别在必应中文上浪费时间。搜狗返回搜索页框架但结果一般。
- **360搜索结果真实URL在 data-mdurl 属性（2026-08-25实证）**：so.com 结果 href 是
  `/link?m=...` 跳转串，真实域名藏在 `<a ... data-mdurl="https://真实域名/...">` 里。
  只提取URL：`curl ... | grep -oP 'data-mdurl="[^"]*"'`；要URL+标题配对：
  `grep -oP 'data-mdurl="([^"]+)"[^>]*>\s*([^<]{5,60})'`。
  过滤自带噪音链接：360kan.com、hao.360.com、bing.com 等。
  实证（琶洲算法大赛调研）：首轮query摘要全不相关，但靠 data-mdurl 挖出官方站
  www.aicompetition-pz.com，再顺官方站赛题详情页拿到全部官方细则——360 摘要本身
  没给到的关键信息藏在结果DOM属性里。抓大HTML（100KB+）时 bash 管道 grep 可能
  空手而归，换 execute_code 的 Python urllib + 关键词上下文窗口（±200字符去标签）
  提取，屡试不爽。
- **必应对中文公司名分词失败，引号也救不了（2026-08-24 实证）**：
  "智谱AI 招聘 内容运营 社招"加 %22 引号后仍返回单字"智"的字典/百科结果；
  而"百川智能"这种常见词组的公司名能正常出结果。中文公司名搜索别依赖必应：
  用聚合站（DataHub）、平台公司页（zhipin.com/gongsi/、zhaopin.com/
  companydetail/）或 360。DuckDuckGo html 端点国内网络常超时（000）。
- **终端里别跑 python（2026-08-24 实证）**：`python -c`/heredoc 解析命令
  会被审批拦下，纯 curl 则放行。抓取用纯 curl 存文件，解析一律走
  execute_code 工具（可读文件、跑正则、处理 JSON），别在终端里混写 python。
- **高校官网可直连抓考情**（2026-08-20实证）：国内高校官网（www.hpu.edu.cn）
  直连200；研究生院/招生信息站（adge.hpu.edu.cn）可抓。找"招生章程"→
  内含专业目录附件；招生公告列表通常分页，翻页URL为栏目路径/N.htm。
- **JSP附件下载带Referer**（2026-08-20实证）：adge.hpu.edu.cn 的
  download.jsp?urltype=news.DownloadAttachUrl 不带Referer返回4.9KB HTML错误页，
  带 `Referer: 引用的公告页URL` 才返回真PDF（214KB）。抓任何下载类URL一律先带Referer。
- **研招网硕士目录API（2026-08-20实证）**：查考试科目绕开PDF解析的权威途径。
  GET https://yz.chsi.com.cn/zsml/ 拿cookie → POST https://yz.chsi.com.cn/zsml/rs/zys.do
  （form: ssdm=省代码如41、dwmc=学校名、mldm=门类如08、yjxkdm=一级学科如0814、
  xwlx=xs学硕、xxfs=1全日制、pageno=1）→ JSON list 含 zydm/zymc/sign/sign2；
  详情页 GET /zsml/zydetail.do?…&sign=&sign2= （Vue异步加载，科目数据不一定在HTML里，
  考试科目用学校官网发布的考试大纲zip确认更直接）。
- **PDF无解析库时的科目代码提取（2026-08-20实证）**：使用者拒绝 pip 装 pdfplumber/pypdf，
  可用 zlib.decompress 解所有 stream 块后搜 ASCII（数字科目代码101/201/301/8xx可见；
  中文是CID编码不可直接读，不值得手写ToUnicode CMap）——只够确认"考数一/英一"这类，
  完整科目表仍走研招网API或官网HTML。
- **execute_code的Python是Windows原生环境**：MSYS路径 /c/temp 不存在会
  FileNotFoundError；写临时文件用 tempfile.gettempdir()（中文用户名下也OK）。
- **需要装新库才能继续时先停下问使用者**（2026-08-20实证）：PDF解析缺
  pdfplumber/fitz/pypdf 时使用者拒绝了 pip install——不要默默装包，先停下
  给替代方案（使用者浏览器打开文件、换公开API/官网查询、用系统已有工具），
  使用者讨厌绕远路和折腾环境。同一会话内不要换命令重试被拒的安装。


- **中文专业信息搜索（展会名/行业活动）成功率极低（2026-08-17 实证）**：
  必应中文版搜展会名返回旅游/泛结果（搜"长沙国际工程机械展览会"全是长沙旅游攻略、
  "林芝水利水电机械展"全是林芝旅游/城市介绍），百度百科词条反爬（curl 直抓返回
  8~164 字节的极短内容，正常词条应几KB），官方域名靠猜必错（cicee.cn 不通、
  cicee.com.cn 是内燃机期刊网站）。**不要闷头反复搜**——把已知部分写成
  "名字可能不准"丢给使用者确认，使用者自己查（浏览器+人肉）通常一两分钟就有准信
  （本案例使用者直接给出两个展会全名：长沙国际工程机械展览会、中国工程建设林芝\n  博览会暨水利水电装备与技术展览会）\n- **外部 AI（ds/DeepSeek 等）给的行业信息必须先经用户确认再写进对外材料**\n  （2026-08-17 实证）：展会时间、厂商名单、规范名称、行业数据（如\"超挖降20%\"）\n  都可能编造。使用者让把 ds 建议整理进 BP 时，规范名 ds 说《钻爆法隧道智能建造\n  施工技术规范》，使用者纠正为《钻爆法隧道智能化施工技术规范》——以用户确认为准，\n  拿不准的（展会时间、厂商名单细节）要么不写要么标注待核实
- **000 = 没走代理或站点不通**，不是"站点不存在"；export 代理后重试
- 搜索引擎 HTML 抓取成功率低（百度 `<h3>` 要过安全验证；必应返回
  "Object moved" 重定向）——不要浪费时间，直接上 API
- GitHub API 未认证限流 60次/小时，够用；大批量搜索加 token
- 部分站点要求 UA：`-H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"`
- 调研结果必须**注明来源**（哪个仓库/文档第几行），不确定就说不知道，
  不编造模型/数据（写作铁律同样适用于调研）
- **中文用户名 Windows git-bash 下 `curl -o 文件` 会失败**（2026.8 实测：
  bash 打不开重定向目标，报 "No such file or directory"，$HOME 路径含中文
  乱码所致，即使 cd 到 $HOME 也一样）。别落盘：直接 `curl ... | grep ...`
  管道处理，或写到**原生 Windows 路径**
  （`$LOCALAPPDATA/Temp/x.html`、`C:/temp/x.md` 这类）。注意 `/tmp/...` 与 `/c/...`
  是 MSYS 写法，**原生 curl/grep 解析不了**：curl 会静默写不成（不报错），紧接着
  grep 报 `No such file or directory`，看起来像是抓取失败，实际是路径写错了
  （2026-09 实测）；必须落盘/解压时改用
  execute_code 的 Python（中文路径无问题），别反复试 bash 写法浪费时间
- **git clone github.com 失败，但 api.github.com 直连却通**（或 clone 中途
  submodule 报错）：兜底用 codeload 走代理下 zip：
  `https://codeload.github.com/owner/repo/zip/refs/heads/<分支>`，Python
  zipfile 解压到目标目录，再对本地路径做注册（如
  `claude plugin marketplace add --scope user <本地路径>`）。
  完整实战案例见 `references/claude-code-zh-cn-install.md`。
