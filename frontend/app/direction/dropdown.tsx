"use client";
import React, { useState } from "react";
import "./direction.css";
import Image from 'next/image';

export default function CourseRequirementsDropdown1() {
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
                <div key={index} className="dropdown-container2" >
                    {/* 標題區域 */}
                    <div className="dropdown-header" onClick={() => toggleDropdown(index)}>
                        <span className="dropdown-title">{item.title}</span>
                        <span className="dropdown-arrow">{isOpenArray[index] ? "▾" : "▸"}</span>
                    </div>

                    {/* 展開內容 */}
                    {isOpenArray[index] && (
                        <div className="dropdown-content open">
                            <hr style={{ marginBottom: '5px' }} />
                            {item.content.map((text, idx) => (
                                <p key={idx}>{text}</p>
                            ))}
                            <p style={{ marginBottom: '5px' }} />
                            {item.content1?.map((text, idx) => (
                                <p key={idx}>{text}</p>
                            ))}

                            {item.image && <Image src={item.image} alt="說明圖片" className="imgadd" />}
                            {item.image3 && <Image src={item.image3} alt="說明圖片" className="imgclass" />}
                            <p style={{ marginBottom: '5px' }} />

                            {item.content2?.map((text, idx) => (
                                <p key={idx}>{text}</p>
                            ))}
                            {item.image1 && <Image src={item.image1} alt="說明圖片" className="imgclass" />}
                            <p style={{ marginBottom: '5px' }} />

                            {item.content3?.map((text, idx) => (
                                <p key={idx}>{text}</p>
                            ))}
                            {item.image2 && <Image src={item.image2} alt="說明圖片" className="imgclass" />}
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
        title: "排課時段選擇",
        content: [
            "選擇自己想要排課的時，GradAIde 將根據您的需求提供個人化課表建議。",

        ],
        content1: [
            "Ⅰ.點選對話框左邊的「✚」圖示",
        ],
        image: "/img/addclass.png",
        content2: [
            "Ⅱ.出現課表表格，選擇想要系統提供建議的課程時段後，點選確定。",

        ],
        image1: "/img/class.png",

    },
    {
        title: "忘記密碼",
        content: [
            "忘記密碼別慌張，跟著以下步驟解決問題吧。",

        ],
        content1: [
            "Ⅰ.從登入頁面點選忘記密碼，並輸入帳號及電子郵件。",
        ],
        image3: "/img/forget1.png",
        content2: [
            "Ⅱ.到個人信箱中查看驗證碼並輸入到框框中(需注意驗證碼可能會被歸類為垃圾郵件)。",

        ],
        image1: "/img/forget2.png", 
        content3: [
            "Ⅲ.輸入新密碼就可以再次登入了。",

        ],
        image2: "/img/forget3.png",

    },
   
];