from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, constr
from fastapi.responses import JSONResponse
from firebase_config import db

router = APIRouter()

class ChangeNameRequest(BaseModel):
    account: str
    new_name: str

@router.post("/change_name")
async def change_name(data: ChangeNameRequest):
    doc_ref = db.collection("Users").document(data.account)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="帳號不存在")

    db.collection("Users").document(data.account).update({
        "username": data.new_name
    })

    return JSONResponse(content={"message": "名稱變更成功"})

@router.get("/get_username/{account}")
async def get_username(account: str):
    doc = db.collection("Users").document(account).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="帳號不存在")

    user = doc.to_dict()
    return {"username": user.get("username")}

# 🆕 新增：取得完整使用者資料（包含學年資訊）
@router.get("/get_user_info/{account}")
async def get_user_info(account: str):
    """取得使用者完整資料，包含學年等詳細資訊"""
    doc = db.collection("Users").document(account).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="帳號不存在")

    user_data = doc.to_dict()
    
    # 準備回傳的使用者資訊
    user_info = {
        "account": account,
        "username": user_data.get("username", ""),
        "email": user_data.get("email", ""),
        "role": user_data.get("role", ""),
        "subscribe": user_data.get("subscribe", False)
    }
    
    # 如果是學生，加入學年相關資訊
    if user_data.get("role") == "student":
        user_info.update({
            "admission_year": user_data.get("admission_year", ""),
            "department_name": user_data.get("department_name", ""),
            "study_type": user_data.get("study_type", ""),
            "student_id": user_data.get("student_id", "")
        })
    
    return user_info