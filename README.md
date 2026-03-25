# GradAIde2

GradAIde2 是一個以輔仁大學課程與校園情境為核心的 AI 助理系統，包含：

- FastAPI 後端 API
- Next.js 前端介面
- Firebase / Firestore 使用者資料與狀態管理
- 課程搜尋、課程評價查詢、圖片上傳與訂閱管理功能

目前程式碼顯示這是一個「簡化版」部署，訂閱狀態管理仍保留，但部分郵件通知功能已從主要流程移除。

## 技術棧

### 後端

- Python 3
- FastAPI
- Uvicorn
- Firebase Admin SDK / Firestore
- LangChain
- Ollama embeddings
- OpenAI Vision

### 前端

- Next.js App Router
- React
- TypeScript
- axios / fetch

## 專案結構

```text
gradAIde2/
├── README.md
├── requirements.txt
├── backend/
│   ├── main.py                  # FastAPI 主入口
│   ├── llm.py                   # LLM 與向量檢索邏輯
│   ├── login.py                 # 登入 / 註冊
│   ├── forget.py                # 忘記密碼
│   ├── change.py                # 修改密碼
│   ├── changename.py            # 修改名稱
│   ├── report.py                # 問題回報
│   ├── upload_image.py          # 圖片上傳
│   ├── subscription.py          # 訂閱管理
│   ├── course_search.py         # 課程搜尋
│   ├── extract_reviews.py       # 課程評價抓取
│   ├── command_line.py          # 命令列代理工具
│   └── firebase_config.py       # Firebase 連線初始化
└── frontend/
	├── app/
	│   ├── page.tsx
	│   ├── login/
	│   ├── forget/
	│   ├── name/
	│   ├── password/
	│   ├── question/
	│   └── subscription-manage/
	└── public/
```

## macOS 開發環境需求

建議使用以下版本：

- macOS
- Python 3.10 以上
- Node.js 18 以上
- npm 9 以上

可先確認版本：

```bash
python3 --version
node --version
npm --version
```

## 後端安裝與啟動

### 1. 建立虛擬環境

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r ../requirements.txt
```

### 2. 準備 Firebase 憑證

目前 `backend/firebase_config.py` 會直接讀取：

```text
backend/firebase-adminsdk.json
```

請將你的 Firebase Admin SDK 金鑰檔放到 `backend/` 目錄下，並命名為：

```text
firebase-adminsdk.json
```

### 3. 準備環境變數

建議在 `backend/.env` 放入至少以下設定：

```env
OPENAI_API_KEY=your_openai_api_key
PROJECT_ID=your_gcp_or_firebase_project_id
USER_AGENT=Mozilla/5.0 (GradAIdeBot)
```

補充說明：

- 圖片對話功能會用到 `OPENAI_API_KEY`
- `llm.py` 會讀取 `PROJECT_ID`
- 部分載入流程會使用 `USER_AGENT`

### 4. 啟動後端

```bash
cd backend
source .venv/bin/activate
python main.py
```

預設會啟動在：

```text
http://127.0.0.1:8000
```

健康檢查：

```text
http://127.0.0.1:8000/health
```

### 5. 常用 API

- `POST /query`：文字或圖片對話
- `POST /login`：登入
- `POST /register_student`：學生註冊
- `POST /register_non_student`：非學生註冊
- `POST /send_verification_code`：寄送忘記密碼驗證碼
- `POST /verify_code`：驗證碼驗證
- `POST /reset_password`：重設密碼
- `POST /change_password`：修改密碼
- `POST /change_name`：修改名稱
- `POST /report_issue`：問題回報
- `POST /pre_upload_check`：圖片上傳前檢查
- `POST /upload_image`：圖片上傳
- `GET /get_user_profile/{account}`：取得使用者資料
- `POST /update_subscription`：前端使用者更新訂閱狀態
- `GET /api/subscription-status`：信件或連結用訂閱狀態查詢
- `POST /api/update-subscription`：信件或連結用訂閱狀態更新

## 前端安裝與啟動

前端程式碼結構明確是 Next.js App Router 專案，並且依賴以下環境變數：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

建議在 `frontend/.env.local` 建立這個設定。

### 重要說明

目前 workspace 內沒有看到 `frontend/package.json`，因此這份 README 只能先根據現有程式碼說明前端需求，無法直接提供完整的安裝指令。

如果你的前端 `package.json` 在其他位置，或尚未加入版本控制，請確認至少包含：

- `next`
- `react`
- `react-dom`
- `typescript`
- `axios`

若你已補齊 `package.json`，一般啟動方式會是：

```bash
cd frontend
npm install
npm run dev
```

預設開發網址通常會是：

```text
http://127.0.0.1:3000
```

## 功能摘要

### 已保留

- AI 文字對話
- 圖片理解與上傳
- 課程搜尋
- 課程評價查詢
- 使用者登入 / 註冊 / 基本資料修改
- 訂閱狀態管理

### 目前主程式標示為已移除或簡化

- 郵件通知主流程
- `notify_course_users` 模組整合
- 訂閱變更郵件通知
- 郵件模板系統

## 其他腳本

### 命令列課程代理

`backend/command_line.py` 會使用瀏覽器代理到輔大課程系統查詢資料。

執行範例：

```bash
cd backend
source .venv/bin/activate
python command_line.py --query "星期一早上的通識課"
```

這個腳本依賴：

- 本機可用的 Ollama 服務
- `qwen3:32b`
- `browser-use` 相關套件

而且程式中目前寫死使用：

```text
http://localhost:11435
```

## 已知注意事項

### 1. Firebase 憑證路徑不完全一致

不同檔案對 Firebase 憑證的讀取方式不完全相同：

- `firebase_config.py` 讀取 `backend/firebase-adminsdk.json`
- `llm.py` 內仍有寫死的 Linux 絕對路徑

如果你要在 macOS 本機穩定執行，建議後續統一改成 `.env` 或單一相對路徑設定。

### 2. 前端依賴清單目前不在 workspace 中

若要在新機器完整重建前端環境，需要先補上 `package.json`。

### 3. CORS 已允許本機開發網址

後端目前允許：

- `http://localhost:3000`
- `http://localhost:3001`

因此本機前端可直接串接後端測試。

## 建議啟動順序

```bash
# Terminal 1
cd backend
source .venv/bin/activate
python main.py

# Terminal 2
cd frontend
npm run dev
```

## 部署前建議

- 將 Firebase 憑證改為環境變數或固定的安全掛載路徑
- 將所有 API 金鑰與 SMTP 設定移出程式碼
- 補齊前端 `package.json` 與鎖檔
- 補上 `.env.example`
- 補上前後端啟動與部署腳本
