import os
import asyncio
import concurrent.futures
from opencc import OpenCC
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_firestore import FirestoreVectorStore
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
from langchain.tools.retriever import create_retriever_tool
from autogen import register_function
from langchain_core.messages import HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
from langchain_core.documents import Document

# 🔹 導入課程搜尋 API (包含課程大綱網址)
from course_search import course_search_api, course_name_search_api, teacher_course_search_api, format_courses_for_agent

# 🔹 導入課程評價爬蟲工具 - 異步版本
from extract_reviews import (
    smart_recommend_courses, 
    search_by_course_name, 
    search_by_teacher_name
)

if not firebase_admin._apps:
    cred = credentials.Certificate("/home/a411401516/gradAIde_shared/local/backend/gradaide5-firebase-adminsdk-fbsvc-1f64c30917.json")
    firebase_admin.initialize_app(cred)

# 讀取環境變數
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["USER_AGENT"] = os.getenv("USER_AGENT")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/a411401516/gradAIde_shared/local/backend/gradaide5-firebase-adminsdk-fbsvc-1f64c30917.json"

PROJECT_ID = os.getenv("PROJECT_ID")

retriever_tools = []  # 全域 retriever 工具集合
global_embedding = None  # 全域 embedding 模型

# 🔹 FAQ配置 - 使用真實相似度分數計算，返回3筆資料
FAQ_CONFIG = {
    "RELEVANCE_THRESHOLD": 0.7,  # 相關性閾值（真實餘弦相似度分數）
    "MAX_RESULTS": 2,            # 最大檢索結果數改為3
    "AUTO_SEARCH": True,         # 是否每次都自動搜尋
    "LOG_SCORES": True,          # 是否記錄相關性分數
    "USE_SIMILARITY": True,      # 使用相似度檢索
    "REAL_SCORES": True          # 計算真實相似度分數
}

SPLITTER_CONFIG = {
    "chunk_size": 200,           # 設定很小，強制分割
    "chunk_overlap": 0,          # 不使用重疊
    "separators": ["。"],        # 只用句號分割
    "length_function": len,      # 使用字符數計算長度
    "is_separator_regex": False, # 不使用正則表達式
    "keep_separator": True       # 保留句號
}

# **🔹 課程搜尋工具（使用爬蟲）**
def course_search(query: str) -> str:
    """
    課程搜尋工具 - 使用自然語言查詢開課資訊（依系所、時間、星期等條件）
    這個工具會解析自然語言查詢，並爬取智慧大學課程查詢系統
    適用於有明確系所、時間或星期條件的查詢
    查詢結果會包含課程大綱查詢提醒
    🔹 修改：確保返回5門課程名稱不重複的課程
    
    Args:
        query (str): 自然語言查詢字串，例如「星期一早上的人文通識」、「資管系的課程」
        
    Returns:
        str: 格式化的課程查詢結果，含課程大綱查詢提醒
    """
    try:
        # 使用 API 化的課程搜尋函數（已包含大綱查詢提醒）
        search_result = course_search_api(query)
        
        # 將結果格式化為適合 Agent 閱讀的格式
        formatted_result = format_courses_for_agent(search_result)
        
        return formatted_result
        
    except Exception as e:
        return f"❌ 課程搜尋發生錯誤：{str(e)}"

# **🔹 課程名稱關鍵字搜尋工具**
def course_name_search(course_name_keyword: str) -> str:
    """
    課程名稱關鍵字搜尋工具 - 根據課程名稱關鍵字查詢課程
    適用於想要找特定名稱或包含特定關鍵字的課程
    查詢結果會包含課程大綱查詢提醒
    🔹 修改：確保返回5門課程名稱不重複的課程
    
    Args:
        course_name_keyword (str): 課程名稱關鍵字，例如「倫理學」、「程式設計」、「資料庫」
        
    Returns:
        str: 格式化的課程查詢結果，含課程大綱查詢提醒
    """
    try:
        # 使用 API 化的課程名稱搜尋函數（已包含大綱查詢提醒）
        search_result = course_name_search_api(course_name_keyword)
        
        # 將結果格式化為適合 Agent 閱讀的格式
        formatted_result = format_courses_for_agent(search_result)
        
        return formatted_result
        
    except Exception as e:
        return f"❌ 課程名稱搜尋發生錯誤：{str(e)}" 

# **🔹 新增：教師課程搜尋工具**
def teacher_course_search(teacher_name: str) -> str:
    """
    教師課程搜尋工具 - 根據教師姓名查詢該教師開設的課程
    這個工具會在智慧大學課程查詢系統中搜尋指定教師開設的所有課程
    適用於想了解特定教師開課情況的查詢
    查詢結果會包含課程大綱查詢提醒
    🔹 確保返回5門課程名稱不重複的課程
    
    Args:
        teacher_name (str): 教師姓名，例如「謝錦偉」、「陳建良」
        
    Returns:
        str: 格式化的教師課程查詢結果，含課程大綱查詢提醒
    """
    try:
        # 使用新增的教師課程搜尋函數
        search_result = teacher_course_search_api(teacher_name)
        
        # 將結果格式化為適合 Agent 閱讀的格式
        formatted_result = format_courses_for_agent(search_result)
        
        return formatted_result
        
    except Exception as e:
        return f"❌ 教師課程搜尋發生錯誤：{str(e)}"

# **🔹 異步課程評價工具（內部使用）**
async def smart_course_review_recommend_async(query: str) -> str:
    """
    智能課程評價推薦工具 - 異步版本（內部使用）
    """
    try:
        print(f"🧠 開始智能課程評價推薦，查詢：{query}")
        result = await smart_recommend_courses(query, headless=True)
        return result
    except Exception as e:
        return f"❌ 智能課程評價推薦發生錯誤：{str(e)}"

async def course_review_search_async(course_name: str, category: str = "所有評價", sort_method: str = "推薦高至低") -> str:
    """
    課程名稱評價搜尋工具 - 異步版本（內部使用）
    """
    try:
        print(f"📚 開始課程名稱評價搜尋，課程：{course_name}，分類：{category}，排序：{sort_method}")
        result = await search_by_course_name(
            course_name=course_name,
            category=category,
            sort_method=sort_method,
            headless=True
        )
        return result
    except Exception as e:
        return f"❌ 課程名稱評價搜尋發生錯誤：{str(e)}"

async def teacher_review_search_async(teacher_name: str, category: str = "所有評價", sort_method: str = "推薦高至低") -> str:
    """
    教師姓名評價搜尋工具 - 異步版本（內部使用）
    """
    try:
        print(f"👨‍🏫 開始教師姓名評價搜尋，教師：{teacher_name}，分類：{category}，排序：{sort_method}")
        result = await search_by_teacher_name(
            teacher_name=teacher_name,
            category=category,
            sort_method=sort_method,
            headless=True
        )
        return result
    except Exception as e:
        return f"❌ 教師姓名評價搜尋發生錯誤：{str(e)}"

# **🔹 同步包裝器工具（供 AutoGen 使用）**
def smart_course_review_recommend(query: str) -> str:
    """
    智能課程評價推薦工具 - 使用自然語言查詢推薦課程評價
    
    這個工具會解析自然語言查詢，自動判斷分類和排序方式，從 classin.info 獲取推薦課程評價。
    適用於模糊查詢和自然語言描述，例如：
    - "推薦一些自然通識課程"
    - "有什麼輕鬆的體育課"
    - "作業少的人文通識課"
    - "想要找有趣的數學課"
    
    Args:
        query (str): 自然語言查詢字串，描述想要的課程特性
        
    Returns:
        str: Markdown 格式的智能推薦結果，包含解析資訊、推薦條件、統計資料和課程詳情
    """
    try:
        # 檢查是否已經在事件循環中
        try:
            loop = asyncio.get_running_loop()
            # 在現有事件循環中，使用執行緒池執行異步函數
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, smart_course_review_recommend_async(query))
                return future.result()
        except RuntimeError:
            # 沒有運行中的事件循環，直接運行
            return asyncio.run(smart_course_review_recommend_async(query))
    except Exception as e:
        return f"❌ 智能課程評價推薦發生錯誤：{str(e)}"

def course_review_search(course_name: str, category: str = "所有評價", sort_method: str = "推薦高至低") -> str:
    """
    課程名稱評價搜尋工具 - 根據課程名稱搜尋評價
    
    這個工具會在 classin.info 的搜尋框中輸入課程名稱進行搜尋，
    適用於想了解特定課程的學生評價和推薦度。
    
    Args:
        course_name (str): 課程名稱或關鍵字，例如「網球」、「程式設計」、「英文」
        category (str): 評價分類，可選項目：
                       "所有評價", "人文通識評價", "自然通識評價", 
                       "社會通識評價", "體育評價"
        sort_method (str): 排序方式，可選項目：
                          "推薦高至低", "作業低至高", "考試少至多", 
                          "收穫高至低", "有趣高至低", "要求少至多", "時間新至舊"
        
    Returns:
        str: Markdown 格式的課程評價搜尋結果，包含評價詳情、推薦度、評分等資訊
    """
    try:
        # 檢查是否已經在事件循環中
        try:
            loop = asyncio.get_running_loop()
            # 在現有事件循環中，使用執行緒池執行異步函數
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, course_review_search_async(course_name, category, sort_method))
                return future.result()
        except RuntimeError:
            # 沒有運行中的事件循環，直接運行
            return asyncio.run(course_review_search_async(course_name, category, sort_method))
    except Exception as e:
        return f"❌ 課程名稱評價搜尋發生錯誤：{str(e)}"

def teacher_review_search(teacher_name: str, category: str = "所有評價", sort_method: str = "推薦高至低") -> str:
    """
    教師姓名評價搜尋工具 - 根據教師姓名搜尋評價
    
    這個工具會在 classin.info 的搜尋框中輸入教師姓名進行搜尋，
    適用於想了解特定教師的教學評價和學生回饋。
    
    Args:
        teacher_name (str): 教師姓名，例如「謝錦偉」、「王小明」
        category (str): 評價分類，可選項目：
                       "所有評價", "人文通識評價", "自然通識評價", 
                       "社會通識評價", "體育評價"
        sort_method (str): 排序方式，可選項目：
                          "推薦高至低", "作業低至高", "考試少至多", 
                          "收穫高至低", "有趣高至低", "要求少至多", "時間新至舊"
        
    Returns:
        str: Markdown 格式的教師評價搜尋結果，包含評價詳情、推薦度、評分等資訊
    """
    try:
        # 檢查是否已經在事件循環中
        try:
            loop = asyncio.get_running_loop()
            # 在現有事件循環中，使用執行緒池執行異步函數
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, teacher_review_search_async(teacher_name, category, sort_method))
                return future.result()
        except RuntimeError:
            # 沒有運行中的事件循環，直接運行
            return asyncio.run(teacher_review_search_async(teacher_name, category, sort_method))
    except Exception as e:
        return f"❌ 教師姓名評價搜尋發生錯誤：{str(e)}"

# **🔹 FAQ檢索系統 - 使用相似度檢索，返回2筆資料，嚴格閾值過濾**
def faq_universal_search(query: str, relevance_threshold: float = 0.7) -> dict:
    """
    FAQ資料庫檢索 - 計算真實餘弦相似度分數，返回3筆最相關的資料，嚴格按閾值過濾
    
    Args:
        query (str): 使用者問題
        relevance_threshold (float): 相關性閾值（餘弦相似度分數）
        
    Returns:
        dict: 包含檢索結果和相關資訊
    """
    print(f"🔍 FAQ相似度檢索，查詢：{query}")
    
    # 檢查向量資料庫是否已初始化
    if vectordb is None:
        print("❌ vectordb 為 None，尚未初始化")
        return {
            "results": [],
            "max_score": 0,
            "should_use": False,
            "threshold": relevance_threshold,
            "query": query,
            "error": "向量資料庫尚未初始化"
        }
    
    if "faq" not in vectordb:
        print("❌ FAQ向量資料庫不存在於 vectordb 中")
        return {
            "results": [],
            "max_score": 0,
            "should_use": False,
            "threshold": relevance_threshold,
            "query": query,
            "error": "FAQ向量資料庫不存在"
        }
    
    try:
        print("🔍 開始執行相似度檢索...")
        # 使用 Firestore 支援的 similarity_search，檢索3筆資料
        docs = vectordb["faq"].similarity_search(query, k=3)
        print(f"✅ 相似度檢索完成，找到 {len(docs)} 個結果")
        
        # 獲取embedding模型來計算相似度分數
        # 使用全域embedding模型或創建新的
        global global_embedding
        if global_embedding is None:
            from langchain_ollama import OllamaEmbeddings
            global_embedding = OllamaEmbeddings(model="bge-m3:latest")
        
        embedding_model = global_embedding
        
        query_vector = embedding_model.embed_query(query)
        
        results = []
        for i, doc in enumerate(docs):
            try:
                # 根據你的資料庫結構解析
                # page_content 直接就是問題文本
                question = doc.page_content
                
                # 答案從嵌套的 metadata 中獲取
                # 根據調試信息，實際結構是 metadata.metadata.answer
                nested_metadata = doc.metadata.get('metadata', {})
                answer = nested_metadata.get('answer', 'N/A')
                
                # 添加調試信息來查看metadata結構
                print(f"  📋 metadata keys: {list(doc.metadata.keys())}")
                print(f"  📋 nested metadata keys: {list(nested_metadata.keys()) if nested_metadata else 'None'}")
                
                # 如果嵌套metadata中沒有answer，嘗試其他位置
                if answer == 'N/A':
                    # 檢查直接metadata
                    answer = doc.metadata.get('answer', 'N/A')
                    if answer != 'N/A':
                        print(f"  ✅ 找到答案在直接metadata中")
                    else:
                        # 檢查其他可能的鍵名
                        for key in ['Answer', 'response', 'Response', 'reply', 'Reply']:
                            if key in nested_metadata:
                                answer = nested_metadata[key]
                                print(f"  ✅ 找到答案在嵌套metadata的鍵: {key}")
                                break
                            elif key in doc.metadata:
                                answer = doc.metadata[key]
                                print(f"  ✅ 找到答案在直接metadata的鍵: {key}")
                                break
                        
                        # 如果還是找不到，嘗試尋找包含中文的值
                        if answer == 'N/A':
                            for key, value in nested_metadata.items():
                                if isinstance(value, str) and len(value) > 10:  # 可能是答案
                                    answer = value
                                    print(f"  ✅ 使用嵌套metadata中較長的文字作為答案，來源鍵: {key}")
                                    break
                else:
                    print(f"  ✅ 成功從嵌套metadata.answer獲取答案")
                
                # 計算真實的相似度分數
                doc_vector = embedding_model.embed_query(question)
                
                # 計算餘弦相似度
                import numpy as np
                
                def cosine_similarity(vec1, vec2):
                    """計算兩個向量的餘弦相似度"""
                    vec1 = np.array(vec1)
                    vec2 = np.array(vec2)
                    
                    # 計算點積
                    dot_product = np.dot(vec1, vec2)
                    
                    # 計算向量的模長
                    norm_vec1 = np.linalg.norm(vec1)
                    norm_vec2 = np.linalg.norm(vec2)
                    
                    # 避免除零錯誤
                    if norm_vec1 == 0 or norm_vec2 == 0:
                        return 0.0
                    
                    # 計算餘弦相似度
                    similarity = dot_product / (norm_vec1 * norm_vec2)
                    return float(similarity)
                
                real_similarity_score = cosine_similarity(query_vector, doc_vector)
                
                print(f"📄 結果 {i+1}:")
                print(f"  問題：{question}")
                print(f"  答案：{answer[:100]}..." if len(answer) > 100 else f"  答案：{answer}")
                print(f"  真實相似度分數：{real_similarity_score:.6f}")
                print(f"  是否超過閾值({relevance_threshold})：{real_similarity_score >= relevance_threshold}")
                
                # 只收集超過閾值的結果
                if real_similarity_score >= relevance_threshold:
                    results.append({
                        "question": question,
                        "answer": answer,
                        "score": real_similarity_score,
                        "real_score": True
                    })
                
            except Exception as e:
                print(f"❌ 計算第{i+1}個文檔相似度時發生錯誤: {e}")
                # 如果計算真實分數失敗，使用模擬分數作為後備
                simulated_score = 0.95 - (i * 0.05)
                print(f"  使用模擬分數：{simulated_score:.6f}")
                if simulated_score >= relevance_threshold:
                    results.append({
                        "question": question,
                        "answer": answer,
                        "score": simulated_score,
                        "real_score": False,
                        "fallback": True
                    })
                continue
        
        # 按分數排序並限制為最多2個結果
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:FAQ_CONFIG["MAX_RESULTS"]]
        
        # 檢查是否有足夠相關的結果
        max_score = results[0]["score"] if results else 0
        should_use = len(results) > 0
        
        if FAQ_CONFIG["LOG_SCORES"]:
            print(f"📊 FAQ檢索統計:")
            print(f"  最高分數: {max_score:.6f}")
            print(f"  閾值: {relevance_threshold}")
            print(f"  是否使用: {should_use}")
            print(f"  通過閾值的結果數量: {len(results)}")
        
        if should_use:
            print("✅ FAQ相關性足夠，將提供給LLM")
            for i, result in enumerate(results, 1):
                print(f"📋 結果{i} (分數: {result['score']:.6f}): {result['question']}")
        else:
            print("❌ FAQ相關性不足，不會提供給LLM")
        
        return {
            "results": results,
            "max_score": max_score,
            "should_use": should_use,
            "threshold": relevance_threshold,
            "query": query,
            "note": "使用真實餘弦相似度分數過濾"
        }
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ FAQ檢索錯誤：{error_str}")
        print(f"❌ 錯誤類型：{type(e).__name__}")
        print(f"❌ 詳細錯誤：{repr(e)}")
        
        # 檢查是否是向量索引問題
        if "Missing vector index configuration" in error_str or "index" in error_str.lower():
            print("⚠️ 可能是向量索引問題")
        
        # 檢查是否是連接問題  
        if "connection" in error_str.lower() or "timeout" in error_str.lower():
            print("⚠️ 可能是資料庫連接問題")
            
        # 檢查是否是embedding問題
        if "embedding" in error_str.lower() or "model" in error_str.lower():
            print("⚠️ 可能是embedding模型問題")
        
        # 降級處理：使用關鍵字搜尋
        if "Missing vector index configuration" in error_str:
            print("⚠️ 向量索引尚未建立，使用降級模式（關鍵字搜尋）")
            
            try:
                from google.cloud import firestore
                client = firestore.Client()
                faq_ref = client.collection("InfoHub")
                faq_docs = faq_ref.stream()
                
                results = []
                query_lower = query.lower()
                
                for doc in faq_docs:
                    data = doc.to_dict()
                    question = data.get('question', '')
                    answer = data.get('answer', '')
                    
                    # 簡單關鍵字匹配計分
                    score = 0.0
                    if question:
                        # 完全匹配
                        if query_lower == question.lower():
                            score = 0.95
                        # 包含查詢字串
                        elif query_lower in question.lower():
                            score = 0.85
                        # 關鍵字匹配
                        elif any(word in question.lower() for word in query_lower.split() if len(word) > 1):
                            score = 0.75
                    
                    # 只收集超過閾值的結果
                    if score >= relevance_threshold:
                        results.append({
                            "question": question,
                            "answer": answer,
                            "score": score,
                            "fallback": True
                        })
                
                # 按分數排序並限制結果數量
                results = sorted(results, key=lambda x: x["score"], reverse=True)[:FAQ_CONFIG["MAX_RESULTS"]]
                max_score = results[0]["score"] if results else 0
                should_use = len(results) > 0
                
                print(f"📊 降級搜尋完成，找到 {len(results)} 個超過閾值的結果")
                
                return {
                    "results": results,
                    "max_score": max_score,
                    "should_use": should_use,
                    "threshold": relevance_threshold,
                    "query": query,
                    "note": "使用關鍵字搜尋（向量索引未建立，嚴格閾值過濾）",
                    "fallback_mode": True
                }
                
            except Exception as fallback_error:
                print(f"❌ 降級搜尋也失敗：{str(fallback_error)}")
        
        return {
            "results": [],
            "max_score": 0,
            "should_use": False,
            "threshold": relevance_threshold,
            "query": query,
            "error": error_str,
            "vector_index_missing": "Missing vector index configuration" in error_str
        }

def faq(query: str) -> str:
    """
    查詢常見問題與解答 - 使用相似度檢索，返回最多2筆相關結果，嚴格按閾值過濾
    """
    print("📥 接收到的 faq query:", query)
    
    # 使用相似度檢索
    search_result = faq_universal_search(query, relevance_threshold=FAQ_CONFIG["RELEVANCE_THRESHOLD"])
    
    if not search_result["should_use"] or len(search_result["results"]) == 0:
        # 相關性不足，返回提示訊息
        print(f"📊 FAQ相關性不足 (最高分數: {search_result['max_score']:.6f}, 閾值: {search_result['threshold']})")
        return "目前FAQ資料庫中沒有找到高度相關的問題解答。"
    
    # 相關性足夠，格式化結果
    print(f"✅ FAQ相關性足夠 (最高分數: {search_result['max_score']:.6f})")
    
    formatted_results = []
    for i, result in enumerate(search_result["results"], 1):
        # 所有返回的結果都已經通過閾值篩選
        if FAQ_CONFIG["LOG_SCORES"]:
            formatted_result = f"Q{i}: {result['question']}\nA{i}: {result['answer']}\n(相關性: {result['score']:.6f})"
        else:
            formatted_result = f"Q{i}: {result['question']}\nA{i}: {result['answer']}"
        formatted_results.append(formatted_result)
    
    if not formatted_results:
        return "目前FAQ資料庫中沒有找到高度相關的問題解答。"
    
    return "\n\n".join(formatted_results)

# **🔹 載入向量資料庫 - FAQ使用相似度支援的格式**
async def load_vector_database():
    file_path = "/home/a411401516/gradAIde_shared/local/PDF/畢業門檻"
    pages = []
    client = firestore.Client()
    embedding = OllamaEmbeddings(model="bge-m3:latest")

    # 🔹 初始化文檔切割器 - 針對你的需求優化
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=SPLITTER_CONFIG["chunk_size"],
        chunk_overlap=SPLITTER_CONFIG["chunk_overlap"],
        separators=SPLITTER_CONFIG["separators"],
        length_function=SPLITTER_CONFIG["length_function"],
        is_separator_regex=SPLITTER_CONFIG["is_separator_regex"],
        keep_separator=SPLITTER_CONFIG["keep_separator"]
    )

    # 讀取 PDF - 修課規範（使用句號分割方式）
    for file in os.listdir(file_path):
        if file.endswith('.pdf'):
            pdf_path = os.path.join(file_path, file)
            # print(f"📖 正在處理: {file}")
            
            loader = PyPDFLoader(pdf_path)
            pdf_docs = loader.load()
            
            # print(f"   📄 原始文檔數量: {len(pdf_docs)}")
            
            # 清洗每頁 PDF 文件的內容
            cleaned_docs = []
            for doc in pdf_docs:
                content = doc.page_content
                cleaned_text = clean_chinese_spacing(content)
                cleaned_docs.append(Document(page_content=cleaned_text, metadata=doc.metadata))

            # 🔹 使用 text_splitter 處理已清洗過的文本
            split_docs = text_splitter.split_documents(cleaned_docs)
            
            # print(f"   ✂️ 切割後文檔數量: {len(split_docs)}")
            
            pages.extend(split_docs)

    print(f"✅ PDF 處理完成，總共生成 {len(pages)} 個文檔塊")

    # 建立規則向量資料庫
    rules_store = FirestoreVectorStore.from_documents(
        documents=pages,
        embedding=embedding,
        collection="rules_vector",
        client=client
    )

    print(f"✅ 已載入 PDF 修課規範，文檔塊數量: {len(pages)}")

    # 載入 Firestore Teacher 資料
    teacher_docs = []
    teacher_page = []
    teacher_ref = client.collection("Teacher")
    teacher_stream = teacher_ref.stream()

    for doc in teacher_stream:
        data = doc.to_dict()
        lines = [f"{k}: {v}" for k, v in data.items()]
        content = "\n".join(lines)
        teacher_docs.append(Document(
            page_content=content,
            metadata={"source": "Teacher", "id": doc.id}
        ))

    teacher_page.extend(teacher_docs)

    teachers_store = FirestoreVectorStore.from_documents(
        documents=teacher_page,
        embedding=embedding,
        collection="teachers_vector",
        client=client
    )
    print(f"✅ 已載入 Firestore 教師數量: {len(teacher_page)}")

    # 🔹 載入FAQ資料 - 支援相似度檢索的格式
    faq_docs = []
    faq_page = []
    faq_ref = client.collection("InfoHub")  # 你的FAQ集合名稱
    faq_stream = faq_ref.stream()

    for doc in faq_stream:
        data = doc.to_dict()
        question = data.get('question', '')
        answer = data.get('answer', '')
        
        if question:  # 確保問題不為空
            # 建立支援相似度檢索的Document格式
            # 使用問題作為page_content，便於相似度比對
            faq_docs.append(Document(
                page_content=question,  # 使用問題文本進行相似度比對
                metadata={
                    "question": question,
                    "answer": answer
                }
            ))

    faq_page.extend(faq_docs)

    # 建立FAQ向量資料庫 - 支援相似度檢索
    faq_store = FirestoreVectorStore.from_documents(
        documents=faq_page,
        embedding=embedding,
        collection="faq_vector",
        client=client
    )
    print(f"✅ 已載入 FAQ 數量: {len(faq_page)}")
    print(f"✅ FAQ 支援相似度檢索格式")

    # 建立 retriever 工具（不包含FAQ工具，因為會自動調用）
    rules_tool = create_retriever_tool(
        rules_store.as_retriever(search_kwargs={"k": 10}),
        name="rules",
        description="查詢修課與畢業規定"
    )

    teachers_tool = create_retriever_tool(
        teachers_store.as_retriever(search_kwargs={"k": 10}),
        name="teachers",
        description="查詢教師資訊"
    )

    # FAQ不需要建立tool，因為會在每次對話中自動檢索
    tools = [rules_tool, teachers_tool]

    return {
        "vectordb": {
            "rules": rules_store,
            "teachers": teachers_store,
            "faq": faq_store  # 支援相似度檢索的版本
        },
        "tools": tools
    }

def clean_chinese_spacing(text: str) -> str:
    # 移除中文字之間的空格（只保留英數之間的正常空格）
    return re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)

# **初始化向量資料庫**
vectordb = None
async def init_vectordb():
    global vectordb
    global retriever_tools
    global global_embedding
    loaded = await load_vector_database()
    vectordb = loaded["vectordb"]
    retriever_tools = loaded["tools"]
    
    # 初始化全域embedding模型
    global_embedding = OllamaEmbeddings(model="bge-m3:latest")

# 🔧 查詢工具函式定義
def teachers(query: str) -> str:
    """查詢教師資訊"""
    print("📥 接收到的 teachers query:", query)
    
    # 使用 similarity_search 獲取相似文檔
    docs_sim = vectordb["teachers"].similarity_search(query, k=1)
    
    # 提取文檔內容
    results = "\n\n".join([doc.page_content for doc in docs_sim])
    
    return results

def rules(query: str) -> str:
    """查詢修課與畢業規定"""
    print("📥 接收到的 rules query:", query)
    docs_sim = vectordb["rules"].similarity_search(query, k=1)

    results = "\n\n".join([doc.page_content for doc in docs_sim])
    return results

# 🔹 新增：清理推薦問題中的格式化符號
def clean_recommended_questions(content: str) -> str:
    """
    清理推薦問題中的格式化符號
    """
    if not content:
        return content
    
    # 移除各種markdown格式符號
    cleaned = content
    cleaned = cleaned.replace('**', '')  # 移除粗體標記
    cleaned = cleaned.replace('__', '')  # 移除底線粗體
    cleaned = cleaned.replace('~~', '')  # 移除刪除線
    cleaned = cleaned.replace('***', '') # 移除粗體斜體
    cleaned = cleaned.replace('*', '')   # 移除剩餘的星號
    cleaned = cleaned.replace('###', '') # 移除標題符號
    cleaned = cleaned.replace('##', '')  # 移除標題符號
    cleaned = cleaned.replace('#', '')   # 移除標題符號
    
    # 移除其他可能的格式化符號
    import re
    cleaned = re.sub(r'\[.*?\]', '', cleaned)  # 移除方括號內容
    # 注意：這裡不移除所有圓括號，因為可能包含重要資訊
    
    return cleaned.strip()

# 🧠 AutoGen 多代理對話整合 - 精簡版 + FAQ 相似度檢索 + 增強調試
def start_multi_agent_chat(user_input: str):
    from autogen import UserProxyAgent, ConversableAgent, GroupChat, GroupChatManager

    if user_input.strip() in ["你好", "嗨", "哈囉", "您好", "Hello", "hello"]:
        return "您好，我是智慧大學AI助理，有什麼需要我幫忙的嗎？"

    # 🔍 每次對話開始前，先執行FAQ相似度檢索
    faq_search_result = faq_universal_search(user_input, relevance_threshold=FAQ_CONFIG["RELEVANCE_THRESHOLD"])
    
    # 🔥 UserProxyAgent - 自動模式
    user = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        code_execution_config=False,
        max_consecutive_auto_reply=0,
        is_termination_msg=lambda x: False,
    )

    # ✅ 精簡 Question Inspector
    inspector = ConversableAgent(
        name="QuestionInspector",
        llm_config={
            "model": "qwen3:latest",
            "temperature": 0.3,
            "base_url": "http://localhost:11434",
            "api_type": "ollama",
        },
        system_message="""你是問題檢查員。請用繁體中文簡單判斷。

判斷規則（只看問題表面）：
- 問課程、教師、規定、學分 → 回答：需要檢索
- 一般聊天、問候 → 回答：不需要檢索

**重要**：
- 不要分析用戶動機或深層需求
- 不要推測用戶想要什麼
- 只看問題字面意思
- 圖片相關問題通常涉及課程 → 需要檢索

只回答上述其中一句，請使用繁體中文。""",
        human_input_mode="NEVER",
    )

    # ✅ 更新 Retriever Agent - 包含FAQ相似度檢索邏輯
    retriever = ConversableAgent(
        name="RetrieverAgent",
        llm_config={
            "model": "qwen3:latest",
            "temperature": 0.1,
            "base_url": "http://localhost:11434",
            "api_type": "ollama",
        },
        max_consecutive_auto_reply=2,
        system_message=f"""你是資料檢索代理。請用繁體中文執行檢索任務。

**執行邏輯：**
1. 查看 QuestionInspector 的判斷結果
2. 如果是「不需要檢索」→ 回應「檢索完成」（FAQ結果會自動提供）
3. 如果是「需要檢索」→ 根據問題選擇適當的額外工具執行檢索

**額外工具選擇指南：**

【基本資料查詢】
- teachers：查詢教師聯絡資訊（輸入教師姓名）
- rules：查詢畢業與修課規定（輸入關鍵字）

- rules：查詢畢業與修課規定（可查詢：畢業學分、英文門檻、程式機測、擋修規定等）

【課程資訊查詢】
- course_search：依系所、星期、時段查詢課程（輸入如「資管系 禮拜四 下午課」）
- course_name_search：依課程名稱查詢相關資料（輸入課程名稱關鍵字）
- teacher_course_search：查詢特定教師開設的課程（輸入教師姓名，如「謝錦偉」、「陳建良」）

【課程評價查詢】
- smart_course_review_recommend：智能推薦課程評價（自然語言，如「推薦輕鬆的體育課」）
- course_review_search：特定課程評價搜尋（輸入課程名稱，如「網球」、「程式設計」）
- teacher_review_search：特定教師評價搜尋（輸入教師姓名，如「謝錦偉」）

**快速決策原則：**
- 問「畢業學分數」→ 用 rules("畢業學分")
- 問「英檢」→ 用 rules("英文檢定")
- 問「機測」→ 用 rules("程式語言機測")
- 問「擋修規定」→ 用 rules("擋修規定")
- 問教師相關 → 用 teachers("教師姓名")
- 問課程相關 → 用對應的course工具

**重要提醒：**
- 相關結果會自動提供給回答代理
- 你只需要選擇其他必要的檢索工具，不須自行回應
- 一次回應只使用一個檢索資料
- **特別注意：根據向量資料庫的分拆結構，使用精確的標題關鍵詞檢索**

""",
        human_input_mode="NEVER",
    )

    # ✅ Primary Answer Agent - 重點：繁體中文 + 自然回答 + 多FAQ整合 + 增強調試
    faq_context = ""
    if faq_search_result["should_use"]:
        # ✅ 處理最多2個結果
        results = faq_search_result["results"]
        if len(results) > 0:
            faq_context_parts = []
            for i, result in enumerate(results, 1):
                # 已經過閾值篩選，不需要再次檢查
                faq_context_parts.append(f"Q{i}: {result['question']}\nA{i}: {result['answer']}")
            
            if faq_context_parts:
                faq_context = f"\n\n【FAQ資料庫相關內容】\n" + "\n\n".join(faq_context_parts)

    # ✅ 添加調試輸出
    print("🔍 FAQ上下文調試：")
    print(f"📊 should_use: {faq_search_result['should_use']}")
    print(f"📊 結果數量: {len(faq_search_result.get('results', []))}")
    print(f"📊 最高分數: {faq_search_result.get('max_score', 0):.6f}")
    print(f"📊 閾值: {faq_search_result.get('threshold', 0.8):.1f}")
    print(f"📋 faq_context 內容：")
    print(faq_context if faq_context else "（無相關FAQ內容）")
    print("="*80)
    
    primary = ConversableAgent(
        name="PrimaryAnswerAgent",
        llm_config={
            "model": "qwen3:latest",
            "temperature": 0.7,
            "base_url": "http://localhost:11434",
            "api_type": "ollama",
        },
        system_message=f"""你是智慧大學資管系AI助理。

**可用的FAQ資料庫內容：**{faq_context}

回答指南：
1. 使用繁體中文直接回答問題，語氣親切自然
2. 如果有提供FAQ資料庫內容，可以參考並自然整合進回答中
3. 如果沒有FAQ內容或相關性不足，根據常識和其他檢索資料回答
4. 課程時段說明：D1-D2是上午第一二節，D3-D4是上午第三四節，D5-D6是下午第五六節，等（不給具體時間）
5. 通識課程說明：智慧大學必修跨領域課程，分人文藝術、自然科技、社會科學三領域
6. 課程評價說明：包含學生推薦度、作業量、考試難度、收穫程度等真實評價
7. 機測說明：資管系重要的程式語言測驗項目，是電腦上機實作考試，通常考驗程式設計能力
8. 避免機器人式用語，像朋友在回答
9. 使用者只看得到你的回覆，所以請忽略不相關的資訊

使用者問題：{user_input}

記住：務必使用繁體中文，禁用簡體字！""",
        human_input_mode="NEVER",
    )

    # ✅ Question Recommender - 重點：繁體中文 + 相關性推薦
    recommender = ConversableAgent(
        name="QuestionRecommender",
        llm_config={
            "model": "qwen3:latest",
            "temperature": 0.8,
            "base_url": "http://localhost:11434",
            "api_type": "ollama",
        },
        system_message="""你負責分析前面的回答內容，判斷查詢的完整性，並推薦能夠延續話題的下一個問題。

**分析邏輯：**

1. **話題完整性判斷：**
   - 如果回答包含課程評價但缺少開課資訊 → 推薦查詢開課狀況
   - 如果回答包含開課資訊但缺少學生評價 → 推薦查詢課程評價
   - 如果回答包含課程名稱但缺少教師資訊 → 推薦查詢授課教師
   - 如果回答包含教師姓名但缺少其他課程 → 推薦查詢該教師的其他課程
   - 如果回答關於修課規定但缺少具體課程 → 推薦查詢相關課程

2. **延續性推薦：**
   - 提取回答中的關鍵資訊（課程名稱、教師姓名、系所、時段等）
   - 基於這些資訊生成具體的後續問題
   - 問題必須能夠填補資訊缺口或深化理解

3. **推薦原則：**
   - 優先推薦能完成當前話題的問題
   - 其次推薦相關延伸問題
   - 問題必須具體明確，包含具體的課程名稱或教師姓名
   - 避免重複已經回答的內容

**問題類型範例：**

**補完型問題（優先）：**
- 「[具體課程名稱]在這學期是否有開課？」
- 「[教師姓名]老師還有開設哪些課程？」
- 「[課程名稱]的學生評價如何？」
- 「[教師姓名]老師的教學評價怎麼樣？」

**延伸型問題（次要）：**
- 「還有其他[領域/類型]的推薦課程嗎？」
- 「[時段/星期]還有什麼課程可以選？」
- 「[系所]還有哪些必修課程？」

**推薦格式：**

推薦問題：

1. [基於回答內容的具體問題]？

2. [補完資訊缺口的問題]？

3. [相關延伸問題]？

**重要提醒：**
- 問題中必須包含具體的課程名稱、教師姓名或明確條件
- 禁止使用格式化符號（**、#、[]等）
- 使用繁體中文
- 避免推薦與生活、社團、行政流程無關的問題

**禁止行為：**
- 禁止解說任何課程內容
- 禁止重複 PrimaryAnswerAgent 已回答的資訊
- 禁止給予學習建議或選課建議
- 禁止使用 **粗體**、# 標題等格式化符號
- 禁止回答問題，只能推薦問題

記住：你的唯一職責是推薦 3 個後續問題，其他什麼都不做！""",
        human_input_mode="NEVER",
        is_termination_msg=lambda x: "推薦完成" in x.get("content", ""),
    )

    # 🔹 註冊工具函數 - 使用同步包裝器版本
    register_function(f=teachers, caller=retriever, executor=retriever, name="teachers", description="查詢教師資訊")
    register_function(f=rules, caller=retriever, executor=retriever, name="rules", description="查詢修業規定")
    register_function(f=course_search, caller=retriever, executor=retriever, name="course_search", description="查詢開課資訊")
    register_function(f=course_name_search, caller=retriever, executor=retriever, name="course_name_search", description="根據課程名稱查詢")
    
    # 🔹 新增：註冊教師課程搜尋工具
    register_function(f=teacher_course_search, caller=retriever, executor=retriever, name="teacher_course_search", description="查詢教師開設的課程")
    
    # 🔹 註冊課程評價工具 - 使用同步包裝器版本
    register_function(f=smart_course_review_recommend, caller=retriever, executor=retriever, name="smart_course_review_recommend", description="智能推薦課程評價")
    register_function(f=course_review_search, caller=retriever, executor=retriever, name="course_review_search", description="課程名稱評價搜尋")
    register_function(f=teacher_review_search, caller=retriever, executor=retriever, name="teacher_review_search", description="教師姓名評價搜尋")

    # 🔥 固定順序執行
    group_chat = GroupChat(
        agents=[user, inspector, retriever, primary, recommender],
        messages=[],
        max_round=6,
        speaker_selection_method="round_robin",
        allow_repeat_speaker=False,
        enable_clear_history=True,
    )

    # ✅ GroupChat Manager - 重點：流程控制
    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config={
            "model": "qwen3:latest",
            "temperature": 0.2,
            "base_url": "http://localhost:11434",
            "api_type": "ollama",
        },
        system_message="""群組對話管理員，確保流程順暢。

執行順序：User → Inspector → Retriever → Primary → Recommender

管理重點：
- FAQ資料庫已自動使用相似度檢索完成，最多返回2筆結果
- Inspector 準確分類問題
- Retriever 精確執行額外查詢（包含教師課程搜尋和課程評價工具）
- Primary 整合FAQ和其他檢索結果，用繁體中文自然回答
- Recommender 用繁體中文推薦問題"""
    )

    # 執行對話
    result = user.initiate_chat(
        recipient=manager, 
        message=user_input,
        interactive=False,
        clear_history=True
    )

    # 處理回應結果
    cc = OpenCC('s2tw')
    primary_content = ""
    recommended_content = ""
    
    for message in result.chat_history:
        message['content'] = cc.convert(message['content'])
        name = message.get("name", "")
        content = message.get("content", "").strip()
        
        # 過濾思考內容
        if not content:
            continue
        content = filter_thinking_content(content)
        
        def is_status_message(text: str) -> bool:
            """判斷是否為狀態訊息"""
            if not text:
                return True
            
            # 短訊息且只包含狀態關鍵字的才算狀態訊息
            if len(text.strip()) < 20:
                status_keywords = [
                    "需要檢索", "不需要檢索", "檢索完成", "不需查詢",
                    "主要回答完成", "推薦完成", "對話結束",
                    "執行完成", "處理完成"
                ]
                return any(keyword in text for keyword in status_keywords)
            
            return False
        
        # 跳過狀態訊息
        if is_status_message(content):
            continue
            
        if name == "PrimaryAnswerAgent" and content:
            lines = content.split('\n')
            useful_lines = [line for line in lines if line.strip() and 
                          not any(marker in line for marker in ["主要回答完成", "回答完成", "完成"])]
            if useful_lines:
                primary_content = '\n'.join(useful_lines)
                
        elif name == "QuestionRecommender" and content:
            if "推薦問題：" in content:
                lines = content.split('\n')
                useful_lines = [line for line in lines if line.strip() and 
                              not any(marker in line for marker in ["推薦完成", "對話結束", "完成"])]
                if useful_lines:
                    cleaned_lines = [clean_recommended_questions(line) for line in useful_lines]
                    recommended_content = '\n'.join(cleaned_lines)

    # 組合最終回答
    final_response_parts = []
    
    if primary_content:
        final_response_parts.append(primary_content)
    
    if final_response_parts:
        base_reply = "\n\n".join(final_response_parts)
    else:
        base_reply = "目前無法取得回答內容。"

    # 添加推薦問題
    if recommended_content:
        base_reply += f"\n\n{recommended_content}"
    
    # 最終過濾
    base_reply = filter_thinking_content(base_reply)
    converted = cc.convert(base_reply)
    
    return converted


def interpret_image(base64_image: str, question: str = "這張圖在說什麼？") -> str:
    """
    用 GPT-4 Vision 解讀課程評價診斷圖片，僅返回客觀分析資訊
    """
    print("🖼️ 使用 GPT-4 Vision 處理圖片中...")

    vision_model = ChatOpenAI(
        model="gpt-4.1-2025-04-14",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://api.openai.com/v1",
        temperature=0.1,
        max_tokens=1000,
    )

    # 🔹 精簡的客觀分析提示詞
    objective_prompt = """
分析這張智慧大學資訊管理學系的課程評價診斷圖片。

請客觀描述：
1. 圖片中顯示的通識教育領域狀態
2. 哪些領域標示為「未完成」(通常是驚嘆號!或紅色標記)
3. 哪些領域標示為「已完成」(通常是綠色勾選✓)
4. 如果有學分數字，請說明

通識領域包括：
- 人文與藝術領域
- 自然與科技領域  
- 社會科學領域

請只回傳客觀的分析結果，不需要建議或問候語。
使用繁體中文回答。
"""

    # 圖片格式設定
    image_payload = {
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}",
            "detail": "high"
        },
    }

    messages = [
        HumanMessage(
            content=[
                {"type": "text", "text": objective_prompt},
                image_payload
            ]
        )
    ]

    try:
        response = vision_model.invoke(messages)
        print("📩 圖片分析結果：", response.content)
        return response.content
    except Exception as e:
        print("❌ 圖片解析錯誤：", e)
        return f"圖片無法解析。錯誤：{str(e)}"

def smart_multi_agent_chat(user_input):
    """
    智慧多代理對話主函數，支援圖片和純文字
    """
    if isinstance(user_input, dict) and "image" in user_input:
        print("🖼 偵測到圖片，使用 OpenAI Vision 模式")

        # 自動補文字敘述（若缺）
        user_text = user_input.get("text", "").strip()
        if not user_text:
            user_text = "請分析這張課程評價診斷圖片"

        # 圖片描述處理
        image_text = interpret_image(user_input["image"], user_text)

        # 🔥 精簡圖片處理prompt
        combined_prompt = f"""
圖片分析：{image_text}

使用者問題：{user_text}

請根據圖片內容用繁體中文回答問題，如涉及缺少的通識領域，請查詢相關課程。
"""
        return start_multi_agent_chat(combined_prompt)
    else:
        print("📝 純文字對話")
        return start_multi_agent_chat(user_input)

def filter_thinking_content(text: str) -> str:
    """
    過濾掉 qwen3 模型的思考內容和不必要的輸出
    """
    import re
    
    # 1. 移除 <think> 標籤及其內容
    pattern = r'<think>.*?</think>'
    filtered_text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. 移除其他常見的狀態訊息
    status_patterns = [
        r'檢索完成.*',
        r'主要回答完成.*',
        r'輔助回答完成.*',
        r'推薦完成.*',
        r'對話結束.*',
        r'請回答者處理.*',
        r'直接回答即可.*'
    ]
    
    for pattern in status_patterns:
        filtered_text = re.sub(pattern, '', filtered_text, flags=re.IGNORECASE)
    
    # 3. 移除markdown格式化符號
    filtered_text = filtered_text.replace('**', '')  # 移除粗體標記
    filtered_text = filtered_text.replace('__', '')  # 移除底線粗體
    filtered_text = filtered_text.replace('~~', '')  # 移除刪除線
    filtered_text = filtered_text.replace('***', '') # 移除粗體斜體
    filtered_text = filtered_text.replace('#', '')
    # 小心處理星號，避免移除列表項目
    filtered_text = re.sub(r'\*(?!\s)', '', filtered_text)  # 移除非列表的星號
    
    # 4. 清理多餘的空行和空格
    lines = filtered_text.split('\n')
    cleaned_lines = []
    
    prev_empty = False
    for line in lines:
        stripped_line = line.strip()
        
        if stripped_line:  # 非空行
            cleaned_lines.append(line.rstrip())  # 保留原始縮排，移除尾部空格
            prev_empty = False
        elif not prev_empty:  # 避免連續空行
            cleaned_lines.append('')
            prev_empty = True
    
    # 移除開頭和結尾的空行
    result = '\n'.join(cleaned_lines).strip()
    
    return result