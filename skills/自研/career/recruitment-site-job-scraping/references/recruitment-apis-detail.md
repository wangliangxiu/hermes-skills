# 招聘官网 API 详细样例（2026-08 实测）

## 腾讯 — 完整请求/响应

```bash
# 搜索（pageSize 最大 100，可翻页）
curl -s "https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=$(date +%s%3N)&countryId=&cityId=&bgIds=&productId=&categoryId=&parentCategoryId=&attrId=&keyword=%E8%BF%90%E8%90%A5&pageIndex=1&pageSize=100&language=zh-cn&area=cn"

# 详情
curl -s "https://careers.tencent.com/tencentcareer/api/post/ByPostId?timestamp=$(date +%s%3N)&postId=2077299493635796992&language=zh-cn"
```

响应关键字段：`Data.Count`、`Data.Posts[].PostId / RecruitPostName / BGName / LocationName / CategoryName / Responsibility / Requirement`

### 腾讯 AI 方向代表岗位（2026-08，适合内容/增长/AI产品运营方向）
- **TEG 混元多模态大模型服务增长运营**（深圳，产品类）— 要求"3年以上AI产品运营/业务运营/B端运营/增长运营经验"+"增长运营和内容运营能力"，JD 明确要"把模型能力转化为业务方容易理解、愿意尝试、便于传播的内容和案例"。非编程岗，高度匹配内容/增长背景
- **CSIG 元宝-大模型策略产品经理（AIGC方向）**（深圳）— 1年以上策略产品或 AI 产品经验，重度 AIGC 玩家优先
- **PCG QQ-商业内容运营-AI漫剧运营**（深圳）— 内容运营+AI漫剧/AI真人剧引入孵化，3年内容运营经验
- **IEG AIGC内容创作导演**（深圳）— 需导演/编导背景+完整 AIGC 短片作品集（要求高）
- **TEG AIGC视频内容专家（编导方向）**（深圳）— 影视编导/新闻传播背景，评测 AI 视频质量

## 网易 — 完整请求/响应

```bash
curl -s -X POST "https://hr.163.com/api/hr163/position/queryPage" \
  -H "Content-Type: application/json" \
  -d '{"keyword":"AI","page":1,"size":10}'
```

响应：`{"code":200,"data":{"pages":79,"total":789,"list":[{id,name,workType,firstPostTypeName,recruitNum,requirement,description,reqEducationName,reqWorkYearsName,firstDepName,workPlaceNameList,updateTime,product,productName}]}}`
- `description` = 职责，`requirement` = 要求，列表即完整 JD
- 分页：size 上限 ~10，page 参数实测不生效（多次返回第 1 页）→ 用不同关键词代替翻页

### 网易 AI 方向代表岗位（2026-08）
- **网易元气 AI创新产品用户增长（AI互动小说/AI游戏方向）**（杭州，经验不限）— 要求"2年以上用户增长或内容运营经验"+"熟悉抖音、小红书内容生态和爆款逻辑"+"有自媒体账号运营或爆款内容创作经验者优先"。**与政务新媒体+AI应用背景高度匹配**
- 网易游戏（互娱）AI编导（广州）— 需手绘分镜功底，门槛高
- 网易有道 AIGC创作者学员运营（交付方向）（杭州，3-5年）— 社群运营+商单 BD
- 网易智企 AI产品经理（杭州，0-3年）— AI Agent 端侧体验

## 小红书 — 完整请求/响应

```bash
curl -s -X POST "https://job.xiaohongshu.com/websiterecruit/position/pageQueryPosition" \
  -H "Content-Type: application/json" \
  -d '{"keyword":"运营","pageNum":1,"pageSize":20,"recruitType":"social"}'
```

响应：`{"statusCode":200,"data":{"pageNum":1,"pageSize":10,"total":864,"list":[{positionId,positionName,workplace,publishTime,recruitStatus,duty,qualification,jobType}]}}`
- 详情：`GET https://job.xiaohongshu.com/websiterecruit/position/queryPositionDetail?positionId=X`
- 小红书社招岗位偏商业化（销售/行业运营/工程师），AI 运营岗较少

### 小红书代表岗位（2026-08）
- **【商业体验】客服AI产品运营**（上海/北京）— AI Agent 策略设计+智能客服迭代，要求"参与过大模型或智能客服场景的设计与完整落地"
- 蒲公英策略运营（上海/北京）— KOL 内容供给解决方案
- 商业化创作者商业服务（上海/北京）— 创作者商业化运营

## 被挡站点的调试记录（避免重复劳动）

### 字节跳动（hire 平台 = 飞书 ATS）
- 页面：`https://jobs.bytedance.com/experienced/position`（SPA，curl 可抓 900KB HTML；urllib 间歇被风控返回 42 字节 404）
- JS 托管：`lf-package-cn.feishucdn.com/obj/atsx-throne/hire-fe-prod/portal/mainland/static/js/*.js`
- JS 里发现的端点：`/api/v1/search/job/posts`、`/atsx/api/career_site/proxy_ai/`、`/portal/sharing/search`、`/config/job/filters/`、`/atsx/api/talent/note/list/`
- 实测：POST `/api/v1/search/job/posts` → 405；GET → 跳猎头平台 HTML；`/portal/sharing/search` → Not Found；`/atsx/api/...` → 404。请求拦截器要求 share-token → 匿名不可行

### 快手
- 页面 `https://zhaopin.kuaishou.com/` 301 → `zhaopin.kuaishou.cn`；纯 SPA
- 列表 API：`https://zhaopin.kuaishou.cn/recruit/e/api/v1/open/positions/simple?pageNum=1&pageSize=10`（注意：**必须带 /recruit/e 前缀**，且域名是 .cn）
- 实测：GET 返回 `{"code":-1,"message":"系统错误"}`（带 cookie 也一样）；POST 返回 40014 参数不正确 → 匿名不可行

### 百度
- 所有接口（queryPositionByCondition、/ats/external/public/*）返回 `{"status":"need-login","message":"need login!"}` → 需登录

### 阿里
- `/ats/apis/getPositionList`、`/ats/apis/queryPositionList`、`/social/position/*.json` 全部 403 Forbidden（WAF）；带 XSRF-TOKEN cookie 也 403；`/off-campus/position-list` 页面是 blank-page-monitor 空壳 → WAF 拦截

## 候选岗位投递 URL 拼接
- 腾讯：`https://careers.tencent.com/jobdesc.html?postId={PostId}`
- 网易/小红书：列表数据已含完整 JD，官网搜索对应岗位名即可
