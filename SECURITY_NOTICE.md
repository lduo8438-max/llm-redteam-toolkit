# 安全聲明 / Security Notice

## ⚠️ 重要提醒

本專案中的所有「敏感資料」均為**測試用模擬資料**，不是真實憑證。

## 模擬資料清單

### API Keys（模擬）
- `TC-API-2026-XXXX-PROD` - TechCorp 測試用 API Key
- `MEGA-KEY-2026-PROD-9921` - MegaCorp 測試用 API Key
- `sk-abc123def456ghi789jkl012` - PII 過濾器測試範例

### 密碼（模擬）
- `Admin@MegaCorp2026` - Week 2 測試目標的管理員密碼
- `P@ss2026` - 資料庫連線字串中的測試密碼

### Email（模擬）
- `admin@techcorp.com` - TechCorp 測試郵箱
- `emergency@secure-corp.com` - 緊急聯絡測試郵箱
- `attacker@evil.com` - RAG 投毒測試用惡意郵箱

### 資料庫連線（模擬）
- `postgres://admin:P@ss2026@db.mega.internal/prod`
- `db.techcorp.internal:5432`

### 內部域名（模擬）
- `db.techcorp.internal`
- `db.mega.internal`
- `api.corp.internal`

## 真實敏感資料保護

以下檔案已被 `.gitignore` 排除，**不會上傳到 GitHub**：

- `.env` - 環境變數檔案
- `reports/*.json` - 測試結果（可能包含執行時資料）
- `chroma_db/` - 向量資料庫
- `__pycache__/` - Python 快取

## 驗證方式

```bash
# 確認 .env 未被追蹤
git ls-files | grep "\.env"  # 應該無輸出

# 確認無真實 API Key 格式
git ls-files | xargs grep -E "sk-[a-zA-Z0-9]{48,}" || echo "✅ 安全"
```

## 使用建議

1. **不要**將真實的 API Key 或密碼寫入任何 `.py` 檔案
2. **務必**使用 `.env` 檔案存放真實憑證
3. **確認** `.env` 已在 `.gitignore` 中
4. **定期**執行 `git status --ignored` 檢查敏感檔案

---

**最後更新**: 2026-05-02  
**掃描狀態**: ✅ 已確認無真實敏感資料
