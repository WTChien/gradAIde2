"use client";
import React, { useState, useEffect, useRef, useCallback } from 'react';
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

// 字體大小設定常數 - 移到元件外部避免重複創建
const FONT_SIZE_CONFIGS = {
  small: {
    name: 'small',
    displayName: '小',
    sizes: {
      messageText: '14px',
      responseText: '14px', 
      userMessage: '14px',
      navText: '16px',
      buttonText: '14px',
      inputText: '14px',
      sendboxText: '14px',
      welcomeTitle: '22px',
      welcomeSubtitle: '12px',
      suggestionsTitle: '14px',
      smallText: '10px',
      errorText: '11px'
    }
  },
  medium: {
    name: 'medium',
    displayName: '中',
    sizes: {
      messageText: '16px',
      responseText: '16px',
      userMessage: '16px', 
      navText: '18px',
      buttonText: '16px',
      inputText: '16px',
      sendboxText: '16px',
      welcomeTitle: '28px',
      welcomeSubtitle: '16px',
      suggestionsTitle: '18px',
      smallText: '12px',
      errorText: '12px'
    }
  },
  large: {
    name: 'large',
    displayName: '大',
    sizes: {
      messageText: '20px',
      responseText: '20px',
      userMessage: '20px',
      navText: '22px',
      buttonText: '18px',
      inputText: '18px',
      sendboxText: '18px',
      welcomeTitle: '32px',
      welcomeSubtitle: '18px',
      suggestionsTitle: '20px',
      smallText: '14px',
      errorText: '14px'
    }
  }
};

// 🔹 修復後的字體大小切換元件 - 解決被遮擋問題
const FontSizeToggle: React.FC<{ compact?: boolean }> = ({ compact = false }) => {
  const [currentSize, setCurrentSize] = useState<string>('medium');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // 套用字體大小到 CSS 變數 - 使用 useCallback 避免重複創建
  const applyFontSize = useCallback((sizeName: string) => {
    const config = FONT_SIZE_CONFIGS[sizeName as keyof typeof FONT_SIZE_CONFIGS];
    if (!config) return;

    const root = document.documentElement;
    
    Object.entries(config.sizes).forEach(([key, value]) => {
      root.style.setProperty(`--font-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`, value);
    });
    
    console.log(`✅ 字體大小已切換為: ${config.displayName} (${sizeName})`);
  }, []);

  // 載入已儲存的字體大小設定
  useEffect(() => {
    const savedSize = localStorage.getItem('fontSize');
    if (savedSize && FONT_SIZE_CONFIGS[savedSize as keyof typeof FONT_SIZE_CONFIGS]) {
      setCurrentSize(savedSize);
      applyFontSize(savedSize);
    } else {
      applyFontSize('medium');
    }
  }, [applyFontSize]);

  // 切換字體大小
  const changeFontSize = useCallback((sizeName: string) => {
    setCurrentSize(sizeName);
    applyFontSize(sizeName);
    localStorage.setItem('fontSize', sizeName);
    setIsDropdownOpen(false);
    
    window.dispatchEvent(new CustomEvent('fontSizeChanged', { 
      detail: { size: sizeName, config: FONT_SIZE_CONFIGS[sizeName as keyof typeof FONT_SIZE_CONFIGS] } 
    }));
  }, [applyFontSize]);

  // 點擊外部關閉下拉選單
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.font-size-toggle')) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  const currentConfig = FONT_SIZE_CONFIGS[currentSize as keyof typeof FONT_SIZE_CONFIGS];

  if (compact) {
    // 緊湊模式：用於設定選單中 - 🔹 修復遮擋問題
    return (
      <div className="font-size-toggle" style={{ 
        position: 'relative', 
        display: 'inline-block',
        // 🔹 確保下拉選單不被遮擋
        zIndex: isDropdownOpen ? 9999 : 'auto'
      }}>
        <button 
          className="font-size-button"
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          title={`字體大小: ${currentConfig.displayName}`}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px',
            background: 'transparent',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            cursor: 'pointer',
            color: 'var(--color)',
            fontSize: '14px',
            minWidth: '34px',
            marginLeft:'12px',
            minHeight: '34px',
            justifyContent: 'space-between',
            transition: 'all 0.2s ease'
          }}
        >
          <span style={{ fontWeight: '500' }}>{currentConfig.displayName}</span>
          <Image
            src={isDropdownOpen ? "/img/up.png" : "/img/down.png"}
            alt="Toggle"
            width={12}
            height={12}
            style={{ opacity: 0.6 }}
          />
        </button>
        
        {isDropdownOpen && (
          <>
            {/* 🔹 添加遮罩層確保下拉選單在最上層 */}
            <div 
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                zIndex: 9998,
                background: 'transparent'
              }}
              onClick={() => setIsDropdownOpen(false)}
            />
            <div 
              className="font-size-dropdown"
              style={{
                position: 'fixed', // 🔹 改為 fixed 定位
                top: 'auto',
                right: 'auto',
                left: 'auto',
                bottom: 'auto',
                // 🔹 動態計算位置
                transform: 'translateX(-50%)',
                background: 'var(--navbackground)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                zIndex: 9999, // 🔹 確保在最上層
                minWidth: '150px',
                marginTop:'8px',
                overflow: 'visible',
                animation: 'dropdownSlideIn 0.2s ease-out'
              }}
              // 🔹 動態設定位置
              ref={(el) => {
                if (el && isDropdownOpen) {
                  // 🔹 使用更安全的方式獲取按鈕元素
                  const toggle = el.parentElement;
                  const button = toggle?.querySelector('.font-size-button') as HTMLElement;
                  if (button) {
                    const rect = button.getBoundingClientRect();
                    el.style.left = `${rect.left + rect.width / 2}px`;
                    el.style.top = `${rect.bottom + 4}px`;
                  }
                }
              }}
            >
              <div style={{
                padding: '8px 12px',
                background: 'var(--loginbg)',
                borderBottom: '1px solid var(--border)',
                fontSize: '12px',
                fontWeight: '600',
                color: 'var(--color)',
                opacity: '0.8'
              }}>
                選擇字體大小
              </div>
              {Object.values(FONT_SIZE_CONFIGS).map((config) => (
                <button
                  key={config.name}
                  onClick={() => changeFontSize(config.name)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    width: '100%',
                    padding: '12px 14px',
                    background: currentSize === config.name ? 'var(--loginbg)' : 'none',
                    border: 'none',
                    textAlign: 'left',
                    cursor: 'pointer',
                    color: currentSize === config.name ? 'var(--loginbutton)' : 'var(--color)',
                    fontSize: '14px',
                    fontWeight: currentSize === config.name ? '600' : '500',
                    transition: 'all 0.2s ease',
                    minHeight: '42px'
                  }}
                  onMouseEnter={(e) => {
                    if (currentSize !== config.name) {
                      e.currentTarget.style.background = 'var(--hover)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (currentSize !== config.name) {
                      e.currentTarget.style.background = 'none';
                    }
                  }}
                >
                  <span style={{ flex: 1 }}>{config.displayName}字體</span>
                  {currentSize === config.name && (
                    <span style={{ color: 'var(--loginbutton)', fontSize: '16px' }}>✓</span>
                  )}
                </button>
              ))}
            </div>
          </>
        )}

        <style jsx>{`
          @keyframes dropdownSlideIn {
            from {
              opacity: 0;
              transform: translateX(-50%) translateY(-8px);
            }
            to {
              opacity: 1;
              transform: translateX(-50%) translateY(0);
            }
          }

          .font-size-button:hover {
            background: var(--hover) !important;
            border-color: var(--loginbutton) !important;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(89, 91, 212, 0.15);
          }
        `}</style>
      </div>
    );
  }

  // 完整模式：用於縮小導航欄
  return (
    <div className="font-size-toggle" style={{ position: 'relative', display: 'inline-block' }}>
      <button 
        className="font-size-button"
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        title={`目前字體大小: ${currentConfig.displayName}`}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '10px 16px',
          background: 'var(--navbackground)',
          border: '1px solid var(--border)',
          borderRadius: '10px',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          color: 'var(--color)',
          fontSize: '15px',
          fontWeight: '500',
          minWidth: '100px',
          minHeight: '44px',
          justifyContent: 'space-between'
        }}
      >
        <span style={{ fontSize: '14px', flex: 1, textAlign: 'center', fontWeight: '600' }}>
          {currentConfig.displayName}
        </span>
        <Image
          src={isDropdownOpen ? "/img/up.png" : "/img/down.png"}
          alt="Toggle"
          width={16}
          height={16}
          style={{ opacity: 0.7, transition: 'transform 0.2s ease' }}
        />
      </button>
      
      {isDropdownOpen && (
        <div 
          className="font-size-dropdown"
          style={{
            position: 'absolute',
            top: 'calc(100% + 4px)',
            left: '0',
            right: '0',
            background: 'var(--navbackground)',
            border: '1px solid var(--border)',
            borderRadius: '10px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            zIndex: 1000,
            minWidth: '200px',
            overflow: 'hidden',
            animation: 'dropdownSlideIn 0.2s ease-out'
          }}
        >
          <div style={{
            padding: '10px 16px',
            background: 'var(--loginbg)',
            borderBottom: '1px solid var(--border)',
            fontSize: '13px',
            fontWeight: '600',
            color: 'var(--color)',
            opacity: '0.8'
          }}>
            選擇字體大小
          </div>
          {Object.values(FONT_SIZE_CONFIGS).map((config) => (
            <button
              key={config.name}
              onClick={() => changeFontSize(config.name)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                width: '100%',
                padding: '14px 16px',
                background: currentSize === config.name ? 'var(--loginbg)' : 'none',
                border: 'none',
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                color: currentSize === config.name ? 'var(--loginbutton)' : 'var(--color)',
                fontWeight: currentSize === config.name ? '600' : 'normal',
                minHeight: '50px'
              }}
            >
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: '3px' }}>
                <span style={{ fontSize: '14px', fontWeight: '500' }}>
                  {config.displayName}字體
                </span>
                <span style={{ fontSize: '12px', opacity: '0.7' }}>
                  ({config.sizes.messageText})
                </span>
              </div>
              {currentSize === config.name && (
                <span style={{ color: 'var(--loginbutton)', fontSize: '16px', fontWeight: 'bold' }}>
                  ✓
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      <style jsx>{`
        @keyframes dropdownSlideIn {
          from {
            opacity: 0;
            transform: translateY(-8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .font-size-button:hover {
          background: var(--hover) !important;
          border-color: var(--loginbutton) !important;
          transform: translateY(-1px);
          box-shadow: 0 3px 10px rgba(89, 91, 212, 0.2);
        }

        .font-size-dropdown button:hover {
          background: var(--hover) !important;
          transform: translateX(2px);
        }

        @media screen and (max-width: 768px) {
          .font-size-button {
            padding: 8px 12px !important;
            font-size: 13px !important;
            min-width: 85px !important;
            min-height: 38px !important;
          }

          .font-size-dropdown {
            min-width: 170px !important;
          }

          .font-size-dropdown button {
            padding: 12px 14px !important;
            min-height: 46px !important;
          }
        }
      `}</style>
    </div>
  );
};

// 🆕 新增上传统计组件 - 从 sendbox 移植而来，支持真实数据
const UploadStats: React.FC<{ isCollapsed: boolean }> = ({ isCollapsed }) => {
  // 🔹 使用与 sendbox 相同的接口和状态管理
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

  // 🔹 从 sendbox 移植的 API 调用函数
  const fetchUploadInfo = useCallback(async () => {
    if (!account) return null;
    
    try {
      console.log("📊 获取用户上传信息...");
      const response = await axios.post('https://llm.gradaide.xyz/pre_upload_check', {
        account: account
      }, {
        timeout: 10000
      });
      
      const info = response.data;
      console.log("✅ 用户上传信息:", info);
      
      if (info.is_admin) {
        console.log("🔑 检测到管理员身份，无限上传权限");
      }
      
      setUploadInfo(info);
      return info;
    } catch (error) {
      console.error("❌ 获取上传信息失败:", error);
      return null;
    }
  }, [account]);

  // 初始化和定期刷新
  useEffect(() => {
    if (account && !uploadInfo) {
      fetchUploadInfo();
    }
  }, [account, uploadInfo, fetchUploadInfo]);

  // 如果是折叠状态，不显示统计
  if (isCollapsed) {
    return null;
  }

  // 如果没有登录或没有数据，不显示
  if (!account || !uploadInfo) {
    return null;
  }

  // 展开状态：显示完整的上传统计信息
  return (
    <div className="upload-stats" style={{
      padding: '12px',
      borderRadius: '10px',
      background: 'linear-gradient(135deg, var(--navbackground) 0%, var(--loginbg) 100%)',
      border: '1px solid var(--border)',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
      transition: 'all 0.3s ease',
      cursor: 'pointer',
      width: '210px', // 🔹 修改：限制最大宽度，适合navbar(250px)
    }}
    onClick={fetchUploadInfo}
    title="點擊刷新統計"
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateY(-2px)';
      e.currentTarget.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.15)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
    }}
    >
      {/* 标题和图标 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px', // 🔹 修改：减小间距
        marginBottom: '10px' // 🔹 修改：减小底部边距
      }}>
        <span style={{ fontSize: '14px' }}>📊</span>
        <span style={{
          fontSize: '13px', // 🔹 修改：减小字体
          fontWeight: '600',
          color: 'var(--color)'
        }}>
          上傳統計
        </span>
        {uploadInfo.is_admin && (
          <span style={{
            fontSize: '9px', // 🔹 修改：减小字体
            padding: '1px 4px', // 🔹 修改：减小padding
            color: '#000',
            borderRadius: '3px',
            fontWeight: '600'
          }}>
            👑
          </span>
        )}
        <span style={{
          fontSize: '10px', // 🔹 修改：减小字体
          color: 'var(--color)',
          opacity: '0.7',
          marginLeft: 'auto' // 🔹 修改：推到右边
        }}>
          ({uploadInfo.user_type})
        </span>
      </div>

      {/* 使用情况网格 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '6px', // 🔹 修改：减小间距
        marginBottom: '10px' // 🔹 修改：减小底部边距
      }}>
        <div style={{
          fontSize: '11px', // 🔹 修改：减小字体
          color: 'var(--color)',
          opacity: '0.8'
        }}>
          今日: {uploadInfo.today_usage}/
          {typeof uploadInfo.limits.daily_uploads === 'number' 
            ? uploadInfo.limits.daily_uploads 
            : uploadInfo.limits.daily_uploads}
        </div>
        <div style={{
          fontSize: '11px', // 🔹 修改：减小字体
          color: 'var(--color)',
          opacity: '0.8'
        }}>
          剩餘: {typeof uploadInfo.remaining_uploads === 'number' 
            ? uploadInfo.remaining_uploads 
            : uploadInfo.remaining_uploads} 次
        </div>
      </div>

      {/* 进度条 */}
      <div style={{
        width: '100%',
        height: '5px', // 🔹 修改：减小高度
        background: 'var(--border)',
        borderRadius: '3px',
        overflow: 'hidden',
        marginBottom: '8px' // 🔹 修改：减小底部边距
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
          borderRadius: '3px',
          transition: 'width 0.3s ease'
        }} />
      </div>

      {/* 底部信息行 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        {/* 文件限制 */}
        <div style={{
          fontSize: '10px', // 🔹 修改：减小字体
          color: 'var(--color)',
          opacity: '0.7'
        }}>
          限制: {(uploadInfo.limits.max_file_size / 1024 / 1024).toFixed(1)}MB
        </div>

        {/* 状态指示器 */}
        {!uploadInfo.can_upload && !uploadInfo.is_admin ? (
          <div style={{ 
            color: '#e74c3c',
            fontSize: '9px', // 🔹 修改：减小字体
            padding: '2px 4px', // 🔹 修改：减小padding
            backgroundColor: 'rgba(231, 76, 60, 0.1)',
            borderRadius: '4px',
            border: '1px solid rgba(231, 76, 60, 0.2)'
          }}>
            ⚠️ 已達限制
          </div>
        ) : uploadInfo.is_admin ? (
          <div style={{ 
            color: '#27ae60',
            fontSize: '9px', // 🔹 修改：减小字体
            padding: '2px 4px', // 🔹 修改：减小padding
            backgroundColor: 'rgba(39, 174, 96, 0.1)',
            borderRadius: '4px',
            border: '1px solid rgba(39, 174, 96, 0.2)'
          }}>
            ✨ 無限制
          </div>
        ) : (
          <div style={{ 
            color: '#27ae60',
            fontSize: '9px', // 🔹 修改：减小字体
            padding: '2px 4px', // 🔹 修改：减小padding
            backgroundColor: 'rgba(39, 174, 96, 0.1)',
            borderRadius: '4px',
            border: '1px solid rgba(39, 174, 96, 0.2)'
          }}>
            ✅ 可用
          </div>
        )}
      </div>
    </div>
  );
};

export default function NavBar() {
  const [isDropdownMemOpen, setIsDropdownMemOpen] = useState(false);
  const [isDropdownSetOpen, setIsDropdownSetOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 更新CSS變數的函數 - 使用 useCallback 避免重複創建
  const updateNavbarWidth = useCallback((collapsed: boolean) => {
    const root = document.documentElement;
    if (collapsed) {
      root.style.setProperty('--nav-width', '80px');
      root.style.setProperty('--nav-offset', '40px');
      root.style.setProperty('--sidebar-width', '80px');
      document.body.className = 'nav-collapsed';
    } else {
      root.style.setProperty('--nav-width', '250px');
      root.style.setProperty('--nav-offset', '125px');
      root.style.setProperty('--sidebar-width', '250px');
      document.body.className = '';
    }
  }, []);

  const toggleCollapse = useCallback(() => {
    const newCollapsedState = !isCollapsed;
    setIsCollapsed(newCollapsedState);
    updateNavbarWidth(newCollapsedState);
  }, [isCollapsed, updateNavbarWidth]);

  // 初始化時設定CSS變數
  useEffect(() => {
    updateNavbarWidth(isCollapsed);
  }, [isCollapsed, updateNavbarWidth]);

  const toggleDropdownMem = useCallback(() => setIsDropdownMemOpen(!isDropdownMemOpen), [isDropdownMemOpen]);
  const toggleDropdownSet = useCallback(() => setIsDropdownSetOpen(!isDropdownSetOpen), [isDropdownSetOpen]);

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

  const handleClose = useCallback(() => setShow(false), []);
  const handleShow = useCallback(() => setShow(true), []);

  const [isDarkMode, setIsDarkMode] = useState(false);
  const [reportText, setReportText] = useState("");
  
  // 載入之前保存的主題
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark-theme");
      setIsDarkMode(true);
    }
  }, []);

  // 切换主题函数
  const toggleTheme = useCallback(() => {
    if (isDarkMode) {
      document.documentElement.classList.remove("dark-theme");
      localStorage.setItem("theme", "light");
    } else {
      document.documentElement.classList.add("dark-theme");
      localStorage.setItem("theme", "dark");
    }
    setIsDarkMode(!isDarkMode);
  }, [isDarkMode]);

  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    setIsLoggedIn(!!token);
  }, []);

  const handleClick = useCallback(() => {
    if (isLoggedIn) {
      localStorage.removeItem("token");
      localStorage.removeItem("account");
      localStorage.removeItem("username");
      localStorage.removeItem("admission_year");
      alert("登出成功");
      window.location.href = "/";
    } else {
      router.push("/login");
    }
  }, [isLoggedIn, router]);

  const handleReport = useCallback(async () => {
    const account = localStorage.getItem("account");

    if (!account) {
      alert("請先登入");
      return;
    }

    let email = "";

    try {
      const res = await axios.get<{ email: string }>(`https://llm.gradaide.xyz/get_email/${account}`);
      email = res.data.email;
      localStorage.setItem("email", email);
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
  }, [reportText, handleClose]);

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
            width={24}
            height={24}
          />
        </button>
      </div>

      {isCollapsed ? (
        <div className="collapsed-content">
          {isLoggedIn && (
          <Image src="/img/person.png" className="nav-icon-thin" alt="會員專區" width={24} height={24} />)}
          <Image src="/img/Question.png" className="nav-icon-thin" alt="常見問題" width={24} height={24} />
          <Image src="/img/use.png" className="nav-icon-thin" alt="使用說明" width={24} height={24} />
          {isLoggedIn && (
          <Image src="/img/Subtract.png" className="nav-icon-thin" alt="回報問題" width={24} height={24} />)}
          <Image src="/img/set.png" className="nav-icon-thin" alt="設定" width={24} height={24} />
          
          {/* 🆕 折叠状态下不显示上传统计，保持简洁 */}
          
          <button className="sticky-bottom-thin" onClick={() => router.push('/login')}>
            <Image src="/img/logout.png" alt="登出" style={{ width: '24px', height: '24px' }} width={24} height={24} />
          </button>
        </div>
      ) : (
        <nav style={{ 
          display: 'flex', 
          flexDirection: 'column',
          height: 'calc(100vh - 80px)', // 减去头部高度
          overflow: 'hidden'
        }}>
          <ul style={{ 
            flex: '1',
            overflowY: 'auto',
            paddingBottom: '20px'
          }}>
            <li className="dropdown lil">
              {isLoggedIn && (
                <>
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <Image src="/img/person.png" className="nav-icon" alt="會員專區" width={24} height={24} />
                    會員專區
                    <button className="arrow" style={{ marginLeft: '5em' }} onClick={toggleDropdownMem}>
                      <Image src={isDropdownMemOpen ? "/img/up.png" : "/img/down.png"} alt="Toggle" className="icon-image" width={24} height={24} />
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
                <Image  src="/img/Question.png" className="nav-icon" alt="常見問題" width={24} height={24} />
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
              <button onClick={handleShow} className='button'>
                <li className="lil">
                  <Image src="/img/Subtract.png" className="nav-icon" alt="回報問題" width={24} height={24} />
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
                    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                      e.preventDefault();

                      const target = textareaRef.current;
                      if (!target) return;

                      const startIdx = target.selectionStart ?? reportText.length;
                      const endIdx = target.selectionEnd ?? reportText.length;

                      const before = reportText.slice(0, startIdx);
                      const after = reportText.slice(endIdx);
                      const newText = `${before}\n${after}`;

                      setReportText(newText);

                      setTimeout(() => {
                        target.selectionStart = target.selectionEnd = startIdx + 1;
                      }, 0);

                      return;
                    }

                    if (e.key === "Enter") {
                      e.preventDefault();
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
                <Image src="/img/set.png" className="nav-icon" alt="設定" width={24} height={24} />
                設定
                <button className="arrow" style={{ marginLeft: '8em' }} onClick={toggleDropdownSet}>
                  <Image src={isDropdownSetOpen ? "/img/up.png" : "/img/down.png"} alt="Toggle" className="icon-image" width={24} height={24} />
                </button>
              </div>
              {/* 🔹 修復設定選單容器的 overflow 問題 */}
              {isDropdownSetOpen && (
                <ul 
                  className="dropdown-menu show"
                  style={{
                    // 🔹 確保內容不被裁切
                    overflow: 'visible',
                    position: 'relative',
                    zIndex: 1
                  }}
                >
                  {/* 🔹 主題切換 */}
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
                  
                  {/* 🔹 修復後的字體大小切換區域 */}
                  <li className='dropdown-font' style={{ 
                    fontWeight: 'lighter',
                    paddingLeft: '32px',
                    paddingRight: '18px',
                    paddingTop: '8px',
                    paddingBottom: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    minHeight: '40px',
                    // 🔹 確保字體切換器的下拉選單不被遮擋
                    position: 'relative',
                    overflow: 'visible',
                    zIndex: 2
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}>
                       {isDarkMode ? (
                        <>
                          <Image src='/img/alp.png' alt="" className='coloricon' width={24} height={24} />
                          <span style={{ color: "#fff" }}>字體大小</span>
                        </>
                      ) : (
                        <>
                          <Image src='/img/alphabet.png' alt="" className='coloricon' width={24} height={24} />
                          <span>字體大小</span>
                        </>
                      )}
                    </div>
                    <FontSizeToggle compact={true} />
                  </li>
                </ul>
              )}
            </li>
          </ul>
          
          {/* 🆕 底部区域：上传统计 + 登出按钮 */}
          <div style={{ justifyContent: 'center', marginBottom: '80px' }}>
            {/* 🆕 展开状态下的上传统计 - 仅在登录时显示 */}
            {isLoggedIn && <UploadStats isCollapsed={false} />}
            
            {/* 登出按钮 */}
            <button onClick={handleClick} className="sticky-bottom" style={{
              
            }}>
              <Image src="/img/logout.png" className="logout-image" alt="登出" width={24} height={24} />
              <span style={{ paddingLeft: "5px" }}>
                {isLoggedIn ? "登出" : "登入"}
              </span>
            </button>
          </div>
        </nav>
      )}
      
      {/* 🔹 添加全局樣式來確保下拉選單正確顯示 */}
      <style jsx global>{`
        /* 確保設定選單容器不會裁切內容 */
        .dropdown-menu {
          overflow: visible !important;
          position: relative !important;
        }
        
        /* 確保導航欄容器允許內容溢出 */
        .navbar, .collapsed {
          overflow: visible !important;
        }
        
        nav {
          overflow: visible !important;
        }
        
        nav ul {
          overflow: visible !important;
        }
        
        nav ul li {
          overflow: visible !important;
        }
        
        /* 確保字體切換器的下拉選單在最上層 */
        .font-size-toggle {
          overflow: visible !important;
        }
        
        .font-size-dropdown {
          overflow: visible !important;
        }

        /* 🆕 上传统计样式 */
        .upload-stats:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15) !important;
        }

        .upload-stats-collapsed:hover {
          transform: translateY(-1px);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        /* 响应式设计 */
        @media screen and (max-width: 768px) {
          .upload-stats {
            padding: 12px !important;
            margin: 8px 0 !important;
          }
          
          .upload-stats-collapsed {
            padding: 8px !important;
            margin: 6px 0 !important;
          }
        }
      `}</style>
    </aside>
  );
}