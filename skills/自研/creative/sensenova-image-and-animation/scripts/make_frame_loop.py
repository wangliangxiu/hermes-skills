# -*- coding: utf-8 -*-
"""把若干张同尺寸图串成循环动画 (mp4 + gif), 并做抽帧校验。

用法:
  python make_frame_loop.py 帧1.png 帧2.png --out 鹈鹕骑自行车_动画
  python make_frame_loop.py a.png b.png --dur 0.5 --loops 5 --size 1024 --out anim

说明:
  - 帧的顺序就是播放顺序; 末帧后接回首帧, 做无缝循环。
  - 输出 mp4 + gif, 并 ffprobe 打印时长/帧数, 另抽 0.2s/0.6s 两帧供用 vision 比对。
  - 缺帧直接退出, 不要拿旧帧凑。
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print('命令失败:', ' '.join(cmd))
        print(r.stderr[-800:])
        sys.exit(1)
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('frames', nargs='+', help='帧图片(按播放顺序)')
    ap.add_argument('--dur', type=float, default=0.4, help='每帧时长秒(默认0.4)')
    ap.add_argument('--loops', type=int, default=7, help='整段重复次数(默认7)')
    ap.add_argument('--size', type=int, default=1024, help='mp4 边长(默认1024)')
    ap.add_argument('--out', default='frame_loop', help='输出文件名(不含扩展名)')
    a = ap.parse_args()

    if shutil.which('ffmpeg') is None:
        sys.exit('找不到 ffmpeg')
    for f in a.frames:
        if not os.path.exists(f):
            sys.exit(f'缺帧: {f}')

    work = tempfile.mkdtemp(prefix='frameloop_')
    lst = os.path.join(work, 'list.txt')
    with open(lst, 'w', encoding='utf-8') as fh:
        for f in a.frames:
            p = os.path.abspath(f).replace('\\', '/')
            fh.write(f"file '{p}'\nduration {a.dur}\n")
        first = os.path.abspath(a.frames[0]).replace('\\', '/')
        fh.write(f"file '{first}'\n")

    mp4 = a.out + '.mp4'
    gif = a.out + '.gif'
    base = ['ffmpeg', '-y', '-loglevel', 'error', '-stream_loop', str(a.loops),
            '-f', 'concat', '-safe', '0', '-i', lst]
    run(base + ['-vf', f'fps=24,scale={a.size}:{a.size}:flags=lanczos',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4])
    run(base + ['-vf', 'fps=8,scale=720:720:flags=lanczos,'
                       'split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse', gif])

    info = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size',
                '-show_entries', 'stream=width,height,nb_frames',
                '-of', 'default=noprint_wrappers=1', mp4])
    print(info.strip())

    checks = []
    for t in (0.2, 0.6):
        out = os.path.join(work, f'chk_{t}.png')
        run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(t), '-i', mp4,
             '-frames:v', '1', out])
        checks.append(out)
    print('成片:', mp4, '|', gif)
    print('抽帧校验(用 vision 看两帧确实不同):')
    for c in checks:
        print('  ', c)


if __name__ == '__main__':
    main()
