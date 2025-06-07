# 完善版 main.py - 加入圖片上傳功能並支援管理員無限上傳
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
from changename import router as changename_router
from report import router as report_router

# 🔹 新增：圖片上傳 router
from upload_image import router as upload_router

# lifespan 初始化資料庫
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🧹 清除原有向量資料庫...")
    delete_collection("teachers_vector")
    delete_collection("rules_vector")
    delete_collection("faq_vector") 
    print("🚀 初始化向量資料庫...")
    await init_vectordb()
    print("✅ 向量資料庫初始化完成！")
    yield
    print("🛑 伺服器關閉中...")

# 建立 app 並套用 middleware + router
app = FastAPI(
    title="GradAIde API",
    description="智慧大學AI助理後端服務 - 支援圖片上傳與智能分析，管理員無限上傳",
    version="2.2.0",  # 🔹 版本更新
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

# 🔹 新增：包含圖片上傳功能
app.include_router(upload_router, tags=["圖片上傳"])

# 查詢請求模型（支援圖片）
class QueryRequest(BaseModel):
    message: str
    image: str | None = None

# 🔹 新增：上傳限制檢查請求模型
class UploadCheckRequest(BaseModel):
    account: str

@app.get("/")
async def root():
    return {
        "message": "GradAIde API 服務正常運行",
        "version": "2.2.0",  # 🔹 版本更新
        "status": "running",
        "features": {
            "chat": True,
            "image_chat": True,
            "vector_db": True,
            "multi_agent": True,
            "course_search": True,
            "streaming": False,
            "image_upload": True,
            "upload_statistics": True,
            "image_compression": True,
            "user_type_limits": True,
            "admin_unlimited_upload": True,  # 🔹 新增功能標識
            "role_based_permissions": True  # 🔹 新增權限管理
        },
        "endpoints": {
            "auth": ["/login", "/register_student", "/register_non_student"],
            "password": ["/send_verification_code", "/verify_code", "/reset_password", "/change_password"],
            "user": ["/change_name", "/get_username/{account}"],
            "chat": ["/query", "/test_course_search"],
            "upload": [
                "/upload_image",
                "/upload_statistics/{account}",
                "/check_upload_limit", 
                "/get_upload_count/{account}",
                "/increment_upload_count",
                "/clear_upload_history/{account}",
                "/admin/all_upload_stats"  # 🔹 新增管理員端點
            ]
        },
        "upload_limits": {
            "student": {
                "max_file_size": "10MB",
                "daily_limit": "20 uploads",  # 🔹 更新為20次
                "description": "一般學生權限"
            },
            "admin": {
                "max_file_size": "50MB",
                "daily_limit": "無限制",  # 🔹 管理員無限制
                "description": "管理員無限上傳權限"
            },
            "teacher": {
                "max_file_size": "20MB", 
                "daily_limit": "50 uploads",
                "description": "教師權限"
            },
            "free": {
                "max_file_size": "5MB",
                "daily_limit": "5 uploads", 
                "description": "未登入或未找到用戶"
            },
            "supported_formats": ["JPEG", "PNG", "GIF", "WebP", "BMP"],
            "features": ["Auto compression", "Size validation", "Usage statistics", "Role-based limits"]
        },
        "user_roles": {
            "student": "學生用戶，標準上傳限制",
            "admin": "管理員用戶，無限上傳權限",
            "teacher": "教師用戶，較高上傳限制", 
            "free": "訪客用戶，最低上傳限制"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康檢查端點，用於監控服務狀態"""
    try:
        # 🔹 新增：檢查資料庫連線
        test_doc = db.collection("health_check").document("test")
        test_doc.set({"timestamp": datetime.now().isoformat()})
        
        return {
            "status": "healthy",
            "service": "GradAIde API",
            "database": "connected",
            "features": {
                "vector_db": "ready",
                "image_upload": "ready", 
                "multi_agent": "ready",
                "admin_upload": "ready"  # 🔹 新增管理員上傳狀態
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "GradAIde API", 
            "database": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# 主要查詢端點（支援圖片）
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
        
        # 直接返回 JSON 回應
        return {
            "response": response, 
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "has_image": bool(data.image)
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

# 🔹 修改：圖片上傳前置檢查端點，支援管理員判斷
@app.post("/pre_upload_check")
async def pre_upload_check(data: UploadCheckRequest):
    """上傳前檢查用戶限制和狀態，支援管理員無限上傳"""
    try:
        from upload_image import get_user_info, get_user_limits, get_upload_statistics
        
        user_info = await get_user_info(data.account)
        user_limits = get_user_limits(user_info["type"])
        stats = await get_upload_statistics(data.account)
        
        # 🔹 管理員總是可以上傳
        if user_info["type"] == "admin":
            can_upload = True
            remaining_uploads = "無限制"
        else:
            can_upload = stats["today"] < user_limits["daily_uploads"]
            remaining_uploads = max(0, user_limits["daily_uploads"] - stats["today"])
        
        return {
            "can_upload": can_upload,
            "user_type": user_info["type"],
            "limits": user_limits,
            "today_usage": stats["today"],
            "remaining_uploads": remaining_uploads,
            "statistics": stats,
            "is_admin": user_info["type"] == "admin",  # 🔹 新增：標示管理員身份
            "recommendations": {
                "compress_large_images": True,
                "supported_formats": ["JPEG", "PNG", "GIF", "WebP"],
                "max_dimension": "2048x2048px",
                "admin_privileges": user_info["type"] == "admin"  # 🔹 新增：管理員特權提示
            }
        }
        
    except Exception as e:
        print(f"❌ 上傳前檢查錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"檢查失敗: {str(e)}")

# 🔹 新增：管理員專用端點，獲取系統整體統計
@app.get("/admin/system_stats/{admin_account}")
async def get_admin_system_stats(admin_account: str):
    """管理員獲取系統整體統計信息"""
    try:
        from upload_image import get_user_info
        
        # 驗證管理員身份
        admin_info = await get_user_info(admin_account)
        if admin_info["type"] != "admin":
            raise HTTPException(status_code=403, detail="僅管理員可以查看此資訊")
        
        # 獲取今日總上傳量
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 統計各用戶今日上傳
        upload_counts = db.collection("upload_counts").stream()
        total_uploads_today = 0
        active_users = 0
        user_type_stats = {"student": 0, "admin": 0, "teacher": 0, "free": 0}
        
        for doc in upload_counts:
            data = doc.to_dict()
            today_count = data.get(today, 0)
            if today_count > 0:
                total_uploads_today += today_count
                active_users += 1
                
                # 獲取用戶類型統計
                user_info = await get_user_info(doc.id)
                user_type = user_info.get("type", "free")
                if user_type in user_type_stats:
                    user_type_stats[user_type] += today_count
        
        # 統計總歷史記錄
        history_count = len(list(db.collection("upload_history").stream()))
        
        return {
            "admin": admin_account,
            "system_stats": {
                "total_uploads_today": total_uploads_today,
                "active_users_today": active_users,
                "total_history_records": history_count,
                "user_type_uploads": user_type_stats,
                "server_status": "healthy"
            },
            "features_status": {
                "image_upload": "active",
                "compression": "active", 
                "user_limits": "active",
                "statistics": "active",
                "admin_privileges": "active"  # 🔹 新增管理員特權狀態
            },
            "upload_limits_summary": {
                "student_daily_limit": 20,  # 🔹 更新為20
                "admin_daily_limit": "無限制",
                "teacher_daily_limit": 50,
                "free_daily_limit": 5
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 管理員系統統計錯誤: {str(e)}")
        return {
            "system_stats": {
                "error": str(e),
                "server_status": "error"
            },
            "timestamp": datetime.now().isoformat()
        }

# 🔹 優化：系統統計端點（一般用戶可訪問的版本）
@app.get("/system_stats")
async def get_system_stats():
    """獲取系統整體統計信息（一般用戶版本）"""
    try:
        # 獲取今日總上傳量
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 統計各用戶今日上傳
        upload_counts = db.collection("upload_counts").stream()
        total_uploads_today = 0
        active_users = 0
        
        for doc in upload_counts:
            data = doc.to_dict()
            today_count = data.get(today, 0)
            if today_count > 0:
                total_uploads_today += today_count
                active_users += 1
        
        # 統計總歷史記錄
        history_count = len(list(db.collection("upload_history").stream()))
        
        return {
            "system_stats": {
                "total_uploads_today": total_uploads_today,
                "active_users_today": active_users,
                "total_history_records": history_count,
                "server_status": "healthy"
            },
            "features_status": {
                "image_upload": "active",
                "compression": "active", 
                "user_limits": "active",
                "statistics": "active"
            },
            "upload_limits": {
                "student_limit": "20/day",  # 🔹 更新為20
                "admin_limit": "unlimited",
                "teacher_limit": "50/day",
                "free_limit": "5/day"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 系統統計錯誤: {str(e)}")
        return {
            "system_stats": {
                "error": str(e),
                "server_status": "error"
            },
            "timestamp": datetime.now().isoformat()
        }

# 🔹 新增：檢查用戶角色端點
@app.get("/check_user_role/{account}")
async def check_user_role(account: str):
    """檢查用戶角色和權限"""
    try:
        from upload_image import get_user_info, get_user_limits
        
        user_info = await get_user_info(account)
        user_limits = get_user_limits(user_info["type"])
        
        return {
            "account": account,
            "role": user_info.get("role", "student"),
            "type": user_info["type"],
            "limits": user_limits,
            "is_admin": user_info["type"] == "admin",
            "privileges": {
                "unlimited_upload": user_info["type"] == "admin",
                "higher_file_size": user_info["type"] in ["admin", "teacher"],
                "access_admin_stats": user_info["type"] == "admin"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檢查用戶角色失敗: {str(e)}")

# 保持向後兼容的舊端點路徑
@app.get("/get_upload_count/{account}")
def get_upload_count_legacy(account: str):
    """舊版上傳次數查詢端點（向後兼容）"""
    try:
        doc = db.collection("upload_counts").document(account).get()
        data = doc.to_dict()
        today = datetime.now().strftime("%Y-%m-%d")
        count = data.get(today, 0) if data else 0
        
        return {
            "count": count, 
            "date": today,
            "status": "success"
        }
    except Exception as e:
        print(f"❌ 獲取上傳次數錯誤: {str(e)}")
        return {
            "count": 0, 
            "error": str(e),
            "status": "error"
        }

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
            new_count = counts[today]
        else:
            doc_ref.set({today: 1})
            new_count = 1
            
        return {
            "status": "success", 
            "new_count": new_count,
            "date": today
        }
    except Exception as e:
        print(f"❌ 更新上傳次數錯誤: {str(e)}")
        return {
            "status": "error", 
            "error": str(e)
        }

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