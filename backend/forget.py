# forget.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from email.message import EmailMessage
import aiosmtplib
import random
import string
import time
from firebase_config import db
from fastapi import APIRouter

router = APIRouter()

GMAIL_USER = "gradaide2@gmail.com"
GMAIL_APP_PASSWORD = "vyvo vnvq oypr ator"

verification_codes = {}  # { email: (code, timestamp) }

class EmailRequest(BaseModel):
    account: str
    email: EmailStr

class PasswordReset(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class CodeOnlyVerify(BaseModel):
    email: EmailStr
    code: str

def generate_verification_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

async def send_email_async(to_email: str, code: str):
    message = EmailMessage()
    message["From"] = GMAIL_USER
    message["To"] = to_email
    message["Subject"] = "【GradAIde】驗證碼"
    message.set_content(f"您的驗證碼為：{code}，請於 5 分鐘內完成操作。")

    await aiosmtplib.send(
        message,
        hostname="smtp.gmail.com",
        port=587,
        start_tls=True,
        username=GMAIL_USER,
        password=GMAIL_APP_PASSWORD
    )

@router.post("/send_verification_code")
async def send_verification_code(data: EmailRequest, background_tasks: BackgroundTasks):
    doc_ref = db.collection("Users").document(data.account)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="帳號不存在")

    user_data = doc.to_dict()
    if user_data.get("email") != data.email:
        raise HTTPException(status_code=400, detail="帳號與信箱不符")

    code = generate_verification_code()
    verification_codes[data.email] = (code, time.time())
    background_tasks.add_task(send_email_async, data.email, code)
    return {"message": "驗證碼已寄出"}

@router.post("/verify_code")
async def verify_code(data: CodeOnlyVerify):
    if data.email not in verification_codes:
        raise HTTPException(status_code=400, detail="請先寄送驗證碼")
    saved_code, timestamp = verification_codes[data.email]
    if data.code != saved_code:
        raise HTTPException(status_code=400, detail="驗證碼錯誤")
    if time.time() - timestamp > 300:
        del verification_codes[data.email]
        raise HTTPException(status_code=400, detail="驗證碼已過期")
    return {"message": "驗證成功"}

@router.post("/reset_password")
async def reset_password(data: PasswordReset):
    if data.email not in verification_codes:
        raise HTTPException(status_code=400, detail="請先驗證電子郵件")

    saved_code, timestamp = verification_codes[data.email]
    if data.code != saved_code:
        raise HTTPException(status_code=400, detail="驗證碼錯誤")
    if time.time() - timestamp > 300:
        del verification_codes[data.email]
        raise HTTPException(status_code=400, detail="驗證碼已過期")

    users = db.collection("Users").where("email", "==", data.email).stream()
    user_doc = next(users, None)
    if not user_doc:
        raise HTTPException(status_code=404, detail="找不到該使用者")

    db.collection("Users").document(user_doc.id).update({"password": data.new_password})
    del verification_codes[data.email]
    return {"message": "密碼重設成功"}