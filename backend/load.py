# load.py
import os
import re
import asyncio
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_core.documents import Document
from langchain_text_splitters import HTMLSectionSplitter

load_dotenv()
os.environ["USER_AGENT"] = os.getenv("USER_AGENT") or "Mozilla/5.0 (GradAIdeBot)"

def html_teacher_to_document(html_chunk: str) -> Document:
    soup = BeautifulSoup(html_chunk, "html.parser")
    h2 = soup.find("h2")
    name_title = h2.get_text(separator=" ", strip=True) if h2 else "這位老師"

    def extract_text(label: str) -> str:
        regex = re.compile(rf"{label}[:：]?\s*([^\n\r]+)")
        match = regex.search(html_chunk)
        return match.group(1).strip() if match else ""

    fields = {
        "姓名": name_title.split()[0] if name_title else "",
        "職稱": " ".join(name_title.split()[1:]) if len(name_title.split()) > 1 else "",
        "專長": extract_text("專長"),
        "實驗室": extract_text("實驗室"),
        "電話": re.search(r"(電話|TEL).*?(\(02\)\s*\d{4}-\d{4}|\(02\)\s*\d+)", html_chunk),
        "信箱": extract_text("信箱"),
        "辦公室位置": extract_text("辦公室位置")
    }

    # 特殊處理電話欄位（如果用正規式有 match 才取 group(2)）
    phone_match = re.search(r"(電話|TEL)[：:\s]*([^\s<\n]+)", html_chunk)
    fields["電話"] = phone_match.group(2) if phone_match else ""

    page_content = "\n".join([f"{k}：{v}" for k, v in fields.items()])
    metadata = {"Header 2": name_title, "source": "智慧大學網頁"}

    return Document(page_content=page_content, metadata=metadata)



# 主流程：抓 HTML → 擷取教師區塊 → 結構化
async def main():
    # 讀取 HTML
    loader = AsyncChromiumLoader(["https://www.im.fju.edu.tw/%E5%B0%88%E4%BB%BB%E6%95%99%E5%B8%AB/"])
    html_pages = []
    html_data = []
    async for html in loader.alazy_load():  # **這裡正確地遍歷 async generator**
        html_data.append(html)

    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    html_splitter = HTMLSectionSplitter(headers_to_split_on)
    html_header_splits = html_splitter.split_text(str(html))

    filtered_splits = [
        doc for doc in html_header_splits 
        if "Header 2" in doc.metadata and doc.metadata["Header 2"] != "學校地理位置"
    ]

    for doc in filtered_splits:
        if hasattr(doc, 'content'):
            del doc.metadata["content"]

        doc.page_content = re.sub(r'[\n\t\xa0"更多資訊"]+|(\\n)|(\\t)', '', doc.page_content).strip()
        doc.metadata["source"] = "智慧大學網頁"

    # print("filtered_splits:\n",filtered_splits)
    print(filtered_splits)


if __name__ == "__main__":
    asyncio.run(main())
