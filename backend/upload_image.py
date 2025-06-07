from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_config import db
from datetime import datetime, timedelta
from base64 import b64encode
import os
from PIL import Image
import io
import hashlib
import json
from typing import Optional, Dict, Any
import asyncio

router = APIRouter()
security = HTTPBearer(auto_error=False)

# 配置設定
class UploadConfig:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DAILY_UPLOADS = 20  # 🔹 改為每日上傳限制20次
    ALLOWED_FORMATS = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}
    MAX_IMAGE_DIMENSION = 2048  # 最大圖片尺寸
    COMPRESS_QUALITY = 85  # 壓縮品質
    
    # 🔹 修改：根據 role 設定不同的用戶限制
    USER_LIMITS = {
        "student": {"daily_uploads": 20, "max_file_size": 10 * 1024 * 1024},  # 🔹 改為20次
        "admin": {"daily_uploads": 999999, "max_file_size": 50 * 1024 * 1024},  # 🔹 管理員無限上傳
        "teacher": {"daily_uploads": 50, "max_file_size": 20 * 1024 * 1024},
        "free": {"daily_uploads": 5, "max_file_size": 5 * 1024 * 1024}  # 未登入或找不到的用戶
    }

async def get_user_info(account: str) -> Dict[str, Any]:
    """🔹 修改：從 Users 集合中獲取用戶信息，根據 role 欄位判斷用戶類型"""
    try:
        print(f"🔍 查詢用戶信息，帳號: {account}")
        
        # 🔹 修改：從 Users 集合中查詢用戶
        doc = db.collection("Users").document(account).get()
        
        if doc.exists:
            user_data = doc.to_dict()
            user_role = user_data.get("role", "student")  # 預設為 student
            
            print(f"✅ 找到用戶: {account}, role: {user_role}")
            
            # 🔹 根據 role 設定用戶類型
            user_data["type"] = user_role  # 直接使用 role 作為 type
            return user_data
        else:
            print(f"❌ 找不到用戶: {account}")
            # 預設為免費用戶
            return {"type": "free", "account": account, "role": "free"}
            
    except Exception as e:
        print(f"❌ 獲取用戶信息錯誤: {e}")
        return {"type": "free", "account": account, "role": "free"}

def get_user_limits(user_type: str) -> Dict[str, int]:
    """🔹 修改：根據用戶類型獲取上傳限制，支援 admin 無限上傳"""
    limits = UploadConfig.USER_LIMITS.get(user_type, UploadConfig.USER_LIMITS["free"])
    print(f"📊 用戶類型 {user_type} 的限制: {limits}")
    return limits

def validate_image_file(file: UploadFile, max_size: int) -> Dict[str, Any]:
    """驗證圖片檔案"""
    errors = []
    
    # 檢查檔案大小
    if hasattr(file, 'size') and file.size and file.size > max_size:
        errors.append(f"檔案過大（{file.size / 1024 / 1024:.2f}MB），限制為 {max_size / 1024 / 1024:.1f}MB")
    
    # 檢查檔案類型
    if file.content_type not in UploadConfig.ALLOWED_FORMATS:
        errors.append(f"不支援的檔案格式：{file.content_type}")
    
    # 檢查檔案名稱
    if not file.filename:
        errors.append("檔案名稱無效")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "content_type": file.content_type,
        "filename": file.filename
    }

async def compress_image(image_data: bytes, target_quality: int = 85) -> bytes:
    """壓縮圖片以減少檔案大小"""
    try:
        # 開啟圖片
        image = Image.open(io.BytesIO(image_data))
        
        # 轉換為RGB模式（如果需要）
        if image.mode in ('RGBA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # 調整尺寸（如果太大）
        if max(image.size) > UploadConfig.MAX_IMAGE_DIMENSION:
            ratio = UploadConfig.MAX_IMAGE_DIMENSION / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # 壓縮並保存
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=target_quality, optimize=True)
        compressed_data = output.getvalue()
        
        return compressed_data
    except Exception as e:
        print(f"❌ 圖片壓縮錯誤: {e}")
        return image_data  # 如果壓縮失敗，返回原始數據

async def get_upload_statistics(account: str) -> Dict[str, Any]:
    """獲取詳細的上傳統計信息"""
    try:
        doc_ref = db.collection("upload_counts").document(account)
        doc = doc_ref.get()
        
        today = datetime.now().strftime("%Y-%m-%d")
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
        month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        
        if doc.exists:
            data = doc.to_dict()
            
            # 計算各種統計
            today_count = data.get(today, 0)
            week_count = sum(data.get(date, 0) for date in data.keys() 
                           if date >= week_start and date <= today)
            month_count = sum(data.get(date, 0) for date in data.keys() 
                            if date >= month_start and date <= today)
            total_count = sum(data.values()) if isinstance(data, dict) else 0
            
            return {
                "today": today_count,
                "week": week_count,
                "month": month_count,
                "total": total_count,
                "last_upload": max(data.keys()) if data else None
            }
        else:
            return {
                "today": 0,
                "week": 0,
                "month": 0,
                "total": 0,
                "last_upload": None
            }
    except Exception as e:
        print(f"❌ 獲取上傳統計錯誤: {e}")
        return {"today": 0, "week": 0, "month": 0, "total": 0, "last_upload": None}

async def update_upload_count(account: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
    """更新上傳計數並記錄詳細信息"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().isoformat()
        
        # 更新計數
        count_doc_ref = db.collection("upload_counts").document(account)
        count_doc = count_doc_ref.get()
        
        if count_doc.exists:
            counts = count_doc.to_dict()
            counts[today] = counts.get(today, 0) + 1
            
            # 清除超過30天的記錄
            thirty_days_ago = datetime.now() - timedelta(days=30)
            for key in list(counts.keys()):
                try:
                    date_obj = datetime.strptime(key, "%Y-%m-%d")
                    if date_obj < thirty_days_ago:
                        del counts[key]
                except:
                    continue
            
            count_doc_ref.set(counts)
        else:
            count_doc_ref.set({today: 1})
        
        # 記錄詳細的上傳歷史
        upload_history = {
            "account": account,
            "timestamp": timestamp,
            "date": today,
            "file_info": file_info,
            "ip_address": "unknown",  # 可以從請求中獲取
            "user_agent": "unknown"   # 可以從請求中獲取
        }
        
        # 儲存到上傳歷史集合
        db.collection("upload_history").add(upload_history)
        
        return {"success": True, "new_count": counts.get(today, 1) if count_doc.exists else 1}
        
    except Exception as e:
        print(f"❌ 更新上傳計數錯誤: {e}")
        return {"success": False, "error": str(e)}

@router.get("/upload_statistics/{account}")
async def get_upload_stats(account: str):
    """🔹 修改：獲取用戶的上傳統計信息，支援管理員無限上傳顯示"""
    if not account:
        raise HTTPException(status_code=401, detail="需要提供用戶帳號")
    
    try:
        user_info = await get_user_info(account)
        user_limits = get_user_limits(user_info["type"])
        stats = await get_upload_statistics(account)
        
        # 🔹 特別處理管理員的顯示
        if user_info["type"] == "admin":
            remaining_today = "無限制"
            usage_percentage = 0  # 管理員不顯示使用率
        else:
            remaining_today = max(0, user_limits["daily_uploads"] - stats["today"])
            usage_percentage = (stats["today"] / user_limits["daily_uploads"]) * 100
        
        return {
            "account": account,
            "user_type": user_info["type"],
            "limits": user_limits,
            "usage": stats,
            "remaining_today": remaining_today,
            "usage_percentage": usage_percentage,
            "is_admin": user_info["type"] == "admin"  # 🔹 新增：標示是否為管理員
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取統計信息失敗: {str(e)}")

# 🔹 修改：使用正確的 FastAPI 參數聲明，並支援管理員無限上傳
@router.post("/upload_image")
async def upload_image(
    account: str = Form(...),           # 🔹 使用 Form 接收表單字段
    file: UploadFile = File(...)        # 🔹 使用 File 接收上傳文件
):
    """🔹 修改：修復 422 錯誤的圖片上傳端點，支援管理員無限上傳"""
    
    print(f"🔍 收到上傳請求 - 帳號: {account}, 檔案: {file.filename}")
    
    # 基本驗證
    if not account:
        print("❌ 帳號為空")
        raise HTTPException(status_code=401, detail="未登入使用者無法上傳圖片")
    
    if not file:
        print("❌ 檔案為空")
        raise HTTPException(status_code=400, detail="未提供檔案")
    
    try:
        print(f"📁 處理檔案: {file.filename}, 類型: {file.content_type}")
        
        # 獲取用戶信息和限制
        user_info = await get_user_info(account)
        user_limits = get_user_limits(user_info["type"])
        
        print(f"👤 用戶類型: {user_info['type']}, 限制: {user_limits}")
        
        # 讀取檔案內容
        file_content = await file.read()
        actual_file_size = len(file_content)
        
        print(f"📊 檔案大小: {actual_file_size / 1024 / 1024:.2f}MB")
        
        # 驗證檔案
        validation = validate_image_file(file, user_limits["max_file_size"])
        if not validation["valid"]:
            print(f"❌ 檔案驗證失敗: {validation['errors']}")
            raise HTTPException(status_code=400, detail="; ".join(validation["errors"]))
        
        # 額外檢查實際檔案大小
        if actual_file_size > user_limits["max_file_size"]:
            raise HTTPException(
                status_code=413, 
                detail=f"檔案過大（{actual_file_size / 1024 / 1024:.2f}MB），限制為 {user_limits['max_file_size'] / 1024 / 1024:.1f}MB"
            )
        
        # 🔹 修改：檢查今日上傳次數，管理員跳過檢查
        if user_info["type"] != "admin":  # 🔹 管理員跳過上傳次數檢查
            stats = await get_upload_statistics(account)
            if stats["today"] >= user_limits["daily_uploads"]:
                raise HTTPException(
                    status_code=429, 
                    detail=f"今天已達圖片上傳上限（最多 {user_limits['daily_uploads']} 次），請明天再試"
                )
        else:
            print("🔑 管理員身份，跳過上傳次數檢查")
            stats = await get_upload_statistics(account)  # 仍然獲取統計信息用於記錄
        
        print("🗜️ 開始壓縮圖片...")
        
        # 壓縮圖片
        compressed_content = await compress_image(file_content, UploadConfig.COMPRESS_QUALITY)
        compressed_size = len(compressed_content)
        
        print(f"✅ 壓縮完成，原始大小: {actual_file_size}, 壓縮後: {compressed_size}")
        
        # 生成檔案資訊
        file_hash = hashlib.md5(compressed_content).hexdigest()
        file_info = {
            "original_filename": file.filename,
            "content_type": file.content_type,
            "original_size": actual_file_size,
            "compressed_size": compressed_size,
            "compression_ratio": (1 - compressed_size / actual_file_size) * 100 if actual_file_size > 0 else 0,
            "file_hash": file_hash,
            "user_type": user_info["type"]  # 🔹 新增：記錄用戶類型
        }
        
        # 更新上傳計數
        update_result = await update_upload_count(account, file_info)
        if not update_result["success"]:
            print(f"⚠️ 更新計數失敗: {update_result.get('error')}")
        
        # 轉換為 base64
        encoded = b64encode(compressed_content).decode("utf-8")
        
        print("✅ 圖片上傳處理完成")
        
        # 🔹 修改：回應內容，管理員顯示特殊狀態
        if user_info["type"] == "admin":
            usage_info = {
                "today_uploads": stats["today"] + 1,
                "daily_limit": "無限制",
                "remaining": "無限制",
                "user_type": user_info["type"],
                "is_admin": True
            }
        else:
            usage_info = {
                "today_uploads": stats["today"] + 1,
                "daily_limit": user_limits["daily_uploads"],
                "remaining": user_limits["daily_uploads"] - stats["today"] - 1,
                "user_type": user_info["type"],
                "is_admin": False
            }
        
        return {
            "status": "success",
            "message": "圖片上傳成功",
            "base64": encoded,
            "file_info": {
                "original_size_mb": round(actual_file_size / 1024 / 1024, 2),
                "compressed_size_mb": round(compressed_size / 1024 / 1024, 2),
                "compression_ratio": round(file_info["compression_ratio"], 1),
                "content_type": file.content_type
            },
            "usage_info": usage_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 圖片上傳處理錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"圖片處理失敗: {str(e)}")

@router.post("/check_upload_limit")
async def check_upload_limit(data: dict):
    """🔹 修改：檢查上傳限制（不實際上傳），支援管理員無限上傳"""
    account = data.get("account")
    if not account:
        raise HTTPException(status_code=400, detail="需要提供帳號")
    
    try:
        user_info = await get_user_info(account)
        user_limits = get_user_limits(user_info["type"])
        stats = await get_upload_statistics(account)
        
        # 🔹 管理員總是可以上傳
        if user_info["type"] == "admin":
            can_upload = True
            remaining = "無限制"
            daily_limit = "無限制"
        else:
            can_upload = stats["today"] < user_limits["daily_uploads"]
            remaining = max(0, user_limits["daily_uploads"] - stats["today"])
            daily_limit = user_limits["daily_uploads"]
        
        return {
            "can_upload": can_upload,
            "today_uploads": stats["today"],
            "daily_limit": daily_limit,
            "remaining": remaining,
            "user_type": user_info["type"],
            "max_file_size_mb": user_limits["max_file_size"] / 1024 / 1024,
            "statistics": stats,
            "is_admin": user_info["type"] == "admin"  # 🔹 新增：標示是否為管理員
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檢查限制失敗: {str(e)}")

# 保留其他端點...
@router.delete("/clear_upload_history/{account}")
async def clear_upload_history(account: str, days: int = 30):
    """清除指定天數前的上傳歷史（管理員功能）"""
    if not account:
        raise HTTPException(status_code=400, detail="需要提供帳號")
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        # 清除計數記錄
        doc_ref = db.collection("upload_counts").document(account)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            cleaned_data = {k: v for k, v in data.items() if k >= cutoff_str}
            doc_ref.set(cleaned_data)
        
        # 清除歷史記錄
        history_query = db.collection("upload_history").where("account", "==", account).where("date", "<", cutoff_str)
        docs = history_query.stream()
        
        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        
        return {
            "status": "success",
            "message": f"已清除 {days} 天前的上傳記錄",
            "deleted_history_records": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除記錄失敗: {str(e)}")

# 🔹 新增：管理員專用端點，可以查看所有用戶的上傳統計
@router.get("/admin/all_upload_stats")
async def get_all_upload_stats(admin_account: str):
    """管理員查看所有用戶的上傳統計（僅管理員可用）"""
    try:
        # 驗證管理員身份
        admin_info = await get_user_info(admin_account)
        if admin_info["type"] != "admin":
            raise HTTPException(status_code=403, detail="僅管理員可以查看此資訊")
        
        # 獲取所有上傳計數
        upload_counts = db.collection("upload_counts").stream()
        today = datetime.now().strftime("%Y-%m-%d")
        
        all_stats = []
        total_uploads_today = 0
        
        for doc in upload_counts:
            account = doc.id
            data = doc.to_dict()
            today_count = data.get(today, 0)
            total_uploads_today += today_count
            
            if today_count > 0:  # 只顯示今天有上傳的用戶
                user_info = await get_user_info(account)
                all_stats.append({
                    "account": account,
                    "today_uploads": today_count,
                    "user_type": user_info.get("type", "unknown"),
                    "total_uploads": sum(data.values())
                })
        
        # 按今日上傳量排序
        all_stats.sort(key=lambda x: x["today_uploads"], reverse=True)
        
        return {
            "admin": admin_account,
            "total_uploads_today": total_uploads_today,
            "active_users_today": len(all_stats),
            "user_stats": all_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")