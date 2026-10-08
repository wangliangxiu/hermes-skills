# Workbuddy Integration: 让 workbuddy 执行安装/配置步骤

用户有时会让 workbuddy（一个能操作电脑的工具/助理）执行安装配置步骤。这种情况下，AI 需要准备**可直接交付的详细操作指引**，让 workbuddy 按步骤执行。

## 交付格式要求

1. **清单化** — 步骤编号，每步一句话
2. **包含完整的按钮文字和路径** — 用户英文界面看不懂，需要写 "点左侧第三个图标（📚书状）" 而不是 "打开库管理器"
3. **标明需要点的位置和顺序**
4. 执行完毕后，**AI 需要验证 workbuddy 的执行结果**（检查文件是否安装、目录是否正确）

## 验证 checklist

workbuddy 执行完后，AI 应检查：
- 库文件是否在正确路径（注意库默认放 C 盘，除非改过）
- 开发板是否选中
- 所有需要的库是否全部安装（不要漏装）

## 典型验证命令（Windows bash）

```bash
# 检查库是否安装
/usr/bin/ls "/c/Users/<用户名>/Documents/Arduino/libraries/"
# 或如果改过路径：
/usr/bin/ls "/d/Arduino/libraries/"
```

注意：中文用户名在 bash 中可能导致路径显示乱码，但文件操作仍可用双引号包住路径执行。
