# 微信 4.x 数据库解密算法（PBKDF2-SHA512 + AES-256-CBC）

2026-08-14 实测成功：26 个库全解、620 会话 / 29 万条文本消息。
算法来源：wechat-export-toolkit 的 `wxManager/decrypt/decrypt_v4.py`
（其上游是 WeChatMsg 系，纯 Python + PyCryptodome，不依赖 WCDB）。

## 加密结构（SQLCipher 变体）
- 每个库文件开头 16 字节 = 随机盐 `salt`
- 每页 4096 字节独立加密；页尾保留区 = 16B IV + 64B HMAC-SHA512（+ 填充到 AES 块）
- 第 1 页特殊：`salt(16) + 数据(4032) + 保留区(48)`
- 后续页：`数据(4048) + 保留区(48)`
- 页号从 1 开始，参与 HMAC

## 密钥派生
```python
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA512

passphrase = bytes.fromhex(key_hex)          # miyu key get 拿到的 64 位 hex
salt = f.read(16)
mac_salt = bytes(x ^ 0x3a for x in salt)     # 校验盐 = 盐异或 0x3a

key     = PBKDF2(passphrase, salt,     dkLen=32, count=256000, hmac_hash_module=SHA512)
mac_key = PBKDF2(key,       mac_salt,  dkLen=32, count=2,      hmac_hash_module=SHA512)
```

## 逐页解密
```python
PAGE_SIZE, IV_SIZE, HMAC_SHA256_SIZE = 4096, 16, 64
AES_BLOCK_SIZE = 16
reserve = IV_SIZE + HMAC_SHA256_SIZE           # 80 → 补齐到 80 (已是16倍数)

out.write(b"SQLite format 3" + b"\x00")        # 标准 SQLite 头
cur_page = 0
while True:
    if cur_page == 0:
        page = f.read(PAGE_SIZE - 16); page = salt + page   # 补回盐
    else:
        page = f.read(PAGE_SIZE)
    if not page: break
    offset = 16 if cur_page == 0 else 0
    end = len(page)
    if all(x == 0 for x in page):              # 空页直接抄写
        out.write(page); break
    # HMAC 校验：数据(去保留区前 IV 部分) + 页号(小端4字节)
    mac = hmac.new(mac_key, page[offset:end - reserve + IV_SIZE], SHA512)
    mac.update(struct.pack("<I", cur_page + 1))
    assert mac.digest() == page[end - reserve + IV_SIZE : end - reserve + IV_SIZE + 64], "密钥错误或文件损坏"
    iv  = page[end - reserve : end - reserve + IV_SIZE]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    out.write(cipher.decrypt(page[offset : end - reserve]))
    out.write(page[end - reserve : end])       # 保留区原样写回（含 IV/HMAC）
    cur_page += 1
```

## 输出
- 解密产物 = 标准 SQLite 文件（可 sqlite3 打开）
- 目录结构保持：message/、contact/、session/、sns/ 等子目录一一对应

## 常见问题
- `HMAC 不匹配`：密钥错 / 文件损坏 / 用了别的账号库
- 解密后 sqlite3 打开报 `file is not a database`：页解密顺序或保留区处理错
- 大库（100MB+）解密几十秒，正常；"空页提前结束"是正常结尾
