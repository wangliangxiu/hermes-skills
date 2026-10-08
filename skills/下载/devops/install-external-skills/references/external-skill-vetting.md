# 外部技能/仓库的采用核验（推荐与交付前）

适用：要推荐某个第三方仓库、要把它写进合作方案/工期、或用户问"这个能不能用"时。
判定标准：报告里必须能区分"我实测过"和"README 说的"；没跑过的部分明说没跑过。

## 1. 拉下来看真身

GitHub 会被墙，clone 带代理；仓库改名/迁移时 API 返回 301 `Moved Permanently`，此时用仓库 ID 继续：

```bash
git -c http.proxy=http://127.0.0.1:17890 -c https.proxy=http://127.0.0.1:17890 \
    clone --depth 1 <repo_url> /d/<name>
find . -iname "LICENSE*"        # 空 = 只有声明没有许可文件
curl -sL "https://api.github.com/repositories/<id>"   # license 字段为 null 同上
```

许可写法：仓库根有 LICENSE 文件才叫落实；只有 README 徽章/description 声明时，写"声明 MIT 但仓库无 LICENSE 文件，商用前请作者补文件并留沟通记录"，不要直接写"MIT"。

## 2. 三类硬依赖，逐类 grep

| 找什么 | 命令 | 含义 |
|---|---|---|
| 绑特定 runtime 的内置工具 | `grep -rni "内置\|image_gen\|imagegen\|workbuddy\|codex\|claude" --include=SKILL.md .` | 换 runtime 就要改接口（"内置出图模型"在别的 runtime 并不存在） |
| 第三方 key / 私有接口 | `grep -rn "API_KEY\|TOKEN\|os.environ\|Authorization" --include=*.py --include=*.js --include=*.mjs .` | 装上不等于能用，要配 key、要长期维护 |
| 数据来自谁的服务器 | `grep -rn "https\?://" --include=*.py --include=*.js . \| grep -v github` | 作者自建域名＝随作者成本/心情断供 |

跨 runtime 声明的正确读法：README 自称支持 N 个 runtime，只说明它**没写死**；真正的绑定在"内置工具"和"key"这两处。

## 3. 跑最上游那一步，看后端是否还活着

数据/情报类脚本先单独跑一条最小查询（脚本的 `--help` 或一条关键词），三类结果三种写法：

- 返回真数据 → 可用，记录查到几条
- 报缺 key → 可用但要配 `X_API_KEY`，写成"需自备付费 key"
- `getaddrinfo failed` / 超时 / `curl` 返回 `000` → 这条链路已断，**不要写进方案或工期**

脚本的报错文案本身就暴露它的原生平台（例如提示"请在 Coze 平台的环境变量中添加"＝这个库最初是给 Coze 写的），把这些线索一并报给用户。

## 4. 产出侧要自己出一次成品

文字/排版/配图类：拿真实内容走一遍，把成品文件路径交给用户，别只说"应该能出"。
本机 HTML → PNG 不需要装 playwright，用系统 Chrome 无头模式即可：

```bash
"C:/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=2 --window-size=940,760 \
  --screenshot="D:/out/x.png" "file:///D:/out/x.html"
```

出图后自己看一眼（能看图时用 vision 检查中文有无乱码、文字有无溢出、元素是否截断），确认可用再交付。

## 5. 结论模板

一段话讲清四件事：**哪一半能用了、哪一半要改造、哪一半已经断了、这东西依赖谁（作者自建服务 / 平台官方接口 / 付费 API）**。
对合作方案的意义也要落到具体条目（例如"c92 自建清单里的这几项可以不自己造了"），否则用户拿不到可用的判断。
