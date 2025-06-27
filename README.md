# TSD AI 助手 - 智能技術支援文檔查詢系統

## 專案概述

TSD AI 助手是一個基於 RAG (Retrieval-Augmented Generation) 技術的智能文檔查詢系統，專為東擎科技 (ASRock Industrial) 技術支援部門 (TSD) 設計。系統結合了文檔檢索、智能篩選和自動化回答生成，能夠快速從大量技術支援文檔中找到相關資訊並提供準確的答案。

## 核心功能

### 🔍 智能文檔檢索
- 支援多種文檔格式：TXT、PDF、MD、JSON、DOCX、DOC、XLSX、XLS
- 基於語義相似度的向量搜索
- 支援時間區間篩選
- 自動提取文檔時間戳

### 🤖 AI 代理系統
- 使用 AutoGen 框架構建多代理協作系統
- 文檔篩選代理：智能判斷文檔與查詢的相關性
- 答案合成代理：整合相關文檔生成綜合性答案
- 支援 Ollama 本地 LLM 模型

### 🌐 多用戶獨立性
- 基於 IP 的用戶隔離機制
- 每個 IP 用戶擁有獨立的 agent 執行環境
- 支援多用戶並發使用，互不干擾
- 頁面刷新時自動停止當前 IP 的任務

### 📊 實時處理反饋
- Server-Sent Events (SSE) 實時流式回應
- 詳細的處理步驟展示：搜索 → 篩選 → 答案生成
- 任務進度追蹤和狀態管理
- 篩選過程的詳細交互記錄

### 📁 文檔管理
- Web 界面文檔上傳
- 批量文檔處理
- 文檔列表查看和管理
- 文檔內容預覽
- 支援文檔刪除和批量刪除

### 📝 查詢歷史
- 完整的查詢歷史記錄
- 歷史查詢結果查看
- 支援歷史記錄刪除
- 篩選交互過程回放

## 系統架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Flask Backend │    │   Ollama LLM    │
│   (HTML/JS/CSS) │◄──►│   (Python)      │◄──►│   (Local)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Vector DB     │
                       │   (JSON-based)  │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AutoGen       │
                       │   Multi-Agent   │
                       └─────────────────┘
```

## 技術棧

### 後端技術
- **Python 3.x**: 主要開發語言
- **Flask**: Web 框架
- **AutoGen**: 多代理協作框架
- **Ollama**: 本地 LLM 服務
- **LangChain**: 文檔處理和分割
- **Scikit-learn**: 向量相似度計算
- **OpenCC**: 簡繁體中文轉換

### 前端技術
- **HTML5/CSS3**: 頁面結構和樣式
- **JavaScript (ES6+)**: 交互邏輯
- **Server-Sent Events**: 實時數據流
- **Bootstrap**: UI 框架

### 數據存儲
- **JSONVectorDB**: 自定義向量數據庫
- **JSON**: 文檔和元數據存儲
- **File System**: 上傳文檔管理

## 安裝和部署

### 系統要求
- Python 3.8+
- Ollama 服務
- 8GB+ RAM (推薦)
- 10GB+ 磁盤空間

### 1. 克隆專案
```bash
git clone <repository-url>
cd agentic_rag_web_0627
```

### 2. 安裝依賴
```bash
pip install flask ollama autogen langchain pandas python-docx numpy scikit-learn opencc-python-reimplemented
```

### 3. 配置 Ollama
```bash
# 安裝 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 下載所需模型
ollama pull tsd_4500datas_summary20250606_epoch11_f32:latest
ollama pull qwen3:30b
```

### 4. 啟動服務
```bash
# 使用啟動腳本
python start_server.py

# 或直接啟動
python app.py
```

### 5. 訪問系統
打開瀏覽器訪問：http://localhost:5000

## 使用指南

### 文檔上傳
1. 進入管理頁面：http://localhost:5000/manage
2. 點擊「選擇文件」上傳支援格式的文檔
3. 系統自動處理並建立向量索引

### 智能查詢
1. 在主頁面輸入查詢問題
2. 選擇時間區間（可選）
3. 點擊「查詢」開始處理
4. 觀看實時處理過程和結果

### 歷史查詢
1. 訪問歷史頁面：http://localhost:5000/history
2. 查看所有歷史查詢記錄
3. 點擊查詢可查看詳細結果

## 配置說明

### 模型配置 (`agent_rag_0609.py`)
```python
# Ollama 配置
self.base_url = "http://localhost:11434/v1"
self.embedding_model = "tsd_4500datas_summary20250606_epoch11_f32:latest"
self.llm_model = "qwen3:30b"  # 或 "gemma3:27b"
```

### 系統配置 (`app.py`)
```python
# 文件上傳配置
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 支援的文件類型
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'md', 'json', 'docx', 'doc', 'xlsx', 'xls'
}
```

## API 文檔

### 主要 API 端點

#### 文檔查詢
```
GET /api/query/stream?question=<query>&date_range=<range>
```
- 實時流式查詢
- 返回 SSE 格式數據

#### 文檔上傳
```
POST /api/upload
Content-Type: multipart/form-data
```

#### 文檔管理
```
GET /api/documents          # 獲取文檔列表
DELETE /api/documents/<filename>  # 刪除文檔
DELETE /api/documents/batch      # 批量刪除
```

#### 歷史查詢
```
GET /api/history/list       # 獲取歷史列表
GET /api/history/<id>       # 獲取歷史詳情
DELETE /api/history/<id>    # 刪除歷史
```

## 測試指南

### 自動化測試
```bash
# 多 IP 用戶獨立性測試
python test_multi_ip.py
```

### 手動測試
1. 開啟多個瀏覽器窗口
2. 同時發送查詢請求
3. 驗證各自獨立處理

### 性能測試
```bash
# 使用 Apache Bench
ab -n 100 -c 10 http://localhost:5000/

# 使用 wrk
wrk -t12 -c400 -d30s http://localhost:5000/
```

## 故障排除

### 常見問題

#### 1. Ollama 連接失敗
```bash
# 檢查 Ollama 服務狀態
ollama list
systemctl status ollama  # Linux
```

#### 2. 模型下載問題
```bash
# 手動下載模型
ollama pull <model-name>
```

#### 3. 內存不足
- 調整模型大小
- 增加系統內存
- 優化批處理大小

#### 4. 文檔處理失敗
- 檢查文檔格式
- 確認文件權限
- 查看錯誤日誌

### 日誌查看
系統運行時會在控制台輸出詳細日誌，包括：
- 查詢請求信息
- 文檔處理狀態
- 任務管理狀態
- 錯誤信息

## 開發指南

### 專案結構
```
agentic_rag_web_0627/
├── app.py                 # 主應用程序
├── agent_rag_0609.py      # RAG 代理系統
├── vector_db.py           # 向量數據庫
├── start_server.py        # 啟動腳本
├── test_multi_ip.py       # 測試腳本
├── templates/             # HTML 模板
│   ├── index.html        # 主頁面
│   ├── manage.html       # 管理頁面
│   ├── history.html      # 歷史頁面
│   └── history_detail.html # 歷史詳情
├── static/               # 靜態資源
├── uploads/              # 上傳文檔
├── custom_json_rag_db/   # 向量數據庫
└── history/              # 查詢歷史
```

### 擴展開發
1. **添加新的文檔格式支援**
   - 在 `agent_rag_0609.py` 中添加處理函數
   - 更新 `ALLOWED_EXTENSIONS`

2. **自定義 AI 代理**
   - 修改 `setup_agents()` 方法
   - 調整代理的系統提示

3. **優化向量搜索**
   - 改進 `JSONVectorDB` 類
   - 添加更多搜索策略

## 貢獻指南

1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 創建 Pull Request

## 授權協議

本專案採用 MIT 授權協議。

## 聯繫方式

如有問題或建議，請聯繫技術支援團隊。

---

**版本**: 1.0.0  
**最後更新**: 2024年12月  
**維護者**: TSD Team 