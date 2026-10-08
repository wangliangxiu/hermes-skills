# -*- coding: utf-8 -*-
"""编译 Solidity 合约 → abi + bytecode。

为什么不用 solcx.compile_files：solc 是原生程序，命令行参数里的中文路径会被
按非 UTF-8 解析，直接报 `invalid UTF-8 byte at index N: 0xF5`。这里改成
Python 读源码字符串、走 stdin 交给编译器，路径不进命令行。

用法：
    <venv>/Scripts/python.exe compile_sol.py contracts/Xxx.sol [solc版本，默认 0.8.26]

产物：
    <源码目录的上一级>/build/<合约名>.json  ->  {"abi": [...], "bytecode": "..."}
    例：code/contracts/X.sol  ->  code/build/X.json
"""
import json
import os
import sys

import solcx


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("用法: python compile_sol.py <合约.sol> [solc版本]")
    src = os.path.abspath(sys.argv[1])
    solc_version = sys.argv[2] if len(sys.argv) > 2 else "0.8.26"
    if not os.path.isfile(src):
        raise SystemExit(f"找不到文件: {src}")

    root = os.path.dirname(os.path.dirname(src))
    outdir = os.path.join(root, "build")
    os.makedirs(outdir, exist_ok=True)

    installed = [str(v) for v in solcx.get_installed_solc_versions()]
    if solc_version not in installed:
        print(f"正在下载 solc {solc_version} ...")
        solcx.install_solc(solc_version)

    with open(src, "r", encoding="utf-8") as f:
        source = f.read()

    compiled = solcx.compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version=solc_version,
        optimize=True,
    )

    stem = os.path.splitext(os.path.basename(src))[0]
    names = [k for k in compiled if ":" in k]
    if not names:
        raise SystemExit("编译没有产出，检查源码")
    key = next((k for k in names if k.split(":")[-1] == stem), names[-1])
    name = key.split(":")[-1]

    abi = compiled[key]["abi"]
    bytecode = compiled[key]["bin"]
    outfile = os.path.join(outdir, f"{name}.json")
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump({"abi": abi, "bytecode": bytecode}, f, ensure_ascii=False, indent=2)

    print(f"编译成功: {name}")
    print(f"ABI 条目: {len(abi)} | 字节码: {len(bytecode) // 2} 字节")
    print("函数:", [a.get("name") for a in abi if a.get("type") == "function"])
    print("事件:", [a.get("name") for a in abi if a.get("type") == "event"])
    print("产物:", outfile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
