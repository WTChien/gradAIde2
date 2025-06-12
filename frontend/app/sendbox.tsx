"use client";
import React, { useState, useEffect, useRef, useCallback } from 'react';
import './style.css';
import { Modal } from 'react-bootstrap';
import axios, { AxiosError } from "axios";
import Image from 'next/image';

interface Message {
  type: string;
  content: string;
  isStreaming?: boolean;
  recommendedQuestions?: string[];
  processingStage?: string;
  startTime?: number;
  isCancelled?: boolean; // 新增：標記是否被取消
}

interface RequestData {
  message: string;
  image?: string;
}

// 上傳限制和統計介面，支援管理員無限上傳
interface UploadLimits {
  daily_uploads: number | string;
  max_file_size: number;
}

interface UploadStatistics {
  today: number;
  week: number;
  month: number;
  total: number;
  last_upload: string | null;
}

interface UserUploadInfo {
  can_upload: boolean;
  user_type: string;
  limits: UploadLimits;
  today_usage: number;
  remaining_uploads: number | string;
  statistics: UploadStatistics;
  is_admin?: boolean;
}

type SendBoxProps = {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
};

export default function SendBox({ messages, setMessages }: SendBoxProps) {
  console.log(messages);

  // 動態 sidebar width 控制
  const updateSidebarWidth = useCallback((collapsed: boolean) => {
    const root = document.documentElement;
    
    if (collapsed) {
      root.style.setProperty('--sidebar-width', '80px');
      document.body.className = 'nav-collapsed';
    } else {
      root.style.setProperty('--sidebar-width', '250px');
      document.body.className = '';
    }
  }, []);

  // 監聽 sidebar 狀態變化
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        updateSidebarWidth(true);
      } else {
        const isCurrentlyCollapsed = document.body.className.includes('nav-collapsed');
        updateSidebarWidth(isCurrentlyCollapsed);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [updateSidebarWidth]);

  // 基本狀態
  const [inputText, setInputText] = useState('');
  const [show, setShow] = useState(false);
  const [selectedTime, setSelectedTime] = useState<string | null>(null);
  const [tempSelectedTime, setTempSelectedTime] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [localImageUrl, setLocalImageUrl] = useState<string | undefined>(undefined);
  const [isRecommendedHidden, setIsRecommendedHidden] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  
  // 上傳相關狀態
  const [uploadInfo, setUploadInfo] = useState<UserUploadInfo | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  
  const abortControllerRef = useRef<AbortController | null>(null);
  
  // 只獲取登入資訊，移除學年相關代碼
  const account = typeof window !== 'undefined' ? (localStorage.getItem("account") || "") : "";

  // 時間選擇相關
  const handleClose = () => setShow(false);
  const handleClose2 = () => {
    setSelectedTime(tempSelectedTime);
    setShow(false);
  };
  const handleShow = () => {
    setTempSelectedTime(selectedTime);
    setShow(true);
  };

  // 週一至週五和時間區塊定義
  const weekdays = ["一", "二", "三", "四", "五"];
  const timeBlocks = [
    { start: "D1", end: "D2", slots: ["----\n\nD1\n\n", "D2\n\n----"] },
    { start: "D3", end: "D4", slots: ["----\n\nD3\n\n", "D4\n\n----"] },
    { start: "D5", end: "D6", slots: ["----\n\nD5\n\n", "D6\n\n----"] },
    { start: "D7", end: "D8", slots: ["----\n\nD7\n\n", "D8\n\n----"] },
  ];

  // 網路連線檢查
  const checkNetworkConnection = useCallback(async (): Promise<boolean> => {
    try {
      console.log("🌐 檢查網路連線...");
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch('https://llm.gradaide.xyz/health', {
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      console.log("✅ 網路連線正常，伺服器狀態:", response.status);
      return response.ok;
    } catch (error) {
      console.log("❌ 網路連線檢查失敗:", error);
      return false;
    }
  }, []);

  // 獲取用戶上傳信息，支援管理員無限上傳
  const fetchUploadInfo = useCallback(async (): Promise<UserUploadInfo | null> => {
    if (!account) return null;
    
    try {
      console.log("📊 獲取用戶上傳信息...");
      const response = await axios.post('https://llm.gradaide.xyz/pre_upload_check', {
        account: account
      }, {
        timeout: 10000
      });
      
      const info = response.data as UserUploadInfo;
      console.log("✅ 用戶上傳信息:", info);
      
      if (info.is_admin) {
        console.log("🔑 檢測到管理員身份，無限上傳權限");
      }
      
      setUploadInfo(info);
      return info;
    } catch (error) {
      console.error("❌ 獲取上傳信息失敗:", error);
      return null;
    }
  }, [account]);

  // 檔案驗證，管理員有較寬鬆的限制
  const validateFile = useCallback((file: File, limits?: UploadLimits): { valid: boolean; errors: string[] } => {
    const errors: string[] = [];
    
    // 檢查檔案類型
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
    if (!allowedTypes.includes(file.type)) {
      errors.push(`不支援的檔案格式 (${file.type})，請使用 JPEG、PNG、GIF、WebP 或 BMP`);
    }
    
    // 檢查檔案大小，處理管理員的較大限制
    if (limits && typeof limits.max_file_size === 'number') {
      const maxSize = limits.max_file_size;
      if (file.size > maxSize) {
        errors.push(`檔案過大 (${(file.size / 1024 / 1024).toFixed(2)}MB)，限制為 ${(maxSize / 1024 / 1024).toFixed(1)}MB`);
      }
    }
    
    // 檢查檔案名稱
    if (!file.name || file.name.length > 255) {
      errors.push("檔案名稱無效或過長");
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }, []);

  // 完善的圖片上傳功能（只在發送時調用）
  const uploadImageToServer = useCallback(async (file: File): Promise<string | undefined> => {
    if (!account) {
      alert("請先登入才能上傳圖片");
      return undefined;
    }

    try {
      console.log("=== 開始圖片上傳流程 ===");
      setIsUploadingImage(true);
      setUploadProgress(0);

      // 檢查網路連線
      const isConnected = await checkNetworkConnection();
      if (!isConnected) {
        throw new Error("網路連線異常，請檢查網路狀態");
      }

      // 獲取最新的上傳信息
      const currentUploadInfo = await fetchUploadInfo();

      // 檢查上傳限制，管理員跳過
      if (currentUploadInfo && !currentUploadInfo.can_upload && !currentUploadInfo.is_admin) {
        const dailyLimit = typeof currentUploadInfo.limits.daily_uploads === 'number' 
          ? currentUploadInfo.limits.daily_uploads 
          : "無限制";
        throw new Error(`今日上傳次數已達上限 (${dailyLimit} 次)`);
      }

      // 檔案驗證
      const validation = validateFile(file, currentUploadInfo?.limits);
      if (!validation.valid) {
        throw new Error(validation.errors.join('; '));
      }

      console.log("✅ 檔案驗證通過");
      setUploadProgress(20);

      // 準備上傳
      const formData = new FormData();
      formData.append("account", account);
      formData.append("file", file);

      console.log("📤 開始上傳...");
      setUploadProgress(30);

      const startTime = Date.now();
      const response = await axios.post("https://llm.gradaide.xyz/upload_image", formData, {
        headers: { 
          "Content-Type": "multipart/form-data",
        },
        timeout: 60000,
        maxContentLength: 50 * 1024 * 1024,
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            const adjustedProgress = 30 + (progress * 0.6);
            setUploadProgress(adjustedProgress);
            console.log(`📊 上傳進度: ${progress}%`);
          }
        }
      });

      const endTime = Date.now();
      console.log(`⏱️ 上傳耗時: ${endTime - startTime}ms`);
      setUploadProgress(95);

      if (response.data?.status === 'success' && response.data?.base64) {
        console.log("✅ 上傳成功");
        console.log("📊 檔案信息:", response.data.file_info);
        console.log("📈 使用狀況:", response.data.usage_info);
        
        setUploadProgress(100);
        
        // 更新本地上傳信息，處理管理員狀態
        if (response.data.usage_info) {
          const usageInfo = response.data.usage_info;
          const newUploadInfo: UserUploadInfo = {
            can_upload: usageInfo.is_admin || usageInfo.remaining > 0,
            user_type: usageInfo.user_type,
            limits: {
              daily_uploads: usageInfo.daily_limit,
              max_file_size: currentUploadInfo?.limits.max_file_size || 10 * 1024 * 1024
            },
            today_usage: usageInfo.today_uploads,
            remaining_uploads: usageInfo.remaining,
            statistics: currentUploadInfo?.statistics || { today: 0, week: 0, month: 0, total: 0, last_upload: null },
            is_admin: usageInfo.is_admin
          };
          setUploadInfo(newUploadInfo);
          
          // 通知导航栏刷新统计
          window.dispatchEvent(new CustomEvent('uploadStatsChanged', { 
            detail: newUploadInfo 
          }));
        }
        
        return response.data.base64;
      } else {
        throw new Error("伺服器回應格式不正確");
      }

    } catch (error: unknown) {
      console.error("=== 圖片上傳錯誤 ===");
      console.error("詳細錯誤:", error);
      
      let errorMessage = "圖片上傳失敗";
      
      if (error instanceof AxiosError) {
        if (error.code === 'ECONNABORTED') {
          errorMessage = "上傳超時，請檢查網路連線或選擇較小的圖片";
        } else if (error.response?.status === 413) {
          errorMessage = "圖片檔案過大，請選擇較小的圖片";
        } else if (error.response?.status === 429) {
          errorMessage = "今日上傳次數已達上限，請明天再試";
        } else if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response?.data?.error) {
          errorMessage = error.response.data.error;
        }
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }
      
      alert(errorMessage);
      return undefined;
      
    } finally {
      setIsUploadingImage(false);
      setUploadProgress(0);
    }
  }, [account, checkNetworkConnection, fetchUploadInfo, validateFile]);

  // 本地圖片預覽處理函數
  const handleLocalImagePreview = useCallback((file: File) => {
    console.log("📁 處理本地圖片預覽:", file.name);
    
    // 前端驗證
    const validation = validateFile(file, uploadInfo?.limits);
    if (!validation.valid) {
      alert(validation.errors.join('; '));
      return;
    }
    
    // 創建本地預覽 URL
    const localUrl = URL.createObjectURL(file);
    setImageFile(file);
    setLocalImageUrl(localUrl);
    console.log("✅ 本地預覽準備完成");
  }, [uploadInfo, validateFile]);

  // 檔案選擇處理器（只做本地預覽，不上傳）
  const handleFileSelection = useCallback((file: File) => {
    console.log("📁 檔案選擇處理:", file.name);
    
    if (!account) {
      alert("請先登入才能上傳圖片");
      return;
    }
    
    // 檢查上傳限制，管理員跳過
    if (uploadInfo && !uploadInfo.can_upload && !uploadInfo.is_admin) {
      const dailyLimit = typeof uploadInfo.limits.daily_uploads === 'number' 
        ? uploadInfo.limits.daily_uploads 
        : "無限制";
      alert(`今日上傳次數已達上限 (${dailyLimit} 次)`);
      return;
    }
    
    // 只做本地預覽，不立即上傳
    handleLocalImagePreview(file);
  }, [account, uploadInfo, handleLocalImagePreview]);

  // 貼上事件處理器
  useEffect(() => {
    const handlePaste = async (e: ClipboardEvent) => {
      if (!account) {
        alert("請先登入才能上傳圖片");
        return;
      }
      
      if (e.clipboardData) {
        const items = e.clipboardData.items;
        for (const item of items) {
          if (item.type.startsWith("image/")) {
            e.preventDefault();
            
            const file = item.getAsFile();
            if (file) {
              console.log("📋 從剪貼簿貼上圖片:", file.name || "未命名");
              handleFileSelection(file);
            }
            break;
          }
        }
      }
    };

    const handleWelcomeQuestionClick = (event: CustomEvent) => {
      const { question } = event.detail;
      setInputText(question);
    };

    window.addEventListener("paste", handlePaste);
    window.addEventListener("welcomeQuestionClick", handleWelcomeQuestionClick as EventListener);
    
    return () => {
      window.removeEventListener("paste", handlePaste);
      window.removeEventListener("welcomeQuestionClick", handleWelcomeQuestionClick as EventListener);
    };
  }, [account, handleFileSelection]);

  // 初始化載入用戶上傳信息
  useEffect(() => {
    if (account && !uploadInfo) {
      fetchUploadInfo();
    }
  }, [account, uploadInfo, fetchUploadInfo]);

  // 清理函數：在組件卸載時釋放本地 URL
  useEffect(() => {
    return () => {
      if (localImageUrl) {
        URL.revokeObjectURL(localImageUrl);
      }
    };
  }, [localImageUrl]);

  // 清理 abort controller
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    e.target.style.height = "24px";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 123)}px`;
  };

  // 更新 localStorage
  const updateLocalStorage = (newMessages: Message[]) => {
    try {
      localStorage.setItem("chatHistory", JSON.stringify(newMessages));
      window.dispatchEvent(new Event('storage'));
    } catch (error) {
      console.error('儲存到 localStorage 失敗:', error);
    }
  };

  // 從 AI 回應中提取並移除推薦問題
  const extractAndCleanResponse = (content: string) => {
    const lines = content.split('\n');
    const questions: string[] = [];
    const cleanedLines: string[] = [];
    
    let foundRecommendSection = false;
    let skipLines = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      if (line.includes('推薦問題') || line.includes('你可能還會想問')) {
        foundRecommendSection = true;
        skipLines = true;
        continue;
      }
      
      if (foundRecommendSection && line.endsWith('？')) {
        const cleanQuestion = line
          .replace(/^\d+\.?\s*/, '')
          .replace(/^[\-\*\•]\s*/, '')
          .trim();
        
        if (cleanQuestion.length > 3 && cleanQuestion.length < 50) {
          questions.push(cleanQuestion);
        }
        
        if (questions.length >= 3) {
          foundRecommendSection = false;
          skipLines = false;
        }
        continue;
      }
      
      if (!skipLines) {
        cleanedLines.push(lines[i]);
      } else if (line === '' && foundRecommendSection) {
        skipLines = false;
        foundRecommendSection = false;
      }
    }
    
    // 補充預設問題
    const defaultQuestions = [
      "有推薦的通識課程嗎？",
      "這個老師的評價如何？", 
      "修課時間衝突怎麼辦？"
    ];
    
    while (questions.length < 3) {
      const defaultQ = defaultQuestions[questions.length];
      if (defaultQ && !questions.includes(defaultQ)) {
        questions.push(defaultQ);
      } else {
        break;
      }
    }
    
    return {
      cleanedContent: cleanedLines.join('\n').trim(),
      recommendedQuestions: questions.slice(0, 3)
    };
  };

  // 修改 sendMessage 函數，移除學年資訊相關處理
  const sendMessage = async () => {
    if (!inputText.trim() && !imageFile) return;
    if (isLoading) return;

    // 取消之前的請求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setIsLoading(true);
    
    try {
      let messageText = inputText.trim() || ""; // 統一使用一個文字變數
      let base64Image: string | undefined;

      // 在發送時才上傳圖片
      if (imageFile) {
        console.log("🚀 開始上傳圖片...");
        base64Image = await uploadImageToServer(imageFile);
        
        if (!base64Image) {
          setIsLoading(false);
          return;
        }
        
        console.log("✅ 圖片上傳完成，準備發送訊息");
      }

      // 如果沒有文字且沒有圖片，提示用戶
      if (!messageText && !base64Image) {
        alert("請輸入問題或上傳圖片再發送");
        setIsLoading(false);
        return;
      }

      // 如果只有圖片沒有文字，給預設文字
      if (!messageText && base64Image) {
        messageText = "請分析這張圖片";
      }

      // 處理時間選擇
      if (selectedTime) {
        const [day, startPeriod] = selectedTime.split("-");
        const timeBlock = timeBlocks.find((block) => block.start === startPeriod);
        const endPeriod = timeBlock?.end || "";
        const timeInfo = `\n（偏好的排課時間為：星期${day} ${startPeriod}~${endPeriod}）`;
        messageText += timeInfo;
      }

      // 準備使用者訊息內容
      let userMessageContent = messageText;
      if (imageFile && base64Image) {
        const imageMarkdown = `![上傳圖片](data:image/jpeg;base64,${base64Image})`;
        userMessageContent = `${imageMarkdown}\n${messageText}`;
      }

      // 建立使用者訊息
      const userMessage: Message = {
        type: 'user',
        content: userMessageContent,
        isStreaming: false
      };

      // 建立 AI 回應佔位符
      const aiMessage: Message = {
        type: 'ai',
        content: '__TYPING__',
        isStreaming: true
      };

      // 更新訊息列表
      const newMessages = [...messages, userMessage, aiMessage];
      setMessages(newMessages);
      updateLocalStorage(newMessages);

      // 清空輸入
      setInputText('');
      setImageFile(null);
      if (localImageUrl) {
        URL.revokeObjectURL(localImageUrl);
        setLocalImageUrl(undefined);
      }
      setSelectedTime(null);

      // 準備請求資料
      const requestData: RequestData = {
        message: messageText // 發送的文字不包含學年資訊
      };

      if (base64Image) {
        requestData.image = base64Image;
      }

      console.log('🚀 發送請求:', { 
        hasImage: !!base64Image, 
        messageLength: messageText.length,
        imageSize: base64Image ? base64Image.length : 0,
        messagePreview: messageText.substring(0, 50) + '...'
      });

      const response = await fetch('https://llm.gradaide.xyz/query', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestData),
        signal: abortControllerRef.current!.signal
      });

      if (!response.ok) {
        let errorMessage = `連線失敗 (HTTP ${response.status})`;
        
        try {
          const errorData = await response.json();
          if (typeof errorData === 'string') {
            errorMessage = errorData;
          } else if (errorData.error) {
            errorMessage = errorData.error;
          } else if (errorData.message) {
            errorMessage = errorData.message;
          } else if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch (e) {
          console.warn('無法解析錯誤回應:', e);
        }
        
        throw new Error(errorMessage);
      }

      const result = await response.json();
      
      if (!result) {
        throw new Error("伺服器回應為空");
      }
      
      if (result.error) {
        const errorMsg = typeof result.error === 'string' ? result.error : "處理請求時發生錯誤";
        throw new Error(errorMsg);
      }

      // 清理回應並提取推薦問題
      const { cleanedContent, recommendedQuestions } = extractAndCleanResponse(result.response || '處理完成');
      
      // 更新最終回應
      const updatedMessages = [...newMessages];
      updatedMessages[updatedMessages.length - 1] = {
        type: 'ai',
        content: cleanedContent,
        isStreaming: false,
        recommendedQuestions: recommendedQuestions
      };
      
      setMessages(updatedMessages);
      updateLocalStorage(updatedMessages);

    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('請求已取消');
        return;
      }
      
      console.error('請求失敗:', error);
      
      let errorMessage = "連線失敗，請重新嘗試";
      
      if (error instanceof Error) {
        errorMessage = `連線失敗: ${error.message}`;
      } else if (typeof error === 'string') {
        errorMessage = `連線失敗: ${error}`;
      }
      
      // 更新錯誤訊息到聊天記錄
      const currentMessages = [...messages];
      if (currentMessages.length > 0) {
        const lastMessage = currentMessages[currentMessages.length - 1];
        if (lastMessage.type === 'ai' && lastMessage.isStreaming) {
          lastMessage.content = `❌ ${errorMessage}`;
          lastMessage.isStreaming = false;
          setMessages(currentMessages);
          updateLocalStorage(currentMessages);
        }
      }
      
    } finally {
      setIsLoading(false);
    }
  };

  // 修改停止回應函數
  const stopResponse = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
      
      // 更新最後一條 AI 訊息為取消狀態
      const currentMessages = [...messages];
      if (currentMessages.length > 0) {
        const lastMessage = currentMessages[currentMessages.length - 1];
        if (lastMessage.type === 'ai' && lastMessage.isStreaming) {
          lastMessage.content = "目前無法取得回應，請稍後再試";
          lastMessage.isStreaming = false;
          lastMessage.isCancelled = true; // 標記為被取消
          setMessages(currentMessages);
          updateLocalStorage(currentMessages);
        }
      }
    }
  };

  // 獲取最新的推薦問題
  const getLatestRecommendedQuestions = (): string[] => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].type === 'ai' && messages[i].recommendedQuestions) {
        return messages[i].recommendedQuestions || [];
      }
    }
    return [];
  };

  const latestRecommendedQuestions = getLatestRecommendedQuestions();
  const hasConversationHistory = messages.length >= 2;

  // 計算上傳按鈕的禁用狀態，管理員不禁用
  const isUploadDisabled = isUploadingImage || (uploadInfo !== null && !uploadInfo.can_upload && !uploadInfo.is_admin);

  return (
    <>
      {/* 上傳進度顯示 */}
      {isUploadingImage && (
        <div 
          style={{
            position: "fixed",
            top: "20px",
            right: "20px",
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            color: "white",
            padding: "15px 20px",
            borderRadius: "10px",
            zIndex: 1000,
            minWidth: "250px"
          }}
        >
          <div style={{ marginBottom: "10px" }}>正在上傳圖片...</div>
          <div style={{ 
            width: "100%", 
            height: "6px", 
            backgroundColor: "#333", 
            borderRadius: "3px",
            overflow: "hidden"
          }}>
            <div 
              style={{
                width: `${uploadProgress}%`,
                height: "100%",
                backgroundColor: "#4CAF50",
                transition: "width 0.3s ease"
              }}
            />
          </div>
          <div style={{ marginTop: "5px", fontSize: "14px" }}>
            {uploadProgress.toFixed(0)}%
          </div>
        </div>
      )}

      {/* 推薦問題區域 */}
      {hasConversationHistory && latestRecommendedQuestions.length > 0 && !isLoading && !isRecommendedHidden && (
        <div className="recommended-questions">
          <div className="recommended-header">
            <div className="recommended-title">💡 你可能還會想問：</div>
            <button
              className="recommended-close-btn"
              onClick={() => setIsRecommendedHidden(true)}
              title="隱藏推薦問題"
            >
              ✕
            </button>
          </div>
          {latestRecommendedQuestions.map((question, index) => (
            <button
              key={index}
              className="recommended-question-btn"
              onClick={() => setInputText(question)}
            >
              {question}
            </button>
          ))}
        </div>
      )}

      {/* 顯示推薦問題的按鈕（當隱藏時） */}
      {hasConversationHistory && latestRecommendedQuestions.length > 0 && !isLoading && isRecommendedHidden && (
        <button
          className="recommended-show-btn"
          onClick={() => setIsRecommendedHidden(false)}
          title="顯示推薦問題"
        >
          💡
        </button>
      )}

      {/* 圖片預覽組件 */}
      {localImageUrl && (
        <div
          style={{
            position: "absolute",
            bottom: "93px",
            left: "90px",
            backgroundColor: "#f3f3f3",
            borderRadius: "12px",
            padding: "6px",
            boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            zIndex: 10,
            marginBottom: "10px",
          }}
        >
          <Image
            src={localImageUrl}
            alt="預覽圖片"
            width={120}
            height={120}
            style={{
              maxWidth: "120px",
              maxHeight: "120px",
              borderRadius: "6px",
              objectFit: "cover"
            }}
          />
          <button
            onClick={() => {
              setImageFile(null);
              if (localImageUrl) {
                URL.revokeObjectURL(localImageUrl);
                setLocalImageUrl(undefined);
              }
            }}
            style={{
              marginTop: "4px",
              backgroundColor: "transparent",
              border: "none",
              color: "#f44336",
              cursor: "pointer",
              fontSize: "12px"
            }}
          >
            ❌ 移除圖片
          </button>
        </div>
      )}

      {/* 時間選擇 Modal */}
      <Modal
        show={show}
        onHide={handleClose}
        dialogClassName="custom-modal1"
      >
        <div className="modal-header">
          <h1 className="modalfont">通識選課</h1>
          <button className="close-button" onClick={handleClose}>
            &times;
          </button>
        </div>

        <div className="modal-content1">
          <p style={{ textAlign: "left", marginTop: "8px" }}>
            請選擇有課的時間（一次只能選擇一個時間區塊）
          </p>

          <div className="grid-header-container">
            <div className="grid-header"></div>
            {weekdays.map((day) => (
              <div key={day} className="grid-header">
                {day}
              </div>
            ))}
          </div>

          <div className="schedule-grid">
            {timeBlocks.map((block) => (
              <div key={block.start} className="grid-row">
                <div className="time-label">
                  {block.slots.map((s, i) => (
                    <div key={i}>{s}</div>
                  ))}
                </div>

                {weekdays.map((day) => {
                  const key = `${day}-${block.start}`;
                  const isSelected = tempSelectedTime === `${day}-${block.start}`;

                  return (
                    <div
                      key={key}
                      className={`grid-cell ${isSelected ? "selected" : ""}`}
                      onClick={() => {
                        const key = `${day}-${block.start}`;
                        setTempSelectedTime((prev) => (prev === key ? null : key));
                      }}                 
                    ></div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        <div className="modal-footer1">
          <button
            className="confirm-button"
            style={{ marginRight: "10px" }}
            onClick={handleClose}
          >
            取消
          </button>
          <button className="confirm-button" onClick={handleClose2}>
            確定
          </button>
        </div>
      </Modal>

      {/* 輸入容器 */}
      <div className="input-container"
           style={{ 
             left: 'calc(var(--sidebar-width, 250px) + 20px)',
             width: 'calc(100vw - var(--sidebar-width, 250px) - 50px)',
             transition: 'left 0.3s ease, width 0.3s ease'
           }}
      >
        {/* 時間選擇按鈕 */}
        <button className="classtable" onClick={handleShow}>
          <Image
            className="sendicon"
            src={selectedTime ? "/img/sign.png" : "/img/add.png"}
            alt="時間選擇"
            width={24}
            height={24}
          />
        </button>

        {/* 圖片上傳按鈕，支援管理員狀態顯示 */}
        <label className="classtable" style={{ 
          opacity: isUploadDisabled ? 0.5 : 1,
          cursor: isUploadDisabled ? 'not-allowed' : 'pointer'
        }}>
          <Image 
            alt="上傳圖片" 
            className="sendicon" 
            src="/img/image.png" 
            width={24} 
            height={24} 
            style={{ 
              filter: uploadInfo?.is_admin ? 'hue-rotate(45deg) brightness(1.2)' : 'none' 
            }}
          />
          <input
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp,image/bmp"
            onChange={async (e) => {
              console.log("📁 檔案選擇事件觸發");
              
              if (!account) {
                console.log("❌ 未登入狀態");
                alert("請先登入才能上傳圖片");
                e.target.value = "";
                return;
              }
              
              if (e.target.files && e.target.files[0]) {
                const selectedFile = e.target.files[0];
                console.log("📁 選擇的檔案:", {
                  name: selectedFile.name,
                  size: selectedFile.size,
                  type: selectedFile.type
                });
                
                // 檢查上傳限制，管理員跳過
                if (uploadInfo && !uploadInfo.can_upload && !uploadInfo.is_admin) {
                  const dailyLimit = typeof uploadInfo.limits.daily_uploads === 'number' 
                    ? uploadInfo.limits.daily_uploads 
                    : "無限制";
                  alert(`今日上傳次數已達上限 (${dailyLimit} 次)`);
                  e.target.value = "";
                  return;
                }
                
                try {
                  // 使用統一的檔案選擇處理函數
                  handleFileSelection(selectedFile);
                } catch (error) {
                  console.error('檔案處理失敗:', error);
                } finally {
                  e.target.value = "";
                }
              }
            }}
            style={{ display: 'none' }}
            disabled={isUploadDisabled}
            title={uploadInfo?.is_admin ? "管理員 - 無限上傳" : undefined}
          />
        </label>

        {/* 輸入框 */}
        <textarea
          className="sendbox"
          name="question"
          value={inputText}
          onChange={handleInputChange}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          placeholder="輸入你的問題..."
          disabled={isLoading}
        />

        {/* 發送/停止按鈕 */}
        {isLoading ? (
          <button 
            className="stop-button" 
            onClick={stopResponse} 
            title="停止回應"
            style={{
              position: 'absolute',
              right: '10px',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              border: 'none',
              background: 'linear-gradient(135deg, #8B5CF6, #7C3AED)',
              color: 'white',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '16px',
              fontWeight: 'bold',
              boxShadow: '0 4px 12px rgba(139, 92, 246, 0.3)',
              transition: 'all 0.2s ease',
              zIndex: 10
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-50%) scale(1.05)';
              e.currentTarget.style.boxShadow = '0 6px 16px rgba(139, 92, 246, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(139, 92, 246, 0.3)';
            }}
            onMouseDown={(e) => {
              e.currentTarget.style.transform = 'translateY(-50%) scale(0.95)';
            }}
            onMouseUp={(e) => {
              e.currentTarget.style.transform = 'translateY(-50%) scale(1.05)';
            }}
          >
            ⏹
          </button>
        ) : (
          <button 
            className="send-button" 
            onClick={sendMessage}
            disabled={isLoading}
          >
            <Image className="sendicon" src="/img/clip.png" alt="Send" width={24} height={24} />
          </button>
        )}
      </div>

      {/* 免責聲明 */}
      <div className='duty' >
        此系統提供資訊可能有誤，實際資訊以校方公告為準。
      </div>

      {/* 開發除錯面板，移除學年資訊顯示 */}
      {process.env.NODE_ENV === 'development' && (
        <div 
          style={{
            position: 'fixed',
            bottom: '10px',
            left: '10px',
            background: 'rgba(0,0,0,0.8)',
            color: 'white',
            padding: '10px',
            borderRadius: '5px',
            fontSize: '12px',
            zIndex: 9999,
            display: 'block'
          }}
          id="debug-panel"
        >
          <div>圖片上傳除錯 {uploadInfo?.is_admin && '👑'}</div>
          <button 
            onClick={() => {
              console.log("當前上傳信息:", uploadInfo);
              console.log("登入帳號:", account);
              console.log("上傳按鈕狀態:", { 
                isUploadDisabled, 
                isUploadingImage, 
                canUpload: uploadInfo?.can_upload,
                isAdmin: uploadInfo?.is_admin 
              });
              console.log("本地圖片URL:", localImageUrl);
              console.log("選擇的檔案:", imageFile);
            }}
            style={{ margin: '2px', padding: '2px 5px', fontSize: '10px' }}
          >
            檢查狀態
          </button>
          <button 
            onClick={() => fetchUploadInfo()}
            style={{ margin: '2px', padding: '2px 5px', fontSize: '10px' }}
          >
            刷新限制
          </button>
          <button 
            onClick={() => checkNetworkConnection()}
            style={{ margin: '2px', padding: '2px 5px', fontSize: '10px' }}
          >
            測試連線
          </button>
          {/* 顯示當前狀態，移除學年資訊 */}
          <div style={{ marginTop: '5px', fontSize: '10px' }}>
            <div>登入帳號: {account || '未登入'}</div>
            <div>上傳中: {isUploadingImage ? '是' : '否'}</div>
            <div>可上傳: {uploadInfo?.can_upload ? '是' : '否'}</div>
            <div>管理員: {uploadInfo?.is_admin ? '是' : '否'}</div>
            <div>按鈕禁用: {isUploadDisabled ? '是' : '否'}</div>
            <div>
              今日使用: {uploadInfo?.today_usage || 0}/
              {typeof uploadInfo?.limits.daily_uploads === 'number' 
                ? uploadInfo.limits.daily_uploads 
                : uploadInfo?.limits.daily_uploads || 0}
            </div>
            <div>本地預覽: {localImageUrl ? '有' : '無'}</div>
            <div>檔案選擇: {imageFile ? imageFile.name : '無'}</div>
          </div>
        </div>
      )}
    </>
  );
}