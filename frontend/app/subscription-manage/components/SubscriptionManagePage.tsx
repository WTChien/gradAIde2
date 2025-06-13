'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';

const SubscriptionManagePage: React.FC = () => {
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [userEmail, setUserEmail] = useState('');
  const [currentStatus, setCurrentStatus] = useState<boolean | null>(null);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error' | 'info'>('info');
  const [processing, setProcessing] = useState(false);

  // 從URL參數獲取郵箱和token
  const getUrlParams = useCallback(() => {
    return {
      email: searchParams.get('email'),
      token: searchParams.get('token')
    };
  }, [searchParams]);

  // 顯示訊息
  const showMessage = useCallback((text: string, type: 'success' | 'error' | 'info') => {
    setMessage(text);
    setMessageType(type);
    
    if (type === 'success') {
      setTimeout(() => {
        setMessage('');
        setMessageType('info');
      }, 5000);
    }
  }, []);

  // 載入用戶訂閱狀態
  const loadUserStatus = useCallback(async () => {
    const params = getUrlParams();
    
    if (!params.email) {
      showMessage('缺少必要參數，請從郵件中的連結進入。', 'error');
      setLoading(false);
      return;
    }

    setUserEmail(params.email);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/subscription-status?email=${encodeURIComponent(params.email)}&token=${params.token}`);
      
      if (!response.ok) {
        throw new Error('無法獲取訂閱狀態');
      }

      const data = await response.json();
      setCurrentStatus(data.subscribed);
      setLoading(false);

    } catch (error) {
      console.error('載入失敗:', error);
      showMessage('載入訂閱狀態失敗，請稍後再試或聯繫客服。', 'error');
      setLoading(false);
    }
  }, [getUrlParams, showMessage]);

  // 更改訂閱狀態
  const changeSubscription = useCallback(async (subscribe: boolean) => {
    const params = getUrlParams();
    
    if (!window.confirm(subscribe ? '確定要訂閱選課提醒服務嗎？' : '確定要取消訂閱選課提醒服務嗎？')) {
      return;
    }

    setProcessing(true);
    showMessage('正在處理中...', 'info');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/update-subscription`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userEmail,
          token: params.token,
          subscribe: subscribe
        })
      });

      if (!response.ok) {
        throw new Error('更新失敗');
      }

      const result = await response.json();
      
      if (result.success) {
        setCurrentStatus(subscribe);
        showMessage(
          subscribe ? '✅ 訂閱成功！您將會收到選課提醒郵件。' : '✅ 取消訂閱成功！您將不再收到選課提醒郵件。',
          'success'
        );
      } else {
        throw new Error(result.message || '更新失敗');
      }

    } catch (error) {
      console.error('更新失敗:', error);
      showMessage('操作失敗，請稍後再試或聯繫客服。', 'error');
    } finally {
      setProcessing(false);
    }
  }, [getUrlParams, userEmail, showMessage]);

  // 頁面載入時執行
  useEffect(() => {
    loadUserStatus();
  }, [loadUserStatus]);

  const styles = {
    container: {
      fontFamily: "'Microsoft JhengHei', Arial, sans-serif",
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    },
    card: {
      background: 'white',
      borderRadius: '15px',
      boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
      maxWidth: '500px',
      width: '100%',
      overflow: 'hidden'
    },
    header: {
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      padding: '30px',
      textAlign: 'center' as const
    },
    headerTitle: {
      fontSize: '24px',
      margin: '0 0 10px 0'
    },
    headerSubtitle: {
      opacity: 0.9,
      fontSize: '14px',
      margin: 0
    },
    content: {
      padding: '30px'
    },
    loading: {
      textAlign: 'center' as const,
      padding: '20px',
      color: '#666'
    },
    statusCard: {
      background: '#f8f9fa',
      borderRadius: '10px',
      padding: '20px',
      marginBottom: '25px',
      borderLeft: '4px solid #28a745'
    },
    statusCardUnsubscribed: {
      background: '#f8f9fa',
      borderRadius: '10px',
      padding: '20px',
      marginBottom: '25px',
      borderLeft: '4px solid #dc3545'
    },
    statusBadge: {
      background: '#28a745',
      color: 'white',
      padding: '5px 15px',
      borderRadius: '20px',
      fontSize: '12px',
      fontWeight: 'bold' as const,
      display: 'inline-block',
      marginBottom: '10px'
    },
    statusBadgeUnsubscribed: {
      background: '#dc3545',
      color: 'white',
      padding: '5px 15px',
      borderRadius: '20px',
      fontSize: '12px',
      fontWeight: 'bold' as const,
      display: 'inline-block',
      marginBottom: '10px'
    },
    emailInfo: {
      color: '#666',
      fontSize: '14px',
      marginBottom: '15px'
    },
    actionButtons: {
      display: 'flex',
      gap: '15px',
      marginTop: '20px'
    },
    button: {
      flex: 1,
      padding: '12px 20px',
      border: 'none',
      borderRadius: '8px',
      fontSize: '14px',
      fontWeight: 'bold' as const,
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      textDecoration: 'none',
      textAlign: 'center' as const,
      display: 'inline-block'
    },
    buttonPrimary: {
      background: '#667eea',
      color: 'white'
    },
    buttonDanger: {
      background: '#dc3545',
      color: 'white'
    },
    buttonSecondary: {
      background: '#6c757d',
      color: 'white'
    },
    buttonDisabled: {
      background: '#ccc',
      color: '#666',
      cursor: 'not-allowed'
    },
    message: {
      padding: '15px',
      borderRadius: '8px',
      marginBottom: '20px',
      border: '1px solid'
    },
    messageSuccess: {
      background: '#d4edda',
      color: '#155724',
      borderColor: '#c3e6cb'
    },
    messageError: {
      background: '#f8d7da',
      color: '#721c24',
      borderColor: '#f5c6cb'
    },
    messageInfo: {
      background: '#d1ecf1',
      color: '#0c5460',
      borderColor: '#bee5eb'
    },
    footer: {
      background: '#f8f9fa',
      padding: '20px',
      textAlign: 'center' as const,
      fontSize: '12px',
      color: '#666',
      borderTop: '1px solid #e9ecef'
    },
    footerLink: {
      color: '#667eea',
      textDecoration: 'none'
    }
  };

  const getMessageStyle = () => {
    const baseStyle = styles.message;
    switch (messageType) {
      case 'success': 
        return { ...baseStyle, ...styles.messageSuccess };
      case 'error': 
        return { ...baseStyle, ...styles.messageError };
      case 'info': 
        return { ...baseStyle, ...styles.messageInfo };
      default: 
        return baseStyle;
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
          <h1 style={styles.headerTitle}>📧 訂閱管理</h1>
          <p style={styles.headerSubtitle}>GradAIde 選課提醒服務</p>
        </div>

        <div style={styles.content}>
          {loading ? (
            <div style={styles.loading}>
              <p>正在載入您的訂閱資訊...</p>
            </div>
          ) : (
            <>
              {message && (
                <div style={getMessageStyle()}>
                  {message}
                </div>
              )}
              
              <div style={currentStatus ? styles.statusCard : styles.statusCardUnsubscribed}>
                <div style={currentStatus ? styles.statusBadge : styles.statusBadgeUnsubscribed}>
                  {currentStatus ? '已訂閱' : '未訂閱'}
                </div>
                <div style={styles.emailInfo}>
                  <strong>電子郵件：</strong>{userEmail}
                </div>
                <p>
                  {currentStatus 
                    ? '您目前已訂閱 GradAIde 選課提醒服務，我們會在重要的選課時間節點向您發送提醒郵件。'
                    : '您目前未訂閱 GradAIde 選課提醒服務。訂閱後，我們會在重要的選課時間節點向您發送提醒郵件。'
                  }
                </p>
              </div>

              <div style={styles.actionButtons}>
                {currentStatus ? (
                  <button 
                    style={{
                      ...styles.button, 
                      ...styles.buttonDanger,
                      ...(processing ? styles.buttonDisabled : {})
                    }}
                    onClick={() => changeSubscription(false)}
                    disabled={processing}
                  >
                    {processing ? '處理中...' : '🚫 取消訂閱'}
                  </button>
                ) : (
                  <button 
                    style={{
                      ...styles.button, 
                      ...styles.buttonPrimary,
                      ...(processing ? styles.buttonDisabled : {})
                    }}
                    onClick={() => changeSubscription(true)}
                    disabled={processing}
                  >
                    {processing ? '處理中...' : '📧 訂閱提醒'}
                  </button>
                )}
              </div>

              <div style={{ ...styles.actionButtons, marginTop: '10px' }}>
                <a 
                  href={process.env.NEXT_PUBLIC_API_BASE_URL || 'https://llm.gradaide.xyz'} 
                  style={{ ...styles.button, ...styles.buttonSecondary }}
                >
                  🏠 返回主站
                </a>
              </div>
            </>
          )}
        </div>

        <div style={styles.footer}>
          <p>
            如有任何問題，歡迎聯繫{' '}
            <a href="mailto:gradaide2@gmail.com" style={styles.footerLink}>
              gradaide2@gmail.com
            </a>
          </p>
          <p>© 2025 GradAIde 團隊</p>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionManagePage;