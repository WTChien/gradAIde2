# 簡化版 main.py - 移除郵件通知模組，使用簡化的 subscription router
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import traceback
import logging
import sys
from datetime import datetime

from llm import smart_multi_agent_chat, init_vectordb
from firestore import delete_collection
from firebase_config import db

# 導入所有 router（移除 notify_course_users 依賴）
from login import router as login_router
from forget import router as forget_router
from change import router as change_router
from changename import router as changename_router
from report import router as report_router
from upload_image import router as upload_router
from subscription import router as subscription_router  # 🔥 使用簡化版 subscription router

# 配置詳細的 logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger("gradaide_main")
logger.setLevel(logging.DEBUG)

# ========== 數據模型 ==========

class QueryRequest(BaseModel):
    message: str
    image: str | None = None

class UploadCheckRequest(BaseModel):
    account: str

# ========== FastAPI 應用初始化 ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🧹 清除原有向量資料庫...")
    delete_collection("teachers_vector")
    delete_collection("rules_vector")
    delete_collection("faq_vector") 
    logger.info("🚀 初始化向量資料庫...")
    await init_vectordb()
    logger.info("✅ 向量資料庫初始化完成！")
    yield
    logger.info("🛑 伺服器關閉中...")

app = FastAPI(
    title="GradAIde API",
    description="智慧大學AI助理後端服務 - 簡化版（無郵件通知）",
    version="2.6.0",
    lifespan=lifespan, 
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.gradaide.xyz",
        "http://140.136.155.32:3001",
        "http://localhost:3001",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 包含所有功能的 router（移除郵件通知模組）
app.include_router(login_router, tags=["認證"])
app.include_router(forget_router, tags=["忘記密碼"])
app.include_router(change_router, tags=["密碼變更"])
app.include_router(changename_router, tags=["用戶管理"])
app.include_router(report_router, tags=["報告"])
app.include_router(upload_router, tags=["圖片上傳"])
app.include_router(subscription_router, tags=["訂閱管理"])  # 🔥 簡化版訂閱管理 router

# ========== 基本端點 ==========

@app.get("/")
async def root():
    return {
        "message": "GradAIde API 服務正常運行 - 簡化版（無郵件通知）",
        "version": "2.6.0",
        "status": "running",
        "features": {
            "chat": True,
            "image_chat": True,
            "vector_db": True,
            "multi_agent": True,
            "course_search": True,
            "subscription_management": True,
            "email_notifications": False,  # 🔥 明確標示郵件功能已移除
            "unified_endpoints": True,
            "enhanced_logging": True,
            "router_integration": True
        },
        "available_endpoints": {
            "chat": "/query",
            "health": "/health",
            "auth": "/login, /register, /forget_password, /change_password",
            "user_management": "/changename",
            "reports": "/report/*",
            "image_upload": "/upload_image/*",
            "subscription": "/api/subscription-status, /update_subscription, /get_user_profile/*"
        },
        "integrated_routers": [
            "login_router",
            "forget_router", 
            "change_router",
            "changename_router",
            "report_router",
            "upload_router",
            "subscription_router (簡化版)"
        ],
        "removed_features": [
            "郵件發送功能",
            "notify_course_users 模組",
            "訂閱變更郵件通知",
            "郵件內容生成",
            "個性化郵件模板"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    try:
        test_doc = db.collection("health_check").document("test")
        test_doc.set({"timestamp": datetime.now().isoformat()})
        
        return {
            "status": "healthy",
            "service": "GradAIde API - 簡化版（無郵件通知）",
            "version": "2.6.0",
            "database": "connected",
            "subscription_service": "active (簡化版)",
            "email_service": "disabled",  # 🔥 明確標示郵件服務已停用
            "router_integration": "active",
            "logging": "enhanced",
            "all_routers_loaded": True,
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

# ========== 聊天端點 ==========

@app.post("/query")
async def query_model(data: QueryRequest):
    logger.info(f"📥 /query 收到請求: {data.message[:50]}...")
    
    try:
        if data.image:
            logger.info("🖼️ 偵測到圖片，使用圖片對話模式")
            response = smart_multi_agent_chat({"text": data.message, "image": data.image})
        else:
            logger.info("📝 使用純文字對話模式")
            response = smart_multi_agent_chat(data.message)
        
        return {
            "response": response, 
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "has_image": bool(data.image)
        }
        
    except Exception as e:
        logger.error(f"❌ 查詢處理錯誤: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        )

# ========== 圖片上傳相關端點 ==========

@app.post("/pre_upload_check")
async def pre_upload_check(data: UploadCheckRequest):
    """上傳前檢查用戶限制和狀態"""
    try:
        from upload_image import get_user_info, get_user_limits, get_upload_statistics
        
        user_info = await get_user_info(data.account)
        user_limits = get_user_limits(user_info["type"])
        stats = await get_upload_statistics(data.account)
        
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
            "is_admin": user_info["type"] == "admin",
            "recommendations": {
                "compress_large_images": True,
                "supported_formats": ["JPEG", "PNG", "GIF", "WebP"],
                "max_dimension": "2048x2048px",
                "admin_privileges": user_info["type"] == "admin"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 上傳前檢查錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"檢查失敗: {str(e)}")

# ========== 系統統計端點 ==========

@app.get("/admin/system_stats/{admin_account}")
async def get_admin_system_stats(admin_account: str):
    """管理員獲取系統整體統計信息"""
    try:
        from upload_image import get_user_info
        
        admin_info = await get_user_info(admin_account)
        if admin_info["type"] != "admin":
            raise HTTPException(status_code=403, detail="僅管理員可以查看此資訊")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
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
                
                user_info = await get_user_info(doc.id)
                user_type = user_info.get("type", "free")
                if user_type in user_type_stats:
                    user_type_stats[user_type] += today_count
        
        history_count = len(list(db.collection("upload_history").stream()))
        
        return {
            "admin": admin_account,
            "system_stats": {
                "total_uploads_today": total_uploads_today,
                "active_users_today": active_users,
                "total_history_records": history_count,
                "user_type_uploads": user_type_stats,
                "server_status": "healthy",
                "router_integration_status": "active"
            },
            "features_status": {
                "image_upload": "active",
                "compression": "active", 
                "user_limits": "active",
                "statistics": "active",
                "admin_privileges": "active",
                "subscription_management": "active (簡化版)",
                "email_notifications": "disabled",  # 🔥 郵件功能已停用
                "unified_routers": "active"
            },
            "upload_limits_summary": {
                "student_daily_limit": 20,
                "admin_daily_limit": "無限制",
                "teacher_daily_limit": 50,
                "free_daily_limit": 5
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 管理員系統統計錯誤: {str(e)}")
        return {
            "system_stats": {
                "error": str(e),
                "server_status": "error"
            },
            "timestamp": datetime.now().isoformat()
        }

@app.get("/system_stats")
async def get_system_stats():
    """獲取系統整體統計信息（一般用戶版本）"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        
        upload_counts = db.collection("upload_counts").stream()
        total_uploads_today = 0
        active_users = 0
        
        for doc in upload_counts:
            data = doc.to_dict()
            today_count = data.get(today, 0)
            if today_count > 0:
                total_uploads_today += today_count
                active_users += 1
        
        history_count = len(list(db.collection("upload_history").stream()))
        
        return {
            "system_stats": {
                "total_uploads_today": total_uploads_today,
                "active_users_today": active_users,
                "total_history_records": history_count,
                "server_status": "healthy",
                "integration_status": "unified_routers"
            },
            "features_status": {
                "image_upload": "active",
                "compression": "active", 
                "user_limits": "active",
                "statistics": "active",
                "subscription_management": "active (簡化版)",
                "email_notifications": "disabled",  # 🔥 郵件功能已停用
                "router_integration": "active"
            },
            "upload_limits": {
                "student_limit": "20/day",
                "admin_limit": "unlimited",
                "teacher_limit": "50/day",
                "free_limit": "5/day"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 系統統計錯誤: {str(e)}")
        return {
            "system_stats": {
                "error": str(e),
                "server_status": "error"
            },
            "timestamp": datetime.now().isoformat()
        }

# ========== 向後兼容端點 ==========

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
        logger.error(f"❌ 獲取上傳次數錯誤: {str(e)}")
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
        logger.error(f"❌ 更新上傳次數錯誤: {str(e)}")
        return {
            "status": "error", 
            "error": str(e)
        }

# ========== 路由檢查端點 ==========

@app.get("/debug/routes")
async def list_all_routes():
    """列出所有可用的路由端點"""
    routes_info = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes_info.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": getattr(route, 'name', 'Unknown')
            })
    
    return {
        "total_routes": len(routes_info),
        "routes": sorted(routes_info, key=lambda x: x['path']),
        "router_integration": "active",
        "email_service": "disabled",  # 🔥 郵件服務已停用
        "timestamp": datetime.now().isoformat()
    }

# ========== 🔥 新增：郵件功能狀態端點 ==========

@app.get("/email/status")
async def get_email_service_status():
    """獲取郵件服務狀態"""
    return {
        "email_service": {
            "status": "disabled",
            "reason": "郵件功能已移除以簡化系統",
            "subscription_management": "active (僅狀態管理)",
            "notifications": "disabled",
            "removed_features": [
                "訂閱變更郵件通知",
                "歡迎郵件",
                "密碼重設郵件",
                "系統通知郵件",
                "批量郵件發送"
            ]
        },
        "alternative_features": {
            "subscription_status_management": "可透過 API 管理訂閱狀態",
            "in_app_notifications": "建議使用應用內通知替代",
            "admin_dashboard": "管理員可透過儀表板查看統計"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/admin/email/migration-info")
async def get_email_migration_info():
    """獲取郵件功能移除的遷移信息（管理員端點）"""
    return {
        "migration_info": {
            "version": "2.6.0",
            "migration_date": "2025-06-09",
            "reason": "簡化系統架構，專注核心功能",
            "removed_modules": [
                "notify_course_users.py",
                "郵件模板系統",
                "SMTP 配置",
                "郵件發送統計"
            ],
            "preserved_features": [
                "訂閱狀態管理",
                "用戶資料管理", 
                "系統統計",
                "管理員功能"
            ],
            "api_changes": {
                "removed_endpoints": [
                    "POST /test_email_notification",
                    "GET /admin/email-statistics",
                    "GET /admin/failed-emails"
                ],
                "modified_endpoints": [
                    "PUT /update_subscription - 移除 send_notification 參數",
                    "POST /api/update-subscription - 簡化回應格式"
                ],
                "preserved_endpoints": [
                    "GET /get_user_profile/{account}",
                    "GET /api/subscription-status",
                    "GET /admin/subscription-stats"
                ]
            }
        },
        "recommendations": {
            "for_users": [
                "訂閱狀態設定仍可正常使用",
                "重要通知建議透過應用內提示",
                "可隨時查看個人訂閱狀態"
            ],
            "for_developers": [
                "如需郵件功能，可重新整合第三方服務",
                "建議使用推送通知替代郵件提醒",
                "考慮使用 webhook 整合外部通知服務"
            ],
            "for_admins": [
                "訂閱統計功能保持不變",
                "用戶管理功能完整保留",
                "系統性能和穩定性將有所提升"
            ]
        },
        "future_considerations": {
            "可能的替代方案": [
                "整合第三方郵件服務 (SendGrid, AWS SES)",
                "實作推送通知系統",
                "使用 webhook 連接外部通知服務",
                "開發應用內通知中心"
            ],
            "系統優勢": [
                "減少依賴項目",
                "提高系統穩定性",
                "降低維護複雜度",
                "專注核心功能開發"
            ]
        },
        "timestamp": datetime.now().isoformat()
    }

# ========== 錯誤處理器 ==========

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域錯誤處理器"""
    logger.error(f"❌ 未處理的錯誤: {str(exc)}")
    logger.error(traceback.format_exc())
    return {
        "error": "內部伺服器錯誤",
        "status": "error",
        "email_service": "disabled",
        "timestamp": datetime.now().isoformat()
    }

# ========== 主程序入口 ==========

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 啟動 GradAIde API 服務 - 簡化版（無郵件通知）v2.6.0")
    logger.info("📋 已整合的 Router:")
    logger.info("   ✅ login_router")
    logger.info("   ✅ forget_router") 
    logger.info("   ✅ change_router")
    logger.info("   ✅ changename_router")
    logger.info("   ✅ report_router")
    logger.info("   ✅ upload_router")
    logger.info("   🔥 subscription_router (簡化版，無郵件功能)")
    logger.info("")
    logger.info("🚫 已移除的功能:")
    logger.info("   ❌ notify_course_users 模組")
    logger.info("   ❌ 郵件發送功能")
    logger.info("   ❌ 訂閱變更郵件通知")
    logger.info("   ❌ 郵件模板系統")
    logger.info("   ❌ SMTP 配置")
    logger.info("")
    logger.info("✅ 保留的功能:")
    logger.info("   ✅ 訂閱狀態管理")
    logger.info("   ✅ 用戶資料管理")
    logger.info("   ✅ 系統統計")
    logger.info("   ✅ 管理員功能")
    logger.info("   ✅ 所有聊天和上傳功能")
    uvicorn.run(app, host="0.0.0.0", port=8000)