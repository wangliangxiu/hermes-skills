# -*- coding: utf-8 -*-
"""Hermes 数据备份打包脚本（Windows 实测可用）。
用法: 改顶部 HERMES_HOME / DESKTOP 后运行: python backup_hermes.py
产出: 桌面 hermes-backup-<时间戳>.zip，zip 根目录为 hermes/，
      解压后内容直接对应新机 HERMES_HOME，覆盖粘贴即可。
注意: 中文用户名下用正斜杠路径；git-bash 的 $HOME 会乱码，别用。
"""
import os, zipfile, sqlite3, datetime

HERMES_HOME = r"C:\Users\使用者\AppData\Local\hermes"   # ← 改成实际路径
DESKTOP = r"C:\Users\使用者\Desktop"                     # ← 改成实际路径

# 不打包的目录（新电脑重装就有 / 缓存 / 源码 / 日志）
EXCLUDE_DIRS = {
    "hermes-agent", "bin", "logs", "cache", "audio_cache", "image_cache",
    "images", "pastes", "lsp", "sandboxes", "whatsapp", "workspace",
    "state-snapshots", "__pycache__",
}
# 不打包的文件（state.db 用一致性 backup 代替；-wal/-shm 是运行时文件）
EXCLUDE_FILES = {
    "state.db", "state.db-wal", "state.db-shm",
    "config.yaml.bak",
    "auth.lock", "kanban.db.init.lock",
    ".tick.lock", ".jobs.lock",
}

def db_backup(src, dst):
    """对正在使用（WAL 模式）的 SQLite 库做一致性备份。"""
    try:
        con = sqlite3.connect(src)
        out = sqlite3.connect(dst)
        try:
            con.backup(out)
        finally:
            out.close(); con.close()
        return True
    except Exception as e:
        print(f"  [db_backup 失败] {src}: {e}")
        return False

def main():
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = os.path.join(DESKTOP, f"hermes-backup-{stamp}.zip")
    os.makedirs(DESKTOP, exist_ok=True)
    count, total = 0, 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # 1) state.db 一致性备份（写到临时文件再入 zip，避免半截复制）
        src_db = os.path.join(HERMES_HOME, "state.db")
        tmp_db = os.path.join(HERMES_HOME, "state.db.bak_tmp")
        if os.path.exists(src_db) and db_backup(src_db, tmp_db):
            zf.write(tmp_db, "hermes/state.db")
            os.remove(tmp_db)
            count += 1
            total += os.path.getsize(src_db)

        # 2) 其余全部走 os.walk（唯一来源，避免重复条目警告）
        for root, dirs, files in os.walk(HERMES_HOME):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            rel = os.path.relpath(root, HERMES_HOME)
            for f in files:
                if f in EXCLUDE_FILES or f.endswith(".lock"):
                    continue
                p = os.path.join(root, f)
                arc = os.path.join("hermes", rel, f) if rel != "." else os.path.join("hermes", f)
                try:
                    zf.write(p, arc)
                    count += 1
                    total += os.path.getsize(p)
                except Exception as e:
                    print(f"  [跳过] {p}: {e}")

    print(f"完成: {zip_path}")
    print(f"文件数: {count}, 原始 {total/1048576:.1f}MB, 压缩后 {os.path.getsize(zip_path)/1048576:.1f}MB")
    print("验证: python -c \"import zipfile,collections; c=collections.Counter(zipfile.ZipFile(r'%s').namelist()); print('重复:', [k for k,v in c.items() if v>1] or '无')\"" % zip_path)

if __name__ == "__main__":
    main()
