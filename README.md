# 智能文檔查詢系統 - AI RAG Web 應用

## 專案概述

這是一個基於 RAG (Retrieval-Augmented Generation) 技術的智能文檔查詢系統。系統結合了文檔檢索、智能篩選和自動化回答生成，能夠快速從大量文檔中找到相關資訊並提供準確的答案。適用於企業知識庫管理、技術文檔查詢、客服支援等多種場景。

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

# 下載所需模型（可根據需求選擇其他模型）
ollama pull llama2:7b
ollama pull nomic-embed-text
```

### 4. 配置模型
編輯 `agent_rag_0609.py` 文件，根據您的模型選擇進行配置：
```python
# 修改為您使用的模型
self.embedding_model = "nomic-embed-text"
self.llm_model = "llama2:7b"
```

### 5. 啟動服務
```bash
# 使用啟動腳本
python start_server.py

# 或直接啟動
python app.py
```

### 6. 訪問系統
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
self.embedding_model = "nomic-embed-text"  # 嵌入模型
self.llm_model = "llama2:7b"  # 語言模型
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

### 代理系統配置
可以根據您的需求自定義代理的系統提示詞：
```python
# 文檔篩選代理提示詞
system_message = """您是專業的文檔篩選專家。您的任務是:
1. 仔細閱讀提供的文檔內容
2. 精確判斷文檔是否與用戶查詢相關
3. 如果相關，返回 "RELEVANT: [相關原因]"
4. 如果不相關，返回 "NOT_RELEVANT: [不相關原因]"
"""
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

#### 5. 中文處理問題
- 確保安裝了 opencc-python-reimplemented
- 檢查文檔編碼格式

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

#### 1. 添加新的文檔格式支援
```python
# 在 agent_rag_0609.py 中添加處理函數
def add_new_format_document(self, file_path: str):
    # 實現新格式的處理邏輯
    pass

# 更新允許的文件擴展名
ALLOWED_EXTENSIONS.add('new_format')
```

#### 2. 自定義 AI 代理
```python
# 修改 setup_agents() 方法
def setup_agents(self):
    self.custom_agent = autogen.AssistantAgent(
        name="CustomAgent",
        llm_config=self.llm_config,
        system_message="自定義代理的系統提示詞"
    )
```

#### 3. 優化向量搜索
```python
# 改進 JSONVectorDB 類
class JSONVectorDB:
    def advanced_search(self, query, filters=None):
        # 實現高級搜索功能
        pass
```

## 應用場景

- **企業知識庫**: 快速檢索企業內部文檔和知識
- **技術支援**: 自動回答技術問題和故障排除
- **客服系統**: 智能客服機器人的知識後端
- **研究助手**: 學術文獻和研究資料的智能檢索
- **法律諮詢**: 法律條文和案例的快速查詢
- **醫療資訊**: 醫學文獻和診療指南的檢索

## 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 創建 Pull Request

## 授權協議

本專案採用 MIT 授權協議。詳見 [LICENSE](LICENSE) 文件。

## 致謝

感謝以下開源專案的支持：
- [AutoGen](https://github.com/microsoft/autogen)
- [Ollama](https://ollama.ai/)
- [LangChain](https://langchain.com/)
- [Flask](https://flask.palletsprojects.com/)

---

**版本**: 1.0.0  
**最後更新**: 2025年06月  
**維護者**: CHAO YU CHEN 