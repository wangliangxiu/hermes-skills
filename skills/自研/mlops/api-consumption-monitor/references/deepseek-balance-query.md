# DeepSeek 余额查询配方

## API 端点

```
GET https://api.deepseek.com/user/balance
Authorization: Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 返回格式

```json
{
  "is_available": true,
  "balance_infos": [
    {
      "currency": "CNY",
      "total_balance": "18.81",
      "granted_balance": "0.00",
      "topped_up_balance": "18.81"
    }
  ]
}
```

## Python 查询脚本（可放入 cron 任务）

```python
import urllib.request, json
key = open('/path/to/.env').read().split('DEEPSEEK_API_KEY=')[1].split('\\n')[0].strip().strip(\"'\").strip('\"')
req = urllib.request.Request(
    'https://api.deepseek.com/user/balance',
    headers={'Authorization': f'Bearer {key}'}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    balance = data['balance_infos'][0]['total_balance']
    print(f'DeepSeek 余额: {balance} 元')
```

## 注意事项

- 国内站 `api.deepseek.cn` 在某些网络环境下 DNS 解析失败，优先用国际站 `api.deepseek.com`
- 返回的 `total_balance` 是字符串
- 密钥从 `.env` 文件读取时注意行尾可能有引号或空格需要 strip
