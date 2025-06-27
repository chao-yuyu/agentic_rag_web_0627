#!/usr/bin/env python3
"""
測試多IP用戶獨立性的腳本
"""

import requests
import time
import threading
from flask import Flask
import json

# 測試配置
BASE_URL = "http://localhost:5000"
TEST_QUESTION = "EMX-BTX-D 主板的問題"
TEST_DATE_RANGE = "20200101 - 20201231"

def simulate_user_session(user_id, delay=0):
    """模擬單個用戶的會話"""
    print(f"用戶 {user_id} 開始測試...")
    
    # 設置自定義headers來模擬不同的IP
    headers = {
        'X-Forwarded-For': f'192.168.1.{100 + user_id}',
        'User-Agent': f'TestUser-{user_id}'
    }
    
    try:
        # 1. 訪問主頁
        print(f"用戶 {user_id}: 訪問主頁")
        response = requests.get(f"{BASE_URL}/", headers=headers)
        if response.status_code != 200:
            print(f"用戶 {user_id}: 訪問主頁失敗 - {response.status_code}")
            return
        
        # 2. 發送查詢請求
        print(f"用戶 {user_id}: 發送查詢請求")
        query_url = f"{BASE_URL}/api/query/stream?question={TEST_QUESTION}&date_range={TEST_DATE_RANGE}"
        
        # 使用 EventSource 模擬
        response = requests.get(query_url, headers=headers, stream=True)
        if response.status_code != 200:
            print(f"用戶 {user_id}: 查詢請求失敗 - {response.status_code}")
            return
        
        # 讀取流式響應
        task_id = None
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]  # 移除 'data: ' 前綴
                    try:
                        data = json.loads(data_str)
                        if data.get('step') == 'task_id':
                            task_id = data.get('task_id')
                            print(f"用戶 {user_id}: 獲得任務ID - {task_id}")
                        elif data.get('step') == 'search':
                            print(f"用戶 {user_id}: 搜索完成，找到 {len(data.get('results', []))} 個文檔")
                        elif data.get('step') == 'filter':
                            print(f"用戶 {user_id}: 篩選完成，保留 {len(data.get('results', []))} 個文檔")
                        elif data.get('step') == 'answer':
                            print(f"用戶 {user_id}: 答案生成完成")
                            break
                        elif data.get('step') == 'error':
                            print(f"用戶 {user_id}: 發生錯誤 - {data.get('message')}")
                            break
                    except json.JSONDecodeError:
                        continue
        
        print(f"用戶 {user_id} 測試完成")
        
    except Exception as e:
        print(f"用戶 {user_id} 測試失敗: {str(e)}")

def test_concurrent_users():
    """測試並發用戶"""
    print("開始測試並發用戶...")
    
    # 創建多個線程模擬不同用戶
    threads = []
    for i in range(3):  # 測試3個用戶
        thread = threading.Thread(
            target=simulate_user_session, 
            args=(i, i * 2)  # 每個用戶延遲2秒啟動
        )
        threads.append(thread)
        thread.start()
    
    # 等待所有線程完成
    for thread in threads:
        thread.join()
    
    print("並發用戶測試完成")

def test_single_user():
    """測試單個用戶"""
    print("開始測試單個用戶...")
    simulate_user_session(0)
    print("單個用戶測試完成")

if __name__ == "__main__":
    print("多IP用戶獨立性測試")
    print("=" * 50)
    
    # 檢查服務器是否運行
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("服務器運行正常")
        else:
            print(f"服務器響應異常: {response.status_code}")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("無法連接到服務器，請確保 Flask 應用正在運行")
        exit(1)
    
    print("\n1. 測試單個用戶")
    test_single_user()
    
    print("\n2. 測試並發用戶")
    test_concurrent_users()
    
    print("\n測試完成！") 