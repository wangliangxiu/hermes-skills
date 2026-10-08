---
name: avalanche-testnet-ops
description: 在 Avalanche 测试网领币、核余额、部署时用。别信界面，核链为准。
---

# Avalanche 测试网：领币、核账、部署

区块链测试网上的操作，界面数字一律要拿链上数据复核，钱包要分清是哪一个。

## 一、核余额用 RPC（直连即可，不用代理）

```
curl -s -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_getBalance","params":["0x你的地址","latest"]}' \
  https://api.avax-test.network/ext/bc/C/rpc
```

- 返回 `"0x0"` 就是 0；有币会返回十六进制 wei。
- 主网：`https://api.avax.network/ext/bc/C/rpc`。两网都可以直接连（不必走本地代理）。
- 富士测试网 C-Chain chainId 43113，主网 43114。
- 结论要用链上数据下，不要用截图下——截图上的余额可能是**另一个钱包**的。

## 二、三种“钱包”别搞混

- **项目钱包**：自己持有私钥的地址。只有这种能用——部署合约、发交易都要它签名。项目要用它，就别把界面上的余额当成它的余额。
- **Console / 钱包应用自带钱包**：跟平台登录账号绑定，界面直接显示它的 C-Chain/P-Chain 余额。Builder Hub Console 的 Testnet Faucet 里，C-Chain 卡片**没有填地址的输入框**，是直接打进登录账号那个钱包；P-Chain 卡片才要你粘地址。这种钱包先确认私钥/助记词能不能导出——不能用私钥的地址，币到了也没用。
- **P-Chain 和 C-Chain 不是一个账本**：P-Chain 走 UTXO。P-Chain 领币失败报 `Insufficient funds! Provided UTXOs need...` 是 UTXO 不够，跟 C-Chain 余额不是一回事，不要把这条报错当成“没领到币”。

要币落到项目地址上，三条路：导出 Console 钱包私钥用它；从 Console 钱包转出到项目地址；换一个能自己填地址的水龙头（faucet.avax.network 一类）直接往项目地址打。

## 三、术语口径（使用者会把领币说成“虚拟代币”）

使用者问“这个算是虚拟代币成功了吗”时，回答要分清三步：

1. 领水龙头 = 领 **gas 费**；
2. AVAX 是链自己的币，不是我们发的；
3. 发行代币是另一步（部署 ERC-20 合约）——本项目红线是**不发代币**、额度不可转让不可变现、链上只记凭证。

测试网 0.5 AVAX 够用（测试网手续费极低），部署合约加发一批交易都够。

## 四、红线

- 全程测试网，不收款、不碰真实资金。界面写“主网络”时先确认到底是主网还是富士——主网真币不得用于项目。
- 领币/查账之后把结论回写到项目的交接说明或日志里（地址、够不够用、下一步卡在哪）。
