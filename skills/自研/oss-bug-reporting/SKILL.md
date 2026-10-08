---
name: oss-bug-reporting
description: "Use when filing a bug upstream — dedupe open fix PRs first."
version: 1.0.1
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [github, issues, bug-report, upstream, cn-mirror]
    related_skills: [github, hermes-desktop-troubleshooting]
---

# 向上游报 bug（先查重，再动手）

把本机诊断出来的缺陷报给上游项目时走这个流程。目标不是「开一条 issue 交差」，
而是让修的人最快看到证据并合并 —— 所以**先查重，再决定报 issue 还是顶 PR**。
还覆盖：报告正文该有什么、怎么核实"真的提交了"、CN 镜像通道的坑。

## When to Use

- 用户说「把这个 bug 报给官方 / 报 issue / 反馈给作者」
- 诊断出上游代码本身的缺陷（不是自己配置错），准备开 issue 或评论 PR
- 已经写好一条 issue 正文，要判断该发在哪里、发之前该查什么
- 想确认自己/用户是不是真的提交成功了

## 铁律

1. **先查重，而且搜索要同时覆盖 PR 和 issue。**
   很多 bug 已经有写好的修复 PR 卡在没合并 —— 这时开新 issue 只会被标成重复。
   区分方法：搜索结果项里带 `pull_request` 字段的是 PR，没有的才是 issue。
2. **已有 open 的修复 PR → 去那条 PR 下面贴实测证据催合并**（重点写"已发布版本仍然受影响"、影响面多大），
   不要另开 issue。确实没有任何 PR 才开 issue，并且正文里引用相关 PR 编号/关键词，免得被当重复关掉。
3. **没装 gh、没登录也能查重。** `api.github.com` 通常直连可通、无需鉴权，用 python urllib 打搜索接口就够：
   `https://api.github.com/search/issues?q=repo:<owner>/<repo>+<关键词>&sort=created&order=desc`
   （`is:issue` / `in:title` 可收窄）。本机 MSYS 里的 curl 常取不到响应正文，**不要用 curl 判断网络**。
4. **提交必须有登录态，而且必须核实真的提交成功。** 用户一句「我提交了」不算证据 ——
   回列表页读回确认（issue 列表页 / `gh issue list --search ...`）之后才能说提交了；
   没登录就直说卡在哪一步，不要含糊地报"已提交"。
5. **同一份材料两处复用时，先想清楚哪边管用。** 上游仓库是修复落地的地方；CN 镜像/国内通道
   （如 `cnb.cool` 上的镜像组）是中文用户更容易被官方看到的地方，issue 区往往只有个位数，
   但常要微信扫码、页面 JS 渲染 → urllib 抓不到列表，只能用浏览器看、提交只能用户本人来。

## 报告正文要素（缺一项就会被追着问细节）

- 环境：系统版本、**用户名是否含非 ASCII**、代码页/locale、程序版本号、安装方式
- 症状：原样贴报错文字（带上英文 locale 的说法）、退出码、**有没有 traceback**
  （这一项决定是"命令没找到"还是"命令找到了、内部路径解析失败"，两类根因完全不同）
- 根因：定位到具体文件 + 大致行号 + 关键那几行代码
- 最小复现 / 判据：一条能确诊的命令，附两种可能性的**实测对照数据**
- 试过但无效的方案：省得维护者再让你试一遍
- 建议补丁 + 验证数据：改完在复刻真实环境下跑出的退出码/耗时
- 影响面：什么条件下必然中招、是不是边角情况（"只有中文用户名机器"这类限制要写清楚）
- 实测和推测分开写，推测必须标明是推测

## 用户偏好（固定）

- 报告写成**纯文本 .txt 放桌面**（使用者不看 md），文件名直白写清是什么 bug
- 写完之后**直接推进到提交，不要停下来等使用者审草稿**（他会说"不用看，直接提交就行"）；
  只在**必须他本人授权**的地方停（登录、扫码、2FA），其余流程自己跑完
- 结论先行，过程中间不用逐条汇报搜索/查证动作

## 附：本机要提交 GitHub，先装 gh 并登录

见 `references/gh-cli-install-and-login.md` —— 从 release zip 解压到 D 盘、winreg 改用户 PATH、
代理下的设备码登录、一次性码如何转述给用户。
