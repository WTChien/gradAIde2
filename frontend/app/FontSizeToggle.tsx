// 改善後的 FontSizeToggle 元件 - 加大點擊區域並修復 ESLint 警告
"use client";
import React, { useState, useEffect, useCallback } from 'react';
import Image from 'next/image';

// 字體大小設定常數 - 移到元件外部避免重複創建
const FONT_SIZE_CONFIGS = {
  small: {
    name: 'small',
    displayName: '小',
    icon: '🔍',
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
    icon: '📝',
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
    icon: '📖',
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

// 🔹 改善後的字體大小切換元件
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
  }, [applyFontSize]); // 添加 applyFontSize 依賴

  // 切換字體大小 - 使用 useCallback 避免重複創建
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
    // 緊湊模式：用於設定選單中 - 🔹 增大點擊區域
    return (
      <div className="font-size-toggle" style={{ position: 'relative', display: 'inline-block' }}>
        <button 
          className="font-size-button"
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          title={`字體大小: ${currentConfig.displayName}`}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px', // 🔹 增加內邊距
            background: 'transparent',
            border: '1px solid var(--border)',
            borderRadius: '8px', // 🔹 增加圓角
            cursor: 'pointer',
            color: 'var(--color)',
            fontSize: '14px', // 🔹 增大字體
            minWidth: '80px', // 🔹 增加最小寬度
            minHeight: '36px', // 🔹 增加最小高度
            justifyContent: 'space-between',
            transition: 'all 0.2s ease'
          }}
        >
          <span style={{ fontSize: '16px' }}>{currentConfig.icon}</span>
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
          <div 
            className="font-size-dropdown"
            style={{
              position: 'absolute',
              top: 'calc(100% + 4px)',
              right: '0',
              background: 'var(--navbackground)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              zIndex: 1001,
              minWidth: '140px', // 🔹 增加下拉選單寬度
              overflow: 'hidden'
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
                  padding: '12px 14px', // 🔹 增加點擊區域
                  background: currentSize === config.name ? 'var(--loginbg)' : 'none',
                  border: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  color: currentSize === config.name ? 'var(--loginbutton)' : 'var(--color)',
                  fontSize: '14px', // 🔹 增大字體
                  fontWeight: currentSize === config.name ? '600' : '500',
                  transition: 'all 0.2s ease',
                  minHeight: '42px' // 🔹 增加最小高度
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
                <span style={{ fontSize: '16px', minWidth: '20px' }}>{config.icon}</span>
                <span style={{ flex: 1 }}>{config.displayName}字體</span>
                {currentSize === config.name && (
                  <span style={{ color: 'var(--loginbutton)', fontSize: '16px' }}>✓</span>
                )}
              </button>
            ))}
          </div>
        )}

        <style jsx>{`
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

  // 完整模式：用於縮小導航欄 - 🔹 同樣增大點擊區域
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
          padding: '10px 16px', // 🔹 增加內邊距
          background: 'var(--navbackground)',
          border: '1px solid var(--border)',
          borderRadius: '10px', // 🔹 增加圓角
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          color: 'var(--color)',
          fontSize: '15px', // 🔹 增大字體
          fontWeight: '500',
          minWidth: '100px', // 🔹 增加最小寬度
          minHeight: '44px', // 🔹 增加最小高度
          justifyContent: 'space-between'
        }}
      >
        <span style={{ fontSize: '18px' }}>{currentConfig.icon}</span>
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
            minWidth: '200px', // 🔹 增加下拉選單寬度
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
                padding: '14px 16px', // 🔹 增大點擊區域
                background: currentSize === config.name ? 'var(--loginbg)' : 'none',
                border: 'none',
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                color: currentSize === config.name ? 'var(--loginbutton)' : 'var(--color)',
                fontWeight: currentSize === config.name ? '600' : 'normal',
                minHeight: '50px' // 🔹 增加最小高度
              }}
            >
              <span style={{ fontSize: '20px', minWidth: '24px', textAlign: 'center' }}>
                {config.icon}
              </span>
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

export default FontSizeToggle;