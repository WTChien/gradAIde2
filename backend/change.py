from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from firebase_config import db

router = APIRouter()

class ChangePasswordRequest(BaseModel):
    account: str
    old_password: str
    new_password: str
    confirm_password: str


@router.post("/change_password")
async def change_password(data: ChangePasswordRequest):
    doc_ref = db.collection("Users").document(data.account)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="帳號不存在")

    user = doc.to_dict()
    if user.get("password") != data.old_password:
        raise HTTPException(status_code=400, detail="原密碼錯誤")

    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="新密碼與確認密碼不一致")

    db.collection("Users").document(data.account).update({
        "password": data.new_password
    })

    return JSONResponse(content={"message": "密碼變更成功"})