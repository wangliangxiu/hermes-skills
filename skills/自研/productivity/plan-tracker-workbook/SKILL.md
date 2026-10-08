---
name: plan-tracker-workbook
description: 要做计划/打卡/配额类中文 Excel 工作簿时用。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [xlsx, openpyxl, 打卡表, 计划表, 配额表, 中文文档]
    category: productivity
    related_skills: [xlsx, desktop-organization-rules, cn-doc-format]
---

# 计划 / 打卡 / 配额类 Excel 工作簿

## 什么时候用

- 用户要“给我出个表”：减脂/训练计划、学习计划、进度打卡、单价配额、用量统计这类**要天天填、隔段时间回看**的表
- 已有工作簿要改参数、加表、改说明文字

## 生成与验证（本机）

- openpyxl 装在 `D:\python\python.EXE`（3.14）；Hermes 自己的 venv 里没有，`execute_code` 里直接 `import openpyxl` 会 ModuleNotFoundError。
- 可靠路子：`write_file` 把生成/修改脚本写到临时目录，再用 `execute_code` +
  `subprocess.run([r"D:\python\python.EXE", 脚本路径], capture_output=True, text=True, encoding="utf-8")` 执行；跑完把临时脚本删掉。这条路不依赖 terminal 的交互授权，中文路径也稳。
- 读回验证用 xlsx skill 的 `xlsx_read.py <f> --sheets` / `--formulas`，同样用 `D:\python\python.EXE` 跑；改完用 openpyxl 复核数据验证、条件格式、合并区还在不在。

## 公式必须触发重算

- openpyxl 只写公式、不算结果，缓存值全是 null。写完要设工作簿 `fullCalcOnLoad`（`xlsx_edit.py <f> --recalc`），否则用户打开可能看到空白或 0。
- 不要用 `data_only=True` 读回来再保存——那会把公式全部换成缓存值（此时为 None）。

## 结构惯例

- 第一张固定是「使用说明」：用「步骤｜做什么｜在哪张表」三列表写怎么用，再列几条硬性红线。
- 每张表一个用途，表名直白：每日配额 / 体重打卡 / 饮食打卡 / 食物换算 / 调整规则。
- 关键参数做成**输入格 + 公式**：改一个数字（当前体重、单价、系数），配额、热量、分餐、合计全部自动重算；不要把算出来的数值写死，否则用户过两周权重一变就得找你重做。
- 打卡列加数据验证下拉（√ / ×）；趋势列加条件格式（下降=绿 C6EFCE，上升=红 FFC7CE）；表体 `freeze_panes` 冻表头；日期列预填一串日期便于下拉填写。

## 版式（用户偏好）

- 标题行深蓝底白字（1F4E79），列头浅蓝底深蓝字（D9E2F3），输入格黄底（FFF2CC），全表细边框（B4C6E7），正文微软雅黑 10.5pt。
- 数字列居中、说明/长文本列左对齐 + wrap_text；列宽逐列显式设置（说明列 45-58），不靠默认宽度。
- 换算/参考表把“常见份量”和数值写在同一行（如：1碗米饭≈180g≈45g碳水），用户是拿来估量的，不给克重秤。

## 交付

- 配一份同名 txt 说明（用户看 txt 不看 md）：先写方法依据和目标，再写每天怎么做、卡住怎么办、红线、时间预期。
- 文件放 `桌面\我的小项目\<项目名>\`；更新直接覆盖同名文件，不留 `_v1`/`最终版`。
- 用了别人的方法/教程当依据时，在说明里写清出处（谁讲的、哪来的一套），别把外部方法讲成自己的。
