from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, constr
from fastapi.responses import JSONResponse
from firebase_config import db
from datetime import datetime

router = APIRouter()

class ReportRequest(BaseModel):
    account: str
    email: EmailStr
    message: str

@router.get("/get_email/{account}")
async def get_email(account: str):
    doc = db.collection("Users").document(account).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="帳號不存在")

    data = doc.to_dict()
    return {"email": data.get("email")}


@router.post("/report_issue")
async def report_issue(data: ReportRequest):
    try:
        db.collection("Report").add({
            "account": data.account,
            "email": data.email,
            "message": data.message,
            "timestamp": datetime.utcnow()
        })
        return JSONResponse(content={"message": "問題已成功回報，將盡快提供回覆，感謝您！"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回報失敗：{str(e)}")