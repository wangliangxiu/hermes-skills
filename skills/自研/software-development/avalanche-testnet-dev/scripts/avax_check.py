#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Avalanche 测试网核验小工具（富士 / 主网双查）。只处理地址，不要传私钥。

用法：
  python avax_check.py balance 0x地址
  python avax_check.py txlist  0x地址
  python avax_check.py samekey 0x地址 P-fuji1...
  python avax_check.py pchain  P-fuji1...

依赖：只用标准库（urllib / json）。
"""
import json
import sys
import urllib.request

RPC = {
    "fuji": "https://api.avax-test.network/ext/bc/C/rpc",
    "mainnet": "https://api.avax.network/ext/bc/C/rpc",
}
P_API = {
    "fuji": "https://api.avax-test.network/ext/bc/P",
    "mainnet": "https://api.avax.network/ext/bc/P",
}
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=25).read())


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    return json.loads(urllib.request.urlopen(req, timeout=35).read())


def bech32_decode(bech):
    """返回 (hrp, payload_bytes)。校验和不对就抛 ValueError。"""
    pos = bech.rfind("1")
    if pos <= 0:
        raise ValueError("不是合法 bech32 地址")
    hrp, data = bech[:pos], bech[pos + 1:]
    vals = [CHARSET.find(c) for c in data]
    if -1 in vals:
        raise ValueError("地址含非法字符")

    def polymod(values):
        gen = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
        chk = 1
        for v in values:
            top = chk >> 25
            chk = (chk & 0x1ffffff) << 5 ^ v
            for i in range(5):
                if (top >> i) & 1:
                    chk ^= gen[i]
        return chk

    expand = [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]
    if polymod(expand + vals) != 1:
        raise ValueError("校验和不对，地址可能抄错了")
    acc = bits = 0
    out = bytearray()
    for v in vals[:-6]:
        acc = (acc << 5) | v
        bits += 5
        while bits >= 8:
            bits -= 8
            out.append((acc >> bits) & 0xff)
    return hrp, bytes(out)


def to_hex_address(addr):
    """0x… 原样返回；P-fuji1…/P-avax1… 解码成 0x… 形式。"""
    s = addr.strip()
    low = s.lower()
    if low.startswith("0x"):
        return low
    if low[:2] in ("p-", "x-"):
        s = s[2:]
    _hrp, raw = bech32_decode(s)
    return "0x" + raw.hex()


def cmd_balance(addr):
    for name, url in RPC.items():
        ch = post(url, {"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []})["result"]
        bal = post(url, {"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance",
                         "params": [addr, "latest"]})["result"]
        nonce = post(url, {"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionCount",
                           "params": [addr, "latest"]})["result"]
        code = post(url, {"jsonrpc": "2.0", "id": 1, "method": "eth_getCode",
                          "params": [addr, "latest"]})["result"]
        kind = "是合约" if len(code) > 2 else "普通地址"
        print(f"[{name}] chainId={int(ch, 16)}  余额={int(bal, 16) / 1e18} AVAX  "
              f"nonce={int(nonce, 16)}  {kind}")


def cmd_txlist(addr):
    url = ("https://api.routescan.io/v2/network/testnet/evm/43113/etherscan/api"
           f"?module=account&action=txlist&address={addr}&sort=asc&offset=50")
    d = get_json(url)
    rows = d.get("result")
    if not isinstance(rows, list):
        print("没拿到交易列表：", json.dumps(d, ensure_ascii=False)[:300])
        return
    print(f"富士网 共 {len(rows)} 笔")
    for t in rows:
        _to = (t.get("to") or "")[:12]
        state = "失败" if t.get("isError") == "1" else "成功"
        print(f"  {t['hash'][:24]}…  时间戳 {t['timeStamp']}  "
              f"{t['from'][:12]}… → {_to}…  {int(t['value']) / 1e18} AVAX  {state}")


def cmd_samekey(a, b):
    try:
        ha, hb = to_hex_address(a), to_hex_address(b)
    except Exception as e:
        print("解码失败：", e)
        return
    print("A 底层字节:", ha)
    print("B 底层字节:", hb)
    print("结论:", "同一把钥匙（同一私钥的不同写法）" if ha == hb
          else "不是同一把钥匙 —— 两把不同私钥，别混用")


def cmd_pchain(addr):
    s = addr.strip()
    if s.lower()[:2] in ("p-", "x-"):
        s = s[2:]
    if "1" not in s:
        print("地址形态不对，要 P-fuji1… / P-avax1… 这种")
        return
    suffix = s.split("1", 1)[1]
    for name, url in P_API.items():
        hrp = "fuji" if name == "fuji" else "avax"
        a = f"P-{hrp}1{suffix}"
        try:
            r = post(url, {"jsonrpc": "2.0", "id": 1, "method": "platform.getBalance",
                           "params": {"addresses": [a]}})
            res = r.get("result") or {}
            print(f"[{name}] {a}  余额={int(res.get('balance', 0)) / 1e18} AVAX  "
                  f"可用={int(res.get('unlocked', 0)) / 1e18}")
        except Exception as e:
            print(f"[{name}] 查询失败: {e}")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "balance":
        cmd_balance(args[0])
    elif cmd == "txlist":
        cmd_txlist(args[0])
    elif cmd == "samekey" and len(args) >= 2:
        cmd_samekey(args[0], args[1])
    elif cmd == "pchain":
        cmd_pchain(args[0])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
