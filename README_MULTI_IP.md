# 多IP用戶獨立性修改說明

## 問題描述

原本的系統中，所有用戶共享同一個任務管理系統，當一個IP的用戶正在等待agent執行時，如果另一個IP的用戶訪問網站，會導致原本正在執行的agent被中斷。

## 解決方案

修改了任務管理系統，讓每個IP用戶都有獨立的agent執行環境，同時保持現有的lock機制和頁面刷新時停止agent的功能。

## 主要修改

### 1. 任務管理系統重構 (`app.py`)

#### 修改前：
```python
# 全局變量用於追踪正在執行的任務
running_tasks = {}
```

#### 修改後：
```python
# 修改任務管理系統：按IP分組
# 結構: {ip: {task_id: task_data}}
running_tasks_by_ip = {}
```

### 2. 新增IP獲取功能

```python
def get_client_ip():
    """獲取客戶端IP地址"""
    # 檢查是否有代理
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr
```

### 3. 新增IP任務清理功能

```python
def cleanup_ip_tasks(ip):
    """清理指定IP的所有正在執行的任務"""
    with task_lock:
        if ip in running_tasks_by_ip:
            for task_id, task_data in running_tasks_by_ip[ip].items():
                if task_data.get('rag_system'):
                    task_data['rag_system'].stop_current_task()
            del running_tasks_by_ip[ip]
            print(f"已清理IP {ip} 的所有任務")
```

### 4. 修改路由處理

- **主頁路由 (`/`)**: 只清理當前IP的任務
- **管理頁面路由 (`/manage`)**: 只清理當前IP的任務
- **查詢流路由 (`/api/query/stream`)**: 為每個IP創建獨立的任務

### 5. 修改篩選交互查詢

更新了 `get_filter_interaction` 函數，使其能夠在按IP分組的任務管理系統中正確查找任務。

## 功能特點

### ✅ 保持的功能
1. **Lock機制**: 仍然使用 `task_lock` 和 `completed_task_lock` 確保線程安全
2. **頁面刷新停止**: 用戶刷新頁面或訪問管理頁面時，仍然會停止該IP的所有正在執行的agent
3. **任務過期清理**: 已完成的任務仍然會在1小時後自動清理
4. **篩選交互查詢**: 仍然可以查詢文檔篩選的交互過程

### ✅ 新增的功能
1. **IP隔離**: 每個IP的用戶都有完全獨立的agent執行環境
2. **並發支持**: 多個IP可以同時使用系統，互不影響
3. **獨立任務管理**: 每個IP的任務獨立管理，不會相互干擾

## 使用方式

### 正常使用
用戶的使用方式完全沒有改變，所有功能保持不變。

### 測試多IP功能
可以使用提供的測試腳本：

```bash
python test_multi_ip.py
```

測試腳本會模擬3個不同IP的用戶同時使用系統，驗證獨立性。

## 技術細節

### 數據結構變化
```python
# 修改前
running_tasks = {
    "task_id_1": {"rag_system": agent1, "start_time": time1},
    "task_id_2": {"rag_system": agent2, "start_time": time2}
}

# 修改後
running_tasks_by_ip = {
    "192.168.1.100": {
        "task_id_1": {"rag_system": agent1, "start_time": time1}
    },
    "192.168.1.101": {
        "task_id_2": {"rag_system": agent2, "start_time": time2}
    }
}
```

### 線程安全
- 使用 `task_lock` 保護 `running_tasks_by_ip` 的讀寫操作
- 使用 `completed_task_lock` 保護 `completed_task_interactions` 的讀寫操作
- 每個 `CustomRAGAgentSystem` 實例都有自己的 `_stop_flag`，確保獨立的中斷控制

### 內存管理
- 任務完成後會自動清理對應的IP條目
- 如果某個IP沒有其他任務，會清理整個IP條目
- 已完成的任務仍然會在1小時後自動清理

## 注意事項

1. **IP識別**: 系統會優先使用 `X-Forwarded-For` 或 `X-Real-IP` header，如果都沒有則使用 `request.remote_addr`
2. **代理環境**: 如果在代理環境中運行，請確保正確設置了 `X-Forwarded-For` header
3. **內存使用**: 每個IP的用戶都會創建獨立的 `CustomRAGAgentSystem` 實例，請注意內存使用情況
4. **並發限制**: 雖然支持多IP並發，但建議根據服務器性能限制同時連接的用戶數量

## 兼容性

此修改完全向後兼容，不會影響現有的功能和使用方式。所有現有的API端點和前端功能都保持不變。 