# 中国 AI 大模型公司招聘入口速查（2026-08-24 实测，全部 URL 经 curl 验证）

## 目标公司招聘入口一览

| 公司 | 招聘入口（实测 200） | 平台类型 | 备注 |
|:-----|:--------------------|:---------|:-----|
| DeepSeek | https://talent.deepseek.com/ | 自建 SPA + mokahr | 岗位 JSON 内嵌 JS bundle（见下），投递走 mokahr high-flyer 租户 |
| 智谱AI (Z.ai) | https://zhipuai.cn/careers | 官网 SPA | 返回首页壳；HTML 内嵌 careers i18n JSON：社招/校招分类（产品经理/项目经理、销售、运营-校招）+ 北京/上海/杭州/深圳/成都/吉隆坡 6 地。无岗位列表 |
| MiniMax | https://www.minimaxi.com/careers → https://vrfi1sk8a0.jobs.feishu.cn/index/ | 飞书 hire | 社招 project id=7496820276634634537（URL 参数里可区分社招/校招项目） |
| 零一万物 | https://01ai.jobs.feishu.cn/index/ | 飞书 hire | |
| 百川智能 | https://cq6qe6bvfr6.jobs.feishu.cn/baichuanzhaopin | 飞书 hire | 岗位同步发 BOSS 直聘（zhipin.com/gongsi/8d42a94fe13be56c03N43t-7GVU~.html，27 岗）和智联（zhaopin.com/companydetail/CZ178852320.htm，19 岗） |
| 昆仑万维 | https://jobs.kunlun.com/index | 飞书 hire (atsx-throne) | 官网 https://www.kunlun.com/html/join |
| 商汤科技 | https://hr-jobs.sensetime.com/exp/position/list | 飞书 hire | 官网 https://www.sensetime.com/cn/join-index；页顶有 js-websiteInfo tenant_info JSON |
| 阶跃星辰 | 官网 www.stepfun.com 无公开招聘页 | — | DataHub 显示 719 岗在招（活跃榜第 2），岗位基本只在 BOSS/公众号 |
| 面壁智能 | modelbest.cn 无公开招聘页（/recruit、/join 均 404） | — | DataHub 显示 498 岗在招；靠 BOSS 直聘 |
| 云从科技 | www.cloudwalk.com 首页无招聘链接 | — | 靠 BOSS/猎聘 |
| 第四范式 | https://www.4paradigm.com/join 仅 JS 占位页（1KB） | — | 靠 BOSS/猎聘 |

## DataHub 聚合站（AI 行业岗位首选，2026-08-24 实测）

- 站点：https://datahub.ac.cn/ai-jobs/ —— 收录 8,517 条 AI 岗位、39 家公司（快照 2026-07-22）
- 公司活跃榜：`/ai-jobs/data/ai-company-ranking.html`（排名+岗位数，如阶跃719/智谱558/面壁498/MiniMax412/DeepSeek224/昆仑135/商汤82/百川77）
- 公司页：`/ai-jobs/companies/company-<hash>.html`（如百川 company-47ce5eabe1.html）——含公司简介、岗位方向分布统计（"产品与运营 13"）、在招岗位明细（标题+职责摘要+地点+日期+薪资），岗位链接 `/ai-jobs/jobs/job_<hash>.html`（"查看详情"）
- 找公司页 URL：`/ai-jobs/topics/ai-company-hiring.html`（只列了部分公司）+ 必应 site:datahub.ac.cn <公司名>
- 坑：`/ai-jobs/companies/` 目录 index 返回 403；`/ai-jobs/` 列表页 JS 渲染显示"没有匹配的岗位"；公司页本身 curl 可直抓
- sitemap：/sitemap.xml → sitemap-main.xml（无公司页，只有首页/博客）、sitemap-ai-jobs-001..008.xml（岗位页）、sitemap-4a-jobs-001..011.xml
- 注意：聚合站数据有时效（如百川页 2026-07-20 更新），且可能混入同名不同公司岗位（百川页里混了唐山百川智能机器股份的岗位），按城市/地点甄别

## DeepSeek talent 站 JS bundle 解析（SPA 内嵌岗位 JSON 的范本）

- 首页 https://talent.deepseek.com/ 只有 `<div id="root">` + `<script src="/static/main.<hash>.js">`
- 抓 main.<hash>.js（约 370KB），岗位全量 JSON 内嵌其中，正则提取：
  `\{"id":"[0-9a-f-]{36}","title":"(.*?)","functionName":"(.*?)","locations":\[(.*?)\],"descriptionHtml":"(.*?)","detailUrl":"(.*?)"`
- descriptionHtml 里是富文本 JD（<p><strong>【岗位要求】</strong>…），去标签后即 JD 全文
- 投递走 mokahr：detailUrl 形如 `https://app.mokahr.com/social-recruitment/high-flyer/140576#/job/<uuid>`，submitUrl 加 /apply
- 2026-08 实测 DeepSeek 有非编程岗：AI 产品运营（体验与服务方向，新部门虚位以待）、AI 创作数据产品经理（写作/公文方向，不要求编程）、情感智能数据产品经理、通用 Agent 数据产品经理——注意 DeepSeek 岗位多为"数据产品经理"形态，重文字审美/判断力而非编程

## mokahr 投递系统模式

- URL 结构：`app.mokahr.com/social-recruitment/<tenant>/<id>#/job/<uuid>`（社招）、`/campus-recruitment/...`（校招）
- 已知租户：DeepSeek=high-flyer/140576；其他公司（智谱/月之暗面等）也常用 mokahr，可猜 `app.mokahr.com/social-recruitment/<拼音租户名>` 验证
- mokahr 页面本身也是 SPA，岗位数据建议从公司 talent 站 JS bundle 或 DataHub 拿

## 飞书招聘站（jobs.feishu.cn）要点

- 页面 HTML 只有表单 schema（"职位名称/职位类别/职位类型/职位亮点"的 i18n 定义 + biz_create_time 等字段元数据），无岗位数据
- API `GET /api/v1/search/job?page_size=..&page_token=0&applied_for_me=false` 经 curl 直调返回"字节跳动猎头平台"HTML 壳（带 Referer 也一样）；别逆向了，岗位细节走聚合站/第三方平台
- 页面顶部 `<script id="js-websiteInfo" type="text/json">` 有 tenant_info
- 商汤 hr-jobs.sensetime.com、零一 01ai.jobs.feishu.cn、MiniMax vrfi1sk8a0.jobs.feishu.cn、百川 cq6qe6bvfr6.jobs.feishu.cn、昆仑 jobs.kunlun.com 均为该系

## 必应中文搜索陷阱（2026-08-24 再确认）

- "智谱AI 招聘 内容运营 社招"→ 返回单字"智"的字典/百度百科结果；加 %22 引号无效
- "百川智能 招聘"→ 正常出结果（百川是常见词组）；说明必应按词切分，四字品牌名（智谱AI/零一万物/阶跃星辰）会被拆成单字
- 有效替代：DataHub 聚合站 > 平台公司页（zhipin.com/gongsi/<id>、zhaopin.com/companydetail/<id>）> 360 搜索（so.com，2026-08-20 实证有效）
- DuckDuckGo html 端点（html.duckduckgo.com/html/?q=）国内网络 000 超时

## 本次产出岗位样例（说明报告形态）

- DeepSeek AI 产品运营（体验与服务方向）：北京海淀/浙江拱墅，新部门虚位以待 → 最匹配"产品运营"字面
- DeepSeek AI 创作数据产品经理：重文本审美+实用文本（公文/文案）功底，不要求编程 → 适合政务写作背景
- 百川智能 AI 产品助理：2 年经验门槛低，偏产品但含增长目标/行业调研
- 报告表格：公司|岗位|地点|要求摘要|投递入口|匹配度 + 总结（最值得投/值得跟进/信息封闭），注明数据时效与未能抓取的 SPA 列表
