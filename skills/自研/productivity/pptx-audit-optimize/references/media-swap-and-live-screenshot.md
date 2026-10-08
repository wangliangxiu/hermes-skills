# media 图片替换 + 真机截图配方（2026-08-14 实证）

场景：PPT 里某张截图与标签不符（如"AI 设计助手"下放的却是深色 3D 渲染图），需要换真实截图。

## 1. 判断截图内容类型（无视觉工具时）

用 PIL 像素统计代替肉眼：
- 深色占比 >50%（均亮 <110）→ 3D 渲染/深色界面
- 浅色+文字为主 → 对话框/表单界面
- 行亮度剖面：顶部 230+（标题栏）、中间稳定深色=内容区、底部亮=状态栏

AI 对话界面是浅色 QTextEdit（白底黑字），3D 渲染图是大片深色。标签写什么，图就得是什么。

## 2. 定位图片真实 media 路径（关键坑）

`sh.image.filename` 返回 basename（"image.png"），多张图同名，**不能用它定位**。

```python
from pptx.oxml.ns import qn
blip = sh._element.find('.//' + qn('a:blip'))
rId = blip.get(qn('r:embed'))
rel = slide.part.rels[rId]
real_path = rel.target_ref  # 如 ../media/image2.png
```

替换前遍历全 PPT 所有图片 shape 的 r:embed→target，确认目标 media 只被一个 shape 引用（zipfile 替换会连坐所有引用者）。

## 3. 裁剪到目标比例 + zipfile 替换

```python
from PIL import Image
im = Image.open(SHOT).convert('RGB')
w, h = im.size
target_ratio = 4.05 / 2.13   # shape 宽/高
cur = w / h
if cur < target_ratio:       # 太高 → 裁上下
    new_h = int(w / target_ratio); top = (h-new_h)//2
    im = im.crop((0, top, w, top+new_h))
else:                        # 太宽 → 裁左右
    new_w = int(h * target_ratio); left = (w-new_w)//2
    im = im.crop((left, 0, left+new_w, h))
im.save(CROP)

import zipfile, os
tmp = SRC + '.tmp'
target = 'ppt/media/image2.png'   # 第2步拿到的真实路径
with zipfile.ZipFile(SRC,'r') as zin, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == target:
            data = open(CROP,'rb').read()
        zout.writestr(item, data)
os.replace(tmp, SRC)
```

验证：读回该 shape `hashlib.md5(sh.image.blob).hexdigest()` 与新图一致；重新导出 PNG 确认结构完好。

## 4. 真机截软件界面（PyQt5 应用）

AI 对话/GL 渲染等 offscreen 抓不到的界面，必须真机窗口截图（窗口会闪现，截完立即 close）：

```python
app = QApplication(sys.argv)
w = dd.MainWindow(); w.resize(1500, 800); w.show(); app.processEvents()

def shot():
    try:
        w.tabs.setCurrentIndex(10)              # 切到目标 Tab
        app.processEvents(); time.sleep(1.2)
        w.agent_panel.input.setText(DEMAND)     # 填输入
        w.agent_panel._send()                   # 触发内部逻辑
        dlg = w.agent_panel.dlg
        for _ in range(40):                     # 轮询完成标记
            app.processEvents(); time.sleep(0.5)
            if '✅ 设计完成' in dlg.toPlainText(): break
        time.sleep(1.0); app.processEvents()
        import win32gui
        hwnd = int(w.winId())
        win32gui.SetForegroundWindow(hwnd); time.sleep(0.4)
        x, y, x2, y2 = win32gui.GetWindowRect(hwnd)
        ImageGrab.grab(bbox=(x, y, x2, y2)).save(OUT)  # PIL.ImageGrab
        print('对话区行数:', len(dlg.toPlainText().splitlines()))
    finally:
        w.close(); app.quit()

QTimer.singleShot(800, shot)
sys.exit(app.exec_())
```

坑：
- `ctypes.windll.user32.GetWindowRect` 返回 int（无 .left 属性）→ 用 win32gui
- 截图时机必须等处理完成（轮询文本标记，不要固定 sleep）
- 截图前 SetForegroundWindow 防窗口被遮挡
- 截图时使用者屏幕会闪现程序窗口，提前告知
