from openai import OpenAI
from dotenv import main
import base64
import os

main.load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def encode_image(image_path):
    """將圖片轉換為 Base64 編碼"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_course_image(image_path):
    """
    解析課程系統截圖，回傳學分缺少資訊
    :param image_path: 圖片檔案路徑
    :return: GPT-4o 回應的內容
    """
    
    base64_image = encode_image(image_path)

    prompt = """
        你是專精於圖片分析的 AI 助理，負責解析智慧大學資管系的課程系統截圖，並從中萃取與課程相關的重要資訊。

    ### 【你的任務】：
    1 **辨識尚未達標的課程**
       - 請你辨識人文、自然、社會領域課程
       - 課程前面標有 `!` 符號，代表該課程所屬領域的學分尚未達標。
       - 例如：「！全人 人文與藝術通識領域 4」代表該領域學分未達標，總共需要修 4 學分。
       - 如果前面沒有！而是綠色打勾，代表這門通識領域已獲得通過畢業門檻的學分。

    2 **分類課程至對應領域**
       - 「人文與藝術通識領域」
       - 「自然與科技通識領域」
       - 「社會科學通識領域」

    3 **計算缺少的學分**
       - 從標頭為 `!` 的課程資訊中，提取領域名稱與缺少的學分數。
       - 將不同領域的學分統整，例如：
         ```
          **學分統計**
         - 人文與藝術通識領域：尚缺 0 學分
         - 自然與科技通識領域：尚缺 2 學分
         - 社會科學通識領域：尚缺 4 學分，正在修「理財學」
         ```
         如果在領域名稱下面有：ccc
         「31533-00 / 111-1 科學與社會：歷史脈絡-英 75」這種格式，
         75代表學期成績75分，如果是「未評定成績」，
        「36094-00 / 113-2 理財學 未評定成績」
         代表正在修這門課程，尚缺總學分可以減去這2學分，
         並標注尚缺 4 學分，正在修「理財學」。
         如果領域名稱下面沒有這行，代表還缺少這學分。

    4 **回傳格式**
       - 如果圖片中沒有 `!` 符號的課程，請回應：「所有通識領域學分均已達標。」

    ### ** 注意事項**
    - 請將所有三個領域的尚缺學分都列出來
    - 請**忠實回應圖片資訊，不要自行推測或添加內容**。

    請開始解析這張圖片並回傳結果，使用繁體中文。
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ],
            }
        ],
    )

    return response.choices[0].message.content

# # 測試函數（可以註解掉，如果你要在其他地方引入此函數）
# if __name__ == "__main__":
#     image_path = "圖片/大郭.jpg"
#     result = analyze_course_image(image_path)
#     print(result)
