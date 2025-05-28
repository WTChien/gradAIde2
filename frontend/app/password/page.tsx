"use client"
import React, { useState, useEffect } from 'react';
import "./password.css";
import { useRouter } from 'next/navigation';
import axios from "axios";
import { AxiosError } from "axios";
import Image from 'next/image';

export default function Pass() {
  const [passwordShown1, setPasswordShown1] = useState(false);
  const [passwordShown2, setPasswordShown2] = useState(false);
  const [passwordShown3, setPasswordShown3] = useState(false);
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [account, setAccount] = useState<string | null>(null);

  useEffect(() => {
    const storedAccount = localStorage.getItem("account");
    setAccount(storedAccount);
  }, []);

  const router = useRouter();



   const togglePasswordVisibility1 = () => setPasswordShown1(!passwordShown1);
  const togglePasswordVisibility2 = () => setPasswordShown2(!passwordShown2);
  const togglePasswordVisibility3 = () => setPasswordShown3(!passwordShown3);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); // 防止表單刷新

    if (!account || !password || !newPassword || !confirmNewPassword) {
      alert("請填寫所有欄位");
      return;
    }

    if (newPassword.length < 6 || newPassword.length > 15) {
      alert("新密碼長度需介於 6 到 15 字元之間");
      return;
    }

    if (newPassword !== confirmNewPassword) {
      alert("兩次輸入的新密碼不一致");
      return;
    }

    try {
      const response = await axios.post<{ message: string }>(
        "https://llm.gradaide.xyz/change_password",
        {
          account,
          old_password: password,
          new_password: newPassword,
          confirm_password: confirmNewPassword
        }
      );

      alert(response.data.message);
      router.push("/");
    } catch (error) {
      const err = error as AxiosError<{ detail?: string }>;
      const msg =
        err.response?.data?.detail ||
        (typeof err.response?.data === "string"
          ? err.response?.data
          : JSON.stringify(err.response?.data)) ||
        "密碼變更失敗，請稍後再試";
      alert(msg);
    }
    
  };

  return (
    <div className="vid-container2">
      <div className="inner-container2">
        <Image alt='' src="/img/Frame 16.png" className="logoicon2" />
        <form onSubmit={handleSubmit}>
          <div className="box2">
            <h1>變更密碼</h1>

            <div className="password-container2">
              <input
                type={passwordShown1 ? "text" : "password"}
                placeholder="請輸入原密碼"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button type="button" className="toggle-password2" onClick={togglePasswordVisibility1}>
                <Image alt='' src={passwordShown1 ? "/img/eye-fill.png" : "/img/eye-slash-fill.png"} className="icon2" />
              </button>
            </div>

            <div className="password-container2">
              <input
                type={passwordShown2 ? "text" : "password"}
                placeholder="請輸入新密碼"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              <button type="button" className="toggle-password2" onClick={togglePasswordVisibility2}>
                <Image alt='' src={passwordShown2 ? "/img/eye-fill.png" : "/img/eye-slash-fill.png"} className="icon2" />
              </button>
            </div>

            <div className="password-container2">
              <input
                type={passwordShown3 ? "text" : "password"}
                placeholder="再次輸入新密碼"
                value={confirmNewPassword}
                onChange={(e) => setConfirmNewPassword(e.target.value)}
              />
              <button type="button" className="toggle-password2" onClick={togglePasswordVisibility3}>
                <Image alt='' src={passwordShown3 ? "/img/eye-fill.png" : "/img/eye-slash-fill.png"} className="icon2" />
              </button>
            </div>

            <button className="login2" type="submit">
              <span style={{ fontSize: "18px" }}>確定</span>
            </button>

            <button className="indexbutton2" type="button" onClick={() => router.push("/")}>
              取消變更
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}