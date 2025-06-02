import datetime
import os
import re
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from glob import glob

import pytesseract
from google.cloud.firestore_v1.base_query import FieldFilter
from pdf2image import convert_from_path

import pdfplumber

# === 設定 ===
TEST_MODE = True 
SERVICE_ACCOUNT_JSON = "gradaide5-firebase-adminsdk-fbsvc-37992a77d2.json"
GMAIL_USER = "gradaide2@gmail.com"
APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD') or input("請輸入 Gmail App Password: ")

# 114-1 學期設定
CURRENT_SEMESTER = "114-1-TEST" if TEST_MODE else "114-1"
SEMESTER_YEAR = 2025

if not APP_PASSWORD or APP_PASSWORD.strip() == "":
    print("❌ 錯誤：需要有效的 Gmail App Password")
    print("📋 如何取得 App Password:")
    print("   1. 到 Google 帳戶設定")
    print("   2. 安全性 → 兩步驟驗證")
    print("   3. 應用程式密碼 → 產生新密碼")
    exit()

# 自動找出最新 PDFvyvo vnvq oypr ator
def find_latest_pdf():
    pdf_files = glob("*114-1*.pdf")  # 優先找114-1的PDF
    if not pdf_files:
        pdf_files = glob("*.pdf")  # 找不到就找所有PDF
    if not pdf_files:
        return None
    latest_pdf = max(pdf_files, key=os.path.getmtime)
    print(f"✅ 自動選擇 PDF：{latest_pdf}")
    return latest_pdf

PDF_PATH = find_latest_pdf()
if not PDF_PATH:
    print("❌ 沒有找到任何 PDF 檔案")
    exit()

# 解析日期格式 (支援 6/11、06/11、2025/6/11 等格式)
def parse_date_from_text(date_str, year=SEMESTER_YEAR):
    """從文字中解析日期，自動補上年份"""
    date_patterns = [
        r'(\d{4})/(\d{1,2})/(\d{1,2})',  # 2025/6/11
        r'(\d{1,2})/(\d{1,2})',          # 6/11
        r'(\d{1,2})月(\d{1,2})日',        # 6月11日
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                if len(match.groups()) == 3:  # 有年份
                    year, month, day = match.groups()
                    return datetime(int(year), int(month), int(day))
                else:  # 沒有年份，使用預設年份
                    month, day = match.groups()
                    return datetime(year, int(month), int(day))
            except ValueError:
                continue
    return None

# 從PDF提取重要日期
def extract_important_dates(pdf_path):
    """從PDF中提取重要的選課日期"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"❌ PDF 讀取失敗: {e}")
        return {}

    if len(text.strip()) < 50:
        print("⚠️  pdfplumber 擷取的文字太少，嘗試使用 OCR...")
        text = extract_text_with_ocr(pdf_path)

    # 解析重要日期
    important_dates = {}
    
    # 定義重要事件的關鍵字和提醒天數
    date_events = {
        "開課資料查詢": {"keywords": ["開課資料查詢", "開課系統"], "remind_days": 3},
        "預選登記": {"keywords": ["預選登記", "預選"], "remind_days": 3},
        "全人課程志願選填": {"keywords": ["全人課程志願選填", "志願選填"], "remind_days": 2},
        "網路初選": {"keywords": ["網路初選"], "remind_days": 2},
        "網路加退選": {"keywords": ["網路加退選", "加退選"], "remind_days": 2},
        "選課確認": {"keywords": ["選課確認"], "remind_days": 2},
        "停修申請": {"keywords": ["停修申請"], "remind_days": 5},
    }
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        for event_name, event_info in date_events.items():
            # 檢查這行是否包含事件關鍵字
            if any(keyword in line for keyword in event_info["keywords"]):
                # 在這行和接下來幾行中尋找日期
                search_lines = [line]
                current_index = lines.index(line) if line in lines else -1
                if current_index >= 0:
                    # 也搜尋前後幾行
                    for i in range(max(0, current_index-2), min(len(lines), current_index+5)):
                        if i != current_index:
                            search_lines.append(lines[i])
                
                for search_line in search_lines:
                    date_obj = parse_date_from_text(search_line)
                    if date_obj and event_name not in important_dates:
                        important_dates[event_name] = {
                            "date": date_obj,
                            "remind_days": event_info["remind_days"],
                            "original_text": search_line.strip()
                        }
                        print(f"✅ 找到 {event_name}: {date_obj.strftime('%Y/%m/%d')} ({search_line.strip()})")
                        break
    
    if not important_dates:
        print("⚠️  未找到任何重要日期，請檢查PDF內容")
    
    return important_dates

# 檢查今天是否需要發送通知
def should_send_notification_today(important_dates):
    """檢查今天是否有需要提醒的事件"""
    today = datetime.now().date()
    notifications_to_send = []
    
    for event_name, event_info in important_dates.items():
        event_date = event_info["date"].date()
        remind_days = event_info["remind_days"]
        remind_date = event_date - timedelta(days=remind_days)
        
        print(f"📅 {event_name}: {event_date}, 提醒日: {remind_date}")
        
        if today == remind_date:
            notifications_to_send.append({
                "event": event_name,
                "date": event_date,
                "days_before": remind_days,
                "original_text": event_info["original_text"]
            })
            print(f"🔔 今天需要提醒: {event_name}")
        elif today == event_date:
            notifications_to_send.append({
                "event": event_name,
                "date": event_date,
                "days_before": 0,
                "original_text": event_info["original_text"]
            })
            print(f"🔔 今天就是事件日: {event_name}")
    
    return notifications_to_send

# 圖片型 PDF 用 OCR 擷取文字
def extract_text_with_ocr(pdf_path):
    print("🔍 這是圖片型 PDF，使用 OCR 擷取...")
    try:
        images = convert_from_path(pdf_path)
        text = ""
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image, lang='chi_tra')
            text += f"\n--- 第 {i+1} 頁 ---\n" + page_text
        return text
    except Exception as e:
        print(f"❌ OCR 擷取失敗: {e}")
        return ""

# 生成通知內容
def generate_notification_content(notifications_to_send, important_dates):
    """根據需要提醒的事件生成通知內容"""
    if not notifications_to_send:
        return None
    
    content_lines = ["📅 輔仁大學 114-1 學期選課重要提醒：\n"]
    
    for notification in notifications_to_send:
        event = notification["event"]
        date = notification["date"]
        days_before = notification["days_before"]
        
        if days_before == 0:
            content_lines.append(f"🔥 【今天就是】{event} ({date.strftime('%m/%d')})")
        else:
            content_lines.append(f"⏰ 【{days_before}天後】{event} ({date.strftime('%m/%d')})")
        
        content_lines.append(f"   📝 {notification['original_text']}\n")
    
    # 加入完整時程表
    content_lines.append("\n📋 完整114-1選課時程：")
    for event_name, event_info in sorted(important_dates.items(), key=lambda x: x[1]["date"]):
        date_str = event_info["date"].strftime('%m/%d')
        content_lines.append(f"🔸 {date_str} - {event_name}")
    
    content_lines.append("\n💡 請及時完成相關選課作業，避免影響學習規劃！")
    content_lines.append("\n📱 更多選課資訊請上輔大選課系統查詢")
    content_lines.append("-- GradAIde 團隊 關心您的學習")
    
    return "\n".join(content_lines)

# 初始化 Firestore
def init_firestore(json_path):
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        if not os.path.exists(json_path):
            print(f"❌ Firebase 憑證檔案不存在: {json_path}")
            return None
            
        if not firebase_admin._apps:
            cred = credentials.Certificate(json_path)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"❌ Firebase 初始化失敗: {e}")
        return None

# 取得訂閱者
def get_subscribers(db, notification_key):
    """取得還沒收到特定通知的訂閱者"""
    subscribers = []
    all_docs = db.collection('Users').stream()
    
    for doc in all_docs:
        data = doc.to_dict()
        email = data.get('email', '').strip()
        notified_list = data.get('notified_events', [])

        # 測試模式：忽略已通知檢查
        if TEST_MODE:
            if email and '@' in email and data.get('subscribe', False):
                subscribers.append({
                    'email': email,
                    'name': data.get('username', '用戶'),
                    'ref': doc.reference
                })
                print(f"✅ [測試模式] 加入: {email}")
            else:
                print(f"⏭️  [測試模式] 跳過: {email} (未訂閱或無效郵件)")
        else:
            # 正式模式：檢查是否已通知過這個特定事件
            if email and '@' in email and notification_key not in notified_list and data.get('subscribe', False):
                subscribers.append({
                    'email': email,
                    'name': data.get('username', '用戶'),
                    'ref': doc.reference
                })
                print(f"✅ 加入: {email} 尚未收到 {notification_key} 通知")
            else:
                print(f"⏭️  跳過: {email} 已通知或不符合")
    
    return subscribers

# 生成專業HTML郵件
def generate_professional_html_email(name, content):
    """"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GradAIde 選課提醒</title>
    </head>
    <body style="font-family: 'Microsoft JhengHei', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">📚 GradAIde 選課小提醒</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">輔仁大學選課提醒服務</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-left: 4px solid #667eea;">
            <h2 style="color: #667eea; margin-top: 0;">親愛的 {name} 同學您好！</h2>
            <div style="background: white; padding: 15px; border-radius: 8px; white-space: pre-line; border-left: 3px solid #28a745;">
                {content}
            </div>
        </div>
        
        <div style="background: #e9ecef; padding: 15px; border-radius: 0 0 10px 10px; text-align: center; font-size: 12px; color: #6c757d;">
            <p>此郵件由 GradAIde 自動發送，請勿回覆</p>
            <p>如不想收到此類通知，請登入系統取消訂閱</p>
        </div>
    </body>
    </html>
    """
    return html_content

# 發送郵件
def send_email(to_email, to_name, content, doc_ref=None, notification_key=None):
    # 測試模式在主旨加上標記
    subject_prefix = "[TEST] " if TEST_MODE else ""
    subject = f"{subject_prefix}📣 GradAIde 114-1 選課提醒通知 / Course Selection Reminder"

    # 簡單的純文字版本
    test_prefix = "[測試郵件] " if TEST_MODE else ""
    body_plain = f"{test_prefix}親愛的 {to_name} 同學您好：\n\n{content}\n\n-- GradAIde 團隊"
    
    # 使用專業 HTML 模板
    body_html = generate_professional_html_email(to_name, content)

    msg = MIMEMultipart("alternative")
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body_plain, 'plain', 'utf-8'))
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    try:
        print(f"📧 正在發送給 {to_email}...")
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ 成功寄送給 {to_email}")

        # 測試模式不更新資料庫
        if doc_ref and not TEST_MODE and notification_key:
            # 更新已通知事件列表
            doc_ref.update({
                'notified_events': firestore.ArrayUnion([notification_key]),
                'last_notified': datetime.today().strftime('%Y-%m-%d')
            })
            print(f"📝 已更新 {to_email} 的通知記錄")
        elif TEST_MODE:
            print(f"🧪 [測試模式] 跳過資料庫更新")

        return True

    except smtplib.SMTPAuthenticationError:
        print(f"❌ Gmail 認證失敗 - 請檢查帳號密碼")
        return False
    except smtplib.SMTPRecipientsRefused:
        print(f"❌ 收件者被拒絕: {to_email}")
        return False
    except Exception as e:
        print(f"❌ 發送失敗給 {to_email}: {e}")
        return False

# === 主程式 ===
def main():
    print("🚀 開始執行 114-1 學期選課通知程式...")
    print(f"📅 當前日期: {datetime.now().strftime('%Y/%m/%d')}")
    
    if TEST_MODE:
        print("🧪 *** 測試模式啟用 ***")
        print("   - 會忽略已通知記錄")
        print("   - 不會更新資料庫")
        print("   - 主旨會加上 [TEST] 標記")
        print("   - 郵件內容會顯示測試標記")
        print()
    
    print("📥 從PDF提取重要日期...")
    important_dates = extract_important_dates(PDF_PATH)
    
    if not important_dates:
        print("❌ 無法從PDF中提取重要日期")
        return
    
    print(f"✅ 成功提取 {len(important_dates)} 個重要日期")
    
    # 檢查今天是否需要發送通知
    notifications_to_send = should_send_notification_today(important_dates)
    
    if not notifications_to_send and not TEST_MODE:
        print("ℹ️  今天沒有需要提醒的事件")
        return
    elif TEST_MODE:
        print("🧪 測試模式：強制生成通知內容")
        # 測試模式下，如果沒有今天的通知，就用最近的事件來測試
        if not notifications_to_send:
            today = datetime.now().date()
            nearest_event = min(important_dates.items(), 
                              key=lambda x: abs((x[1]["date"].date() - today).days))
            notifications_to_send = [{
                "event": nearest_event[0],
                "date": nearest_event[1]["date"].date(),
                "days_before": (nearest_event[1]["date"].date() - today).days,
                "original_text": nearest_event[1]["original_text"]
            }]
    
    # 生成通知內容
    content = generate_notification_content(notifications_to_send, important_dates)
    if not content:
        print("❌ 無法生成通知內容")
        return
    
    print("📧 通知內容預覽：")
    print("-" * 50)
    print(content)
    print("-" * 50)
    
    # 生成通知鍵值（用於追蹤是否已通知）
    event_names = [n["event"] for n in notifications_to_send]
    notification_key = f"{CURRENT_SEMESTER}_{'+'.join(event_names)}_{datetime.now().strftime('%Y%m%d')}"
    
    print("🔗 連接 Firestore...")
    db = init_firestore(SERVICE_ACCOUNT_JSON)
    if not db:
        print("❌ Firestore 連接失敗")
        return

    print("📋 擷取符合訂閱的使用者...")
    subscribers = get_subscribers(db, notification_key)
    
    if not subscribers:
        print("❌ 沒有找到符合條件的訂閱用戶")
        return
        
    print(f"📨 將發送通知給 {len(subscribers)} 位使用者...")
    
    success_count = 0
    for i, user in enumerate(subscribers):
        if send_email(user['email'], user['name'], content, user['ref'], notification_key):
            success_count += 1
        
        if i < len(subscribers) - 1:
            print("⏱️  等待 2 秒...")
            time.sleep(2)

    print(f"🎉 完成！成功發送 {success_count}/{len(subscribers)} 封郵件")
    if TEST_MODE:
        print("🧪 測試模式執行完畢，資料庫未被修改")

if __name__ == "__main__":
    main()