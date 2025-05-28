"use client";
import React, { useState, useEffect } from "react";
import "./name.css";
import { useRouter } from "next/navigation";
import axios from "axios";
import { AxiosError } from "axios";
import Image from 'next/image';

export default function Name() {
  const router = useRouter();
  const [newName, setNewName] = useState("");
  const [account, setAccount] = useState<string | null>(null);

  useEffect(() => {
    const storedAccount = localStorage.getItem("account");
    if (!storedAccount) {
      alert("請先登入");
      router.push("/login");
    } else {
      setAccount(storedAccount);
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!account || !newName.trim()) {
      alert("請輸入新名稱");
      return;
    }

    try {
      const response = await axios.post<{ message: string }>(
        "https://llm.gradaide.xyz/change_name",
        {
          account,
          new_name: newName
        }
      );
      alert(response.data.message);
  router.push("/");
} catch (error) {
  const err = error as AxiosError<{ detail?: string }>;
  const msg = err.response?.data?.detail || "名稱變更失敗，請稍後再試";
  alert(msg);
}
  };

  return (
    <div className="vid-container1">
      <div className="inner-container1">
        <Image alt="" src="/img/Frame 16.png" className="logoicon1" />
        <form onSubmit={handleSubmit}>
          <div className="box1">
            <h1>變更名稱</h1>
            <div className="password-container1">
              <input
                type="text"
                placeholder="請輸入新暱稱"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
              />
              <Image alt="" src="/img/Write.png" className="icon1 toggle-password1" />
            </div>

            <button className="login1" type="submit">
              <span style={{ fontSize: "18px" }}>確定</span>
            </button>
            <button
              className="indexbutton1"
              type="button"
              onClick={() => router.push("/")}
            >
              取消變更
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}