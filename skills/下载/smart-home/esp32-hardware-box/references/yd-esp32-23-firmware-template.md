# YD-ESP32-23 固件模板参考

## 板子信息

- **型号：** YD-ESP32-23 (2022-v1.3)
- **芯片：** 经典 ESP32（非 ESP32-S3）
- **USB 芯片：** CH343（驱动用 CH341SER.EXE 或 CH343SER.EXE）
- **IDE 板子选择：** ESP32 Dev Board（不是 ESP32S3 Dev Module）

## 引脚定义

```
// 屏幕 ST7789 (SPI)
TFT_MOSI = 13, TFT_SCLK = 14
TFT_CS   = 10, TFT_DC   = 11
TFT_RST  = 12, TFT_BL   = 15

// 麦克风 INMP441 (I2S)
I2S_MIC_BCLK = 4, I2S_MIC_LRC = 5, I2S_MIC_DIN = 6

// 功放 MAX98357 (I2S) — 用原生 driver/i2s.h，不用 Adafruit 库
I2S_AMP_BCLK = 7, I2S_AMP_LRC = 8, I2S_AMP_DOUT = 9

// 按键
BTN_WAKE = 1, BTN_MODE = 2, BTN_CONFIRM = 3
```

## 关键修改记录

### 2026-06-28: 从 S3 固件改为经典 ESP32

**改了什么：**
1. 去掉 `#include <Adafruit_MAX98357.h>` — 用 `driver/i2s.h` 替代
2. 去掉 TFT_eSPI 的 pin 重定义（User_Setup.h 已配好）
3. 添加原生 I2S 初始化函数（`initI2SMic()` 和 `initI2SAmp()`）
4. WiFi 密码填入用户实际密码（用 `netsh wlan show profiles` 查询）

**原始固件位置：** `D:\HermesStudio\zhender_box\zhender_box.ino`

## 烧录检查清单

- [ ] 工具 → 开发板 → ESP32 Dev Board
- [ ] 工具 → 端口 → COM3（或实际端口号）
- [ ] WiFi 名和密码已填写
- [ ] USB 线能传数据（板子红灯亮）
- [ ] User_Setup.h 中 ST7789 驱动已启用，引脚已配置
- [ ] TFT_eSPI 库已安装

## 典型烧录流程

```
1. 打开 Arduino IDE
2. 文件 → 打开 → D:\HermesStudio\zhender_box\zhender_box.ino
3. 工具 → 开发板 → ESP32 Dev Board
4. 工具 → 端口 → COM3
5. 点 →（上传）
6. 等待编译（1-3分钟）
7. 等待上传完成
8. 板子自动重启，屏幕显示启动画面
```
