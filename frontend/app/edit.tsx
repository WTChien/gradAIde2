"use client";
import React, { useEffect, useState } from 'react';
import './style.css';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { Modal } from 'react-bootstrap';
import Image from 'next/image';


export default function Top() {
  const router = useRouter();
  const [username, setUsername] = useState("同學");
  const [showConfirmClear, setShowConfirmClear] = useState(false);


  // 取得並設定使用者名稱
  const fetchUsername = async () => {
    const account = localStorage.getItem("account");
    if (!account) {
      setUsername("同學");
      return;
    }

    try {
      const res = await axios.get<{ username: string }>(`https://llm.gradaide.xyz/get_username/${account}`);
      if (res.data.username && isNaN(Number(res.data.username))) {
        setUsername(`${res.data.username}同學`);
        localStorage.setItem("username", res.data.username);
      } else {
        setUsername("同學");
      }
    } catch {
      console.warn("⚠️ 無法取得使用者名稱，使用預設名稱");
      setUsername("同學");
    }
  };

  useEffect(() => {
    fetchUsername();

    // 監聽 localStorage 變化（例如登出時清除帳號）
    const handleStorageChange = () => {
      fetchUsername();
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  return (
    <div className="header">
      <button className="add" onClick={() => router.push('/')}>
      <Image
        src="/img/Write.png"
        className="addicon"
        onClick={() => setShowConfirmClear(true)}
        alt="開始新對話"
    />

      </button>
      <b className="addfont">HI, {username}</b>
        <Modal
            show={showConfirmClear}
            onHide={() => setShowConfirmClear(false)}
            backdrop="static"
            keyboard={true}
            dialogClassName="custom-modal"
            >
            <div className="modal-header">
                <h1 className="modalfont">確定要開始新對話嗎？</h1>
                <button className="close-button" onClick={() => setShowConfirmClear(false)}>
                &times;
                </button>
            </div>
            <div className="modal-content">
                <p>這將會清除目前的歷史紀錄。</p>
            </div>
            <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button className="confirm-button" onClick={() => {
                localStorage.removeItem("chatHistory");
                setShowConfirmClear(false);
                window.location.reload(); // ✅ 重新整理頁面
                }}>
                確定
                </button>
                <button className="cancel-button" onClick={() => setShowConfirmClear(false)}>
                取消
                </button>
            </div>
        </Modal>

    </div>
    
  );
}
