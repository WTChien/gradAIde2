# email_reply_handler.py
# 處理用戶回覆「UNSUBSCRIBE」的郵件自動取消訂閱

import imaplib
import email
import re
from email.header import decode_header
from google.cloud import firestore
from notify_course_users import send_subscription_change_notification
import time

class EmailReplyHandler:
    def __init__(self, gmail_user, gmail_password):
        self.gmail_user = gmail_user
        self.gmail_password = gmail_password
        self.db = firestore.Client()
    
    def connect_to_gmail(self):
        """連接到Gmail IMAP服務器"""
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.gmail_user, self.gmail_password)
            return mail
        except Exception as e:
            print(f"❌ Gmail連接失敗: {e}")
            return None
    
    def decode_email_subject(self, subject):
        """解碼郵件主旨"""
        try:
            decoded_parts = decode_header(subject)
            decoded_subject = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_subject += part.decode(encoding or 'utf-8')
                else:
                    decoded_subject += part
            return decoded_subject
        except:
            return subject
    
    def extract_email_content(self, msg):
        """提取郵件內容"""
        content = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        content += part.get_payload(decode=True).decode('utf-8')
                    except:
                        try:
                            content += part.get_payload(decode=True).decode('big5')
                        except:
                            content += str(part.get_payload())
        else:
            try:
                content = msg.get_payload(decode=True).decode('utf-8')
            except:
                try:
                    content = msg.get_payload(decode=True).decode('big5')
                except:
                    content = str(msg.get_payload())
        return content
    
    def process_unsubscribe_request(self, sender_email, content):
        """處理取消訂閱請求"""
        try:
            # 檢查內容是否包含取消訂閱關鍵字
            unsubscribe_keywords = ['UNSUBSCRIBE', 'unsubscribe', '取消訂閱', '退訂']
            
            if not any(keyword in content for keyword in unsubscribe_keywords):
                return False
            
            print(f"📧 處理來自 {sender_email} 的取消訂閱請求")
            
            # 查詢用戶
            users_ref = self.db.collection('Users')
            query = users_ref.where('email', '==', sender_email).limit(1)
            docs = list(query.stream())
            
            if not docs:
                print(f"⚠️  找不到用戶: {sender_email}")
                return False
            
            user_doc = docs[0]
            user_data = user_doc.to_dict()
            old_status = user_data.get('subscribe', False)
            
            if not old_status:
                print(f"ℹ️  用戶 {sender_email} 已經是未訂閱狀態")
                return True
            
            # 更新為未訂閱
            user_doc.reference.update({
                'subscribe': False,
                'last_subscription_update': time.strftime('%Y-%m-%d %H:%M:%S'),
                'unsubscribe_method': 'email_reply'
            })
            
            # 發送確認郵件
            user_name = user_data.get('username', '用戶')
            send_subscription_change_notification(
                user_email=sender_email,
                user_name=user_name,
                new_status=False,
                old_status=old_status
            )
            
            print(f"✅ 成功處理 {sender_email} 的取消訂閱請求")
            return True
            
        except Exception as e:
            print(f"❌ 處理取消訂閱請求失敗: {e}")
            return False
    
    def check_replies(self):
        """檢查並處理回覆郵件"""
        mail = self.connect_to_gmail()
        if not mail:
            return
        
        try:
            # 選擇收件匣
            mail.select('inbox')
            
            # 搜尋未讀郵件，且回覆給我們的郵件
            search_criteria = '(UNSEEN TO "gradaide2@gmail.com")'
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                print("❌ 搜尋郵件失敗")
                return
            
            message_ids = messages[0].split()
            print(f"📬 找到 {len(message_ids)} 封未讀回覆郵件")
            
            for msg_id in message_ids:
                try:
                    # 獲取郵件
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    # 解析郵件
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)
                    
                    # 獲取寄件者
                    sender = msg['From']
                    sender_email = re.findall(r'[\w\.-]+@[\w\.-]+', sender)[0] if re.findall(r'[\w\.-]+@[\w\.-]+', sender) else sender
                    
                    # 獲取主旨
                    subject = self.decode_email_subject(msg['Subject'] or '')
                    
                    # 檢查是否是回覆我們的郵件
                    if 'GradAIde' not in subject and 'gradaide' not in subject.lower():
                        continue
                    
                    # 提取郵件內容
                    content = self.extract_email_content(msg)
                    
                    print(f"📧 處理來自 {sender_email} 的郵件")
                    print(f"   主旨: {subject}")
                    print(f"   內容預覽: {content[:100]}...")
                    
                    # 處理取消訂閱請求
                    if self.process_unsubscribe_request(sender_email, content):
                        # 標記為已讀
                        mail.store(msg_id, '+FLAGS', '\\Seen')
                        print(f"✅ 郵件 {msg_id} 處理完成並標記為已讀")
                    
                except Exception as e:
                    print(f"❌ 處理郵件 {msg_id} 時發生錯誤: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ 檢查回覆郵件時發生錯誤: {e}")
        finally:
            mail.close()
            mail.logout()

def main():
    """主函數 - 可以設定為定時任務"""
    print("🔄 開始檢查郵件回覆...")
    
    # 從環境變數或設定檔讀取
    GMAIL_USER = "gradaide2@gmail.com"
    GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')  # 使用App Password
    
    if not GMAIL_PASSWORD:
        print("❌ 請設定 GMAIL_APP_PASSWORD 環境變數")
        return
    
    handler = EmailReplyHandler(GMAIL_USER, GMAIL_PASSWORD)
    handler.check_replies()
    
    print("✅ 郵件回覆檢查完成")

if __name__ == "__main__":
    import os
    main()