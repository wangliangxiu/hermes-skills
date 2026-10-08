---
name: avalanche-testnet-dev
description: 在 Avalanche 富士测试网做链上开发/核验时用：领测试币、核 RPC、判地址、管私钥。
---

# Avalanche 测试网开发与核验（富士 / Fuji）

触发：领测试币、"这个地址到账了吗/是不是成功"、判断地址/钱包归属、部署合约前的准备、
黑客松链上项目的日常核验。核心原则一句话：**界面数字不是证据，一律用 RPC 和区块 API 复核。**

## 铁律（每次都适用）

1. **先分清两张网，报数必须双网。**
   - 富士 Fuji = 测试网，chainId 43113（0xa869），RPC `https://api.avax-test.network/ext/bc/C/rpc`，币无价值
   - 主网 Mainnet，chainId 43114（0xa86a），RPC `https://api.avax.network/ext/bc/C/rpc`，**真钱**
   - 同一地址在两网各有余额，是**两本互不相通的账**；跨网发送到不了（等于丢）
   - 结论写成"测试网 X AVAX、主网 0"这种形式，别只说一个数
2. **不拿界面数字下结论。** 截图/水龙头页面只能当线索，到账与否用 RPC + routescan 双证。
3. **私钥纪律**：不打印整串（只打字段名 + 长度 + 前 6 位就够判断）、不贴进对话、不让使用者发过来。
   看钱包文件用 Python 读字段名，助记词同理。
4. **能签名才算"能用"**：链上操作要"有私钥的地址"。托管钱包（Builder Hub Console 账户钱包这类）
   拿不到私钥时，让它用界面上的"发送"转到自有地址，别在托管界面里翻钥匙。
5. **合规基线**（本人链上消费类项目通用）：全程测试网、不收款、不碰真实资金；不发代币
   （链上只记凭证，额度不可转让/不可变现）；不做押注、下注、翻倍类赌性玩法。
   术语别混："领水龙头"是领 gas 费，**不是发行虚拟代币**——使用者问"这算代币成功了吗"要直接纠。

## 1. 核余额 / nonce / 是不是合约（一条命令跑两张网）

```bash
ADDR=0x...
req(){ curl -s --max-time 25 -H 'Content-Type: application/json' --data "$1" "$2"; }
for spec in "fuji|https://api.avax-test.network/ext/bc/C/rpc" "mainnet|https://api.avax.network/ext/bc/C/rpc"; do
  name=${spec%%|*}; url=${spec##*|}
  echo "=== $name ==="
  echo -n "chainId: "; req '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' "$url"; echo
  echo -n "balance: "; req "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getBalance\",\"params\":[\"$ADDR\",\"latest\"]}" "$url"; echo
  echo -n "nonce  : "; req "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getTransactionCount\",\"params\":[\"$ADDR\",\"latest\"]}" "$url"; echo
done
```

- 返回是十六进制 wei：`0xde0b6b3a7640000` = 1e18 = **1.0 AVAX**，`0x0` = 0。换算用 execute_code，别心算。
- `nonce=0` = 这地址从没发过交易（全新地址，只能收）。
- 也可直接跑 `scripts/avax_check.py balance 0x地址`，一次打双网。

## 2. 核交易历史（水龙头到没到账）

富士网走 routescan 的 etherscan 兼容接口（43113）：

```bash
curl -s "https://api.routescan.io/v2/network/testnet/evm/43113/etherscan/api?module=account&action=txlist&address=$ADDR&sort=asc&offset=20"
```

`result[]` 每笔有 {hash, timeStamp, from, to, value, isError}。实测能核出"水龙头热钱包 0xd2717e58…
分两笔各 0.5 AVAX 入账、间隔正好 24 小时"，与 RPC 余额一分不差。
浏览器里的交易详情页（状态/区块/时间戳/from/to/value/gas）可以拿来对照，但**结论以 API 为准**。

## 3. 判"两个地址是不是同一把钥匙"

Avalanche 的 C 链地址（`0x…`）与 P/X 链地址（`P-fuji1…` / `P-avax1…`）是**同一串 20 字节**的两种写法：
同一个私钥，两者底层字节必然相同。bech32 解码后比对即可判定（`scripts/avax_check.py samekey`）。

- 字节不同 = **两把不同的钥匙**。别因为"都是同一个 Console 账户里看到的"就当成一个钱包——
  这次就是这么发现使用者给的两个地址不是一把钥匙的。
- P 链余额另查：POST 到 `https://api.avax-test.network/ext/bc/P`，方法 `platform.getBalance`，
  地址要带 `P-fuji` 前缀。P 链是 UTXO 记账，跟 C 链余额不是一本账。

## 4. 领测试币（Builder Hub Console 实测形态）

- Console → Primary Network → **Testnet Faucet**。C 链那张卡**没有地址输入框**，币直接发给你登录
  账户的钱包（文档原话：有 Builder 账户 + 连接钱包，测试币自动发到你的钱包，不需要优惠码、
  不需持有主网余额）。
- 配额与冷却：0.5 AVAX/次，24 小时冷却。按钮显示 `Wait 23h57m` / `等待23小时59分钟` = 冷却中，
  `✓ 准备好了` 才是可领。
- P 链那张卡要手填地址，常见报 `Insufficient funds! Provided UTXOs need…`——那是 P 链 UTXO
  没钱，不是 C 链没钱；只用 EVM 的话忽略它。
- **`Faucet: 26.33 AVAX` 是水龙头池子的余额，不是你的余额**；0.5 AVAX 才是发给你的量。别读错。
- Console 账户钱包的**私钥官方没有导出入口**（Builder Account / Faucet / platform-cli 三个文档页
  都翻过，全无此说明）→ 别在 Console 里找私钥，改走"发送"或换水龙头。
- 备选水龙头：Core 官方 `core.app/tools/testnet-faucet/?token=c`；或在参赛群/群里直接求 0.5 个
  （要给出自有地址）。

## 5. Core 钱包：看地址 / 导私钥 / 看助记词（官方步骤）

- 看 C 链地址：解锁 Core 扩展 → Tools → Settings 打开 **Testnet Mode** → 账户里看地址。
- **导私钥**（扩展）：解锁 → 点左上角账户 → 账户列表里点目标账户的 **Options** →
  **Show Private Key** → 选链（要选 C-Chain）→ 输密码 → **Reveal**。
- **看助记词**：解锁 → 顶部**齿轮** → **Privacy and Security** → **Show recovery phrase** → 输密码。
- 手机版：左上角账户名 → 选账户 → 右侧 **i** → 往下 **Show private key**。
- 坑一：**私钥导出只对"助记词钱包"可用**；用邮箱创建的**无种子钱包（seedless）那一项是灰的**，
  只能导恢复短语。看到灰的别以为操作错了。
- 坑二：C 链私钥与 X/P 链私钥不是同一串（派生路径不同），导之前选对链。

## 6. 本项目（财神算力红包）钱包文件

- 路径 `C:\Users\使用者\.caishen\testnet_wallet.json`，字段 `address` / `private_key` / `note`。
- 代码读它：`caishen/chain.py` 第 21 行 `KEYFILE`、第 47 行 `json.load(...)["private_key"]`。
  **"项目钱包"就是这个文件，不是某个 App**——使用者问"项目钱包在哪"就答这个路径。
- 换钥匙：改 `private_key`（带不带 `0x` 都认），顺手改 `address`；动手前先复制一份 `.bak`。
- 查看内容时只打字段名与长度（见铁律 3）。

## 陷阱

- 别把水龙头池子余额当自己的余额；别把截图当到账证据（见 §2、§4）。
- 十六进制一律用 Python 换算，`0x0` / `0xde0b…` 肉眼猜必错。
- 需要渲染 JS 文档页 / 看页面结构时：浏览器工具没装 Chromium 的话，用手边的 python 环境跑
  playwright（`D:\venvs\caishen\Scripts\python.exe`，配 `PLAYWRIGHT_BROWSERS_PATH=D:/ms-playwright`），
  抓完把临时脚本删掉（使用者规矩：临时脚本不留桌面/临时目录）。
- 登录墙页面（Console 账户面板、钱包设置页）抓不到，也别猜 UI 长什么样：给使用者分步"点哪儿"的
  指令，或请他截图——本次就是靠这个把 Core 导私钥的路径定下来的。
- 官方帮助页（support.core.app 这类）正文用 web_extract 可能只返回标题，改用 playwright 渲染再取。

## 附带脚本

`scripts/avax_check.py` — `balance`（双网余额/nonce/是否合约）、`txlist`（富士交易历史）、
`samekey`（判两个地址是否同一把钥匙）、`pchain`（P 链余额）。只传地址，绝不传私钥。
