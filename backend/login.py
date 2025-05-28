# login.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, constr
from typing import Annotated, Pattern
from firebase_config import db
import secrets
from fastapi.responses import JSONResponse


UsernameStr = Annotated[str, constr(min_length=3, max_length=15)]
AccounT = Annotated[str, constr(min_length=6, max_length=15)]
PassWord = Annotated[str, constr(min_length=6, max_length=15)]

router = APIRouter()

class LoginRequest(BaseModel):
    account: str
    password: str

class StudentRegister(BaseModel):
    student_id: str
    password: PassWord
    confirm_password: str
    username: UsernameStr
    email: EmailStr

class NonStudentRegister(BaseModel):
    account: AccounT
    password: PassWord
    confirm_password: str
    username: UsernameStr
    email: EmailStr

@router.post("/register_student")
async def register_student(data: StudentRegister):
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="密碼與確認密碼不一致")

    if len(data.student_id) != 9:
        raise HTTPException(status_code=400, detail="學號必須為 9 碼")

    study_type_code = data.student_id[0]
    admission_year = str(int(data.student_id[1:3]) + 100)
    department_code = data.student_id[3:5]

    if study_type_code == "4":
        study_type = "日間部"
    elif study_type_code == "5":
        study_type = "進修部"
    else:
        study_type = "未知"

    department_mapping = {
        "01": "中國文學系", "02": "歷史學系", "03": "哲學系", "04": "圖書資訊學系",
    "05": "影像傳播學系", "06": "新聞傳播學系", "07": "廣告傳播學系",
    "08": "體育學系體育學組", "09": "體育學系運動競技組", "10": "體育學系運動健康管理組",
    "11": "英國語文學系", "12": "法國語文學系", "13": "西班牙語文學系",
    "14": "日本語文學系", "15": "義大利語文學系", "16": "德國語文學系",
    "17": "數學系資訊數學組", "18": "數學系應用數學組", "19": "化學系",
    "20": "心理學系", "21": "織品服裝學系織品設計組", "22": "織品服裝學系織品服飾行銷組",
    "23": "織品服裝學系服飾設計組", "24": "電機工程學系", "26": "資訊工程學系",
    "27": "生命科學系", "28": "物理學系物理組", "29": "物理學系光電物理組",
    "30": "餐旅管理學系", "31": "兒童與家庭學系", "32": "法律學系",
    "33": "社會學系", "34": "社會工作學系", "35": "經濟學系",
    "36": "財經法律學系", "37": "學士後法律學系", "38": "企業管理學系",
    "39": "會計學系", "40": "資訊管理學系", "41": "金融與國際企業學系",
    "42": "統計資訊學系", "43": "音樂學系", "44": "應用美術系",
    "45": "景觀設計系", "46": "食品科學系", "47": "營養科學系",
    "48": "宗教學系", "49": "護理學系", "50": "公共衛生學系",
    "51": "醫學系", "52": "臨床心理學系", "53": "職能治療學系",
    "54": "呼吸治療學系", "55": "天主教研修學士學位學程",
    "56": "教育領導與科技發展學士學位學程", "57": "醫學資訊與創新應用學士學位學程",
    "58": "人工智慧與資訊安全學士學位學程"
    }
    department_name = department_mapping.get(department_code, "未知系所")

    doc_ref = db.collection("Users").document(data.student_id)
    if doc_ref.get().exists:
        raise HTTPException(status_code=400, detail="學號已被註冊")

    doc_ref.set({
        "student_id": data.student_id,
        "password": data.password,
        "username": data.username,
        "email": data.email,
        "role": "student",
        "study_type": study_type,
        "admission_year": admission_year,
        "department_code": department_code,
        "department_name": department_name
    })
    return {"message": "學生註冊成功", "student_id": data.student_id}

@router.post("/register_non_student")
async def register_non_student(data: NonStudentRegister):
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="密碼與確認密碼不一致")

    doc_ref = db.collection("Users").document(data.account)
    if doc_ref.get().exists:
        raise HTTPException(status_code=400, detail="帳號已被註冊")

    doc_ref.set({
        "account": data.account,
        "password": data.password,
        "username": data.username,
        "email": data.email,
        "role": "non-student"
    })
    return {"message": "非本校學生註冊成功", "account": data.account}

@router.post("/login")
async def login(data: LoginRequest):
    doc_ref = db.collection("Users").document(data.account)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=400, detail="帳號不存在")

    user_data = doc.to_dict()
    if user_data.get("password") != data.password:
        raise HTTPException(status_code=400, detail="密碼錯誤")

    token = secrets.token_hex(16)  # 模擬 token，實際應使用 JWT
    return JSONResponse(content={
        "message": "登入成功",
        "account": data.account,
        "token": token
    })