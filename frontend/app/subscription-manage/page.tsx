import React, { Suspense } from 'react';
import SubscriptionManagePage from './components/SubscriptionManagePage';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '訂閱管理 - GradAIde',
  description: '管理您的GradAIde選課提醒訂閱設定',
  robots: 'noindex, nofollow',
};

// 載入中組件
function LoadingComponent() {
  const spinKeyframes = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: spinKeyframes }} />
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        fontFamily: "'Microsoft JhengHei', Arial, sans-serif"
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '50px',
            height: '50px',
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #667eea',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          <p>正在載入訂閱管理頁面...</p>
        </div>
      </div>
    </>
  );
}

export default function SubscriptionManage() {
  return (
    <Suspense fallback={<LoadingComponent />}>
      <SubscriptionManagePage />
    </Suspense>
  );
}
