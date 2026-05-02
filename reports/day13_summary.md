# Day 13 Burp Suite + LLM HTTP層攻擊總結

## 測試環境
- **靶場**: http_target.py（Flask LLM API）
- **工具**: Burp Suite Community + curl + http_attack.py
- **攔截流量**: Kali → Burp(8080) → Mac(5001) → Ollama
- **測試日期**: 2026-05-01
- **總請求數**: 112

## 發現的漏洞（按嚴重程度）

### Critical

#### 1. /api/admin/logs 無認證存取
- **影響**: 洩漏112筆歷史對話記錄
- **洩漏內容**:
  - 所有 session_id
  - 完整請求/響應內容
  - 用戶 IP 地址
  - 請求 headers
- **利用方式**: `curl http://192.168.64.1:5001/api/admin/logs`
- **可重建完整攻擊歷史**

#### 2. /api/sessions/{id} 無認證存取
- **影響**: 任意存取其他用戶對話
- **發現高價值目標**: session: `admin-session`
- **利用方式**: `curl http://192.168.64.1:5001/api/sessions/admin-session`

#### 3. 系統身份信息洩漏
- **洩漏內容**: 
  - `"我是一个由阿里云开发的SecureAI助手"`
  - 暴露系統提供商和內部名稱
- **攻擊者可利用**: 針對性社交工程攻擊

### High

#### 4. /api/health 配置資訊洩漏
- **洩漏內容**:
  - 模型名稱和版本
  - 內部端點地址
  - 系統架構信息
- **利用方式**: `curl http://192.168.64.1:5001/api/health`

#### 5. 無輸入大小限制
- **測試結果**:
  - 1KB: 正常處理
  - 10KB: 正常處理
  - 50KB: 正常處理
  - 100KB: 正常處理但響應變慢
  - 1MB: timeout（DoS 閾值確認）
- **影響**: 可導致服務拒絕攻擊（DoS）

### Medium

#### 6. Content-Type 混淆
- **問題**: 伺服器接受錯誤的 Content-Type 但仍處理 JSON
- **測試**: 發送 `Content-Type: text/plain` 但 body 為 JSON
- **影響**: 可能繞過某些安全檢查

#### 7. HTTP 參數污染
- **問題**: 重複 JSON key 處理行為不一致
- **測試**: `{"message": "A", "message": "B"}`
- **影響**: 可能導致邏輯錯誤

### Low

#### 8. Session 劫持嘗試（防禦有效）
- **測試 payload**:
  - `admin-session`
  - `../../../etc/passwd`
  - `'; DROP TABLE sessions; --`
  - `<script>alert('xss')</script>`
- **結果**: 系統正確拒絕，但未記錄攻擊行為

## Burp Suite 實戰技巧

### HTTP History
- 記錄所有流量，發現隱藏端點
- 過濾功能快速定位特定請求
- 發現了 `/api/health`、`/api/admin/logs`、`/api/sessions/*` 等端點

### Repeater
- 重複修改請求，測試參數
- 快速測試不同 payload
- 觀察響應差異

### Intruder
- 自動化掃描端點
- Payload fuzzing
- 暴力測試 session_id

## 攻擊鏈整合

```
1. 偵察階段
   └─> /api/health 獲取系統信息
   
2. 信息收集
   └─> /api/admin/logs 獲取所有歷史記錄
       └─> 提取所有 session_id
       
3. 橫向移動
   └─> /api/sessions/{id} 存取其他用戶對話
       └─> 發現 admin-session
       
4. 權限提升（嘗試）
   └─> Header 注入 (X-Admin: true)
   └─> 結果: 未成功
   
5. 拒絕服務
   └─> 發送超大 payload (>1MB)
```

## OWASP 對應

| 漏洞 | OWASP 分類 |
|------|-----------|
| /api/sessions 無認證存取 | API1: Broken Object Level Authorization |
| /api/admin/logs 無認證 | API2: Broken Authentication |
| /health 資訊洩漏 | API8: Security Misconfiguration |
| 系統身份洩漏 | LLM06: Sensitive Information Disclosure |
| 無輸入大小限制 | API4: Unrestricted Resource Consumption |
| Content-Type 混淆 | API8: Security Misconfiguration |

## 防禦建議

### 立即修復（Critical）

1. **所有管理端點加入認證**
   ```python
   @app.before_request
   def check_auth():
       if request.path.startswith('/api/admin'):
           token = request.headers.get('X-API-Key')
           if token != ADMIN_API_KEY:
               abort(401)
   ```

2. **Session 存取控制**
   ```python
   # 驗證 session 所有權
   if session_id not in user_sessions[current_user]:
       abort(403)
   ```

3. **移除系統身份信息**
   - 修改 system prompt，移除「阿里云」、「SecureAI」等標識
   - 使用通用回應

### 短期修復（High）

4. **限制輸入大小**
   ```python
   MAX_MESSAGE_LENGTH = 1000  # 1KB
   if len(request.json.get('message', '')) > MAX_MESSAGE_LENGTH:
       abort(413, 'Message too long')
   ```

5. **Rate Limiting**
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app, key_func=lambda: request.remote_addr)
   
   @app.route('/api/chat', methods=['POST'])
   @limiter.limit("10 per minute")
   def chat():
       ...
   ```

6. **保護或移除 /health 端點**
   - 移除敏感信息
   - 或加入認證

### 長期改進（Medium）

7. **嚴格的 Content-Type 驗證**
   ```python
   if request.content_type != 'application/json':
       abort(415)
   ```

8. **攻擊檢測和日誌**
   ```python
   # 記錄可疑請求
   if is_suspicious(request):
       log_security_event(request)
       alert_admin()
   ```

9. **Session ID 簽名**
   ```python
   import hmac
   session_id = f"{user_id}:{timestamp}:{hmac_signature}"
   ```

## 測試數據統計

- **總攻擊測試**: 7 類
- **成功繞過**: 3 個（無認證端點、信息洩漏、DoS）
- **防禦有效**: 4 個（Token 洩漏、對話歷史、SQL 注入、XSS）
- **Burp 捕獲請求**: 112 個
- **發現隱藏端點**: 3 個

## 關鍵發現

1. **無認證是最大問題** - 3 個 Critical 漏洞都源於此
2. **信息洩漏嚴重** - 系統身份、配置、歷史記錄全部可存取
3. **LLM 防禦部分有效** - 拒絕提供 Token，但洩漏系統身份
4. **缺乏基本安全措施** - 無認證、無限流、無輸入驗證

## 下一步

- [ ] 實施所有 Critical 修復
- [ ] 測試修復後的安全性
- [ ] 建立自動化安全測試
- [ ] 整合到 CI/CD pipeline
- [ ] 進行完整的滲透測試

## 參考資料

- OWASP API Security Top 10: https://owasp.org/API-Security/
- OWASP LLM Top 10: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- Burp Suite Documentation: https://portswigger.net/burp/documentation
