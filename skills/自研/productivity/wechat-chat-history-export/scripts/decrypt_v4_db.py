# -*- coding: utf-8 -*-
"""微信4.x数据库解密：PBKDF2+SHA512+AES-256-CBC（算法来自 wechat-export-toolkit/wxManager）
用法: python decrypt_v4_db.py <keyHex> <src_db_storage> <dst_dir>
依赖: pip install pycryptodome
"""
import hmac
import os
import struct
import sys
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


def decrypt_db_file_v4(pkey, in_db_path, out_db_path):
    if not os.path.exists(in_db_path):
        print(f'[跳过] {in_db_path} 不存在')
        return False
    with open(in_db_path, 'rb') as f_in, open(out_db_path, 'wb') as f_out:
        salt = f_in.read(SALT_SIZE)
        if not salt:
            print(f'[空文件] {in_db_path}')
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
    if len(sys.argv) != 4:
        print(__doc__)
        return 1
    pkey, src_dir, dst_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    done, failed = 0, 0
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if not file.endswith('.db'):
                continue
            src = os.path.join(root, file)
            rel = os.path.relpath(root, src_dir)
            dest_sub = os.path.join(dst_dir, rel)
            os.makedirs(dest_sub, exist_ok=True)
            dst = os.path.join(dest_sub, file)
            print(f'解密: {file} ({os.path.getsize(src)//1024}KB)')
            r = decrypt_db_file_v4(pkey, src, dst)
            if r:
                done += 1
            else:
                failed += 1
    print(f'完成：成功{done}个，失败{failed}个')
    print('输出目录:', dst_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
