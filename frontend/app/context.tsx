"use client";
import React, { useState, useEffect, useRef, useCallback } from 'react';
import './style.css';
import Image from 'next/image';
import { Modal } from 'react-bootstrap';

interface Message {
  type: string;
  content: string;
  isStreaming?: boolean;
  recommendedQuestions?: string[];
  processingStage?: string;
  startTime?: number;
  isError?: boolean;
  isCancelled?: boolean;
}

interface UserData {
  subscribe?: boolean | null;
  admission_year?: string;
  department_code?: string;
  department_name?: string;
  email?: string;
  last_notified?: string;
  notified_semesters?: string[] | null;
  password?: string;
  role?: string;
  student_id?: string;
  study_type?: string;
  username?: string;
  [key: string]: string | boolean | string[] | null | undefined;
}

// 🔥 簡化版訂閱彈窗組件 - 移除郵件發送功能
const SubscriptionModal = ({ 
  isOpen, 
  onSubscribe, 
  onDecline,
  onClose,
  currentStatus,
  userName,
  userEmail,
  isLoading
}: { 
  isOpen: boolean; 
  onSubscribe: () => void; 
  onDecline: () => void; 
  onClose: () => void;
  currentStatus?: boolean | null;
  userName?: string;
  userEmail?: string;
  isLoading?: boolean;
}) => {
  
  // 根據當前狀態決定顯示內容
  const getModalContent = () => {
    if (isLoading) {
      return {
        title: "載入中...",
        description: "正在載入您的訂閱狀態...",
        primaryButton: "載入中",
        secondaryButton: "關閉",
        primaryDisabled: true
      };
    }

    if (currentStatus === null || currentStatus === undefined) {
      // 新用戶或未設定狀態
      return {
        title: "選課提醒服務",
        description: `${userName ? `親愛的 ${userName}，` : ''}是否要訂閱選課提醒服務？訂閱後您的帳號將被標記為接收提醒狀態，可以在系統內管理您的訂閱偏好。`,
        primaryButton: "立即訂閱",
        secondaryButton: "暫不訂閱",
        primaryDisabled: false
      };
    } else if (currentStatus === true) {
      // 已訂閱狀態
      return {
        title: "訂閱管理",
        description: `您目前已訂閱選課提醒服務。您的帳號已標記為接收提醒狀態。是否要取消訂閱？`,
        primaryButton: "取消訂閱",
        secondaryButton: "保持訂閱",
        primaryDisabled: false
      };
    } else {
      // 未訂閱狀態
      return {
        title: "訂閱管理", 
        description: `您目前未訂閱選課提醒服務。是否要重新訂閱以接收重要的選課時間提醒？`,
        primaryButton: "重新訂閱",
        secondaryButton: "保持現狀",
        primaryDisabled: false
      };
    }
  };

  const modalContent = getModalContent();
  
  return (
    <>
      {isOpen && (
        <div className="modal-backdrop"></div>
      )}
      <Modal show={isOpen} onHide={onClose} dialogClassName="custom-modal">
        <div className="modal-header" style={{paddingLeft:"20px",paddingRight:"20px"}}>
          <h1 className='modalfont'>{modalContent.title}</h1>
          {/* 顯示當前訂閱狀態徽章 */}
          {currentStatus !== null && currentStatus !== undefined && !isLoading && (
            <div style={{
              marginLeft: 'auto',
              marginRight: '10px',
              display: 'flex',
              alignItems: 'center'
            }}>
              <span style={{
                background: currentStatus ? '#28a745' : '#dc3545',
                color: 'white',
                padding: '4px 12px',
                borderRadius: '15px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {currentStatus ? '已訂閱' : '未訂閱'}
              </span>
            </div>
          )}
          <button className="close-button" onClick={onClose}>
            &times;
          </button>
        </div>
        
        <div className="modal-content" style={{paddingLeft:"20px",paddingRight:"20px"}}>
          <p className="subscription-modal-description" style={{fontSize:'16px'}}>
            {modalContent.description}
          </p>
          
          {/* 顯示用戶資訊 */}
          {(userName || userEmail) && (
            <div style={{
              background: '#f8f9fa',
              padding: '12px',
              borderRadius: '8px',
              margin: '15px 0',
              fontSize: '14px',
              color: '#666'
            }}>
              {userName && <div><strong>用戶：</strong>{userName}</div>}
              {userEmail && <div><strong>郵箱：</strong>{userEmail}</div>}
            </div>
          )}

        </div>
        
        <div className="modal-footer">
          <button 
            className="subscription-btn subscription-btn-secondary confirm-button"
            onClick={onDecline}
            style={{marginRight:'10px'}}
            disabled={isLoading}
          >
            <b>{modalContent.secondaryButton}</b>
          </button>
          <button 
            className="subscription-btn subscription-btn-primary confirm-button"
            onClick={onSubscribe}
            disabled={modalContent.primaryDisabled}
            style={{
              opacity: modalContent.primaryDisabled ? 0.5 : 1,
              cursor: modalContent.primaryDisabled ? 'not-allowed' : 'pointer'
            }}
          >
            <b>{modalContent.primaryButton}</b>
          </button>
        </div>
      </Modal>
    </>
  );
};

// 迎賓畫面組件
const WelcomeScreen = ({
  onQuestionClick,
  isLoggedIn,
  currentUserData
}: {
  onQuestionClick: (question: string) => void;
  isLoggedIn: boolean;
  currentUserData?: UserData | null;
}) => {

  const welcomeQuestions = [
    "請問葉承達教授辦公室的位置和email？",
    "生死學這門課程的評價如何？",
    "有推薦的課嗎？",
    "這學期有沒有這時間的自然通識課？"
  ];

  const isDevelopment = typeof window !== 'undefined' && 
                     (process.env.NODE_ENV === 'development' || 
                      window.location.hostname === 'localhost' ||
                      window.location.hostname.includes('localhost'));
  
  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        {/* AI 助理頭像和歡迎訊息 */}
        <div className="welcome-avatar">
          <Image 
            src="/img/logo.png" 
            alt="AI助理" 
            width={64} 
            height={64}
            className="welcome-logo"
          />
        </div>
        
        <div className="welcome-message">
          <h2 className="welcome-title">歡迎使用 GradAIde！</h2>
          <p className="welcome-subtitle">
            我是你的專屬學習助理，可以幫你解答課程相關問題、
            <br />
            提供選課建議，讓你的學習之路更加順利！
          </p>
        </div>

        {/* 快速開始問題 */}
        <div className="welcome-suggestions">
          <h3 className="suggestions-title">你可以這樣開始：</h3>
          <div className="suggestions-grid">
            {welcomeQuestions.map((question, index) => (
              <button
                key={index}
                className="suggestion-btn"
                onClick={() => onQuestionClick(question)}
              >
                <span className="suggestion-text">{question}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 功能介紹 */}
        <div className="welcome-features">
          <div className="feature-item">
            <span className="feature-icon">📚</span>
            <span className="feature-text">課程推薦</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">⏰</span>
            <span className="feature-text">時間安排</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🎯</span>
            <span className="feature-text">選課策略</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">📝</span>
            <span className="feature-text">學習規劃</span>
          </div>
        </div>

        {/* 開發模式下的測試按鈕 */}
        {isLoggedIn && isDevelopment && (
          <div style={{ 
            marginTop: '20px', 
            textAlign: 'center',
            padding: '15px',
            background: '#f0f0f0',
            borderRadius: '8px',
            border: '1px dashed #ccc'
          }}>
            <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#666' }}>
              🛠️ 開發測試工具
            </h4>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <button 
                onClick={() => {
                  if (typeof window !== 'undefined') {
                    window.dispatchEvent(new CustomEvent('showTestModal'));
                  }
                }}
                style={{
                  padding: '6px 12px',
                  background: '#6366f1',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                測試訂閱彈窗
              </button>
              <button 
                onClick={() => {
                  if (typeof window !== 'undefined') {
                    console.log('🔍 當前用戶狀態:', currentUserData);
                    console.log('🔍 localStorage token:', localStorage.getItem('token') ? '存在' : '不存在');
                    console.log('🔍 localStorage account:', localStorage.getItem('account'));
                  }
                }}
                style={{
                  padding: '6px 12px',
                  background: '#f59e0b',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                檢查狀態
              </button>
            </div>
          </div>
        )}
        
        {/* 生產環境下的簡單按鈕 */}
        {isLoggedIn && !isDevelopment && (
          <div style={{ marginTop: '20px', textAlign: 'center' }}>
            <button 
              onClick={() => {
                if (typeof window !== 'undefined') {
                  window.dispatchEvent(new CustomEvent('showTestModal'));
                }
              }}
              style={{
                padding: '8px 16px',
                background: '#6366f1',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '12px',
                cursor: 'pointer',
                opacity: 0.7
              }}
            >
              管理訂閱設定
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default function ContextArea() {         
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const [enlargedImage, setEnlargedImage] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    
    // 狀態管理
    const [currentUserData, setCurrentUserData] = useState<UserData | null>(null);

    useEffect(() => {
      if (typeof window !== 'undefined') {
        const account = localStorage.getItem('account');
        if (account) {
          setIsLoggedIn(true);
        }
      }
    }, []);

    useEffect(() => {
      const setVh = () => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
      };
      setVh();
      window.addEventListener('resize', setVh);
      return () => window.removeEventListener('resize', setVh);
    }, []);

    // 獲取用戶資料函數
    const getUserData = async (): Promise<UserData | null> => {
      try {
        if (typeof window === 'undefined') return null;
        
        const account = localStorage.getItem('account');
        if (!account) return null;

        console.log('嘗試獲取用戶資料 for account:', account);

        const response = await fetch(`https://llm.gradaide.xyz/get_user_profile/${account}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (response.ok) {
          const userData: UserData = await response.json();
          console.log('成功獲取用戶資料:', userData);
          return userData;
        } else {
          console.log('API 回應錯誤:', response.status);
          throw new Error(`API 錯誤: ${response.status}`);
        }
      } catch (error) {
        console.error('API 調用失敗:', error);
        
        // 如果 API 連接失敗，返回模擬資料進行測試
        if (typeof window !== 'undefined') {
          const account = localStorage.getItem('account');
          if (account) {
            console.log('使用模擬資料進行測試');
            return {
              subscribe: null,
              email: account,
              username: 'Test User'
            };
          }
        }
        
        return null;
      }
    };

    // 🔥 簡化版 updateSubscriptionStatus 函數 - 移除郵件發送功能
    const updateSubscriptionStatus = async (status: boolean): Promise<void> => {
      try {
        if (typeof window === 'undefined') {
          throw new Error('此功能僅在客戶端可用');
        }
        
        const account = localStorage.getItem('account');
        const token = localStorage.getItem('token');
        
        if (!account || !token) {
          throw new Error('用戶未登入');
        }
        
        console.log(`🔄 開始更新訂閱狀態:`);
        console.log(`   - Account: ${account}`);
        console.log(`   - Status: ${status}`);
        console.log(`   - Token: ${token ? '存在' : '不存在'}`);
        
        // 🔥 簡化的請求格式，移除郵件通知參數
        const requestBody = { 
          account: account,
          subscribe: status
        };
        
        console.log(`📤 請求數據:`, requestBody);
        
        const response = await fetch(`https://llm.gradaide.xyz/update_subscription`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(requestBody)
        });
        
        console.log(`📥 HTTP 響應:`);
        console.log(`   - Status: ${response.status}`);
        console.log(`   - OK: ${response.ok}`);
        
        const result = await response.json();
        console.log(`📧 API 詳細回應:`, result);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${result.detail || result.message || 'Unknown error'}`);
        }
        
        // 🔥 簡化的成功提示，不涉及郵件發送
        console.log(`✅ 訂閱狀態更新成功！`);
        console.log(`   - 舊狀態: ${result.old_status}`);
        console.log(`   - 新狀態: ${result.new_status}`);
        console.log(`   - 用戶: ${result.user_name} (${result.user_email})`);
        
        // 顯示簡潔的成功提示
        alert(`✅ 訂閱狀態已更新為：${status ? '已訂閱' : '未訂閱'}`);
        
      } catch (error) {
        console.error('❌ 更新訂閱狀態失敗:', error);
        
        // 詳細的錯誤處理
        const errorMessage = error instanceof Error ? error.message : String(error);
        
        if (error instanceof TypeError && errorMessage.includes('fetch')) {
          alert('❌ 網路連接錯誤，請檢查網路連接');
        } else if (errorMessage.includes('401')) {
          alert('❌ 認證失敗，請重新登入');
        } else if (errorMessage.includes('404')) {
          alert('❌ 找不到用戶，請聯繫客服');
        } else {
          alert(`❌ 操作失敗：${errorMessage}`);
        }
        
        throw error;
      }
    };

    // 檢查用戶登入狀態和訂閱狀態
    useEffect(() => {
      const checkSubscriptionStatus = async () => {
        try {
          if (typeof window === 'undefined') return;
          
          const token = localStorage.getItem('token');
          const account = localStorage.getItem('account');
          
          console.log('檢查登入狀態:', { token: !!token, account });
          
          if (token && account) {
            try {
              const userData = await getUserData();
              console.log('獲取到的用戶資料:', userData);
              
              if (userData) {
                setCurrentUserData(userData);
                
                // 如果subscribe欄位為空值、null、undefined，顯示彈窗
                if (userData.subscribe === null || userData.subscribe === undefined) {
                  console.log('用戶 subscribe 為空值，顯示訂閱彈窗');
                  setShowSubscriptionModal(true);
                } else {
                  console.log('用戶已有訂閱設定:', userData.subscribe);
                }
              }
            } catch (error) {
              console.error('獲取用戶資料失敗:', error);
              // 設定模擬資料以便測試
              setCurrentUserData({
                subscribe: null,
                email: account,
                username: '測試用戶'
              });
              setShowSubscriptionModal(true);
            }
          } else {
            console.log('用戶未登入');
          }
        } catch (error) {
          console.error('檢查訂閱狀態失敗:', error);
        }
      };

      const timer = setTimeout(checkSubscriptionStatus, 1000);
      
      // 測試事件監聽器
      const handleTestModal = async () => {
        console.log('測試彈窗被觸發');
        
        try {
          // 重新獲取用戶資料以顯示最新狀態
          const userData = await getUserData();
          if (userData) {
            setCurrentUserData(userData);
          }
        } catch (error) {
          console.error('獲取用戶資料失敗:', error);
        } finally {
          setShowSubscriptionModal(true);
        }
      };
      
      if (typeof window !== 'undefined') {
        window.addEventListener('showTestModal', handleTestModal);
      }
      
      return () => {
        clearTimeout(timer);
        if (typeof window !== 'undefined') {
          window.removeEventListener('showTestModal', handleTestModal);
        }
      };
    }, []);

    useEffect(() => {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.ctrlKey && e.shiftKey && e.key === 'T') {
          console.log('快捷鍵觸發測試彈窗');
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('showTestModal'));
          }
        }
      };

      if (typeof window !== 'undefined') {
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
      }
    }, []);

    // 🔥 簡化版處理訂閱選擇 - 移除郵件通知
    const handleSubscribe = async () => {
      try {
        console.log(`🔥 handleSubscribe 被調用`);
        console.log(`   - 當前用戶狀態:`, currentUserData);
        
        const newStatus = currentUserData?.subscribe === true ? false : true;
        
        console.log(`   - 新狀態: ${newStatus}`);
        
        // 🔥 調用簡化版API（不發送郵件）
        await updateSubscriptionStatus(newStatus);
        
        // 更新本地狀態
        setCurrentUserData(prev => prev ? { ...prev, subscribe: newStatus } : null);
        
        // 顯示成功訊息
        console.log(`✅ 訂閱狀態更新為: ${newStatus ? '已訂閱' : '未訂閱'}`);
        
        setShowSubscriptionModal(false);
      } catch (error) {
        console.error('❌ handleSubscribe 失敗:', error);
        alert('操作失敗，請稍後再試');
      }
    };

    const handleDecline = async () => {
      // 如果是新用戶選擇暫不訂閱
      if (currentUserData?.subscribe === null || currentUserData?.subscribe === undefined) {
        try {
          await updateSubscriptionStatus(false); // 簡化版，不發送郵件
          setCurrentUserData(prev => prev ? { ...prev, subscribe: false } : null);
          setShowSubscriptionModal(false);
        } catch (error) {
          console.error('更新訂閱狀態失敗:', error);
        }
      } else {
        // 已有狀態的用戶選擇保持現狀
        setShowSubscriptionModal(false);
      }
    };

    const cleanResponseContent = useCallback((content: string): string => {
        if (!content || typeof content !== 'string') return '';
        
        const cleanContent = content
            .replace(/HELPER_START/g, '')
            .replace(/HELPER_END/g, '')
            .replace(/HELPER_THINKING/g, '')
            .replace(/HELPER_ERROR/g, '')
            .replace(/HELPER_BEGIN/g, '')
            .replace(/HELPER_COMPLETE/g, '')
            .replace(/\[SYSTEM\].*?\[\/SYSTEM\]/g, '')
            .replace(/\[DEBUG\].*?\[\/DEBUG\]/g, '')
            .replace(/\[CONTROL\].*?\[\/CONTROL\]/g, '')
            .replace(/\n\s*\n\s*\n/g, '\n\n')
            .trim();
        
        return cleanContent;
    }, []);

    const clearThinkingState = useCallback(() => {
        if (typeof window === 'undefined') return;
        
        const currentMessages = JSON.parse(localStorage.getItem("chatHistory") || "[]") as Message[];
        const updatedMessages = currentMessages.map(msg => {
            if (msg.content === "__TYPING__" || msg.isStreaming) {
                return {
                    ...msg,
                    content: msg.content === "__TYPING__" ? "處理請求時發生錯誤，請重試。" : cleanResponseContent(msg.content),
                    isStreaming: false,
                    isError: msg.content === "__TYPING__" ? true : false
                };
            }
            return {
                ...msg,
                content: cleanResponseContent(msg.content),
                isStreaming: false
            };
        });
        
        localStorage.setItem("chatHistory", JSON.stringify(updatedMessages));
        setMessages(updatedMessages);
    }, [cleanResponseContent]);
    
    useEffect(() => {
        if (typeof window === 'undefined') return;
        
        const savedMessages = localStorage.getItem("chatHistory");
        if (savedMessages) {
          try {
            const parsedMessages = JSON.parse(savedMessages) as Message[];
            const formattedMessages = parsedMessages.map((msg: Message) => ({
              type: msg.type,
              content: cleanResponseContent(msg.content),
              isStreaming: false,
              recommendedQuestions: msg.recommendedQuestions || undefined,
              processingStage: msg.processingStage,
              startTime: msg.startTime,
              isError: msg.isError || false,
              isCancelled: msg.isCancelled || false
            }));
            setMessages(formattedMessages);
          } catch (error) {
            console.error('解析 localStorage 資料失敗:', error);
            setMessages([]);
          }
        }
      
        const handleStorageChange = () => {
          if (typeof window === 'undefined') return;
          
          const updatedMessages = localStorage.getItem("chatHistory");
          if (updatedMessages) {
            try {
              const parsedMessages = JSON.parse(updatedMessages) as Message[];
              const formattedMessages = parsedMessages.map((msg: Message) => ({
                type: msg.type,
                content: cleanResponseContent(msg.content),
                isStreaming: msg.isStreaming || false,
                recommendedQuestions: msg.recommendedQuestions || undefined,
                processingStage: msg.processingStage,
                startTime: msg.startTime,
                isError: msg.isError || false,
                isCancelled: msg.isCancelled || false
              }));
              setMessages(formattedMessages);
            } catch (error) {
              console.error('解析更新的 localStorage 資料失敗:', error);
              clearThinkingState();
            }
          }
        };
      
        if (typeof window !== 'undefined') {
          window.addEventListener("storage", handleStorageChange);
        }
      
        return () => {
          if (typeof window !== 'undefined') {
            window.removeEventListener("storage", handleStorageChange);
          }
        };
    }, [cleanResponseContent, clearThinkingState]);

    useEffect(() => {
        const handleBeforeUnload = () => {
            clearThinkingState();
        };

        const handleError = (event: ErrorEvent) => {
            console.error('頁面錯誤:', event);
            clearThinkingState();
        };

        const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
            console.error('未處理的 Promise 拒絕:', event);
            clearThinkingState();
        };

        if (typeof window !== 'undefined') {
          window.addEventListener('beforeunload', handleBeforeUnload);
          window.addEventListener('error', handleError);
          window.addEventListener('unhandledrejection', handleUnhandledRejection);
        }

        return () => {
          if (typeof window !== 'undefined') {
            window.removeEventListener('beforeunload', handleBeforeUnload);
            window.removeEventListener('error', handleError);
            window.removeEventListener('unhandledrejection', handleUnhandledRejection);
          }
        };
    }, [clearThinkingState]);

    const handleWelcomeQuestionClick = (question: string) => {
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('welcomeQuestionClick', { 
              detail: { question } 
          }));
        }
    };

    const renderRawContent = (content: string) => {
        const cleanedContent = cleanResponseContent(content);
        
        if (cleanedContent.startsWith("![上傳圖片](data:image")) {
          const match = cleanedContent.match(/!\[.*?\]\((.*?)\)/);
          const src = match?.[1];
          return (
            <>
              {src && (
                <Image
                  src={src}
                  alt="描述文字"
                  width={150}
                  height={150}
                  style={{ maxWidth: '150px', borderRadius: '8px', objectFit: 'cover' }}
                />
              )}
              <br />
              <pre style={{ 
                whiteSpace: 'pre-wrap', 
                fontFamily: 'inherit',
                margin: 0,
                lineHeight: '1.5'
              }}>
                {cleanedContent.replace(/!\[.*?\]\(.*?\)/, '')}
              </pre>
            </>
          );
        }
        
        return (
          <pre style={{ 
            whiteSpace: 'pre-wrap', 
            fontFamily: 'inherit',
            margin: 0,
            lineHeight: '1.5',
            wordWrap: 'break-word',
            overflowWrap: 'break-word'
          }}>
            {cleanedContent}
          </pre>
        );
    };

    const renderStreamingContent = (content: string) => {
        const cleanedContent = cleanResponseContent(content);
        
        if (!cleanedContent.trim()) {
            return (
                <div className="ai-thinking">
                    <div className="loader">
                        <span className="loader__dot"></span>
                        <span className="loader__dot"></span>
                        <span className="loader__dot"></span>
                    </div>
                    <span style={{ 
                        fontSize: '14px', 
                        color: '#666', 
                        marginLeft: '8px',
                        fontStyle: 'italic'
                    }}>
                        正在處理中...
                    </span>
                </div>
            );
        }
        
        return (
          <div className="streaming-content">
            <pre style={{ 
              whiteSpace: 'pre-wrap', 
              fontFamily: 'inherit',
              margin: 0,
              lineHeight: '1.5',
              wordWrap: 'break-word',
              overflowWrap: 'break-word'
            }}>
              {cleanedContent}
              <span className="streaming-cursor">▊</span>
            </pre>
          </div>
        );
    };

    const renderCancelledContent = (content: string) => {
        return (
          <div className="cancelled-message" style={{
            display: 'flex',
            alignItems: 'center',
            padding: '12px 16px',
            backgroundColor: '#f8f4ff',
            border: '1px solid #d8b4fe',
            borderRadius: '8px',
            color: '#7c3aed',
            fontSize: '14px',
            fontWeight: '500'
          }}>
            <span style={{ 
              fontSize: '18px', 
              marginRight: '8px',
              filter: 'grayscale(20%)'
            }}>
              ⏹️
            </span>
            <span>{content}</span>
          </div>
        );
    };

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const showWelcomeScreen = messages.length === 0;

    return (
        <>
          <div className="chat-container" ref={chatContainerRef}>
            {showWelcomeScreen ? (
              <WelcomeScreen 
                onQuestionClick={handleWelcomeQuestionClick} 
                isLoggedIn={isLoggedIn}
                currentUserData={currentUserData}
              />
            ) : (
              messages.map((message, index) => (
                <div key={index} className={`${message.type === 'user' ? 'user-message-container' : 'ai-response'} ${message.isError ? 'message-error' : ''}`}>
                  {message.type === 'user' ? (
                    <div className="user-message">
                      {renderRawContent(message.content)}
                    </div>
                  ) : (
                    <>
                      <div>
                        <Image 
                          src="/img/logo.png" 
                          className="logoicon" 
                          alt="Logo" 
                          width={28} 
                          height={28}
                        />
                      </div>
                      <div className="response-text">
                        {message.content === "__TYPING__" ? (
                          <div className="ai-thinking">
                            <div className="loader">
                              <span className="loader__dot"></span>
                              <span className="loader__dot"></span>
                              <span className="loader__dot"></span>
                            </div>
                            <span style={{ 
                              fontSize: '14px', 
                              color: '#666', 
                              marginLeft: '8px',
                              fontStyle: 'italic'
                            }}>
                              正在思考中...
                            </span>
                          </div>
                        ) : message.isCancelled ? (
                          renderCancelledContent(message.content)
                        ) : message.isStreaming ? (
                          renderStreamingContent(message.content)
                        ) : (
                          <div style={{ marginTop: '3px', lineHeight: '1.2' }}>
                            {message.isError ? (
                              <div className="error-message">
                                <span className="error-icon">⚠️</span>
                                <span>{message.content || "處理請求時發生錯誤，請重試。"}</span>
                              </div>
                            ) : (
                              renderRawContent(message.content)
                            )}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
          </div>

          {/* 🔥 簡化版訂閱提醒彈窗 - 移除郵件發送功能 */}
          <SubscriptionModal 
            isOpen={showSubscriptionModal}
            onSubscribe={handleSubscribe}
            onDecline={handleDecline}
            onClose={() => setShowSubscriptionModal(false)}
            currentStatus={currentUserData?.subscribe}
            userName={currentUserData?.username}
            userEmail={currentUserData?.email}
            isLoading={false}
          />
      
          {enlargedImage && (
            <div
              onClick={() => setEnlargedImage(null)}
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100vw',
                height: '100vh',
                backgroundColor: 'rgba(0,0,0,0.7)',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                zIndex: 9999
              }}
            >
              <Image
                src={enlargedImage}
                alt="放大圖片"
                width={500}
                height={500}
                style={{ maxWidth: '90vw', maxHeight: '90vh', borderRadius: '10px', objectFit: 'contain' }}
              />
            </div>
          )}
        </>
      );
}