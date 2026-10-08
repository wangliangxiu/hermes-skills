# PyInstaller 打包：外部资源内嵌 + exe 验证（v0.11 实证，2026-08-13）

## 场景
智能炮孔设计系统 v0.11 打包交付。主程序是单文件 exe（-F -w），AI 设计助手知识问答
依赖外部文件夹《凿岩台车Agent资料库》（项目同级 `../凿岩台车Agent资料库/`）——
PyInstaller -F 模式下 `__file__` 指向 _MEIPASS 临时解压目录，开发路径直接失效 → 问答降级。
另：dxf_panel.py 的 DxfPreview 画布 paintEvent 藏有 `self.height` 遮蔽坑，offscreen 回归
tail 截断漏掉，直到启动 exe 看 stderr 才暴露。

## 1. spec 里 datas 内嵌外部资源文件夹
```python
datas = [('C:/Users/使用者/Desktop/我的小项目/凿岩台车Agent资料库',
          '凿岩台车Agent资料库')]
```
打包用 spec（唯一配置源）：
```bash
"D:/python/python.exe" -m PyInstaller --clean --noconfirm 智能炮孔设计系统.spec
```

## 2. 代码侧 MEIPASS 回退链（ai_agent_core.py）
```python
def _kb_dir():
    if hasattr(sys, '_MEIPASS'):                              # ① 打包内嵌
        p = os.path.join(sys._MEIPASS, '凿岩台车Agent资料库')
        if os.path.isdir(p):
            return p
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))   # ② exe 同级
    p = os.path.join(exe_dir, '凿岩台车Agent资料库')
    if os.path.isdir(p):
        return p
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),  # ③ 开发路径
                        '..', '凿岩台车Agent资料库')
KB_DIR = _kb_dir()
```
注意：开发模式 sys.argv[0] 是脚本路径 → exe_dir=项目目录，自动回退 ③，不破坏 dev 环境。
需要 `import sys`。纯函数 `kb_load_all()` 不变，测试断言 KB_DIR 存在 + 加载 5 个 txt。

## 3. exe 验证（本会话两次教训）
1. **offscreen 回归输出不能 tail 截断**：`2>&1 | tail -15` 会截掉 Qt 吞掉的 paintEvent
   Traceback（界面不崩、只 stderr 打印）——本次 dxf_panel `self.height` 就是漏网后到
   exe 里才暴露。回归脚本必须全量输出 + `grep -E "Traceback|TypeError|Error"`，
   ERR_COUNT 计数断言。
2. **tasklist grep 中文 exe 名会失败**（git-bash GBK 编码输出中文进程名乱码）→ 误判
   "exe 没起来"。用 terminal(background=true) 启动 + `process(action='poll')`：
   status=running + output_preview 里能看到真实 stderr（被 Qt 吞的 Traceback 打在这里）。
3. 启动验证流程：background 启动 exe → poll 看 stderr 无 Traceback → 确认后 kill 再交付。

## 4. 本次修复清单
- `ai_agent_core.py`：+import sys；KB_DIR 常量 → `_kb_dir()` 回退链
- `dxf_panel.py` DxfPreview：`self.height = 5.0` → `self.sec_height`（属性赋值/引用 3 处，
  `self.height()` 方法调用保留不动）——老坑（实例属性撞 QWidget 方法名）漏进新模块，
  打包前全项目 `grep -n "self\.height" *.py` 复查
- `智能炮孔设计系统.spec`：datas 加资料库文件夹

## 5. 交付物
- exe: `dist/智能炮孔设计系统.exe`（约 166MB）
- 压缩 zip 放桌面（使用者要求）
- 追加《项目推进日志.txt》（下一步清单里的"打包 v0.11 exe + zip"对应本记录）
