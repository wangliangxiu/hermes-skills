# 中国AI公司招聘入口实测明细（2026-08-24 调研）

9家AI公司招聘入口的 curl 实测结果，供后续"查公司有没有岗位"复用。

## 招聘入口与 SSR/SPA 判定

| 公司 | 招聘入口 | 实测 | 岗位数据获取方式 |
|---|---|---|---|
| 生数科技（Vidu） | https://shengshu.jobs.feishu.cn/index/ | 200 | 飞书 SPA，curl 无岗位数据 |
| 爱诗科技（PixVerse） | https://pixverse.ai/zh/career | 200（60KB） | Next.js SPA，无 __NEXT_DATA__ |
| 智元机器人 | https://agirobot.jobs.feishu.cn/socialrecruitment | 200 | 飞书 SPA；官网 /join_us 的"社会招聘"按钮跳此 |
| 宇树科技 | https://www.unitree.com/careers | 200（98KB） | **SSR，岗位文本直接可见**（如"机器人数据运营工程师"） |
| 月之暗面（Kimi） | https://careers.kimi.com/ | 200（11KB） | Next.js SPA；/api/jobs、/api/v1/jobs 均 404 |
| 金山办公 | join.wps.cn | 302 → /campus-recruitment/wps/41436（仅校招） | 社招官网未公开；campus.wps.cn 是学习中心；ksou.cn 不通 |
| 小红书 | https://jobs.xiaohongshu.com/ | 200（4KB 壳） | SPA |
| 钉钉（阿里） | talent.alibaba.com | 未深抓 | 阿里招聘站 |
| 飞书（字节） | jobs.bytedance.com | 未深抓 | 字节招聘站 |

## 飞书招聘（jobs.feishu.cn）逆向失败路径（别再走）

- `GET /api/v1/search/job/posts?job_type=social` → 200 但返回"字节跳动猎头平台"HTML（非JSON）
- `GET /api/search/job/posts` → 同上
- `POST /api/v1/search/job/posts`（JSON body）→ 405
- `/ats/position/search` → 404；`/atsx/api/v1/position/search` → 404
- 主 JS chunk `8825.xxx.js` 7.2MB，grep API 路径无果——SPA 逆向成本高，放弃
- 正确姿势：官方页只当投递入口，岗位列表走 360 搜索第三方平台快照

## 360 搜索岗位快照要点（2026-08-24 实证）

- query 直接写"公司名 招聘 岗位关键词"（如"宇树科技 招聘 新媒体运营 社招 2026"）
- 快照摘要含：岗位名+薪资+地点+经验门槛+收录时间，如"【北京 海外产品运营招聘】-生数科技 25-45k·15薪"
- 还能拿到岗位类别统计（"全部(212) 技术(181) 客服/运营(2)…"）→ 快速判断该公司运营岗多不多
- 无效查询：site:shengshu.jobs.feishu.cn、site:jobs.xiaohongshu.com、site:agirobot.jobs.feishu.cn 均 0 条；必应 site: 也空

## 本次结论速查（9家公司运营岗供给）

- 运营岗多：金山办公（BOSS 42条客服/运营）、小红书、飞书/钉钉（AI产品运营/内容运营专家在招）
- 运营岗极少：月之暗面（44岗中运营1）、无问芯穹（46岗几乎全技术）、智元（212岗中运营+市场仅4）
- 岗位快照时效：第三方平台收录时间跨度 2024-12 ~ 2026-08，投递前需在官方入口确认在招
