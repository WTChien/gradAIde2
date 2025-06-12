from playwright.async_api import async_playwright
import json
import sys
import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

async def smart_recommend_courses(query: str, headless: bool = True) -> str:
    """
    🧠 智能課程推薦 - 解析自然語言查詢，不使用搜尋框，純粹透過分類和排序推薦
    """
    parsed_params = parse_natural_query(query)
    
    review_data = await _extract_by_category_sort(
        category=parsed_params['category'],
        sort_method=parsed_params['sort_method'],
        headless=headless
    )
    
    if review_data.get("success"):
        review_data["parsed_query"] = {
            "original_query": query,
            "parsed_params": parsed_params,
            "confidence": parsed_params["confidence"]
        }
        review_data["search_mode"] = "smart_recommend"
    
    markdown_result = format_smart_recommend_to_markdown(review_data)
    return markdown_result

async def search_by_course_name(course_name: str, 
                         category: str = "所有評價",
                         sort_method: str = "推薦高至低",
                         headless: bool = True) -> str:
    """
    📚 課程名稱搜尋 - 在搜尋框輸入課程關鍵字進行搜尋
    """
    review_data = await _extract_with_keyword_search(
        keyword=course_name,
        category=category,
        sort_method=sort_method,
        search_type="course",
        headless=headless
    )
    
    review_data["search_mode"] = "course_search"
    markdown_result = format_search_to_markdown(review_data)
    return markdown_result

async def search_by_teacher_name(teacher_name: str,
                          category: str = "所有評價", 
                          sort_method: str = "推薦高至低",
                          headless: bool = True) -> str:
    """
    👨‍🏫 教師姓名搜尋 - 在搜尋框輸入教師姓名進行搜尋
    """
    review_data = await _extract_with_keyword_search(
        keyword=teacher_name,
        category=category,
        sort_method=sort_method,
        search_type="teacher",
        headless=headless
    )
    
    review_data["search_mode"] = "teacher_search"
    markdown_result = format_search_to_markdown(review_data)
    return markdown_result

async def _extract_by_category_sort(category: str, sort_method: str, headless: bool = True) -> Dict[str, Any]:
    """純粹透過分類和排序進行推薦，不使用關鍵字搜尋"""
    result = []
    
    category_mapping = {
        "所有評價": "所有評價",
        "人文通識評價": "人文通識評價", 
        "自然通識評價": "自然通識評價",
        "社會通識評價": "社會通識評價",
        "體育評價": "體育評價"
    }
    
    sort_mapping = {
        "推薦高至低": "推薦高至低",
        "作業低至高": "作業低至高", 
        "考試少至多": "考試少至多",
        "收穫高至低": "收穫高至低",
        "有趣高至低": "有趣高至低",
        "要求少至多": "要求少至多",
        "時間新至舊": "時間新至舊"
    }
    
    if category not in category_mapping:
        return {
            "success": False,
            "message": f"不支援的分類: {category}",
            "data": [],
            "search_params": {"category": category, "sort_method": sort_method}
        }
    
    if sort_method not in sort_mapping:
        return {
            "success": False,
            "message": f"不支援的排序方式: {sort_method}",
            "data": [],
            "search_params": {"category": category, "sort_method": sort_method}
        }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        
        try:
            await page.goto("https://classin.info/view")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            if category != "所有評價":
                try:
                    category_button = page.locator(f"button:has-text('{category}')")
                    await category_button.wait_for(timeout=5000)
                    await category_button.click()
                    await asyncio.sleep(3)
                except Exception:
                    pass

            try:
                sort_button = page.locator(f"button:has-text('{sort_method}')")
                await sort_button.wait_for(timeout=5000)
                await sort_button.click()
                await asyncio.sleep(6)
            except Exception:
                pass
            
            cards_found, final_cards = await _find_review_cards(page, 5)
            
            if not cards_found:
                return {
                    "success": False,
                    "message": f"未找到符合條件的推薦課程",
                    "data": [],
                    "search_params": {"category": category, "sort_method": sort_method}
                }

            if len(final_cards) > 5:
                final_cards = final_cards[:5]
            
            for card in final_cards:
                try:
                    review_data = await _parse_review_card(card)
                    if review_data:
                        result.append(review_data)
                except Exception:
                    continue

        except Exception as e:
            return {
                "success": False,
                "message": f"推薦失敗: {str(e)}",
                "data": [],
                "search_params": {"category": category, "sort_method": sort_method}
            }
        finally:
            await browser.close()

    if not result:
        return {
            "success": False,
            "message": f"沒有找到符合條件的推薦課程",
            "data": [],
            "search_params": {"category": category, "sort_method": sort_method}
        }
    
    return {
        "success": True,
        "message": f"成功推薦 {len(result)} 筆課程",
        "data": result,
        "search_params": {
            "category": category, 
            "sort_method": sort_method
        },
        "statistics": _calculate_statistics(result)
    }

async def _extract_with_keyword_search(keyword: str, category: str, sort_method: str, search_type: str, headless: bool = True) -> Dict[str, Any]:
    """使用關鍵字搜尋框進行搜尋（課程名稱或教師姓名）"""
    result = []
    
    search_type_names = {
        "course": "課程名稱",
        "teacher": "教師姓名"
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        
        try:
            await page.goto("https://classin.info/view")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            search_input = page.locator("input[placeholder='評價編號、課程名稱或教師姓名']")
            await search_input.wait_for(timeout=5000)
            await search_input.scroll_into_view_if_needed()

            while not await search_input.is_visible():
                await asyncio.sleep(0.5)

            await search_input.click()
            await search_input.fill(keyword)
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)

            if category != "所有評價":
                try:
                    category_button = page.locator(f"button:has-text('{category}')")
                    await category_button.wait_for(timeout=5000)
                    await category_button.click()
                    await asyncio.sleep(3)
                except Exception:
                    pass

            try:
                sort_button = page.locator(f"button:has-text('{sort_method}')")
                await sort_button.wait_for(timeout=5000)
                await sort_button.click()
                await asyncio.sleep(6)
            except Exception:
                pass
            
            cards_found, final_cards = await _find_review_cards(page, 5)
            
            if not cards_found:
                return {
                    "success": False,
                    "message": f"未找到 '{keyword}' 的{search_type_names[search_type]}搜尋結果",
                    "data": [],
                    "search_params": {"keyword": keyword, "category": category, "sort_method": sort_method, "search_type": search_type}
                }

            if len(final_cards) > 5:
                final_cards = final_cards[:5]
            
            for card in final_cards:
                try:
                    review_data = await _parse_review_card(card)
                    if review_data:
                        result.append(review_data)
                except Exception:
                    continue

        except Exception as e:
            return {
                "success": False,
                "message": f"搜尋失敗: {str(e)}",
                "data": [],
                "search_params": {"keyword": keyword, "category": category, "sort_method": sort_method, "search_type": search_type}
            }
        finally:
            await browser.close()

    if not result:
        return {
            "success": False,
            "message": f"沒有找到 '{keyword}' 的{search_type_names[search_type]}搜尋結果",
            "data": [],
            "search_params": {"keyword": keyword, "category": category, "sort_method": sort_method, "search_type": search_type}
        }
    
    return {
        "success": True,
        "message": f"成功找到 {len(result)} 筆 '{keyword}' 的{search_type_names[search_type]}搜尋結果",
        "data": result,
        "search_params": {
            "keyword": keyword,
            "category": category, 
            "sort_method": sort_method,
            "search_type": search_type
        },
        "statistics": _calculate_statistics(result)
    }

def parse_natural_query(query: str) -> Dict[str, Any]:
    """解析自然語言查詢，提取搜尋參數"""
    params = {
        "category": "所有評價",
        "sort_method": "推薦高至低",
        "confidence": 0.0
    }
    
    query_lower = query.lower()
    
    category_keywords = {
        "人文通識": ["人文", "文學", "哲學", "藝術", "語言", "英文", "中文", "外語"],
        "自然通識": ["自然", "數學", "物理", "化學", "生物", "地理", "環境", "天文"],
        "社會通識": ["社會", "經濟", "政治", "法律", "社會學", "心理", "管理", "商業", "歷史", "古代", "近代", "世界史", "台灣史", "中國史"],
        "體育": ["體育", "運動", "健身", "球類", "游泳", "跑步", "網球", "籃球", "足球", "羽球", "桌球"]
    }
    
    sort_keywords = {
        "推薦高至低": ["推薦", "好評", "評價高", "口碑", "熱門", "受歡迎"],
        "作業低至高": ["作業少", "輕鬆", "不累", "作業輕", "負擔輕"],
        "考試少至多": ["考試少", "不考試", "免考", "期末報告"],
        "收穫高至低": ["收穫", "學到", "有用", "實用", "學習"],
        "有趣高至低": ["有趣", "好玩", "不無聊", "生動", "活潑"],
        "要求少至多": ["要求低", "門檻低", "簡單", "容易過"],
        "時間新至舊": ["最新", "新的", "近期", "最近"]
    }
    
    confidence = 0.0
    
    # 解析分類
    category_found = False
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in query_lower:
                if category == "體育":
                    params["category"] = "體育評價"
                else:
                    params["category"] = f"{category}評價"
                category_found = True
                confidence += 0.4
                break
        if category_found:
            break
    
    # 解析排序偏好
    sort_found = False
    for sort_method, keywords in sort_keywords.items():
        for keyword in keywords:
            if keyword in query_lower:
                params["sort_method"] = sort_method
                sort_found = True
                confidence += 0.3
                break
        if sort_found:
            break
    
    # 判斷查詢意圖
    if any(word in query_lower for word in ["推薦", "建議", "介紹", "有什麼", "哪些"]):
        confidence += 0.3
    
    params["confidence"] = confidence
    return params

def format_smart_recommend_to_markdown(review_data: Dict[str, Any]) -> str:
    """將智能推薦結果格式化為 Markdown，包含解析資訊"""
    
    if not review_data.get("success"):
        parsed_info = review_data.get("parsed_query", {})
        if parsed_info:
            return f"""# 🧠 智能課程推薦結果

## 查詢解析
- **原始查詢**: {parsed_info.get('original_query', '未知')}
- **解析信心度**: {parsed_info.get('confidence', 0):.2f}

## 推薦失敗
{review_data.get('message', '未知錯誤')}
"""
        else:
            return f"## 推薦失敗\n\n{review_data.get('message', '未知錯誤')}"
    
    data = review_data["data"]
    search_params = review_data.get("search_params", {})
    statistics = review_data.get("statistics", {})
    parsed_query = review_data.get("parsed_query", {})
    
    if not data:
        return f"""# 🧠 智能課程推薦結果

## 查詢解析
- **原始查詢**: {parsed_query.get('original_query', '未知')}
- **解析信心度**: {parsed_query.get('confidence', 0):.2f}

## 推薦結果
{review_data.get('message', '沒有找到推薦課程')}
"""
    
#     markdown = f"""# 🧠 智能課程推薦結果

# ## 查詢解析
# - **原始查詢**: "{parsed_query.get('original_query', '未知')}"
# - **解析信心度**: {parsed_query.get('confidence', 0):.2f}

# ## 推薦條件
# - **分類**: {search_params.get('category', '所有評價')}
# - **排序方式**: {search_params.get('sort_method', '推薦高至低')}
# - **推薦數量**: 5 (固定)

# ## 推薦統計
# - **課程總數**: {statistics.get('total_reviews', len(data))}
# - **不同課程**: {statistics.get('unique_courses', 0)}
# - **不同教師**: {statistics.get('unique_teachers', 0)}
# - **平均推薦度**: {statistics.get('average_recommendation', 0):.1f}

# """

#     confidence = parsed_query.get('confidence', 0)
#     if confidence < 0.5:
#         markdown += f"""
# > ⚠️ **解析信心度較低 ({confidence:.2f})**  
# > 如果結果不符合預期，建議使用更明確的關鍵字，例如：  
# > - "推薦一些自然通識課程"
# > - "有什麼輕鬆的體育課"
# > - "作業少的人文通識課"

# """

    # if statistics.get('average_course_ratings'):
    #     markdown += "### 平均課程評分\n"
    #     for rating_type, avg_score in statistics['average_course_ratings'].items():
    #         markdown += f"- **{rating_type}**: {avg_score:.1f}星\n"
    #     markdown += "\n"

    markdown = "## 🎯 推薦課程列表\n\n"
    
    for i, review in enumerate(data, 1):
        markdown += f"### 📚 推薦 {i}\n\n"
        
        field_order = ["評價編號", "課程名稱", "教師", "評論", "發布時間", "推薦度", "課程評分", "教師評分", "考試類型"]
        
        for field in field_order:
            if field in review and review[field]:
                value = review[field]
                
                if field in ["課程評分", "教師評分"]:
                    if isinstance(value, dict):
                        rating_str = ", ".join([f"{k}: {v}星" for k, v in value.items()])
                        markdown += f"- **{field}**: {rating_str}\n"
                elif field == "考試類型":
                    if isinstance(value, list):
                        markdown += f"- **{field}**: {', '.join(value)}\n"
                elif field == "推薦度":
                    hearts = "❤️" * value
                    markdown += f"- **{field}**: {hearts} ({value}/5)\n"
                else:
                    markdown += f"- **{field}**: {value}\n"
        
        markdown += "\n---\n\n"
    
    return markdown

def format_search_to_markdown(review_data: Dict[str, Any]) -> str:
    """將搜尋結果格式化為 Markdown"""
    if not review_data.get("success"):
        return f"## 搜尋失敗\n\n{review_data.get('message', '未知錯誤')}"
    
    data = review_data["data"]
    search_params = review_data.get("search_params", {})
    statistics = review_data.get("statistics", {})
    search_mode = review_data.get("search_mode", "search")
    
    if not data:
        return f"## 搜尋結果\n\n{review_data.get('message', '沒有找到搜尋結果')}"
    
    if search_mode == "course_search":
        title = "# 📚 課程名稱搜尋結果"
        search_type_label = "課程關鍵字"
    elif search_mode == "teacher_search":
        title = "# 👨‍🏫 教師姓名搜尋結果"
        search_type_label = "教師姓名"
    else:
        title = "# 🔍 搜尋結果"
        search_type_label = "關鍵字"
    
    markdown = f"""{title}

## 搜尋條件
- **{search_type_label}**: {search_params.get('keyword', '無')}
- **分類**: {search_params.get('category', '所有評價')}
- **排序方式**: {search_params.get('sort_method', '推薦高至低')}
- **結果數量**: 5 (固定)

## 搜尋統計
- **找到評價**: {statistics.get('total_reviews', len(data))}
- **不同課程**: {statistics.get('unique_courses', 0)}
- **不同教師**: {statistics.get('unique_teachers', 0)}
- **平均推薦度**: {statistics.get('average_recommendation', 0):.1f}

"""

    if statistics.get('average_course_ratings'):
        markdown += "### 平均課程評分\n"
        for rating_type, avg_score in statistics['average_course_ratings'].items():
            markdown += f"- **{rating_type}**: {avg_score:.1f}星\n"
        markdown += "\n"

    markdown += "## 🔍 搜尋結果詳情\n\n"
    
    for i, review in enumerate(data, 1):
        markdown += f"### 結果 {i}\n\n"
        
        field_order = ["評價編號", "課程名稱", "教師", "評論", "發布時間", "推薦度", "課程評分", "教師評分", "考試類型"]
        
        for field in field_order:
            if field in review and review[field]:
                value = review[field]
                
                if field in ["課程評分", "教師評分"]:
                    if isinstance(value, dict):
                        rating_str = ", ".join([f"{k}: {v}星" for k, v in value.items()])
                        markdown += f"- **{field}**: {rating_str}\n"
                elif field == "考試類型":
                    if isinstance(value, list):
                        markdown += f"- **{field}**: {', '.join(value)}\n"
                elif field == "推薦度":
                    hearts = "❤️" * value
                    markdown += f"- **{field}**: {hearts} ({value}/5)\n"
                else:
                    markdown += f"- **{field}**: {value}\n"
        
        markdown += "\n---\n\n"
    
    return markdown

def _calculate_statistics(data: List[Dict]) -> Dict[str, Any]:
    """計算評價資料統計"""
    if not data:
        return {}
    
    courses = set(item.get("課程名稱", "") for item in data if item.get("課程名稱"))
    teachers = set(item.get("教師", "") for item in data if item.get("教師"))
    recommendations = [item.get("推薦度", 0) for item in data if item.get("推薦度") is not None]
    
    rating_stats = {}
    for item in data:
        if "課程評分" in item and item["課程評分"]:
            for rating_type, score in item["課程評分"].items():
                if rating_type not in rating_stats:
                    rating_stats[rating_type] = []
                rating_stats[rating_type].append(score)
    
    avg_ratings = {k: sum(v)/len(v) for k, v in rating_stats.items() if v}
    
    return {
        "total_reviews": len(data),
        "unique_courses": len(courses),
        "unique_teachers": len(teachers),
        "average_recommendation": sum(recommendations) / len(recommendations) if recommendations else 0,
        "average_course_ratings": avg_ratings,
        "courses_list": list(courses),
        "teachers_list": list(teachers)
    }

async def _find_review_cards(page, max_wait_time: int):
    """尋找評價卡片元素"""
    cards_found = False
    final_cards = []
    
    possible_selectors = [
        ".Card__CardWrapper-sc-eg2nis-0",
        "[class*='Card'][class*='Wrapper']",
        "[class*='card'][class*='wrapper']",
        ".card",
        "[data-testid*='card']",
        "div[class*='Card']"
    ]
    
    for attempt in range(max_wait_time):
        loading_indicators = await page.query_selector_all("[class*='loading'], [class*='spinner'], .loading")
        if loading_indicators:
            await asyncio.sleep(1)
            continue
        
        for selector in possible_selectors:
            cards = await page.query_selector_all(selector)
            if len(cards) > 0:
                final_cards = cards
                cards_found = True
                break
        
        if cards_found:
            await asyncio.sleep(2)
            break
            
        no_results_selectors = [
            "text=沒有找到相關資料",
            "text=無搜尋結果", 
            "text=沒有結果",
            "[class*='no-result']",
            "[class*='empty']"
        ]
        
        for no_result_selector in no_results_selectors:
            no_result_element = await page.query_selector(no_result_selector)
            if no_result_element:
                return False, []
        
        await asyncio.sleep(1)
    
    return cards_found, final_cards

async def _parse_review_card(card) -> Optional[Dict[str, Any]]:
    """解析單個評價卡片"""
    review_data = {}
    
    review_id_node = await card.query_selector(".Typography__Title-sc-qms70n-0.fkKYpx")
    if review_id_node:
        review_data["評價編號"] = (await review_id_node.inner_text()).strip()
    
    course_section = await card.query_selector(".w-5\\/12, .lg\\:w-3\\/12")
    if course_section:
        title_nodes = await course_section.query_selector_all(".Typography__Title-sc-qms70n-0.fkKYpx")
        if title_nodes:
            review_data["課程名稱"] = (await title_nodes[0].inner_text()).strip()
        
        course_ratings = await _extract_ratings(course_section)
        if course_ratings:
            review_data["課程評分"] = course_ratings
        
        exam_badges = await course_section.query_selector_all(".bg-secondary.rounded")
        if exam_badges:
            exam_types = []
            for badge in exam_badges:
                exam_type = (await badge.inner_text()).strip()
                if exam_type:
                    exam_types.append(exam_type)
            if exam_types:
                review_data["考試類型"] = exam_types

    teacher_section = await card.query_selector(".w-4\\/12.lg\\:w-3\\/12")
    if teacher_section:
        teacher_node = await teacher_section.query_selector(".Typography__Title-sc-qms70n-0.fkKYpx")
        if teacher_node:
            review_data["教師"] = (await teacher_node.inner_text()).strip()
        
        teacher_ratings = await _extract_ratings(teacher_section)
        if teacher_ratings:
            review_data["教師評分"] = teacher_ratings

    comment_node = await card.query_selector("pre")
    if comment_node:
        comment = (await comment_node.inner_text()).strip()
        if comment:
            review_data["評論"] = comment
        
        timestamp = await _extract_timestamp(comment_node)
        if timestamp:
            review_data["發布時間"] = timestamp

    recommendation_section = await card.query_selector(".lg\\:w-4\\/12")
    if recommendation_section:
        hearts = await recommendation_section.query_selector_all("svg.text-primary path[fill-rule='evenodd'][d*='5.172a4']")
        if hearts:
            review_data["推薦度"] = len(hearts)

    return review_data if review_data else None

async def _extract_ratings(section) -> Optional[Dict[str, int]]:
    """從區塊中提取評分資訊"""
    ratings = {}
    rating_sections = await section.query_selector_all(".md\\:flex.items-center")
    
    for rating_section in rating_sections:
        label_node = await rating_section.query_selector(".Typography__SubTitle-sc-qms70n-1.jybTmf")
        if label_node:
            label = (await label_node.inner_text()).strip()
            star_container = await rating_section.query_selector(".flex.items-center")
            if star_container:
                filled_stars = await star_container.query_selector_all("svg.text-primary")
                if filled_stars:
                    ratings[label] = len(filled_stars)
    
    return ratings if ratings else None

async def _extract_timestamp(comment_node) -> Optional[str]:
    """提取時間戳記"""
    try:
        parent = await comment_node.evaluate_handle("e => e.parentElement")
        siblings = await parent.query_selector_all("div")
        for sibling in siblings:
            text = (await sibling.inner_text()).strip()
            if "/" in text and ":" in text:
                return text
    except:
        pass
    return None

def get_available_options() -> Dict[str, List[str]]:
    """獲取所有可用的選項"""
    return {
        "categories": [
            "所有評價", 
            "人文通識評價", 
            "自然通識評價", 
            "社會通識評價", 
            "體育評價"
        ],
        "sort_methods": [
            "推薦高至低", 
            "作業低至高", 
            "考試少至多", 
            "收穫高至低", 
            "有趣高至低", 
            "要求少至多", 
            "時間新至舊"
        ]
    }

# 命令列介面（簡化版，僅用於測試）
async def main():
    """主要執行函數"""
    if len(sys.argv) < 2:
        options = get_available_options()
        print(f"""
🧠 智能課程評價系統 - 三合一搜尋模式 (異步版本)

使用方式:
1. 智能推薦模式 (自然語言，不使用搜尋框):
   python extract_reviews.py smart "可以推薦我一些自然通識課嘛？" [--headless]

2. 課程名稱搜尋模式:
   python extract_reviews.py course [課程名稱] [分類] [排序方式] [--headless]

3. 教師姓名搜尋模式:
   python extract_reviews.py teacher [教師姓名] [分類] [排序方式] [--headless]

支援的分類: {', '.join(options['categories'])}
支援的排序: {', '.join(options['sort_methods'])}
        """)
        return
    
    command = sys.argv[1]
    headless_mode = "--headless" in sys.argv
    
    if command == "smart":
        if len(sys.argv) < 3:
            return
        
        query = sys.argv[2]
        result = await smart_recommend_courses(query, headless=headless_mode)
        print(result)
        
    elif command == "course":
        course_name = sys.argv[2] if len(sys.argv) > 2 else ""
        if not course_name:
            return
        
        category = sys.argv[3] if len(sys.argv) > 3 else "所有評價"
        sort_method = sys.argv[4] if len(sys.argv) > 4 else "推薦高至低"
        
        result = await search_by_course_name(
            course_name=course_name,
            category=category, 
            sort_method=sort_method,
            headless=headless_mode
        )
        print(result)
        
    elif command == "teacher":
        teacher_name = sys.argv[2] if len(sys.argv) > 2 else ""
        if not teacher_name:
            return
        
        category = sys.argv[3] if len(sys.argv) > 3 else "所有評價"
        sort_method = sys.argv[4] if len(sys.argv) > 4 else "推薦高至低"
        
        result = await search_by_teacher_name(
            teacher_name=teacher_name,
            category=category, 
            sort_method=sort_method,
            headless=headless_mode
        )
        print(result)
        
    elif command == "options":
        options = get_available_options()
        print(f"\n📋 可用選項:")
        print(f"📂 分類: {', '.join(options['categories'])}")
        print(f"🔄 排序: {', '.join(options['sort_methods'])}")

if __name__ == "__main__":
    asyncio.run(main())