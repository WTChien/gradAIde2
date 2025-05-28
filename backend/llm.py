import os
import asyncio
import concurrent.futures
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_firestore import FirestoreVectorStore
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
from langchain.tools.retriever import create_retriever_tool
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen import register_function
from google.cloud.firestore_v1.base_query import FieldFilter
from langchain_core.messages import HumanMessage
import json

# 🔹 導入課程搜尋 API
from course_search import course_search_api, format_courses_for_agent

if not firebase_admin._apps:
    cred = credentials.Certificate("/home/a411401516/gradAIde_shared/local/backend/gradaide5-firebase-adminsdk-fbsvc-1f64c30917.json")
    firebase_admin.initialize_app(cred)

# 讀取環境變數
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["USER_AGENT"] = os.getenv("USER_AGENT")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["MISTRAL_API_KEY"] = os.getenv("MISTRAL_API_KEY")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/a411401516/gradAIde_shared/local/backend/gradaide5-firebase-adminsdk-fbsvc-1f64c30917.json"

PROJECT_ID = os.getenv("PROJECT_ID")

# **載入 LLM 模型**
model = OllamaLLM(model="llama3.3:latest")
agent_model = ChatOpenAI(model="gpt-3.5-turbo-1106")
ollama_model_client = OllamaChatCompletionClient(model="llama3.3:latest")

retriever_tools = []  # 全域 retriever 工具集合

# **🔹 課程搜尋工具（使用爬蟲）**
def course_search(query: str) -> str:
    """
    課程搜尋工具 - 使用自然語言查詢開課資訊
    這個工具會解析自然語言查詢，並爬取輔仁大學課程查詢系統
    
    Args:
        query (str): 自然語言查詢字串
        
    Returns:
        str: 格式化的課程查詢結果
    """
    try:
        # 使用 API 化的課程搜尋函數
        search_result = course_search_api(query)
        
        # 將結果格式化為適合 Agent 閱讀的格式
        formatted_result = format_courses_for_agent(search_result)
        
        return formatted_result
        
    except Exception as e:
        return f"❌ 課程搜尋發生錯誤：{str(e)}"
    
# **🔹 載入向量資料庫**
async def load_vector_database():
    file_path = "/home/a411401516/gradAIde_shared/local/PDF/畢業門檻"
    pages = []
    client = firestore.Client()
    embedding = OllamaEmbeddings(model="nomic-embed-text")

    # 讀取 PDF - 修課規範
    for file in os.listdir(file_path):
        if file.endswith('.pdf'):
            pdf_path = os.path.join(file_path, file)
            loader = PyPDFLoader(pdf_path)
            pdf_docs = loader.load()

            for doc in pdf_docs:
                doc.metadata["source"] = file  # 記錄原始檔案名稱
            
            pages.extend(pdf_docs)
    
    rules_store = FirestoreVectorStore.from_documents(
        documents=pages,
        embedding=embedding,
        collection="rules_vector",
        client=client
    )

    print(f"✅ 已載入 PDF 修課規範數量: {len(pages)}")

    # 載入 Firestore Teacher 資料
    teacher_docs = []
    teacher_page = []
    client = firestore.Client()
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

    # 建立 retriever 工具（只保留 rules 和 teachers）
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

    tools = [rules_tool, teachers_tool]

    return {
        "vectordb": {
            "rules": rules_store,
            "teachers": teachers_store
        },
        "tools": tools
    }

# **初始化向量資料庫**
vectordb = None
async def init_vectordb():
    global vectordb
    global retriever_tools
    loaded = await load_vector_database()
    vectordb = loaded["vectordb"]
    retriever_tools = loaded["tools"]

# 🔧 查詢工具函式定義
def teachers(query: str) -> str:
    """查詢教師資訊"""
    print("📥 接收到的 teachers query:", query)
    docs_sim = vectordb["teachers"].similarity_search(query, k=3)
    docs_mmr = vectordb["teachers"].max_marginal_relevance_search(query, 1,
                            filters=FieldFilter("metadata.id", "==", query)
                                                                )
    # 移除重複的 Document（依 page_content）
    unique_docs_mmr = list({doc.page_content: doc for doc in docs_mmr}.values())

    # 組合兩種結果
    sim_results = "\n\n".join([doc.page_content for doc in docs_sim])
    mmr_results = "\n\n".join([
        doc.page_content.encode('utf-8').decode('unicode_escape')
        for doc in unique_docs_mmr
    ])
 
    combined_results = sim_results + "\n\n" + mmr_results

    return combined_results

def rules(query: str) -> str:
    """查詢修課與畢業規定"""
    print("📥 接收到的 rules query:", query)
    docs_mmr = vectordb["rules"].max_marginal_relevance_search(query, 2)
    unique_docs = list({doc.page_content: doc for doc in docs_mmr}.values())
    results = "\n\n".join([
        doc.page_content.encode('utf-8').decode('unicode_escape')
        for doc in unique_docs
    ])

    return results

# 🧠 AutoGen 多代理對話整合
def start_multi_agent_chat(user_input: str):
    from autogen import UserProxyAgent, ConversableAgent, GroupChat, GroupChatManager

    if user_input.strip() in ["你好", "嗨", "哈囉", "您好", "Hello", "hello"]:
        return "您好，我是智慧大學AI助理，有什麼需要我幫忙的嗎？"

    # 使用者
    user = UserProxyAgent(
        name="User",
        is_termination_msg=lambda x: "Final Answer:" in x,
        human_input_mode="NEVER",
        code_execution_config={"use_docker": False},
    )

    # Step 1: Question Inspector
    inspector = ConversableAgent(
        name="QuestionInspector",
        llm_config={
            "model": "qwen3:latest",
            "temperature": 0.3,
            "base_url": "http://localhost:11434",
            "api_type": "ollama",
        },
        system_message="""
你是問題檢查員，負責判斷使用者的問題是否需要查詢資料。
如果問題牽涉到課程、修業規則、機測、英檢、畢業學分、教師，就需要透過檢索獲得資訊。

請根據內容，只回答以下兩句其中之一：
- 需要檢索
- 不需要檢索

請注意只能回答上面其中一句，不能多加說明。不要顯示思考過程。
"""
    )

    # Step 2: Retriever Agent（含工具）
    retriever = ConversableAgent(
        name="RetrieverAgent",
        llm_config={
            "model": "qwen3:latest",
            "temperature": 0.1,
            "base_url": "http://localhost:11434",
            "api_type": "ollama",
        },
        system_message = f"""
你是智慧大學的資料檢索代理，負責根據上一位代理人的指示，判斷是否需要使用工具進行查詢。

---

執行規則：

1. 若上一位代理的回答是「需要檢索」，請使用對應的工具查詢。
2. 若上一位回答是「不需要檢索」，請直接回覆：
   Observation: 不需查詢。
3. 請使用繁體中文的原始用語作為查詢內容，避免更改使用者的語意。

---

工具使用規則：

teachers 工具（查詢教師資訊）：
- 請使用 metadata.id（即教師「姓名」欄位）進行查詢。
- 錯誤範例：歐思鼎教授的信箱？
- 正確查詢關鍵字：歐思鼎
- 請勿傳整句話，僅擷取教師姓名作為查詢輸入。

---

course_search 工具（查詢開課資訊）：
- 當使用者詢問「什麼課程」、「有哪些課」、「開課資訊」、「課程時間表」、「選課」時，請使用此工具
- 支援自然語言查詢，如「星期一早上的人文通識」、「資管系的課程」、「下午有什麼課」
- 請將使用者的原始查詢傳給此工具，它會自動解析條件
- 這個工具會即時查詢最新的開課資訊

---

rules 工具（查詢修課與畢業規定）：
- 當問題與以下主題有關時，請使用「學年度 + 關鍵詞」格式查詢：
  - 機測
  - 英文檢定
  - 畢業學分
  - 學程規定
  - 修課規範

- 建議查詢格式：
  例如：108學年度 英檢
       112學年度 機測規定

---

禁止事項：
- 不要自行解釋使用者問題。
- 不要加入評論。
- 僅負責執行查詢或略過查詢。
- 不要顯示思考過程。

---

使用者問題如下：
{user_input}
"""
    )

    # 🔹 註冊工具（移除了 courses 工具，只保留必要的）
    register_function(f=teachers, caller=retriever, executor=retriever, name="teachers", description="查詢教師資訊")
    register_function(f=rules, caller=retriever, executor=retriever, name="rules", description="查詢修業規定")
    register_function(f=course_search, caller=retriever, executor=retriever, name="course_search", description="查詢開課資訊和課程時間表")

    # Step 3: Primary Answerer
    primary = ConversableAgent(
        name="PrimaryAnswerAgent",
        llm_config={
            "model": "qwen3:latest",
            "temperature": 0.7,
            "base_url": "http://localhost:11434",
            "api_type": "ollama",
        },
        system_message = """
你是智慧大學資訊管理學系的主要回答者，負責清楚、專業、條理分明地回答學生的問題。

---

請遵守以下規則：

1. 回答時請直接切入重點，條列並說明清楚，不要出現「根據 observation」、「你提到...」等敘述。
2. 避免使用「我」這個主詞，例如「我看到」、「我認為」等說法，改以第三人稱或說明式句型作答。
3. 使用者問題若涉及教師資訊，若無法查到結果，請提醒可能是姓名拼寫錯誤或不完整，建議再次確認教師姓名。
4. 回答內容必須是可信、完整、條理清楚的說明，風格如學長姊協助解惑。
5. 回答請使用繁體中文，語氣自然、禮貌、專業。
6. 若找不到答案，請簡潔說明「目前沒有明確資訊」，不要編造內容。
7. 🔹 若回答中涉及課程時間的「早上」或「下午」等描述，請對照以下節次代碼：
   - 早上：D1～D4（含08:10–12:00）
   - 下午：D5～D8（含13:10–17:00）
   - 晚上：D9～DC（含17:10之後）
8. 🔹 重要：不要顯示思考過程，直接提供最終答案。

禁止使用簡體字。
"""
    )

    # Step 4: Helper Answerer
    helper = ConversableAgent(
        name="HelperAnswerAgent",
        llm_config={
            "model": "qwen3:latest",
            "temperature": 0.6,
            "base_url": "http://localhost:11434",
            "api_type": "ollama",
        },
        system_message = """
你是智慧助理的輔助回答者，負責補充主要回答內容的延伸資訊或提醒。

---

請遵守以下規則：

1. 不要重複主要回答的內容，也不要用「根據上述回覆」、「如剛剛所說」等句子開頭。
2. 專注於補充背景知識、提供額外資訊、提醒學生注意事項，或給出實用建議。
3. 若問題與教師有關，也可提醒學生再次確認教師姓名是否正確（例如是否打錯或缺字）。
4. 回覆應簡潔清楚、自然口語，語氣親切溫和但具專業感。
5. 僅補充，不需總結或重述主要回覆。
6. 🔹 重要：不要顯示思考過程，直接提供最終答案。

請使用繁體中文，且禁止使用簡體字。
"""
    )

    # Question Recommender
    recommender = ConversableAgent(
        name="QuestionRecommender",
        llm_config={
            "model": "qwen3:latest",
            "temperature": 0.8,
            "base_url": "http://localhost:11434",
            "api_type": "ollama",
        },
        system_message="""
你是下一個可能問題推薦者，負責根據目前的對話內容預測使用者接下來可能會問的三個問題。

請嚴格按照以下格式回傳：

推薦問題：
1. 第一個問題？
2. 第二個問題？
3. 第三個問題？

注意事項：
- 每個問題都必須以「？」結尾
- 問題應該與先前對話相關但未被提問過
- 風格請自然口語，符合大學生日常提問風格
- 你是智慧大學所屬，請不要提到其他學校名稱
- 不要加上任何其他解釋文字
- 🔹 重要：不要顯示思考過程，直接提供最終答案
"""
    )

    # 建立 Group Chat
    group_chat = GroupChat(
        agents=[user, inspector, retriever, primary, helper, recommender],
        messages=[],
        max_round=7,
        speaker_selection_method="round_robin",
        enable_clear_history=True,
    )

    # 管理員
    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config={
            "model": "qwen3:latest",
            "temperature": 0.3,
            "base_url": "http://localhost:11434",
            "api_type": "ollama",
        }
    )

    result = user.initiate_chat(manager, message=user_input, interactive=False)

    # 🔹 分離主要回答和推薦問題，並過濾思考內容
    primary_content = ""
    helper_content = ""
    recommended_content = ""
    
    for i, message in enumerate(result.chat_history):
        name = message.get("name", "")
        content = message.get("content", "").strip()
        
        # 🔹 過濾思考內容
        content = filter_thinking_content(content)
        
        if name == "PrimaryAnswerAgent" and content and "Final Answer:" not in content:
            # 移除 [PRIMARY_END] 標記
            clean_content = content.replace("[PRIMARY_END]", "").strip()
            if clean_content:
                primary_content = clean_content
            
        elif name == "HelperAnswerAgent" and content and "Final Answer:" not in content:
            # 提取 [HELPER_START] 和 [HELPER_END] 之間的內容
            if "[HELPER_START]" in content and "[HELPER_END]" in content:
                start_idx = content.find("[HELPER_START]") + len("[HELPER_START]")
                end_idx = content.find("[HELPER_END]")
                helper_content = content[start_idx:end_idx].strip()
            else:
                # 如果沒有標記，直接使用整個內容
                helper_content = content.strip()
            
        elif name == "QuestionRecommender" and content:
            recommended_content = content.strip()

    # 🔹 組合最終回答
    final_response_parts = []
    
    if primary_content:
        final_response_parts.append(primary_content)
    
    if helper_content:
        final_response_parts.append(helper_content)
    
    # 最終回答
    if final_response_parts:
        base_reply = "\n\n".join(final_response_parts)
    else:
        base_reply = "目前無法取得回答內容。"
        print("❌ 沒有收集到任何有效回答")

    # 🔹 將推薦問題添加到回答末尾，供前端提取使用
    if recommended_content:
        base_reply += f"\n\n{recommended_content}"
    
    # 🔹 最終過濾：確保最終回答也沒有思考內容
    base_reply = filter_thinking_content(base_reply)
    
    return base_reply

def interpret_image(base64_image: str, question: str = "這張圖在說什麼？") -> str:
    """
    用 GPT-4 Vision 解讀 base64 圖片，回傳中文描述文字。
    """
    print("🖼️ 使用 GPT-4 Vision 處理圖片中...")

    vision_model = ChatOpenAI(
        model="gpt-4.1-2025-04-14",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://api.openai.com/v1",
        temperature=0.3,
        max_tokens=1024,
    )

    # 圖片格式設定
    image_payload = {
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}",
        },
    }

    messages = [
        HumanMessage(
            content=[
                {"type": "text", "text": question},
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
        return "圖片無法解析。請重新上傳或改用文字提問。"

def smart_multi_agent_chat(user_input):
    """
    智慧多代理對話主函數，支援圖片和純文字
    """
    if isinstance(user_input, dict) and "image" in user_input:
        print("🖼 偵測到圖片，使用 OpenAI Vision 模式")

        # 自動補文字敘述（若缺）
        user_text = user_input.get("text", "").strip()
        if not user_text:
            user_text = """
            這張圖可能是學生的修課結果，請根據圖片內容找出缺少的修課類別。
            驚嘆號的圖案代表「未完成」相關課程的含意。
            綠色打勾的圖案代表「已完成」相關課程的含意。
            請你回傳所缺少的通識領域類別名稱。
            """

        # 圖片描述處理
        image_text = interpret_image(user_input["image"], user_text)

        # 建立結構化的 prompt
        combined_prompt = f"""
            🖼️ 使用者提供了一張圖片。

            📷 圖片內容分析如下：
            {image_text}

            🧾 使用者希望詢問的內容如下：
            {user_text}

            🎯 請根據圖片與問題，協助判斷是否缺少修課類別、是否符合畢業條件，並結合可用資料工具給予回覆。
            如使用者圖片資訊包括了缺少的通識領域類別名稱，請從course_search工具檢索出該通識相關課程。
        """

        return start_multi_agent_chat(combined_prompt)

    else:
        print("📝 純文字對話，使用本地 Ollama 模式")
        return start_multi_agent_chat(user_input)

def filter_thinking_content(text: str) -> str:
    """
    過濾掉 qwen3 模型的思考內容 (<think>...</think>)
    """
    import re
    
    # 使用正則表達式移除 <think> 標籤及其內容
    # 支援多行匹配，不區分大小寫
    pattern = r'<think>.*?</think>'
    filtered_text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 清理多餘的空行
    lines = filtered_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        if stripped_line:  # 保留非空行
            cleaned_lines.append(line)
        elif cleaned_lines and cleaned_lines[-1].strip():  # 保留一個空行作為段落分隔
            cleaned_lines.append('')
    
    return '\n'.join(cleaned_lines).strip()