"use client";
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import './style.css';
import './name/name.css';
import './login/login.css';
import './password/password.css';
import './forget/forget.css';
import axios from 'axios';
import { Modal} from 'react-bootstrap';
import Image from 'next/image';

export default function Topph() {
    const router = useRouter();
    const [isNavOpen, setIsNavOpen] = useState(false);
    const navRef = useRef<HTMLDivElement>(null);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [showConfirmClear, setShowConfirmClear] = useState(false);


    // 切換 NavBar 顯示狀態
    const toggleNav = () => {
        setIsNavOpen((prev) => {
            if (!prev) {
                setShow(false); // 關閉 Modal
            }
            return !prev;
        });
    };

    // 點擊外部時關閉 NavBar
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (navRef.current && !navRef.current.contains(event.target as Node)) {
                setIsNavOpen(false);
            }
        };
    const token = localStorage.getItem("token");
    setIsLoggedIn(!!token);
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);
    const [isDropdownMemOpen, setIsDropdownMemOpen] = useState(false);
    const [isDropdownSetOpen, setIsDropdownSetOpen] = useState(false);
    const [isCollapsed] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // State for titles and editing functionality
   
    // Toggle collapse

    // Toggle dropdown menus
    const toggleDropdownMem = () => setIsDropdownMemOpen(!isDropdownMemOpen);
    const toggleDropdownSet = () => setIsDropdownSetOpen(!isDropdownSetOpen);

   

    // Close dropdowns when clicking outside
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

    // Handle editing title
   

    
   
   


    const [show, setShow] = useState(false);

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const [isDarkMode, setIsDarkMode] = useState(false);

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

    const [username, setUsername] = useState("同學");

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

    const handleStorageChange = () => {
        fetchUsername();
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
    }, []);
    const updateHeight = () => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
      };
      
      updateHeight();
      window.addEventListener('resize', updateHeight);
      
    return (
        <div className="header" ref={navRef}>
            <div className={`overlay ${isNavOpen ? "show" : ""}`} onClick={() => setIsNavOpen(false)}></div>

            {/* 點擊圖示展開或收起 NavBar */}
            <button className="add">
                <Image
                    src="/img/therr.png"
                    className="addicon"
                    onClick={toggleNav}
                    alt="展開導覽列"
                />
                <Image
                    src="/img/Write.png"
                    className="addicon"
                    onClick={() => setShowConfirmClear(true)}
                    alt="開始新對話"
                />

            </button>

            <b className="addfont">HI, {username}</b>


            {/* 根據 isNavOpen 決定是否顯示 NavBar */}
            {isNavOpen && (
                <aside className={`navbar ${isNavOpen ? "open" : ""}`}>
                    <div className="header-container" style={{ width: '220px' }}>
                        {!isCollapsed && (
                            <button onClick={() => router.push('/')} className='button'>
                                <h1 className="gradAIde">
                                    Grad<span style={{ color: '#595BD4' }}>AI</span>de.
                                </h1>
                            </button>
                        )}
                    </div>
                    <nav >
                        <ul>
                        {isLoggedIn && (
  <li className="dropdown lil">
    <div style={{ display: 'flex', alignItems: 'center' }} onClick={toggleDropdownMem}>
      <Image src="/img/person.png" className="nav-icon" alt="會員專區" />
      會員專區
      <button className="arrow" style={{ marginLeft: '5em' }} onClick={toggleDropdownMem}>
        <Image src={isDropdownMemOpen ? "/img/up.png" : "/img/down.png"} alt="Toggle" className="icon-image" />
      </button>
    </div>
    {isDropdownMemOpen && (
      <ul className="dropdown-menu show">
        <li className="dropdown-font lil" style={{ fontWeight: 'lighter' }}>
          <button onClick={() => router.push('/password')} className='button1' style={{fontSize:"16px"}}>變更密碼</button>
        </li>
        <li className="dropdown-font lil" style={{ fontWeight: 'lighter' }}>
          <button onClick={() => router.push('/name')} className='button1' style={{fontSize:"16px"}}>變更名稱</button>
        </li>
      </ul>
    )}
  </li>
)}

                            <button onClick={() => router.push('/question')} className='button'>
                                <li className="lil">
                                    <Image src="/img/Question.png" className="nav-icon" alt="常見問題" />
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
  <>
    <button onClick={handleShow} className='button'>
      <li className="lil">
        <Image src="/img/Subtract.png" className="nav-icon" alt="回報問題" />
        回報問題
      </li>
    </button>
    {show && (
      <div className="modal-backdrop"></div>
    )}
    <Modal
      show={show}
      onHide={handleClose}
      backdrop={true}
      keyboard={true}
      dialogClassName="custom-modal"
    >
      <div className="modal-header">
        <h1 className='modalfont'>回報問題</h1>
        <button className="close-button" onClick={handleClose}>&times;</button>
      </div>
      <div className="modal-content">
        <p>我們將會回覆至您的電子郵件</p>
        <textarea placeholder="請輸入您的問題..." className="modal-text" />
      </div>
      <div className="modal-footer">
        <button className="confirm-button" onClick={handleClose}>確定</button>
      </div>
    </Modal>
  </>
)}



                            <li className="dropdown lil" >
                                <div style={{ display: 'flex', alignItems: 'center' }} onClick={toggleDropdownSet}>
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
                        <button
                            onClick={() => {
                                if (isLoggedIn) {
                                localStorage.removeItem("token");
                                localStorage.removeItem("account");
                                localStorage.removeItem("username");
                                alert("登出成功");
                                window.location.href = "/";
                                } else {
                                router.push("/login");
                                }
                            }}
                            className="sticky-bottom"
                            >
                            <Image src="/img/logout.png" className="logout-image" alt={isLoggedIn ? "登出" : "登入"} />
                            <span style={{ paddingLeft: '5px' }}>
                                {isLoggedIn ? "登出" : "登入"}
                            </span>
                            </button>

                    </nav>
                </aside>
            )}
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
                <div className="modal-footer" >
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
