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