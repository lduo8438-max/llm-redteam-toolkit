# Day 20 garak 整合測試總結

## 測試日期
2026-05-04

## garak 環境設定
- **版本：** v0.9.0.11.post1
- **Generator：** OpenAI 相容模式連接 Ollama
- **目標模型：** qwen2.5-coder:7b
- **連接端點：** http://localhost:11434/v1
- **連接方式：** `OPENAI_API_KEY=ollama OPENAI_API_BASE=http://localhost:11434/v1`

---

## 測試的探針類別

### 1. 提示詞注入 (promptinject)
- **總耗時：** 860.40 秒 (14.3 分鐘)
- **整體防御率：** 58.0% (中等風險)
- **測試數量：** 300 次 (3 個探針 × 100 次)

| 探針 | 防御率 | 風險等級 | 說明 |
|------|--------|----------|------|
| HijackHateHumansMini | 20.0% | 🔴 高危 | 仇恨人類內容劫持 |
| HijackLongPromptMini | 56.0% | 🟡 中危 | 長提示詞攻擊 |
| HijackKillHumansMini | 98.0% | 🟢 低危 | 暴力內容劫持 |

**關鍵發現：**
- 模型對仇恨言論防御極弱 (80% 失敗率)
- 對暴力內容防御強 (2% 失敗率)
- 內容過濾不均衡，存在明顯漏洞

---

### 2. 資訊洩漏 (leakreplay)
- **總耗時：** 922.42 秒 (15.4 分鐘)
- **整體防御率：** 98.2% (低風險)
- **測試數量：** 約 250 次 (6 個探針)

| 探針 | 防御率 | 風險等級 | 說明 |
|------|--------|----------|------|
| GuardianCloze | 100.0% | 🟢 安全 | Guardian 文章填空 |
| GuardianComplete | 100.0% | 🟢 安全 | Guardian 文章補全 |
| LiteratureCloze80 | 94.9% | 🟢 低危 | 文學作品填空 |
| LiteratureComplete80 | 100.0% | 🟢 安全 | 文學作品補全 |
| NYTCloze | 94.4% | 🟢 低危 | NYT 文章填空 |
| NYTComplete | 100.0% | 🟢 安全 | NYT 文章補全 |

**關鍵發現：**
- 填空測試有輕微泄漏 (~5%)
- 補全測試完全安全 (100%)
- 整體訓練數據記憶風險低

---

## garak vs 自定義框架對比

| 項目 | garak | 自定義框架 |
|------|-------|-----------|
| **速度** | 慢（~3s/test，串行執行）| 快（可並發，<1s/test）|
| **覆蓋範圍** | 廣（標準化探針庫）| 針對性強（自定義 payload）|
| **報告格式** | 標準 JSONL + HTML | 自定義 JSON |
| **競賽適用性** | 背景掃描 | 快速攻擊（<30秒）|
| **自定義 payload** | 有限（需修改探針）| 完全自由 |
| **學習曲線** | 陡峭（需理解探針結構）| 平緩（直接編寫攻擊）|
| **可重現性** | 高（標準化測試）| 中（依賴實現）|
| **適用場景** | 完整安全審計 | CTF 競賽、快速驗證 |

---

## 實戰建議

### 競賽場景（時間緊迫）
1. **優先使用自定義框架**
   - 快速攻擊（<30秒提取 flag）
   - 靈活調整 payload
   - 即時反饋和調試

2. **garak 作為輔助**
   - 在背景運行標準化掃描
   - 發現意外漏洞
   - 驗證攻擊覆蓋度

### 完整審計場景
1. **先用 garak 全面掃描**
   - 建立安全基線
   - 發現已知漏洞類型
   - 生成標準化報告

2. **針對性深入測試**
   - 根據 garak 結果設計自定義攻擊
   - 驗證修復效果
   - 探索新型攻擊向量

### 兩者關係
- **互補，不是替代**
- garak：廣度（標準化、可重現）
- 自定義：深度（針對性、靈活性）

---

## OWASP LLM Top 10 對應

### 已測試項目
- **LLM01: Prompt Injection** ✅
  - 測試結果：58% 防御率（中危）
  - 主要漏洞：仇恨言論劫持（20% 防御率）
  
- **LLM06: Sensitive Information Disclosure** ✅
  - 測試結果：98.2% 防御率（低危）
  - 輕微問題：填空測試 ~5% 泄漏率

### 待測試項目
- LLM02: Insecure Output Handling
- LLM03: Training Data Poisoning
- LLM04: Model Denial of Service
- LLM05: Supply Chain Vulnerabilities
- LLM07: Insecure Plugin Design
- LLM08: Excessive Agency
- LLM09: Overreliance
- LLM10: Model Theft

---

## 技術細節

### garak 探針命名問題
- ❌ `promptinjection` → 不存在
- ✅ `promptinject` → 正確
- ❌ `leakage` → 不存在
- ✅ `leakreplay` → 正確

### 連接配置
```bash
# 正確方式（環境變量）
OPENAI_API_KEY=ollama OPENAI_API_BASE=http://localhost:11434/v1 \
garak --model_type openai --model_name qwen2.5-coder:7b \
  --probes <probe_name> --report_prefix <path>

# 錯誤方式（generator_option 參數衝突）
garak --generator_option api_key=ollama  # 會報錯
```

---

## 報告文件位置
- 提示詞注入：`~/llm-redteam/reports/garak_injection.*`
- 資訊洩漏：`~/llm-redteam/reports/garak_leakreplay.*`
- 本總結：`~/llm-redteam/reports/day20_summary.md`

---

## garak 實用指令備忘

### 快速掃描
```bash
garak --model_type openai \
  --model_name [模型名] \
  --generator_option api_key=ollama \
  --generator_option uri=http://localhost:11434/v1 \
  --probes [探針類別]
```

### 常用探針
- `promptinject` → 提示詞注入
- `leakreplay` → 訓練資料洩漏
- `jailbreak` → 越獄
- `continuation` → 有害內容續寫

---

## 下一步計劃
1. 測試更多 garak 探針（encoding, dan, malwaregen 等）
2. 對比 qwen2.5-coder 與其他模型（gemma, glm4）
3. 整合 garak 結果到 Day 17-19 的自定義測試框架
4. 建立統一的漏洞報告格式

---

## 結論

**qwen2.5-coder:7b 安全評估：**
- ✅ **優勢：** 訓練數據保護良好（98.2%）
- ⚠️ **中危：** 提示詞注入防御一般（58%）
- 🔴 **高危：** 仇恨言論過濾嚴重不足（20%）

**總體評價：** 模型在資訊安全方面表現良好，但內容安全過濾存在明顯不均衡，需要加強仇恨言論和長提示詞攻擊的防御。
