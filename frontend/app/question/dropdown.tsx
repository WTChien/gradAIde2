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
    title: "輔大資管系的畢業學分要求",
    content: [
      "通識課程：通常需要修滿至少 28 學分（其中包含部分特定領域要求）。",
      "專業必修：大約 60-80 學分，根據不同年級與課程設計可能會有所不同。",
      "選修課程：大約 20-40 學分，視系上規定而定。",
      "總學分數：通常在 128 學分 左右，具體數量要參照當年度的課程規劃與畢業要求。",
    ],
  },
  {
    title: "輔大資管系的畢業學分要求",
    content: [
      "通識課程：需要修滿至少 30 學分。",
      "專業必修：60 學分。",
      "選修課程：20-40 學分。",
      "總學分數：通常在 130 學分左右。",
    ],
  },
  {
    title: "輔大資管系的畢業學分要求",
    content: [
      "通識課程：需要修滿至少 30 學分。",
      "專業必修：60 學分。",
      "選修課程：20-40 學分。",
      "總學分數：通常在 130 學分左右。",
    ],
  },
  {
    title: "輔大資管系的畢業學分要求",
    content: [
      "通識課程：需要修滿至少 30 學分。",
      "專業必修：60 學分。",
      "選修課程：20-40 學分。",
      "總學分數：通常在 130 學分左右。",
    ],
  },
  {
    title: "輔大資管系的畢業學分要求",
    content: [
      "通識課程：需要修滿至少 30 學分。",
      "專業必修：60 學分。",
      "選修課程：20-40 學分。",
      "總學分數：通常在 130 學分左右。",
    ],
  },
];