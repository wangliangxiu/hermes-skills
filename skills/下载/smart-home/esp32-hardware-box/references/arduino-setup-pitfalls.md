# Arduino IDE Setup Pitfalls for Windows Beginners

## 1. Download — Don't Get Tricked!

| ❌ Wrong Download | ✅ Right Download |
|:-----------------|:-----------------|
| `arduino-ide.org` (third-party Chinese mirror/promotional site, not official) | Only `arduino.cc/en/software` |
| **Arduino PLC IDE** (industrial PLC tool, not for ESP32) | Select the **Win 10 and newer** big green button |
| **ArduinoAppLab** (different tool entirely) | File name: `arduino-ide_x.x.x_Windows_64bit.exe` |
| **MSI installer** (second choice) | NSIS `.exe` installer (first choice, ~200MB+) |
| **ZIP package** (manual install) | Easiest: just double-click the NSIS installer |

## 2. Installation Steps (Chinese)

1. 双击 `.exe` 安装包
2. 语言选"中文"（如有）
3. 安装路径：**默认 C 盘** 或改为 **D:\\ArduinoIDE**
4. 一路"下一步"/"同意"

## 3. Library Path (if IDE installed to D:)

Even if IDE is on D:, libraries default to:
`C:\\Users\\<用户名>\\Documents\\Arduino\\libraries\\`

**To move to D::**
- **文件 → 首选项**
- 将 **「项目文件位置」**（Sketchbook location）改为 `D:\\Arduino`
- 点确定
- 之后装的库会到 `D:\\Arduino\\libraries\\`

## 4. Adding ESP32 Board Support

1. **文件 → 首选项**
2. 在 **「附加开发板管理器网址」** 添加（用逗号分隔多个）：
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
3. **⚠️ 关键：点「确定」→ 完全关闭 Arduino IDE → 重新打开**（否则列表不刷新）
4. 点左侧 **📚 库管理器**（书图标，第三个）装需要的库
5. 点左侧 **🔍 开发板管理器**（电路板图标，第二个）
6. 搜索 **ESP32**
7. 安装 **esp32 by Espressif Systems**（不是 Adafruit 的，不是 Arduino Nano ESP）

## 5. Installing Libraries

| Library | Purpose | How to Install |
|---------|---------|---------------|
| **TFT_eSPI** (by Bodmer) | Screen driver (ST7789, etc.) | Library Manager → search → install |
| **Adafruit MAX98357** | I2S audio amplifier | Library Manager OR manual ZIP install |

**If Library Manager can't find a library (network issues/GitHub blocked):**
1. Go to the GitHub repo
2. Download ZIP
3. Arduino IDE → **项目 → 加载库 → 添加 .ZIP 库**
4. Select the downloaded ZIP file

## 6. ESP32-S3 Driver (CH340/CH343 on Windows)

合成 ESP32-S3 N16R8 等国产板通常需要 CH340 驱动：

1. 打开 `www.wch.cn/download/CH341SER_EXE.html`（沁恒官方）
2. 下载并安装
3. **必须重启电脑**（驱动才能生效）
4. 插上板子，检查设备管理器是否有新 COM 口

## 7. Identifying the Two USB Ports on ESP32-S3

| Port Label | Function | Use for |
|:----------:|:--------:|:-------:|
| **COM** / **UART** | Serial + programming | **✅ 烧录用这个口** |
| **USB** | USB-OTG (keyboard, flash drive) | ❌ 不能烧录 |

If nothing shows up in device manager after plugging in:
1. Try the **other** Type-C port
2. Replace the USB cable (some cables are charge-only)
3. Install CH340 driver
4. Restart computer

## 8. First Upload Checklist

- [ ] ESP32-S3 Dev Board selected in IDE
- [ ] Correct COM port selected in **工具 → 端口**
- [ ] USB cable is a **data cable** (not charge-only)
- [ ] Plugged into **COM/UART** port (not USB-OTG port)
- [ ] TFT_eSPI User_Setup.h configured correctly (driver, pins, resolution)
- [ ] ESP32 board package installed via Board Manager
- [ ] All `#include` libraries installed via Library Manager

## 9. Common Error Messages & Fixes

| Error | Likely Cause | Fix |
|:------|:-------------|:----|
| "Failed to connect" | Wrong COM port / no driver | Check port, install CH340, reboot |
| "A fatal error occurred: Failed to connect to ESP32" | Not in download mode | Hold BOOT → tap RST → release BOOT |
| "Compilation error: TFT_eSPI.h: No such file" | TFT_eSPI library not installed | Install via Library Manager |
| "Tone was not declared" | Old ESP32 core | Update esp32 board package |
| "Serial port not found" | Wrong cable / wrong port | Try data cable, try other USB port |
| Upload succeeds but screen stays black | User_Setup.h wrong pins | Check CS/DC/RST/MOSI/SCLK match wiring |
