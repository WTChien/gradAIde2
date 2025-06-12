#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GradAIde 完整郵件通知模組 - 整合增強版
包含訂閱郵件發送、選課通知、系統通知等功能
整合了智能狀態分析與個性化郵件內容生成
作者: GradAIde 團隊
版本: 2.1.0
"""

import os
import sys
import time
import smtplib
import base64
import hashlib
import logging
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import traceback

# 載入環境變數
load_dotenv()

# === 郵件設定 ===
GMAIL_USER = os.getenv('GMAIL_USER', "gradaide2@gmail.com")
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', "vyvo vnvq oypr ator")
TEST_MODE = os.getenv('TEST_MODE', 'True').lower() == 'true'

# === 日誌設定 ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gradaide_notify")

# === 核心郵件發送函數 ===

def send_email(to_email: str, subject: str, html_content: str, plain_content: str = None, attachments: list = None) -> bool:
    """
    通用郵件發送函數
    
    Args:
        to_email: 收件人郵箱
        subject: 郵件主旨
        html_content: HTML 郵件內容
        plain_content: 純文字郵件內容（可選）
        attachments: 附件列表（可選）
    
    Returns:
        bool: 發送是否成功
    """
    try:
        # 測試模式標記
        test_prefix = "[TEST] " if TEST_MODE else ""
        full_subject = f"{test_prefix}{subject}"
        
        # 建立郵件
        msg = MIMEMultipart("alternative")
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = full_subject
        
        # 添加純文字版本
        if plain_content:
            msg.attach(MIMEText(plain_content, 'plain', 'utf-8'))
        else:
            # 從 HTML 生成簡化的純文字版本
            import re
            plain_text = re.sub(r'<[^>]+>', '', html_content)
            plain_text = re.sub(r'\s+', ' ', plain_text).strip()
            if TEST_MODE:
                plain_text = f"[測試郵件] {plain_text}"
            msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
        
        # 添加 HTML 版本
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # 添加附件
        if attachments:
            for attachment_path in attachments:
                if os.path.isfile(attachment_path):
                    with open(attachment_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    msg.attach(part)
        
        # 發送郵件
        logger.info(f"📧 正在發送郵件給 {to_email}...")
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ 郵件成功發送給 {to_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ Gmail 認證失敗: {e}")
        logger.error("📋 請檢查 Gmail App Password 是否正確")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"❌ 收件者被拒絕: {to_email} - {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 郵件發送失敗給 {to_email}: {e}")
        logger.error(traceback.format_exc())
        return False

def generate_unsubscribe_token(email: str) -> str:
    """生成取消訂閱 token"""
    today = datetime.now().strftime('%Y%m%d')
    token_string = f"{email}_{today}_unsubscribe"
    return base64.b64encode(hashlib.md5(token_string.encode()).digest()).decode()[:16]

def generate_unsubscribe_section(user_email: str) -> str:
    """生成取消訂閱區塊，包含網頁連結"""
    try:
        token = generate_unsubscribe_token(user_email)
        unsubscribe_url = f"https://www.gradaide.xyz/subscription-manage?email={user_email}&token={token}"
        
        return f"""
🔧 管理訂閱設定：
• 前往訂閱管理頁面：{unsubscribe_url}
• 或回覆此郵件「UNSUBSCRIBE」即可取消訂閱

如有任何問題，歡迎聯繫我們。"""
    except Exception as e:
        logger.error(f"⚠️ 生成取消訂閱連結失敗: {e}")
        return "\n🔧 如需變更訂閱設定，請登入GradAIde系統或聯繫客服。"

def generate_email_template(title: str, content: str, template_type: str = "notification", status_color: str = "#667eea", status_text: str = "", status_icon: str = "📧") -> str:
    """
    生成通用郵件 HTML 模板
    
    Args:
        title: 郵件標題
        content: 郵件內容
        template_type: 模板類型 (notification, subscription, course, system)
        status_color: 狀態顏色
        status_text: 狀態文字
        status_icon: 狀態圖標
    
    Returns:
        str: HTML 郵件內容
    """
    # 根據模板類型設定樣式
    template_configs = {
        "notification": {"bg_gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "title_icon": "📧"},
        "subscription": {"bg_gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "title_icon": "📧"},
        "course": {"bg_gradient": "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)", "title_icon": "📚"},
        "system": {"bg_gradient": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)", "title_icon": "⚙️"},
        "urgent": {"bg_gradient": "linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%)", "title_icon": "🚨"}
    }
    
    config = template_configs.get(template_type, template_configs["notification"])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{ font-family: 'Microsoft JhengHei', 'PingFang TC', 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 0; }}
            .email-container {{ max-width: 600px; margin: 0 auto; background-color: #f5f5f5; }}
            .header {{ background: {config["bg_gradient"]}; color: white; padding: 25px; text-align: center; }}
            .content {{ background: white; padding: 25px; }}
            .status-badge {{ background: {status_color}; color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; display: inline-block; margin-bottom: 15px; }}
            .content-text {{ white-space: pre-line; font-size: 16px; line-height: 1.6; color: #333; }}
            .action-button {{ background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; margin: 15px 0; }}
            .footer {{ background: #e9ecef; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
            .brand-section {{ background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; }}
            @media (max-width: 600px) {{
                .email-container {{ width: 100% !important; }}
                .header, .content {{ padding: 15px !important; }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1 style="margin: 0; font-size: 24px;">{config["title_icon"]} {title}</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 14px;">GradAIde 智慧選課助理</p>
            </div>
            
            <div class="content">
                {f'<div style="text-align: center; margin-bottom: 20px;"><span class="status-badge">{status_icon} {status_text}</span></div>' if status_text else ''}
                
                <div class="content-text">{content}</div>
                
                <div style="text-align: center; margin: 25px 0;">
                    <a href="https://www.gradaide.xyz" class="action-button">
                        🏠 返回 GradAIde
                    </a>
                    <a href="https://www.gradaide.xyz/subscription-manage" class="action-button" style="background: #28a745; margin-left: 10px;">
                        🔧 管理訂閱
                    </a>
                </div>
                
                <div class="brand-section">
                    <p style="margin: 0; font-size: 14px; color: #1976d2;">
                        <strong>📚 GradAIde - 您的智慧選課助手</strong><br>
                        讓選課變得更輕鬆，不錯過任何重要資訊！
                    </p>
                </div>
            </div>
            
            <div class="footer">
                <p style="margin: 0;">
                    此郵件由 GradAIde 自動發送，請勿直接回覆<br>
                    如有問題請聯繫客服：<a href="mailto:gradaide2@gmail.com" style="color: #667eea;">gradaide2@gmail.com</a>
                </p>
                <p style="margin: 10px 0 0 0; font-size: 11px; color: #999;">
                    © 2025 GradAIde 團隊 - 輔仁大學智慧選課助理
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# ========== 🔥 新增：智能訂閱狀態分析 ==========

def analyze_subscription_change(old_status, new_status):
    """
    分析訂閱狀態變更
    
    Args:
        old_status: 舊訂閱狀態
        new_status: 新訂閱狀態
        
    Returns:
        dict: 變更分析結果
    """
    # 標準化狀態
    old_bool = None if old_status is None else bool(old_status)
    new_bool = bool(new_status)
    
    logger.info(f"🔍 訂閱狀態分析:")
    logger.info(f"   - 原始舊狀態: {old_status} (類型: {type(old_status)})")
    logger.info(f"   - 原始新狀態: {new_status} (類型: {type(new_status)})")
    logger.info(f"   - 標準化舊狀態: {old_bool}")
    logger.info(f"   - 標準化新狀態: {new_bool}")
    
    # 無變更檢查
    if old_bool == new_bool:
        logger.info("📊 分析結果: 無變更")
        return {
            'has_change': False,
            'change_type': 'no_change',
            'should_send_email': False,
            'email_priority': 'none',
            'message_type': 'none',
            'description': '訂閱狀態沒有變更'
        }
    
    # 變更類型判斷
    if old_status is None:  # 新用戶
        if new_bool:
            logger.info("📊 分析結果: 新用戶訂閱")
            return {
                'has_change': True,
                'change_type': 'new_subscription',
                'should_send_email': True,
                'email_priority': 'high',
                'message_type': 'welcome',
                'description': '新用戶首次訂閱'
            }
        else:
            logger.info("📊 分析結果: 新用戶拒絕")
            return {
                'has_change': True,
                'change_type': 'new_decline',
                'should_send_email': True,
                'email_priority': 'low',
                'message_type': 'info',
                'description': '新用戶選擇不訂閱'
            }
    elif old_bool and not new_bool:  # 取消訂閱
        logger.info("📊 分析結果: 取消訂閱")
        return {
            'has_change': True,
            'change_type': 'unsubscribe',
            'should_send_email': True,
            'email_priority': 'medium',
            'message_type': 'farewell',
            'description': '用戶取消訂閱'
        }
    elif not old_bool and new_bool:  # 重新訂閱
        logger.info("📊 分析結果: 重新訂閱")
        return {
            'has_change': True,
            'change_type': 'resubscribe',
            'should_send_email': True,
            'email_priority': 'high',
            'message_type': 'welcome_back',
            'description': '用戶重新訂閱'
        }

def generate_subscription_email_content(change_type: str, user_name: str, user_email: str) -> dict:
    """
    根據變更類型生成對應的郵件內容
    
    Args:
        change_type: 變更類型
        user_name: 用戶名稱
        user_email: 用戶郵件
        
    Returns:
        dict: 郵件內容配置
    """
    logger.info(f"📝 生成郵件內容，變更類型: {change_type}")
    
    templates = {
        'new_subscription': {
            'subject': '🎉 歡迎訂閱 GradAIde 通知服務',
            'emoji': '🎉',
            'status_text': '新用戶訂閱',
            'status_color': '#28a745',
            'content_template': '''🎉 親愛的 {user_name} 同學您好：

歡迎訂閱 GradAIde 選課通知服務！

🌟 您將收到以下通知：
• 📚 重要選課時間提醒
• 🔄 課程異動通知
• 📢 系統重要公告
• 💡 選課技巧與建議

🚀 開始使用：
1. 登入 GradAIde 系統
2. 設定您的課程偏好
3. 開始與 AI 助理對話

我們會在重要時刻為您發送提醒，讓您不錯過任何選課機會！'''
        },
        
        'new_decline': {
            'subject': '📝 感謝您使用 GradAIde 服務',
            'emoji': '📝',
            'status_text': '暫不訂閱',
            'status_color': '#6c757d',
            'content_template': '''📝 親愛的 {user_name} 同學您好：

感謝您使用 GradAIde 選課助理！

雖然您暫時選擇不訂閱郵件通知，但您仍可以：
• 🤖 使用 AI 聊天功能
• 📚 查詢課程相關資訊
• 💡 獲得選課建議

💌 隨時歡迎您：
如果之後想要接收重要通知，可以隨時在系統中開啟郵件訂閱功能。

祝您選課順利！'''
        },
        
        'unsubscribe': {
            'subject': '😔 您已取消 GradAIde 通知服務',
            'emoji': '😔',
            'status_text': '已取消訂閱',
            'status_color': '#dc3545',
            'content_template': '''😔 親愛的 {user_name} 同學您好：

我們已為您取消郵件通知訂閱。

📋 取消詳情：
• 不再接收選課提醒郵件
• 不再接收系統公告通知
• 您仍可正常使用 GradAIde 系統功能

🤔 為什麼取消？
如果是因為郵件頻率或內容問題，歡迎提供建議讓我們改進。

💌 隨時歡迎回來：
如需重新訂閱，只要在系統設定中重新開啟即可。'''
        },
        
        'resubscribe': {
            'subject': '🔄 歡迎回來！重新訂閱成功',
            'emoji': '🔄',
            'status_text': '重新訂閱',
            'status_color': '#17a2b8',
            'content_template': '''🔄 親愛的 {user_name} 同學您好：

歡迎回來！您已成功重新訂閱 GradAIde 通知服務。

🎯 重新啟用功能：
• 📚 選課時間提醒
• 🔄 課程異動通知  
• 📢 重要系統公告
• 💡 個人化選課建議

✨ 新功能搶先看：
我們在您離開期間新增了更多實用功能，期待為您提供更好的服務！

感謝您再次信任 GradAIde！'''
        }
    }
    
    template = templates.get(change_type, templates['new_subscription'])
    
    content = {
        'subject': template['subject'],
        'content': template['content_template'].format(
            user_name=user_name,
            user_email=user_email
        ),
        'emoji': template['emoji'],
        'status_text': template['status_text'],
        'status_color': template['status_color']
    }
    
    logger.info(f"✅ 郵件內容生成完成: {content['subject']}")
    return content

# ========== 🔥 增強版訂閱通知函數 ==========

def send_subscription_change_notification_enhanced(user_email: str, user_name: str, new_status: bool, old_status: bool = None) -> dict:
    """
    增強版訂閱變更通知發送（詳細結果回傳）
    
    Args:
        user_email: 用戶郵箱
        user_name: 用戶姓名
        new_status: 新的訂閱狀態 (True/False)
        old_status: 舊的訂閱狀態 (True/False/None)
    
    Returns:
        dict: 詳細的發送結果
    """
    logger.info(f"📧 開始增強版訂閱通知處理:")
    logger.info(f"   - 收件人: {user_email}")
    logger.info(f"   - 用戶名: {user_name}")
    logger.info(f"   - 新狀態: {new_status}")
    logger.info(f"   - 舊狀態: {old_status}")
    
    try:
        # 步驟 1: 分析訂閱變更
        change_analysis = analyze_subscription_change(old_status, new_status)
        
        # 步驟 2: 檢查是否需要發送郵件
        if not change_analysis['should_send_email']:
            logger.info("ℹ️ 根據分析結果，不需要發送郵件")
            return {
                'sent': False,
                'reason': 'no_email_needed',
                'change_analysis': change_analysis,
                'error': None,
                'timestamp': datetime.now().isoformat()
            }
        
        # 步驟 3: 生成個性化郵件內容
        email_content = generate_subscription_email_content(
            change_analysis['change_type'], user_name, user_email
        )
        
        # 步驟 4: 添加退訂連結（如果是訂閱狀態）
        if new_status:
            unsubscribe_section = generate_unsubscribe_section(user_email)
            email_content['content'] += f"\n\n{unsubscribe_section}"
        
        # 步驟 5: 生成 HTML 郵件
        html_content = generate_email_template(
            title=email_content['subject'],
            content=email_content['content'],
            template_type="subscription",
            status_color=email_content['status_color'],
            status_text=email_content['status_text'],
            status_icon=email_content['emoji']
        )
        
        # 步驟 6: 發送郵件
        logger.info("📧 開始發送個性化訂閱通知...")
        success = send_email(user_email, email_content['subject'], html_content)
        
        if success:
            logger.info("✅ 增強版訂閱通知發送成功")
            return {
                'sent': True,
                'reason': 'sent_successfully',
                'change_analysis': change_analysis,
                'email_content': {
                    'subject': email_content['subject'],
                    'change_type': change_analysis['change_type']
                },
                'error': None,
                'timestamp': datetime.now().isoformat()
            }
        else:
            logger.error("❌ 增強版訂閱通知發送失敗")
            return {
                'sent': False,
                'reason': 'send_failed',
                'change_analysis': change_analysis,
                'error': 'send_email 函數返回 False',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ 增強版訂閱通知處理異常: {str(e)}")
        traceback.print_exc()
        return {
            'sent': False,
            'reason': 'exception',
            'change_analysis': {},
            'error': f'處理異常: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }

def send_subscription_change_notification(user_email: str, user_name: str, new_status: bool, old_status: bool = None) -> bool:
    """
    發送訂閱狀態變更通知（保持向後兼容）
    
    Args:
        user_email: 用戶郵箱
        user_name: 用戶姓名
        new_status: 新的訂閱狀態 (True/False)
        old_status: 舊的訂閱狀態 (True/False/None)
    
    Returns:
        bool: 發送是否成功
    """
    logger.info(f"📧 調用兼容版訂閱通知函數")
    
    try:
        # 使用增強版函數
        result = send_subscription_change_notification_enhanced(
            user_email, user_name, new_status, old_status
        )
        
        # 記錄詳細結果
        logger.info(f"📧 訂閱通知詳細結果:")
        logger.info(f"   - 發送成功: {result['sent']}")
        logger.info(f"   - 原因: {result['reason']}")
        logger.info(f"   - 變更分析: {result['change_analysis']}")
        if result['error']:
            logger.error(f"   - 錯誤: {result['error']}")
        
        # 返回簡單的布林值以保持兼容性
        return result['sent']
        
    except Exception as e:
        logger.error(f"❌ 兼容版訂閱通知發送異常: {str(e)}")
        traceback.print_exc()
        return False

# === 原有的其他郵件發送函數 ===

def send_course_notification(user_email: str, user_name: str, course_info: dict) -> bool:
    """
    發送選課通知
    
    Args:
        user_email: 用戶郵箱
        user_name: 用戶姓名
        course_info: 課程資訊字典
    
    Returns:
        bool: 發送是否成功
    """
    try:
        course_name = course_info.get('name', '未知課程')
        course_time = course_info.get('time', '未知時間')
        course_location = course_info.get('location', '未知地點')
        course_teacher = course_info.get('teacher', '未知教師')
        notification_type = course_info.get('type', 'info')  # info, warning, urgent
        
        # 根據通知類型設定樣式
        if notification_type == 'urgent':
            status_color = "#dc3545"
            status_text = "緊急通知"
            status_icon = "🚨"
            template_type = "urgent"
        elif notification_type == 'warning':
            status_color = "#ffc107"
            status_text = "重要提醒"
            status_icon = "⚠️"
            template_type = "course"
        else:
            status_color = "#17a2b8"
            status_text = "課程通知"
            status_icon = "📚"
            template_type = "course"
        
        subject = f"📚 GradAIde 選課通知 - {course_name} ({datetime.now().strftime('%Y/%m/%d')})"
        
        content = f"""📚 親愛的 {user_name} 同學您好：

關於您關注的課程有新的通知：

📋 課程資訊：
• 課程名稱：{course_name}
• 授課教師：{course_teacher}
• 上課時間：{course_time}
• 上課地點：{course_location}

📢 通知內容：
{course_info.get('message', '請查看課程詳細資訊')}

{generate_unsubscribe_section(user_email)}

祝您學習愉快！

-- GradAIde 團隊"""

        html_content = generate_email_template(
            title="GradAIde 選課通知",
            content=content,
            template_type=template_type,
            status_color=status_color,
            status_text=status_text,
            status_icon=status_icon
        )
        
        success = send_email(user_email, subject, html_content)
        
        if success:
            logger.info(f"✅ 選課通知已發送給 {user_email}")
        else:
            logger.error(f"❌ 選課通知發送失敗 {user_email}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 發送選課通知時發生錯誤: {e}")
        logger.error(traceback.format_exc())
        return False

def send_system_notification(user_email: str, user_name: str, notification_info: dict) -> bool:
    """
    發送系統通知
    
    Args:
        user_email: 用戶郵箱
        user_name: 用戶姓名
        notification_info: 通知資訊字典
    
    Returns:
        bool: 發送是否成功
    """
    try:
        notification_title = notification_info.get('title', '系統通知')
        notification_message = notification_info.get('message', '')
        notification_type = notification_info.get('type', 'info')
        notification_priority = notification_info.get('priority', 'normal')  # low, normal, high, urgent
        
        # 根據優先級設定樣式
        if notification_priority == 'urgent':
            status_color = "#dc3545"
            status_text = "緊急通知"
            status_icon = "🚨"
            template_type = "urgent"
        elif notification_priority == 'high':
            status_color = "#fd7e14"
            status_text = "重要通知"
            status_icon = "⚠️"
            template_type = "system"
        else:
            status_color = "#17a2b8"
            status_text = "系統通知"
            status_icon = "⚙️"
            template_type = "system"
        
        subject = f"⚙️ GradAIde 系統通知 - {notification_title} ({datetime.now().strftime('%Y/%m/%d')})"
        
        content = f"""⚙️ 親愛的 {user_name} 同學您好：

{notification_message}

📋 通知詳情：
• 通知標題：{notification_title}
• 通知時間：{datetime.now().strftime('%Y/%m/%d %H:%M')}
• 優先級別：{notification_priority.upper()}

{generate_unsubscribe_section(user_email)}

如有疑問，歡迎聯繫客服。

-- GradAIde 團隊"""

        html_content = generate_email_template(
            title="GradAIde 系統通知",
            content=content,
            template_type=template_type,
            status_color=status_color,
            status_text=status_text,
            status_icon=status_icon
        )
        
        success = send_email(user_email, subject, html_content)
        
        if success:
            logger.info(f"✅ 系統通知已發送給 {user_email}")
        else:
            logger.error(f"❌ 系統通知發送失敗 {user_email}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 發送系統通知時發生錯誤: {e}")
        logger.error(traceback.format_exc())
        return False

def send_welcome_email(user_email: str, user_name: str) -> bool:
    """
    發送歡迎郵件
    
    Args:
        user_email: 用戶郵箱
        user_name: 用戶姓名
    
    Returns:
        bool: 發送是否成功
    """
    try:
        subject = f"🎉 歡迎使用 GradAIde！"
        
        content = f"""🎉 親愛的 {user_name} 同學您好：

歡迎加入 GradAIde 智慧選課助理！

🌟 GradAIde 能為您提供：
• 🤖 AI 智慧選課建議
• 📚 課程資訊查詢
• ⏰ 重要時間提醒
• 📧 選課通知服務
• 📊 學習分析報告

🚀 開始使用：
1. 登入 GradAIde 系統
2. 完善您的學習偏好
3. 開始與 AI 助理對話
4. 設定您關注的課程

💡 小提示：
您可以隨時在設定中管理郵件通知偏好。

{generate_unsubscribe_section(user_email)}

祝您使用愉快！

-- GradAIde 團隊"""

        html_content = generate_email_template(
            title="歡迎使用 GradAIde",
            content=content,
            template_type="notification",
            status_color="#28a745",
            status_text="歡迎加入",
            status_icon="🎉"
        )
        
        success = send_email(user_email, subject, html_content)
        
        if success:
            logger.info(f"✅ 歡迎郵件已發送給 {user_email}")
        else:
            logger.error(f"❌ 歡迎郵件發送失敗 {user_email}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 發送歡迎郵件時發生錯誤: {e}")
        logger.error(traceback.format_exc())
        return False

def send_password_reset_email(user_email: str, user_name: str, reset_token: str) -> bool:
    """
    發送密碼重設郵件
    
    Args:
        user_email: 用戶郵箱
        user_name: 用戶姓名
        reset_token: 重設密碼的 token
    
    Returns:
        bool: 發送是否成功
    """
    try:
        reset_url = f"https://www.gradaide.xyz/reset-password?token={reset_token}&email={user_email}"
        
        subject = f"🔐 GradAIde 密碼重設請求"
        
        content = f"""🔐 親愛的 {user_name} 同學您好：

我們收到了您的密碼重設請求。

🔗 重設連結：
{reset_url}

⚠️ 安全提醒：
• 此連結有效期為 24 小時
• 請勿與他人分享此連結
• 如非本人操作，請忽略此郵件

🛡️ 為了您的帳號安全，建議：
• 使用複雜密碼（包含大小寫字母、數字、特殊符號）
• 定期更換密碼
• 不要在公共場所登入帳號

如有疑問，請聯繫客服。

-- GradAIde 團隊"""

        html_content = generate_email_template(
            title="GradAIde 密碼重設",
            content=content,
            template_type="system",
            status_color="#ffc107",
            status_text="密碼重設",
            status_icon="🔐"
        )
        
        success = send_email(user_email, subject, html_content)
        
        if success:
            logger.info(f"✅ 密碼重設郵件已發送給 {user_email}")
        else:
            logger.error(f"❌ 密碼重設郵件發送失敗 {user_email}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 發送密碼重設郵件時發生錯誤: {e}")
        logger.error(traceback.format_exc())
        return False

# === 批量郵件發送 ===

def send_bulk_notification(recipients: list, subject: str, content: str, template_type: str = "notification", delay: float = 1.0) -> dict:
    """
    批量發送通知郵件
    
    Args:
        recipients: 收件人列表 [{"email": "...", "name": "..."}, ...]
        subject: 郵件主旨
        content: 郵件內容
        template_type: 模板類型
        delay: 發送間隔（秒）
    
    Returns:
        dict: 發送結果統計
    """
    results = {
        "total": len(recipients),
        "success": 0,
        "failed": 0,
        "failed_emails": []
    }
    
    logger.info(f"📧 開始批量發送郵件給 {len(recipients)} 位用戶...")
    
    for i, recipient in enumerate(recipients, 1):
        try:
            user_email = recipient.get("email")
            user_name = recipient.get("name", "用戶")
            
            logger.info(f"📧 發送進度: {i}/{len(recipients)} - {user_email}")
            
            # 個人化內容
            personalized_content = content.replace("{name}", user_name)
            personalized_content += f"\n\n{generate_unsubscribe_section(user_email)}"
            
            html_content = generate_email_template(
                title=subject,
                content=personalized_content,
                template_type=template_type
            )
            
            success = send_email(user_email, subject, html_content)
            
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["failed_emails"].append(user_email)
            
            # 發送間隔
            if i < len(recipients):
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"❌ 批量發送郵件失敗 {recipient}: {e}")
            results["failed"] += 1
            results["failed_emails"].append(recipient.get("email", "unknown"))
    
    logger.info(f"📊 批量發送完成: 成功 {results['success']}, 失敗 {results['failed']}")
    return results

# ========== 🔥 智能批量訂閱通知 ==========

def send_bulk_subscription_notifications(subscription_changes: list, delay: float = 2.0) -> dict:
    """
    智能批量發送訂閱變更通知
    
    Args:
        subscription_changes: 訂閱變更列表 [{"email": "", "name": "", "old_status": None, "new_status": True}, ...]
        delay: 發送間隔（秒）
    
    Returns:
        dict: 批量發送結果統計
    """
    results = {
        "total": len(subscription_changes),
        "sent": 0,
        "skipped": 0,
        "failed": 0,
        "details": []
    }
    
    logger.info(f"📧 開始智能批量發送訂閱通知給 {len(subscription_changes)} 位用戶...")
    
    for i, change in enumerate(subscription_changes, 1):
        try:
            user_email = change.get("email")
            user_name = change.get("name", "用戶")
            old_status = change.get("old_status")
            new_status = change.get("new_status")
            
            logger.info(f"📧 處理進度: {i}/{len(subscription_changes)} - {user_email}")
            
            # 使用增強版函數處理
            result = send_subscription_change_notification_enhanced(
                user_email, user_name, new_status, old_status
            )
            
            # 統計結果
            if result['sent']:
                results["sent"] += 1
            elif result['reason'] == 'no_email_needed':
                results["skipped"] += 1
            else:
                results["failed"] += 1
            
            # 記錄詳細結果
            results["details"].append({
                "email": user_email,
                "result": result['reason'],
                "change_type": result.get('change_analysis', {}).get('change_type', 'unknown'),
                "sent": result['sent']
            })
            
            # 發送間隔（只在實際發送郵件時等待）
            if result['sent'] and i < len(subscription_changes):
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"❌ 批量訂閱通知處理失敗 {change}: {e}")
            results["failed"] += 1
            results["details"].append({
                "email": change.get("email", "unknown"),
                "result": "exception",
                "error": str(e),
                "sent": False
            })
    
    logger.info(f"📊 智能批量訂閱通知完成:")
    logger.info(f"   - 總數: {results['total']}")
    logger.info(f"   - 已發送: {results['sent']}")
    logger.info(f"   - 已跳過: {results['skipped']}")
    logger.info(f"   - 失敗: {results['failed']}")
    
    return results

# === 郵件模板管理 ===

def get_template_preview(template_type: str, sample_data: dict = None) -> str:
    """
    獲取郵件模板預覽
    
    Args:
        template_type: 模板類型
        sample_data: 範例資料
    
    Returns:
        str: HTML 預覽內容
    """
    if sample_data is None:
        sample_data = {
            "name": "張小明",
            "email": "test@example.com",
            "course_name": "資料結構",
            "message": "這是一則範例通知訊息。"
        }
    
    if template_type == "subscription":
        content = f"✅ 親愛的 {sample_data['name']} 同學您好：\n\n您已成功訂閱選課提醒服務。\n\n這是範例預覽內容。"
        return generate_email_template(
            title="GradAIde 訂閱通知",
            content=content,
            template_type="subscription",
            status_color="#28a745",
            status_text="已訂閱",
            status_icon="✅"
        )
    elif template_type == "course":
        content = f"📚 親愛的 {sample_data['name']} 同學您好：\n\n關於課程「{sample_data['course_name']}」有新的通知。\n\n{sample_data['message']}"
        return generate_email_template(
            title="GradAIde 選課通知",
            content=content,
            template_type="course",
            status_color="#17a2b8",
            status_text="課程通知",
            status_icon="📚"
        )
    else:
        content = f"📧 親愛的 {sample_data['name']} 同學您好：\n\n{sample_data['message']}"
        return generate_email_template(
            title="GradAIde 通知",
            content=content,
            template_type="notification"
        )

# === 郵件發送統計 ===

def get_email_statistics() -> dict:
    """
    獲取郵件發送統計（需要配合資料庫）
    
    Returns:
        dict: 統計資料
    """
    # 這裡可以連接資料庫獲取真實統計
    # 目前返回模擬資料
    return {
        "total_sent": 0,
        "success_rate": 0.0,
        "last_24h": 0,
        "last_7d": 0,
        "last_30d": 0,
        "by_type": {
            "subscription": 0,
            "course": 0,
            "system": 0,
            "welcome": 0,
            "password_reset": 0
        },
        "timestamp": datetime.now().isoformat()
    }

# ========== 🔥 新增：統計追蹤函數 ==========

def track_email_sending(email_type: str, recipient_email: str, success: bool, change_type: str = None, error_message: str = None):
    """
    追蹤郵件發送統計
    
    Args:
        email_type: 郵件類型 (subscription, course, system, etc.)
        recipient_email: 收件人郵箱（會被匿名化）
        success: 是否成功
        change_type: 變更類型（訂閱相關）
        error_message: 錯誤訊息
    """
    try:
        # 匿名化郵箱
        email_hash = hashlib.md5(recipient_email.encode()).hexdigest()[:8]
        
        # 記錄統計（這裡可以存入資料庫）
        stats = {
            'timestamp': datetime.now().isoformat(),
            'email_type': email_type,
            'change_type': change_type,
            'success': success,
            'email_hash': email_hash,
            'error_message': error_message if not success else None,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'hour': datetime.now().hour
        }
        
        logger.info(f"📊 郵件統計記錄: {email_type}, 成功={success}, 變更類型={change_type}")
        
        # 實際應用中可以存入資料庫
        # db.collection('email_statistics').add(stats)
        
    except Exception as e:
        logger.error(f"❌ 記錄郵件統計失敗: {e}")

# === 測試功能增強版 ===

class EmailTester:
    """郵件測試器類別 - 增強版"""
    
    def __init__(self):
        self.test_email = None
        self.test_name = "測試用戶"
        self.setup_test_config()
    
    def setup_test_config(self):
        """設置測試配置"""
        logger.info("🔧 設置測試配置...")
        
        # 檢查環境變數
        if not GMAIL_USER or not GMAIL_APP_PASSWORD:
            logger.error("❌ 請確保 .env 檔案中有正確的 GMAIL_USER 和 GMAIL_APP_PASSWORD")
            sys.exit(1)
        
        # 設置測試郵箱（可以設定預設值）
        self.test_email = "40273089w@gmail.com"  # 可以改成你的郵箱
        
        logger.info(f"✅ 測試配置完成:")
        logger.info(f"   📧 測試郵箱: {self.test_email}")
        logger.info(f"   👤 測試名稱: {self.test_name}")
        logger.info(f"   📤 發送郵箱: {GMAIL_USER}")
        logger.info(f"   🧪 測試模式: {'啟用' if TEST_MODE else '停用'}")

    def test_smtp_connection(self) -> bool:
        """測試SMTP連線"""
        logger.info("🧪 測試SMTP連線...")
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.quit()
            logger.info("✅ SMTP連線測試成功")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error("❌ Gmail 認證失敗")
            return False
        except Exception as e:
            logger.error(f"❌ SMTP連線測試失敗: {e}")
            return False

    def test_subscription_notification(self) -> bool:
        """測試訂閱通知"""
        logger.info("🧪 測試訂閱通知...")
        return send_subscription_change_notification(
            user_email=self.test_email,
            user_name=self.test_name,
            new_status=True,
            old_status=None
        )

    def test_enhanced_subscription_notification(self) -> bool:
        """測試增強版訂閱通知"""
        logger.info("🧪 測試增強版訂閱通知...")
        
        # 測試所有變更類型
        test_scenarios = [
            (None, True, "新用戶訂閱"),
            (None, False, "新用戶拒絕"),
            (True, False, "取消訂閱"),
            (False, True, "重新訂閱"),
            (True, True, "無變更（應跳過）")
        ]
        
        all_success = True
        for old_status, new_status, description in test_scenarios:
            logger.info(f"🔬 測試場景: {description}")
            
            result = send_subscription_change_notification_enhanced(
                user_email=self.test_email,
                user_name=self.test_name,
                new_status=new_status,
                old_status=old_status
            )
            
            logger.info(f"📊 場景結果: {result}")
            
            # 只有無變更的情況應該跳過發送
            if old_status == new_status:
                success = not result['sent'] and result['reason'] == 'no_email_needed'
            else:
                success = result['sent']
            
            if not success:
                all_success = False
                logger.error(f"❌ 場景 {description} 測試失敗")
            else:
                logger.info(f"✅ 場景 {description} 測試成功")
            
            # 測試間隔
            time.sleep(2)
        
        return all_success

    def test_course_notification(self) -> bool:
        """測試選課通知"""
        logger.info("🧪 測試選課通知...")
        course_info = {
            "name": "資料結構",
            "teacher": "王教授",
            "time": "週一 09:00-12:00",
            "location": "資訊大樓 R101",
            "message": "本課程將於下週一開始上課，請同學準時出席。",
            "type": "info"
        }
        return send_course_notification(self.test_email, self.test_name, course_info)

    def test_system_notification(self) -> bool:
        """測試系統通知"""
        logger.info("🧪 測試系統通知...")
        notification_info = {
            "title": "系統維護通知",
            "message": "系統將於今晚 23:00-01:00 進行維護，期間可能無法正常使用。",
            "type": "system",
            "priority": "high"
        }
        return send_system_notification(self.test_email, self.test_name, notification_info)

    def test_welcome_email(self) -> bool:
        """測試歡迎郵件"""
        logger.info("🧪 測試歡迎郵件...")
        return send_welcome_email(self.test_email, self.test_name)

    def test_password_reset_email(self) -> bool:
        """測試密碼重設郵件"""
        logger.info("🧪 測試密碼重設郵件...")
        reset_token = "test_token_123456"
        return send_password_reset_email(self.test_email, self.test_name, reset_token)

    def test_bulk_notification(self) -> bool:
        """測試批量通知"""
        logger.info("🧪 測試批量通知...")
        recipients = [
            {"email": self.test_email, "name": self.test_name},
            {"email": self.test_email, "name": "測試用戶2"}  # 同一個郵箱測試
        ]
        
        results = send_bulk_notification(
            recipients=recipients,
            subject="批量測試通知",
            content="這是一則批量測試通知，收件人：{name}",
            template_type="notification",
            delay=2.0
        )
        
        logger.info(f"📊 批量測試結果: {results}")
        return results["success"] > 0

    def test_bulk_subscription_notifications(self) -> bool:
        """測試智能批量訂閱通知"""
        logger.info("🧪 測試智能批量訂閱通知...")
        
        subscription_changes = [
            {
                "email": self.test_email,
                "name": self.test_name,
                "old_status": None,
                "new_status": True
            },
            {
                "email": self.test_email,
                "name": "測試用戶2",
                "old_status": True,
                "new_status": False
            },
            {
                "email": self.test_email,
                "name": "測試用戶3",
                "old_status": True,
                "new_status": True  # 應該被跳過
            }
        ]
        
        results = send_bulk_subscription_notifications(subscription_changes, delay=2.0)
        
        logger.info(f"📊 智能批量訂閱通知結果: {results}")
        return results["sent"] > 0 or results["skipped"] > 0

    def test_subscription_analysis(self) -> bool:
        """測試訂閱狀態分析"""
        logger.info("🧪 測試訂閱狀態分析...")
        
        test_cases = [
            (None, True, True),    # 新用戶訂閱，應該發送
            (None, False, True),   # 新用戶拒絕，應該發送
            (True, False, True),   # 取消訂閱，應該發送
            (False, True, True),   # 重新訂閱，應該發送
            (True, True, False),   # 無變更，不應該發送
            (False, False, False)  # 無變更，不應該發送
        ]
        
        all_correct = True
        for old_status, new_status, should_send in test_cases:
            analysis = analyze_subscription_change(old_status, new_status)
            actual_should_send = analysis['should_send_email']
            
            if actual_should_send == should_send:
                logger.info(f"✅ 分析正確: {old_status} -> {new_status}, 應發送={should_send}")
            else:
                logger.error(f"❌ 分析錯誤: {old_status} -> {new_status}, 預期={should_send}, 實際={actual_should_send}")
                all_correct = False
        
        return all_correct

    def run_comprehensive_test(self) -> bool:
        """執行完整測試"""
        logger.info("🚀 開始執行郵件系統完整測試（增強版）...")
        logger.info("=" * 60)
        
        test_results = []
        
        # 測試清單
        tests = [
            ("SMTP連線測試", self.test_smtp_connection),
            ("訂閱狀態分析測試", self.test_subscription_analysis),
            ("增強版訂閱通知測試", self.test_enhanced_subscription_notification),
            ("兼容版訂閱通知測試", self.test_subscription_notification),
            ("選課通知測試", self.test_course_notification),
            ("系統通知測試", self.test_system_notification),
            ("歡迎郵件測試", self.test_welcome_email),
            ("密碼重設郵件測試", self.test_password_reset_email),
            ("批量通知測試", self.test_bulk_notification),
            ("智能批量訂閱通知測試", self.test_bulk_subscription_notifications)
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n📧 執行: {test_name}")
                result = test_func()
                test_results.append((test_name, result))
                
                if result:
                    logger.info(f"✅ {test_name} - 成功")
                else:
                    logger.error(f"❌ {test_name} - 失敗")
                
                # 測試間隔
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ {test_name} - 錯誤: {e}")
                test_results.append((test_name, False))
        
        # 結果統計
        logger.info("\n" + "=" * 60)
        logger.info("📊 測試結果統計:")
        logger.info("=" * 60)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通過" if result else "❌ 失敗"
            logger.info(f"{status} - {test_name}")
        
        logger.info(f"\n🎯 總計: {passed}/{total} 項測試通過")
        
        if passed == total:
            logger.info("🎉 所有測試都通過了！郵件系統運作正常")
        else:
            logger.warning("⚠️ 部分測試失敗，請檢查配置")
        
        return passed == total

# === 工具函數 ===

def validate_email_format(email: str) -> bool:
    """驗證郵箱格式"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def check_email_environment() -> bool:
    """檢查郵件環境設定"""
    logger.info("🔍 檢查郵件環境設定...")
    
    issues = []
    
    if not GMAIL_USER:
        issues.append("缺少 GMAIL_USER 設定")
    elif not validate_email_format(GMAIL_USER):
        issues.append("GMAIL_USER 格式不正確")
    
    if not GMAIL_APP_PASSWORD:
        issues.append("缺少 GMAIL_APP_PASSWORD 設定")
    elif len(GMAIL_APP_PASSWORD) < 16:
        issues.append("GMAIL_APP_PASSWORD 長度可能不正確")
    
    if not os.path.exists('.env'):
        issues.append("找不到 .env 檔案")
    
    if issues:
        logger.error("❌ 發現以下問題:")
        for issue in issues:
            logger.error(f"   • {issue}")
        return False
    else:
        logger.info("✅ 郵件環境設定檢查通過")
        return True

def generate_test_data() -> dict:
    """生成測試資料"""
    return {
        "user_email": "test@example.com",
        "user_name": "測試用戶",
        "course_info": {
            "name": "測試課程",
            "teacher": "測試教師",
            "time": "週一 09:00-12:00",
            "location": "測試教室",
            "message": "這是測試訊息",
            "type": "info"
        },
        "notification_info": {
            "title": "測試通知",
            "message": "這是測試系統通知",
            "type": "system",
            "priority": "normal"
        }
    }

# === API 整合函數 ===

def notify_user(user_email: str, user_name: str, notification_type: str, data: dict) -> bool:
    """
    統一的用戶通知接口
    
    Args:
        user_email: 用戶郵箱
        user_name: 用戶姓名
        notification_type: 通知類型 (subscription, course, system, welcome, password_reset)
        data: 通知資料
    
    Returns:
        bool: 發送是否成功
    """
    try:
        if notification_type == "subscription":
            return send_subscription_change_notification(
                user_email, user_name, 
                data.get("new_status"), 
                data.get("old_status")
            )
        elif notification_type == "course":
            return send_course_notification(user_email, user_name, data)
        elif notification_type == "system":
            return send_system_notification(user_email, user_name, data)
        elif notification_type == "welcome":
            return send_welcome_email(user_email, user_name)
        elif notification_type == "password_reset":
            return send_password_reset_email(
                user_email, user_name, 
                data.get("reset_token")
            )
        else:
            logger.error(f"❌ 未知的通知類型: {notification_type}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 通知發送失敗: {e}")
        return False

def notify_user_enhanced(user_email: str, user_name: str, notification_type: str, data: dict) -> dict:
    """
    增強版統一用戶通知接口（返回詳細結果）
    
    Args:
        user_email: 用戶郵箱
        user_name: 用戶姓名
        notification_type: 通知類型 (subscription, course, system, welcome, password_reset)
        data: 通知資料
    
    Returns:
        dict: 詳細的發送結果
    """
    try:
        if notification_type == "subscription":
            return send_subscription_change_notification_enhanced(
                user_email, user_name, 
                data.get("new_status"), 
                data.get("old_status")
            )
        else:
            # 其他類型使用舊函數並包裝結果
            if notification_type == "course":
                success = send_course_notification(user_email, user_name, data)
            elif notification_type == "system":
                success = send_system_notification(user_email, user_name, data)
            elif notification_type == "welcome":
                success = send_welcome_email(user_email, user_name)
            elif notification_type == "password_reset":
                success = send_password_reset_email(
                    user_email, user_name, data.get("reset_token")
                )
            else:
                return {
                    'sent': False,
                    'reason': 'unknown_type',
                    'error': f'未知的通知類型: {notification_type}',
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'sent': success,
                'reason': 'sent_successfully' if success else 'send_failed',
                'notification_type': notification_type,
                'error': None if success else 'send_email 函數返回 False',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ 增強版通知發送失敗: {e}")
        return {
            'sent': False,
            'reason': 'exception',
            'error': f'處理異常: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }

# ========== 🔥 新增：郵件內容分析工具 ==========

def analyze_email_content(content: str) -> dict:
    """
    分析郵件內容的特徵
    
    Args:
        content: 郵件內容
        
    Returns:
        dict: 內容分析結果
    """
    try:
        import re
        
        # 基本統計
        word_count = len(content.split())
        char_count = len(content)
        line_count = len(content.split('\n'))
        
        # 檢查是否包含特定元素
        has_emoji = bool(re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content))
        has_links = bool(re.search(r'https?://[^\s]+', content))
        has_unsubscribe = '取消訂閱' in content or 'unsubscribe' in content.lower()
        
        # 情感傾向簡單分析
        positive_words = ['歡迎', '恭喜', '成功', '感謝', '很高興', '棒', '好', '優秀']
        negative_words = ['抱歉', '失敗', '錯誤', '問題', '取消', '失望']
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'word_count': word_count,
            'char_count': char_count,
            'line_count': line_count,
            'has_emoji': has_emoji,
            'has_links': has_links,
            'has_unsubscribe': has_unsubscribe,
            'sentiment': sentiment,
            'positive_score': positive_count,
            'negative_score': negative_count,
            'readability': 'easy' if word_count < 100 else 'medium' if word_count < 200 else 'complex'
        }
        
    except Exception as e:
        logger.error(f"❌ 郵件內容分析失敗: {e}")
        return {'error': str(e)}

# === 命令行介面增強版 ===

def show_help():
    """顯示使用說明"""
    print("📧 GradAIde 完整郵件通知系統 - 整合增強版")
    print("=" * 60)
    print()
    print("📋 主要功能:")
    print("  • 智能訂閱狀態分析")
    print("  • 個性化郵件內容生成")
    print("  • 增強版訂閱變更通知")
    print("  • 選課相關通知")
    print("  • 系統公告通知")
    print("  • 歡迎郵件")
    print("  • 密碼重設郵件")
    print("  • 批量郵件發送")
    print("  • 智能批量訂閱通知")
    print("  • 郵件內容分析")
    print("  • 發送統計追蹤")
    print()
    print("🧪 測試命令:")
    print("  python notify_course_users.py test          # 完整測試（包含增強功能）")
    print("  python notify_course_users.py smtp          # SMTP連線測試")
    print("  python notify_course_users.py subscription  # 兼容版訂閱通知測試")
    print("  python notify_course_users.py enhanced      # 增強版訂閱通知測試")
    print("  python notify_course_users.py analysis      # 訂閱狀態分析測試")
    print("  python notify_course_users.py course        # 選課通知測試")
    print("  python notify_course_users.py system        # 系統通知測試")
    print("  python notify_course_users.py welcome       # 歡迎郵件測試")
    print("  python notify_course_users.py password      # 密碼重設測試")
    print("  python notify_course_users.py bulk          # 批量發送測試")
    print("  python notify_course_users.py bulk_sub      # 智能批量訂閱通知測試")
    print()
    print("🔧 工具命令:")
    print("  python notify_course_users.py check         # 檢查環境設定")
    print("  python notify_course_users.py preview       # 預覽郵件模板")
    print("  python notify_course_users.py stats         # 查看發送統計")
    print("  python notify_course_users.py content       # 分析郵件內容")
    print()
    print("⚙️ 環境設定:")
    print("  確保 .env 檔案包含:")
    print("    GMAIL_USER=your_email@gmail.com")
    print("    GMAIL_APP_PASSWORD=your_app_password")
    print("    TEST_MODE=True")
    print()
    print("🎯 v2.1.0 新功能:")
    print("  • analyze_subscription_change() - 智能狀態分析")
    print("  • generate_subscription_email_content() - 個性化內容生成")
    print("  • send_subscription_change_notification_enhanced() - 增強版通知")
    print("  • send_bulk_subscription_notifications() - 智能批量通知")
    print("  • analyze_email_content() - 內容分析工具")
    print("  • notify_user_enhanced() - 增強版統一接口")

def main():
    """主函數"""
    print("📧 GradAIde 完整郵件通知系統 v2.1.0 - 整合增強版")
    print("=" * 60)
    
    # 檢查命令行參數
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ['-h', '--help', 'help']:
            show_help()
            return 0
        elif command == 'check':
            return 0 if check_email_environment() else 1
        elif command == 'preview':
            # 預覽郵件模板
            template_types = ['subscription', 'course', 'system']
            for template_type in template_types:
                print(f"\n🎨 預覽 {template_type} 模板...")
                html = get_template_preview(template_type)
                filename = f"preview_{template_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"💾 模板已保存: {filename}")
            return 0
        elif command == 'stats':
            # 查看統計
            stats = get_email_statistics()
            print(f"\n📊 郵件發送統計:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
            return 0
        elif command == 'content':
            # 分析郵件內容
            sample_content = """🎉 親愛的張同學您好：

歡迎訂閱 GradAIde 選課通知服務！

🌟 您將收到以下通知：
• 📚 重要選課時間提醒
• 🔄 課程異動通知

感謝您的使用！

如需取消訂閱，請點擊 https://www.gradaide.xyz/unsubscribe"""
            
            analysis = analyze_email_content(sample_content)
            print(f"\n📊 郵件內容分析結果:")
            for key, value in analysis.items():
                print(f"   {key}: {value}")
            return 0
        elif command in ['test', 'smtp', 'subscription', 'enhanced', 'analysis', 'course', 'system', 'welcome', 'password', 'bulk', 'bulk_sub']:
            # 執行測試
            if not check_email_environment():
                return 1
            
            tester = EmailTester()
            
            if command == 'test':
                success = tester.run_comprehensive_test()
            elif command == 'smtp':
                success = tester.test_smtp_connection()
            elif command == 'subscription':
                success = tester.test_subscription_notification()
            elif command == 'enhanced':
                success = tester.test_enhanced_subscription_notification()
            elif command == 'analysis':
                success = tester.test_subscription_analysis()
            elif command == 'course':
                success = tester.test_course_notification()
            elif command == 'system':
                success = tester.test_system_notification()
            elif command == 'welcome':
                success = tester.test_welcome_email()
            elif command == 'password':
                success = tester.test_password_reset_email()
            elif command == 'bulk':
                success = tester.test_bulk_notification()
            elif command == 'bulk_sub':
                success = tester.test_bulk_subscription_notifications()
            
            return 0 if success else 1
        else:
            print(f"❌ 未知命令: {command}")
            show_help()
            return 1
    else:
        # 交互式模式
        show_help()
        print("\n請使用上述命令來測試或使用郵件系統")
        return 0

# === 模組導出 ===

__all__ = [
    # 核心郵件發送
    'send_email',
    'generate_email_template',
    'generate_unsubscribe_section',
    'generate_unsubscribe_token',
    
    # 訂閱相關（增強版）
    'analyze_subscription_change',
    'generate_subscription_email_content',
    'send_subscription_change_notification',
    'send_subscription_change_notification_enhanced',
    
    # 其他類型郵件
    'send_course_notification', 
    'send_system_notification',
    'send_welcome_email',
    'send_password_reset_email',
    
    # 批量發送
    'send_bulk_notification',
    'send_bulk_subscription_notifications',
    
    # 統一接口
    'notify_user',
    'notify_user_enhanced',
    
    # 工具函數
    'get_template_preview',
    'get_email_statistics',
    'validate_email_format',
    'check_email_environment',
    'track_email_sending',
    'analyze_email_content',
    'generate_test_data',
    
    # 測試類別
    'EmailTester'
]

# ========== 版本信息 ==========

def get_version_info():
    """獲取版本信息"""
    return {
        "version": "2.1.0",
        "title": "GradAIde 完整郵件通知模組 - 整合增強版",
        "description": "整合了智能狀態分析與個性化郵件內容生成的完整郵件通知系統",
        "features": [
            "智能訂閱狀態分析",
            "個性化郵件內容生成",
            "增強版訂閱變更通知",
            "智能批量訂閱通知",
            "郵件內容分析工具",
            "發送統計追蹤",
            "增強版統一接口",
            "完整的測試覆蓋"
        ],
        "new_in_v2_1": [
            "analyze_subscription_change() - 避免無意義郵件發送",
            "generate_subscription_email_content() - 根據場景生成個性化內容",
            "send_subscription_change_notification_enhanced() - 詳細結果回傳",
            "send_bulk_subscription_notifications() - 智能批量處理",
            "analyze_email_content() - 內容特徵分析",
            "notify_user_enhanced() - 統一增強接口",
            "track_email_sending() - 統計追蹤",
            "EmailTester 增強版測試套件"
        ],
        "compatibility": "向後兼容 v2.0.0，保持原有函數接口不變",
        "author": "GradAIde 團隊",
        "last_updated": "2025-06-09",
        "python_version": "3.8+",
        "dependencies": [
            "smtplib (內建)",
            "email (內建)", 
            "dotenv",
            "hashlib (內建)",
            "base64 (內建)",
            "datetime (內建)",
            "logging (內建)"
        ]
    }

if __name__ == "__main__":
    try:
        # 顯示版本信息
        version_info = get_version_info()
        print(f"📧 {version_info['title']}")
        print(f"🏷️ 版本: {version_info['version']}")
        print(f"📝 描述: {version_info['description']}")
        print()
        
        # 執行主程序
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ 程式被用戶中斷")
        exit(1)
    except Exception as e:
        print(f"\n❌ 程式執行失敗: {e}")
        logger.error(traceback.format_exc())
        exit(1)