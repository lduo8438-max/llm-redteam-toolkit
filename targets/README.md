# Targets - 測試目標應用

本資料夾包含各種 LLM 應用的測試目標，從無防禦的基礎版本到多層防禦的加固版本。

## 🎯 測試目標清單

### 基礎聊天應用
- **`chat_app.py`** - 基礎聊天機器人
  - 無任何防禦機制
  - 適合初學者練習基本 Prompt Injection
  - 防禦等級: ⚠️ 無

### 企業級客服系統
- **`final_target.py`** - TechCorp 客服系統 v2.0
  - 模擬真實企業客服場景
  - 包含敏感資訊（API Key、內部域名）
  - 防禦等級: ⚠️ 低
  
- **`final_target_improved.py`** - TechCorp 客服系統 v2.1
  - 加入四層防禦機制
  - 輸入過濾 + 語義檢測 + 輸出過濾
  - 防禦等級: 🛡️ 高

- **`week2_final_target.py`** - MegaCorp AI Assistant v3.0
  - Week 2 測試目標
  - 更複雜的防禦架構
  - 防禦等級: 🛡️ 中等

### 防禦測試
- **`defended_app.py`** - 四層防禦版本
  - 第 1 層: 輸入過濾（長度、格式、Rate Limiting）
  - 第 2 層: 語義檢測（Prompt Injection 檢測）
  - 第 3 層: 系統提示詞加固
  - 第 4 層: 輸出過濾（PII 過濾）
  - 防禦等級: 🛡️ 中等

### RAG 系統
- **`rag_app.py`** - RAG 知識庫系統
  - 使用 ChromaDB 向量資料庫
  - 測試間接 Prompt Injection
  - 防禦等級: ⚠️ 低
  
- **`rag_poison_app.py`** - RAG 投毒測試環境
  - 專門用於測試 RAG 資料投毒攻擊
  - 無防禦機制
  - OWASP: LLM03
  - 防禦等級: ⚠️ 無

### Agent 系統
- **`agent_app.py`** - LangChain ReAct Agent
  - 包含文件讀取、計算器等工具
  - 測試 Agent 工具濫用
  - OWASP: LLM08
  - 防禦等級: 🛡️ 中等

- **`function_calling_app.py`** - Function Calling 測試
  - 測試函數呼叫劫持
  - OWASP: LLM08
  - 防禦等級: ⚠️ 低

### 多輪對話
- **`multi_turn_app.py`** - 多輪對話系統
  - 測試跨輪次的攻擊鏈
  - 記憶機制測試
  - 防禦等級: ⚠️ 低

### HTTP API
- **`http_target.py`** - Flask API 端點（含漏洞）
  - 無認證的管理端點
  - 會話 ID 可遍歷
  - API 文檔洩漏
  - OWASP: API1, API2, LLM07
  - 防禦等級: ⚠️ 無

## 📁 輔助資料

- **`docs/`** - RAG 測試用文檔
- **`week2_docs/`** - Week 2 測試文檔
- **`agent_files/`** - Agent 測試用文件
- **`chroma_db/`** - ChromaDB 向量資料庫（已加入 .gitignore）

## 🚀 使用方式

### 啟動基礎聊天應用
```bash
python chat_app.py
```

### 啟動 Flask API 目標
```bash
python http_target.py
# 預設監聽 http://localhost:5000
```

### 啟動 RAG 系統
```bash
python rag_app.py
# 需要先啟動 Ollama 服務
```

### 啟動 Agent 系統
```bash
python agent_app.py
# 需要 LangChain 和 Ollama
```

## 📊 防禦等級說明

- ⚠️ **無**: 完全無防禦，所有攻擊都會成功
- ⚠️ **低**: 基本防禦，容易被繞過
- 🛡️ **中等**: 多層防禦，部分攻擊可被攔截
- 🛡️ **高**: 完整防禦架構，大部分攻擊會失敗

## 🎯 測試建議

1. **初學者**: 從 `chat_app.py` 開始
2. **進階**: 測試 `defended_app.py` 的防禦繞過
3. **專家**: 挑戰 `final_target_improved.py` 的五層防禦
4. **RAG 專項**: 使用 `rag_poison_app.py` 練習投毒攻擊
5. **HTTP 層**: 使用 `http_target.py` + Burp Suite

## ⚠️ 使用注意

所有目標應用僅供**授權測試**和**教育用途**。請勿將這些應用部署到生產環境。
