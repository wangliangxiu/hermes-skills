# -*- coding: utf-8 -*-
"""生成 MS Project XML（.xml；Project 双击可打开，也可另存为 .mpp）。

用法：改 START 与 ROWS，然后：python make_msproj_xml.py [输出路径]

三条要点（都踩过）：
  1) 不定义自定义日历 —— Project 不认，会按默认标准日历（周一~周五）重算工期，数字全对不上。
     这里按标准日历自己把日期算自洽（跳过周末），写进去就不会被改动。
  2) Duration 以分钟计（8 小时工作日 = 480 分钟/天）。
  3) 前置关系（Type=1 为 FS）放在任务元素末尾。
生成后务必用 Project 打开核对日期、工期与显示单位。
"""
import datetime as dt
import os
import sys
import xml.etree.ElementTree as ET

OUT = sys.argv[1] if len(sys.argv) > 1 else "project.xml"
START = dt.datetime(2026, 10, 1)          # 计划开工日，须为工作日
DAY_START, DAY_END = "08:00:00", "17:00:00"
MIN_PER_DAY = 480

# (任务名, 工期工作日, 前置任务 ID 列表)；工期 0 = 里程碑。ID 从 1 起按顺序自动编号。
ROWS = [
    ("施工准备", 10, []),
    ("围护结构施工", 50, [1]),
    ("基坑开挖及支撑架设", 60, [2]),
    ("主体结构施工", 45, [3]),
    ("附属结构", 40, [4]),
    ("基坑回填及场地恢复", 25, [4, 5]),
    ("竣工验收", 0, [6]),
]

is_wd = lambda d: d.weekday() < 5


def next_wd(d):
    while not is_wd(d):
        d += dt.timedelta(days=1)
    return d


def add_wd(start, n):
    """从 start（含）起第 n 个工作日"""
    d, c = start, 1
    while c < n:
        d += dt.timedelta(days=1)
        if is_wd(d):
            c += 1
    return d


finish, sched = {}, []
for i, (name, dur, preds) in enumerate(ROWS, 1):
    if preds:
        base = max(finish[p] for p in preds)
        start = base if dur == 0 else next_wd(base + dt.timedelta(days=1))
    else:
        start = next_wd(START)
    end = start if dur == 0 else add_wd(start, dur)
    finish[i] = end
    sched.append((i, name, dur, preds, start, end))

# 自洽性校验：起止日是工作日、工期等于工作日数
for i, name, dur, preds, s, e in sched:
    assert is_wd(s) and is_wd(e), "起止日不是工作日: %s" % name
    if dur:
        n = sum(1 for k in range((e - s).days + 1) if is_wd(s + dt.timedelta(days=k)))
        assert n == dur, "%s 工期标注 %d 天，实际 %d 个工作日" % (name, dur, n)

fmt = lambda d, t: d.strftime("%Y-%m-%dT") + t
esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
proj_finish = max(s[5] for s in sched)
now = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

TASKS = []
for i, name, dur, preds, start, end in sched:
    px = "".join(
        "      <PredecessorLink>\n"
        "        <PredecessorUID>%d</PredecessorUID><Type>1</Type><CrossProject>0</CrossProject>\n"
        "        <LinkLag>0</LinkLag><LagFormat>4</LagFormat>\n"
        "      </PredecessorLink>\n" % p for p in preds)
    TASKS.append(
        "    <Task>\n"
        "      <UID>%d</UID>\n      <ID>%d</ID>\n      <Name>%s</Name>\n"
        "      <Type>0</Type>\n      <IsNull>0</IsNull>\n      <CreateDate>%s</CreateDate>\n"
        "      <WBS>%d</WBS>\n      <OutlineNumber>%d</OutlineNumber>\n"
        "      <OutlineLevel>1</OutlineLevel>\n      <Priority>500</Priority>\n"
        "      <Start>%s</Start>\n      <Finish>%s</Finish>\n"
        "      <Duration>%d</Duration>\n      <DurationFormat>4</DurationFormat>\n"
        "      <Milestone>%d</Milestone>\n      <Summary>0</Summary>\n"
        "%s    </Task>\n" % (
            i, i, esc(name), now, i, i, fmt(start, DAY_START), fmt(end, DAY_END),
            dur * MIN_PER_DAY, 1 if dur == 0 else 0, px))

XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Project xmlns="http://schemas.microsoft.com/project">
  <SaveVersion>14</SaveVersion>
  <Name>施工进度计划</Name>
  <ScheduleFromStart>1</ScheduleFromStart>
  <StartDate>%(start)s</StartDate>
  <FinishDate>%(finish)s</FinishDate>
  <DefaultStartTime>%(ds)s</DefaultStartTime>
  <DefaultFinishTime>%(de)s</DefaultFinishTime>
  <MinutesPerDay>480</MinutesPerDay>
  <MinutesPerWeek>2400</MinutesPerWeek>
  <DurationFormat>4</DurationFormat>
  <WeekStartDay>2</WeekStartDay>
  <Tasks>
%(tasks)s  </Tasks>
  <Resources/>
</Project>
""" % dict(start=fmt(START, DAY_START), finish=fmt(proj_finish, DAY_END),
             ds=DAY_START, de=DAY_END, tasks="".join(TASKS))

open(OUT, "w", encoding="utf-8", newline="\r\n").write(XML)
root = ET.parse(OUT).getroot()          # 至少验证 XML 能解析
ns = {"p": "http://schemas.microsoft.com/project"}
print("已生成 %s（%.1f KB，%d 个任务）" % (OUT, os.path.getsize(OUT) / 1024,
                                    len(root.findall("p:Tasks/p:Task", ns))))
for i, name, dur, preds, s, e in sched:
    print("  %-24s %-6s %s → %s  前置:%s" % (
        name, "%d 工作日" % dur if dur else "里程碑",
        s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d"), preds or "-"))
