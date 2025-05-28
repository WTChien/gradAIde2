"use client";
import React, { useState, useEffect, useRef } from 'react';
import '../style.css';
import Image from 'next/image';

export default function ContextAreaph() {
    const [messages, setMessages] = useState([
        { type: 'user', content:  `
           我現在修課狀態：修滿通識6學分，全人教育課程2學分，我要再修多少學分可以達到畢業門檻？
            `, },
        {
            type: 'ai',
            content: `根據資管系的畢業條件（111資訊管理學系修業規則適用111學年度新生）：
1.全人教育核心課程：需修滿8學分（你目前已修2學分，因此還需要6學分）。
2.通識涵養課程：需修滿12學分（你目前已修6學分，因此還需要6學分）。
3.專業必修課程：需修滿64學分。
4.畢業總學分數：至少128學分，其中需要包含專業選修至少10學分。

如果你尚未修習專業課程及其他選修課程，則你還需修以下學分：
全人教育核心課程：6學分
通識涵養課程：6學分
專業必修課程：64學分
專業選修課程：至少10學分
總畢業學分需達128學分

你可以告訴我你的專業課程修課狀況，我可以再幫你更精準計算剩餘學分。

`,
        },

    ]);
    const [editingIndex, setEditingIndex] = useState<number | null>(null);
    const [editingContent, setEditingContent] = useState<string>('');
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null); // 創建一個 ref 來引用輸入框

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const handleEdit = (index: number) => {
        setEditingIndex(index);
        setEditingContent(messages[index].content);
        setTimeout(() => inputRef.current?.focus(), 0); // 在設置狀態後讓輸入框自動聚焦
    };

    const handleSave = (index: number) => {
        const updatedMessages = [...messages];
        updatedMessages[index].content = editingContent;
        setMessages(updatedMessages);
        setEditingIndex(null); // 結束編輯模式
    };

    const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
        if (event.key === 'Enter') {
            handleSave(index); // 當按下 Enter 鍵時保存編輯
        }
    };

    return (
        <div className="chat-container" ref={chatContainerRef}>
            {messages.map((message, index) => (
                <div
                    key={index}
                    className={message.type === 'user' ? 'user-message-container' : 'ai-response'}
                >
                    {message.type === 'user' ? (
                        <>
                            <div className="user-message">
                                {editingIndex === index ? (
                                    <input
                                        type="text"
                                        value={editingContent}
                                        onChange={(e) => setEditingContent(e.target.value)}
                                        onKeyDown={(e) => handleKeyDown(e, index)}
                                        className="edit-input"
                                        ref={inputRef} // 將 ref 連接到輸入框
                                    />
                                ) : (
                                    <p className="message-text">{message.content}</p>
                                )}
                            </div>
                            <div>
                                {editingIndex === index ? (
                                    <button className="save add" onClick={() => handleSave(index)}>
                                        <Image alt='' style={{ width: '14px', marginLeft: '5px' }} src="/img/save.png" />
                                    </button>
                                ) : (
                                    <button className="add" onClick={() => handleEdit(index)}>
                                        <Image src="/img/Write.png" className="editicon" alt="Edit" />
                                    </button>
                                )}
                            </div>
                        </>
                    ) : (
                        <>
                            <div>
                                <Image src="/img/logo.png" className="logoicon" alt="Logo" />
                            </div>
                            <div className="response-text">
                                <p style={{ marginTop: '3px', lineHeight: '1.2' }}>{message.content}</p>
                            </div>
                        </>
                    )}
                </div>
            ))}
        </div>
    );
}
