"use client";
import React, { useState, useEffect } from "react";

import "../style.css";
import NavBar from "../navbar";
import Top from "../edit";
import Topph from "../editph";
import CourseRequirementsDropdown1 from "./dropdown";

export default function Direction() {
  const [isMobile, setIsMobile] = useState(false);
  
    // 監聽視窗大小變化
    useEffect(() => {
      const checkScreenSize = () => {
        setIsMobile(window.innerWidth < 768); // 判斷是否為手機
      };
  
      checkScreenSize(); // 初始載入時判斷一次
      window.addEventListener("resize", checkScreenSize);
  
      return () => window.removeEventListener("resize", checkScreenSize);
    }, []);
    return (
      <div className="layout-container">
                {isMobile ? null: <NavBar />}
                <div className="content">
                  <div className="content-section1">{isMobile ? <Topph /> : <Top />}</div>
                  <div className="content-section2"> <CourseRequirementsDropdown1 /></div>
                </div>
              </div>
    );
  }