import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# 檢查是否已初始化 Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate("/home/a411401516/gradAIde_shared/local/backend/gradaide5-firebase-adminsdk-fbsvc-1f64c30917.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 🔹 讀取 JSON 檔案的函數
def load_faq_data(file_path='faq_data.json'):
    """
    從 JSON 檔案讀取 FAQ 資料
    
    Args:
        file_path (str): JSON 檔案路徑，預設為 'faq_data.json'
    
    Returns:
        list: FAQ 資料列表，若讀取失敗則回傳空列表
    """
    try:
        # 檢查檔案是否存在
        if not os.path.exists(file_path):
            print(f"❌ 檔案 '{file_path}' 不存在")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print(f"✅ 成功讀取 {len(data)} 筆 FAQ 資料")
            return data
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式錯誤: {e}")
        return []
    except Exception as e:
        print(f"❌ 讀取 FAQ 資料時發生錯誤: {e}")
        return []

# 🔹 新增課程
def add_course(data):
    try:
        doc_ref = db.collection('InfoHub').add(data)
        print(f"✅ 課程已新增，文件 ID: {doc_ref[1].id}")
    except Exception as e:
        print(f"❌ 新增課程時發生錯誤: {e}")

# 🔹 取得所有課程
def get_courses():
    try:
        courses = db.collection('InfoHub').stream()
        for course in courses:
            print(f"{course.id} => {course.to_dict()}")
    except Exception as e:
        print(f"❌ 取得課程時發生錯誤: {e}")

# 🔹 根據條件篩選文件（新版寫法）
def get_filtered_data(collection_name, field_name, operator, value):
    try:
        valid_operators = ["!=", "<", "<=", "==", ">", ">=", "array_contains", "array_contains_any", "in", "not-in"]
        if operator not in valid_operators:
            raise ValueError(f"❌ 錯誤的條件運算符 '{operator}'，請使用有效的運算符 {valid_operators}")

        # ✅ 用最穩定寫法（位置參數）
        docs = db.collection(collection_name).where(field_name, operator, value).stream()
        found = False
        for doc in docs:
            found = True
            print(f"{doc.id} => {doc.to_dict()}")
        if not found:
            print("🔍 沒有符合條件的文件")
    except Exception as e:
        print(f"❌ 查詢時發生錯誤: {e}")

# 🔹 更新課程資料
def update_course(course_id, update_data):
    try:
        doc_ref = db.collection('Course').document(course_id)
        doc_ref.update(update_data)
        print(f"✅ 課程 {course_id} 已成功更新")
    except Exception as e:
        print(f"❌ 更新課程時發生錯誤: {e}")

# 🔹 刪除課程
def delete_course(course_id):
    try:
        db.collection('Course').document(course_id).delete()
        print(f"✅ 課程 {course_id} 已成功刪除")
    except Exception as e:
        print(f"❌ 刪除課程時發生錯誤: {e}")

def count_documents(collection_name):
    try:
        docs = db.collection(collection_name).stream()
        count = len(list(docs))
        print(f"📦 集合「{collection_name}」共有 {count} 筆資料")
    except Exception as e:
        print(f"❌ 計算文件數量時發生錯誤: {e}")

def delete_collection(collection_name):
    try:
        docs = db.collection(collection_name).stream()
        deleted = 0
        for doc in docs:
            db.collection(collection_name).document(doc.id).delete()
            deleted += 1
        print(f"✅ 已刪除集合「{collection_name}」中的 {deleted} 筆文件")
    except Exception as e:
        print(f"❌ 刪除集合時發生錯誤: {e}")

# 🔹 批次新增 FAQ 資料（更有效率）
def add_faq_batch_transaction(faq_list):
    try:
        if not faq_list:
            print("⚠️ 沒有資料可以新增")
            return
        
        batch = db.batch()
        collection_ref = db.collection('InfoHub')
        
        for faq_item in faq_list:
            doc_ref = collection_ref.document()  # 自動生成 ID
            batch.set(doc_ref, faq_item)
        
        batch.commit()
        print(f"🎉 成功批量新增 {len(faq_list)} 筆 FAQ 資料")
    except Exception as e:
        print(f"❌ 批量新增 FAQ 時發生錯誤: {e}")

# 🔹 從 JSON 檔案載入並新增 FAQ 資料
def load_and_add_faq(file_path='faq_data.json'):
    """
    從 JSON 檔案讀取 FAQ 資料並批次新增到 Firestore
    
    Args:
        file_path (str): JSON 檔案路徑
    """
    print(f"📁 開始從 '{file_path}' 載入 FAQ 資料...")
    faq_data = load_faq_data(file_path)
    
    if faq_data:
        add_faq_batch_transaction(faq_data)
    else:
        print("❌ 無法載入 FAQ 資料，請檢查檔案路徑和格式")

# ================================
# 🔹 使用範例和測試區域
# ================================

if __name__ == "__main__":
    # 📝 使用範例：
    
    # 1. 從 JSON 檔案載入並新增 FAQ 資料
    
    # 2. 只讀取 JSON 資料（不新增到資料庫）
    # faq_data = load_faq_data('faq_data.json')
    # print(f"讀取到 {len(faq_data)} 筆資料")
    
    # 3. 測試查詢課程
    # get_courses()
    
    # 4. 測試篩選條件
    # get_filtered_data("Users", "student_id", "==", "411401516")
    
    # 5. 測試更新課程
    # update_course("D740101483", {"course_credit": 3})
    
    # 6. 測試刪除課程
    # delete_course("D740101483")
    
    # 7. 計算集合數量
    # count_documents("InfoHub")
    
    # 8. 🔥 小心使用！會刪除整個集合的所有文件
    # delete_collection("teachers_vector")
    # delete_collection("courses_vector")
    # delete_collection("rules_vector")
    # delete_collection("InfoHub")
    
    # load_and_add_faq('faq_data.json')

    pass

# 🔹 記得關閉 Firebase 連線
# firebase_admin.delete_app(firebase_admin.get_app())