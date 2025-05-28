import firebase_admin
from firebase_admin import credentials, firestore

# 檢查是否已初始化 Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate("/home/a411401516/gradAIde_shared/local/backend/gradaide5-firebase-adminsdk-fbsvc-1f64c30917.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 🔹 新增課程
def add_course(course_data):
    try:
        doc_ref = db.collection('Course').add(course_data)
        print(f"✅ 課程已新增，文件 ID: {doc_ref[1].id}")
    except Exception as e:
        print(f"❌ 新增課程時發生錯誤: {e}")

# 🔹 取得所有課程
def get_courses():
    try:
        courses = db.collection('Course').stream()
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




# 🔹 測試新增課程
new_course = {
    'course_day': '星期五',
    'course_department': '資管一', 
    'course_id': 'D740101483', 
    'course_count': {'開放總人數': 100, '外系': 20}, 
    'course_web': 'https://outline.fju.edu.tw/#/outLineSearch/outlineView/714765/0', 
    'course_credit': 2, 
    'course_teacher': '許嘉霖', 
    'course_name.en': 'Marketing Management', 
    'course_room': 'ES317', 
    'course_language': '中文', 
    'course_name.zh': '行銷管理', 
    'course_type': '選', 
    'course_time': ['D3', 'D4'], 
    'course_enable_years': {'最低年級': '一年級', '最高年級': '四年級', '分發優先順序': '開課單位學生優先'}, 
    'course_semester': '學期'
}

# 測試新增
# add_course(new_course)

# 測試查詢課程
# get_courses()

# 測試篩選條件
# get_filtered_data("Course", "course_name_zh", "==", "電腦應用")

# 測試更新課程
# update_course("D740101483", {"course_credit": 3})

# 測試刪除課程
# delete_course("D740101483")

# 計算集合數量
# count_documents("Course")

# # 🔥 小心使用！會刪除整個集合的所有文件
# delete_collection("teachers_vector")
# delete_collection("courses_vector")
# delete_collection("rules_vector")


# 🔹 記得關閉 Firebase 連線
# firebase_admin.delete_app(firebase_admin.get_app())

def clone_course_to_clean_by_zh_name(source="CourseClean", target="CourseClean"):
    try:
        docs = db.collection(source).stream()
        copied = 0

        for doc in docs:
            data = doc.to_dict()
            cleaned_data = {}

            # 欄位轉換：將 .en/.zh 改為 _en/_zh
            for key, value in data.items():
                if key == "course_name.en":
                    cleaned_data["course_name_en"] = value
                elif key == "course_name.zh":
                    cleaned_data["course_name_zh"] = value
                else:
                    cleaned_data[key] = value

            # 用中文課程名稱作為 ID
            zh_name = cleaned_data.get("course_name_zh")
            if zh_name:
                db.collection(target).document(zh_name).set(cleaned_data)
                print(f"✅ 已複製課程：{zh_name}")
                copied += 1
            else:
                print(f"⚠️ 略過沒有 course_name_zh 的課程：{doc.id}")

        print(f"\n🎉 總共成功複製 {copied} 筆課程到集合「{target}」")
    except Exception as e:
        print(f"❌ 複製過程發生錯誤：{e}")
# clone_course_to_clean_by_zh_name()

