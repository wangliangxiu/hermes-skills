#!/usr/bin/env python3
"""
公众号文章抓取+分析脚本

用法：
  python fetch_wechat_article.py <公众号文章URL>

功能：
  1. 抓取微信公众号文章内容（移动端 UA 绕过验证）
  2. 提取正文、分析风格参数（字数/句长/高频词/开篇/结尾/图片数）
  3. 保存报告到桌面参考范文目录
  4. 更新索引文件

输出位置：
  C:\Users\<用户名>\Desktop\参考范文\{序号}_{风格标签}_{标题}.txt
  C:\Users\<用户名>\Desktop\参考范文\索引.txt
"""
import urllib.request, re, os, sys

def fetch_article(url):
    """抓取公众号文章"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Xiaomi 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47"
    }
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req, timeout=20)
    return resp.read().decode("utf-8", "ignore")

def extract_title(html):
    """提取文章标题"""
    for pattern in [
        r'og:title" content="([^"]+)"',
        r'twitter:title" content="([^"]+)"',
        r'var title = "([^"]+)"',
    ]:
        m = re.search(pattern, html)
        if m:
            t = m.group(1).strip()
            if t and t != "微信公众平台":
                return t
    return "未知标题"

def extract_content(html):
    """提取正文"""
    m = re.search(r'id="js_content"[^>]*>(.*?)</div>', html, re.DOTALL)
    if not m:
        return None
    return m.group(1)

def clean_html(html_content):
    """清理HTML标签，提取可读文字"""
    text = re.sub(r'<br\s*/?>', '\n', html_content)
    text = re.sub(r'<p[^>]*>', '\n', text)
    text = re.sub(r'</p>', '', text)
    text = re.sub(r'<section[^>]*>', '\n', text)
    text = re.sub(r'</section>', '', text)
    text = re.sub(r'<span[^>]*>', '', text)
    text = re.sub(r'</span>', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'^点击[^。]*。', '', text)
    return text.strip()

def analyze_style(text):
    """分析风格参数"""
    sentences = []
    for raw_s in text.replace("？", "？\n").replace("！", "！\n").replace("……", "……\n").split("。"):
        s = raw_s.strip()
        if len(s) > 2:
            sentences.append(s + "。")
    
    total_chars = len(text.replace("\n", ""))
    total_sentences = len(sentences)
    avg_sentence_len = total_chars / total_sentences if total_sentences else 0
    
    short = sum(1 for s in sentences if len(s) < 15)
    long_s = sum(1 for s in sentences if len(s) > 30)
    
    words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
    stopwords = {"我们", "一个", "可以", "没有", "就是", "不是", "但是", "这个", "那个", "什么", "怎么", "已经", "他们", "你们", "它们", "自己", "因为", "所以", "如果", "虽然", "而且", "或者", "之后", "之前", "其中", "以及", "还有", "这些", "那些", "这样", "那样", "这里", "那里", "成为", "记者", "来源", "编辑", "图片", "往期", "推荐", "关注", "点击"}
    word_freq = {}
    for w in words:
        if w not in stopwords and len(w) >= 2:
            word_freq[w] = word_freq.get(w, 0) + 1
    top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:20]
    
    return {
        "chars": total_chars,
        "sentences": total_sentences,
        "avg_sentence": avg_sentence_len,
        "short_sentences": short,
        "long_sentences": long_s,
        "top_words": top_words,
        "opening": [s[:60] for s in sentences[:3]],
        "closing": [s[:80] for s in sentences[-3:]] if len(sentences) >= 3 else [],
    }

def infer_style_tag(title):
    """根据标题推断风格标签"""
    if "桥" in title: return "文艺叙事"
    if "碑" in title: return "历史叙事"
    if "商" in title: return "商业叙事"
    if "鸟" in title: return "生态叙事"
    if "树" in title: return "生态叙事"
    return "通用"

def main():
    if len(sys.argv) < 2:
        print("用法: python fetch_wechat_article.py <公众号文章URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"📡 正在抓取: {url}")
    
    try:
        html = fetch_article(url)
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        print("提示：尝试手动复制文章内容粘贴给 LLM")
        sys.exit(1)
    
    if "环境异常" in html:
        print("❌ 触发微信反爬验证，无法自动抓取")
        print("提示：手动复制文章内容")
        sys.exit(1)
    
    title = extract_title(html)
    print(f"📌 标题: {title}")
    
    raw = extract_content(html)
    if not raw:
        print("❌ 未找到正文")
        sys.exit(1)
    
    text = clean_html(raw)
    img_count = raw.count("<img")
    stats = analyze_style(text)
    style_tag = infer_style_tag(title)
    
    # 生成报告
    report = f"""
================================================================================
📋 范文风格参数报告
================================================================================

📐 基本信息
  文章标题：{title}
  总字数：{stats['chars']}字
  句子数：{stats['sentences']}句
  平均句长：{stats['avg_sentence']:.0f}字

🏗️ 开篇方式（前3句）：
"""
    for i, s in enumerate(stats["opening"], 1):
        report += f"  {i}. {s}\n"
    
    report += f"""
📝 句子节奏
  平均句长：{stats['avg_sentence']:.0f}字
  最短句：{stats['short_sentences']}句（<15字）
  最长句：{stats['long_sentences']}句（>30字）

🔤 高频词（前20）：
"""
    for i, (word, count) in enumerate(stats["top_words"], 1):
        report += f"  {i:2d}. {word}  ({count}次)\n"
    
    report += f"""
🖼️ 图片数：约{img_count}张

🎯 结尾收束（最后3句）：
"""
    for i, s in enumerate(stats["closing"], 1):
        report += f"  {i}. {s[:100]}\n"
    
    report += """
================================================================================
"""
    
    # 保存到桌面
    home = os.path.expanduser("~")
    ref_folder = os.path.join(home, "Desktop", "参考范文")
    os.makedirs(ref_folder, exist_ok=True)
    
    files = sorted([f for f in os.listdir(ref_folder) if f.endswith(".txt") and f != "索引.txt"])
    next_num = len(files) + 1
    
    safe_title = title.replace(" ", "").replace("/", "_").replace("\\", "_").replace("?", "")[:15]
    filename = f"{next_num:03d}_{style_tag}_{safe_title}.txt"
    filepath = os.path.join(ref_folder, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ 已保存: {filename}")
    
    # 更新索引
    all_files = sorted([f for f in os.listdir(ref_folder) if f.endswith(".txt") and f != "索引.txt"])
    index = "参考范文索引\n" + "=" * 40 + "\n"
    index += f"共收录 {len(all_files)} 篇范文\n\n"
    for i, f in enumerate(all_files, 1):
        index += f"{i:2d}. {f}\n"
    
    with open(os.path.join(ref_folder, "索引.txt"), "w", encoding="utf-8") as f:
        f.write(index)
    
    print(f"📊 索引已更新: 共{len(all_files)}篇")
    print(report)

if __name__ == "__main__":
    main()
