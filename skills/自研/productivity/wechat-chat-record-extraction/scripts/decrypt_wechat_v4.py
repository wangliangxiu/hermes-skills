# -*- coding: utf-8 -*-
"""微信 4.x 数据库批量解密（独立脚本，纯 pycryptodome）
用法：改 SRC_DIR / DST_DIR / PKEY 三个常量后运行：
    D:/python/python.exe decrypt_wechat_v4.py
密钥来源：miyu key get --save（见 wechat-chat-record-extraction 技能）
"""
import hmac
import os
import struct
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA512

IV_SIZE = 16
HMAC_SHA256_SIZE = 64
KEY_SIZE = 32
AES_BLOCK_SIZE = 16
ROUND_COUNT = 256000
PAGE_SIZE = 4096
SALT_SIZE = 16
SQLITE_HEADER = b"SQLite format 3"

# ---- 按实际情况修改 ----
SRC_DIR = r'D:\xwechat_files\wxid_vdzc8nun1idr22_7dcb\db_storage'
DST_DIR = r'D:\tools\wxkey\decrypted'
PKEY = '2ffa6fad40e148b3a5471866c8674bf166de03c7b81b4baaae63272a267c296b'  # 从 ~/.miyu/config.json 读 keyHex


def decrypt_db_file_v4(pkey, in_db_path, out_db_path):
    if not os.path.exists(in_db_path):
        print(f'[跳过] {in_db_path} 不存在')
        return False
    with open(in_db_path, 'rb') as f_in, open(out_db_path, 'wb') as f_out:
        salt = f_in.read(SALT_SIZE)
        if not salt:
            return False
        mac_salt = bytes(x ^ 0x3a for x in salt)
        passphrase = bytes.fromhex(pkey)
        key = PBKDF2(passphrase, salt, dkLen=KEY_SIZE, count=ROUND_COUNT, hmac_hash_module=SHA512)
        mac_key = PBKDF2(key, mac_salt, dkLen=KEY_SIZE, count=2, hmac_hash_module=SHA512)

        f_out.write(SQLITE_HEADER)
        f_out.write(b'\x00')
        reserve = IV_SIZE + HMAC_SHA256_SIZE
        reserve = ((reserve + AES_BLOCK_SIZE - 1) // AES_BLOCK_SIZE) * AES_BLOCK_SIZE

        cur_page = 0
        while True:
            if cur_page == 0:
                page = f_in.read(PAGE_SIZE - SALT_SIZE)
                if not page:
                    break
                page = salt + page
            else:
                page = f_in.read(PAGE_SIZE)
            if not page:
                break
            offset = SALT_SIZE if cur_page == 0 else 0
            end = len(page)
            if all(x == 0 for x in page):
                f_out.write(page)
                break
            mac = hmac.new(mac_key, page[offset:end - reserve + IV_SIZE], SHA512)
            mac.update(struct.pack('<I', cur_page + 1))
            hash_mac = mac.digest()
            hash_mac_start_offset = end - reserve + IV_SIZE
            if hash_mac != page[hash_mac_start_offset:hash_mac_start_offset + len(hash_mac)]:
                print(f'[密钥错误或文件损坏] {in_db_path}')
                return None
            iv = page[end - reserve:end - reserve + IV_SIZE]
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_data = cipher.decrypt(page[offset:end - reserve])
            f_out.write(decrypted_data)
            f_out.write(page[end - reserve:end])
            cur_page += 1
    return True


def main():
    done, failed = 0, 0
    for root, dirs, files in os.walk(SRC_DIR):
        for file in files:
            if not file.endswith('.db'):
                continue
            src = os.path.join(root, file)
            rel = os.path.relpath(root, SRC_DIR)
            dest_sub = os.path.join(DST_DIR, rel)
            os.makedirs(dest_sub, exist_ok=True)
            dst = os.path.join(dest_sub, file)
            print(f'解密: {file} ({os.path.getsize(src)//1024}KB)')
            r = decrypt_db_file_v4(PKEY, src, dst)
            if r:
                done += 1
            else:
                failed += 1
    print(f'完成：成功{done}个，失败{failed}个')
    print('输出目录:', DST_DIR)


if __name__ == '__main__':
    main()
