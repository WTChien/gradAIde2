# 匯入必要的標準函式庫
import argparse  # 用於解析命令列參數
import asyncio   # 提供非同步 I/O 支援
import os        # 提供與作業系統互動的功能，如路徑操作
import sys       # 提供與 Python 解譯器互動的功能，如修改模組搜尋路徑


# 匯入第三方套件
from langchain_ollama import ChatOllama  # 使用 Ollama 提供的 ChatOllama 類別，作為大型語言模型（LLM）

# 將專案的上層目錄加入模組搜尋路徑，確保可以匯入本地模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 匯入 dotenv 套件，用於載入 .env 檔案中的環境變數
from dotenv import load_dotenv

# 從本地模組 browser_use 中匯入所需的類別
from browser_use import Agent  # 代理類別，用於執行自動化任務
from browser_use.browser.browser import Browser, BrowserConfig  # 瀏覽器類別及其設定
from browser_use.controller.service import Controller  # 控制器類別，用於管理代理的行為

# 載入 .env 檔案中的環境變數，若已有同名變數則覆蓋
load_dotenv(override=True)


def parse_arguments():
    """
    解析命令列參數，允許使用者指定查詢內容。
    若未提供，則使用預設查詢。
    """
    parser = argparse.ArgumentParser(description='使用 LLM 代理程式自動執行瀏覽器任務。')
    parser.add_argument(
        '--query',  # 參數名稱
        type=str,  # 資料型別為字串
        help='要處理的查詢',  # 參數說明
        default='go to reddit and search for posts about browser-use'  # 預設查詢內容
    )
    return parser.parse_args()  # 回傳解析後的參數物件

def initialize_agent(query: str):
    """
    初始化代理所需的組件，包括 LLM、控制器和瀏覽器。
    傳入查詢內容，回傳代理實例與瀏覽器實例。
    """
    # 建立 LLM 實例，使用指定的模型與上下文長度
    llm = ChatOllama(model="qwen3:32b", num_ctx=32000, base_url="http://localhost:11435")

    # 建立控制器實例，用於管理代理的行為
    controller = Controller()

    # 建立瀏覽器實例，使用預設的瀏覽器設定
    browser = Browser(config=BrowserConfig())

    # 建立代理實例，設定任務內容與相關組件
    agent = Agent(
        task = f"""
## 🎯 任務目標：
根據使用者的查詢需求，到輔仁大學課程查詢網站 `http://estu.fju.edu.tw/fjucourse/Secondpage.aspx`，操作查詢表單並擷取課程資料，最多回傳前 5 筆查詢結果。

使用者查詢條件如下：
{query}

---

## 🧭 操作步驟（請嚴格依序執行）：

1. 開啟網站 `http://estu.fju.edu.tw/fjucourse/Secondpage.aspx`
2. 點選最上方的「依基本開課資料查詢」按鈕，載入查詢表單
3. 設定「開課部別」為 `D-日間部`（對應 `<select id="DDL_AvaDiv">`)

> ⚠️ **注意：** 請確認開課部別確實選擇為日間部後再進行下一步

4. 勾選「選別」欄位中的 `通識`
5. 若使用者敘述中有提到「星期幾」，請在「上課時間」欄位勾選對應的星期（如星期一）
6. 處理上課節次條件：
   - ✅ 若使用者有明確輸入節次（如 D1、D2 等），請設定：
     - 「上課節次（起）」欄位（`#DDL_Section_S`) → 設定為開始節次
     - 「上課節次（迄）」欄位（`#DDL_Section_E`) → 設定為結束節次
   - ✅ 若使用者**未指定節次**，但有出現「早上、下午、晚上」這類模糊時間詞，請套用以下預設節次範圍進行查詢：
     - 「早上」 → D3-D4
     - 「下午」 → D5-D6
     - 「晚上」 → D7-D8
     - 並照上述對應填入「起訖節次」欄位

> ⚠️ **注意：**
> - 「上課節次」欄位若設定，查詢條件必須「完全符合」起訖節次，才會有資料顯示。例如課程為 D1-D2，若你選 D1-D3，會查不到。
> - 若未提及節次且未提及時間段（如早上等），則可跳過「節次」設定。

7. 點擊下方的「查詢(Search)」按鈕
8. 等待頁面載入查詢結果，依使用者需求擷取最多 5 筆課程資訊（包含課程名稱、授課教師、時間與地點等）
9. 回傳查詢結果（若無符合條件課程，請明確說明查無資料）

---

## 📌 限制與規則：

- 僅需設定上述欄位（`開課部別`、`選別`、`上課時間`、`上課節次`)
- 其餘欄位如「課程系所」、「開課班級」、「開放條件」等，**一律忽略**
- 請使用繁體中文回答
- 不得提前結束任務，務必完成查詢後才擷取資料
- 若無符合條件之課程，僅回答「查無該條件之課程資料」

✅ 請務必完成查詢後再擷取資料。未查詢前請勿回傳資料。
---

## 📤 輸出格式要求：

- 請將查詢結果以 **JSON 陣列格式** 回傳
- 每筆課程請包含下列欄位：
  - `"course_name"`：課程名稱
  - `"instructor"`：授課教師
  - `"time"`：上課時間（含星期與節次）
  - `"location"`：上課教室

""",
        llm=llm,  # 指定使用的 LLM
        controller=controller,  # 指定使用的控制器
        browser=browser,  # 指定使用的瀏覽器
        use_vision=True,  # 是否啟用視覺功能，這裡設定為不啟用
        enable_memory= True,
    )

    return agent, browser  # 回傳代理實例與瀏覽器實例

async def main():
    """
    主程式的非同步入口點。
    解析命令列參數，初始化代理，執行任務，並在任務完成後關閉瀏覽器。
    """
    args = parse_arguments()  # 解析命令列參數
    agent, browser = initialize_agent(args.query)  # 初始化代理與瀏覽器

    history = await agent.run(max_steps=10)  # 執行代理任務
    

    # 寫入檔案
    final = history.final_result()
    with open("result.txt", "w", encoding="utf-8") as f:
        if final:
            f.write(final)
        else:
            f.write("⚠️ 沒有找到任何結果內容（可能任務失敗或中斷）。")

    # input('按 Enter 鍵關閉瀏覽器...')  # 等待使用者按下 Enter 鍵
    await browser.close()  # 關閉瀏覽器

# 程式的進入點
if __name__ == '__main__':
    asyncio.run(main())  # 執行主程式
