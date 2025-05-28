"use client";
import React, { useState, useEffect } from 'react';
import "./forget.css";
import { useRouter } from 'next/navigation';
import Image from 'next/image';

export default function Pass() {
    const [isLoading, setIsLoading] = useState(true);
    const [step, setStep] = useState(1);
    const [passwordShown1, setPasswordShown1] = useState(false);
    const [passwordShown2, setPasswordShown2] = useState(false);
    const [account, setAccount] = useState('');
    const [email, setEmail] = useState('');
    const [code, setCode] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [codeError, setCodeError] = useState('');

    useEffect(() => {
        setIsLoading(false);
    }, []);

    const togglePasswordVisibility1 = () => setPasswordShown1(!passwordShown1);
    const togglePasswordVisibility2 = () => setPasswordShown2(!passwordShown2);

    const router = useRouter();

    const handleSubmit = async () => {
        try {
            if (step === 1) {
                if (!account.trim() || !email.trim()) {
                    alert("帳號與電子郵件欄位不得為空");
                    return;
                }

                const res = await fetch("https://llm.gradaide.xyz/send_verification_code", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ account, email })
                });
                const data = await res.json();

                if (res.ok) {
                    alert("驗證碼已寄出\n(可能出現在垃圾信箱)");
                    setStep(2);
                } else if (Array.isArray(data) && data[0]?.msg) {
                    alert(data[0].msg);
                } else if (typeof data.detail === 'string') {
                    alert(data.detail);
                } else {
                    alert("發送驗證碼失敗，請確認帳號與電子郵件是否正確");
                }
            } else if (step === 2) {
                if (!code) {
                    alert("請輸入驗證碼");
                    return;
                }

                const res = await fetch("https://llm.gradaide.xyz/verify_code", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, code })
                });
                const data = await res.json();

                if (res.ok) {
                    setCodeError('');
                    setStep(3);
                } else if (typeof data.detail === 'string') {
                    alert(data.detail);
                } else {
                    alert("驗證碼錯誤或過期");
                }
            } else if (step === 3) {
                if (newPassword.length < 6 || newPassword.length > 15) {
                  alert("密碼長度需介於 6 到 15 字元之間");
                  return;
                }
              
                if (newPassword !== confirmPassword) {
                  alert("兩次密碼不一致");
                  return;
                }
              
                const res = await fetch("https://llm.gradaide.xyz/reset_password", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, code, new_password: newPassword })
                  });
                  
              

                const data = await res.json();
                if (res.ok) {
                    alert("密碼重設成功！");
                    router.push("/login");
                } else if (typeof data.detail === 'string') {
                    alert(data.detail);
                } else {
                    alert("密碼重設失敗");
                }
            }
        } catch {
            alert("發生錯誤，請稍後再試");
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            handleSubmit();
        }
    };

    const renderStepContent = () => {
        switch (step) {
            case 1:
                return (
                    <>
                        <div className="password-container2">
                            <input
                                type="text"
                                placeholder="請輸入帳號"
                                value={account}
                                onChange={(e) => setAccount(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                        </div>
                        <div className="password-container2">
                            <input
                                type="text"
                                placeholder="請輸入電子郵件"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                        </div>
                    </>
                );
            case 2:
                return (
                    <div className="password-container2">
                        <input
                            type="text"
                            placeholder="請輸入驗證碼"
                            value={code}
                            onChange={(e) => setCode(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                        {codeError && <p style={{ color: 'red' }}>{codeError}</p>}
                    </div>
                );
            case 3:
                return (
                    <>
                        <div className="password-container2">
                            <input
                                type={passwordShown1 ? "text" : "password"}
                                placeholder="請輸入新密碼"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                            <button
                                type="button"
                                className="toggle-password2"
                                onClick={togglePasswordVisibility1}
                            >
                                {passwordShown1 ? <Image src="/img/eye-fill.png" alt="隱藏密碼" className='icon2' /> : <Image src="/img/eye-slash-fill.png" alt="顯示密碼" className='icon2' />}
                            </button>
                        </div>
                        <div className="password-container2">
                            <input
                                type={passwordShown2 ? "text" : "password"}
                                placeholder="請再次輸入新密碼"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                            <button
                                type="button"
                                className="toggle-password2"
                                onClick={togglePasswordVisibility2}
                            >
                                {passwordShown2 ? <Image src="/img/eye-fill.png" alt="隱藏密碼" className='icon2' /> : <Image src="/img/eye-slash-fill.png" alt="顯示密碼" className='icon2' />}
                            </button>
                        </div>
                    </>
                );
            default:
                return null;
        }
    };

    const getButtonText = () => {
        switch (step) {
            case 1:
            case 2:
                return "送出";
            case 3:
                return "確認更改";
            default:
                return "送出";
        }
    };

    if (isLoading) return null;

    return (
        <div>
            <div className="vid-container2">
                <div className="inner-container2">
                    <Image alt='' src='/img/Frame 16.png' className='logoicon2' />
                    <div className="box2">
                        <h1>忘記密碼</h1>
                        {renderStepContent()}
                        <button className='login2' onClick={handleSubmit}>
                            <span style={{ fontSize: '18px' }}>{getButtonText()}</span>
                        </button>
                        <button className="indexbutton2" onClick={() => router.push('/login')}>
                            返回登入
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}