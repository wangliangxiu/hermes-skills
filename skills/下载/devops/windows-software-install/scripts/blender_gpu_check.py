# -*- coding: utf-8 -*-
"""Blender GPU 能力自检：枚举 Cycles 渲染设备 + 微渲染一张小图。

用法（在 git-bash 里，Windows 路径用正斜杠）：
  "D:/Blender/blender-4.5.10-windows-x64/blender.exe" -b --factory-startup \
      --python "C:/Users/<user>/AppData/Local/Temp/blender_gpu_check.py"

判读：
  DEVICES 里出现 ('CUDA' 或 'OPTIX', '<你的显卡>') 且 use=True → GPU 渲染可用；
  RENDER DONE + 输出文件存在 = 真的跑通了（不是只认到设备）。
注意：不要在 -b 里用 gpu.platform.*，后台模式没有绘图上下文，必然 SystemError。
"""
import os
import time

import bpy

OUT = os.environ.get("GPUCHECK_OUT", "D:/Blender/_gputest.png")

prefs = bpy.context.preferences.addons["cycles"].preferences
print("compute_device_type default:", prefs.compute_device_type)
prefs.compute_device_type = "CUDA"
try:
    prefs.refresh_devices()
except Exception as e:  # 老版本没有这个方法时别炸
    print("refresh_devices failed:", e)
print("DEVICES:", [(d.type, d.name, d.use) for d in prefs.devices])

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "GPU"
sc.cycles.samples = 16
sc.render.resolution_x = 160
sc.render.resolution_y = 120
sc.render.filepath = OUT

t0 = time.time()
bpy.ops.render.render(write_still=True)
print("RENDER DONE %.1fs" % (time.time() - t0))
print("OUTPUT:", OUT, os.path.exists(OUT))
