# INMP441 麦克风 + MAX98357 功放 接线参考

## INMP441 麦克风（6脚模块）

| 引脚 | 说明 | 接到 |
|:----|:-----|:-----|
| VDD | 电源 3.3V | 3.3V 电源 |
| GND | 地 | GND |
| DOUT | I2S 数据输出 | GPIO6（DIN） |
| BCK | I2S 位时钟 (Bit Clock) | GPIO4（BCLK） |
| WS  | I2S 左右声道选择 (Word Select/LRC) | GPIO5（LRC） |
| LR  | 左右声道选择（通常接地=左声道） | GND |

## MAX98357 功放（I2S）

| 引脚 | 说明 | 接到 |
|:----|:-----|:-----|
| VDD | 电源（可接 3.3V 或 5V） | 3.3V 或 5V |
| GND | 地 | GND |
| BCLK | 位时钟 | GPIO7（BCLK） |
| LRC  | 左右声道时钟 | GPIO8（LRC） |
| DIN  | I2S 数据输入 | GPIO9（DOUT） |
| SD_MODE | 关断/模式选择 | 拉高到 3.3V（否则无声） |

## YD-ESP32-23 完整推荐引脚映射

| 外设 | 引脚 | 功能 |
|:----|:----|:-----|
| 屏幕 CS | GPIO10 | SPI 片选 |
| 屏幕 DC | GPIO11 | 数据/命令选择 |
| 屏幕 RST | GPIO12 | 复位 |
| 屏幕 MOSI | GPIO13 | SPI 数据 |
| 屏幕 SCLK | GPIO14 | SPI 时钟 |
| 屏幕 BL | GPIO15 | 背光 |
| 麦克风 BCLK | GPIO4 | I2S 位时钟 |
| 麦克风 LRC/WS | GPIO5 | I2S 声道选择 |
| 麦克风 DOUT | GPIO6 | I2S 数据输出 |
| 功放 BCLK | GPIO7 | I2S 位时钟 |
| 功放 LRC | GPIO8 | I2S 声道选择 |
| 功放 DIN | GPIO9 | I2S 数据输入 |
| SD_MODE | 3.3V 直连 | 拉高使能输出 |

## 注意事项

1. **麦克风和功放使用不同的 I2S 端口**（I2S_NUM_0 = mic，I2S_NUM_1 = amp），不会冲突
2. **SD_MODE 不能悬空**——悬空 = 静音。必须拉到 3.3V 才有声音输出
3. **GND 必须共地**——所有模块的 GND 都要连在一起（通过面包板蓝色母线）
4. **功放 VDD 可以接 3.3V 或 5V**——3.3V 声音小一些，5V 声音大一些。先接 3.3V 安全
5. **喇叭不分正负极**——随便接两根线到 MAX98357 的输出端子就行
