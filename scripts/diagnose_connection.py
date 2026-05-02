#!/usr/bin/env python3
"""診斷連接問題"""
import requests
import time

TARGET = "http://192.168.64.1:5001/api/chat"
PROXY = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}

print("🔍 診斷 1: 直接訪問目標（不通過代理）")
try:
    start = time.time()
    r = requests.post(TARGET, json={"message": "test", "session_id": "diag"}, timeout=10, verify=False)
    print(f"✅ 成功 - 狀態碼: {r.status_code}, 耗時: {(time.time()-start)*1000:.0f}ms")
except Exception as e:
    print(f"❌ 失敗: {e}")

print("\n🔍 診斷 2: 通過 Burp 代理訪問")
try:
    start = time.time()
    r = requests.post(TARGET, json={"message": "test", "session_id": "diag"}, proxies=PROXY, timeout=10, verify=False)
    print(f"✅ 成功 - 狀態碼: {r.status_code}, 耗時: {(time.time()-start)*1000:.0f}ms")
except Exception as e:
    print(f"❌ 失敗: {e}")

print("\n💡 解決方案:")
print("1. 如果診斷1成功但診斷2失敗 → Burp Suite 問題")
print("   - 關閉 Burp 的 Intercept (Proxy > Intercept > Intercept is off)")
print("   - 檢查 Proxy Listener 是否監聽 127.0.0.1:8080")
print("2. 如果診斷1和2都失敗 → 目標服務器問題")
print("   - 確認目標服務器正在運行")
print("   - 檢查防火牆設置")
