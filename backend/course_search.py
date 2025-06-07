from playwright.async_api import async_playwright
import asyncio
import time
import json
import re

def parse_query_string(query):
    """
    解析自然語言查詢字串，提取篩選條件
    🔹 新增：當偵測到「通識」關鍵字但沒有指定領域時，預設為社會通識
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
    
    # 🔹 新增：通識課程特殊處理邏輯
    dept_code = None
    
    # 先檢查是否有明確的系所或領域關鍵字
    for keyword, code in dept_mapping.items():
        if keyword in query_lower:
            dept_code = code
            break
    
    # 🔹 如果沒有找到明確的系所，但有「通識」關鍵字，預設為社會通識
    if dept_code is None:
        general_education_keywords = ["通識", "通識課", "通識課程", "general education", "ge"]
        
        # 檢查是否包含通識關鍵字
        has_general_keyword = any(keyword in query_lower for keyword in general_education_keywords)
        
        if has_general_keyword:
            print(f"🔹 偵測到通識關鍵字但未指定領域，預設為社會通識 (ST)")
            dept_code = "ST"  # 預設為社會通識
    
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

def ensure_unique_courses(courses, max_courses=5):
    """
    確保課程名稱不重複，最多返回指定數量的課程
    
    Args:
        courses (list): 課程列表
        max_courses (int): 最大課程數量，預設5門
        
    Returns:
        list: 去重後的課程列表
    """
    seen_names = set()
    unique_courses = []
    
    for course in courses:
        course_name = course.get('課程名稱', '').strip()
        if course_name and course_name not in seen_names:
            seen_names.add(course_name)
            unique_courses.append(course)
            
            # 達到最大數量就停止
            if len(unique_courses) >= max_courses:
                break
    
    return unique_courses

async def extract_course_info(row):
    """
    從表格行中提取課程資訊的通用函數
    """
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
        
        # 只有當課程代號和課程名稱都存在時才回傳
        if course["課程代號"] and course["課程名稱"]:
            return course
        else:
            return None
            
    except Exception as e:
        # 解析單筆資料失敗時，回傳None
        return None

async def search_courses_crawler(dept_code, start_section, end_section, weekday):
    """
    課程查詢函數 - 使用 Async Playwright 爬蟲 (API 版本)
    🔹 修改：確保返回5門課程名稱不重複的課程
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

            for row in rows:
                course = await extract_course_info(row)
                if course:
                    courses.append(course)

            await browser.close()
            
            # 🔹 確保課程名稱不重複，最多返回5門課程
            unique_courses = ensure_unique_courses(courses, max_courses=5)
            
            return {
                "success": True,
                "total_courses": len(unique_courses),
                "courses": unique_courses,
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

async def search_courses_by_name_crawler(course_name_keyword):
    """
    🔹 修改：根據課程名稱關鍵字查詢課程，確保返回5門課程名稱不重複的課程
    使用輔仁大學課程查詢系統的科目資料查詢功能
    
    Args:
        course_name_keyword (str): 課程名稱關鍵字
        
    Returns:
        dict: 包含查詢結果的 JSON 格式數據
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # 導航至輔仁大學課程查詢系統
            await page.goto("http://estu.fju.edu.tw/fjucourse/Secondpage.aspx")

            # 點擊依科目資料查詢
            await page.click("input[value='依科目資料查詢']")

            # 等待頁面載入
            await page.wait_for_timeout(1000)

            # 在課程名稱欄位輸入關鍵字
            await page.fill("input[name='Txt_CouCna']", course_name_keyword)

            # 點擊查詢按鈕
            await page.click("input[name='But_Run']")

            # 等待查詢結果載入
            await page.wait_for_timeout(3000)

            # 獲取課程列表
            rows = await page.query_selector_all("table#GV_CourseList tr[style*='background-color:White']")
            courses = []

            for row in rows:
                course = await extract_course_info(row)
                if course:
                    courses.append(course)

            await browser.close()
            
            # 🔹 確保課程名稱不重複，最多返回5門課程
            unique_courses = ensure_unique_courses(courses, max_courses=5)
            
            return {
                "success": True,
                "total_courses": len(unique_courses),
                "courses": unique_courses,
                "search_keyword": course_name_keyword,
                "search_type": "course_name"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "courses": [],
            "search_keyword": course_name_keyword,
            "search_type": "course_name"
        }

async def search_courses_by_teacher_crawler(teacher_name):
    """
    🔹 新增：根據教師姓名查詢課程
    使用輔仁大學課程查詢系統的授課教師查詢功能
    
    Args:
        teacher_name (str): 教師姓名
        
    Returns:
        dict: 包含查詢結果的 JSON 格式數據
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # 導航至輔仁大學課程查詢系統
            await page.goto("http://estu.fju.edu.tw/fjucourse/Secondpage.aspx")

            # 點擊依授課教師查詢
            await page.click("input[value='依授課教師查詢']")

            # 等待頁面載入
            await page.wait_for_timeout(1000)

            # 在教師姓名欄位輸入教師姓名
            await page.fill("input[name='Txt_TchCna']", teacher_name)

            # 點擊查詢按鈕
            await page.click("input[name='But_Run']")

            # 等待查詢結果載入
            await page.wait_for_timeout(3000)

            # 獲取課程列表
            rows = await page.query_selector_all("table#GV_CourseList tr[style*='background-color:White']")
            courses = []

            for row in rows:
                course = await extract_course_info(row)
                if course:
                    courses.append(course)

            await browser.close()
            
            # 🔹 確保課程名稱不重複，最多返回5門課程
            unique_courses = ensure_unique_courses(courses, max_courses=5)
            
            return {
                "success": True,
                "total_courses": len(unique_courses),
                "courses": unique_courses,
                "search_teacher": teacher_name,
                "search_type": "teacher_name"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "courses": [],
            "search_teacher": teacher_name,
            "search_type": "teacher_name"
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
    🔹 修改：確保返回5門課程名稱不重複的課程
    
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

def course_name_search_api(course_name_keyword: str) -> dict:
    """
    🔹 修改：課程名稱搜尋 API 函數，確保返回5門課程名稱不重複的課程
    根據課程名稱關鍵字查詢課程
    
    Args:
        course_name_keyword (str): 課程名稱關鍵字
        
    Returns:
        dict: 包含查詢結果的 JSON 格式數據
    """
    try:
        # 執行異步爬蟲查詢
        result = run_async_in_sync(search_courses_by_name_crawler(course_name_keyword))
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"課程名稱搜尋發生錯誤：{str(e)}",
            "search_keyword": course_name_keyword,
            "search_type": "course_name",
            "courses": []
        }

def teacher_course_search_api(teacher_name: str) -> dict:
    """
    🔹 新增：教師課程搜尋 API 函數
    根據教師姓名查詢該教師開設的課程，確保返回5門課程名稱不重複的課程
    
    Args:
        teacher_name (str): 教師姓名
        
    Returns:
        dict: 包含查詢結果的 JSON 格式數據
    """
    try:
        # 執行異步爬蟲查詢
        result = run_async_in_sync(search_courses_by_teacher_crawler(teacher_name))
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"教師課程搜尋發生錯誤：{str(e)}",
            "search_teacher": teacher_name,
            "search_type": "teacher_name",
            "courses": []
        }

def format_courses_for_agent(search_result: dict) -> str:
    """
    🔹 統一格式版本：格式化課程搜尋結果，完全使用垂直清單格式
    確保所有課程資訊都像「社會通識課程」那樣整齊排列
    🔹 新增：課程大綱查詢提醒
    🔹 修改：支援教師姓名搜尋結果格式化
    
    Args:
        search_result (dict): course_search_api 或 course_name_search_api 或 teacher_course_search_api 返回的結果
        
    Returns:
        str: 格式化後的課程資訊字串
    """
    if not search_result.get('success', False):
        return f"課程搜尋失敗：{search_result.get('error', '未知錯誤')}"
    
    courses = search_result.get('courses', [])
    
    if not courses:
        search_type = search_result.get('search_type', 'unknown')
        if search_type == 'course_name':
            keyword = search_result.get('search_keyword', '')
            base_message = f"未找到包含「{keyword}」關鍵字的課程，請嘗試其他關鍵字。"
        elif search_type == 'teacher_name':
            teacher_name = search_result.get('search_teacher', '')
            base_message = f"未找到「{teacher_name}」老師開設的課程，請確認教師姓名是否正確。"
        else:
            base_message = "未找到符合條件的課程，請嘗試調整查詢條件。"
        
        # 即使沒找到課程也提供課程大綱查詢提醒
        return base_message + "\n\n📋 **課程大綱查詢提醒：**\n如需查看詳細課程大綱，可至開課查詢網站（http://estu.fju.edu.tw/fjucourse/Secondpage.aspx）或 Tronclass 的課程資訊中查看。"
    
    # 🔹 使用純文字格式，完全垂直顯示課程資訊
    course_count = len(courses)
    
    # 根據搜尋類型顯示不同的標題
    if search_result.get('search_type') == 'course_name':
        keyword = search_result.get('search_keyword', '')
        result = f"找到 {course_count} 門包含「{keyword}」的課程：\n\n"
    elif search_result.get('search_type') == 'teacher_name':
        teacher_name = search_result.get('search_teacher', '')
        result = f"找到 {course_count} 門「{teacher_name}」老師開設的課程：\n\n"
    else:
        result = f"找到 {course_count} 門課程：\n\n"
    
    for i, course in enumerate(courses, 1):
        # 🔹 課程編號和名稱
        result += f"{i}. {course['課程名稱']}\n\n"
        
        # 🔹 完全垂直排列所有資訊，每個資訊獨佔一行
        if course['課程代號']:
            result += f"課程代號：{course['課程代號']}\n"
        
        if course['開課單位']:
            result += f"開課單位：{course['開課單位']}\n"
        
        if course['授課教師']:
            result += f"授課教師：{course['授課教師']}\n"
        
        if course['學分']:
            result += f"學分：{course['學分']}\n"
        
        if course['教室']:
            result += f"教室：{course['教室']}\n"
        
        if course['領域']:
            result += f"領域：{course['領域']}\n"
        
        if course['上課時間'] or course['節次']:
            time_str = f"{course['上課時間']} {course['節次']}".strip()
            if time_str:
                result += f"上課時間：{time_str}\n"
        
        # 🔹 課程之間用分隔線和空行分開
        result += "\n" + "─" * 50 + "\n\n"
    
    # 🔹 移除最後多餘的分隔線
    if result.endswith("─" * 50 + "\n\n"):
        result = result[:-53]  # 移除最後的分隔線和空行
    
    # 🔹 添加課程數量提示
    if course_count >= 5:
        result += "\n\n如需查看更多課程，請縮小查詢範圍或使用更具體的條件。"
    
    # 🔹 新增：課程大綱查詢提醒
    result += "\n\n📋 **課程大綱查詢提醒：**\n"
    result += "如需查看詳細課程大綱，可至開課查詢網站（http://estu.fju.edu.tw/fjucourse/Secondpage.aspx）或 Tronclass 的課程資訊中查看。"
    
    return result

# 使用範例
if __name__ == "__main__":
    # API 使用範例
    test_queries = [
        "星期一早上的人文通識",
        "資管系的課程", 
        "星期三下午的社會科學課程"
    ]
    
    test_keywords = [
        "倫理學",
        "程式設計",
        "資料庫"
    ]
    
    test_teachers = [
        "謝錦偉",
        "陳建良"
    ]
    
    print("=== 條件查詢測試 ===")
    for query in test_queries:
        print(f"\n測試查詢: {query}")
        print("-" * 50)
        
        # 獲取 JSON 結果
        result = course_search_api(query)
        
        # 格式化顯示給 Agent
        formatted_result = format_courses_for_agent(result)
        print(formatted_result)
        print("=" * 50)
    
    print("\n=== 課程名稱關鍵字查詢測試 ===")
    for keyword in test_keywords:
        print(f"\n測試關鍵字: {keyword}")
        print("-" * 50)
        
        # 獲取 JSON 結果
        result = course_name_search_api(keyword)
        
        # 格式化顯示給 Agent
        formatted_result = format_courses_for_agent(result)
        print(formatted_result)
        print("=" * 50)
        
    print("\n=== 教師課程查詢測試 ===")
    for teacher in test_teachers:
        print(f"\n測試教師: {teacher}")
        print("-" * 50)
        
        # 獲取 JSON 結果
        result = teacher_course_search_api(teacher)
        
        # 格式化顯示給 Agent
        formatted_result = format_courses_for_agent(result)
        print(formatted_result)
        print("=" * 50)