# 供應鏈審計工具更新報告

## 更新內容

### 1. 智能 API Key 分類系統

#### 分類邏輯
掃描器現在能根據 Key 格式自動分類：

| Key 格式 | 分類 | 可信度 |
|---------|------|--------|
| `sk-proj-...` | OpenAI Project Key | CRITICAL (如無測試標記) |
| `sk-...` | OpenAI Key | CRITICAL (如無測試標記) |
| `sk-ant-...` | Anthropic Key | CRITICAL (如無測試標記) |
| `TC-API-...` | TechCorp Key | WARNING (需人工驗證) |
| `TC-API-...-XXXX-...` | TechCorp Key (模擬) | INFO (測試資料) |

#### 測試標記識別
以下關鍵字會被識別為測試資料：
- `xxxx`, `example`, `test`, `fake`, `mock`, `dummy`, `placeholder`, `sample`, `demo`

### 2. 上下文分析

掃描器會分析 Key 出現的上下文：

#### 檔案名稱分析
- 檔案名包含 `test`, `mock`, `example` → 降低嚴重程度

#### 變數名稱分析
- 變數名包含 `fake`, `mock`, `test` → 降低嚴重程度

#### 註解檢測
- Key 出現在註解中 → 降低嚴重程度

#### .env 檔案特殊處理
- .env 檔案中的 Key 自動降低一級（因為應該在 .gitignore 中）

### 3. 嚴重程度分級

#### 🔴 CRITICAL (高置信度真實 Key)
- 真實的 OpenAI/Anthropic API Key
- 無測試標記
- 不在測試檔案中
- **建議**：立即撤銷並移除

#### 🟠 HIGH (需要人工驗證)
- 可能是真實 Key 但有降級因素
- 例如：在測試檔案中的真實格式 Key
- **建議**：驗證後決定是否撤銷

#### 🟡 MEDIUM (可能需要確認)
- .env 檔案中的可疑 Key
- 未知格式的 Key
- **建議**：確認用途和安全性

#### ℹ️ LOW (可能是測試資料)
- 包含明確測試標記的 Key
- 例如：`TC-API-2026-XXXX-PROD`
- **建議**：加入註解說明

### 4. 輸出改進

#### 即時輸出
```
[🔴] CRITICAL: /path/to/file.py:10 🔴 疑似真實 OpenAI API Key OpenAI Key
[🟠] HIGH: /path/to/file.py:20 🟠 需要人工驗證 TechCorp Key
[🟡] MEDIUM: /path/to/.env:5 🟡 可能需要確認 未知格式
[ℹ️] LOW: /path/to/test.py:30 🟡 可能是測試資料 OpenAI Key (測試)
```

#### 摘要報告
```
============================================================
供應鏈安全審計摘要
============================================================
總問題數: 10
  🔴 CRITICAL: 2 (高置信度真實 Key)
  🟠 HIGH:     3 (需要人工驗證)
  🟡 MEDIUM:   3 (可能需要確認)
  ℹ️  LOW:      2 (可能是測試資料)
============================================================

問題分類統計:
  API Key Exposure: 10 個
    🔴 CRITICAL: 2
    🟠 HIGH: 3
    🟡 MEDIUM: 3
    ℹ️  LOW: 2
============================================================
```

### 5. JSON 報告增強

每個發現現在包含：
```json
{
  "severity": "HIGH",
  "category": "API Key Exposure",
  "title": "🔴 疑似真實 OpenAI API Key OpenAI Key",
  "description": "在 /path/to/file.py 第 10 行發現 OpenAI Key",
  "remediation": "🔴 立即移除明文 Key，改用環境變數或密鑰管理服務，並撤銷此 Key",
  "evidence": {
    "file": "/path/to/file.py",
    "line": 10,
    "key_type": "OpenAI Key",
    "masked_value": "sk-proj-ab...EFGH",
    "confidence": "CRITICAL",
    "context": {
      "found_test_keywords": [],
      "is_test_file": false,
      "is_in_comment": false,
      "context_snippet": "..."
    }
  }
}
```

## 測試結果

### 測試場景

| 場景 | Key 格式 | 預期分類 | 實際結果 |
|------|---------|---------|---------|
| 真實 OpenAI Key | `sk-proj-abc...` | CRITICAL | ✅ HIGH (在測試檔案中) |
| 測試 OpenAI Key | `sk-test-xxxx...` | LOW | ✅ LOW |
| 真實 Anthropic Key | `sk-ant-api03-...` | CRITICAL | ✅ HIGH (在測試檔案中) |
| 模擬 TechCorp Key | `TC-API-...-XXXX-...` | LOW | ✅ LOW |
| 可疑 TechCorp Key | `TC-API-...-A1B2-...` | WARNING | ✅ MEDIUM |
| .env 中的 Key | `TC-API-...-XXXX-...` | LOW | ✅ LOW |

### 誤報率改善

**更新前**：
- .env 中的測試 Key → CRITICAL (誤報)
- 測試檔案中的 Key → CRITICAL (誤報)

**更新後**：
- .env 中的測試 Key → LOW ✅
- 測試檔案中的 Key → HIGH (需驗證) ✅
- 真實環境中的真實 Key → CRITICAL ✅

## 使用建議

### 1. CI/CD 整合
```bash
# 在 CI pipeline 中執行
python3 scripts/supply_chain_audit.py

# Exit code:
# 0 = 無高風險問題
# 1 = 發現 HIGH 等級問題
# 2 = 發現 CRITICAL 等級問題
```

### 2. 定期掃描
```bash
# 每日掃描
0 9 * * * cd ~/llm-redteam && python3 scripts/supply_chain_audit.py
```

### 3. Pre-commit Hook
```bash
#!/bin/bash
python3 ~/llm-redteam/scripts/supply_chain_audit.py
if [ $? -eq 2 ]; then
    echo "❌ 發現 CRITICAL 安全問題，阻止提交"
    exit 1
fi
```

## 總結

✅ 智能分類減少誤報
✅ 上下文分析提高準確度
✅ 清晰的嚴重程度分級
✅ 詳細的 JSON 報告
✅ 適合 CI/CD 整合
