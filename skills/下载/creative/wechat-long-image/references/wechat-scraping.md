# WeChat Public Article Scraping (mp.weixin.qq.com)

Extract readable body text from WeChat public account articles for reference/analysis when the user shares a link.

## Working technique (confirmed 2026-07-01)

```python
import urllib.request, re

url = "https://mp.weixin.qq.com/s/<article-id>"
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Xiaomi 13) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 "
                  "MicroMessenger/8.0.47",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://mp.weixin.qq.com/",
}
req = urllib.request.Request(url, headers=headers)
resp = urllib.request.urlopen(req, timeout=20)
html = resp.read().decode("utf-8", "ignore")

# Extract js_content (always use this selector)
m = re.search(r'id=["\']js_content["\'][^>]*>(.*?)</div>', html, re.DOTALL)
if m:
    text = re.sub(r'<[^>]+>', '', m.group(1))
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'\s+', ' ', text).strip()
```

## Key points

- **Mobile MicroMessenger UA** is essential — desktop UA triggers "环境异常" verification
- **Response is ~3MB** HTML for a normal-length article (JS-heavy SPA wrapper)
- **Content is NOT JS-rendered** — the article body IS in the initial HTML, just hidden inside the SPA shell
- Fallback selectors: `rich_media_content`, `rich_media_area_primary`
- Detection of blocked request: check for "环境异常" or "完成验证后即可继续访问" in first 2000 chars
- Python 3.13+ `requests` module may fail (missing `cgi`); use `urllib.request` instead

## When it fails

- Page requires "仅粉丝可见" / login — cannot bypass
- Page is a video-only or short-notice post (~160 chars extracted content)
- Dynamic captcha triggered (rare for single requests)

## General Chinese Site Extraction (beyond WeChat)

### UA rotation strategy

| Site type | Effective UA |
|-----------|-------------|
| WeChat articles | Android + MicroMessenger (above) |
| Most Chinese portals | Mobile Safari / Chrome for Android |
| Baidu/Zhihu | Standard desktop Chrome |
| Paywalled news | Incognito + desktop Chrome |

### Content extraction patterns (general)

Once you have HTML from any Chinese site:

1. Search for known content container IDs/classes (`js_content`, `rich_media_content`, `article-content`, `post-content`)
2. If the page is JS-rendered (SPA), search for `__INITIAL_STATE__` or `window.__` variables containing serialized JSON data
3. Strip all HTML tags, normalize `&nbsp;` entities, collapse whitespace
4. Tokenize by `。` (Chinese period + space) or `\n` for paragraph structure

### When scraping fails

- Site requires login/cookie (e.g., "仅粉丝可见") — cannot bypass
- Captcha/滑块验证 triggered — cannot bypass programmatically
- Content loaded via dynamic JS (React/Vue SPA) — need a browser engine (Playwright/Puppeteer)

### Python 3.13 note

The `requests` package may fail with `ModuleNotFoundError: No module named 'cgi'` due to removal of the `cgi` module. Always use `urllib.request` (stdlib) for web scraping on Python 3.13+.

### GitHub API rate limiting

Unauthenticated GitHub API calls have a 60/hr limit per IP. If you hit "API rate limit exceeded" when trying to access raw content, use `git clone --depth 1 --filter=blob:none --sparse` + `git sparse-checkout set <path>` instead of Contents API calls.
