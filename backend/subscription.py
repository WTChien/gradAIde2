# 簡化版 subscription.py - 移除郵件發送功能，只保留訂閱狀態管理
# 版本：3.2.0 - 無郵件通知版本

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import hashlib
import base64
import traceback
import sys
import logging
from firebase_config import db

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("subscription")

# 創建路由器
router = APIRouter()

# ========== 數據模型 ==========

class SubscriptionUpdateRequest(BaseModel):
    """郵件連結訂閱更新請求模型"""
    email: str
    token: str
    subscribe: bool

class FrontendSubscriptionRequest(BaseModel):
    """前端訂閱更新請求模型"""
    account: str
    subscribe: bool

class UserProfileResponse(BaseModel):
    """用戶資料回應模型"""
    subscribe: bool | None
    email: str | None
    username: str | None
    admission_year: str | None
    department_name: str | None
    status: str

# ========== 核心工具函數 ==========

def validate_email_token(email: str, token: str) -> bool:
    """
    驗證郵件連結中的 token 是否有效
    支持當天和前一天的 token（處理時區問題）
    
    Args:
        email: 郵件地址
        token: 驗證 token
        
    Returns:
        bool: 驗證是否成功
    """
    try:
        # 檢查今天的 token
        today = datetime.now().strftime('%Y%m%d')
        token_string = f"{email}_{today}_unsubscribe"
        expected_token = base64.b64encode(hashlib.md5(token_string.encode()).digest()).decode()[:16]
        
        if token == expected_token:
            logger.info(f"✅ 今天的 token 驗證成功: {email}")
            return True
        
        # 檢查昨天的 token（處理時區問題）
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        token_string_yesterday = f"{email}_{yesterday}_unsubscribe"
        expected_token_yesterday = base64.b64encode(hashlib.md5(token_string_yesterday.encode()).digest()).decode()[:16]
        
        if token == expected_token_yesterday:
            logger.info(f"✅ 昨天的 token 驗證成功: {email}")
            return True
            
        logger.warning(f"❌ Token 驗證失敗: {email}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Token 驗證異常: {e}")
        return False

def find_user_by_email_or_account(identifier: str):
    """
    尋找用戶，支持多種查詢方式：
    1. email
    2. student_id  
    3. document ID (account)
    
    Args:
        identifier: 用戶標識符（email/student_id/document_id）
        
    Returns:
        DocumentSnapshot | None: 用戶文檔或 None
    """
    try:
        users_ref = db.collection('Users')
        
        # 方式 1: 按 email 查詢
        try:
            query = users_ref.where('email', '==', identifier).limit(1)
            docs = list(query.stream())
            if docs:
                logger.info(f"✅ 通過 email 找到用戶: {identifier}")
                return docs[0]
        except Exception as e:
            logger.warning(f"⚠️ Email 查詢失敗: {e}")
        
        # 方式 2: 按 student_id 查詢
        try:
            query = users_ref.where('student_id', '==', identifier).limit(1)
            docs = list(query.stream())
            if docs:
                logger.info(f"✅ 通過 student_id 找到用戶: {identifier}")
                return docs[0]
        except Exception as e:
            logger.warning(f"⚠️ Student_id 查詢失敗: {e}")
        
        # 方式 3: 按文檔 ID 查詢（account）
        try:
            doc = users_ref.document(identifier).get()
            if doc.exists:
                logger.info(f"✅ 通過 document ID 找到用戶: {identifier}")
                return doc
        except Exception as e:
            logger.warning(f"⚠️ Document ID 查詢失敗: {e}")
        
        logger.error(f"❌ 找不到用戶: {identifier}")
        return None
        
    except Exception as e:
        logger.error(f"❌ 查詢用戶時發生錯誤: {e}")
        return None

def generate_unsubscribe_token(email: str) -> str:
    """
    為郵件地址生成退訂 token
    
    Args:
        email: 郵件地址
        
    Returns:
        str: 生成的 token
    """
    try:
        today = datetime.now().strftime('%Y%m%d')
        token_string = f"{email}_{today}_unsubscribe"
        token = base64.b64encode(hashlib.md5(token_string.encode()).digest()).decode()[:16]
        logger.info(f"📧 為 {email} 生成退訂 token")
        return token
    except Exception as e:
        logger.error(f"❌ 生成 token 失敗: {e}")
        return ""

def generate_unsubscribe_url(email: str, base_url: str = "https://www.gradaide.xyz") -> str:
    """
    生成完整的退訂連結
    
    Args:
        email: 郵件地址
        base_url: 基礎 URL
        
    Returns:
        str: 完整的退訂連結
    """
    try:
        token = generate_unsubscribe_token(email)
        if not token:
            return ""
        
        url = f"{base_url}/unsubscribe?email={email}&token={token}"
        logger.info(f"📧 為 {email} 生成退訂連結")
        return url
    except Exception as e:
        logger.error(f"❌ 生成退訂連結失敗: {e}")
        return ""

def get_user_subscription_status(identifier: str) -> dict:
    """
    獲取用戶的訂閱狀態
    
    Args:
        identifier: 用戶標識符
        
    Returns:
        dict: 用戶訂閱狀態信息
    """
    try:
        user_doc = find_user_by_email_or_account(identifier)
        if not user_doc:
            return {
                "found": False,
                "subscribed": False,
                "email": None,
                "username": None
            }
        
        user_data = user_doc.to_dict()
        return {
            "found": True,
            "subscribed": user_data.get('subscribe', False),
            "email": user_data.get('email'),
            "username": user_data.get('username', '用戶'),
            "user_id": user_doc.id
        }
    except Exception as e:
        logger.error(f"❌ 獲取訂閱狀態失敗: {e}")
        return {
            "found": False,
            "subscribed": False,
            "email": None,
            "username": None,
            "error": str(e)
        }

def update_user_subscription(user_doc, new_status: bool) -> bool:
    """
    更新用戶的訂閱狀態
    
    Args:
        user_doc: 用戶文檔
        new_status: 新的訂閱狀態
        
    Returns:
        bool: 更新是否成功
    """
    try:
        update_data = {
            'subscribe': new_status,
            'last_subscription_update': datetime.now().isoformat()
        }
        
        user_doc.reference.update(update_data)
        logger.info(f"✅ 用戶 {user_doc.id} 訂閱狀態更新為: {new_status}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 更新訂閱狀態失敗: {e}")
        return False

def verify_subscription_update(user_doc, expected_status: bool) -> bool:
    """
    驗證訂閱狀態更新是否成功
    
    Args:
        user_doc: 用戶文檔
        expected_status: 預期狀態
        
    Returns:
        bool: 驗證是否通過
    """
    try:
        # 重新讀取資料庫
        fresh_data = user_doc.reference.get().to_dict()
        actual_status = fresh_data.get('subscribe')
        
        verification_passed = actual_status == expected_status
        logger.info(f"🔍 訂閱狀態驗證: 預期={expected_status}, 實際={actual_status}, 通過={verification_passed}")
        
        return verification_passed
        
    except Exception as e:
        logger.error(f"❌ 訂閱狀態驗證失敗: {e}")
        return False

# ========== 簡化的處理流程 ==========

async def handle_subscription_change(account: str, new_status: bool) -> dict:
    """
    處理訂閱狀態變更的簡化流程（不發送郵件）
    
    Args:
        account: 用戶帳號
        new_status: 新的訂閱狀態
        
    Returns:
        dict: 處理結果
    """
    result = {
        'success': False,
        'message': '',
        'old_status': None,
        'new_status': None,
        'user_email': None,
        'user_name': None,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # 步驟 1: 查找用戶
        user_doc = find_user_by_email_or_account(account)
        if not user_doc:
            result['message'] = '用戶不存在'
            return result
        
        user_data = user_doc.to_dict()
        old_status = user_data.get('subscribe')
        user_email = user_data.get('email')
        user_name = user_data.get('username', '用戶')
        
        result['old_status'] = old_status
        result['new_status'] = new_status
        result['user_email'] = user_email
        result['user_name'] = user_name
        
        # 步驟 2: 檢查是否需要更新
        if old_status == new_status:
            result['success'] = True
            result['message'] = '訂閱狀態沒有變更'
            return result
        
        # 步驟 3: 更新資料庫
        if not update_user_subscription(user_doc, new_status):
            result['message'] = '資料庫更新失敗'
            return result
        
        # 步驟 4: 驗證更新
        if not verify_subscription_update(user_doc, new_status):
            result['message'] = '資料庫更新驗證失敗'
            return result
        
        result['success'] = True
        result['message'] = '訂閱狀態更新成功'
        
        return result
        
    except Exception as e:
        result['message'] = f'處理失敗: {str(e)}'
        logger.error(f"❌ 訂閱變更處理失敗: {e}")
        traceback.print_exc()
        return result

# ========== 統計和管理函數 ==========

def get_subscription_statistics() -> dict:
    """
    獲取訂閱統計信息
    
    Returns:
        dict: 訂閱統計數據
    """
    try:
        users_ref = db.collection('Users')
        all_users = list(users_ref.stream())
        
        total_users = len(all_users)
        subscribed_users = 0
        unsubscribed_users = 0
        no_preference_users = 0
        
        for user_doc in all_users:
            user_data = user_doc.to_dict()
            subscribe_status = user_data.get('subscribe')
            
            if subscribe_status is True:
                subscribed_users += 1
            elif subscribe_status is False:
                unsubscribed_users += 1
            else:
                no_preference_users += 1
        
        return {
            "total_users": total_users,
            "subscribed_users": subscribed_users,
            "unsubscribed_users": unsubscribed_users,
            "no_preference_users": no_preference_users,
            "subscription_rate": round((subscribed_users / total_users * 100), 2) if total_users > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取訂閱統計失敗: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def get_users_by_subscription_status(subscribed: bool = True) -> list:
    """
    獲取指定訂閱狀態的用戶列表
    
    Args:
        subscribed: 訂閱狀態
        
    Returns:
        list: 用戶列表
    """
    try:
        users_ref = db.collection('Users')
        query = users_ref.where('subscribe', '==', subscribed)
        users = []
        
        for user_doc in query.stream():
            user_data = user_doc.to_dict()
            users.append({
                "user_id": user_doc.id,
                "email": user_data.get('email'),
                "username": user_data.get('username'),
                "department_name": user_data.get('department_name'),
                "admission_year": user_data.get('admission_year'),
                "last_subscription_update": user_data.get('last_subscription_update')
            })
        
        logger.info(f"✅ 找到 {len(users)} 個訂閱狀態為 {subscribed} 的用戶")
        return users
        
    except Exception as e:
        logger.error(f"❌ 獲取用戶列表失敗: {e}")
        return []

def batch_update_subscriptions(user_identifiers: list, new_status: bool) -> dict:
    """
    批量更新用戶訂閱狀態
    
    Args:
        user_identifiers: 用戶標識符列表
        new_status: 新的訂閱狀態
        
    Returns:
        dict: 批量更新結果
    """
    try:
        results = {
            "success_count": 0,
            "failed_count": 0,
            "failed_users": [],
            "success_users": []
        }
        
        for identifier in user_identifiers:
            try:
                user_doc = find_user_by_email_or_account(identifier)
                if not user_doc:
                    results["failed_count"] += 1
                    results["failed_users"].append({
                        "identifier": identifier,
                        "error": "用戶不存在"
                    })
                    continue
                
                if update_user_subscription(user_doc, new_status):
                    results["success_count"] += 1
                    results["success_users"].append({
                        "identifier": identifier,
                        "user_id": user_doc.id
                    })
                else:
                    results["failed_count"] += 1
                    results["failed_users"].append({
                        "identifier": identifier,
                        "error": "更新失敗"
                    })
                    
            except Exception as e:
                results["failed_count"] += 1
                results["failed_users"].append({
                    "identifier": identifier,
                    "error": str(e)
                })
        
        logger.info(f"✅ 批量更新完成: 成功 {results['success_count']}, 失敗 {results['failed_count']}")
        return results
        
    except Exception as e:
        logger.error(f"❌ 批量更新失敗: {e}")
        return {
            "success_count": 0,
            "failed_count": len(user_identifiers),
            "error": str(e)
        }

# ========== API 端點 ==========

@router.get("/api/subscription-status")
async def get_subscription_status_endpoint(email: str, token: str):
    """
    獲取訂閱狀態（來自郵件連結）
    
    Args:
        email: 郵件地址
        token: 驗證 token
        
    Returns:
        dict: 訂閱狀態信息
    """
    try:
        logger.info(f"📧 獲取訂閱狀態: {email}")
        
        if not email or not token:
            raise HTTPException(status_code=400, detail="缺少必要參數")
        if not validate_email_token(email, token):
            raise HTTPException(status_code=403, detail="無效的驗證token")
        
        user_doc = find_user_by_email_or_account(email)
        if not user_doc:
            raise HTTPException(status_code=404, detail="用戶不存在")
            
        user_data = user_doc.to_dict()
        result = {
            "subscribed": user_data.get('subscribe', False),
            "email": email,
            "username": user_data.get('username', '用戶'),
            "status": "success"
        }
        
        logger.info(f"✅ 訂閱狀態查詢成功: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 獲取訂閱狀態失敗: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤")

@router.post("/api/update-subscription")
async def update_subscription_via_email_endpoint(data: SubscriptionUpdateRequest):
    """
    通過郵件連結更新訂閱狀態（簡化版，不發送郵件）
    
    Args:
        data: 訂閱更新請求數據
        
    Returns:
        dict: 更新結果
    """
    try:
        logger.info(f"📧 郵件訂閱更新請求: {data.email}")
        
        if not validate_email_token(data.email, data.token):
            raise HTTPException(status_code=403, detail="無效的驗證token")
            
        # 使用簡化的處理流程
        result = await handle_subscription_change(
            account=data.email,
            new_status=data.subscribe
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['message'])
        
        return {
            "success": True,
            "message": result['message'],
            "new_status": result['new_status'],
            "old_status": result['old_status'],
            "timestamp": result['timestamp']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 更新訂閱狀態失敗: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="服務器錯誤")

@router.put("/update_subscription")
async def update_subscription_from_frontend_endpoint(data: FrontendSubscriptionRequest):
    """
    前端訂閱狀態更新端點（簡化版，不發送郵件）
    
    Args:
        data: 前端訂閱更新請求數據
        
    Returns:
        dict: 更新結果
    """
    try:
        logger.info("🚀 ========== 前端訂閱更新開始 ==========")
        logger.info(f"📥 收到的原始請求數據:")
        logger.info(f"   - account: {data.account}")
        logger.info(f"   - subscribe: {data.subscribe}")
        
        # 使用簡化的處理流程
        result = await handle_subscription_change(
            account=data.account,
            new_status=data.subscribe
        )
        
        # 構建回應
        response = {
            "success": result['success'],
            "message": result['message'],
            "new_status": result['new_status'],
            "old_status": result['old_status'],
            "user_email": result['user_email'],
            "user_name": result['user_name'],
            "timestamp": result['timestamp']
        }
        
        logger.info(f"📤 前端訂閱更新完成: {response}")
        return response
        
    except Exception as e:
        logger.error(f"❌ 前端訂閱更新失敗: {e}")
        traceback.print_exc()
        
        error_response = {
            "success": False,
            "message": f"更新失敗: {str(e)}",
            "new_status": None,
            "old_status": None,
            "user_email": None,
            "user_name": None,
            "timestamp": datetime.now().isoformat()
        }
        
        raise HTTPException(status_code=500, detail=error_response)

@router.get("/get_user_profile/{account}")
async def get_user_profile_endpoint(account: str):
    """
    獲取用戶資料
    
    Args:
        account: 用戶帳號
        
    Returns:
        UserProfileResponse: 用戶資料
    """
    try:
        logger.info(f"📋 獲取用戶資料: {account}")
        
        user_doc = find_user_by_email_or_account(account)
        if not user_doc:
            logger.error(f"❌ 找不到用戶: {account}")
            raise HTTPException(status_code=404, detail="用戶不存在")
            
        user_data = user_doc.to_dict()
        
        result = {
            'subscribe': user_data.get('subscribe'),
            'email': user_data.get('email'),
            'username': user_data.get('username'),
            'admission_year': user_data.get('admission_year'),
            'department_name': user_data.get('department_name'),
            'status': 'success'
        }
        
        logger.info(f"✅ 用戶資料獲取成功: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 獲取用戶資料失敗: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ========== 管理端點 ==========

@router.get("/admin/subscription-stats")
async def get_subscription_stats_endpoint():
    """
    獲取訂閱統計信息（管理員端點）
    
    Returns:
        dict: 訂閱統計數據
    """
    try:
        stats = get_subscription_statistics()
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ 獲取訂閱統計失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/users-by-status")
async def get_users_by_status_endpoint(subscribed: bool = True):
    """
    獲取指定訂閱狀態的用戶列表（管理員端點）
    
    Args:
        subscribed: 訂閱狀態
        
    Returns:
        dict: 用戶列表
    """
    try:
        users = get_users_by_subscription_status(subscribed)
        return {
            "status": "success",
            "subscribed": subscribed,
            "count": len(users),
            "users": users,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ 獲取用戶列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/batch-update")
async def batch_update_endpoint(user_identifiers: list[str], new_status: bool):
    """
    批量更新用戶訂閱狀態（管理員端點）
    
    Args:
        user_identifiers: 用戶標識符列表
        new_status: 新的訂閱狀態
        
    Returns:
        dict: 批量更新結果
    """
    try:
        results = batch_update_subscriptions(user_identifiers, new_status)
        return {
            "status": "success",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ 批量更新失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== 工具端點 ==========

@router.get("/tools/generate-unsubscribe-url")
async def generate_unsubscribe_url_endpoint(email: str, base_url: str = "https://www.gradaide.xyz"):
    """
    生成退訂連結（工具端點）
    
    Args:
        email: 郵件地址
        base_url: 基礎 URL
        
    Returns:
        dict: 包含退訂連結的結果
    """
    try:
        url = generate_unsubscribe_url(email, base_url)
        token = generate_unsubscribe_token(email)
        
        return {
            "status": "success",
            "email": email,
            "unsubscribe_url": url,
            "token": token,
            "base_url": base_url,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ 生成退訂連結失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/validate-token")
async def validate_token_endpoint(email: str, token: str):
    """
    驗證 token（工具端點）
    
    Args:
        email: 郵件地址
        token: 驗證 token
        
    Returns:
        dict: 驗證結果
    """
    try:
        is_valid = validate_email_token(email, token)
        
        return {
            "status": "success",
            "email": email,
            "token": token,
            "is_valid": is_valid,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Token 驗證失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== 模組信息端點 ==========

@router.get("/module-info")
async def get_module_info_endpoint():
    """
    獲取模組版本和功能信息
    
    Returns:
        dict: 模組信息
    """
    return {
        "module": "subscription.py",
        "version": "3.2.0",
        "description": "GradAIde 訂閱管理模組 - 無郵件通知版本",
        "features": [
            "用戶查找（email/student_id/document_id）",
            "Token 驗證（支持當天和前一天）",
            "訂閱狀態管理",
            "退訂連結生成",
            "訂閱統計",
            "批量操作",
            "管理員功能",
            "狀態驗證機制"
        ],
        "removed_features": [
            "郵件發送功能",
            "郵件內容生成",
            "訂閱變更通知",
            "個性化郵件模板",
            "郵件統計追蹤",
            "失敗重試機制"
        ],
        "api_endpoints": [
            "GET /api/subscription-status",
            "POST /api/update-subscription", 
            "PUT /update_subscription",
            "GET /get_user_profile/{account}",
            "GET /admin/subscription-stats",
            "GET /admin/users-by-status",
            "POST /admin/batch-update",
            "GET /tools/generate-unsubscribe-url",
            "GET /tools/validate-token",
            "GET /module-info"
        ],
        "utility_functions": [
            "validate_email_token()",
            "find_user_by_email_or_account()",
            "generate_unsubscribe_token()",
            "generate_unsubscribe_url()",
            "get_user_subscription_status()",
            "update_user_subscription()",
            "verify_subscription_update()",
            "handle_subscription_change()",
            "get_subscription_statistics()",
            "get_users_by_subscription_status()",
            "batch_update_subscriptions()"
        ],
        "data_models": [
            "SubscriptionUpdateRequest",
            "FrontendSubscriptionRequest", 
            "UserProfileResponse"
        ],
        "last_updated": "2025-06-09",
        "author": "GradAIde Team",
        "dependencies": [
            "fastapi",
            "pydantic", 
            "firebase_config"
        ],
        "changelog": {
            "v3.2.0": [
                "移除所有郵件發送功能",
                "移除郵件內容生成",
                "移除訂閱變更通知",
                "移除個性化郵件模板",
                "移除郵件統計追蹤",
                "移除失敗重試機制",
                "簡化處理流程",
                "保留核心訂閱狀態管理",
                "保留統計和管理功能"
            ],
            "v3.1.0": [
                "智能訂閱狀態分析",
                "個性化郵件內容生成",
                "增強郵件發送功能",
                "統計追蹤與失敗監控"
            ],
            "v3.0.0": [
                "基礎訂閱管理功能",
                "Token 驗證機制",
                "基本郵件發送",
                "用戶查找與管理"
            ]
        },
        "timestamp": datetime.now().isoformat()
    }

# ========== 測試和調試功能 ==========

def run_module_tests():
    """執行模組測試（無郵件功能版本）"""
    print("🧪 開始執行 subscription.py 模組測試（無郵件版本）...")
    
    # 測試 1: Token 生成與驗證
    print("\n📋 測試 1: Token 生成與驗證")
    test_email = "test@example.com"
    token = generate_unsubscribe_token(test_email)
    print(f"🔑 生成的 token: {token}")
    
    is_valid = validate_email_token(test_email, token)
    print(f"✅ Token 驗證結果: {is_valid}")
    
    # 測試 2: 退訂連結生成
    print("\n📋 測試 2: 退訂連結生成")
    unsubscribe_url = generate_unsubscribe_url(test_email)
    print(f"🔗 退訂連結: {unsubscribe_url}")
    
    # 測試 3: 用戶查找功能
    print("\n📋 測試 3: 用戶查找功能")
    print("✅ 支持的查找方式:")
    print("   - Email 查找")
    print("   - Student ID 查找") 
    print("   - Document ID 查找")
    
    print("\n🎉 模組測試完成！")
    print("\n📝 功能說明:")
    print("   ✅ 保留：訂閱狀態管理")
    print("   ✅ 保留：用戶查找功能")
    print("   ✅ 保留：統計和管理功能")
    print("   ✅ 保留：Token 驗證")
    print("   ❌ 移除：郵件發送功能")
    print("   ❌ 移除：郵件內容生成")
    print("   ❌ 移除：訂閱變更通知")

if __name__ == "__main__":
    # 執行測試
    run_module_tests()
    
    print("\n📝 使用說明:")
    print("1. 作為工具模組導入:")
    print("   from subscription import handle_subscription_change, get_user_subscription_status")
    print("2. 作為 FastAPI router 使用:")
    print("   app.include_router(subscription.router)")
    print("3. 獨立運行測試:")
    print("   python subscription.py")
    print("4. 查看完整 API 文檔:")
    print("   訪問 /docs 端點")
    print("5. 使用簡化處理流程:")
    print("   result = await handle_subscription_change(account, new_status)")
    print("\n🎯 v3.2.0 主要變更:")
    print("   • 移除所有郵件發送相關功能")
    print("   • 簡化處理流程，專注於狀態管理") 
    print("   • 保留核心訂閱管理功能")
    print("   • 提高系統穩定性和可靠性")