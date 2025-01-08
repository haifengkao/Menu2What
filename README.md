# Menu2What API

一個基於 FastAPI 的服務，可以將菜單圖片轉換為結構化的點餐系統，並管理訂單流程。

## 功能特點

### 用戶管理
- 用戶註冊和登入系統
- JWT token 身份驗證
- 安全的密碼加密存儲

### 菜單管理
- 上傳菜單圖片自動識別商品
- 使用 OpenAI Vision API 進行圖像分析
- 自動提取商品名稱、價格、描述和分類

### 臨時性商店
- 商店有效期為 7 天
- 適合臨時性團購或短期訂餐
- 可以分享商店連結給買家

### 訂單系統
- 買家無需登入即可下單
- 只需提供基本聯絡方式
- 自動計算訂單總金額
- 完整的訂單狀態追蹤

## API 端點

### 用戶相關
- `POST /register`: 用戶註冊
- `POST /token`: 用戶登入（獲取 JWT token）

### 菜單相關
- `POST /upload-menu`: 上傳並處理菜單圖片
- `GET /stores`: 獲取用戶的所有商店
- `GET /store/{store_id}`: 獲取特定商店資訊（公開）

### 訂單相關
- `POST /store/{store_id}/order`: 創建新訂單（公開）
- `GET /store/{store_id}/orders`: 獲取商店的所有訂單（僅店主）
- `PUT /store/{store_id}/order/{order_id}`: 更新訂單狀態（僅店主）

## 訂單狀態
- PENDING: 待處理
- CONFIRMED: 已確認
- COMPLETED: 已完成
- CANCELLED: 已取消

## 安裝設置

1. 克隆代碼庫：
   ```bash
   git clone [repository-url]
   cd Menu2What
   ```

2. 創建並設置環境變數文件 (.env)：
   ```
   OPENAI_API_KEY=你的_OpenAI_API_密鑰
   SECRET_KEY=你的_JWT_密鑰
   ```

3. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```

4. 運行服務器：
   ```bash
   uvicorn storeapi.main:app --reload
   ```

## 使用流程

1. **店主端**：
   - 註冊並登入系統
   - 上傳菜單圖片
   - 系統自動生成商店頁面
   - 獲取並分享商店連結
   - 管理訂單狀態

2. **買家端**：
   - 通過分享連結訪問商店
   - 選擇商品並填寫數量
   - 填寫聯絡方式
   - 提交訂單
   - 等待店主確認

## 安全注意事項

- 不要將 .env 文件提交到版本控制系統
- 定期更換 API 密鑰
- 確保 JWT 密鑰的安全性
- .env 文件已包含在 .gitignore 中

## 開發說明

- 開發模式下啟用自動重載
- API 文檔可在 `/docs` 路徑查看
- 目前使用記憶體存儲，生產環境建議使用資料庫
- 支援 OpenAPI 規範的 API 文檔

## API 文檔

完整的 API 文檔可在服務運行時訪問：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 技術棧

- FastAPI
- Python 3.9+
- OpenAI Vision API
- JWT 認證
- Pydantic 數據驗證

## 注意事項

- 商店有效期為創建後 7 天
- 買家下單不需要註冊，但需要提供聯絡方式
- 所有敏感信息都應該存儲在 .env 文件中
- 建議在生產環境中使用資料庫替代記憶體存儲

## 貢獻指南

1. Fork 代碼庫
2. 創建功能分支
3. 提交更改
4. 發起 Pull Request

## 授權

[授權類型]
