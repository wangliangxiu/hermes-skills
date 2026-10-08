# -*- coding: utf-8 -*-
"""从 .docx 里把嵌入的 Visio 图（OLE 对象）导出来，按"图题"命名，并打印索引。

用法:
    python extract_docx_visio_figures.py <输入.docx> <输出目录> [--vsdx]

  --vsdx  老格式 .vsd 用 Visio 另存为 .vsdx（需要本机装 Visio + pywin32）

原理：docx 是 zip；Word 里"双击能进 Visio"的图 = word/embeddings/*.vsdx|*.vsd。
注意 r:embed 指向 word/media（图片），r:id（在 o:OLEObject 上）才指向 embeddings。
命名取图片所在段落往后（找不到就往前）最近的图题段落，没有图题就用最近的小节标题。
"""
import os
import re
import sys
import zipfile


def is_figtitle(t):
    return bool(t) and len(t) <= 30 and t.endswith(('图', '框图', '流程图', '体系图', '示意图'))


def is_heading(t):
    return bool(re.match(r'^\d+(\.\d+){0,3}\s*[^\d\s]', t)) and len(t) <= 40


def safe(name):
    return re.sub(r'[\\/:*?"<>|]+', '_', name).strip()[:80]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    docx, outdir = sys.argv[1], os.path.abspath(sys.argv[2])
    convert = '--vsdx' in sys.argv
    os.makedirs(outdir, exist_ok=True)

    with zipfile.ZipFile(docx) as z:
        doc = z.read('word/document.xml').decode('utf-8', errors='replace')
        rels = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"',
                               z.read('word/_rels/document.xml.rels').decode('utf-8', 'replace')))
        names = z.namelist()

        paras = []
        for p in doc.split('</w:p>'):
            t = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, flags=re.S))
            t = re.sub(r'<[^>]+>', '', t).strip()
            rids = re.findall(r'r:id="([^"]+)"', p) + re.findall(r'r:embed="([^"]+)"', p)
            paras.append((t, rids))

        # 每个嵌入对象 → (图题, 所属小节)
        objs = {}
        for k, (t, rids) in enumerate(paras):
            for rid in rids:
                tgt = rels.get(rid, '')
                if 'embeddings/' not in tgt:
                    continue
                base = os.path.basename(tgt)
                if base in objs:
                    continue
                title = next((paras[m][0] for m in range(k, min(k + 6, len(paras)))
                              if is_figtitle(paras[m][0])), None)
                if title is None:
                    title = next((paras[m][0] for m in range(k, max(0, k - 5), -1)
                                  if is_figtitle(paras[m][0])), None)
                sec = next((paras[m][0] for m in range(k, max(0, k - 60), -1)
                            if is_heading(paras[m][0])), None)
                objs[base] = (title, sec)

        print('嵌入 Visio 对象:', len(objs))

        app = None
        if convert:
            try:
                import win32com.client as wc
                app = wc.Dispatch('Visio.Application')
                app.Visible = False
            except Exception as e:
                print('（Visio 不可用，.vsd 原样拷贝）', e)
                app = None

        used, rows = {}, []
        for base in sorted(objs, key=lambda s: (len(s), s)):
            title, sec = objs[base]
            name = title or sec or base
            n = used.get(name, 0) + 1
            used[name] = n
            ext = os.path.splitext(base)[1]
            want_vsdx = bool(app) and ext.lower() == '.vsd'
            out = os.path.join(outdir, safe(name) + ('' if n == 1 else f'_{n}') +
                               ('.vsdx' if want_vsdx else ext))
            src = next((x for x in names if x.endswith(base)), None)
            if not src:
                print('✗ 找不到', base)
                continue
            if want_vsdx:
                tmp = os.path.join(outdir, base)
                with open(tmp, 'wb') as f:
                    f.write(z.read(src))
                d = app.Documents.OpenEx(tmp, 4)
                d.SaveAs(out)
                d.Close()
                os.remove(tmp)
            else:
                with open(out, 'wb') as f:
                    f.write(z.read(src))
            rows.append((os.path.basename(out), base, title or '—', sec or '—'))
            print(f'✓ {os.path.basename(out)}   ← {base}   图题={title}  节={sec}')

        if app:
            try:
                app.Quit()
            except Exception:
                pass

    with open(os.path.join(outdir, '索引.txt'), 'w', encoding='utf-8') as fp:
        fp.write('文档内嵌 Visio 图索引\n' + '=' * 60 + '\n')
        fp.write('用法：直接拿 .vsdx 在 Visio 里改（项目名称 / 机构 / 工区数）；\n')
        fp.write('      .emf 是矢量图，插进 Word 后可"取消组合"改字。\n\n')
        for f, base, title, sec in rows:
            fp.write(f'  {f}\n      源文件 {base}｜图题 {title}｜所属 {sec}\n')
    print('\n输出目录:', outdir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
