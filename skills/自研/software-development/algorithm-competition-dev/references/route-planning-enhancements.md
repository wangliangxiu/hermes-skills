# 航线规划增强配方（琶洲赛题01 实战，2026-08）

针对"风险识别 + A* 航线规划"类赛题的进阶修复与增强，全部有真实运行验证。

## 1. 预报 netCDF 时次对齐（最易漏、后果最重的 bug）

**现象**：giftdaily 按"数据块"存（每天 `YYYYMMDD080000` 与 `YYYYMMDD200000` 两个目录），
每块 100 个时次。**块的首时次不是 00:00，而是起报时刻 +1h**：

```
08块 (…080000): time[0] = 当天 09:00, time[1] = 10:00, ...
20块 (…200000): time[0] = 当天 21:00, time[1] = 22:00, ...
```

用 `arr[hour]` 直接当索引会静默错位 9~20 小时（`hour=12` 读到 21:00 的数据，
`hour=20` 读到次日 17:00）。程序照跑、平台照 PASS，风险识别结果却全被污染。

**诊断方法**：`xarray.open_dataset(f)` 后打印 `ds['time'].values` 的头几个值，看下标 0 对应几点。

**修复（按 time 坐标对齐，不猜下标）**：

```python
def _gift_target_time(day, hour, forecast_offset=0):
    return (np.datetime64("%s-%s-%sT%02d:00:00" % (day[:4], day[4:6], day[6:8], hour))
            + np.timedelta64(int(forecast_offset), "h"))

def _gift_candidate_blocks(day):
    import datetime as dt
    d = dt.datetime.strptime(day, "%Y%m%d")
    prev = (d - dt.timedelta(days=1)).strftime("%Y%m%d")
    return [day + "080000", day + "200000", prev + "200000", prev + "080000"]

def _gift_index_for(ds, target):
    times = ds["time"].values
    idx = int(np.argmin(np.abs(times - target)))
    if abs(times[idx] - target) > np.timedelta64(1, "h"):  # 偏差>1h=该块不含此时次
        return None
    return idx
```

要点：
- 依次试候选块，`_gift_index_for` 返回 None 就试下一个块（跨天目标用前一天块）。
- glob 文件名要用**块时间戳**匹配（`gust_%s*.nc % blk`），不能用 `day` 匹配——
  前一天块的文件名是 `gust_YYYYMMDD前一日200000.nc`，用 day 会漏掉。
- hour=8 且数据从 09:00 才有 → 取最近可用 09:00（偏差≤1h 内）；数据边界外（如首日 00:00）返回 None → 缺测按 treat_as_low 处理，合理。

## 2. A* 可采纳启发式（风场修正场景）

h = 剩余距离 / **最大可能地速**，不是 / 空速：

```python
# __init__ 里算一次
self._h_speed = self.speed
for w in self.wind_grid.values():
    wm = math.hypot(w[0], w[1])
    if wm > 0:
        self._h_speed = max(self._h_speed, self.speed + wm)

# _astar 里
h = self.dist(nb, goal) * self.cell_size_m / self._h_speed
```

原因：顺风时 `ground_speed = 空速 + 顺风投影` 可 > 空速，h 若用空速会高估剩余时间
→ 非 admissible → 悄悄返回次优路径。修复后实测飞行时长从 10286s 降到 10067s（找到更优路径）。

## 3. 带碰撞检测的路径平滑（Douglas-Peucker）

A* 输出是 26 邻域阶梯折线。DP 简化可去折线，但删点前必须做可见性检查，否则会把禁飞格拉进直线：

```python
def line_of_sight(a, b, risk_grid, max_risk=2):
    if a[2] != b[2]:        # 跨高度层段保守不直连（保留换层避障通道）
        return False
    # Bresenham 直线采样，逐点查 risk_grid[(x,y,z)] > max_risk
    ...

def simplify_path(path, risk_grid, max_risk=2, epsilon=1.0):
    # 标准 DP：找距离线段最远点，max_d > epsilon 则保留该点递归
    # 否则（中间点都在容差内）先 line_of_sight 检查 i->j 直连是否安全：
    #   安全 → 全删中间点；穿禁飞 → 保留最远点并递归
    ...
```

实测：38 点 → 8 点，绕行率 9.2% → 7.6%，每段直线不穿禁飞。

## 4. 配套增强（加分项，评委一眼看出工程价值）

- **续航约束**：`RoutePlanner(max_flight_sec=...)`，plan 后置 `endurance_exceeded`
  （路径仍返回，业务层判"不可达/需换机"），别在 plan 里直接返回 None 丢路径。
- **GeoJSON/航点导出**：LineString 三维坐标 `[x, y, alt_m]` + 起点/终点 Point，
  z 索引用 `z_layers` 转米。网格坐标即可（真经纬度需 geo_align 二次转换，t003 无锚点）。
- **途中风险动态校验**：沿路径按飞行时间每 ~10min 采样，`load_gift_hour(forecast_offset=ceil(t/3600))`
  查未来时次阵风/雷暴，达禁飞级则告警——比"起飞时算一次"更真实。
- **批量风险分级 API**：`/api/v1/risk` 支持 `{"points":[{"id","elements"},...]}`，
  单点 `{"elements":{...}}` 向后兼容。
- **pytest 单测**：赛题提交含 tests/（`python -m pytest tests/`）体现工程质量，
  打包脚本把 tests/ + requirements-dev.txt 一并收进 zip。

## 5. 验证纪律

- 每改一处跑对应验证；最终一次性 ad-hoc 断言脚本（D:\Temp\UserTemp\hermes-verify-*.py，跑完删）
  覆盖所有改动点（时次对齐/启发/平滑/导出/批量/续航/参数可解析）。
- **改完数据读取逻辑后，report/ 里的旧图和报告全部作废**（基于旧错位数据生成），
  提交前必须重新跑 main_test/batch_test/finish_tasks/ablation_study/compare_scenes 再重新打包。
