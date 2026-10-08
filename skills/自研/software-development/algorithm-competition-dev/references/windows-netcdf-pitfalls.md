# Windows 下 netCDF4/xarray 中文路径与气象数据处理坑（琶洲赛题01 实测 2026-08-25）

## 坑1：netCDF4 打不开中文路径文件（最致命）
症状：
- 文件在资源管理器 / git-bash 里存在，`os.path.exists` 也返回 True
- `xr.open_dataset(p)` / `netCDF4.Dataset(p)` 抛 FileNotFoundError
根因：
- netCDF4 底层 C 库（libnetcdf）用 fopen，Windows 下无法处理非 ANSI 路径
- `os.listdir` 走 Python Unicode API 所以正常 → 迷惑性极强（目录能列出、文件打不开）

修复（首选：subst 虚拟盘符，零拷贝）：
```
subst X: "D:\网页下载\气象数据驱动的低空无人机飞行风险识别与最优航线规划"
```
验证：`subst` 命令应显示映射；Python 里用 `X:\home\...` 打开成功。

关键：subst 映射**重启后失效** → 加载模块里写自动探测函数：
```python
def find_data_base():
    cand = [r"X:\home\temp_upload\upload\t001"]
    for entry in os.listdir("D:\\"):
        if "网页下载" in entry:
            p1 = os.path.join("D:\\", entry)
            for e2 in os.listdir(p1):
                if "气象" in e2:
                    cand.append(os.path.join(p1, e2, "home", "temp_upload", "upload", "t001"))
    for c in cand:
        if os.path.isdir(c):
            return c
    raise FileNotFoundError("未找到数据目录，先执行 subst X: ...")
```
交接说明文档必须写明"重启后先执行 subst"。

## 坑2：git-bash 传中文给 python -c 会乱码
症状：`python -c "open(r'D:\中文\a.nc')"` 从 git-bash 执行报 FileNotFoundError，明明路径对。
根因：git-bash → Windows python 的 argv 编码错乱。
修复：
- 把脚本写成 UTF-8 .py 文件（首行 `# -*- coding: utf-8 -*-`）再执行
- 路径用 os.listdir 逐层探测拼出来，不硬编码中文到命令行
（注意：write_file 写入的 .py 文件路径本身含中文没关系，只有命令行传参才乱码）

## 坑3：10G+ 大目录摸底
- `find 全遍历` 60s 超时；`du -sh` 大目录也慢
- 对策：`find -maxdepth 3 -type d` 看结构 → 对"代表子目录" `du -sh` 测大小 × 数量估算总量
- 用 PowerShell 查权限等重活也要控制超时

## 坑4：nc 嵌套结构别按目录名猜
案例：art_gd_1km 目录名 `20250701000000` 看似单时次，实际每目录=1天、每文件含24小时
（dims time=24, y=39, x=22）。giftdaily 目录 `20250701080000` 的文件 time 从 09:00 起（目录名=归档时刻-1h）。
对策：xarray 打开看 dims/coords/attrs，打印 time 坐标 min/max 验证；网格可能是纯索引坐标
（x:0-21, y:0-38，无经纬度、无 attrs）→ 按索引网格处理，别等经纬度。

## 坑5：时间覆盖检测
- 目录名取日期与理论完整天数对比，按月统计缺失（art 缺 2025-10~12 整3个月=92天）
- giftdaily 有 6 小时跳变（08→14时）= 缺测时段，按缺测处理

## 坑6：阈值校准（数据到后必做）
- 抽样：每月 5/15/25 日 × 全天 ≈ 30 天 / 61.7 万格点样本
- 物理红线保持不动：无人机抗风6级 10.8m/s = 禁飞（业务依据）
- 中/高风险阈值按分位数下调：风速 5.5/10.8 → 3.5/7.0（95分位3.19、99分位4.80；≥5.5 仅0.53%）
- 降水 4/8/16 与数据吻合（≥4mm/h 3.19%、≥16 0.53%）→ 不动
- 能见度 3000/1500/500 与数据吻合（≤3000 1.5%）→ 不动

## 坑7：图片数据（雷达/卫星）不可反推数值
- radar CREF png：1280×717 RGBA、2660色、无元数据 → 无法可靠反推 dBZ，放弃并在报告标注
- fy4b jpg 同理（每小时1张，01时缺）
- 雷电要素缺失 → thresholds.json 保留 lightning 要素，风险计算 row 传 None
  （missing_policy=treat_as_low，不干扰 worst_case 最不利综合）

## 演示时次自动选择（演示效果关键）
- 极端天气（禁飞占比30%+）时 A* 无路径 = 业务正确（暴雨应停飞）但演示效果差
- 自动挑"禁飞占比 8%~35% 且 A* 可达"的时次（find_demo_scene 策略：
  抽样天→r01h 快速筛降水≥5mm/h→逐个算风险+试A*→第一个成功即用）
- 先 batch_test 多场景分类（晴好72时次100%可达/暴雨3时次100%可达/平均禁飞24.1%）
  再选演示场景，报告数字全来自真实运行

## 动态演示（气象变化→重规划）
- 找"同一天从晴到暴雨再转晴"的转变日（max>=20 且 min<2 mm/h），对 08/12/16/20 时
  各跑一次出图 + 生成《动态场景演示说明.txt》，展示风险地图随气象更新、航线自动重规划
