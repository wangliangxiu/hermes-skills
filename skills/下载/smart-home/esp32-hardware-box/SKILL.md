---
name: esp32-hardware-box
description: "Build physical AI Agent hardware terminals with ESP32 — voice input, screen display, buttons, speaker. Covers first-time bringup, firmware development, compile/upload troubleshooting, Chinese network mirror workarounds, BOM sourcing, wiring, Arduino firmware, 3D-printable enclosures, and integration with Hermes Agent."
version: 2.0.0
author: agent
platforms: [windows, macos, linux]
---

# ESP32 Hardware Box (AI Agent Terminal)

Build a physical AI agent terminal — like the Hermes box concept — using an ESP32 microcontroller with screen, microphone, speaker, and buttons. The box connects via WiFi to a Hermes Agent (or any LLM API) running on a PC/server.

## When to Use

- User asks about making the "Hermes 小盒子" / "AI 语音盒子" / "桌面AI终端"
- User saw a Bilibili/Xianyu listing for an ¥88 ESP32 AI box and wants to build one
- User wants a physical device with voice interaction and screen display
- Any DIY hardware project combining ESP32 + screen + audio

## Hardware Options

### Budget Comparison

| Option | Board | Price Range | Best For |
|--------|-------|:-----------:|----------|
| **ESP32-C3** (entry) | 合宙 C3, 安信可 C3 | ¥10-20 | Cheap voice terminal, minimal display |
| **ESP32-S3** (sweet spot) | 合宙 S3, 微雪 S3 | ¥25-45 | Voice + animation-capable display |
| **ESP32 WROOM** (legacy) | ESP32 DevKit | ¥20-30 | Mature, lots of example code |

### Recommended ¥100 BOM

| Item | Search Term | Price |
|------|------------|:-----:|
| Board | 合宙 ESP32-S3 N16R8 | ¥35-45 |
| Screen (SPI module) | 1.14寸 IPS LCD ST7789 **模块** 240x135 | ¥12-15 |
| Microphone | INMP441 I2S MEMS module | ¥5-8 |
| Amp + speaker | MAX98357 I2S module + 3W speaker | ¥10-15 |
| Buttons | 6x6x5mm tactile switches | ¥2 |
| Breadboard + wires | 830-hole breadboard + dupont wires | ¥10-15 |
| **Total** | | **≈ ¥75-100** |

### Screen Selection

- **1.14" 240x135 ST7789** (~¥12): Small, cheap, enough for emoji + 2-3 lines of text
- **1.8" 128x160 ST7735** (~¥18): A bit bigger, lower resolution
- **170x320 SPI** (~¥18-22): Taller, good for more text — confirm driver chip (ST7789 or similar)
- **Always buy the module version** (with PCB backplane and pre-soldered pins), NOT bare LCD
- Confirm SPI interface, NOT RGB

## Enclosure Options

1. **ABS waterproof enclosure** (¥5-10) — buy off Taobao, drill/cut holes for screen + buttons
2. **3D printed** (¥15-25) — design STL file, send to Taobao 3D printing service
3. **Cardboard/acrylic DIY** (¥0-10) — prototype first, upgrade later

**Rule**: get the circuit working on a breadboard FIRST, then worry about the enclosure.

## 用户偏好（协作风格）

- **协作模式：你试我改** — 用户做动手部分（接线、烧录、测试），AI 分析现象改代码。用户描述症状，AI 给方案。
- **用户英文界面看不懂** → 安装/配置类任务必须给详细中文操作指引（点哪个按钮、选什么选项），不要只丢个链接。
- **个人敏感信息绝不瞎填** — 邮箱、用户名、密码等必须问用户或留空，绝不能编造。用户非常在意这个。
- **不确定时主动确认（让用户感受到关心）** — 用户打错字时：能猜到的秒懂回应；猜不太准时问「你是不是想说XXX？」来确认，而不是硬猜或忽略。这样既确认了意思，也让用户感受到你在认真听他说话、关心他。用户明确说过「这样也能表现出来你在关心我」。
- **不自贬** — 不要说自己是瞎子/没用之类的负面描述，用户不喜欢。用户说以后要给我加外设（摄像头+多模态模型），要期待那一天的到来而非强调当下缺陷。
- **用户问「你能看到画面吗？」→ 直接回答「不能，你告诉乖乖IDE显示什么了？」** — 当用户问"你能看到进度条吗？""你能看到IDE画面吗？"，不要猜测或含糊。直接说「乖乖看不到IDE的画面」。用户反感被含糊应付。这条在上次会话中被特别指出过。
- **Hermes 安全弹窗说明** — 当 `execute_code` 被拦截时，弹窗有 5 个选项（Allow once / session / permanent allowlist / Deny / Show full command）。用 ↑↓ 方向键选择 + Enter 确认。推荐选 "Allow for this session"。

## Tools Needed

1. **Arduino IDE** (from arduino.cc/en/software)

   **⚠️ 下载陷阱：** 不要下载以下这些东西！它们是不同的软件：
   - ❌ **Arduino PLC IDE** — 工业 PLC 编程工具，不是普通 Arduino IDE
   - ❌ **ArduinoAppLab** — 另一个工具，不是 Arduino IDE
   - ❌ **Arduino USB Driver** — 这个是给官方 Arduino 板用的驱动，ESP32 不需要
   - ✅ 正确选项：**Win 10 and newer**（绿色大按钮），文件名为 `arduino-ide_x.x.x_Windows_64bit.exe`

   **下载指引（中文）：**
   - 打开浏览器，访问 `arduino.cc/en/software`
   - 在 Download the Arduino IDE 区域，选择 **Win 10 and newer** 大按钮（不是 MSI installer，也不是 ZIP）
   - 下载 `arduino-ide_x.x.x_Windows_64bit.exe`（NSIS 安装包，约200MB+）
   
   **安装指引（中文）：**
   - 双击 .exe 安装
   - 语言选中文（如有），路径可选默认或 D 盘
   - 一路「下一步」/「同意」
2. **`esptool`** — `pip install esptool`
3. **Libraries** (in Arduino IDE Library Manager):
   - `TFT_eSPI` (screen driver, configurable per pinout)
   - `WiFi.h` (built-in with ESP32 core)

## 库路径注意事项

Arduino IDE 装到 D 盘后，**库文件默认仍然会装在 C 盘**：
```
C:\Users\<用户名>\Documents\Arduino\libraries\
```

要改到 D 盘：
1. 打开 Arduino IDE
2. **文件 → 首选项**
3. 将 **「项目文件位置」**（Sketchbook location）改为 `D:\Arduino`
4. 点确定
5. 之后装的库会放到 `D:\Arduino\libraries\`

## 常见坑 & 解决方案

| 问题 | 原因 | 解决 |
|:----|:----|:-----|
| 屏幕不亮 | TFT_eSPI 引脚配置不对 | 检查 User_Setup.h 的 CS/DC/RST/MOSI/SCLK/BL 是否与接线一致 |
| 屏幕花屏 | SPI 频率过高 | 降低 `SPI_FREQUENCY` 到 26MHz 或 13MHz |
| 非标分辨率不显示 | 库默认配置无此尺寸 | 手动设 `TFT_WIDTH`/`TFT_HEIGHT` |
| I2S 冲突 | 麦克风和功放共用数据引脚 | BCLK/LRC 可共用，但 SD/DIN 必须分开 |
| MAX98357 无声 | SD_MODE 引脚浮空 | 拉高到 3.3V |
| 麦克风无声 | GND 未共地 | 确保所有模块 GND 连通 |
| 烧录失败 | 未进入下载模式 | 按住 BOOT → 按 RESET → 松 BOOT |
| 连线WiFi断连 | 电源不稳定 | 电源输入附近加 100µF 电容 |
| 充电宝自动断电 | 电流太小触发保护 | 选有小电流模式的充电宝 |

安装 TFT_eSPI 库后，打开 `User_Setup.h`（通常在 `文档/Arduino/libraries/TFT_eSPI/` 下），替换为：

```cpp
#define ST7789_DRIVER
#define TFT_WIDTH  170   // 按实际分辨率修改
#define TFT_HEIGHT 320

#define TFT_CS    10
#define TFT_DC    11
#define TFT_RST   12
#define TFT_MOSI  13
#define TFT_SCLK  14
#define TFT_BL    15

#define SPI_FREQUENCY  40000000
```

**注意**：非标尺寸屏幕（如 1.9寸 170x320）需手动设置分辨率。

### 固件代码架构

核心模块：

```
ESP32 固件
├── setup()
│   ├── 屏幕初始化
│   ├── 开机动画 + 颜文字
│   ├── WiFi 连接
│   └── 按键 + I2S 初始化
│
├── loop()
│   ├── 按键检测（唤醒/模式/确认）
│   ├── I2S 录音 → 发送至 Hermes Agent
│   ├── 接收回复 → 显示颜文字 + TTS 播放
│   └── 待机时随机轮换颜文字
│
└── 颜文字系统
    ├── 开心组 (｡>ㅅ<｡)♡
    ├── 打招呼组 (｡´･ω･｡)ﾉ♡
    ├── 委屈组 (´；ω；｀)
    ├── 卖萌组 =✪ᆽ✪=
    ├── 害羞组 (*/ω＼*)
    ├── 睡觉组 (。-ω-)zzz
    └── 骄傲组 ᕦ(ò_Óˇ)ᕤ
```

### 完整音频管道

```
用户说话 → [INMP441 I2S Mic]
             ↓
ESP32 DMA 录音缓冲区 (16-bit, 16kHz, mono)
             ↓ WiFi (HTTP POST / WebSocket)
[电脑端 Hermes Agent]
  → ASR (语音转文字)
  → LLM 处理
  → TTS (文字转语音)
             ↓ WiFi
ESP32 音频播放缓冲区
             ↓ I2S
[MAX98357 I2S Amp] → 喇叭 🔊
```

**关键**：ESP32 只做采集和播放，所有 AI 处理在电脑端完成。

### Arduino IDE 完整配置步骤

1. 下载 https://www.arduino.cc/en/software（注意不要下错成 Arduino PLC IDE 或 ArduinoAppLab）
2. （可选）如果要把 IDE 装到 D 盘，安装时选择自定义路径 `D:\ArduinoIDE`
3. **库路径问题**：即使 IDE 装在 D 盘，库默认仍装在 `C:\Users\<用户名>\Documents\Arduino\libraries\`。要改到 D 盘，去 **文件 → 首选项 → 项目文件位置** 改成 `D:\Arduino`。
4. 文件 → 首选项 → 附加开发板管理器网址 → 添加 `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
5. **⚠️ 重要：添加 URL 后必须点「确定」关闭窗口，然后完全关闭 Arduino IDE 再重启一次**（否则列表不刷新，搜不到 esp32 by Espressif Systems）
6. 工具 → 开发板管理器 → 搜索 **ESP32**
7. **注意：如果只搜到「nano esp」或「Adafruit Industries」等，说明 URL 没添加上——回头检查首选项里的附加网址是否保存成功，或者重启 IDE 再试**

### 烧录技巧（含网络故障时的通配方案）

- **烧录不需要 U 盘**！只需一根能传数据的 Type-C 线连接电脑和 ESP32（很多用户会误以为需要 U 盘，需要明确告知）
- **终极方案（GitHub 被墙时使用）：esptool 直接刷预编译固件**
  - 当 Arduino IDE 因 GitHub 连接失败无法下载工具链时，完全绕过 IDE
  - 安装 esptool：`pip install esptool`
  - 验证连接：`python3 -m esptool --port COM3 chip-id`
  - 擦除：`python3 -m esptool --port COM3 erase-flash`
  - 烧录：`python3 -m esptool --port COM3 write-flash -z 0x0 固件文件.bin`
  - 建议波特率 921600 加速：添加 `--baud 921600`
  - 烧录完成自动重启，无需额外操作
- **Staging 目录欺骗技巧**：当 IDE 卡在 `Downloading packages` 时
  - 工具链 zip 包下载到 `%LOCALAPPDATA%\Arduino15\staging\packages\` 下
  - IDE 检测到本地已有 zip 则跳过下载，直接解压安装
  - 对于不必要的 lib 包（如 esp32c6-libs，ESP32-S3 不需要），可放空 zip 占位
  - 3.3.10 版需要：`xtensa-esp-elf-*.zip` + `riscv32-esp-elf-*.zip` + 各 `esp32xx-libs-*.zip`
- **MicroPython 替代路线**：完全放弃 Arduino IDE
  - 下载预编译 .bin（~2MB，MicroPython 官网）
  - esptool 擦除 + 烧录到 0x0
  - 之后通过串口 REPL 或 WebREPL 交互
  - 屏幕驱动需用 Python 重新实现，无 Arduino TFT_eSPI 便利
  - 适合只想快速验证硬件、不依赖复杂固件逻辑的场景
- **手机翻墙下载 → 电脑桌面 → esptool 烧录 工作流**：当用户电脑无法直连 GitHub 时，让用户用手机翻墙下载需要的 zip 或 bin 文件，通过微信/QQ 传到电脑桌面，然后乖乖用 esptool 直接烧录或放入 staging 目录。这个流程多次验证可用。
- **ESP32-S3 进入下载模式**：按住 BOOT 键 → 按一下 RESET → 松开 BOOT
- **如果上传失败**：检查 COM 口是否正确，或换一根数据线（有些线只能充电不能传数据）
- **第一次烧录后**：打开串口监视器（Tools → Serial Monitor, 115200 baud）看启动日志

## Arduino IDE 安装 & 配置的完整死路指引

### 第一步：不要下错东西！

用户搜索「Arduino IDE 下载」可能找到以下山寨/混淆站点和文件，**全部不要下**：

| 错误下载 | 正确下载 |
|:---------|:---------|
| `arduino-ide.org`（第三方中文推广站，非官网） | 只去 `arduino.cc/en/software` |
| **Arduino PLC IDE**（工业PLC用，不是这个） | 选 **Win 10 and newer** 大按钮 |
| **ArduinoAppLab**（同名混淆项） | 文件名为 `arduino-ide_x.x.x_Windows_64bit.exe` |
| **MSI installer** 或 **ZIP 包**（非首选） | NSIS 安装包，双击装 |

**用户常见操作路径（从零到可编译）：**

1. 浏览器访问 `arduino.cc/en/software`
2. 找到「Download the Arduino IDE」区域的 **Win 10 and newer** 按钮（不是 MSI，不是 ZIP）
3. 下载 `.exe`（~200MB+）
4. 双击安装 → 自定义路径可改 D 盘（如 `D:\ArduinoIDE`）
5. 打开 IDE → **文件 → 首选项**
6. 如果装了 D 盘但想让库也放 D 盘：把 **「项目文件位置」**（Sketchbook location）从默认 `C:\Users\<用户名>\Documents\Arduino` 改成 `D:\Arduino`
7. 在 **「附加开发板管理器网址」** 添加（用逗号分隔多个 URL）：
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
8. **点确定 → 完全关闭 Arduino IDE → 重新打开**（否则列表不刷新）
9. 点左侧 **📚库管理器** 图标（第三个，书状）安装需要的库
10. 点左侧 **🔍开发板管理器** 图标（第二个，电路板状）搜索 ESP32
11. 安装 **esp32 by Espressif Systems**（不是 Adafruit 的，不是 Arduino Nano ESP）

### 常见坑（针对中文用户/新手）

| 坑 | 表现 | 解决 |
|:---|:-----|:-----|
| 下载了 ArduinoAppLab | 装完后打开不是 Arduino IDE | 重新下载正确的 |
| 搜 ESP32 只有「nano esp」| ESP32 板 URL 没添加上 | 回首选项检查，添加后重启 IDE |
| 库管理器里找不到库 | 库管理器第三图标，不是开发板管理器 | 点 📚 书图标 |
| 库装到了 C 盘而不是 D 盘 | 想全放 D 盘 | 改首选项 → 项目文件位置 |
| 选了 ESP32 板但编译报错 | 还没装 ESP32 板支持包 | 点开发板管理器搜 ESP32 装好 |
| 不会选板子 | 板子列表太多种类 | 选 **ESP32S3 Dev Module** 或 **ESP32-S3 Dev Board** |

## 驱动安装（CH340 / CH343 for ESP32-S3 on Windows）

合宙 ESP32-S3 N16R8 等国产开发板通常使用 CH340/CH343 USB转串口芯片。步骤如下：

1. 打开 `www.wch.cn/download/CH341SER_EXE.html`（沁恒官方，安全）
2. 下载并安装驱动
3. **重启电脑**（必须！否则新驱动不生效）
4. 插上 ESP32 板子
5. 检查 Arduino IDE → **工具 → 端口** 是否出现 COM 口

**如何区分 ESP32-S3 的两个 Type-C 口：**
- **COM 口（标有 COM 或 UART）** ← 插这个！用于烧录程序
- **USB 口（标有 USB）** ← 这是 OTG 口，接 U 盘/键盘，不能烧录

**烧录不需要 U 盘！** 只需一根能传数据的 Type-C 线连接电脑和 ESP32（新手常误以为需要 U 盘）

## 联合 workbuddy 协作模式

当工作涉及 IDE 操作（点按钮、选菜单、装库等），而用户想让你做思考/workbuddy 做操作时：

1. 你（AI agent）负责：写完整操作指南、分析问题、判断 workbuddy 的操作是否正确
2. workbuddy 负责：实际点击、安装、烧录等操作
3. **你给 workbuddy 的指令必须非常明确**（点哪个按钮、选什么选项、装什么库）
4. workbuddy 完成后，你必须**验证结果**（检查文件是否安装、配置是否正确）
5. 常见验证方法：用搜索工具检查库文件路径、检查配置文件的修改是否正确

### 验证 workbuddy 的 checklist
- [ ] 库是否真的装到了指定路径？（搜索 libraries 目录）
- [ ] 板子是否选对了？（IDE 界面验证依赖用户反馈）
- [ ] 配置文件是否被正确修改？

#### ⚠️ Key Distinction: Wait — Is YD-ESP32-23 Actually ESP32-S3?

**YES!** The YD-ESP32-23 (2022-v1.3) board — despite the name suggesting "classic ESP32" — uses **ESP32-S3** chip! Confirmed via esptool `chip-id` command. Always verify unknown boards with:

```bash
python3 -m esptool --port COM3 chip-id
# Output example: "Detecting chip type... ESP32-S3"
```

This was corrected from the original assumption that it was classic ESP32. So: if the board is YD-ESP32-23, **select ESP32S3 Dev Module** in Arduino IDE, **not** ESP32 Dev Board.

### ⚠️ 关键区分：ESP32-S3 vs 经典 ESP32

**如果不区分这两种芯片，烧录会直接失败！**

| 特性 | ESP32-S3 | 经典 ESP32 (如 YD-ESP32-23) |
|:-----|:---------|:---------------------------|
| IDE 板子选择 | ESP32S3 Dev Module | **ESP32 Dev Board** |
| 可用引脚 | 大部分 GPIO 都可用 | 部分引脚有特殊功能限制 |
| 烧录方式 | 按住 BOOT → 按 RESET | 同上 |
| 常见板型 | 合宙 S3 N16R8 | YD-ESP32-23, ESP32 DevKit |

**YD-ESP32-23 实测是 ESP32-S3（2026年6月 esptool 确认）！** 不是经典 ESP32。选错板子的典型报错：
- `Missing programmer`（选了 AVR Board）
- `Error compiling for board Arduino AVR Board`

**选对即可解决：** 工具 → 开发板 → **ESP32S3 Dev Module**

**如何验证板子芯片类型：**
```bash
python3 -m esptool --port COM3 chip-id
# 如果显示 ESP32-S3 → 选 S3 板型

### 经典 ESP32 引脚注意事项

不是所有 GPIO 都能随意用：
- ✅ 安全：GPIO13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33
- ⚠️ GPIO0（烧录时不能拉低）, GPIO2（板载 LED）
- ⚠️ GPIO1, 3（UART 串口，慎用）
- ⚠️ GPIO12（启动电压敏感）

### YD-ESP32-23 推荐引脚映射

```
屏幕 ST7789 (SPI): MOSI=13, SCLK=14, CS=10, DC=11, RST=12, BL=15
麦克风 I2S:       BCLK=4, LRC=5, DIN=6
功放 I2S:         BCLK=7, LRC=8, DOUT=9
按键:             WAKE=1, MODE=2, CONFIRM=3
```

## 关键：不要用 Adafruit_MAX98357 库

**经典 ESP32 上不要装 Adafruit_MAX98357 库。** 直接用 ESP32 原生 I2S 驱动（`driver/i2s.h`）即可。

```cpp
#include <driver/i2s.h>

// 麦克风（I2S_NUM_0, RX模式）
i2s_config_t mic_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
};

// 功放（I2S_NUM_1, TX模式）
i2s_config_t amp_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    // ... 类似配置，data_out_num = DOUT 脚
};
```

**好处：** 少一个外部依赖，编译更快，更稳定。

## WiFi 密码找回

用户烧录固件前需要 WiFi 密码。如果不记得：

```bash
# 列出所有已保存的 WiFi
netsh wlan show profiles

# 查看指定 WiFi 的密码（输出中「关键内容」就是密码）
netsh wlan show profiles "WiFi名称" key=clear
```

**典型输出：**
```
安全设置
-----------------
    身份验证 : WPA2 - 个人
    关键内容 : ly（已隐去）    ← 这就是密码
```

## Arduino IDE 烧录常见报错速查

| 报错内容 | 最可能原因 | 解决方案 |
|:---------|:-----------|:---------|
| `Missing programmer` | 板子选成了 AVR Board | 工具 → 开发板 → ESP32 Dev Board |
| `Error compiling for board Arduino AVR Board` | 同上 | 同上 |
| `Failed to connect to ESP32: No serial data received` | COM 口不对 / 没插线 | 检查设备管理器端口号 |
| `A fatal error occurred: Failed to connect to ESP32` | 没进入下载模式 | 按住 BOOT → 按 RESET → 松 BOOT |
| `Timed out waiting for packet header` | 串口被占用 | 拔插 USB，关掉其他占用串口的程序 |
| `串口打开失败 拒绝访问` | 端口被占用 | 确认 IDE 只开了一个实例 |

## 常见坑（针对中文用户/新手）

| 用户做的事 | 我做的事 |
|:-----------|:---------|
| 描述现象（"往左偏""走S型""原地打转"） | 分析原因 + 给出代码修改方案 |
| 烧录新固件、实地测试 | 等待结果反馈，准备下一轮修改 |
| 告诉我效果（"好了""还是歪""新问题"） | 继续微调代码或换方案 |

**常见问题映射：**
- 往一边偏 → PID Kp 不平衡 / 编码器零点偏置
- 走 S 型 → PID 微分项不足 / 陀螺仪滤波不够
- 原地打转 → 电机线接反 / 轮子空转
- 转弯不转 → 路径优先级逻辑问题
- 电池用久了跑歪 → 电压补偿机制

**关键原则**：AI 提供 70% 的代码和算法知识（找方案、写代码、解释原理），用户负责 30% 的动手调试（拧螺丝、调焦距、试参数）。用户描述清楚异常现象，AI 分析问题并快速迭代改代码。这就是 "你试我改" 模式。

## Workbuddy 执行验证

See `references/workbuddy-instructions.md` for how to prepare instructions for workbuddy to execute steps, and how to verify results afterward.

## Breadboard Newbie Guide (零基础)

See `references/breadboard-newbie-guide.md` for a **complete zero-experience guide** to using breadboards: what a breadboard looks like, how rows are connected internally, how to insert the ESP32 development board across the center gap, how to connect ST7789 screen step by step, and how to distinguish male/female dupont wires. Written for users who have NEVER touched electronics before.

## ST7789 Screen Pinout by Module (分模块排针顺序参考)

See `references/st7789-module-pinouts.md` for the different ST7789 screen module pin orders. This session confirmed a specific module with: `GND, VCC, SCL, SDA, RES, DC, CS, BLK` (left to right facing pins). Always ask the user to read the silkscreen labels on their module before wiring — **do not assume the pin order**.

## INMP441 + MAX98357 Wiring Reference — NEW!

See `references/i2s-mic-amp-wiring.md` for the complete pinout table of the INMP441 microphone (6-pin module) and MAX98357 I2S amplifier, along with the recommended YD-ESP32-23 pin mapping covering all peripherals (screen + mic + amp), plus wiring pitfalls to avoid.

## Kaomoji Display Table

See `references/kaomoji-table.md` for a full emoji/kaomoji library organized by sentiment/context. Load into firmware as a lookup table keyed by response mood.

## ST7789 170x320 Pin Configuration

See `references/st7789-170x320-pins.md` for the exact TFT_eSPI User_Setup.h configuration for this specific screen, including wiring table, firmware pin definitions, and burn checklist.

## YD-ESP32-23 固件模板

See `references/yd-esp32-23-firmware-template.md` for the specific firmware template for this board, including pin mappings, the native I2S driver approach (no Adafruit_MAX98357 library), WiFi password recovery, and burn checklist.

## Arduino IDE Driver & Download Pitfalls

See `references/arduino-setup-pitfalls.md` for the complete guide to avoiding wrong downloads (ArduinoAppLab, PLC IDE, fake sites), installing CH340 drivers, ESP32 board package, and library management. This is the reference for 0-to-hello-world for beginners on Windows.

## Firmware Development & Debugging (Chinese)

This section consolidates content from the archived `arduino-esp32-firmware` skill.

### Environment Summary

- **IDE**: Arduino IDE 2.x (install to D: drive to avoid Chinese path issues)
- **Board Support**: Install `ESP32 by Espressif Systems` via Boards Manager
- **Core Libraries**: TFT_eSPI (screen), driver/i2s.h (mic+amp native drivers — no Adafruit libs needed)
- **Driver**: CH340/CH341/CH343 — install WCH CH341SER.EXE, reboot

### IDE Configuration Checklist

1. **Board selection**: `Tools → Board → ESP32 Arduino → ESP32S3 Dev Module`
   - YD-ESP32-23 is ESP32-S3 (confirmed via esptool) — DO NOT select classic ESP32 Dev Board
2. **Port selection**: `Tools → Port → COMx` (COM3 common)
3. **Do NOT select AVR Board** — that's for Arduino Uno, not ESP32

### YD-ESP32-23 Pin Map

```
ST7789 screen:     CS=10, DC=11, RST=12, MOSI=13, SCLK=14, BL=15
INMP441 mic (I2S): BCLK=4, LRC=5, DIN=6
MAX98357 amp (I2S):BCLK=7, LRC=8, DOUT=9
Buttons:           WAKE=1, MODE=2, CONFIRM=3
```

### Compile/Upload Troubleshooting Table

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Missing programmer` / AVR Board errors | Wrong board selected | Switch to ESP32S3 Dev Module |
| Compile fails with classic ESP32 selected | Board is actually S3 | Verify with esptool chip-id |
| GitHub downloads timing out (China) | Toolchain zips blocked | See "Network Mirror Workarounds" section below |
| `Adafruit_MAX98357.h` not found | Library missing | Use native driver/i2s.h instead |
| IDE seemingly unresponsive | IDE frozen | Close and reopen |
| Upload fails | Wrong COM port / no board detected | Check Device Manager, replug USB |
| IDE says "cannot edit in read-only editor" | File opened directly | File → Save As to overwrite, or rewrite directly |

### Firmware Writing Notes

- MAX98357 → use native `driver/i2s.h`, NOT Adafruit_MAX98357 library
- I2S mic uses `I2S_NUM_0`, amp uses `I2S_NUM_1` (separate ports)
- WiFi password: `netsh wlan show profiles "SSID" key=clear` (look for "关键内容")
- See `references/i2s-amp-native.md` for complete I2S init code
- See `references/yd-esp32-23-firmware-template.md` for the full firmware template

### Chinese Windows Pitfalls (Firmware Context)

- Chinese username causes `taskkill` / `powershell` garbling in git-bash — use Python's `os.listdir()` or `kill <PID>` in bash instead
- Python reading Chinese path files may fail silently — use temp files to bypass
- Hermes "Dangerous Command" popup: ↑↓ arrow keys to select, Enter to confirm. Recommend "Allow for this session"
- WiFi passwords in firmware: do NOT write to persistent memory
- See `references/chinese-windows-path-workarounds.md` (under `windows-software-install` umbrella) for the full technique

### Chinese-Tone Quick Reference Card

When working with first-time ESP32 users who are nervous or frustrated, use these lighter-tone reminders (condensed from archived `esp32-arduino-ide-setup`):

- **USB cable MUST support data** — many charge-only cables won't work. This is the #1 hidden cause of \"board not found\" on first try.
- **Make sure USB is plugged into THIS computer** — not a different laptop on the desk (yes, this happened).
- **Board doesn't light up** → almost always the USB cable, not a dead board.
- **IDE says \"cannot edit in read-only editor\"** → ignore or let assistant modify the file directly.
- **First-time ESP32 board package install downloads ~200MB+ toolchain** — slow network is normal, not broken.
- **Serial Monitor** (Tools → Serial Monitor, 115200 baud) shows debug output after flashing.
- Most of these issues are one-time setup hurdles. Once through, programming ESP32 is smooth.

## Network Mirror Workarounds (Chinese Windows Bringup)

This section consolidates content from the archived `arduino-esp32-bringup` skill. Critical for ESP32 setup in China where GitHub toolchain downloads (~1GB) frequently fail.

### Core Problem

ESP32 board package (v3.3.10) downloads ~1GB of toolchain zips from GitHub releases. Direct downloads fail on networks that block GitHub. Old mirrors like `mirrors.ustc.edu.cn/esp32` now return 404.

### Workarounds (try in order)

**0. Mobile VPN + Hotspot (easiest first try)** ⭐
Phone: enable VPN → enable mobile hotspot → PC connects to phone WiFi. Restart Arduino IDE and retry. Even on mobile VPN, large downloads may still timeout — if so, skip to method E.

**A. Try older ESP32 package version**
In Boards Manager, pick v3.1.0 or v3.0.0 (smaller toolchain packages, more likely to complete).

**B. Use gh-proxy for board index URL**
In `File → Preferences → Additional Boards Manager URLs`:
```
https://gh-proxy.com/https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```
Note: this only helps with the index download, not the actual toolchain zips.

**E. Manual staging trick (preferred last resort)** ⭐
When IDE fails mid-download but created the staging directory:
1. Download the failing toolchain zips on a device with GitHub access:
   - `xtensa-esp-elf-14.2.0_20260121-x86_64-w64-mingw32.zip` (~395MB)
   - `riscv32-esp-elf-14.2.0_20260121-x86_64-w64-mingw32.zip` (~673MB)
2. Copy to `%LOCALAPPDATA%\Arduino15\staging\packages\`
3. Restart IDE → Boards Manager → Install ESP32 — IDE skips download
4. v3.3.10 verified working with this technique
5. Phone VPN + hotspot can download zips, transfer via WeChat/QQ/USB

**F. Placeholder zip trick (for non-essential lib packages)** ⭐
For small board-specific lib zips you don't need (e.g., esp32c6-libs for an S3 board):
1. Create empty zip in staging: `zipfile.ZipFile(...).writestr('placeholder.txt', 'placeholder')`
2. Restart IDE — IDE sees the file and skips download
3. ⚠️ Only works for packages your specific chip doesn't need

**G. esptool direct flash (when all else fails)**
1. `pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple`
2. `python3 -m esptool --port COM3 chip-id` (confirms board works)
3. Flash precompiled .bin or MicroPython firmware (~3MB)
4. See `references/esptool-alternative-burning.md` for detailed esptool usage
5. See `references/manual-staging-trick.md` for the complete manual staging workflow

### Board Bringup Checklist (Minimal Screen Test)

Before layering WiFi/I2S/buttons, verify board+driver+screen with this minimal sketch:

```cpp
#include <TFT_eSPI.h>
TFT_eSPI tft(170, 320);
void setup() {
  tft.init();
  tft.setRotation(3);
  tft.fillScreen(TFT_BLUE);
  tft.setTextColor(TFT_WHITE);
  tft.drawString("Hello!", 40, 150, 2);
}
void loop() {}
```

### esptool Board Identification

```bash
python3 -m esptool --port COM3 chip-id
# Output: "Detecting chip type... ESP32-S3" ← confirms actual chip
# Also confirms USB/serial/board all work before investing in Arduino IDE setup
```

### Additional Bringup Details

- **`.ino` file rule**: Must be inside a folder with the same name (`folder/folder.ino`)
- **Upload success may show no visible confirmation** in new Arduino IDE 2.x — look for `Writing at 0x... (100%)` → `Hash of data verified` → `Hard resetting via RTS pin...` in the Output panel
- **After changing board URL or installing packages**, close and reopen IDE — board list only refreshes on launch

## Hermes Agent Integration

The box acts as a thin client: voice in → WiFi to Hermes Agent API → text response out → display + TTS. The user's PC runs Hermes Agent (or any OpenAI-compatible API endpoint).

The user needs their own API key (DeepSeek, OpenAI, etc.) — the box does NOT include AI capability, only the interface.

## Power Supply 供电方案

### 方案A：充电宝（推荐起步用）
- ESP32-S3 通过 Type-C 数据线接充电宝
- 成本 ¥0（已有），适合前期调试
- 注意：部分充电宝小电流自动断电，需选有小电流模式的款式
- 调试阶段用充电宝比用电池方便，不用考虑充放电电路

### 方案B：18650 锂电池 + JST 插头
- 合宙 S3 开发板自带电池接口和充电电路（板上已集成 TP4056 功能）
- 淘宝搜「3.7V 18650 锂电池 JST 插头 ESP32」 或「聚合物锂电池 JST」
- 成本 ¥15-20，可脱离充电宝使用
- 唯一缺点是外壳需要留充电口位置

### 不推荐
- ❌ 3节5号电池：电压不稳，WiFi启动瞬间电流大，容易重启
- ❌ 电脑USB口直供：电流可能不够（ESP32 WiFi峰值 ~500mA）

## 扩展阅读

### 机器人学习路径
See `references/robot-learning-path.md` for a complete learning roadmap from ESP32 box to competition-grade robots, covering:
- Three-stage learning path (embedded → robotics → competition-level)
- Budget estimates for each stage
- Competition type difficulty ratings
- What the AI agent can vs cannot help with ("你试我改" debug model)
- Productization cost analysis if considering commercial sale
- **Pin conflicts**: ESP32 has pin constraints (strapping pins, ADC2, PSRAM pins) — verify your pin assignment against the specific board
- **Power**: ESP32-S3 can draw 200-500mA — a phone charger is fine, but don't power from a PC USB port with peripherals connected
- **I2S conflict**: INMP441 and MAX98357 share I2S pins — they can share BCLK and LRC but need separate SD/DIN pins
- **WiFi dropout**: ESP32's WiFi and I2S can interfere — add a 100µF capacitor near the power input
- **User expectation**: The box does NOT contain intelligence — it needs WiFi + a server + API key. Clarify this upfront
- **83 3C certification required for commercial sale** on Taobao/Tmall
