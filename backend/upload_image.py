from fastapi import APIRouter, UploadFile, HTTPException
from firebase_config import db
from datetime import datetime, timedelta
from base64 import b64encode

router = APIRouter()

@router.post("/upload_image")
async def upload_image(account: str, file: UploadFile):
    if not account:
        raise HTTPException(status_code=401, detail="未登入使用者無法上傳圖片")

    today = datetime.now().strftime("%Y-%m-%d")
    doc_ref = db.collection("upload_counts").document(account)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        count = data.get(today, 0)

        if count >= 5:
            raise HTTPException(status_code=403, detail="今天已達圖片上傳上限（最多 5 次）")

        data[today] = count + 1
        # 清除七天前的資料
        seven_days_ago = datetime.now() - timedelta(days=7)
        for key in list(data.keys()):
            try:
                date_obj = datetime.strptime(key, "%Y-%m-%d")
                if date_obj < seven_days_ago:
                    del data[key]
            except:
                continue

        doc_ref.set(data)
    else:
        doc_ref.set({today: 1})

    # 🔒 圖片處理：這裡僅轉 base64 並回傳（實際應存儲到安全空間如 Firebase Storage）
    content = await file.read()
    encoded = b64encode(content).decode("utf-8")

    return {"status": "ok", "base64": encoded}
