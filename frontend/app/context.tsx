"use client";
import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import './style.css';
import Image from 'next/image';

interface Message {
  type: string;
  content: string;
  isStreaming?: boolean;
  recommendedQuestions?: string[]; // 推薦問題支援
  processingStage?: string; // 處理階段
  startTime?: number; // 開始時間
  isError?: boolean; // 新增：錯誤狀態標記
}

export default function ContextArea() {         
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const [enlargedImage, setEnlargedImage] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    
    useEffect(() => {
      const setVh = () => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
      };
      setVh();
      window.addEventListener('resize', setVh);
      return () => window.removeEventListener('resize', setVh);
    }, []);
    
    useEffect(() => {
        const savedMessages = localStorage.getItem("chatHistory");
        if (savedMessages) {
          try {
            const parsedMessages = JSON.parse(savedMessages) as Message[];
            // 確保舊訊息格式相容，並保留推薦問題
            const formattedMessages = parsedMessages.map((msg: Message) => ({
              type: msg.type,
              content: cleanResponseContent(msg.content), // 🔹 清理歷史消息中的控制標記
              isStreaming: false, // 🔹 歷史消息不應該保持 streaming 狀態
              recommendedQuestions: msg.recommendedQuestions || undefined,
              processingStage: msg.processingStage,
              startTime: msg.startTime,
              isError: msg.isError || false
            }));
            setMessages(formattedMessages);
          } catch (error) {
            console.error('解析 localStorage 資料失敗:', error);
            setMessages([]);
          }
        }
      
        const handleStorageChange = () => {
          const updatedMessages = localStorage.getItem("chatHistory");
          if (updatedMessages) {
            try {
              const parsedMessages = JSON.parse(updatedMessages) as Message[];
              const formattedMessages = parsedMessages.map((msg: Message) => ({
                type: msg.type,
                content: cleanResponseContent(msg.content), // 🔹 清理更新消息中的控制標記
                isStreaming: msg.isStreaming || false,
                recommendedQuestions: msg.recommendedQuestions || undefined,
                processingStage: msg.processingStage,
                startTime: msg.startTime,
                isError: msg.isError || false
              }));
              setMessages(formattedMessages);
            } catch (error) {
              console.error('解析更新的 localStorage 資料失敗:', error);
              // 🔹 解析失敗時清除思考狀態
              clearThinkingState();
            }
          }
        };
      
        window.addEventListener("storage", handleStorageChange);
      
        return () => {
          window.removeEventListener("storage", handleStorageChange);
        };
    }, []);

    // 🔹 新增：清理回應內容的函數
    const cleanResponseContent = (content: string): string => {
        if (!content || typeof content !== 'string') return '';
        
        // 移除所有 HELPER_ 標記和其他控制標記
        const cleanContent = content
            .replace(/HELPER_START/g, '')
            .replace(/HELPER_END/g, '')
            .replace(/HELPER_THINKING/g, '')
            .replace(/HELPER_ERROR/g, '')
            .replace(/HELPER_BEGIN/g, '')
            .replace(/HELPER_COMPLETE/g, '')
            // 移除其他可能的控制標記
            .replace(/\[SYSTEM\].*?\[\/SYSTEM\]/g, '')
            .replace(/\[DEBUG\].*?\[\/DEBUG\]/g, '')
            .replace(/\[CONTROL\].*?\[\/CONTROL\]/g, '')
            // 移除多餘的空行
            .replace(/\n\s*\n\s*\n/g, '\n\n')
            .trim();
        
        return cleanContent;
    };

    // 🔹 新增：清除思考狀態的函數
    const clearThinkingState = useCallback(() => {
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
    }, []);

    // 🔹 新增：監聽頁面卸載和錯誤，清理思考狀態
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

        window.addEventListener('beforeunload', handleBeforeUnload);
        window.addEventListener('error', handleError);
        window.addEventListener('unhandledrejection', handleUnhandledRejection);

        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
            window.removeEventListener('error', handleError);
            window.removeEventListener('unhandledrejection', handleUnhandledRejection);
        };
    }, []);
                    
    const renderContent = (content: string) => {
        // 🔹 渲染前先清理內容
        const cleanedContent = cleanResponseContent(content);
        
        // 處理圖片內容
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
              <ReactMarkdown>{cleanedContent.replace(/!\[.*?\]\(.*?\)/, '')}</ReactMarkdown>
            </>
          );
        }
        
        // 處理 Markdown 內容
        return <ReactMarkdown>{cleanedContent}</ReactMarkdown>;
    };

    const renderStreamingContent = (content: string) => {
        // 🔹 串流內容也需要清理
        const cleanedContent = cleanResponseContent(content);
        
        // 如果清理後內容為空，顯示載入狀態
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
        
        // 如果內容包含多行，逐行顯示
        const lines = cleanedContent.split('\n');
        return (
          <div className="streaming-content">
            {lines.map((line, index) => (
              <div key={index} className="streaming-line">
                {line}
                {/* 🔹 在最後一行顯示游標動畫 */}
                {index === lines.length - 1 && (
                    <span className="streaming-cursor">▊</span>
                )}
              </div>
            ))}
          </div>
        );
    };

    // **🔹 設定自動捲動到最新訊息**
    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <>
          <div className="chat-container" ref={chatContainerRef}>
            {messages.map((message, index) => (
              <div key={index} className={`${message.type === 'user' ? 'user-message-container' : 'ai-response'} ${message.isError ? 'message-error' : ''}`}>
                {message.type === 'user' ? (
                  <div className="user-message">
                    {renderContent(message.content)}
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
                        // 🔹 AI 思考中的動畫 - 顯示在 AI 回覆區塊
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
                      ) : message.isStreaming ? (
                        // 串流中的訊息使用特殊渲染
                        renderStreamingContent(message.content)
                      ) : (
                        // 一般訊息使用 ReactMarkdown
                        <div style={{ marginTop: '3px', lineHeight: '1.2' }}>
                          {message.isError ? (
                            // 🔹 錯誤消息的特殊顯示
                            <div className="error-message">
                              <span className="error-icon">⚠️</span>
                              <span>{message.content || "處理請求時發生錯誤，請重試。"}</span>
                            </div>
                          ) : (
                            <ReactMarkdown>{cleanResponseContent(message.content)}</ReactMarkdown>
                          )}
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
      
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