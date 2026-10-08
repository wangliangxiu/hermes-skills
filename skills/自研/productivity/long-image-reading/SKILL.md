---
name: long-image-reading
description: 要读超长截图（长图/长截图）并总结时用。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [vision, 长图, 截图, 图片读取, 总结]
    category: productivity
    related_skills: [sn-da-image-caption, pdf-image-text-extractor]
---

# 超长图片（长图）的读取与总结

## 什么时候用

- 用户甩来一张很长的图（几千到上万像素高：公众号长图、视频总结长图、聊天记录拼接、网页整页截图），要求“总结一下”“看看这个”“这是怎么做到的”
- 任何高过 ~1500px、一次看不清的图片

## 铁律

vision_analyze 一次只能看清约 622×900 像素的信息量。整张长图丢进去会被等比缩小到几十像素宽，字全糊。必须切片读，并且边读边落盘。

## 步骤

1. 先量尺寸：`execute_code` 里 `from PIL import Image; Image.open(p).size`，据此算切几条。
2. 按 ≤900px 高度切竖条，逐条读：
   `vision_analyze(image_url=原图, region=[0, y, 宽, y+900], question="逐字誊写这一段（含表格数字）。")`
   - 用 `region` 切，不要先裁成小图再放大：`region` 保留原始分辨率，而把 crop 放大 2 倍没意义——超过 622×900 一样会被降采样回去。
3. 每条都要确认“真的读到了”：返回里没出现文字内容（只有一行 note）就是这条读失败，**原样重试同一个 region**，一般第二次就出来。一批 2-3 条比一批 4 条稳。
4. 读到就立刻誊写进笔记文件（workspace 或 Temp 下的 notes.txt），用 `patch` 追加——`write_file` 是整体覆盖，会吃掉前面写的内容。
   **必须马上落盘**：后面每次新的图片调用都会把之前的图从上下文里挤掉（会看到 `[screenshot removed to save context]`），挤掉之后就再也“看”不到它了，别指望回头凭记忆复述。
5. 全部读完，再从笔记文件汇总成成品总结交给用户。用户要的是总结，不是按切片逐条汇报。

## 回答“这个是怎么做出来的”要看的三处证据

- 文件名是几十位十六进制哈希 → 大概率是某个在线工具导出的成品图
- 正文里有语音转写式的错字、断句 → 文字来自 ASR + 大模型结构化，不是人工录入
- 白底结构化文字（带 1/2/3/4 编号小标题）与黑底原视频截图交替 → 典型的「视频 → 图文笔记长图」

通用流程照实说：下载视频/取字幕 → ASR 转写 → 大模型按主题分节、抽表格数据 → 抽关键帧截图 → HTML/CSS 排成约 600px 宽的纵向长页 → 无头浏览器（Playwright/Puppeteer）整页截图导出 PNG。宁可讲清这套通用流程，也不要猜某个具体产品名。
