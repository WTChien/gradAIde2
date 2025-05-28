# 簡化版 main.py - 移除所有串流功能
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import traceback
from datetime import datetime

from llm import smart_multi_agent_chat, init_vectordb
from firestore import delete_collection
from firebase_config import db

# 各功能 router
from login import router as login_router
from forget import router as forget_router
from change import router as change_router
from upload_image import router as upload_image_router
from changename import router as changename_router
from report import router as report_router

# lifespan 初始化資料庫
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🧹 清除原有向量資料庫...")
    delete_collection("teachers_vector")
    delete_collection("rules_vector")
    print("🚀 初始化向量資料庫...")
    await init_vectordb()
    print("✅ 向量資料庫初始化完成！")
    yield
    print("🛑 伺服器關閉中...")

# 建立 app 並套用 middleware + router
app = FastAPI(
    title="GradAIde API",
    description="智慧大學AI助理後端服務",
    version="2.0.0",
    lifespan=lifespan, 
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.gradaide.xyz",       # 部署後的正式前端
        "http://140.136.155.32:3001",     # 內網開發測試
        "http://localhost:3001",          # 本機開發
        "http://localhost:3000",          # 備用本機端口
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加入 router - 不加 prefix 以保持原有 API 路徑
app.include_router(login_router, tags=["認證"])
app.include_router(forget_router, tags=["忘記密碼"])
app.include_router(change_router, tags=["密碼變更"])
app.include_router(changename_router, tags=["用戶管理"])
app.include_router(report_router, tags=["報告"])
app.include_router(upload_image_router, tags=["上傳"])

# 查詢請求模型（移除 stream 參數）
class QueryRequest(BaseModel):
    message: str
    image: str | None = None

@app.get("/")
async def root():
    return {
        "message": "GradAIde API 服務正常運行",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "chat": True,
            "image_chat": True,
            "vector_db": True,
            "multi_agent": True,
            "course_search": True,
            "streaming": False  # 明確標示不支援串流
        },
        "endpoints": {
            "auth": ["/login", "/register_student", "/register_non_student"],
            "password": ["/send_verification_code", "/verify_code", "/reset_password", "/change_password"],
            "user": ["/change_name", "/get_username/{account}"],
            "chat": ["/query", "/test_course_search"],
            "upload": ["/get_upload_count/{account}", "/increment_upload_count"]
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康檢查端點，用於監控服務狀態"""
    return {
        "status": "healthy",
        "service": "GradAIde API",
        "timestamp": datetime.now().isoformat()
    }

# 主要查詢端點（簡化版，移除串流）
@app.post("/query")
async def query_model(data: QueryRequest):
    print(f"📥 /query 收到請求: {data.message[:50]}...")
    
    try:
        if data.image:
            print("🖼️ 偵測到圖片，使用圖片對話模式")
            response = smart_multi_agent_chat({"text": data.message, "image": data.image})
        else:
            print("📝 使用純文字對話模式")
            response = smart_multi_agent_chat(data.message)
        
        # 直接返回 JSON 回應（移除串流邏輯）
        return {
            "response": response, 
            "status": "success"
        }
        
    except Exception as e:
        print(f"❌ 查詢處理錯誤: {str(e)}")
        traceback.print_exc()
        # 使用 HTTPException 返回結構化錯誤
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        )

# 測試課程搜尋工具的端點（僅供開發測試）
@app.post("/test_course_search")
async def test_course_search(data: QueryRequest):
    """
    測試課程搜尋工具的端點 - 僅供開發測試使用
    實際使用時，課程搜尋會通過 /query 端點由 LLM 自動調用
    """
    try:
        from llm import course_search
        print(f"🧪 測試課程搜尋: {data.message}")
        
        result = course_search(data.message)
        return {
            "query": data.message,
            "result": result,
            "status": "success",
            "note": "這是測試端點，實際使用請透過 /query 端點"
        }
        
    except Exception as e:
        print(f"❌ 測試課程搜尋錯誤: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "query": data.message,
                "status": "error",
                "note": "這是測試端點，實際使用請透過 /query 端點"
            }
        )

# 保持向後兼容的舊端點路徑
@app.get("/get_upload_count/{account}")
def get_upload_count_legacy(account: str):
    """舊版上傳次數查詢端點（向後兼容）"""
    try:
        doc = db.collection("upload_counts").document(account).get()
        data = doc.to_dict()
        today = datetime.now().strftime("%Y-%m-%d")
        return {"count": data.get(today, 0) if data else 0}
    except Exception as e:
        print(f"❌ 獲取上傳次數錯誤: {str(e)}")
        return {"count": 0, "error": str(e)}

@app.post("/increment_upload_count")
def increment_upload_count_legacy(data: dict):
    """舊版上傳次數增加端點（向後兼容）"""
    try:
        account = data["account"]
        today = datetime.now().strftime("%Y-%m-%d")
        doc_ref = db.collection("upload_counts").document(account)
        doc = doc_ref.get()
        if doc.exists:
            counts = doc.to_dict()
            counts[today] = counts.get(today, 0) + 1
            doc_ref.set(counts)
        else:
            doc_ref.set({today: 1})
        return {"status": "ok"}
    except Exception as e:
        print(f"❌ 更新上傳次數錯誤: {str(e)}")
        return {"status": "error", "error": str(e)}

# 錯誤處理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域錯誤處理器"""
    print(f"❌ 未處理的錯誤: {str(exc)}")
    traceback.print_exc()
    return {
        "error": "內部伺服器錯誤",
        "status": "error",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)