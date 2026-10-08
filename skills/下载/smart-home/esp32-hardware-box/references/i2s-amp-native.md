# MAX98357 with native driver/i2s.h (no Adafruit library)

The Adafruit_MAX98357 library is optional. ESP32's built-in `driver/i2s.h` works directly.

## Minimal init for MAX98357 (I2S output/amp)

```cpp
#include <driver/i2s.h>

#define I2S_AMP_BCLK 7
#define I2S_AMP_LRC  8
#define I2S_AMP_DOUT 9

#define SAMPLE_RATE   16000
#define I2S_AMP_PORT  I2S_NUM_1

void initI2SAmp() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = 1024,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_AMP_BCLK,
        .ws_io_num = I2S_AMP_LRC,
        .data_out_num = I2S_AMP_DOUT,
        .data_in_num = I2S_PIN_NO_CHANGE
    };

    i2s_driver_install(I2S_AMP_PORT, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_AMP_PORT, &pin_config);
}
```

## Minimal init for INMP441 (I2S input/mic)

```cpp
#include <driver/i2s.h>

#define I2S_MIC_BCLK 4
#define I2S_MIC_LRC  5
#define I2S_MIC_DIN  6

#define SAMPLE_RATE   16000
#define I2S_MIC_PORT  I2S_NUM_0

void initI2SMic() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = 1024,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_MIC_BCLK,
        .ws_io_num = I2S_MIC_LRC,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_MIC_DIN
    };

    i2s_driver_install(I2S_MIC_PORT, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_MIC_PORT, &pin_config);
}
```

## Notes
- I2S_NUM_0 and I2S_NUM_1 are separate I2S controllers on the ESP32 — mic and amp can run simultaneously
- `I2S_COMM_FORMAT_STAND_I2S` is the v3.x+ constant; on older esp32-arduino use `I2S_COMM_FORMAT_I2S`
- Default DMA buffers (4 × 1024) are fine for voice; for music increase to 8 × 2048
