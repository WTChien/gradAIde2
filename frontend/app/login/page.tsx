"use client";
import React, { useState, useEffect } from 'react';
import './login.css';
import { useRouter } from 'next/navigation';
import axios from "axios";
import { AxiosError } from "axios";
import Image from 'next/image';

export default function Index() {
  const router = useRouter();
  const [isSlideUp, setIsSlideUp] = useState(true);
  const handleToggleLogin = () => setIsSlideUp(!isSlideUp);

  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [passwordShown1, setPasswordShown1] = useState(false);
  const [passwordShown2, setPasswordShown2] = useState(false);
  const [passwordShown3, setPasswordShown3] = useState(false);
  const [account, setAccount] = useState("");
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [message] = useState("");

  const togglePasswordVisibility1 = () => setPasswordShown1(!passwordShown1);
  const togglePasswordVisibility2 = () => setPasswordShown2(!passwordShown2);
  const togglePasswordVisibility3 = () => setPasswordShown3(!passwordShown3);
  useEffect(() => {
    const updateHeight = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };
  
    updateHeight();
    window.addEventListener('resize', updateHeight);
    return () => window.removeEventListener('resize', updateHeight);
  }, []);
  
  const handleRegister = async () => {
    if (!password || !confirmPassword || !username || !email || (selectedOption !== "student" && !account)) {
      alert("請填寫所有欄位");
      return;
    }

    if (password !== confirmPassword) {
      alert("密碼與確認密碼不一致");
      return;
    }

    if (selectedOption === "student" && studentId.length !== 9) {
      alert("學號必須為 9 碼");
      return;
    }

    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailPattern.test(email)) {
      alert("請輸入有效的電子郵件地址");
      return;
    }

    // 🔒 前端長度限制檢查 - 正確位置
    if (selectedOption !== "student") {
      if (account.length < 6 || account.length > 15) {
        alert("帳號長度需介於 6 到 15 字元之間");
        return;
      }
    }
    if (password.length < 6 || password.length > 15) {
      alert("密碼長度需介於 6 到 15 字元之間");
      return;
    }
    if (username.length < 3 || username.length > 15) {
      alert("使用者名稱長度需介於 3 到 15 字元之間");
      return;
    }

    const apiUrl =
  selectedOption === "student"
    ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/register_student`
    : `${process.env.NEXT_PUBLIC_API_BASE_URL}/register_non_student`;


    const data =
      selectedOption === "student"
        ? { student_id: studentId, password, confirm_password: confirmPassword, username, email }
        : { account, password, confirm_password: confirmPassword, username, email };

        try {
          const response = await axios.post<{ message: string }>(apiUrl, data);
          alert(response.data.message);
          window.location.reload();
        } catch (error) {
          const err = error as AxiosError<{ detail?: string }>;
          alert(err.response?.data?.detail || "註冊失敗，請稍後再試");
        }
  };

  // 🔹 登入後取得聊天紀錄
  // const loadHistoryFromServer = async (account: string) => {
  //   try {
  //     const res = await axios.get(`https://llm.gradaide.xyz/get_chat_history/${account}`);
  //     const history = res.data; // [{role: 'user', content: '...'}, {role: 'ai', content: '...'}]
  //     const mapped = history.map((entry: any) => ({
  //       type: entry.role === "user" ? "user" : "ai",
  //       content: entry.content,
  //     }));
  //     localStorage.setItem("chatHistory", JSON.stringify(mapped));
  //     window.dispatchEvent(new Event("storage"));  // 通知其他組件刷新
  //   } catch {
  //     localStorage.removeItem("chatHistory");  // 沒有歷史就清空
  //   }
  // };

  
  const handleLogin = async () => {
    if (!account || !password) {
      alert("請輸入帳號與密碼");
      return;
    }
  
    try {
      const response = await axios.post<{
        message: string;
        account: string;
        token: string;
        admission_year?: string; // 🆕 學年資訊
        user_type?: string;      // 🆕 用戶類型
        department_name?: string; // 🆕 系所名稱
        study_type?: string;     // 🆕 學制類型
      }>(`${process.env.NEXT_PUBLIC_API_BASE_URL}/login`, {
        account,
        password,
      });
      
      // 🔹 先載入歷史紀錄（若有）
      // await loadHistoryFromServer(response.data.account);
      
      // ✅ 儲存登入基本資訊
      localStorage.setItem("token", response.data.token);
      localStorage.setItem("account", response.data.account);
      
      // 🆕 儲存學年和用戶類型資訊
      if (response.data.admission_year) {
        localStorage.setItem("admission_year", response.data.admission_year);
        console.log("✅ 學年資訊已儲存:", response.data.admission_year);
      } else {
        localStorage.removeItem("admission_year");
        console.log("ℹ️ 非學生用戶，移除學年資訊");
      }
      
      if (response.data.user_type) {
        localStorage.setItem("user_type", response.data.user_type);
      }
      
      if (response.data.department_name) {
        localStorage.setItem("department_name", response.data.department_name);
      }
      
      if (response.data.study_type) {
        localStorage.setItem("study_type", response.data.study_type);
      }
      
      alert(response.data.message);
      router.push("/");
    } catch (error) {
      const err = error as AxiosError<{ detail?: string }>;
      alert(err.response?.data?.detail || "登入失敗，請稍後再試");
    }
  };
  

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (selectedOption) {
        handleRegister();
      } else {
        handleLogin();
      }
    }
    
  };


  
  return (
    <div className="form-structor">
      <div className={`login ${isSlideUp ? "slide-up" : ""}`} style={{ marginTop: '30px' }}>
        <div className="center">
          <h2 className="form-title" id="login" onClick={handleToggleLogin}>
            <span style={{ color: '#949494' }}>or</span> Sign up
          </h2>
          <div className="form-holder">
            <div className="buttons-container">
              {selectedOption === null ? (
                <div className="buttons-container">
                  <button className="register-button" onClick={() => setSelectedOption('student')}>
                    <Image src="/img/student.png" alt="學生圖標" className="button-icon" />
                    <span>學生</span>
                  </button>
                  <button className="register-button" onClick={() => setSelectedOption('non-student')}>
                    <Image src="/img/bro.png" alt="非在校學生圖標" className="button-icon" />
                    <span>非本校學生</span>
                  </button>
                </div>
              ) : (
                <div className="ph">
                  <div className="header-container">
                    <h2 className="register-title">{selectedOption === "student" ? "學生註冊" : "非本校學生註冊"}</h2>
                    <button className="back-button" onClick={() => setSelectedOption(null)}>
                      <Image alt='' src="/img/left.png" className="icon" />
                    </button>
                  </div>
                  <div className="form-holder1">
                    {selectedOption === "student" && (
                      <input type="text" className="input aa" placeholder="學號" value={studentId} onChange={(e) => setStudentId(e.target.value)} onKeyDown={handleKeyDown} />
                    )}
                    {selectedOption !== "student" && (
                      <input type="text" className="input aa" placeholder="帳號" value={account} onChange={(e) => setAccount(e.target.value)} onKeyDown={handleKeyDown} />
                    )}
                    <div className="password-container4">
                      <input type={passwordShown1 ? "text" : "password"} className="input aa" placeholder="密碼" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={handleKeyDown} />
                      <button type="button" className="toggle-password3" onClick={togglePasswordVisibility1}>
                        {passwordShown1 ? <Image src="/img/eye-fill.png" alt="隱藏密碼" className="icon4" /> : <Image src="/img/eye-slash-fill.png" alt="顯示密碼" className="icon4" />}
                      </button>
                    </div>
                    <div className="password-container4">
                      <input type={passwordShown2 ? "text" : "password"} className="input aa" placeholder="再次輸入密碼" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} onKeyDown={handleKeyDown} />
                      <button type="button" className="toggle-password3" onClick={togglePasswordVisibility2}>
                        {passwordShown2 ? <Image src="/img/eye-fill.png" alt="隱藏密碼" className="icon4" /> : <Image src="/img/eye-slash-fill.png" alt="顯示密碼" className="icon4" />}
                      </button>
                    </div>
                    <input type="text" className="input aa" placeholder="使用者名稱" value={username} onChange={(e) => setUsername(e.target.value)} onKeyDown={handleKeyDown} />
                    <input type="email" className="input aa" placeholder="電子郵件" value={email} onChange={(e) => setEmail(e.target.value)} onKeyDown={handleKeyDown} />
                  </div>
                  <button className="submit-btn" onClick={handleRegister}>Sign up</button>
                  <p>{message}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className={`signup ${isSlideUp ? "" : "slide-up"}`}>
        <h2 className="form-title" id="signup" onClick={handleToggleLogin}>
          <span style={{ color: '#e7e5e2' }}>or</span> Log in
        </h2>
        <div className="form-holder" style={{ marginTop: "10px" }}>
          <input type="text" className="input" placeholder="帳號" value={account} onChange={(e) => setAccount(e.target.value)} onKeyDown={handleKeyDown} required />
          <div className="password-container3">
            <input type={passwordShown3 ? "text" : "password"} className="input" placeholder="密碼" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={handleKeyDown} required />
            <button type="button" className="toggle-password3" onClick={togglePasswordVisibility3}>
              {passwordShown3 ? (
                <Image src="/img/eye-fill.png" alt="隱藏密碼" className="icon3" />
              ) : (
                <Image src="/img/eye-slash-fill.png" alt="顯示密碼" className="icon3" />
              )}
            </button>
          </div>
        </div>
        <button className="submit-btn" onClick={handleLogin}>Log in</button>
        <div className="indexbutton-container">
          <button className="indexbutton" onClick={() => router.push('/')}>不登入？&nbsp;直接使用！</button>
          <a className="indexbutton" href='./forget'>忘記密碼</a>
        </div>
      </div>
    </div>
  );
}