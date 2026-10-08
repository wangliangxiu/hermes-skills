# -*- coding: utf-8 -*-
"""出卷环境自检 / 一键安装（Windows）。

作用：把「生成含公式的 Word」所需的全部依赖装到一个独立 venv 里，并验证能用。
不假设对方机器已经装过任何东西。

用法（任一种）：
    D:\\pyenv\\kaoyan\\Scripts\\python.exe bootstrap_env.py     # 已装就直接自检
    py -3.11 bootstrap_env.py                                    # 从零建环境
    py -3.11 bootstrap_env.py --mirror https://pypi.tuna.tsinghua.edu.cn/simple
    py -3.11 bootstrap_env.py --venv D:/pyenv/kaoyan

退出码 0 = 全部就绪。
"""
import argparse
import glob
import os
import subprocess
import sys

DEPS = ['python-docx', 'lxml', 'latex2mathml', 'pymupdf', 'sympy', 'numpy']
IMPORTS = {'python-docx': 'docx', 'lxml': 'lxml', 'latex2mathml': 'latex2mathml',
           'pymupdf': 'pymupdf', 'sympy': 'sympy', 'numpy': 'numpy'}
DEFAULT_VENV = r'D:\pyenv\kaoyan'


def log(msg):
    print(msg, flush=True)


class _Fail:
    returncode = 1
    stdout = ''
    stderr = ''


def run(cmd, **kw):
    """永不抛异常的外部命令调用：命令不存在/超时都当失败处理"""
    kw.setdefault('text', True)
    kw.setdefault('encoding', 'utf-8')
    kw.setdefault('errors', 'replace')
    try:
        return subprocess.run(cmd, capture_output=True, **kw)
    except Exception as e:                       # FileNotFoundError / TimeoutExpired / OSError
        f = _Fail(); f.stderr = '%s: %s' % (type(e).__name__, e)
        return f


def find_base_python():
    """找一个能建 venv 的 3.9~3.14 解释器（无 py 启动器的机器也能用）"""
    cands = []
    la = os.environ.get('LOCALAPPDATA', '')
    if la:
        cands.append(os.path.join(la, r'hermes\hermes-agent\venv\Scripts\python.exe'))
    for launcher in (['py', '-3.11'], ['py', '-3.12'], ['py', '-3'], ['python'], ['python3']):
        r = run(launcher + ['-c', 'import sys;print(sys.executable)'])
        if r.returncode == 0 and r.stdout.strip():
            cands.append(r.stdout.strip())
    cands.append(sys.executable)
    for c in cands:
        if not c or not os.path.exists(c):
            continue
        v = run([c, '-c', 'import sys;print("%d.%d" % sys.version_info[:2])'])
        if v.returncode != 0:
            continue
        try:
            major, minor = (int(t) for t in v.stdout.strip().split('.'))
        except Exception:
            continue
        if (major, minor) >= (3, 9) and (major, minor) <= (3, 14):
            return c, '%d.%d' % (major, minor)
    return None, None


def find_xsl():
    """定位 Office 自带的 MathML -> OMML 样式表"""
    if os.environ.get('MML2OMML') and os.path.exists(os.environ['MML2OMML']):
        return os.environ['MML2OMML']
    roots = [os.environ.get('ProgramFiles', r'C:\Program Files'),
             os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')]
    for base in roots:
        for sub in (r'Microsoft Office\root\Office16', r'Microsoft Office\Office16',
                    r'Microsoft Office\root\Office15'):
            p = os.path.join(base, sub, 'MML2OMML.XSL')
            if os.path.exists(p):
                return p
    for base in roots:
        hits = glob.glob(os.path.join(base, 'Microsoft Office', '**', 'MML2OMML.XSL'), recursive=True)
        if hits:
            return hits[0]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--venv', default=DEFAULT_VENV)
    ap.add_argument('--mirror', default=None, help='国内镜像源，例如 https://pypi.tuna.tsinghua.edu.cn/simple')
    a = ap.parse_args()

    ok = True
    log('=== 1/4 Python 环境 ===')
    venv_py = os.path.join(a.venv, 'Scripts', 'python.exe')
    if os.path.exists(venv_py):
        log('已存在：%s' % venv_py)
    else:
        base, ver = find_base_python()
        if not base:
            log('✗ 找不到可用的 3.9~3.13 解释器。请先装 Python 3.11（勾选 Add to PATH），'
                '或指定：bootstrap_env.py --venv <目标目录>。')
            return 1
        log('用 %s (Python %s) 创建 venv：%s' % (base, ver, a.venv))
        os.makedirs(os.path.dirname(a.venv), exist_ok=True)
        r = run([base, '-m', 'venv', a.venv])
        if r.returncode != 0 or not os.path.exists(venv_py):
            log('✗ venv 创建失败：%s' % (r.stderr or '')[-400:])
            return 1
    py = venv_py

    log('=== 2/4 依赖库 ===')
    missing = [p for p, m in IMPORTS.items()
               if run([py, '-c', 'import %s' % m]).returncode != 0]
    if missing:
        log('缺少：%s，开始安装（慢就是国际带宽问题，先开 VPN/代理）…' % ', '.join(missing))
        cmd = [py, '-m', 'pip', 'install', '--disable-pip-version-check',
               '--progress-bar', 'off', '--timeout', '60']
        if a.mirror:
            cmd += ['-i', a.mirror]
        cmd += missing
        r = run(cmd, timeout=1800)
        log((r.stdout or '')[-800:])
        if r.returncode != 0:
            log('✗ 安装失败：%s' % (r.stderr or '')[-400:])
            log('   对策：1) 开 VPN 后重跑；2) 或加 --mirror 指定国内镜像。')
            ok = False
    else:
        log('依赖齐全：%s' % ', '.join(DEPS))

    log('=== 3/4 Office 公式样式表 MML2OMML.XSL ===')
    xsl = find_xsl()
    if xsl:
        log('找到：%s' % xsl)
    else:
        ok = False
        log('✗ 未找到。该文件随 Microsoft Office（Word）安装，缺少它就无法把公式转成 Word 原生格式。')
        log('   对策：1) 装/修复 Word；2) 或用环境变量 MML2OMML 指定该文件路径。')

    log('=== 4/4 端到端自检（真生成一个带公式的 docx）===')
    if xsl:
        r = run([py, '-c',
                 'import latex2mathml.converter as c;from lxml import etree;import zipfile,os,tempfile;'
                 'tr=etree.XSLT(etree.parse(%r));'
                 'om=tr(etree.fromstring(c.convert(chr(92)*2+chr(92)*2+"frac{1}{2}"))).getroot();'
                 'from docx import Document;d=Document();p=d.add_paragraph();p._p.append(om);'
                 'f=os.path.join(tempfile.gettempdir(),"bootstrap_smoke.docx");d.save(f);'
                 'x=zipfile.ZipFile(f).read("word/document.xml").decode("utf8");'
                 'print("OMML_OK" if "oMath" in x else "OMML_MISSING")' % (xsl,)])
        out = (r.stdout or '').strip()
        log('探针输出：%s %s' % (out, (r.stderr or '').strip()[:200]))
        if 'OMML_OK' not in out:
            ok = False
    else:
        log('跳过（缺 XSL）')

    log('')
    log('结论：' + ('✓ 环境就绪，可以直接出卷。' if ok else '✗ 还有缺项，按上面提示处理后重跑。'))
    log('出卷时统一用：%s' % py)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
