# Day 12 Supply Chain 風險總結

## 今日測試項目
1. 環境套件審計（Kali + Mac）
2. API Key 洩漏掃描
3. Typosquatting 偵測
4. 供應鏈審計工具開發與優化

## 關鍵發現

### 發現1：system prompt 明文機密
- **位置**：`final_target.py:40`, `final_target_improved.py:44`
- **內容**：`TC-API-2026-XXXX-PROD`、`db.techcorp.internal:5432`
- **風險**：攻擊者取得程式碼後30秒內可找到所有機密
- **判定**：模擬 Key（假陽性），但揭示了真實開發習慣風險
- **修復**：移到 `.env` 檔案，用 `os.getenv()` 讀取

### 發現2：掃描器假陽性問題
- 初版掃描器無法區分真實 Key 和測試資料
- 升級後加入智能分類：HIGH/WARNING/INFO
- **實戰意義**：專業紅隊報告必須避免假陽性誤導客戶

### 發現3：套件版本安全
- **Mac 環境**：langchain 0.3.28（安全）
- **Kali 環境**：ollama 0.6.1（安全）
- 無 Typosquatting 套件發現

## 供應鏈攻擊完整攻擊鏈

```
攻擊者 → 註冊相似套件名 → 上傳到 PyPI → 開發者誤裝 → 竊取環境變數/Token
   ↓
惡意套件執行 setup.py → 讀取 ~/.aws/credentials, ~/.ssh/id_rsa
   ↓
回傳到 C2 伺服器 → 橫向移動到生產環境
```

## 實戰工具清單
- **supply_chain_audit.py**：智能 API Key 掃描器
- **業界工具對比**：
  - truffleHog：高召回率，適合 Git 歷史掃描
  - gitleaks：快速，適合 CI/CD 整合
  - detect-secrets：低假陽性，適合程式碼審查

## 防禦建議（優先級排序）

### 立即執行
1. 所有機密移到環境變數或 Secret Manager
2. 加入 `.gitignore` 防止 `.env` 被提交

### 短期（1-2週）
3. CI/CD 加入自動 secret 掃描（gitleaks）
4. 建立套件白名單，使用私有 PyPI 鏡像

### 長期（1個月+）
5. 定期審計所有依賴套件的版本和來源
6. 實施 Software Bill of Materials (SBOM)
7. 使用 Dependabot 或 Renovate 自動更新套件

## OWASP LLM 對應
- **LLM03**: Training Data Poisoning（套件投毒）
- **LLM06**: Sensitive Information Disclosure（API Key 洩漏）
- **LLM09**: Misinformation（假陽性誤導）
- **OWASP Top 10 A06**: Vulnerable and Outdated Components

## 與前幾天的關聯
- **Day 8 訓練資料洩漏** → 今天的 system prompt 明文機密
- **Day 9 Function Calling** → 今天的 API Key 可直接呼叫未授權 API
- **Day 10 RAG 投毒** → 今天的套件投毒（同樣是污染信任鏈）

## 測試環境
- **Mac 環境**：Python 3.13.1, langchain 0.3.28
- **Kali 環境**：Python 3.12.8, ollama 0.6.1
- **掃描範圍**：~/llm-redteam 整個專案目錄

## 下一步
- Day 13：Model Denial of Service（模型阻斷服務攻擊）
- 測試重點：Token 洪水、無限迴圈、記憶體耗盡
