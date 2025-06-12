"use client";
import React, { useState } from "react";
import "./question.css";

export default function CourseRequirementsDropdown() {
  // 使用 state 來控制每個 dropdown 是否展開
  const [isOpenArray, setIsOpenArray] = useState<boolean[]>(data.map(() => false));

  // 切換某個 dropdown 的展開狀態
  const toggleDropdown = (index: number) => {
    setIsOpenArray((prev) => {
      const updatedArray = [...prev];
      updatedArray[index] = !updatedArray[index];
      return updatedArray;
    });
  };

  return (
    <div className="dropdowns-container1  container1">
      {data.map((item, index) => (
        <div key={index} className="dropdown-container" >
          {/* 標題區域 */}
          <div className="dropdown-header" onClick={() => toggleDropdown(index)}>
            <span className="dropdown-title">{item.title}</span>
            <span className="dropdown-arrow">{isOpenArray[index] ? "▾" : "▸"}</span>
          </div>

          {/* 展開內容 */}
          {isOpenArray[index] && (
            <div className="dropdown-content open">
                <hr style={{marginBottom:'5px'}} />
              {item.content.map((text, idx) => (
                <p key={idx}>{text}</p>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// 模擬數據
const data = [
  {
    "title": "輔大資管系的畢業總學分要求",
    "content": [
      "畢業需修滿 128 學分。",
      "包含全人教育、基本能力、通識、專業必修與專業選修等課程。"
    ]
  },
  {
    "title": "全人教育核心課程需要修幾學分？",
    "content": [
      "需修畢 8 學分，屬於基本通識的一部分，培養全人素養。"
    ]
  },
  {
    "title": "基本能力課程有什麼要求？",
    "content": [
      "需修畢 12 學分，內容可能包含語文、邏輯、寫作等。"
    ]
  },
  {
    "title": "通識涵養課程要修幾學分？",
    "content": [
      "需修畢 12 學分，強調人文、社會與自然科學涵養的平衡。"
    ]
  },
  {
    "title": "專業必修課程需要修幾學分？",
    "content": [
      "需修畢 64 學分，涵蓋核心資訊管理與系統開發等主題。"
    ]
  },
  {
    "title": "專業選修課程有什麼規定？",
    "content": [
      "需修畢至少 10 學分，學生可依興趣與職涯方向自由選課。"
    ]
  },
  {
    "title": "英文畢業門檻是什麼？",
    "content": [
      "需達 CEFR B2 高階級，例如 TOEIC 785 分或 IELTS 6.0。",
      "未達門檻者須參加 8 次英語自學測驗補救。"
    ]
  },
  {
    "title": "英語授課課程有什麼規定？",
    "content": [
      "至少需修畢 5 門（共 15 學分）由本院開設的英文授課專業課程。"
    ]
  },
  {
    "title": "程式語言機測怎麼通過？",
    "content": [
      "單次考試答對 3 題即可通過。",
      "若未通過，可修一門系上程式設計選修課程作為替代。"
    ]
  },
  {
    "title": "有哪些擋修規定？",
    "content": [
      "「系統分析與設計」未通過無法修「資訊系統專題一」。",
      "「資訊系統專題二」不及格者，需重修「專題一」與「專題二」。"
    ]
  }
];