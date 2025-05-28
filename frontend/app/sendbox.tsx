"use client";
import React, { useState, useEffect, useRef } from 'react';
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
}

type SendBoxProps = {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
};

export default function SendBox({ messages, setMessages }: SendBoxProps) {
  console.log(messages);

  const [inputText, setInputText] = useState('');
  const [show, setShow1] = useState(false);
  const [selectedTime, setSelectedTime] = useState<string | null>(null);
  const [tempSelectedTime, setTempSelectedTime] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  
  // 推薦問題隱藏狀態
  const [isRecommendedHidden, setIsRecommendedHidden] = useState(false);
  
  const [isLoading, setIsLoading] = useState(false);
  
  const abortControllerRef = useRef<AbortController | null>(null);
  
  const account = typeof window !== 'undefined' ? (localStorage.getItem("account") || "") : "";

  const handleClose1 = () => {
    setShow1(false);
  };

  const handleClose2 = () => {
    setSelectedTime(tempSelectedTime);
    setShow1(false);
  };
  
  const handleShow1 = () => {
    setTempSelectedTime(selectedTime);
    setShow1(true);
  };

  // 週一至週五和時間區塊定義
  const weekdays = ["一", "二", "三", "四", "五"];
  const timeBlocks = [
    { start: "D1", end: "D2", slots: ["----\n\nD1\n\n", "D2\n\n----"] },
    { start: "D3", end: "D4", slots: ["----\n\nD3\n\n", "D4\n\n----"] },
    { start: "D5", end: "D6", slots: ["----\n\nD5\n\n", "D6\n\n----"] },
    { start: "D7", end: "D8", slots: ["----\n\nD7\n\n", "D8\n\n----"] },
  ];

  // 處理貼上圖片
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      if (!account) {
        alert("請先登入才能上傳圖片");
        return;
      }
      if (e.clipboardData) {
        const items = e.clipboardData.items;
        for (const item of items) {
          if (item.type.startsWith("image/")) {
            const file = item.getAsFile();
            if (file) {
              setImageFile(file);
              const reader = new FileReader();
              reader.onloadend = () => setImagePreviewUrl(reader.result as string);
              reader.readAsDataURL(file);
            }
          }
        }
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, [account]);

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
      
      // 檢測推薦問題標記
      if (line.includes('推薦問題') || line.includes('你可能還會想問')) {
        foundRecommendSection = true;
        skipLines = true;
        continue;
      }
      
      // 如果在推薦問題區域中
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
      
      // 如果不在推薦問題區域，保留這行
      if (!skipLines) {
        cleanedLines.push(lines[i]);
      } else if (line === '' && foundRecommendSection) {
        // 空行可能代表推薦問題區域結束
        skipLines = false;
        foundRecommendSection = false;
      }
    }
    
    // 補充預設問題（如果不足3個）
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

  // 發送訊息函數（簡化版，移除串流邏輯）
  const sendMessage = async () => {
    if (!inputText.trim()) return;
    if (isLoading) return;

    // 取消之前的請求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setIsLoading(true);

    // 準備最終文字內容
    let finalText = inputText;
    if (selectedTime) {
      const [day, startPeriod] = selectedTime.split("-");
      const timeBlock = timeBlocks.find((block) => block.start === startPeriod);
      const endPeriod = timeBlock?.end || "";
      finalText += `\n（偏好的排課時間為：星期${day} ${startPeriod}~${endPeriod}）`;
    }

    // 處理圖片內容
    let userMessageContent = finalText;
    const getImageBase64 = (file: File): Promise<string> => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result?.toString().split(",")[1];
          if (base64) resolve(base64);
          else reject("無法轉換圖片");
        };
        reader.readAsDataURL(file);
      });
    };

    let base64Image: string | undefined;
    if (imageFile) {
      try {
        base64Image = await getImageBase64(imageFile);
        const imageMarkdown = `![上傳圖片](data:image/jpeg;base64,${base64Image})`;
        userMessageContent = `${imageMarkdown}\n${finalText}`;
      } catch (error) {
        console.error('圖片處理失敗:', error);
      }
    }

    // 建立使用者訊息
    const userMessage: Message = {
      type: 'user',
      content: userMessageContent,
      isStreaming: false
    };

    // 建立 AI 回應佔位符（顯示思考動畫）
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
    setImagePreviewUrl(null);
    setImageFile(null);
    setSelectedTime(null);

    try {
      // 準備請求資料（移除 stream 參數）
      const requestData = {
        message: finalText,
        image: base64Image
      };

      // 發送 API 請求
      const response = await fetch('https://llm.gradaide.xyz/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
        signal: abortControllerRef.current!.signal
      });

      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch (e) {
          console.warn('無法解析錯誤回應:', e);
        }
        
        throw new Error(errorMessage);
      }

      const result = await response.json();
      
      if (result.error) {
        throw new Error(result.error);
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
      
      const errorMessages = [...newMessages];
      errorMessages[errorMessages.length - 1] = {
        type: 'ai',
        content: `❌ 連線失敗: ${error instanceof Error ? error.message : '未知錯誤'}`,
        isStreaming: false
      };
      setMessages(errorMessages);
      updateLocalStorage(errorMessages);
      
    } finally {
      setIsLoading(false);
    }
  };

  // 停止回應
  const stopResponse = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
  };

  const checkUploadLimitAndSetImage = async (file: File) => {
    try {
      if (!account) {
        alert("請先登入才能上傳圖片");
        return;
      }

      const formData = new FormData();
      formData.append("account", account);
      formData.append("file", file);

      const res = await axios.post("https://llm.gradaide.xyz/upload_image", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      const base64 = res.data.base64;
      setImageFile(file);
      setImagePreviewUrl(`data:image/jpeg;base64,${base64}`);

    } catch (err: unknown) {
      console.error("圖片上傳失敗：", err);
      if (err instanceof AxiosError && err.response?.data?.detail) {
        alert(err.response.data.detail);
      } else {
        alert("圖片上傳失敗，請稍後再試");
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
  
  // 判斷是否有聊天記錄（至少有一組問答）
  const hasConversationHistory = messages.length >= 2;

  return (
    <>
      {/* 推薦問題區域 */}
      {hasConversationHistory && latestRecommendedQuestions.length > 0 && !isLoading && !isRecommendedHidden && (
        <div className="recommended-questions">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div className="recommended-title">💡 你可能還會想問：</div>
            <button
              onClick={() => setIsRecommendedHidden(true)}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '16px',
                cursor: 'pointer',
                color: 'var(--color)',
                opacity: 0.6,
                padding: '2px 6px',
                borderRadius: '4px',
                transition: 'opacity 0.2s ease'
              }}
              onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
              onMouseLeave={(e) => e.currentTarget.style.opacity = '0.6'}
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
        <div style={{
          position: 'absolute',
          bottom: '90px',
          right: '20px',
          zIndex: 3
        }}>
          <button
            onClick={() => setIsRecommendedHidden(false)}
            style={{
              background: 'rgba(89, 91, 212, 0.9)',
              border: 'none',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              color: 'white',
              fontSize: '18px',
              cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(89, 91, 212, 1)';
              e.currentTarget.style.transform = 'scale(1.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(89, 91, 212, 0.9)';
              e.currentTarget.style.transform = 'scale(1)';
            }}
            title="顯示推薦問題"
          >
            💡
          </button>
        </div>
      )}

      {/* 圖片預覽 */}
      {imagePreviewUrl && (
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
            src={imagePreviewUrl}
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
              setImagePreviewUrl(null);
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
        onHide={handleClose1}
        dialogClassName="custom-modal1"
      >
        <div className="modal-header">
          <h1 className="modalfont">通識選課</h1>
          <button className="close-button" onClick={handleClose1}>
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
            onClick={handleClose1}
          >
            取消
          </button>
          <button className="confirm-button" onClick={handleClose2}>
            確定
          </button>
        </div>
      </Modal>

      {/* 輸入容器 */}
      <div className="input-container">
        {/* 時間選擇按鈕 */}
        <button className="classtable" onClick={handleShow1}>
          <Image
            className="sendicon"
            src={selectedTime ? "/img/sign.png" : "/img/add.png"}
            alt="時間選擇"
            width={24}
            height={24}
          />
        </button>

        {/* 圖片上傳按鈕 */}
        <label className="classtable">
          <Image alt="" className="sendicon" src="/img/image.png" width={24} height={24} />
          <input
            type="file"
            accept="image/*"
            onChange={(e) => {
              if (!account) {
                alert("請先登入才能上傳圖片");
                return;
              }
              if (e.target.files && e.target.files[0]) {
                checkUploadLimitAndSetImage(e.target.files[0]);
                e.target.value = "";
              }
            }}
            hidden
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
          <button className="send-button" onClick={stopResponse} title="停止回應">
            <span style={{ fontSize: '16px' }}>⏹</span>
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
    </>
  );
}