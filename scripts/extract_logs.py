#!/usr/bin/env python3
import requests
import json

response = requests.get("http://192.168.64.1:5001/api/admin/logs")
data = response.json()

print(f"📊 總日誌數：{len(data.get('logs', []))}\n")

# 打印完整的第一條日誌結構
if data.get('logs'):
    print("🔍 第一條日誌的完整結構：")
    print(json.dumps(data['logs'][0], indent=2, ensure_ascii=False))
    print("\n" + "="*60 + "\n")

# 遍歷所有日誌尋找敏感信息
for i, log in enumerate(data.get('logs', []), 1):
    # 檢查所有可能的鍵
    log_str = json.dumps(log, ensure_ascii=False).lower()

    if 'secure-token' in log_str:
        print(f"🚨 發現 secure-token！日誌 #{i}")
        print(json.dumps(log, indent=2, ensure_ascii=False))
        print("\n" + "="*60 + "\n")

    if 'system' in log_str and 'prompt' in log_str:
        print(f"⚠️  可能的 system prompt！日誌 #{i}")
        print(json.dumps(log, indent=2, ensure_ascii=False))
        print("\n" + "="*60 + "\n")
