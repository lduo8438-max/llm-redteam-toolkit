# Scripts - 攻擊工具庫

本資料夾包含 LLM 紅隊測試的核心攻擊腳本與防禦工具。

## 🎯 攻擊工具

### HTTP 層攻擊
- **`http_attack.py`** - HTTP 層攻擊腳本（Burp Suite 整合）
  - 無認證端點掃描
  - 會話 ID 遍歷
  - API 文檔洩漏測試
  - OWASP: API1, API2

### Prompt Injection
- **`advanced_extraction.py`** - 系統提示詞提取攻擊
  - 多種提取技術（直接、間接、編碼）
  - OWASP: LLM07
  
- **`encode_payload.py`** - 編碼繞過生成器
  - 支援 Base64、Unicode、URL 編碼
  - OWASP: LLM01

### DoS 攻擊
- **`dos_test.py`** - DoS 攻擊測試
  - 遞迴推理攻擊
  - 長輸入測試
  - OWASP: LLM04
  
- **`dos_defense.py`** - DoS 防禦測試
  - Token 限制驗證
  - 超時機制測試

### 資訊洩漏
- **`model_fingerprint.py`** - 模型指紋識別
  - 識別底層 LLM 模型
  - OWASP: LLM06
  
- **`extract_logs.py`** - 日誌分析工具
  - 從測試日誌中提取敏感資訊

### 供應鏈安全
- **`supply_chain_audit.py`** - 供應鏈安全審計
  - 套件漏洞掃描
  - API Key 洩漏檢測
  - Typosquatting 檢查
  - OWASP: LLM05

## 🛡️ 防禦工具

- **`pii_filter.py`** - PII 過濾器
  - 過濾 Email、電話、IP、API Key、信用卡號
  - OWASP: LLM06

## 🧪 測試框架

- **`test_single.py`** - 單一 Payload 測試
- **`test_batch.py`** - 批次測試框架
- **`test_encoding_resilience.py`** - 編碼繞過韌性測試
- **`diagnose_connection.py`** - Ollama 連線診斷

## 📊 使用統計

- **總腳本數**: 16 個
- **攻擊工具**: 10 個
- **防禦工具**: 2 個
- **測試框架**: 4 個
- **OWASP 覆蓋**: 8 個分類

## 🚀 快速開始

```bash
# 單一測試
python test_single.py

# 批次測試
python test_batch.py

# HTTP 攻擊（需先啟動目標應用）
python http_attack.py

# 編碼繞過
python encode_payload.py "your payload here"

# 供應鏈審計
python supply_chain_audit.py
```

## ⚠️ 使用注意

所有工具僅供**授權測試**和**教育用途**。未經授權使用這些工具進行攻擊是違法行為。
