from playwright.async_api import async_playwright
import asyncio
import time
import json
import re

def parse_query_string(query):
    """
    解析自然語言查詢字串，提取篩選條件
    """
    # 系所代碼映射
    dept_mapping = {
        # 通識課程
        "人文": "PT", "人文藝術": "PT", "人文通識": "PT",
        "社會": "ST", "社會科學": "ST", "社會通識": "ST",
        "自然": "NT", "自然科技": "NT", "自然通識": "NT",
        # 學系
        "資管": "74", "資訊管理": "74",
        "會計": "71", "會計學系": "71",
        "統計": "76", "統計資訊": "76"
    }
    
    # 星期映射
    weekday_mapping = {
        "星期一": "1", "禮拜一": "1", "週一": "1", "一": "1", "monday": "1",
        "星期二": "2", "禮拜二": "2", "週二": "2", "二": "2", "tuesday": "2",
        "星期三": "3", "禮拜三": "3", "週三": "3", "三": "3", "wednesday": "3",
        "星期四": "4", "禮拜四": "4", "週四": "4", "四": "4", "thursday": "4",
        "星期五": "5", "禮拜五": "5", "週五": "5", "五": "5", "friday": "5",
        "星期六": "6", "禮拜六": "6", "週六": "6", "六": "6", "saturday": "6",
        "星期日": "7", "禮拜日": "7", "週日": "7", "日": "7", "sunday": "7"
    }
    
    # 時間段映射 (針對大學生作息調整)
    time_mapping = {
        "早上": ("D3", "D4"),  # 10:10-12:00 (避開8點課)
        "上午": ("D3", "D4"),
        "中午": ("D5", "D6"),  # 13:10-15:00
        "下午": ("D5", "D6"),  # 13:10-15:00 (不要太晚)
        "傍晚": ("D7", "D8"),  # 15:10-17:00
        "晚上": ("D9", "DA"),  # 17:10-19:00 (不要太晚)
        "夜間": ("D9", "DA")
    }
    
    query_lower = query.lower()
    
    # 解析系所
    dept_code = None
    for keyword, code in dept_mapping.items():
        if keyword in query_lower:
            dept_code = code
            break
    
    # 解析星期
    weekday = None
    for keyword, day in weekday_mapping.items():
        if keyword in query_lower:
            weekday = day
            break
    
    # 解析時間段
    start_section = None
    end_section = None
    for keyword, (start, end) in time_mapping.items():
        if keyword in query_lower:
            start_section = start
            end_section = end
            break
    
    # 如果有具體節次，優先使用節次
    section_pattern = r'D[1-9A-E]'
    sections = re.findall(section_pattern, query.upper())
    if sections:
        start_section = sections[0]
        if len(sections) > 1:
            end_section = sections[-1]
        else:
            end_section = start_section
    
    return {
        "dept_code": dept_code,
        "start_section": start_section,
        "end_section": end_section,
        "weekday": weekday
    }

async def search_courses_crawler(dept_code, start_section, end_section, weekday):
    """
    課程查詢函數 - 使用 Async Playwright 爬蟲 (API 版本)
    🔹 限制只返回前 5 門課程
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # 導航至輔仁大學課程查詢系統
            await page.goto("http://estu.fju.edu.tw/fjucourse/Secondpage.aspx")

            # 點擊基本開課資料查詢
            await page.click("input[value='依基本開課資料查詢']")

            # 選擇開課部別為日間部
            await page.select_option("select[name='DDL_AvaDiv']", "D")

            # 選擇系所
            if dept_code:
                try:
                    await page.select_option("select[name='DDL_Avadpt']", dept_code, timeout=3000)
                    await page.wait_for_timeout(1000)
                except:
                    await browser.close()
                    return {"error": "無法選擇開課系所，操作超時", "courses": []}
            
            # 選擇節次
            if start_section:
                await page.select_option("select[name='DDL_Section_S']", start_section)
                if end_section:
                    await page.select_option("select[name='DDL_Section_E']", end_section)

            # 選擇星期
            if weekday:
                await page.check(f"input[name='CheckBox_WK{weekday}']")

            # 點擊查詢按鈕
            await page.click("input[name='But_Run']")

            # 等待查詢結果載入
            await page.wait_for_timeout(3000)

            # 獲取課程列表
            rows = await page.query_selector_all("table#GV_CourseList tr[style*='background-color:White']")
            courses = []

            # 🔹 限制只處理前 5 筆資料
            max_courses = 5
            processed_count = 0

            for i, row in enumerate(rows):
                if processed_count >= max_courses:
                    break
                    
                try:
                    # 先獲取所有td元素
                    all_tds = await row.query_selector_all("td")
                    
                    # 課程代號 - 第2個td
                    course_code_td = await row.query_selector("td:nth-child(2)")
                    course_code = await course_code_td.inner_text() if course_code_td else ""
                    course_code = course_code.strip()

                    # 課程名稱 - 使用span id
                    course_name_span = await row.query_selector("span[id*='Lab_Coucna_']")
                    course_name = await course_name_span.inner_text() if course_name_span else ""
                    course_name = course_name.strip()
                    
                    # 檢查是否有特殊標籤（程、網等）
                    special_tags = []
                    
                    # 查找同一行中的其他span或td，尋找單字標籤
                    for span in await row.query_selector_all("span"):
                        span_text = await span.inner_text()
                        span_text = span_text.strip()
                        if span_text in ["程", "網", "英-專業"]:
                            if span_text not in special_tags:
                                special_tags.append(span_text)
                    
                    # 也檢查td中的單字標籤
                    for td in all_tds:
                        td_text = await td.inner_text()
                        td_text = td_text.strip()
                        if td_text in ["程", "網", "英-專業"]:
                            if td_text not in special_tags:
                                special_tags.append(td_text)
                    
                    # 將標籤加到課程名稱後
                    if special_tags:
                        for tag in special_tags:
                            course_name += f"({tag})"
                    
                    # 開課單位 - 查找第4欄的內容
                    dept_name = ""
                    if len(all_tds) > 3:
                        dept_text = await all_tds[3].inner_text()
                        dept_text = dept_text.strip()
                        if dept_text and len(dept_text) < 20:
                            dept_name = dept_text

                    # 學分 - 查找包含".00"的td
                    credits = ""
                    for td in all_tds:
                        text = await td.inner_text()
                        text = text.strip()
                        if ".00" in text and len(text) < 10:
                            credits = text
                            break

                    # 授課教師 - 使用span id
                    teacher_span = await row.query_selector("span[id*='Lab_Tchcna_']")
                    teacher = await teacher_span.inner_text() if teacher_span else ""
                    teacher = teacher.strip()
                    
                    # 領域 - 查找包含"領域"文字的span或td
                    domain = ""
                    all_spans = await row.query_selector_all("span")
                    for span in all_spans:
                        span_text = await span.inner_text()
                        span_text = span_text.strip()
                        if (span_text and 
                            span_text not in ["領域：", "領域 ："] and
                            len(span_text) < 20 and
                            not any(keyword in span_text for keyword in ["專長", "年級", "開放", "外系", "學群"])):
                            span_id = await span.get_attribute("id") or ""
                            if "GGroupCna" in span_id:
                                domain = span_text
                                break

                    # 星期和時間 - 查找特定格式
                    time_info = ""
                    classroom = ""
                    weekday_info = ""
                    
                    for j, td in enumerate(all_tds):
                        text = await td.inner_text()
                        text = text.strip()
                        # 先找節次，然後往前找星期
                        if "-" in text and "D" in text and len(text) < 10:
                            time_info = text
                            
                            # 星期通常在節次的前一欄
                            if j > 0:
                                prev_text = await all_tds[j - 1].inner_text()
                                prev_text = prev_text.strip()
                                if prev_text:
                                    # 將簡化星期轉換為完整格式
                                    weekday_map = {
                                        "一": "星期一", "二": "星期二", "三": "星期三", "四": "星期四", 
                                        "五": "星期五", "六": "星期六", "日": "星期日"
                                    }
                                    
                                    for short, full in weekday_map.items():
                                        if short in prev_text and "星期" not in prev_text:
                                            weekday_info = prev_text.replace(short, full)
                                            break
                                    else:
                                        if any(day in prev_text for day in ["一", "二", "三", "四", "五", "六", "日", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
                                            weekday_info = prev_text
                            
                            # 教室通常在時間的下一欄
                            if j + 1 < len(all_tds):
                                next_text = await all_tds[j + 1].inner_text()
                                next_text = next_text.strip()
                                if (next_text and 
                                    len(next_text) < 10 and 
                                    next_text[0].isalpha() and 
                                    any(c.isdigit() for c in next_text) and
                                    not any(keyword in next_text for keyword in ["外系", "開放", "全", "Wed", "Mon", "Tue", "Thu", "Fri"])):
                                    classroom = next_text
                            break

                    course = {
                        "課程代號": course_code,
                        "領域": domain,
                        "開課單位": dept_name,
                        "課程名稱": course_name,
                        "學分": credits,
                        "授課教師": teacher,
                        "上課時間": weekday_info,
                        "節次": time_info,
                        "教室": classroom
                    }
                    
                    # 只有當課程代號和課程名稱都存在時才加入
                    if course["課程代號"] and course["課程名稱"]:
                        courses.append(course)
                        processed_count += 1
                        
                except Exception as e:
                    # 解析單筆資料失敗時，跳過該筆資料繼續處理
                    continue

            await browser.close()
            
            return {
                "success": True,
                "total_courses": len(courses),
                "courses": courses,
                "query_conditions": {
                    "dept_code": dept_code,
                    "start_section": start_section,
                    "end_section": end_section,
                    "weekday": weekday
                }
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "courses": []
        }

def run_async_in_sync(coro):
    """
    在同步環境中運行異步協程的工具函數
    """
    try:
        # 嘗試獲取當前事件循環
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已經在事件循環中，使用 run_in_executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            # 如果沒有運行中的事件循環，直接使用 asyncio.run
            return asyncio.run(coro)
    except RuntimeError:
        # 如果沒有事件循環，創建新的
        return asyncio.run(coro)

def course_search_api(query: str) -> dict:
    """
    課程搜尋 API 函數 - 純粹返回 JSON 數據
    🔹 限制只返回前 5 門課程
    
    Args:
        query (str): 自然語言查詢字串
        
    Returns:
        dict: 包含查詢結果的 JSON 格式數據
    """
    try:
        # 解析查詢條件
        conditions = parse_query_string(query)
        
        # 執行異步爬蟲查詢
        result = run_async_in_sync(search_courses_crawler(
            conditions['dept_code'],
            conditions['start_section'],
            conditions['end_section'],
            conditions['weekday']
        ))
        
        # 添加查詢字串到結果中
        result['original_query'] = query
        result['parsed_conditions'] = conditions
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"課程搜尋發生錯誤：{str(e)}",
            "original_query": query,
            "courses": []
        }

def format_courses_for_agent(search_result: dict) -> str:
    """
    🔹 修正版：格式化課程搜尋結果，避免特殊字符造成前端渲染問題
    使用純文字格式，確保在所有環境下都能正常顯示
    
    Args:
        search_result (dict): course_search_api 返回的結果
        
    Returns:
        str: 格式化後的課程資訊字串
    """
    if not search_result.get('success', False):
        return f"課程搜尋失敗：{search_result.get('error', '未知錯誤')}"
    
    courses = search_result.get('courses', [])
    
    if not courses:
        return "未找到符合條件的課程，請嘗試調整查詢條件。"
    
    # 🔹 使用純文字格式，避免特殊符號
    course_count = len(courses)
    result = f"找到 {course_count} 門課程：\n\n"
    
    for i, course in enumerate(courses, 1):
        # 🔹 使用數字編號，避免表情符號
        result += f"{i}. {course['課程名稱']}\n"
        result += f"   課程代號：{course['課程代號']}\n"
        
        if course['開課單位']:
            result += f"   開課單位：{course['開課單位']}\n"
        
        if course['授課教師']:
            result += f"   授課教師：{course['授課教師']}\n"
        
        if course['學分']:
            result += f"   學分：{course['學分']}\n"
        
        if course['上課時間'] or course['節次']:
            time_str = f"{course['上課時間']} {course['節次']}".strip()
            result += f"   上課時間：{time_str}\n"
        
        if course['教室']:
            result += f"   教室：{course['教室']}\n"
        
        if course['領域']:
            result += f"   領域：{course['領域']}\n"
        
        # 🔹 課程之間用一個空行分隔
        result += "\n"
    
    # 🔹 簡化提示訊息
    if course_count >= 5:
        result += "如需查看更多課程，請縮小查詢範圍或使用更具體的條件。"
    
    return result

# 使用範例
if __name__ == "__main__":
    # API 使用範例
    test_queries = [
        "星期一早上的人文通識",
        "資管系的課程", 
        "星期三下午的社會科學課程"
    ]
    
    for query in test_queries:
        print(f"\n測試查詢: {query}")
        print("-" * 50)
        
        # 獲取 JSON 結果
        result = course_search_api(query)
        
        # 格式化顯示給 Agent
        formatted_result = format_courses_for_agent(result)
        print(formatted_result)
        
        # 也可以直接使用 JSON 數據
        print(f"JSON 數據: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print("=" * 50)