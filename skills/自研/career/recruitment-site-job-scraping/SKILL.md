---
name: recruitment-site-job-scraping
description: 从公司招聘官网抓取社招岗位数据（JSON API）。触发：调研招聘岗位、查某公司社招职位、岗位数据整理、投递前岗位筛选。
---

# 招聘官网岗位数据抓取（中国互联网大厂）

用 curl + 官网 JSON API 抓取社招岗位列表和 JD，替代人工翻页。2026-08 实证：**腾讯/网易/小红书 API 匿名可用**；字节/百度/阿里/快手匿名抓取不可行（见下，别再浪费时间重试）。

## 核心流程

1. 先探测连通性（国内招聘站通常直连可通，不需要代理）
2. 有公开 JSON API 的直接用（见下）
3. SPA 站点（HTML 无数据）：抓首页 → 提取 JS chunk → curl 抓 chunk → grep API 端点
4. 数据落地：中文用户名下别用 `curl -o` 落盘，用 execute_code 的 Python + tempfile.gettempdir()
5. **fail-fast**：每站最多试 3 个端点，不行就标"未能抓取、给官网入口"。先把能抓的站数据拉全，再去啃被挡的站（本会话在 4 个被挡站上烧了约 20 次调用，导致报告没写完——教训）

## 可用的招聘 API（2026-08 实证）

### 腾讯 careers.tencent.com ✅ 最佳
搜索：`GET https://careers.tencent.com/tencentcareer/api/post/Query?timestamp={毫秒}&countryId=&cityId=&bgIds=&productId=&categoryId=&parentCategoryId=&attrId=&keyword={URL编码}&pageIndex=1&pageSize=100&language=zh-cn&area=cn`
- 返回 `{"Code":200,"Data":{"Count":N,"Posts":[{PostId,RecruitPostName,BGName,LocationName,CategoryName,Responsibility,Requirement}]}}` — 列表就带完整 JD
- 详情：`GET .../tencentcareer/api/post/ByPostId?timestamp={毫秒}&postId={PostId}&language=zh-cn`
- pageSize 可到 100；实测关键词命中："运营"374条、"混元"64条、"AIGC"60条、"大模型"100条
- BGName 定位部门：TEG=技术工程（混元大模型）、CSIG=云与智慧（元宝）、WXG=微信、PCG=平台与内容、IEG=互动娱乐、CDG=企业发展

### 网易 hr.163.com ✅
搜索：`POST https://hr.163.com/api/hr163/position/queryPage` body `{"keyword":"运营","page":1,"size":10}`
- 返回 `{"code":200,"data":{"total":N,"list":[{id,name,productName,firstDepName,workPlaceNameList,reqEducationName,reqWorkYearsName,description,requirement}]}}` — 列表自带完整 JD，无需详情接口
- 坑：size 上限约 10；page 参数疑似不生效（多页返回重复）→ 别指望分页拉全量，用多个关键词各拉 1-2 页更划算
- 好关键词："AI"、"大模型"、"AIGC"、"增长"（网易元气/雷火/有道 AI 岗密集）

### 小红书 job.xiaohongshu.com ✅
搜索：`POST https://job.xiaohongshu.com/websiterecruit/position/pageQueryPosition` body `{"keyword":"运营","pageNum":1,"pageSize":20,"recruitType":"social"}`
- **`recruitType:"social"` 必填**，漏了报 999 "招聘类型参数异常"
- 返回 `{"statusCode":200,"data":{"total":N,"list":[{positionId,positionName,workplace,publishTime,duty,qualification}]}}` — duty/qualification 即 JD
- 详情：`GET /websiterecruit/position/queryPositionDetail?positionId=X`（GET + query 参数，不是 POST body）

## 匿名抓取不可行（2026-08 实证，直接给官网入口）

| 公司 | 现象 | 结论 |
|:----|:-----|:-----|
| 字节 jobs.bytedance.com | `/api/v1/search/job/posts` POST 405、GET 跳"猎头平台"；`/atsx/api/career_site/proxy_ai/` 需 share-token；页面 JS 托管在 lf-package-cn.feishucdn.com | 需登录/分享 token，让用户浏览器查 |
| 百度 talent.baidu.com | 所有接口返回 `{"status":"need-login"}`（queryPositionByCondition 等） | 需登录 |
| 阿里 talent.alibaba.com | `/ats/apis/*`、`/social/*.json` 全 403（WAF）；页面是 blank-page-monitor 空壳 | WAF 拦截，带 XSRF cookie 也 403 |
| 快手 zhaopin.kuaishou.cn | 岗位 API `/recruit/e/api/v1/open/positions/simple`（.com 301→.cn 且需 /recruit/e 前缀）返回 `{"code":-1,"message":"系统错误"}`；POST 报 40014 | 匿名不可行 |

## SPA 招聘站 API 挖掘方法

1. `curl -s 首页URL` 抓 HTML（urllib 连续请求易被风控返回 404/短页，curl 稳；同一 URL urllib 404 时换 curl 重试）
2. 提取 JS：`re.findall(r'src="([^"]*\.js)"', html)`，优先抓 main/app/pc/vendor 和数字 chunk
3. grep 端点：`["\'](/[a-zA-Z0-9_\-/]{3,70}(?:api|position|job|search|list)[a-zA-Z0-9_\-/]*)["\']`
4. 看请求封装上下文：axios baseURL、请求拦截器自动加参（字节的 portal_entrance、share-token；快手 $basePath 动态拼接）
5. 301 处理：`curl -L` 或看 Location 头（快手 .com→.cn 连路径前缀都变了，重定向后要用新域名+新前缀）
6. 端点 405/404 后换 base 前缀组合（/api/v1、/atsx/api、根路径）各试一次即止，别无限组合

## 搜索引擎兜底

- **Bing RSS 可用**：`curl -s -L "https://www.bing.com/search?q={查询}&format=rss"`（-L 跟随 301→cn.bing.com）返回标准 RSS item，可绕过 HTML 反爬
- 但 site: 招聘站 SPA 页面基本没被索引，搜出的多是科普文章，找具体岗位帮助有限
- 360 so.com 直抓返回空；必应/百度 HTML 页反爬 — 别浪费时间

## 岗位筛选方法论（求职调研场景）

- 多关键词组合搜索：单一"运营"命中太泛，用"岗位词+AI词"（AI产品运营 / 混元 / AIGC / 大模型 / 增长）交叉搜，再按 JD 关键词筛
- 非编程岗方向（内容运营/增长运营/AI产品运营/AIGC应用）重点看：产品/内容/运营 Category + JD 里"运营经验""内容生态""爆款""增长"字眼
- 候选岗位先存 JSON 再统一筛（tempfile），别边抓边丢
- 抓到的岗位详情页 URL 拼接规则：腾讯 `careers.tencent.com/jobdesc.html?postId=X`；网易/小红书列表数据已含完整 JD，可直接用

## 详细请求/响应样例
见 `references/recruitment-apis-detail.md`（各家完整 curl 命令、响应字段说明、2026-08 抓到的代表岗位快照）。
