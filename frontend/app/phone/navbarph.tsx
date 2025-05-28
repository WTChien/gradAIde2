"use client";
import React from "react";
import "../style.css";
import { useRouter } from "next/navigation";
import Image from 'next/image';

export default function NavBarph() {
  const router = useRouter();

  return (
    <aside className="navbar">
      <nav>
        <ul>
          <button onClick={() => router.push("/question")} className="button">
            <li className="lil">
              <Image src="/img/Question.png" className="nav-icon" alt="常見問題" />
              常見問題
            </li>
          </button>
          <button onClick={() => router.push("/direction")} className="button">
            <li className="lil">
              <Image src="/img/use.png" className="nav-icon" alt="使用說明" />
              使用說明
            </li>
          </button>
          <button onClick={() => router.push("/login")} className="sticky-bottom">
            <Image src="/img/logout.png" className="logout-image" alt="登出" />
            <span style={{ paddingLeft: "5px" }}>登出</span>
          </button>
        </ul>
      </nav>
    </aside>
  );
}