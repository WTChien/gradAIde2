"use client";
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import './style.css';
import './name/name.css';
import './login/login.css';
import './password/password.css';
import './forget/forget.css';
import axios from 'axios';
import { Modal} from 'react-bootstrap';
import Image from 'next/image';

// 🆕 添加上传统计组件 - 手机版
const MobileUploadStats: React.FC = () => {
  const [uploadInfo, setUploadInfo] = useState<{
    can_upload: boolean;
    user_type: string;
    limits: {
      daily_uploads: number | string;
      max_file_size: number;
    };
    today_usage: number;
    remaining_uploads: number | string;
    statistics: {
      today: number;
      week: number;
      month: number;
      total: number;
      last_upload: string | null;
    };
    is_admin?: boolean;
  } | null>(null);
  
  const account = typeof window !== 'undefined' ? (localStorage.getItem("account") || "") : "";

  // 获取上传信息
  const fetchUploadInfo = useCallback(async () => {
    if (!account) return null;
    
    try {
      console.log("📊 [手机版] 获取用户上传信息...");
      const response = await axios.post('https://llm.gradaide.xyz/pre_upload_check', {
        account: account
      }, {
        timeout: 10000
      });
      
      const info = response.data;
      console.log("✅ [手机版] 用户上传信息:", info);
      
      setUploadInfo(info);
      return info;
    } catch (error) {
      console.error("❌ [手机版] 获取上传信息失败:", error);
      return null;
    }
  }, [account]);

  // 初始化
  useEffect(() => {
    if (account && !uploadInfo) {
      fetchUploadInfo();
    }
  }, [account, uploadInfo, fetchUploadInfo]);

  // 如果没有登录或没有数据，不显示
  if (!account || !uploadInfo) {
    return null;
  }

  // 手机版上传统计显示
  return (
    <div style={{
      padding: '10px 12px', // 🔹 修改：减小padding
      margin: '0 12px 10px 12px', // 🔹 修改：左右边距12px，底部边距10px避免重叠
      borderRadius: '8px', // 🔹 修改：减小圆角
      border: '1px solid var(--border)',
      boxShadow: '0 2px 6px rgba(0, 0, 0, 0.08)',
      cursor: 'pointer',
      maxWidth: '210px', // 🔹 修改：限制最大宽度
    }}
    onClick={fetchUploadInfo}
    title="点击刷新统计"
    >
      {/* 标题行 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '8px' // 🔹 修改：减小底部边距
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '5px' // 🔹 修改：减小间距
        }}>
          <span style={{ fontSize: '13px' }}>📊</span> {/* 🔹 修改：减小字体 */}
          <span style={{
            fontSize: '12px', // 🔹 修改：减小字体
            fontWeight: '600',
            color: 'var(--color)'
          }}>
            上傳統計
          </span>
          {uploadInfo.is_admin && (
            <span style={{
              fontSize: '8px', // 🔹 修改：减小字体
              padding: '1px 3px', // 🔹 修改：减小padding
              color: '#000',
              borderRadius: '2px', // 🔹 修改：减小圆角
              fontWeight: '600'
            }}>
              👑
            </span>
          )}
        </div>
        <span style={{
          fontSize: '10px', // 🔹 修改：减小字体
          color: 'var(--color)',
          opacity: '0.7'
        }}>
          ({uploadInfo.user_type})
        </span>
      </div>

      {/* 使用情况 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '6px' // 🔹 修改：减小底部边距
      }}>
        <span style={{
          fontSize: '10px', // 🔹 修改：减小字体
          color: 'var(--color)',
          opacity: '0.8'
        }}>
          今日: {uploadInfo.today_usage}/
          {typeof uploadInfo.limits.daily_uploads === 'number' 
            ? uploadInfo.limits.daily_uploads 
            : uploadInfo.limits.daily_uploads}
        </span>
        <span style={{
          fontSize: '10px', // 🔹 修改：减小字体
          color: 'var(--color)',
          opacity: '0.8'
        }}>
          剩余: {typeof uploadInfo.remaining_uploads === 'number' 
            ? uploadInfo.remaining_uploads 
            : uploadInfo.remaining_uploads} 次
        </span>
      </div>

      {/* 简化的进度条 */}
      <div style={{
        width: '100%',
        height: '3px', // 🔹 修改：减小高度
        background: 'var(--border)',
        borderRadius: '2px',
        overflow: 'hidden',
        marginBottom: '6px' // 🔹 修改：减小底部边距
      }}>
        <div style={{
          width: `${(() => {
            const today = uploadInfo.today_usage;
            const limit = typeof uploadInfo.limits.daily_uploads === 'number' 
              ? uploadInfo.limits.daily_uploads 
              : 100;
            return Math.min((today / limit) * 100, 100);
          })()}%`,
          height: '100%',
          background: uploadInfo.is_admin 
            ? 'linear-gradient(90deg, #ffd700 0%, #ffed4a 100%)' 
            : 'linear-gradient(90deg, #4ade80 0%, #22d3ee 100%)',
          borderRadius: '2px',
          transition: 'width 0.3s ease'
        }} />
      </div>

      {/* 状态指示器 - 简化版 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span style={{
          fontSize: '9px', // 🔹 修改：减小字体
          color: 'var(--color)',
          opacity: '0.7'
        }}>
          限制: {(uploadInfo.limits.max_file_size / 1024 / 1024).toFixed(1)}MB
        </span>
        
        {!uploadInfo.can_upload && !uploadInfo.is_admin ? (
          <span style={{ 
            color: '#e74c3c',
            fontSize: '9px', // 🔹 修改：减小字体
            padding: '1px 4px', // 🔹 修改：减小padding
            backgroundColor: 'rgba(231, 76, 60, 0.1)',
            borderRadius: '3px', // 🔹 修改：减小圆角
            border: '1px solid rgba(231, 76, 60, 0.2)'
          }}>
            ⚠️ 已達限制
          </span>
        ) : uploadInfo.is_admin ? (
          <span style={{ 
            color: '#27ae60',
            fontSize: '9px', // 🔹 修改：减小字体
            padding: '1px 4px', // 🔹 修改：减小padding
            backgroundColor: 'rgba(39, 174, 96, 0.1)',
            borderRadius: '3px', // 🔹 修改：减小圆角
            border: '1px solid rgba(39, 174, 96, 0.2)'
          }}>
            ✨ 無限制
          </span>
        ) : (
          <span style={{ 
            color: '#27ae60',
            fontSize: '9px', // 🔹 修改：减小字体
            padding: '1px 4px', // 🔹 修改：减小padding
            backgroundColor: 'rgba(39, 174, 96, 0.1)',
            borderRadius: '3px', // 🔹 修改：减小圆角
            border: '1px solid rgba(39, 174, 96, 0.2)'
          }}>
            ✅ 可用
          </span>
        )}
      </div>
    </div>
  );
};

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
                    width={24}
                    height={24}
                />
                <Image
                    src="/img/Write.png"
                    className="addicon"
                    onClick={() => setShowConfirmClear(true)}
                    alt="開始新對話"
                    width={24}
                    height={24}
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
                    
                    {/* 🔹 修改：添加滚动容器和底部区域布局 */}
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      height: 'calc(100vh - 80px)', // 减去头部高度
                      overflow: 'hidden'
                    }}>
                      {/* 滚动内容区域 */}
                      <div style={{
                        flex: '1',
                        overflowY: 'auto',
                        paddingBottom: '20px'
                      }}>
                        <nav>
                            <ul>
                            {isLoggedIn && (
                              <li className="dropdown lil">
                                <div style={{ display: 'flex', alignItems: 'center' }} onClick={toggleDropdownMem}>
                                  <Image src="/img/person.png" className="nav-icon" alt="會員專區" width={24} height={24} />
                                  會員專區
                                  <button className="arrow" style={{ marginLeft: '5em' }} onClick={toggleDropdownMem}>
                                    <Image src={isDropdownMemOpen ? "/img/up.png" : "/img/down.png"} alt="Toggle" className="icon-image" width={24} height={24} />
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
                                        <Image src="/img/Question.png" className="nav-icon" alt="常見問題" width={24} height={24} />
                                        常見問題
                                    </li>
                                </button>
                                <button onClick={() => router.push('/direction')} className='button'>
                                    <li className="lil">
                                        <Image src="/img/use.png" className="nav-icon" alt="使用說明" width={24} height={24} />
                                        使用說明
                                    </li>
                                </button>
                                {isLoggedIn && (
                                  <>
                                    <button onClick={handleShow} className='button'>
                                      <li className="lil">
                                        <Image src="/img/Subtract.png" className="nav-icon" alt="回報問題" width={24} height={24} />
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
                                        <Image src="/img/set.png" className="nav-icon" alt="設定" width={24} height={24} />
                                        設定
                                        <button className="arrow" style={{ marginLeft: '8em' }} onClick={toggleDropdownSet}>
                                            <Image src={isDropdownSetOpen ? "/img/up.png" : "/img/down.png"} alt="Toggle" className="icon-image" width={24} height={24} />
                                        </button>
                                    </div>
                                    {isDropdownSetOpen && (
                                        <ul className="dropdown-menu show">
                                            <button className='button' onClick={toggleTheme}>
                                                <li className='dropdown-font' style={{ fontWeight: 'lighter' }}>
                                                    {isDarkMode ? (
                                                        <>
                                                            <Image src='/img/sun.png' alt="" className='coloricon' width={22} height={22} />
                                                            <span style={{ color: "#fff" }}>&nbsp;淺色模式</span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Image src='/img/moon.png' alt="" className='coloricon' width={22} height={22} />
                                                            <span>&nbsp;深色模式</span>
                                                        </>
                                                    )}
                                                </li>
                                            </button>
                                        </ul>
                                    )}
                                </li>
                            </ul>
                        </nav>
                      </div>
                      
                      {/* 🆕 底部区域：上传统计 + 登出按钮 */}
                      <div style={{
                        marginBottom:'70px'
                      }}>
                        {/* 🆕 手机版上传统计 - 仅在登录时显示 */}
                        {isLoggedIn && <MobileUploadStats />}
                        
                        {/* 登出按钮 */}
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
                            style={{
                             
                            }}
                        >
                            <Image src="/img/logout.png" className="logout-image" alt={isLoggedIn ? "登出" : "登入"} width={24} height={24} />
                            <span style={{ paddingLeft: '5px' }}>
                                {isLoggedIn ? "登出" : "登入"}
                            </span>
                        </button>
                      </div>
                    </div>
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