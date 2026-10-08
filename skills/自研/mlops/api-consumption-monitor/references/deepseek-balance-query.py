#!/usr/bin/env python3
"""DeepSeek API 余额查询脚本 — 可独立运行，无需加载任何 skill。

适用于 Hermes cron 任务的自包含查询。
支持国内站 (deepseek.cn) 和海外站 (deepseek.com) 自动回退。

用法：
    python deepseek-balance-query.py              # 从 ~/AppData/Local/hermes/.env 读 key
    python deepseek-balance-query.py sk-xxxxx     # 直接从参数读 key
"""

import json
import os
import re
import urllib.request
import sys
from pathlib import Path


def read_key_from_env(env_path: str = None) -> str:
    """从 .env 文件读取 DEEPSEEK_API_KEY"""
    if not env_path:
        env_path = os.path.expanduser("~/AppData/Local/hermes/.env")
    
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 处理各种格式：key=value, key='value', key="value"
        match = re.search(
            r'^DEEPSEEK_API_KEY\s*=\s*["\']?([^"\'#\n]+)["\']?',
            content,
            re.MULTILINE
        )
        if match:
            return match.group(1).strip()
    except Exception as e:
        return None
    
    return None


def query_balance(api_key: str) -> dict:
    """查询 DeepSeek 余额，国内站失败则回退到海外站"""
    
    endpoints = [
        ("https://api.deepseek.com/user/balance", "海外站"),
    ]
    
    for url, label in endpoints:
        try:
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                return {"success": True, "source": label, "data": data}
        except Exception as e:
            last_error = e
    
    return {"success": False, "error": str(last_error)}


def format_balance_output(result: dict) -> str:
    """格式化输出，适合直接投递"""
    if not result.get("success"):
        return f"❌ 余额查询失败：{result.get('error', '未知错误')}"
    
    data = result["data"]
    balance_infos = data.get("balance_infos", [])
    
    if not balance_infos:
        total = data.get("total_balance", "N/A")
        if total != "N/A":
            return f"💰 DeepSeek 余额：{total} 元"
        return f"⚠️ 已连接 API 但未找到余额信息：{json.dumps(data, ensure_ascii=False)}"
    
    info = balance_infos[0]
    currency = info.get("currency", "CNY")
    total = info.get("total_balance", "N/A")
    topped_up = info.get("topped_up_balance", "N/A")
    granted = info.get("granted_balance", "N/A")
    
    return (
        f"💰 DeepSeek API 余额\n"
        f"总余额：{total} {currency}\n"
        f"充值余额：{topped_up} {currency}\n"
        f"赠送余额：{granted} {currency}"
    )


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else None
    if not key:
        key = read_key_from_env()
    if not key:
        key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        print("❌ 未找到 DeepSeek API Key")
        sys.exit(1)
    
    result = query_balance(key)
    print(format_balance_output(result))
