import asyncio
from llm import faq_universal_search, init_vectordb
from firestore import delete_collection

async def debug_metadata(query):
    """專門調試 metadata 結構的函數"""
    
    print(f"🔍 開始搜尋：'{query}'")
    
    # 確保向量資料庫已初始化
    from llm import vectordb
    
    if not vectordb or "faq" not in vectordb:
        print("❌ 向量資料庫未初始化")
        return False
    
    print("✅ FAQ向量資料庫已就緒")
    
    # 直接測試向量搜尋
    docs = vectordb["faq"].similarity_search(query, k=2)         
    docs2 = vectordb["faq"].max_marginal_relevance_search(query, 2)          

    print("\n" + "="*60)

    # 處理第一組結果 (similarity_search)
    print("=== 相似度搜尋結果 ===")
    if docs:
        print("原問題：", query)
        for i, doc in enumerate(docs, 1):
            # 檢查是否有內層 metadata
            if 'metadata' in doc.metadata:
                inner_metadata = doc.metadata['metadata']
                question = inner_metadata.get('question', 'N/A')
                answer = inner_metadata.get('answer', 'N/A')
            else:
                # 直接從 metadata 取值
                question = doc.metadata.get('question', 'N/A')
                answer = doc.metadata.get('answer', 'N/A')
            
            print(f"❓ 問題{i}: {question}")
            print(f"💡 答案{i}: {answer}")
            print("-" * 50)
    else:
        print("❌ 沒有找到相關文檔")

    # 處理第二組結果 (max_marginal_relevance_search)
    print("\n=== 最大邊際相關性搜尋結果 ===")
    if docs2:
        print("原問題：", query)
        for i, doc in enumerate(docs2, 1):
            try:
                # MMR搜尋結果的資料在 page_content 中，需要解析 JSON
                import json
                content_data = json.loads(doc.page_content)
                
                # 從解析的 JSON 中取得 metadata
                if 'metadata' in content_data:
                    question = content_data['metadata'].get('question', 'N/A')
                    answer = content_data['metadata'].get('answer', 'N/A')
                else:
                    question = content_data.get('question', 'N/A')
                    answer = content_data.get('answer', 'N/A')
                    
                print(f"❓ 問題{i}: {question}")
                print(f"💡 答案{i}: {answer}")
                print("-" * 50)
                
            except (json.JSONDecodeError, KeyError) as e:
                print(f"❌ 解析第{i}個文檔時發生錯誤: {e}")
                print(f"原始內容: {doc.page_content[:200]}...")
                print("-" * 50)
    else:
        print("❌ 沒有找到相關文檔")

    # 統計結果
    similarity_count = len(docs) if docs else 0
    mmr_count = len(docs2) if docs2 else 0
    
    print(f"\n📊 統計:")
    print(f"相似度搜尋找到 {similarity_count} 個結果")
    print(f"MMR搜尋找到 {mmr_count} 個結果")
    
    return True

async def interactive_test():
    """互動式測試函數"""
    print("🎯 進入互動測試模式")
    print("輸入 'quit' 或 'exit' 退出程式")
    print("輸入 'reinit' 重新初始化資料庫")
    print("輸入 'clear' 清除並重新初始化資料庫")
    print("-" * 60)
    
    while True:
        try:
            # 取得使用者輸入
            user_input = input("\n🔍 請輸入測試查詢: ").strip()
            
            # 檢查退出指令
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 再見！")
                break
            
            # 檢查重新初始化指令
            if user_input.lower() == 'reinit':
                print("\n🚀 重新初始化向量資料庫...")
                await init_vectordb()
                print("✅ 向量資料庫重新初始化完成！")
                continue
            
            # 檢查清除並重新初始化指令
            if user_input.lower() == 'clear':
                print("\n🧹 清除原有向量資料庫...")
                delete_collection("teachers_vector")
                delete_collection("rules_vector")
                delete_collection("faq_vector")
                print("✅ 清除完成！")
                
                print("\n🚀 重新初始化向量資料庫...")
                await init_vectordb()
                print("✅ 向量資料庫重新初始化完成！")
                continue
            
            # 檢查空輸入
            if not user_input:
                print("⚠️ 請輸入有效的查詢")
                continue
            
            # 執行搜尋測試
            success = await debug_metadata(user_input)
            
            if not success:
                print("❌ 搜尋失敗，請檢查資料庫狀態")
                print("💡 提示：可以輸入 'reinit' 重新初始化資料庫")
            
        except KeyboardInterrupt:
            print("\n\n👋 程式被中斷，再見！")
            break
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
            print("程式繼續運行...")

async def main():
    print("🎯 FAQ 向量搜尋測試工具")
    print("=" * 60)
    
    # 詢問是否要先清除資料庫
    while True:
        choice = input("是否要先清除並重新初始化資料庫？(y/n/skip): ").strip().lower()
        if choice in ['y', 'yes']:
            # 🧹 先清除舊的向量資料庫
            print("\n🧹 清除原有向量資料庫...")
            delete_collection("teachers_vector")
            delete_collection("rules_vector")
            delete_collection("faq_vector")
            print("✅ 清除完成！")
            
            # 🚀 初始化向量資料庫
            print("\n🚀 初始化向量資料庫...")
            await init_vectordb()
            print("✅ 向量資料庫初始化完成！")
            break
        elif choice in ['n', 'no']:
            # 只初始化，不清除
            print("\n🚀 初始化向量資料庫...")
            await init_vectordb()
            print("✅ 向量資料庫初始化完成！")
            break
        elif choice == 'skip':
            # 跳過初始化，直接使用現有的
            print("⏭️ 跳過初始化，使用現有資料庫")
            break
        else:
            print("❌ 請輸入 y/n/skip")
    
    # 🔄 開始互動式測試
    await interactive_test()
    
    print("\n🎉 程式結束！")

if __name__ == "__main__":
    asyncio.run(main())