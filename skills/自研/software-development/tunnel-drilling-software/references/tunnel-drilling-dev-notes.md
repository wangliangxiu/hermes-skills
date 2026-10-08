# 炮孔设计系统开发笔记

## 项目背景

帮用户（使用者，中铁十五局/本地日报背景，学Python+AI）和他的小伙伴（BIM建模，在国企机械设备厂）开发全电脑凿岩台车的智能炮孔设计系统。目标：先落地可用，再参加河南省青年科技人才创新创业大赛（种子组）。

## 技术路线选择过程

1. 先用网页版（HTML+JS）→ 用户说隧道无网络，放弃
2. 换PyQt5桌面版 → v0.4能跑，v0.5改版后闪退（exit code 3221226505）
3. 最终用tkinter（Windows自带）→ 稳定运行
4. 后续回归PyQt5（Python 3.14 + PyQt5 5.15.2 稳定）→ v0.8~v0.10

## 坐标系约定

- 屏幕坐标Y轴向下为正，导出时翻转
- 导出原点在断面中心（而非屏幕左上角）
- 单位：米（程序内部用像素绘图，通过比例尺转换）

## 开挖方式与布孔区域

- 全断面法：整圆（-90°~270°）
- 台阶法上台阶：上半圆（-90°~90°）
- 台阶法下台阶：下半圆（90°~270°）
- CD法左侧：左半部
- CD法右侧：右半部
- 双侧壁导坑：左导坑/右导坑/核心土，各约120°扇区

## v0.4→v0.10 功能演进

| 版本 | 新增 |
|:---|:---|
| v0.1 | 基础2D断面+示例炮孔 |
| v0.2 | 可调数量、圈径、深度 |
| v0.3 | 自动缩放+比例尺 |
| v0.4 | 开挖方式选择+扇形标注 |
| v0.5 | 台车参数+定位参数+3D模拟 |
| v0.6 | 全面标注+图例+易读性优化 |
| v0.7 | 2D布孔图独立+matplotlib 3D模型（可拖拽旋转） |
| v0.8 | 纯PyQt5重写（去掉matplotlib依赖）+ 钻进参数监控+报警 |
| v0.9 | JSON导入 + Word施工日志自动生成 + 点云3D分析（含实体表面模式）+ 轴向导航天花板 |
| v0.10 | 模块化拆分（drill_modules.py）+ MWD随钻记录+趋势图 + TFGM围岩识别 + 维保预警 + 能耗统计 + 铁建重工功能对标 |

## 自测验证工作流（2026-07-30 确立）

用户指出：每次改代码后不应该让用户双点测试，应该自己先用 offscreen 模式验证。

```
修改代码 → 语法检查（py_compile） → offscreen导入测试 → 确认OK → 通知用户
```

Offscreen 测试命令：
```bash
set QT_QPA_PLATFORM=offscreen && python -c "
from PyQt5.QtWidgets import QApplication
app = QApplication([])
from mymodule import MyWidget
w = MyWidget()
print('OK')
"
```

## 铁建重工对标（2026-07-30）

详见 SKILL.md 中的「功能对标分析模式」章节。

已对标功能：
- MWD随钻测量 → ✅ MWDTracker（drill_modules.py）
- TFGM围岩识别 → ✅ RockIdentifier（drill_modules.py）
- IMW维保警示 → ✅ MaintenanceTracker（drill_modules.py）
- 能耗优化 → ✅ EnergyTracker（drill_modules.py）

未覆盖的硬件层（标注 🔧，交给小伙伴）：
- AVM全景环视、CAS碰撞预警、BAP臂架姿态保持、AD-Pro专业自动钻孔、智能节水双回路

## 待开发功能

- [ ] 串口接入（全站仪NMEA/RTK数据）— 将点云查看器从模拟数据改为真实数据输入
- [ ] ADC参数自适应推荐 — 根据历史数据自动推荐下循环参数
- [ ] DXF文件导入/导出
- [ ] 打包.exe
- [ ] 坐标系转换接口（像素→施工坐标系CGCS2000）
