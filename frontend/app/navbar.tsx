"use client";
import React, { useState, useEffect, useRef } from 'react';
import './style.css';
import './name/name.css';
import './login/login.css';
import './password/password.css';
import './forget/forget.css';
import { useRouter } from 'next/navigation';
import { Modal } from 'react-bootstrap';
import axios from "axios";
import { AxiosError } from "axios";
import Image from 'next/image';

export default function NavBar() {
  const [isDropdownMemOpen, setIsDropdownMemOpen] = useState(false);
  const [isDropdownSetOpen, setIsDropdownSetOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const toggleCollapse = () => setIsCollapsed(!isCollapsed);
  const toggleDropdownMem = () => setIsDropdownMemOpen(!isDropdownMemOpen);
  const toggleDropdownSet = () => setIsDropdownSetOpen(!isDropdownSetOpen);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownMemOpen(false);
        setIsDropdownSetOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);


  const router = useRouter();

  const [show, setShow] = useState(false);

  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);

  const [isDarkMode, setIsDarkMode] = useState(false);
  const [reportText, setReportText] = useState("");
  // 使用 useEffect 来加载之前保存的主题
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark-theme");
      setIsDarkMode(true);
    }
  }, []);

  // 切换主题函数
  const toggleTheme = () => {
    if (isDarkMode) {
      document.documentElement.classList.remove("dark-theme");
      localStorage.setItem("theme", "light"); // 保存主题为 "light"
    } else {
      document.documentElement.classList.add("dark-theme");
      localStorage.setItem("theme", "dark"); // 保存主题为 "dark"
    }
    setIsDarkMode(!isDarkMode);
  };
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    setIsLoggedIn(!!token);
  }, []);

  const handleClick = () => {
    if (isLoggedIn) {
        // ✅ 清除所有登入相關的 localStorage 資料
      localStorage.removeItem("token");
      localStorage.removeItem("account");
      localStorage.removeItem("username");
      alert("登出成功");
      window.location.href = "/"; // ✅ 強制跳回首頁並重新整理
    } else {
      router.push("/login"); // 不登入直接跳 login
    }
  };

  const handleReport = async () => {
    const account = localStorage.getItem("account");

    if (!account) {
      alert("請先登入");
      return;
    }

    let email = "";

    try {
      // 先從後端抓使用者 email
      const res = await axios.get<{ email: string }>(`https://llm.gradaide.xyz/get_email/${account}`);
      email = res.data.email;
      localStorage.setItem("email", email); // 可選：同步儲存
    } catch (err) {
      console.error("無法取得 email", err);
      alert("無法取得使用者信箱，請重新登入");
      return;
    }

    if (reportText.trim().length < 5) {
      alert("請輸入至少 5 個字的問題內容");
      return;
    }

    try {
      const response = await axios.post<{ message: string }>(
        "https://llm.gradaide.xyz/report_issue",
        {
          account,
          email,
          message: reportText.trim()
        }
      );

      alert(response.data.message);
  setReportText("");
  handleClose();
} catch (err) {
  const error = err as AxiosError<{ detail?: string }>;
  alert("回報失敗：" + (error.response?.data?.detail ?? "請稍後再試"));
  console.error(error);
}
  };

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  return (
    <aside className={isCollapsed ? 'collapsed' : 'navbar'}>

      <div className="header-container" style={{ width: '220px' }}>
        {!isCollapsed && (
          <button onClick={() => router.push('/')} className='button'>
            <h1 className="gradAIde">
              Grad<span style={{ color: '#595BD4' }}>AI</span>de.
            </h1>
          </button>
        )}
        <button className="toggle-button arrow" onClick={toggleCollapse} >
          <Image
            src={isCollapsed ? "/img/out.png" : "/img/in.png"}
            alt="Toggle"
            className={`icon-image ${isCollapsed ? 'out-icon' : ''}`}
          />
        </button>
      </div>

      {isCollapsed ? (
        <div className="collapsed-content">
          {isLoggedIn && (
          <Image src="/img/person.png" className="nav-icon-thin" alt="會員專區" />)}
          <Image src="/img/Question.png" className="nav-icon-thin" alt="常見問題" />
          <Image src="/img/use.png" className="nav-icon-thin" alt="使用說明" />
          {isLoggedIn && (
          <Image src="/img/Subtract.png" className="nav-icon-thin" alt="回報問題" />)}
          <Image src="/img/set.png" className="nav-icon-thin" alt="設定" />
          <button className="sticky-bottom-thin" onClick={() => router.push('/login')}>
            <Image src="/img/logout.png" alt="登出" style={{ width: '24px', height: '24px' }} />
          </button>
        </div>
      ) : (
        <nav >
          <ul>

            <li className="dropdown lil">
              {isLoggedIn && (
                <>
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <Image src="/img/person.png" className="nav-icon" alt="會員專區" />
                    會員專區
                    <button className="arrow" style={{ marginLeft: '5em' }} onClick={toggleDropdownMem}>
                      <Image src={isDropdownMemOpen ? "/img/up.png" : "/img/down.png"} alt="Toggle" className="icon-image" />
                    </button>
                  </div>

                  {isDropdownMemOpen && (
                    <ul className="dropdown-menu show">
                      <li className="dropdown-font lil" style={{ fontWeight: 'lighter' }}>
                        <button onClick={() => router.push('/password')} className='button1'>
                          變更密碼
                        </button>
                      </li>
                      <li className="dropdown-font lil" style={{ fontWeight: 'lighter' }}>
                        <button onClick={() => router.push('/name')} className='button1'>
                          變更名稱
                        </button>
                      </li>
                    </ul>
                  )}
                </>
              )}
            </li>

            <button onClick={() => router.push('/question')} className='button'>
              <li className="lil">
                <Image  src="/img/Question.png" className="nav-icon" alt="常見問題" />
                常見問題
              </li>
            </button>
            <button onClick={() => router.push('/direction')} className='button'>
              <li className="lil">
                <Image src="/img/use.png" className="nav-icon" alt="使用說明" />
                使用說明
              </li>
            </button>
            {isLoggedIn && (
              <button onClick={handleShow} className='button'>
                <li className="lil">
                  <Image src="/img/Subtract.png" className="nav-icon" alt="回報問題" />
                  回報問題
                </li>
              </button>
            )}
            {show && (
              <div className="modal-backdrop"></div>
            )}
            <Modal show={show} onHide={handleClose} dialogClassName="custom-modal">
            <div className="modal-header"  style={{paddingLeft:"20px"}}>
                <h1 className='modalfont'>回報問題</h1>
                <button className="close-button" onClick={handleClose}>
                  &times;
                </button>
              </div>
              <div className="modal-content"  style={{paddingLeft:"20px"}}>
                <p>我們將會回覆至您的電子郵件</p>
                <textarea
                  ref={textareaRef}
                  placeholder="請輸入您的問題..."
                  className="modal-text"
                  value={reportText}
                  onChange={(e) => setReportText(e.target.value)}
                  onKeyDown={async (e) => {
                    // ✅ Ctrl + Enter：在游標位置插入換行
                    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                      e.preventDefault(); // 阻止預設行為，手動插入換行

                      const target = textareaRef.current;
                      if (!target) return;

                      const startIdx = target.selectionStart ?? reportText.length;
                      const endIdx = target.selectionEnd ?? reportText.length;

                      const before = reportText.slice(0, startIdx);
                      const after = reportText.slice(endIdx);
                      const newText = `${before}\n${after}`;

                      setReportText(newText);

                      // 讓游標回到換行後的位置
                      setTimeout(() => {
                        target.selectionStart = target.selectionEnd = startIdx + 1;
                      }, 0);

                      return;
                    }

                    // ✅ 單獨 Enter：送出
                    if (e.key === "Enter") {
                      e.preventDefault(); // 阻止換行
                      try {
                        await handleReport();
                      } catch (err) {
                        console.error("送出失敗", err);
                      }
                    }
                  }}
                />

              </div>
              <div className="modal-footer">
                <button className="confirm-button" onClick={handleReport}>
                  確定
                </button>
              </div>
            </Modal>

            <li className="dropdown lil">
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <Image src="/img/set.png" className="nav-icon" alt="設定" />
                設定
                <button className="arrow" style={{ marginLeft: '8em' }} onClick={toggleDropdownSet}>
                  <Image src={isDropdownSetOpen ? "/img/up.png" : "/img/down.png"} alt="Toggle" className="icon-image" />
                </button>
              </div>
              {isDropdownSetOpen && (
                <ul className="dropdown-menu show">
                  <button className='button' onClick={toggleTheme}>
                    <li className='dropdown-font' style={{ fontWeight: 'lighter' }}>
                      {isDarkMode ? (
                        <>
                          <Image src='/img/sun.png' alt="" className='coloricon' />
                          <span style={{ color: "#fff" }}>&nbsp;淺色模式</span>
                        </>
                      ) : (
                        <>
                          <Image src='/img/moon.png' alt="" className='coloricon' />
                          <span>&nbsp;深色模式</span>
                        </>
                      )}
                    </li>
                  </button>
                </ul>
              )}
            </li>
          </ul>
          <button onClick={handleClick} className="sticky-bottom">
            <Image src="/img/logout.png" className="logout-image" alt="登出" />
            <span style={{ paddingLeft: "5px" }}>
              {isLoggedIn ? "登出" : "登入"}
            </span>
          </button>
        </nav>
      )}

    </aside>
  );
}