// ============================================================
// 甄der小盒子 · ESP32-S3 固件模板
// 硬件：ESP32-S3 + ST7789 170x320 + INMP441 + MAX98357 + 按键
//
// 使用说明：
// 1. 修改 WiFi 配置（SSID 和密码）
// 2. 按实际屏幕分辨率调整 TFT_WIDTH / TFT_HEIGHT
// 3. 在 Arduino IDE 中烧录
// ============================================================

#include <Arduino.h>
#include <WiFi.h>
#include <TFT_eSPI.h>
#include <driver/i2s.h>

// ==================== 配置区 ====================
// --- 请修改以下配置 ---

// WiFi
const char* ssid = "你的WiFi名";
const char* password = "你的WiFi密码";

// Hermes Agent 服务器地址（电脑端运行 Hermes 的地址）
const char* hermes_host = "192.168.1.100";  // 改成你电脑的IP
const int hermes_port = 8080;

// ==================== 引脚定义 ====================

// ST7789 屏幕（由 TFT_eSPI 库的 User_Setup.h 配置）

// INMP441 I2S 麦克风
#define I2S_MIC_BCLK  4
#define I2S_MIC_LRC   5
#define I2S_MIC_DIN   6

// MAX98357 I2S 功放
#define I2S_AMP_BCLK  7
#define I2S_AMP_LRC   8
#define I2S_AMP_DOUT  9

// 按键
#define BTN_WAKE      1   // 唤醒/对话键
#define BTN_MODE      2   // 模式切换
#define BTN_CONFIRM   3   // 确认/确认

// 录音参数
#define SAMPLE_RATE   16000
#define RECORD_SEC    5
#define BUFFER_SIZE   (SAMPLE_RATE * RECORD_SEC)

// ==================== 颜文字库 ====================

const char* emoji_happy[] = {
    "(｡>ㅅ<｡)♡",
    "(๑˃̵ᴗ˂̵)و",
    "( ´ ▽ ` )ﾉ",
    "ヾ(´▽｀*)ゝ",
    "(๑¯◡¯๑)",
    "٩(◕‿◕｡)۶"
};

const char* emoji_greeting[] = {
    "(｡´･ω･｡)ﾉ♡",
    "(๑•̀ㅂ•́)و✧",
    "ฅ(^◕ᴥ◕^)ฅ",
    "(*´∀`)~♥"
};

const char* emoji_sad[] = {
    "(´；ω；｀)",
    "(๑´•.̫ • `๑)",
    "(´∩｀.)",
    "(｡•́︿•̀｡)"
};

const char* emoji_cute[] = {
    "=✪ᆽ✪=",
    "(ฅ´ω`ฅ)",
    "(ᐡ •͈ ·̭ •͈ ᐡ)",
    "(◦˘ З˘)♡",
    "₍˄·͈༝·͈˄₎ฅ˒˒"
};

const char* emoji_shy[] = {
    "(´｡• ᵕ •｡`)",
    "(๑´ㅂ`๑)",
    "(ᵒ̤̑ ₀̑ ᵒ̤̑)",
    "(*/ω＼*)"
};

const char* emoji_sleep[] = {
    "(。-ω-)zzz",
    "(ᴗ˳ᴗ)💤",
    "(´-﹏-`；)",
    "( ´◔‸◔`)"
};

const char* emoji_proud[] = {
    "ᕦ(ò_Óˇ)ᕤ",
    "(｀・ω・´)",
    "(๑•̀ㅂ•́)و✧",
    "※\(^o^)/※"
};

// ==================== 对象 ====================

TFT_eSPI tft = TFT_eSPI(170, 320);  // 按实际分辨率修改

// ==================== 显示函数 ====================

void showEmoji(const char* emoji) {
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.setTextSize(2);

    int16_t x1, y1;
    uint16_t w, h;
    tft.getTextBounds(emoji, 0, 0, &x1, &y1, &w, &h);
    tft.setCursor((tft.width() - w) / 2, (tft.height() - h) / 2);
    tft.print(emoji);
}

void showStatus(const char* text, uint16_t color, const char* emoji) {
    tft.fillScreen(TFT_BLACK);

    // 上半部分：颜文字
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.setTextSize(2);
    int16_t x1, y1;
    uint16_t w, h;
    tft.getTextBounds(emoji, 0, 0, &x1, &y1, &w, &h);
    tft.setCursor((tft.width() - w) / 2, (tft.height() - h) / 2 - 30);
    tft.print(emoji);

    // 下半部分：文字
    tft.setTextColor(color, TFT_BLACK);
    tft.setTextSize(1);
    tft.getTextBounds(text, 0, 0, &x1, &y1, &w, &h);
    tft.setCursor((tft.width() - w) / 2, (tft.height() - h) / 2 + 30);
    tft.print(text);
}

void showStartup() {
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_CYAN, TFT_BLACK);
    tft.setTextSize(3);
    tft.setCursor(30, 100);
    tft.println("甄der");
    tft.setTextSize(1);
    tft.setTextColor(TFT_GREEN, TFT_BLACK);
    tft.setCursor(30, 160);
    tft.println("(=✆ᆽ✆=) 启动中...");
}

// ==================== WiFi ====================

void connectWiFi() {
    showEmoji("(｡´･ω･｡)ﾉ♡");
    WiFi.begin(ssid, password);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 40) {
        delay(500);
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        showStatus("WiFi OK!", TFT_GREEN, "(๑¯◡¯๑)");
    } else {
        showStatus("WiFi Failed", TFT_RED, "(´；ω；｀)");
    }
    delay(1500);
}

// ==================== 按键 ====================

void setupButtons() {
    pinMode(BTN_WAKE, INPUT_PULLUP);
    pinMode(BTN_MODE, INPUT_PULLUP);
    pinMode(BTN_CONFIRM, INPUT_PULLUP);
}

// ==================== 录音 ====================

void setupMic() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = 0,
        .dma_buf_count = 8,
        .dma_buf_len = 256
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_MIC_BCLK,
        .ws_io_num = I2S_MIC_LRC,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_MIC_DIN
    };

    i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config);
}

void startRecording() {
    showStatus("听着呢", TFT_GREEN, "(｀・ω・´)");

    int16_t* buffer = (int16_t*)malloc(BUFFER_SIZE * sizeof(int16_t));
    if (!buffer) return;

    size_t bytes_read = 0;
    i2s_read(I2S_NUM_0, buffer, BUFFER_SIZE * sizeof(int16_t), &bytes_read, portMAX_DELAY);

    // TODO: 将音频数据通过 WiFi 发送到 Hermes Agent
    // TODO: 接收回复文本，显示在屏幕上
    // TODO: 通过 MAX98357 播放语音回复

    free(buffer);
}

// ==================== 随机颜文字 ====================

const char* randomEmoji(const char** emojiSet, int count) {
    return emojiSet[random(0, count)];
}

// ==================== 初始化 ====================

void setup() {
    Serial.begin(115200);
    randomSeed(analogRead(0));

    // 初始化屏幕
    tft.init();
    tft.setRotation(3);  // 横屏/竖屏，按实际安装方向调整
    tft.fillScreen(TFT_BLACK);

    showStartup();
    delay(2000);

    connectWiFi();
    setupButtons();
    setupMic();

    // 开机完成，显示颜文字
    showStatus("主人我在呢", TFT_CYAN, "(๑¯◡¯๑)");
    delay(2000);
    showEmoji(randomEmoji(emoji_greeting, 4));
}

// ==================== 主循环 ====================

void loop() {
    if (digitalRead(BTN_WAKE) == LOW) {  // 唤醒/对话
        delay(50);  // 消抖
        startRecording();
        delay(500);
        showEmoji(randomEmoji(emoji_happy, 6));
    }

    if (digitalRead(BTN_MODE) == LOW) {  // 切换模式
        delay(50);
        // 轮换显示不同情绪颜文字
        static int mode = 0;
        mode = (mode + 1) % 5;
        switch (mode) {
            case 0: showEmoji(randomEmoji(emoji_happy, 6)); break;
            case 1: showEmoji(randomEmoji(emoji_cute, 5)); break;
            case 2: showEmoji(randomEmoji(emoji_shy, 4)); break;
            case 3: showEmoji(randomEmoji(emoji_proud, 4)); break;
            case 4: showEmoji(randomEmoji(emoji_sleep, 4)); break;
        }
    }

    if (digitalRead(BTN_CONFIRM) == LOW) {  // 确认/夸夸
        delay(50);
        showEmoji(randomEmoji(emoji_proud, 4));
    }

    delay(100);
}
